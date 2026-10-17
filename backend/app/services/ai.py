"""
Weekly money report.

Provider chain: Groq (free, fast) -> Google Gemini (free tier) -> built-in rules.
The rules fallback means the feature never shows an error in a demo, even
with no API keys configured.

The LLM only sees aggregated numbers (category totals, budget status), never
raw descriptions or the user's email, so no personal identifiers leave the server.
"""
from datetime import date, timedelta

import requests
from flask import current_app

from app.services.analytics import dashboard, load_transactions, by_category

TIMEOUT = 25
# Fixed commitments: no point telling someone to "spread out" their rent
FIXED = {"Rent & Housing", "Hostel & Rent", "EMI & Loans", "Investments", "Taxes", "Fees"}

TONE = {
    "student": ("a friendly finance buddy for an Indian college student living on a monthly "
                "allowance. Suggest student-realistic swaps (mess vs delivery, metro vs cab, "
                "student plans). Never lecture."),
    "employee": ("a sharp personal finance coach for a salaried professional in India. "
                 "Refer to the 50/30/20 rule, EMIs and savings rate where relevant."),
    "freelancer": ("a practical finance coach for an Indian freelancer with irregular income. "
                   "Focus on smoothing income, tax set-aside and business costs."),
}


def week_bounds(today: date) -> tuple[date, date]:
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=6)


def build_context(user, today: date | None = None) -> dict:
    today = today or date.today()
    w_start, _ = week_bounds(today)
    last7 = load_transactions(user.id, today - timedelta(days=6), today)
    prev7 = load_transactions(user.id, today - timedelta(days=13), today - timedelta(days=7))
    dash = dashboard(user, today.year, today.month, today)
    return {
        "profile_type": user.profile_type or "student",
        "name": (user.name or "there").split(" ")[0],
        "week_start": w_start,
        "week_spend": round(sum(t.amount for t in last7 if t.type == "expense"), 2),
        "prev_week_spend": round(sum(t.amount for t in prev7 if t.type == "expense"), 2),
        "week_categories": by_category(last7)[:6],
        "month": dash["summary"],
        "month_categories": dash["by_category"][:6],
        "budgets": [b for b in dash["budgets"] if b["status"] != "ok" and b["category"] not in FIXED],
        "anomalies": dash["anomalies"][:3],
        "recurring": [r for r in dash["recurring"] if 0 <= r["days_until"] <= 10][:3],
        "profile": dash["profile"],
    }


def _profile_lines(ctx: dict) -> list[str]:
    p, ptype = ctx["profile"], ctx["profile_type"]
    lines = []
    if ptype in ("student", "employee") and "cycle" in p:
        c = p["cycle"]
        lines.append(f"Money cycle: ₹{c['left']} left of ₹{c['budget']}, {c['days_left']} days until "
                     f"next income, daily burn ₹{c['daily_burn']}, safe to spend ₹"
                     f"{c['safe_to_spend_today']}/day, status {c['status']}.")
    if ptype == "student":
        lines.append(f"No-spend streak: {p['no_spend_streak']} days. Semester costs (6 mo): ₹{p['semester_total']}.")
    if ptype == "employee":
        r = p["rule_50_30_20"]
        lines.append(f"50/30/20 this month: needs {r['needs']['percent']}%, wants {r['wants']['percent']}%, "
                     f"savings {r['savings']['percent']}%. EMI {p['emi_to_income']}% of income.")
    if ptype == "freelancer":
        lines.append(f"Avg monthly income ₹{p['avg_monthly_income']}, volatility {p['income_volatility']}%, "
                     f"tax set-aside this month ₹{p['tax_set_aside']}.")
    return lines


def build_prompt(ctx: dict) -> str:
    cats = ", ".join(f"{c['category']} ₹{c['amount']}" for c in ctx["week_categories"]) or "no spends"
    mcats = ", ".join(f"{c['category']} ₹{c['amount']}" for c in ctx["month_categories"]) or "none"
    budgets = "; ".join(f"{b['category']} at {b['percent']}% of ₹{b['limit']}" for b in ctx["budgets"]) or "all within limits"
    anomalies = "; ".join(f"{a['category']} {a['ratio']}x usual" for a in ctx["anomalies"]) or "none"
    upcoming = "; ".join(f"{r['merchant']} ₹{r['amount']} in {r['days_until']} days" for r in ctx["recurring"]) or "none"
    m = ctx["month"]
    profile = "\n".join(_profile_lines(ctx))
    return f"""You are {TONE[ctx['profile_type']]}

Write this week's money report for {ctx['name']} using ONLY the numbers below.

DATA
- Last 7 days spent: ₹{ctx['week_spend']} (previous 7 days: ₹{ctx['prev_week_spend']})
- Last 7 days by category: {cats}
- This month so far: income ₹{m['income']}, spent ₹{m['expense']}, savings rate {m['savings_rate']}%
- This month by category: {mcats}
- Budgets needing attention: {budgets}
- Unusual spending vs last 3 months: {anomalies}
- Upcoming recurring payments: {upcoming}
{profile}

FORMAT (follow exactly, plain text, use ₹ for rupees, no markdown headers):
Line 1: one-sentence summary of the week.
Then 3 or 4 lines each starting with "- ": specific observations with numbers. Start with something they did well.
Last line starting with "Action: " giving ONE concrete thing to do this week.
Keep the whole thing under 140 words."""


