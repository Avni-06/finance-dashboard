import { useRef, useState } from "react";
import { FileUp, CheckCircle2, AlertTriangle } from "lucide-react";
import toast from "react-hot-toast";
import Modal from "./Modal";
import { api } from "../lib/api";

export default function UploadDialog({ open, onClose, onDone }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const input = useRef(null);

  const reset = () => {
    setFile(null); setResult(null); setError(""); setBusy(false);
  };
  const close = () => { reset(); onClose(); };

  const pick = (f) => {
    setError(""); setResult(null);
    if (!f) return;
    if (!/\.(csv|txt)$/i.test(f.name)) return setError("That's not a CSV file. Export your statement as CSV and try again.");
    if (f.size > 2 * 1024 * 1024) return setError("File is larger than 2 MB. Upload a shorter date range.");
    setFile(f);
  };

  const upload = async () => {
    const form = new FormData();
    form.append("file", file);
    setBusy(true); setError("");
    try {
      const r = await api.post("/transactions/upload", form);
      setResult(r);
      toast.success(`Imported ${r.imported} transactions`);
      onDone?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={close} title="Import bank statement">
      {!result ? (
        <div className="space-y-4">
          <label
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files[0]); }}
            className={`flex flex-col items-center justify-center text-center gap-2 rounded-panel border-2 border-dashed px-6 py-10 cursor-pointer transition-colors ${
              dragging ? "border-accent bg-accent/5" : "border-line hover:border-muted/60"
            }`}
          >
            <FileUp className="text-muted" size={28} aria-hidden="true" />
            {file ? (
              <span className="font-semibold">{file.name}</span>
            ) : (
              <>
                <span className="font-semibold">Drop your CSV here or click to choose</span>
                <span className="text-sm text-muted">HDFC, SBI, ICICI, Axis, Kotak and most UPI app exports work</span>
              </>
            )}
            <input ref={input} type="file" accept=".csv,.txt" className="sr-only" onChange={(e) => pick(e.target.files[0])} />
          </label>

          <details className="text-sm text-muted">
            <summary className="cursor-pointer font-semibold text-ink">What format works?</summary>
            <p className="mt-2">
              Any CSV with a date column, a description or narration column, and either one amount column
              (negative for spends) or separate debit and credit columns. Uploading the same statement twice
              won't create duplicates.
            </p>
          </details>

          {error && <p className="text-sm text-bad" role="alert">{error}</p>}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost" onClick={close}>Cancel</button>
            <button className="btn-primary" disabled={!file || busy} onClick={upload}>
              {busy ? "Importing…" : "Import transactions"}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="text-good shrink-0 mt-0.5" size={22} aria-hidden="true" />
            <div>
              <p className="font-semibold">{result.imported} new transactions imported and categorised</p>
              <ul className="text-sm text-muted mt-1 space-y-0.5">
                {result.duplicates > 0 && <li>{result.duplicates} already imported before, skipped</li>}
                {result.skipped > 0 && <li>{result.skipped} rows without a date or amount, skipped</li>}
                {result.low_confidence > 0 && <li>{result.low_confidence} need a quick look (marked “Review”)</li>}
              </ul>
            </div>
          </div>
          {result.warnings?.map((w) => (
            <p key={w} className="flex gap-2 text-sm text-warn"><AlertTriangle size={16} className="shrink-0 mt-0.5" />{w}</p>
          ))}
          <div className="flex justify-end gap-2">
            <button className="btn-secondary" onClick={reset}>Import another</button>
            <button className="btn-primary" onClick={close}>Done</button>
          </div>
        </div>
      )}
    </Modal>
  );
}
