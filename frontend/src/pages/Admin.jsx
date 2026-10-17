import { useEffect, useState } from "react";
import { Search, RefreshCw, Users, ReceiptText, Brain, ChevronLeft, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { useFetch } from "../lib/useFetch";
import { api } from "../lib/api";
import { dateShort, PROFILE_LABELS } from "../lib/format";
import { Panel, Skeleton, ErrorNote } from "../components/ui";
import { useTokens } from "../components/charts";

const SOURCE_NAMES = { rule: "Brand rules", ml: "ML model", user_rule: "User rules", manual: "Set manually", unknown: "Unknown" };

function Stat({ icon: Icon, label, value, sub }) {
  return (
    <div className="panel p-5">
      <p className="text-sm text-muted flex items-center gap-2"><Icon size={15} aria-hidden="true" />{label}</p>
      <p className="font-display text-3xl font-bold num mt-1">{value}</p>
      {sub && <p className="text-xs text-muted mt-1">{sub}</p>}
    </div>
  );
}

function ShareList({ data, names = {} }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
  return (
    <ul className="space-y-3">
      {Object.entries(data).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
        <li key={k}>
          <div className="flex justify-between text-sm"><span>{names[k] || k}</span><span className="num font-semibold">{v} <span className="text-muted font-normal">({Math.round((v / total) * 100)}%)</span></span></div>
          <div className="mt-1 h-2 rounded-full bg-raised"><div className="h-full rounded-full bg-accent" style={{ width: `${(v / total) * 100}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}

function UsersTable() {
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [profile, setProfile] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => { const t = setTimeout(() => setDebounced(q), 300); return () => clearTimeout(t); }, [q]);
  useEffect(() => setPage(1), [debounced, profile]);
  const params = new URLSearchParams({ page: String(page) });
  if (debounced) params.set("q", debounced);
  if (profile) params.set("profile_type", profile);
  const { data, reload } = useFetch(`/admin/users?${params}`);

  const toggle = async (u) => {
    try {
      await api.patch(`/admin/users/${u.id}`, { is_active: !u.is_active });
      toast.success(`${u.email} ${u.is_active ? "deactivated" : "reactivated"}`);
      reload();
    } catch (e) {
      toast.error(e.message);
    }
  };

  return (
    <Panel title="Accounts" subtitle="Admins can manage accounts but can't see anyone's transactions." bodyClass="p-0">
      <div className="flex flex-wrap gap-2 px-5 py-4">
        <div className="relative flex-1 min-w-[12rem]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
          <input className="input pl-9" placeholder="Search by name or email" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search accounts" />
        </div>
        <select className="input w-auto" value={profile} onChange={(e) => setProfile(e.target.value)} aria-label="Profile type">
          <option value="">All profiles</option>
          <option value="student">Students</option>
          <option value="employee">Salaried</option>
          <option value="freelancer">Freelancers</option>
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-left text-muted border-y border-line">
              <th className="font-medium px-5 py-2.5">Account</th>
              <th className="font-medium px-3 py-2.5">Profile</th>
              <th className="font-medium px-3 py-2.5">Joined</th>
              <th className="font-medium px-3 py-2.5">Last login</th>
              <th className="font-medium px-3 py-2.5 text-right">Transactions</th>
              <th className="font-medium px-5 py-2.5 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data?.users.map((u) => (
              <tr key={u.id}>
                <td className="px-5 py-3">
                  <p className="font-medium">{u.name}</p>
                  <p className="text-xs text-muted">{u.email}</p>
                </td>
                <td className="px-3 py-3">
                  {u.role === "user" ? PROFILE_LABELS[u.profile_type] || "Not set" : <span className="chip bg-raised text-muted">{u.role}</span>}
                </td>
                <td className="px-3 py-3 text-muted">{dateShort(u.created_at.slice(0, 10))}</td>
                <td className="px-3 py-3 text-muted">{u.last_login_at ? dateShort(u.last_login_at.slice(0, 10)) : "Never"}</td>
                <td className="px-3 py-3 text-right num">{u.transaction_count}</td>
                <td className="px-5 py-3 text-right">
                  {u.role === "admin" ? <span className="text-muted">Admin</span> : (
                    <button className={`btn h-8 px-3 border ${u.is_active ? "border-line text-muted hover:text-bad hover:border-bad/50" : "border-bad/50 text-bad"}`} onClick={() => toggle(u)}>
                      {u.is_active ? "Deactivate" : "Reactivate"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-line text-sm">
          <span className="text-muted">Page {page} of {data.pages}</span>
          <div className="flex gap-1">
            <button className="btn-secondary h-8 px-2" disabled={page <= 1} onClick={() => setPage(page - 1)} aria-label="Previous page"><ChevronLeft size={16} /></button>
            <button className="btn-secondary h-8 px-2" disabled={page >= data.pages} onClick={() => setPage(page + 1)} aria-label="Next page"><ChevronRight size={16} /></button>
          </div>
        </div>
      )}
    </Panel>
  );
}

export default function Admin() {
  const stats = useFetch("/admin/stats");
  const model = useFetch("/admin/model");
  const t = useTokens();
  const [training, setTraining] = useState(false);

  const retrain = async () => {
    setTraining(true);
    try {
      const r = await api.post("/admin/model/retrain");
      toast.success(`Retrained. Accuracy on unseen merchants: ${(r.metrics.accuracy * 100).toFixed(1)}%`);
      model.reload();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setTraining(false);
    }
  };

  const s = stats.data;
  const m = model.data?.current;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold">Admin</h1>
        <p className="text-sm text-muted mt-1">Platform health, accounts and the categorisation model.</p>
      </div>
      <ErrorNote error={stats.error} onRetry={stats.reload} />
      {!s && stats.loading && <Skeleton className="h-28 w-full rounded-panel" />}

      {s && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={Users} label="Users" value={s.users.total} sub={`${s.users.onboarded} finished setup`} />
            <Stat icon={Users} label="Active this week" value={s.users.active_7d} sub={`${s.users.deactivated} deactivated`} />
            <Stat icon={ReceiptText} label="Transactions" value={s.transactions.total.toLocaleString("en-IN")} sub={`${s.transactions.user_corrections} corrected by users`} />
            <Stat icon={Brain} label="Model accuracy" value={m ? `${(m.accuracy * 100).toFixed(1)}%` : "–"} sub="on merchants it never saw in training" />
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <Panel title="Sign-ups" subtitle="Last 8 weeks" className="lg:col-span-2">
              <div className="h-48" role="img" aria-label="Sign-ups per week">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={s.signups} margin={{ top: 4, right: 0, left: -24, bottom: 0 }}>
                    <CartesianGrid vertical={false} stroke={t.line} strokeOpacity={0.6} />
                    <XAxis dataKey="week" tickFormatter={(w) => dateShort(w)} tickLine={false} axisLine={false} tick={{ fill: t.muted, fontSize: 11 }} />
                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: t.muted, fontSize: 11 }} />
                    <Tooltip cursor={{ fill: t.raised, opacity: 0.6 }}
                      content={({ active, payload }) => active && payload?.length ? (
                        <div className="panel px-3 py-2 text-sm">Week to {dateShort(payload[0].payload.week)}: <b>{payload[0].value}</b></div>
                      ) : null} />
                    <Bar isAnimationActive={false} dataKey="count" fill={t.accent} radius={[4, 4, 0, 0]} maxBarSize={36} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <Panel title="Users by profile">
              <ShareList data={s.users.by_profile} names={PROFILE_LABELS} />
            </Panel>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <Panel title="How transactions get categorised">
              <ShareList data={s.transactions.by_category_source} names={SOURCE_NAMES} />
            </Panel>
            <Panel title="Categorisation model" className="lg:col-span-2"
              action={<button className="btn-secondary h-9" onClick={retrain} disabled={training}>
                <RefreshCw size={15} className={training ? "animate-spin" : ""} />{training ? "Training…" : "Retrain with corrections"}
              </button>}>
              {m ? (
                <>
                  <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                    <div><dt className="text-muted">Accuracy</dt><dd className="font-semibold num text-lg">{(m.accuracy * 100).toFixed(1)}%</dd></div>
                    <div><dt className="text-muted">Macro F1</dt><dd className="font-semibold num text-lg">{m.macro_f1.toFixed(3)}</dd></div>
                    <div><dt className="text-muted">Training rows</dt><dd className="font-semibold num text-lg">{m.n_samples.toLocaleString("en-IN")}</dd></div>
                    <div><dt className="text-muted">User corrections</dt><dd className="font-semibold num text-lg">{m.n_user_corrections} <span className="text-muted text-sm font-normal">/ {model.data.available_corrections} available</span></dd></div>
                  </dl>
                  <p className="text-xs text-muted mt-4">
                    Accuracy is measured on a held-out set of merchants the model never saw (group split), so it reflects real generalisation.
                    Weakest concepts: {Object.entries(m.per_concept_f1).sort((a, b) => a[1] - b[1]).slice(0, 3).map(([k, v]) => `${k.replace("_", " ")} (${v})`).join(", ")}.
                  </p>
                  {model.data.runs.length > 0 && (
                    <table className="w-full text-sm mt-4">
                      <thead><tr className="text-left text-muted border-b border-line"><th className="font-medium py-2">Retrained</th><th className="font-medium py-2 text-right">Accuracy</th><th className="font-medium py-2 text-right">Corrections used</th></tr></thead>
                      <tbody className="divide-y divide-line">
                        {model.data.runs.map((r) => (
                          <tr key={r.id}><td className="py-2">{new Date(r.created_at + "Z").toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</td>
                            <td className="py-2 text-right num">{(r.accuracy * 100).toFixed(1)}%</td><td className="py-2 text-right num">{r.n_user_corrections}</td></tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </>
              ) : <p className="text-sm text-muted">The model trains on first use. Upload a statement or open a demo, then refresh.</p>}
            </Panel>
          </div>

          <UsersTable />
        </>
      )}
    </div>
  );
}
