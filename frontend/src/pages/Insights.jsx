import { useState } from "react";
import { Sparkles, RefreshCw, Info } from "lucide-react";
import toast from "react-hot-toast";
import { useFetch } from "../lib/useFetch";
import { api } from "../lib/api";
import { dateShort, dateLong } from "../lib/format";
import { Panel, EmptyState, Skeleton, ErrorNote } from "../components/ui";

const SOURCE_LABEL = { groq: "Written by Llama 3.3 via Groq", gemini: "Written by Google Gemini", rules: "Written by FinSight's built-in rules" };

/** Reports come back as plain lines: summary, "- " bullets, "Action: ...". */
function Report({ content }) {
  const lines = content.split("\n").map((l) => l.trim()).filter(Boolean);
  const bullets = lines.filter((l) => /^[-•*]\s/.test(l)).map((l) => l.replace(/^[-•*]\s+/, "").replace(/\*\*/g, ""));
  const action = lines.find((l) => /^\**action:?\**/i.test(l));
  const rest = lines.filter((l) => !/^[-•*]\s/.test(l) && l !== action).map((l) => l.replace(/\*\*/g, ""));
  return (
    <div className="space-y-4 max-w-2xl">
      {rest.map((l) => <p key={l} className="font-display text-xl sm:text-2xl font-semibold leading-snug">{l}</p>)}
      {bullets.length > 0 && (
        <ul className="space-y-2.5">
          {bullets.map((b) => (
            <li key={b} className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 rounded-full bg-accent shrink-0" aria-hidden="true" />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}
      {action && (
        <div className="rounded-lg border border-accent/40 bg-accent/10 px-4 py-3">
          <p className="text-sm font-semibold text-ink">This week, try this</p>
          <p className="mt-0.5">{action.replace(/^\**action:?\**\s*/i, "").replace(/\*\*/g, "")}</p>
        </div>
      )}
    </div>
  );
}

export default function Insights() {
  const { data, error, loading, reload } = useFetch("/insights/");
  const [busy, setBusy] = useState(false);
  const latest = data?.insights?.[0];
  const history = data?.insights?.slice(1) || [];
  const thisWeek = latest && (() => {
    const d = new Date();
    const monday = new Date(d.getFullYear(), d.getMonth(), d.getDate() - ((d.getDay() + 6) % 7));
    return new Date(`${latest.period_start}T00:00:00`) >= monday;
  })();

  const generate = async (force) => {
    setBusy(true);
    try {
      const r = await api.post("/insights/generate", { force });
      if (!r.cached) toast.success("Fresh report ready");
      reload();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Weekly report</h1>
          <p className="text-sm text-muted mt-1">A short read on your week, with one thing to try next.</p>
        </div>
        {latest && thisWeek && (
          <button className="btn-secondary" disabled={busy} onClick={() => generate(true)}>
            <RefreshCw size={16} className={busy ? "animate-spin" : ""} />Regenerate
          </button>
        )}
      </div>

      <ErrorNote error={error} onRetry={reload} />
      {loading && !data && <Skeleton className="h-64 w-full rounded-panel" />}

      {data && (!latest || !thisWeek) && (
        <Panel>
          <EmptyState icon={Sparkles} title="This week's report isn't ready yet"
            action={<button className="btn-primary" disabled={busy} onClick={() => generate(false)}>
              <Sparkles size={16} />{busy ? "Writing your report…" : "Write this week's report"}
            </button>}>
            FinSight looks at your last 7 days, your budgets and anything unusual, then writes a short summary.
          </EmptyState>
        </Panel>
      )}

      {latest && thisWeek && (
        <Panel bodyClass="p-6 sm:p-8">
          <p className="text-sm text-muted mb-4">Week of {dateLong(latest.period_start)}</p>
          <Report content={latest.content} />
          <p className="flex items-center gap-1.5 text-xs text-muted mt-6">
            <Info size={13} aria-hidden="true" />{SOURCE_LABEL[latest.source]}. Only totals are shared, never your descriptions or email.
          </p>
        </Panel>
      )}

      {history.length > 0 && (
        <Panel title="Earlier reports">
          <ul className="divide-y divide-line -my-2">
            {history.map((i) => (
              <li key={i.id} className="py-3">
                <details>
                  <summary className="cursor-pointer text-sm font-semibold">
                    Week of {dateShort(i.period_start)}
                    <span className="text-muted font-normal ml-2">{i.content.split("\n")[0].slice(0, 80)}</span>
                  </summary>
                  <div className="mt-3"><Report content={i.content} /></div>
                </details>
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