def _call_groq(prompt: str) -> str:
    key = current_app.config.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("no groq key")
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": current_app.config["GROQ_MODEL"], "temperature": 0.5, "max_tokens": 400,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _call_gemini(prompt: str) -> str:
    key = current_app.config.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("no gemini key")
    model = current_app.config["GEMINI_MODEL"]
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.5, "maxOutputTokens": 400}},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def rules_report(ctx: dict) -> str:
    """Deterministic report used when no LLM is available."""
    week, prev = ctx["week_spend"], ctx["prev_week_spend"]
    if prev:
        change = (week - prev) / prev * 100
        trend = f"{'down' if change < 0 else 'up'} {abs(change):.0f}% from the week before"
    else:
        trend = "your first tracked week"
    lines = [f"You spent ₹{week:,.0f} in the last 7 days, {trend}."]

    good = []
    if prev and week < prev:
        good.append(f"- Nice: you spent ₹{prev - week:,.0f} less than the previous week.")
    p = ctx["profile"]
    if ctx["profile_type"] == "student" and p.get("no_spend_streak", 0) >= 2:
        good.append(f"- {p['no_spend_streak']}-day no-spend streak going. Keep it alive!")
    if ctx["month"]["savings_rate"] and ctx["month"]["savings_rate"] > 20:
        good.append(f"- You've kept {ctx['month']['savings_rate']:.0f}% of this month's income so far.")
    lines += good[:1] or ["- You're tracking every rupee, which is the hardest habit to build."]

    if ctx["week_categories"]:
        top = ctx["week_categories"][0]
        lines.append(f"- {top['category']} was your biggest spend this week at ₹{top['amount']:,.0f} "
                     f"({top['share']:.0f}% of the week).")
    for a in ctx["anomalies"][:1]:
        lines.append(f"- {a['category']} is at ₹{a['amount']:,.0f} this month, {a['ratio']}x your usual ₹{a['usual']:,.0f}.")
    for b in ctx["budgets"][:1]:
        lines.append(f"- {b['category']} budget is at {b['percent']:.0f}% (₹{b['spent']:,.0f} of ₹{b['limit']:,.0f}).")
    for r in ctx["recurring"][:1]:
        lines.append(f"- Heads up: {r['merchant']} (₹{r['amount']:,.0f}) is due in {r['days_until']} days.")

    action = None
    if "cycle" in p and p["cycle"]["status"] in ("at_risk", "broke"):
        c = p["cycle"]
        action = ("Action: Pause non-essential spends until your next credit and review subscriptions."
                  if c["status"] == "broke" else
                  f"Action: Keep daily spends under ₹{c['safe_to_spend_today']:,.0f} so your money lasts "
                  f"the {c['days_left']} days until the next credit.")
    elif ctx["anomalies"]:
        a = ctx["anomalies"][0]
        action = (f"Action: Go easy on {a['category']} for the rest of the month. You're already "
                  f"₹{a['amount'] - a['usual']:,.0f} above your usual by this point.")
    elif ctx["budgets"]:
        b = ctx["budgets"][0]
        today = date.today()
        days_left = (date(today.year + today.month // 12, today.month % 12 + 1, 1) - today).days
        if b["remaining"] > 0:
            action = (f"Action: ₹{b['remaining']:,.0f} is left in your {b['category']} budget. That's about "
                      f"₹{b['remaining'] / max(days_left, 1):,.0f}/day for the {days_left} days left this month.")
        else:
            action = f"Action: {b['category']} is over budget. Skip it for the rest of the month if you can."
    elif ctx["profile_type"] == "freelancer" and p.get("tax_set_aside"):
        action = f"Action: Move ₹{p['tax_set_aside']:,.0f} to a separate account for taxes this month."
    elif ctx["profile_type"] == "student":
        action = "Action: Try a 2-day no-spend challenge this week (mess food + metro only)."
    else:
        action = "Action: Set a budget for your top category so you get an alert at 80%."
    lines = lines[:5] + [action]
    return "\n".join(lines)


def generate_report(user, today: date | None = None) -> tuple[str, str, dict]:
    """Returns (content, source, context)."""
    ctx = build_context(user, today)
    prompt = build_prompt(ctx)
    for name, fn in (("groq", _call_groq), ("gemini", _call_gemini)):
        try:
            text = fn(prompt)
            if text:
                return text, name, ctx
        except Exception as e:  # network/quota/key problems -> try the next provider
            current_app.logger.info("AI provider %s unavailable: %s", name, e)
    return rules_report(ctx), "rules", ctx


def providers_status() -> dict:
    return {
        "groq": bool(current_app.config.get("GROQ_API_KEY")),
        "gemini": bool(current_app.config.get("GEMINI_API_KEY")),
        "rules": True,
    }
