import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Upload, Plus, CalendarClock, TrendingUp, FileSpreadsheet, Target } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../lib/useFetch";
import { money, pct, currentMonth, dateShort } from "../lib/format";
import { Panel, EmptyState, Skeleton, ProgressBar, StatusLabel, ErrorNote } from "../components/ui";
import { TrendChart, CategoryBars, DailyChart } from "../components/charts";
import MonthPicker from "../components/MonthPicker";
import UploadDialog from "../components/UploadDialog";
import TransactionDialog from "../components/TransactionDialog";
import {
  StudentHero, StudentExtras, EmployeeHero, EmployeeExtras, FreelancerHero, FreelancerExtras,
} from "../components/ProfilePanels";

function greeting(name) {
  const h = new Date().getHours();
  const part = h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  return `${part}, ${(name || "").split(" ")[0]}`;
}

function SummaryStrip({ summary, running }) {
  const cells = [
    { label: "Money in", value: money(summary.income), change: summary.income_change, good: (c) => c >= 0 },
    { label: "Money out", value: money(summary.expense), change: summary.expense_change, good: (c) => c <= 0 },
    { label: "Net saved", value: money(summary.net), tone: summary.net < 0 ? "text-bad" : "" },
    { label: "Savings rate", value: summary.savings_rate === null ? "–" : `${summary.savings_rate}%` },
  ];
  return (
    <div className="panel grid grid-cols-2 lg:grid-cols-4 divide-line [&>*]:border-line">
      {cells.map((c, i) => (
        <div key={c.label} className={`p-5 ${i % 2 ? "border-l" : ""} ${i > 1 ? "border-t lg:border-t-0" : ""} ${i === 2 ? "lg:border-l" : ""}`}>
          <p className="text-sm text-muted">{c.label}</p>
          <p className={`font-display text-2xl sm:text-[1.75rem] font-bold num mt-1 ${c.tone || ""}`}>{c.value}</p>
          {c.change !== undefined && c.change !== null && (
            <p className={`text-xs mt-1 font-semibold ${c.good(c.change) ? "text-good" : "text-bad"}`}>
              {pct(c.change)} <span className="text-muted font-normal">{running ? "vs same point last month" : "vs last month"}</span>
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-5">
      <Skeleton className="h-48 w-full rounded-panel" />
      <Skeleton className="h-28 w-full rounded-panel" />
      <div className="grid gap-5 lg:grid-cols-3">
        <Skeleton className="h-72 lg:col-span-2 rounded-panel" />
        <Skeleton className="h-72 rounded-panel" />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user, isDemo } = useAuth();
  const navigate = useNavigate();
  const [month, setMonth] = useState(currentMonth());
  const [uploadOpen, setUploadOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const { data, error, loading, reload } = useFetch(`/dashboard/?month=${month}`);
  const cats = useFetch("/transactions/categories");
  const running = month === currentMonth();
  const ptype = user?.profile_type || "student";

  const actions = !isDemo && (
    <div className="flex gap-2">
      <button className="btn-secondary" onClick={() => setUploadOpen(true)}><Upload size={16} />Import CSV</button>
      <button className="btn-primary" onClick={() => setAddOpen(true)}><Plus size={16} />Add</button>
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">{greeting(user?.name)}</h1>
          <p className="text-muted text-sm mt-1">Here's where your money stands.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <MonthPicker value={month} onChange={setMonth} />
          {actions}
        </div>
      </div>

      <ErrorNote error={error} onRetry={reload} />
      {loading && !data && <DashboardSkeleton />}

      {data && !data.has_data && (
        <Panel>
          <EmptyState
            icon={FileSpreadsheet}
            title="Let's get your first transactions in"
            action={!isDemo && (
              <div className="flex flex-wrap justify-center gap-2">
                <button className="btn-primary" onClick={() => setUploadOpen(true)}><Upload size={16} />Import bank statement</button>
                <button className="btn-secondary" onClick={() => setAddOpen(true)}><Plus size={16} />Add one manually</button>
              </div>
            )}
          >
            Import a CSV from your bank or UPI app and FinSight sorts every payment into categories.
            No statement handy? <a className="underline font-semibold text-ink" href="/sample-statement.csv" download>Download a sample</a> and import it.
          </EmptyState>
        </Panel>
      )}

      {data?.has_data && (
        <>
          {ptype === "student" && <StudentHero profile={data.profile} showRunway={running} />}
          {ptype === "employee" && <EmployeeHero profile={data.profile} showRunway={running} />}
          {ptype === "freelancer" && <FreelancerHero profile={data.profile} />}

          <SummaryStrip summary={data.summary} running={running} />

          <div className="grid gap-5 lg:grid-cols-5">
            <Panel title="Last 6 months" className="lg:col-span-3">
              <TrendChart data={data.trend} />
            </Panel>
            <Panel title="Where it went" subtitle="Spending by category" className="lg:col-span-2">
              {data.by_category.length ? (
                <CategoryBars rows={data.by_category} onSelect={(c) => navigate(`/app/transactions?category=${encodeURIComponent(c)}&month=${month}`)} />
              ) : <p className="text-sm text-muted">No spending this month.</p>}
            </Panel>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <Panel title="Budgets" action={<Link to="/app/budgets" className="text-sm font-semibold text-muted hover:text-ink">Manage</Link>}>
              {data.budgets.length ? (
                <ul className="space-y-4">
                  {[...data.budgets].sort((a, b) => b.percent - a.percent).slice(0, 4).map((b) => (
                    <li key={b.id}>
                      <div className="flex justify-between text-sm gap-2">
                        <span className="font-medium truncate">{b.category}</span>
                        <span className="num text-muted shrink-0"><span className="text-ink font-semibold">{money(b.spent)}</span> / {money(b.limit)}</span>
                      </div>
                      <ProgressBar percent={b.percent} status={b.status} className="mt-1.5" />
                      {b.status !== "ok" && <div className="mt-1"><StatusLabel status={b.status} /></div>}
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-muted">No budgets yet. <Link to="/app/budgets" className="underline text-ink">Set one up</Link> to get alerts at 80%.</p>}
            </Panel>

            <Panel title="Coming up" subtitle="Recurring payments FinSight spotted">
              {data.recurring.length ? (
                <ul className="divide-y divide-line -my-2">
                  {data.recurring.slice(0, 5).map((r) => (
                    <li key={r.merchant} className="flex items-center gap-3 py-2.5">
                      <CalendarClock size={16} className="text-muted shrink-0" aria-hidden="true" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{r.merchant}</p>
                        <p className="text-xs text-muted">
                          {r.days_until < 0 ? `Was due ${dateShort(r.next_date)}` : r.days_until === 0 ? "Due today" : `${dateShort(r.next_date)}, in ${r.days_until} day${r.days_until > 1 ? "s" : ""}`}
                        </p>
                      </div>
                      <span className="text-sm font-semibold num">{money(r.amount)}</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-muted">Subscriptions, rent and EMIs show up here after 3 months of history.</p>}
            </Panel>

            <Panel title="Unusual spending" subtitle={running ? "Compared with your usual by this day of the month" : "Compared with the previous 3 months"}>
              {data.anomalies.length ? (
                <ul className="space-y-3">
                  {data.anomalies.map((a) => (
                    <li key={a.category} className="flex gap-3">
                      <TrendingUp size={18} className="text-warn shrink-0 mt-0.5" aria-hidden="true" />
                      <p className="text-sm">
                        <span className="font-semibold">{a.category}</span> is at <span className="num font-semibold">{money(a.amount)}</span>,{" "}
                        <span className="text-warn font-semibold">{a.ratio}×</span> your usual {money(a.usual)}.
                      </p>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-muted">Nothing out of the ordinary. Spending looks like your usual pattern.</p>}
            </Panel>
          </div>

          {ptype === "student" && <StudentExtras profile={data.profile} />}
          {ptype === "employee" && <EmployeeExtras profile={data.profile} />}

          <div className="grid gap-5 lg:grid-cols-5">
            <Panel title="Daily spending" className="lg:col-span-3">
              <DailyChart data={data.daily} />
            </Panel>
            {ptype === "freelancer" ? (
              <div className="lg:col-span-2"><FreelancerExtras profile={data.profile} /></div>
            ) : (
              <Panel title="Top merchants" className="lg:col-span-2">
                {data.top_merchants.length ? (
                  <ul className="divide-y divide-line -my-2">
                    {data.top_merchants.map((m) => (
                      <li key={m.merchant} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                        <div className="min-w-0">
                          <p className="font-medium truncate">{m.merchant}</p>
                          <p className="text-xs text-muted">{m.category}, {m.count} payment{m.count > 1 ? "s" : ""}</p>
                        </div>
                        <span className="font-semibold num">{money(m.amount)}</span>
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-sm text-muted">No spending this month.</p>}
              </Panel>
            )}
          </div>

          {data.goals.length > 0 && (
            <Panel title="Savings goals" action={<Link to="/app/goals" className="text-sm font-semibold text-muted hover:text-ink">All goals</Link>}>
              <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {data.goals.slice(0, 3).map((g) => (
                  <li key={g.id}>
                    <div className="flex items-center gap-2 text-sm font-medium"><Target size={15} className="text-accent" aria-hidden="true" />{g.name}</div>
                    <ProgressBar percent={g.progress} status="ok" className="mt-2" />
                    <p className="text-xs text-muted mt-1 num">{money(g.saved_amount)} of {money(g.target_amount)} ({g.progress}%)</p>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} onDone={reload} />
      <TransactionDialog open={addOpen} onClose={() => setAddOpen(false)} onSaved={reload} categories={cats.data} />
    </div>
  );
}
