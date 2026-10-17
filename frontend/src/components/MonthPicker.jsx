import { ChevronLeft, ChevronRight } from "lucide-react";
import { currentMonth, monthLabel, shiftMonth } from "../lib/format";

export default function MonthPicker({ value, onChange }) {
  const isCurrent = value >= currentMonth();
  return (
    <div className="inline-flex items-center rounded-lg border border-line bg-surface h-10">
      <button className="h-full px-2.5 text-muted hover:text-ink" onClick={() => onChange(shiftMonth(value, -1))} aria-label="Previous month">
        <ChevronLeft size={18} />
      </button>
      <span className="px-2 text-sm font-semibold min-w-[8.5rem] text-center">{monthLabel(value)}</span>
      <button
        className="h-full px-2.5 text-muted hover:text-ink disabled:opacity-30"
        onClick={() => onChange(shiftMonth(value, 1))}
        disabled={isCurrent}
        aria-label="Next month"
      >
        <ChevronRight size={18} />
      </button>
    </div>
  );
}
