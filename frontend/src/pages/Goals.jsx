import { useState } from "react";
import { Target, Plus, Trash2, CheckCircle2 } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../lib/useFetch";
import { api } from "../lib/api";
import { money, dateLong, todayISO } from "../lib/format";
import { Panel, EmptyState, ProgressBar, Skeleton, Field, ErrorNote } from "../components/ui";
import Modal from "../components/Modal";

function monthsUntil(iso) {
  const d = new Date(`${iso}T00:00:00`);
  const now = new Date();
  return Math.max((d.getFullYear() - now.getFullYear()) * 12 + d.getMonth() - now.getMonth(), 1);
}

function GoalDialog({ onClose, onSaved }) {
  const [form, setForm] = useState({ name: "", target_amount: "", saved_amount: "", deadline: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const save = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await api.post("/goals/", {
        name: form.name, target_amount: Number(form.target_amount),
        saved_amount: Number(form.saved_amount || 0), deadline: form.deadline || null,
      });
      toast.success("Goal created");
      onSaved(); onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open onClose={onClose} title="New savings goal">
      <form onSubmit={save} className="space-y-4">
        <Field label="What are you saving for?" htmlFor="g-name">
          <input id="g-name" className="input" required minLength={2} maxLength={80} value={form.name} onChange={set("name")} placeholder="e.g. New laptop" />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Target (₹)" htmlFor="g-target">
            <input id="g-target" className="input num" type="number" min="1" required value={form.target_amount} onChange={set("target_amount")} />
          </Field>
          <Field label="Saved so far (₹)" htmlFor="g-saved">
            <input id="g-saved" className="input num" type="number" min="0" value={form.saved_amount} onChange={set("saved_amount")} />
          </Field>
        </div>
        <Field label="Target date (optional)" htmlFor="g-date">
          <input id="g-date" className="input" type="date" min={todayISO()} value={form.deadline} onChange={set("deadline")} />
        </Field>
        {error && <p className="text-sm text-bad" role="alert">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={busy}>{busy ? "Creating…" : "Create goal"}</button>
        </div>
      </form>
    </Modal>
  );
}

function GoalCard({ goal, readOnly, onChanged }) {
  const [amount, setAmount] = useState("");
  const done = goal.saved_amount >= goal.target_amount;
  const remaining = Math.max(goal.target_amount - goal.saved_amount, 0);
  const perMonth = goal.deadline && !done ? remaining / monthsUntil(goal.deadline) : null;

  const add = async (e) => {
    e.preventDefault();
    if (!Number(amount)) return;
    try {
      await api.patch(`/goals/${goal.id}`, { add_amount: Number(amount) });
      toast.success(`Added ${money(amount)} to ${goal.name}`);
      setAmount("");
      onChanged();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete the goal "${goal.name}"?`)) return;
    try {
      await api.del(`/goals/${goal.id}`);
      toast.success("Goal deleted");
      onChanged();
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <li className="panel p-5 flex flex-col">
      <div className="flex items-start justify-between gap-2">
        <p className="font-semibold flex items-center gap-2">
          {done ? <CheckCircle2 size={17} className="text-good" aria-hidden="true" /> : <Target size={17} className="text-accent" aria-hidden="true" />}
          {goal.name}
        </p>
        {!readOnly && (
          <button className="btn-ghost h-8 w-8 px-0 -mr-2 -mt-1 hover:text-bad" onClick={remove} aria-label={`Delete ${goal.name}`}><Trash2 size={15} /></button>
        )}
      </div>
      <p className="mt-4 num">
        <span className="font-display text-2xl font-bold">{money(goal.saved_amount)}</span>
        <span className="text-muted"> / {money(goal.target_amount)}</span>
      </p>
      <ProgressBar percent={goal.progress} status="ok" className="mt-2" />
      <p className="text-sm text-muted mt-2">
        {done ? "Goal reached. Nice work."
          : perMonth ? `Save ${money(perMonth)}/month to make it by ${dateLong(goal.deadline)}.`
          : `${money(remaining)} to go.`}
      </p>
      {!readOnly && !done && (
        <form onSubmit={add} className="flex gap-2 mt-4 pt-4 border-t border-line">
          <input className="input num h-9" type="number" min="1" placeholder="Amount" value={amount}
            onChange={(e) => setAmount(e.target.value)} aria-label={`Amount to add to ${goal.name}`} />
          <button className="btn-secondary h-9">Add money</button>
        </form>
      )}
    </li>
  );
}

export default function Goals() {
  const { isDemo } = useAuth();
  const [open, setOpen] = useState(false);
  const { data, error, loading, reload } = useFetch("/goals/");

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Savings goals</h1>
          <p className="text-sm text-muted mt-1">A laptop, a trip, fees for next semester. Track each one separately.</p>
        </div>
        {!isDemo && <button className="btn-primary" onClick={() => setOpen(true)}><Plus size={16} />New goal</button>}
      </div>
      <ErrorNote error={error} onRetry={reload} />
      {loading && !data && <Skeleton className="h-48 w-full rounded-panel" />}
      {data && !data.goals.length && (
        <Panel>
          <EmptyState icon={Target} title="No goals yet"
            action={!isDemo && <button className="btn-primary" onClick={() => setOpen(true)}><Plus size={16} />Create your first goal</button>}>
            Set a target and FinSight tells you how much to put away each month.
          </EmptyState>
        </Panel>
      )}
      {data?.goals.length > 0 && (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {data.goals.map((g) => <GoalCard key={g.id} goal={g} readOnly={isDemo} onChanged={reload} />)}
        </ul>
      )}
      {open && <GoalDialog onClose={() => setOpen(false)} onSaved={reload} />}
    </div>
  );
}
