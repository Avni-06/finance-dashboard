import { Flame, GraduationCap, Wallet, Landmark, Users, Receipt } from "lucide-react";
import { Panel, ProgressBar } from "./ui";
import RunwayTrack from "./RunwayTrack";
import { money } from "../lib/format";

/* ---------------- Student ---------------- */
export function StudentHero({ profile, showRunway }) {
  return showRunway ? (
    <Panel title="Money runway" subtitle="How long this month's allowance lasts at your current pace" bodyClass="p-5 pt-4">
      <RunwayTrack cycle={profile.cycle} incomeLabel="allowance" />
    </Panel>
  ) : null;
}

export function StudentExtras({ profile }) {
  const streak = profile.no_spend_streak;
  return (
    <div className="grid gap-5 md:grid-cols-3">
      <Panel title="No-spend streak">
        <div className="flex items-center gap-4">
          <span className={`grid place-items-center h-12 w-12 rounded-full ${streak ? "bg-accent/15 text-accent" : "bg-raised text-muted"}`}>
            <Flame size={22} aria-hidden="true" />
          </span>
          <div>
            <p className="font-display text-3xl font-bold num">{streak} {streak === 1 ? "day" : "days"}</p>
            <p className="text-sm text-muted">
              {streak ? "without food, shopping or fun spends. Keep it going." : "Skip non-essentials today to start one."}
            </p>
          </div>
        </div>
      </Panel>

      <Panel title="Semester costs" subtitle="Fees, books and events in the last 6 months, kept out of your daily budget">
        {profile.semester_spend.length ? (
          <>
            <p className="font-display text-2xl font-bold num">{money(profile.semester_total)}</p>
            <ul className="mt-3 space-y-1.5 text-sm">
              {profile.semester_spend.map((s) => (
                <li key={s.category} className="flex justify-between gap-2">
                  <span className="flex items-center gap-2 text-muted"><GraduationCap size={14} aria-hidden="true" />{s.category}</span>
                  <span className="font-semibold num">{money(s.amount)}</span>
                </li>
              ))}
            </ul>
          </>
        ) : <p className="text-sm text-muted">No fees, books or event payments yet.</p>}
      </Panel>

      <Panel title="Where your money comes from" subtitle="Last 6 months">
        {profile.income_sources.length ? (
          <ul className="space-y-2.5 text-sm">
            {profile.income_sources.map((s) => {
              const total = profile.income_sources.reduce((a, b) => a + b.amount, 0) || 1;
              return (
                <li key={s.source}>
                  <div className="flex justify-between gap-2">
                    <span className="flex items-center gap-2"><Wallet size={14} className="text-income" aria-hidden="true" />{s.source}</span>
                    <span className="font-semibold num">{money(s.amount)}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-raised">
                    <div className="h-full rounded-full bg-income" style={{ width: `${(s.amount / total) * 100}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        ) : <p className="text-sm text-muted">Add your allowance, scholarship or stipend to see this.</p>}
      </Panel>
    </div>
  );
}

/* ---------------- Employee ---------------- */
function SplitRow({ label, hint, part }) {
  const over = label === "Savings" ? part.percent < part.target : part.percent > part.target;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span><span className="font-semibold">{label}</span> <span className="text-muted">{hint}</span></span>
        <span className="num">
          <span className={`font-semibold ${over ? "text-warn" : ""}`}>{part.percent}%</span>
          <span className="text-muted"> / {part.target}%</span>
        </span>
      </div>
      <div className="relative mt-1.5 h-2 rounded-full bg-raised">
        <div className={`h-full rounded-full ${over ? "bg-warn" : "bg-good"}`} style={{ width: `${Math.min(part.percent, 100)}%` }} />
        <div className="absolute -top-1 -bottom-1 w-0.5 bg-ink/70" style={{ left: `${part.target}%` }} title={`Target ${part.target}%`} />
      </div>
      <p className="text-xs text-muted mt-1 num">{money(part.amount)}</p>
    </div>
  );
}

export function EmployeeHero({ profile, showRunway }) {
  const r = profile.rule_50_30_20;
  return (
    <div className="grid gap-5 lg:grid-cols-5">
      {showRunway && (
        <Panel title="Until payday" subtitle="Rent, EMI and SIP are already counted" className="lg:col-span-3">
          <RunwayTrack cycle={profile.cycle} incomeLabel="salary" />
        </Panel>
      )}
      <Panel title="50/30/20 check" subtitle={`Of ${money(r.income)} income this month`} className={showRunway ? "lg:col-span-2" : "lg:col-span-5"}>
        <div className="space-y-4">
          <SplitRow label="Needs" hint="rent, bills, EMI, groceries" part={r.needs} />
          <SplitRow label="Wants" hint="food out, shopping, fun" part={r.wants} />
          <SplitRow label="Savings" hint="SIPs + what's left" part={r.savings} />
        </div>
      </Panel>
    </div>
  );
}

export function EmployeeExtras({ profile }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Panel title="EMI load">
        <div className="flex items-center gap-4">
          <span className="grid place-items-center h-12 w-12 rounded-full bg-raised text-muted"><Landmark size={22} aria-hidden="true" /></span>
          <div>
            <p className="font-display text-3xl font-bold num">{profile.emi_to_income}%</p>
            <p className="text-sm text-muted">of income goes to EMIs ({money(profile.emi_this_month)} this month). Under 30% is healthy.</p>
          </div>
        </div>
      </Panel>
      <Panel title="Emergency fund target" subtitle="6 months of your average spending">
        <p className="font-display text-3xl font-bold num">{money(profile.emergency_fund_target)}</p>
        <p className="text-sm text-muted mt-1">Based on an average monthly spend of {money(profile.avg_monthly_expense)}.</p>
      </Panel>
    </div>
  );
}

/* ---------------- Freelancer ---------------- */
export function FreelancerHero({ profile }) {
  const vol = profile.income_volatility;
  return (
    <div className="grid gap-5 md:grid-cols-3">
      <Panel title="Average month" subtitle="Income over the last 6 months">
        <p className="font-display text-4xl font-bold num">{money(profile.avg_monthly_income)}</p>
        <p className="text-sm text-muted mt-2">Leanest month: <span className="text-ink font-semibold num">{money(profile.lean_month_income)}</span></p>
      </Panel>
      <Panel title="Income swings" subtitle="How much months differ from the average">
        <p className={`font-display text-4xl font-bold num ${vol > 40 ? "text-warn" : ""}`}>{vol ?? "–"}{vol !== null && "%"}</p>
        <p className="text-sm text-muted mt-2">
          {vol > 40 ? "Big swings. Keep 2–3 months of expenses as a buffer." : "Fairly steady income."}
          {profile.buffer_months !== null && ` This month covers ${profile.buffer_months}× your spending.`}
        </p>
      </Panel>
      <Panel title="Tax set-aside" subtitle={`${Math.round(profile.tax_rate * 100)}% of this month's income`}>
        <p className="font-display text-4xl font-bold num">{money(profile.tax_set_aside)}</p>
        <p className="text-sm text-muted mt-2">Paid this month: <span className="text-ink font-semibold num">{money(profile.taxes_paid_this_month)}</span></p>
      </Panel>
    </div>
  );
}

export function FreelancerExtras({ profile }) {
  const max = Math.max(...profile.top_clients.map((c) => c.amount), 1);
  return (
    <Panel title="Top clients" subtitle="Payments received, last 6 months">
      {profile.top_clients.length ? (
        <ul className="space-y-3">
          {profile.top_clients.map((c) => (
            <li key={c.client}>
              <div className="flex justify-between text-sm gap-2">
                <span className="flex items-center gap-2"><Users size={14} className="text-muted" aria-hidden="true" />{c.client}</span>
                <span className="font-semibold num">{money(c.amount)}</span>
              </div>
              <div className="mt-1.5 h-2 rounded-full bg-raised">
                <div className="h-full rounded-full bg-income" style={{ width: `${(c.amount / max) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
      ) : <p className="text-sm text-muted flex items-center gap-2"><Receipt size={14} />Client payments will show up here.</p>}
    </Panel>
  );
}

export { ProgressBar };
