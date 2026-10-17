"""
All dashboard numbers. One DB query loads ~7 months of the user's rows,
then everything is computed in Python in O(n) (n = rows loaded), apart from
recurring detection which sorts each merchant group: O(n log n).
"""
import calendar
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean, median, pstdev

from app.constants import SEMESTER_CATEGORIES, NEEDS, SAVINGS
from app.models.db_models import Transaction, Budget, Goal, User


# ---------- date helpers ----------
def shift_month(y: int, m: int, delta: int) -> tuple[int, int]:
    idx = y * 12 + (m - 1) + delta
    return idx // 12, idx % 12 + 1


def month_bounds(y: int, m: int) -> tuple[date, date]:
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def _on_day(y: int, m: int, day: int) -> date:
    return date(y, m, min(day, calendar.monthrange(y, m)[1]))


def cycle_bounds(today: date, income_day: int) -> tuple[date, date]:
    """Money cycle = last income day on/before today -> next income day."""
    this = _on_day(today.year, today.month, income_day)
    if this <= today:
        ny, nm = shift_month(today.year, today.month, 1)
        return this, _on_day(ny, nm, income_day)
    py, pm = shift_month(today.year, today.month, -1)
    return _on_day(py, pm, income_day), this


def _r(x: float) -> float:
    return round(float(x), 2)


# ---------- building blocks ----------
def load_transactions(user_id: int, start: date, end: date) -> list[Transaction]:
    return (Transaction.query
            .filter(Transaction.user_id == user_id, Transaction.date.between(start, end))
            .order_by(Transaction.date.asc()).all())


def totals(txns) -> dict:
    inc = sum(t.amount for t in txns if t.type == "income")
    exp = sum(t.amount for t in txns if t.type == "expense")
    return {"income": _r(inc), "expense": _r(exp), "net": _r(inc - exp),
            "savings_rate": round((inc - exp) / inc * 100, 1) if inc else None,
            "count": len(txns)}


def by_category(txns, tx_type="expense") -> list[dict]:
    agg = defaultdict(float)
    for t in txns:
        if t.type == tx_type:
            agg[t.category or "Other"] += t.amount
    total = sum(agg.values()) or 1
    return [{"category": c, "amount": _r(a), "share": round(a / total * 100, 1)}
            for c, a in sorted(agg.items(), key=lambda kv: -kv[1])]


def top_merchants(txns, limit=5) -> list[dict]:
    agg = defaultdict(lambda: {"amount": 0.0, "count": 0, "category": None})
    for t in txns:
        if t.type == "expense" and t.merchant:
            a = agg[t.merchant]
            a["amount"] += t.amount
            a["count"] += 1
            a["category"] = t.category
    ranked = sorted(agg.items(), key=lambda kv: -kv[1]["amount"])[:limit]
    return [{"merchant": m.title(), "amount": _r(v["amount"]), "count": v["count"],
             "category": v["category"]} for m, v in ranked]


def monthly_trend(txns, y: int, m: int, months=6) -> list[dict]:
    buckets = {}
    for i in range(months - 1, -1, -1):
        yy, mm = shift_month(y, m, -i)
        buckets[(yy, mm)] = {"month": f"{yy}-{mm:02d}", "label": calendar.month_abbr[mm],
                             "income": 0.0, "expense": 0.0}
    for t in txns:
        b = buckets.get((t.date.year, t.date.month))
        if b:
            b[t.type] += t.amount
    return [{**b, "income": _r(b["income"]), "expense": _r(b["expense"])} for b in buckets.values()]


def daily_spend(txns, start: date, end: date) -> list[dict]:
    days = {start + timedelta(d): 0.0 for d in range((end - start).days + 1)}
    for t in txns:
        if t.type == "expense" and t.date in days:
            days[t.date] += t.amount
    return [{"date": d.isoformat(), "day": d.day, "amount": _r(a)} for d, a in days.items()]


def detect_recurring(txns, today: date) -> list[dict]:
    """Same merchant, 3+ payments ~monthly (25-35 day gaps), amounts within 20%."""
    groups = defaultdict(list)
    for t in txns:
        if t.type == "expense" and t.merchant and t.date >= today - timedelta(days=160):
            groups[t.merchant].append(t)
    found = []
    for merchant, items in groups.items():
        if len(items) < 3:
            continue
        items.sort(key=lambda t: t.date)
        gaps = [(b.date - a.date).days for a, b in zip(items, items[1:])]
        amounts = [t.amount for t in items]
        med_gap, med_amt = median(gaps), median(amounts)
        if not 25 <= med_gap <= 35:
            continue
        if any(abs(a - med_amt) > 0.2 * med_amt for a in amounts[-3:]):
            continue
        nxt = items[-1].date + timedelta(days=round(med_gap))
        found.append({"merchant": merchant.title(), "category": items[-1].category,
                      "amount": _r(med_amt), "next_date": nxt.isoformat(),
                      "days_until": (nxt - today).days})
    return sorted(found, key=lambda r: r["days_until"])


