import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { money, moneyShort, dateShort } from "../lib/format";

/** SVG attributes can't read CSS variables, so resolve the tokens in JS
 *  and re-read them whenever the theme flips. */
export function useTokens() {
  const read = () => {
    const s = getComputedStyle(document.documentElement);
    const c = (n) => `rgb(${s.getPropertyValue(`--${n}`).trim().split(" ").join(",")})`;
    return { income: c("income"), expense: c("expense"), accent: c("accent"), line: c("line"),
             muted: c("muted"), ink: c("ink"), surface: c("surface"), raised: c("raised") };
  };
  const [tokens, setTokens] = useState(read);
  useEffect(() => {
    const obs = new MutationObserver(() => setTokens(read()));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => obs.disconnect();
  }, []);
  return tokens;
}

function TooltipBox({ title, rows }) {
  return (
    <div className="panel px-3 py-2 text-sm shadow-lg">
      <p className="font-semibold mb-1">{title}</p>
      {rows.map((r) => (
        <p key={r.label} className="flex items-center gap-2 text-muted">
          {r.color && <span className="h-2.5 w-2.5 rounded-sm" style={{ background: r.color }} />}
          <span>{r.label}</span>
          <span className="ml-auto pl-4 text-ink font-semibold num">{money(r.value)}</span>
        </p>
      ))}
    </div>
  );
}

/** Six months of income vs spend, grouped bars. */
export function TrendChart({ data }) {
  const t = useTokens();
  return (
    <div>
      <div className="flex gap-4 text-sm text-muted mb-2" aria-hidden="true">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: t.income }} />Money in</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: t.expense }} />Money out</span>
      </div>
      <div className="h-56" role="img" aria-label={`Income and spending for the last ${data.length} months`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={2} barCategoryGap="28%" margin={{ top: 4, right: 0, left: -12, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke={t.line} strokeOpacity={0.6} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: t.muted, fontSize: 12 }} />
            <YAxis tickFormatter={moneyShort} tickLine={false} axisLine={false} width={56} tick={{ fill: t.muted, fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: t.raised, opacity: 0.6 }}
              content={({ active, payload }) =>
                active && payload?.length ? (
                  <TooltipBox title={payload[0].payload.label} rows={[
                    { label: "Money in", value: payload[0].payload.income, color: t.income },
                    { label: "Money out", value: payload[0].payload.expense, color: t.expense },
                  ]} />
                ) : null}
            />
            <Bar isAnimationActive={false} dataKey="income" fill={t.income} radius={[4, 4, 0, 0]} maxBarSize={28} />
            <Bar isAnimationActive={false} dataKey="expense" fill={t.expense} radius={[4, 4, 0, 0]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/** Spend per day of the month, one series. */
export function DailyChart({ data }) {
  const t = useTokens();
  return (
    <div className="h-36" role="img" aria-label="Spending per day this month">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 4, right: 0, left: -12, bottom: 0 }} barCategoryGap="18%">
          <CartesianGrid vertical={false} stroke={t.line} strokeOpacity={0.6} />
          <XAxis dataKey="day" tickLine={false} axisLine={false} interval="preserveStartEnd" tick={{ fill: t.muted, fontSize: 11 }} />
          <YAxis tickFormatter={moneyShort} tickLine={false} axisLine={false} width={50} tick={{ fill: t.muted, fontSize: 11 }} />
          <Tooltip
            cursor={{ fill: t.raised, opacity: 0.6 }}
            content={({ active, payload }) =>
              active && payload?.length ? (
                <TooltipBox title={dateShort(payload[0].payload.date)} rows={[{ label: "Spent", value: payload[0].value }]} />
              ) : null}
          />
          <Bar isAnimationActive={false} dataKey="amount" fill={t.accent} radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Spend by category as sorted horizontal bars (one hue, length = amount). */
export function CategoryBars({ rows, onSelect, limit = 7 }) {
  if (!rows?.length) return null;
  const shown = rows.slice(0, limit);
  const rest = rows.slice(limit);
  const list = rest.length
    ? [...shown, { category: `${rest.length} more`, amount: rest.reduce((s, r) => s + r.amount, 0),
                   share: Math.round(rest.reduce((s, r) => s + r.share, 0) * 10) / 10, more: true }]
    : shown;
  const max = Math.max(...list.map((r) => r.amount));
  return (
    <ul className="space-y-3">
      {list.map((r) => (
        <li key={r.category}>
          <button
            type="button"
            disabled={!onSelect || r.more}
            onClick={() => onSelect?.(r.category)}
            className="w-full text-left group disabled:cursor-default"
            title={`${r.category}: ${money(r.amount)} (${r.share}%)`}
          >
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="font-medium truncate group-enabled:group-hover:underline underline-offset-2">{r.category}</span>
              <span className="num shrink-0">
                <span className="font-semibold">{money(r.amount)}</span>
                <span className="text-muted ml-2">{r.share}%</span>
              </span>
            </div>
            <div className="mt-1.5 h-2 rounded-full bg-raised">
              <div className="h-full rounded-full bg-accent" style={{ width: `${Math.max((r.amount / max) * 100, 2)}%` }} />
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
