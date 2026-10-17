import { money, dateShort } from "../lib/format";

const DAY = 86400000;
const toDate = (iso) => new Date(`${iso}T00:00:00`);

/**
 * The money runway: a track from the last credit (allowance/salary) to the next one.
 *  - solid part: days already gone
 *  - projection: how far the money left lasts at the current daily average
 *  - if it ends before payday, the gap is shown as "days short"
 */
export default function RunwayTrack({ cycle, incomeLabel = "allowance", compact = false }) {
  const start = toDate(cycle.cycle_start);
  const end = toDate(cycle.next_income);
  const total = Math.max(Math.round((end - start) / DAY), 1);
  const daysLeft = cycle.days_left;
  const elapsed = Math.min(Math.max(total - daysLeft, 0), total);
  const lasts = cycle.runway_days === null ? Infinity : cycle.runway_days;
  const runsOutAt = Math.min(elapsed + lasts, total);
  const short = cycle.status !== "on_track" ? Math.max(Math.ceil(daysLeft - lasts), 0) : 0;
  const spare = cycle.status === "on_track"
    ? Math.max(cycle.left - cycle.daily_burn * daysLeft, 0)
    : 0;
  const pctOf = (d) => `${(d / total) * 100}%`;
  const runOutDate = new Date(start.getTime() + Math.floor(runsOutAt) * DAY);

  const headline = cycle.status === "broke"
    ? "You've used this cycle's money"
    : short > 0
      ? `At this pace, money runs out ${short} day${short > 1 ? "s" : ""} before your ${incomeLabel}`
      : `At this pace, you'll reach your ${incomeLabel} with ${money(spare)} to spare`;

  return (
    <div>
      <div className={`grid gap-6 ${compact ? "" : "md:grid-cols-[minmax(0,1fr)_auto] md:items-end"}`}>
        <div>
          <p className="text-sm text-muted">Safe to spend today</p>
          <p className="font-display font-bold text-5xl sm:text-6xl num leading-none mt-1">
            {money(cycle.safe_to_spend_today)}
          </p>
          <p className={`mt-3 text-sm font-semibold ${short > 0 || cycle.status === "broke" ? "text-bad" : "text-good"}`}>
            {headline}
          </p>
        </div>
        <dl className="grid grid-cols-3 gap-x-6 gap-y-1 text-sm">
          <div>
            <dt className="text-muted">Left</dt>
            <dd className="font-semibold num text-base">{money(cycle.left)}</dd>
          </div>
          <div>
            <dt className="text-muted">Daily average</dt>
            <dd className="font-semibold num text-base">{money(cycle.daily_burn)}</dd>
          </div>
          <div>
            <dt className="text-muted">Days to go</dt>
            <dd className="font-semibold num text-base">{daysLeft}</dd>
          </div>
        </dl>
      </div>

      {/* Track */}
      <div className="mt-7" aria-hidden="true">
        <div className="relative h-3 rounded-full bg-raised">
          <div className="absolute inset-y-0 left-0 rounded-l-full bg-muted/45" style={{ width: pctOf(elapsed) }} />
          <div
            className={`absolute inset-y-0 ${runsOutAt >= total ? "rounded-r-full" : ""} ${short > 0 ? "bg-warn" : "bg-good"}`}
            style={{ left: pctOf(elapsed), width: pctOf(Math.max(runsOutAt - elapsed, 0)) }}
          />
          {short > 0 && (
            <div
              className="absolute inset-y-0 rounded-r-full"
              style={{
                left: pctOf(runsOutAt), right: 0,
                background: "repeating-linear-gradient(135deg, rgb(var(--bad) / .55) 0 4px, transparent 4px 8px)",
              }}
            />
          )}
          {/* today marker */}
          <div className="absolute -top-1.5 -bottom-1.5 w-[3px] rounded bg-ink" style={{ left: `calc(${pctOf(elapsed)} - 1.5px)` }} />
        </div>
        <div className="relative h-10 mt-2 text-xs text-muted">
          <span className="absolute left-0">{dateShort(cycle.cycle_start)}</span>
          <span
            className="absolute -translate-x-1/2 font-semibold text-ink whitespace-nowrap"
            style={{ left: `clamp(2.5rem, ${pctOf(elapsed)}, calc(100% - 2.5rem))` }}
          >
            Today
          </span>
          {short > 0 && runsOutAt - elapsed > total * 0.12 && total - runsOutAt > total * 0.12 && (
            <span className="absolute top-5 -translate-x-1/2 text-bad whitespace-nowrap" style={{ left: pctOf(runsOutAt) }}>
              Runs out {runOutDate.toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
            </span>
          )}
          <span className="absolute right-0 text-right">{dateShort(cycle.next_income)}<br />next {incomeLabel}</span>
        </div>
      </div>
      <p className="sr-only">
        {daysLeft} days until the next {incomeLabel}. {money(cycle.left)} left. {headline}.
      </p>
    </div>
  );
}