def detect_anomalies(txns, y: int, m: int) -> list[dict]:
    """Category spend this month vs average of the previous 3 months."""
    cur = defaultdict(float)
    prev = defaultdict(lambda: [0.0, 0.0, 0.0])
    prev_months = [shift_month(y, m, -i) for i in (1, 2, 3)]
    for t in txns:
        if t.type != "expense":
            continue
        key = (t.date.year, t.date.month)
        if key == (y, m):
            cur[t.category] += t.amount
        elif key in prev_months:
            prev[t.category][prev_months.index(key)] += t.amount
    out = []
    for cat, amount in cur.items():
        avg = mean(prev[cat]) if cat in prev else 0
        if avg > 0 and amount > 1.5 * avg and amount - avg >= 300:
            out.append({"category": cat, "amount": _r(amount), "usual": _r(avg),
                        "ratio": round(amount / avg, 1)})
    return sorted(out, key=lambda a: -a["ratio"])


def budget_status(user_id: int, month_txns) -> list[dict]:
    spent = defaultdict(float)
    for t in month_txns:
        if t.type == "expense":
            spent[t.category] += t.amount
    rows = []
    for b in Budget.query.filter_by(user_id=user_id).order_by(Budget.category).all():
        s = spent.get(b.category, 0.0)
        pct = s / b.monthly_limit * 100 if b.monthly_limit else 0
        rows.append({"id": b.id, "category": b.category, "limit": _r(b.monthly_limit),
                     "spent": _r(s), "remaining": _r(b.monthly_limit - s), "percent": round(pct, 1),
                     "status": "over" if pct >= 100 else "warning" if pct >= 80 else "ok"})
    return rows


# ---------- profile-specific blocks ----------
def money_cycle(user: User, txns, today: date, exclude: set[str] = frozenset()) -> dict:
    """Runway + safe-to-spend for the current allowance/salary cycle."""
    start, nxt = cycle_bounds(today, user.income_day)
    in_cycle = [t for t in txns if start <= t.date <= today]
    received = sum(t.amount for t in in_cycle if t.type == "income")
    spent = sum(t.amount for t in in_cycle if t.type == "expense" and t.category not in exclude)
    base = max(received, user.monthly_income or 0)
    left = base - spent
    days_elapsed = (today - start).days + 1
    days_left = max((nxt - today).days, 1)
    burn = spent / days_elapsed if days_elapsed else 0
    runway = (left / burn) if burn > 0 else None
    return {
        "cycle_start": start.isoformat(), "next_income": nxt.isoformat(),
        "days_left": days_left, "budget": _r(base), "spent": _r(spent), "left": _r(left),
        "daily_burn": _r(burn),
        "safe_to_spend_today": _r(max(left, 0) / days_left),
        "runway_days": round(runway, 1) if runway is not None else None,
        "status": ("broke" if left <= 0 else
                   "on_track" if runway is None or runway >= days_left else "at_risk"),
    }


def student_block(user: User, txns, today: date) -> dict:
    cycle = money_cycle(user, txns, today, exclude=SEMESTER_CATEGORIES | {"Hostel & Rent"})
    # No-spend streak: days in a row (ending today/yesterday) with no daily spends
    daily = {t.date for t in txns if t.type == "expense"
             and t.category not in SEMESTER_CATEGORIES | {"Hostel & Rent", "Subscriptions"}}
    streak, d = 0, today
    if d not in daily:
        while d not in daily and (today - d).days < 60:
            streak += 1
            d -= timedelta(days=1)
    six_months_ago = today - timedelta(days=183)
    semester = defaultdict(float)
    income_sources = defaultdict(float)
    for t in txns:
        if t.date < six_months_ago:
            continue
        if t.type == "expense" and t.category in SEMESTER_CATEGORIES:
            semester[t.category] += t.amount
        if t.type == "income":
            income_sources[t.category] += t.amount
    return {
        "cycle": cycle,
        "no_spend_streak": streak,
        "semester_spend": [{"category": c, "amount": _r(a)} for c, a in
                           sorted(semester.items(), key=lambda kv: -kv[1])],
        "semester_total": _r(sum(semester.values())),
        "income_sources": [{"source": c, "amount": _r(a)} for c, a in
                           sorted(income_sources.items(), key=lambda kv: -kv[1])],
    }


