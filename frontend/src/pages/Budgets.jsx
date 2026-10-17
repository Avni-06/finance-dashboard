import { useState } from "react";
import { PiggyBank, Plus, Trash2, Wand2 } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../lib/useFetch";
import { api } from "../lib/api";
import { money, currentMonth } from "../lib/format";
import { Panel, EmptyState, ProgressBar, StatusLabel, Skeleton, Field, ErrorNote } from "../components/ui";
import MonthPicker from "../components/MonthPicker";
import Modal from "../components/Modal";

function BudgetDialog({ open, onClose, onSaved, categories, initial }) {
  // Mounted fresh each time the dialog opens, so initial state is enough
  const [category, setCategory] = useState(initial?.category || categories[0] || "");
  const [limit, setLimit] = useState(initial ? String(initial.limit) : "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const save = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await api.put("/budgets/", { category, monthly_limit: Number(limit) });
      toast.success(`Budget for ${category} saved`);
      onSaved(); onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={initial ? `Edit ${initial.category} budget` : "New budget"}>
      <form onSubmit={save} className="space-y-4">
        {!initial && (
          <Field label="Category" htmlFor="b-cat">
            <select id="b-cat" className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
        )}
        <Field label="Monthly limit (₹)" htmlFor="b-limit" hint="You'll get a warning at 80% and an alert when you cross it.">
          <input id="b-limit" className="input num" type="number" min="1" step="1" required value={limit} onChange={(e) => setLimit(e.target.value)} />
        </Field>
        {error && <p className="text-sm text-bad" role="alert">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Save budget"}</button>
        </div>
      </form>
    </Modal>
  );
}

export default function Budgets() {
  const { user, isDemo } = useAuth();
  const [month, setMonth] = useState(currentMonth());
  const [dialog, setDialog] = useState(null); // null | "new" | budget
  const { data, error, loading, reload } = useFetch(`/budgets/?month=${month}`);

  const applyTemplate = async () => {
    try {
      await api.post("/budgets/template");
      toast.success("Suggested budgets applied");
      reload();
    } catch (e) {
      toast.error(e.message);
    }
  };

  const remove = async (b) => {
    if (!window.confirm(`Remove the ${b.category} budget?`)) return;
    try {
      await api.del(`/budgets/${b.id}`);
      toast.success("Budget removed");
      reload();
    } catch (e) {
      toast.error(e.message);
    }
  };

  const total = data && data.total_limit ? (data.total_spent / data.total_limit) * 100 : 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Budgets</h1>
          <p className="text-sm text-muted mt-1">Monthly limits per category. They reset on the 1st.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <MonthPicker value={month} onChange={setMonth} />
          {!isDemo && (
            <>
              <button className="btn-secondary" onClick={applyTemplate} title={`Uses ${money(user?.monthly_income)} monthly income`}>
                <Wand2 size={16} />Suggest budgets
              </button>
              <button className="btn-primary" onClick={() => setDialog("new")} disabled={!data?.unbudgeted_categories.length}>
                <Plus size={16} />New budget
              </button>
            </>
          )}
        </div>
      </div>

      <ErrorNote error={error} onRetry={reload} />
      {loading && !data && <Skeleton className="h-64 w-full rounded-panel" />}

      {data && data.budgets.length === 0 && (
        <Panel>
          <EmptyState icon={PiggyBank} title="No budgets yet"
            action={!isDemo && <button className="btn-primary" onClick={applyTemplate}><Wand2 size={16} />Suggest budgets for me</button>}>
            FinSight can suggest limits based on your monthly income and what usually works for a {user?.profile_type || "student"}.
          </EmptyState>
        </Panel>
      )}

      {data && data.budgets.length > 0 && (
        <>
          <Panel>
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-sm text-muted">Spent against budgets</p>
                <p className="font-display text-3xl font-bold num mt-1">
                  {money(data.total_spent)} <span className="text-muted text-xl font-semibold">of {money(data.total_limit)}</span>
                </p>
              </div>
              <p className="text-sm text-muted num">{money(Math.max(data.total_limit - data.total_spent, 0))} left this month</p>
            </div>
            <ProgressBar percent={total} status={total >= 100 ? "over" : total >= 80 ? "warning" : "ok"} className="mt-4 h-3" />
          </Panel>

          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {data.budgets.map((b) => (
              <li key={b.id} className="panel p-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold">{b.category}</p>
                    <StatusLabel status={b.status} />
                  </div>
                  {!isDemo && (
                    <div className="flex -mr-2 -mt-1">
                      <button className="btn-ghost h-8 px-2 text-xs" onClick={() => setDialog(b)}>Edit</button>
                      <button className="btn-ghost h-8 w-8 px-0 hover:text-bad" onClick={() => remove(b)} aria-label={`Remove ${b.category} budget`}><Trash2 size={15} /></button>
                    </div>
                  )}
                </div>
                <p className="mt-4 num">
                  <span className="font-display text-2xl font-bold">{money(b.spent)}</span>
                  <span className="text-muted"> / {money(b.limit)}</span>
                </p>
                <ProgressBar percent={b.percent} status={b.status} className="mt-2" />
                <p className={`text-sm mt-2 num ${b.remaining < 0 ? "text-bad font-semibold" : "text-muted"}`}>
                  {b.remaining < 0 ? `Over by ${money(-b.remaining)}` : `${money(b.remaining)} left`}
                </p>
              </li>
            ))}
          </ul>
        </>
      )}

      {dialog && (
        <BudgetDialog
          open
          initial={dialog === "new" ? null : dialog}
          categories={data?.unbudgeted_categories || []}
          onClose={() => setDialog(null)}
          onSaved={reload}
        />
      )}
    </div>
  );
}
