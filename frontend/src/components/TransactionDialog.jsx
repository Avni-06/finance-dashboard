import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import Modal from "./Modal";
import { Field, Segmented } from "./ui";
import { api } from "../lib/api";
import { todayISO } from "../lib/format";

const EMPTY = { type: "expense", description: "", amount: "", date: todayISO(), category: "", note: "" };

/** Add (tx = null) or edit (tx = object) a transaction. */
export default function TransactionDialog({ open, onClose, onSaved, tx, categories }) {
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const editing = Boolean(tx);

  useEffect(() => {
    if (!open) return;
    setError("");
    setForm(tx ? {
      type: tx.type, description: tx.description, amount: String(tx.amount), date: tx.date,
      category: tx.category || "", note: tx.note || "",
    } : { ...EMPTY, date: todayISO() });
  }, [open, tx]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target ? e.target.value : e }));
  const options = categories?.[form.type] || [];

  const save = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    const body = { ...form, amount: Number(form.amount) };
    if (!body.category) delete body.category; // let the classifier pick
    try {
      if (editing) {
        const r = await api.patch(`/transactions/${tx.id}`, body);
        toast.success(r.similar_updated
          ? `Saved. ${r.similar_updated} similar transaction${r.similar_updated > 1 ? "s" : ""} updated too`
          : "Transaction saved");
      } else {
        const r = await api.post("/transactions/", body);
        toast.success(`Added to ${r.transaction.category}`);
      }
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={editing ? "Edit transaction" : "Add transaction"}>
      <form onSubmit={save} className="space-y-4">
        <Segmented
          label="Transaction type"
          value={form.type}
          onChange={(v) => setForm((f) => ({ ...f, type: v, category: "" }))}
          options={[{ value: "expense", label: "Money out" }, { value: "income", label: "Money in" }]}
        />
        <Field label="Description" htmlFor="tx-desc">
          <input id="tx-desc" className="input" required maxLength={255} value={form.description}
            onChange={set("description")} placeholder={form.type === "expense" ? "e.g. Canteen lunch" : "e.g. Pocket money from Papa"} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Amount (₹)" htmlFor="tx-amount">
            <input id="tx-amount" className="input num" required type="number" min="0.01" step="0.01"
              inputMode="decimal" value={form.amount} onChange={set("amount")} />
          </Field>
          <Field label="Date" htmlFor="tx-date">
            <input id="tx-date" className="input" required type="date" max={todayISO()} value={form.date} onChange={set("date")} />
          </Field>
        </div>
        <Field label="Category" htmlFor="tx-cat" hint={!editing && !form.category ? "Leave on auto and FinSight will pick one." : editing ? "Changing it also teaches FinSight for this merchant." : null}>
          <select id="tx-cat" className="input" value={form.category} onChange={set("category")}>
            {!editing && <option value="">Auto-detect</option>}
            {options.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="Note (optional)" htmlFor="tx-note">
          <input id="tx-note" className="input" maxLength={255} value={form.note} onChange={set("note")} placeholder="e.g. split with Riya" />
        </Field>
        {error && <p className="text-sm text-bad" role="alert">{error}</p>}
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : editing ? "Save changes" : "Add transaction"}</button>
        </div>
      </form>
    </Modal>
  );
}