def employee_block(user: User, txns, month_txns, today: date) -> dict:
    income = sum(t.amount for t in month_txns if t.type == "income") or user.monthly_income or 0
    needs = sum(t.amount for t in month_txns if t.type == "expense" and t.category in NEEDS)
    savings_spend = sum(t.amount for t in month_txns if t.type == "expense" and t.category in SAVINGS)
    wants = sum(t.amount for t in month_txns if t.type == "expense") - needs - savings_spend
    saved = max(income - needs - wants, 0)  # includes investments + leftover
    pct = (lambda x: round(x / income * 100, 1) if income else 0)
    expenses_by_month = defaultdict(float)
    for t in txns:
        if t.type == "expense":
            expenses_by_month[(t.date.year, t.date.month)] += t.amount
    avg_monthly = mean(expenses_by_month.values()) if expenses_by_month else 0
    emi = sum(t.amount for t in month_txns if t.type == "expense" and t.category == "EMI & Loans")
    return {
        "cycle": money_cycle(user, txns, today),
        "rule_50_30_20": {
            "income": _r(income),
            "needs": {"amount": _r(needs), "percent": pct(needs), "target": 50},
            "wants": {"amount": _r(wants), "percent": pct(wants), "target": 30},
            "savings": {"amount": _r(saved), "percent": pct(saved), "target": 20},
        },
        "emi_this_month": _r(emi),
        "emi_to_income": pct(emi),
        "emergency_fund_target": _r(avg_monthly * 6),
        "avg_monthly_expense": _r(avg_monthly),
    }


def freelancer_block(user: User, txns, month_txns, y: int, m: int) -> dict:
    per_month = defaultdict(float)
    clients = defaultdict(float)
    for t in txns:
        if t.type == "income":
            per_month[(t.date.year, t.date.month)] += t.amount
            if t.category == "Client Payment":
                clients[(t.merchant or "Unknown").title()] += t.amount
    months = [per_month.get(shift_month(y, m, -i), 0.0) for i in range(6)]
    avg = mean(months)
    volatility = round(pstdev(months) / avg * 100, 1) if avg else None
    month_income = sum(t.amount for t in month_txns if t.type == "income")
    taxes_paid = sum(t.amount for t in month_txns if t.type == "expense" and t.category == "Taxes")
    expenses = sum(t.amount for t in month_txns if t.type == "expense")
    return {
        "avg_monthly_income": _r(avg),
        "income_volatility": volatility,
        "lean_month_income": _r(min(months)) if months else 0,
        "tax_rate": user.tax_rate,
        "tax_set_aside": _r(month_income * user.tax_rate),
        "taxes_paid_this_month": _r(taxes_paid),
        "buffer_months": round((avg - expenses) / expenses, 1) if expenses else None,
        "top_clients": [{"client": c, "amount": _r(a)} for c, a in
                        sorted(clients.items(), key=lambda kv: -kv[1])[:5]],
    }


# ---------- main entry ----------
def dashboard(user: User, y: int, m: int, today: date | None = None) -> dict:
    today = today or date.today()
    m_start, m_end = month_bounds(y, m)
    ty, tm = shift_month(y, m, -5)
    load_from = min(date(ty, tm, 1), today - timedelta(days=183))
    load_to = max(m_end, today)
    txns = load_transactions(user.id, load_from, load_to)

    month_txns = [t for t in txns if m_start <= t.date <= m_end]
    py, pm = shift_month(y, m, -1)
    p_start, p_end = month_bounds(py, pm)
    prev_txns = [t for t in txns if p_start <= t.date <= p_end]

    summary = totals(month_txns)
    prev = totals(prev_txns)
    summary["expense_change"] = (round((summary["expense"] - prev["expense"]) / prev["expense"] * 100, 1)
                                 if prev["expense"] else None)
    summary["income_change"] = (round((summary["income"] - prev["income"]) / prev["income"] * 100, 1)
                                if prev["income"] else None)

    data = {
        "month": f"{y}-{m:02d}",
        "profile_type": user.profile_type,
        "summary": summary,
        "by_category": by_category(month_txns),
        "trend": monthly_trend(txns, y, m),
        "daily": daily_spend(month_txns, m_start, today if m_start <= today < m_end else m_end),
        "top_merchants": top_merchants(month_txns),
        "budgets": budget_status(user.id, month_txns),
        "recurring": detect_recurring(txns, today),
        "anomalies": detect_anomalies(txns, y, m),
        "goals": [g.to_dict() for g in Goal.query.filter_by(user_id=user.id).order_by(Goal.id).all()],
        "has_data": bool(txns),
    }
    if user.profile_type == "employee":
        data["profile"] = employee_block(user, txns, month_txns, today)
    elif user.profile_type == "freelancer":
        data["profile"] = freelancer_block(user, txns, month_txns, y, m)
    else:
        data["profile"] = student_block(user, txns, today)
    return data
