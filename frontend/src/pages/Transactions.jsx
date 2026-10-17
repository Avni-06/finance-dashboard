import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Upload, Plus, Download, Pencil, Trash2, ReceiptText, ChevronLeft, ChevronRight, Sparkles } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../lib/useFetch";
import { api } from "../lib/api";
import { money, dateShort, currentMonth } from "../lib/format";
import { Panel, EmptyState, Skeleton, Segmented, ErrorNote } from "../components/ui";
import MonthPicker from "../components/MonthPicker";
import UploadDialog from "../components/UploadDialog";
import TransactionDialog from "../components/TransactionDialog";

function useDebounced(value, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

const SOURCE_HINT = {
  rule: "Matched a known merchant",
  user_rule: "Your rule for this merchant",
  ml: "Guessed by the ML model",
  manual: "Set by you",
};

function CategoryCell({ tx, categories, disabled, onChange }) {
  const review = tx.category_source === "ml" && tx.confidence < 0.6;
  const options = categories?.[tx.type] || [tx.category];
  return (
    <div className="flex items-center gap-2">
      <select
        aria-label={`Category for ${tx.description}`}
        disabled={disabled}
        value={tx.category || ""}
        onChange={(e) => onChange(tx, e.target.value)}
        title={`${SOURCE_HINT[tx.category_source] || ""}${tx.confidence ? ` (${Math.round(tx.confidence * 100)}% sure)` : ""}`}
        className="h-8 max-w-[11rem] rounded-md bg-raised border border-line px-2 text-xs font-semibold text-ink focus:border-accent focus:outline-none disabled:opacity-100 disabled:appearance-none"
      >
        {options.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      {review && <span className="chip bg-warn/15 text-warn" title="Low confidence, please check">Review</span>}
    </div>
  );
}

export default function Transactions() {
  const { isDemo } = useAuth();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const [month, setMonth] = useState(params.get("month") || currentMonth());
  const [allTime, setAllTime] = useState(params.get("all") === "1");
  const [type, setType] = useState(params.get("type") || "");
  const [category, setCategory] = useState(params.get("category") || "");
  const [review, setReview] = useState(params.get("review") === "1");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const debouncedQ = useDebounced(q);

  const query = useMemo(() => {
    const p = new URLSearchParams({ page: String(page), per_page: "25" });
    if (debouncedQ) p.set("q", debouncedQ);
    if (!allTime) p.set("month", month);
    if (type) p.set("type", type);
    if (category) p.set("category", category);
    if (review) p.set("review", "1");
    return p.toString();
  }, [page, debouncedQ, allTime, month, type, category, review]);

  useEffect(() => { setPage(1); }, [debouncedQ, allTime, month, type, category, review]);
  useEffect(() => {
    const p = new URLSearchParams();
    if (debouncedQ) p.set("q", debouncedQ);
    if (allTime) p.set("all", "1"); else p.set("month", month);
    if (type) p.set("type", type);
    if (category) p.set("category", category);
    if (review) p.set("review", "1");
    setParams(p, { replace: true });
  }, [debouncedQ, allTime, month, type, category, review, setParams]);

  const { data, error, loading, reload } = useFetch(`/transactions/?${query}`);
  const cats = useFetch("/transactions/categories");
  const allCategories = cats.data ? [...cats.data.expense, ...cats.data.income] : [];

  const changeCategory = async (tx, value) => {
    try {
      const r = await api.patch(`/transactions/${tx.id}`, { category: value });
      toast.success(r.similar_updated
        ? `Moved to ${value}. ${r.similar_updated} similar transaction${r.similar_updated > 1 ? "s" : ""} updated, and future ones will follow.`
        : `Moved to ${value}`);
      reload();
    } catch (e) {
      toast.error(e.message);
    }
  };

  const remove = async (tx) => {
    if (!window.confirm(`Delete "${tx.description}"?`)) return;
    try {
      await api.del(`/transactions/${tx.id}`);
      toast.success("Transaction deleted");
      reload();
    } catch (e) {
      toast.error(e.message);
    }
  };

  const exportCsv = () => api.download(`/transactions/export?${query}`, "finsight-transactions.csv")
    .catch((e) => toast.error(e.message));

  const rows = data?.transactions || [];
  const filtersActive = debouncedQ || type || category || review;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Transactions</h1>
          {data && (
            <p className="text-sm text-muted mt-1 num">
              {data.total} transaction{data.total === 1 ? "" : "s"}, <span className="text-income font-semibold">{money(data.summary.income)}</span> in,{" "}
              <span className="text-expense font-semibold">{money(data.summary.expense)}</span> out
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={exportCsv}><Download size={16} />Export</button>
          {!isDemo && <button className="btn-secondary" onClick={() => setUploadOpen(true)}><Upload size={16} />Import CSV</button>}
          {!isDemo && <button className="btn-primary" onClick={() => setAddOpen(true)}><Plus size={16} />Add</button>}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[14rem]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
          <input className="input pl-9" placeholder="Search description, merchant or note" value={q}
            onChange={(e) => setQ(e.target.value)} aria-label="Search transactions" />
        </div>
        {allTime ? (
          <button className="btn-secondary" onClick={() => setAllTime(false)}>All time</button>
        ) : (
          <MonthPicker value={month} onChange={setMonth} />
        )}
        {!allTime && <button className="btn-ghost" onClick={() => setAllTime(true)}>Show all time</button>}
        <Segmented label="Type" value={type} onChange={setType}
          options={[{ value: "", label: "All" }, { value: "expense", label: "Out" }, { value: "income", label: "In" }]} />
        <select className="input w-auto" value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
          <option value="">All categories</option>
          {allCategories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <button
          className={`btn h-10 border ${review ? "border-warn bg-warn/15 text-warn" : "border-line text-muted hover:text-ink"}`}
          onClick={() => setReview((r) => !r)} aria-pressed={review}
        >
          <Sparkles size={15} />Needs review
        </button>
      </div>

      <ErrorNote error={error} onRetry={reload} />

      <Panel bodyClass="p-0">
        {loading && !data ? (
          <div className="p-5 space-y-3">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : rows.length === 0 ? (
          <EmptyState icon={ReceiptText} title={filtersActive ? "No transactions match these filters" : "No transactions in this period"}
            action={filtersActive
              ? <button className="btn-secondary" onClick={() => { setQ(""); setType(""); setCategory(""); setReview(false); }}>Clear filters</button>
              : !isDemo && <button className="btn-primary" onClick={() => setUploadOpen(true)}><Upload size={16} />Import CSV</button>}
          >
            {review && !debouncedQ ? "Every transaction was categorised confidently." : null}
          </EmptyState>
        ) : (
          <>
            {/* Desktop table */}
            <table className="hidden md:table w-full text-sm">
              <thead>
                <tr className="text-left text-muted border-b border-line">
                  <th className="font-medium px-5 py-3 w-24">Date</th>
                  <th className="font-medium px-3 py-3">Description</th>
                  <th className="font-medium px-3 py-3">Category</th>
                  <th className="font-medium px-3 py-3 text-right">Amount</th>
                  {!isDemo && <th className="px-3 py-3 w-20"><span className="sr-only">Actions</span></th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {rows.map((tx) => (
                  <tr key={tx.id} className="hover:bg-raised/40">
                    <td className="px-5 py-3 text-muted whitespace-nowrap">{dateShort(tx.date)}</td>
                    <td className="px-3 py-3 max-w-0 w-full">
                      <p className="font-medium truncate">{tx.merchant ? tx.merchant.replace(/\b\w+/g, (w) => w[0] + w.slice(1).toLowerCase()) : tx.description}</p>
                      <p className="text-xs text-muted truncate" title={tx.description}>{tx.note || tx.description}</p>
                    </td>
                    <td className="px-3 py-3"><CategoryCell tx={tx} categories={cats.data} disabled={isDemo} onChange={changeCategory} /></td>
                    <td className={`px-3 py-3 text-right font-semibold num whitespace-nowrap ${tx.type === "income" ? "text-income" : ""}`}>
                      {tx.type === "income" ? "+" : "−"}{money(tx.amount, { precise: true })}
                    </td>
                    {!isDemo && (
                      <td className="px-3 py-3 whitespace-nowrap">
                        <button className="btn-ghost h-8 w-8 px-0" onClick={() => setEditing(tx)} aria-label={`Edit ${tx.description}`}><Pencil size={15} /></button>
                        <button className="btn-ghost h-8 w-8 px-0 hover:text-bad" onClick={() => remove(tx)} aria-label={`Delete ${tx.description}`}><Trash2 size={15} /></button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Mobile list */}
            <ul className="md:hidden divide-y divide-line">
              {rows.map((tx) => (
                <li key={tx.id} className="p-4 space-y-2">
                  <div className="flex justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium truncate">{tx.merchant || tx.description}</p>
                      <p className="text-xs text-muted">{dateShort(tx.date)}</p>
                    </div>
                    <span className={`font-semibold num ${tx.type === "income" ? "text-income" : ""}`}>
                      {tx.type === "income" ? "+" : "−"}{money(tx.amount, { precise: true })}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <CategoryCell tx={tx} categories={cats.data} disabled={isDemo} onChange={changeCategory} />
                    {!isDemo && (
                      <div className="flex">
                        <button className="btn-ghost h-8 w-8 px-0" onClick={() => setEditing(tx)} aria-label="Edit"><Pencil size={15} /></button>
                        <button className="btn-ghost h-8 w-8 px-0" onClick={() => remove(tx)} aria-label="Delete"><Trash2 size={15} /></button>
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>

            {data.pages > 1 && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-line text-sm">
                <span className="text-muted">Page {data.page} of {data.pages}</span>
                <div className="flex gap-1">
                  <button className="btn-secondary h-8 px-2" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} aria-label="Previous page"><ChevronLeft size={16} /></button>
                  <button className="btn-secondary h-8 px-2" disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)} aria-label="Next page"><ChevronRight size={16} /></button>
                </div>
              </div>
            )}
          </>
        )}
      </Panel>

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} onDone={reload} />
      <TransactionDialog open={addOpen || Boolean(editing)} tx={editing} categories={cats.data}
        onClose={() => { setAddOpen(false); setEditing(null); }} onSaved={reload} />
    </div>
  );
}
