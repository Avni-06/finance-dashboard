import { AlertTriangle, CheckCircle2, CircleAlert } from "lucide-react";

export function Logo({ className = "" }) {
  return (
    <span className={`inline-flex items-center gap-2 font-display font-bold text-lg text-ink ${className}`}>
      <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden="true">
        <rect width="32" height="32" rx="8" className="fill-raised" />
        <path d="M9 22V10h12" fill="none" stroke="rgb(var(--accent))" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 16h8" stroke="rgb(var(--accent))" strokeWidth="3" strokeLinecap="round" />
        <circle cx="23" cy="21" r="2.5" fill="rgb(var(--income))" />
      </svg>
      FinSight
    </span>
  );
}

export function Panel({ title, subtitle, action, children, className = "", bodyClass = "p-5" }) {
  return (
    <section className={`panel ${className}`}>
      {(title || action) && (
        <header className="flex items-start justify-between gap-3 px-5 pt-4">
          <div>
            {title && <h2 className="text-base font-semibold">{title}</h2>}
            {subtitle && <p className="text-sm text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className={bodyClass}>{children}</div>
    </section>
  );
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="flex flex-col items-center text-center py-10 px-6">
      {Icon && (
        <span className="grid place-items-center h-11 w-11 rounded-full bg-raised text-muted mb-3">
          <Icon size={20} />
        </span>
      )}
      <p className="font-semibold">{title}</p>
      {children && <p className="text-sm text-muted mt-1 max-w-sm">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Skeleton({ className = "h-4 w-full" }) {
  return <div className={`skeleton ${className}`} />;
}

const STATUS = {
  ok: { cls: "bg-good", text: "text-good", icon: CheckCircle2, label: "On track" },
  warning: { cls: "bg-warn", text: "text-warn", icon: AlertTriangle, label: "Near limit" },
  over: { cls: "bg-bad", text: "text-bad", icon: CircleAlert, label: "Over budget" },
};

export function ProgressBar({ percent, status = "ok", className = "" }) {
  const width = Math.min(Math.max(percent, 0), 100);
  return (
    <div
      className={`h-2 rounded-full bg-raised overflow-hidden ${className}`}
      role="progressbar" aria-valuenow={Math.round(percent)} aria-valuemin={0} aria-valuemax={100}
    >
      <div className={`h-full rounded-full ${STATUS[status]?.cls || "bg-accent"}`} style={{ width: `${width}%` }} />
    </div>
  );
}

export function StatusLabel({ status }) {
  const s = STATUS[status] || STATUS.ok;
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold ${s.text}`}>
      <Icon size={13} aria-hidden="true" /> {s.label}
    </span>
  );
}

export function Field({ label, hint, children, htmlFor }) {
  return (
    <div>
      {label && <label htmlFor={htmlFor} className="label">{label}</label>}
      {children}
      {hint && <p className="text-xs text-muted mt-1">{hint}</p>}
    </div>
  );
}

export function ErrorNote({ error, onRetry }) {
  if (!error) return null;
  return (
    <div className="panel p-4 flex items-center justify-between gap-3 border-bad/40">
      <p className="text-sm text-bad">{error.message}</p>
      {onRetry && <button className="btn-secondary h-8" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function Segmented({ options, value, onChange, label }) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-lg bg-raised p-1 border border-line">
      {options.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={`px-3 h-8 rounded-md text-sm font-semibold transition-colors ${
            value === o.value ? "bg-surface text-ink shadow-sm" : "text-muted hover:text-ink"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
