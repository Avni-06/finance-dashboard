import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GraduationCap, Briefcase, Laptop } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { Field, Logo } from "../components/ui";

export const PROFILE_OPTIONS = [
  { value: "student", label: "Student", icon: GraduationCap, desc: "Pocket money, scholarship or stipend. Runway, mess vs delivery, semester costs." },
  { value: "employee", label: "Salaried", icon: Briefcase, desc: "Monthly salary. 50/30/20 check, EMIs, payday runway." },
  { value: "freelancer", label: "Freelancer", icon: Laptop, desc: "Irregular income. Income swings, tax set-aside, top clients." },
];

const INCOME_COPY = {
  student: { label: "Monthly allowance (₹)", hint: "Pocket money from home plus any regular stipend.", day: "Which date does it usually arrive?" },
  employee: { label: "Monthly take-home salary (₹)", hint: "After tax and PF.", day: "Salary date" },
  freelancer: { label: "Average monthly income (₹)", hint: "A rough average of the last few months is fine.", day: "Day you usually invoice" },
};

export function ProfilePicker({ value, onChange }) {
  return (
    <div role="radiogroup" aria-label="Who are you?" className="grid gap-3 sm:grid-cols-3">
      {PROFILE_OPTIONS.map((o) => {
        const Icon = o.icon;
        const active = value === o.value;
        return (
          <button
            type="button" key={o.value} role="radio" aria-checked={active} onClick={() => onChange(o.value)}
            className={`text-left rounded-panel border p-4 transition-colors ${active ? "border-accent bg-accent/10" : "border-line bg-raised/40 hover:border-muted/60"}`}
          >
            <Icon size={20} className={active ? "text-accent" : "text-muted"} aria-hidden="true" />
            <p className="font-semibold mt-2">{o.label}</p>
            <p className="text-xs text-muted mt-1 leading-relaxed">{o.desc}</p>
          </button>
        );
      })}
    </div>
  );
}

/** Shared by onboarding and Settings. */
export function ProfileFields({ form, setForm }) {
  const copy = INCOME_COPY[form.profile_type] || INCOME_COPY.student;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  return (
    <div className="space-y-4">
      <ProfilePicker value={form.profile_type} onChange={(v) => setForm({ ...form, profile_type: v })} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={copy.label} htmlFor="p-income" hint={copy.hint}>
          <input id="p-income" className="input num" type="number" min="0" step="1" required
            value={form.monthly_income} onChange={set("monthly_income")} />
        </Field>
        <Field label={copy.day} htmlFor="p-day">
          <select id="p-day" className="input" value={form.income_day} onChange={(e) => setForm({ ...form, income_day: Number(e.target.value) })}>
            {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </Field>
      </div>
      {form.profile_type === "student" && (
        <Field label="Where do you live?" htmlFor="p-living">
          <select id="p-living" className="input" value={form.living} onChange={set("living")}>
            <option value="hostel">College hostel</option>
            <option value="pg">PG / rented room</option>
            <option value="day_scholar">Day scholar (commute)</option>
            <option value="home">At home</option>
          </select>
        </Field>
      )}
      {form.profile_type === "freelancer" && (
        <Field label="Set aside for tax" htmlFor="p-tax" hint="FinSight shows how much of each month's income to keep aside.">
          <select id="p-tax" className="input" value={form.tax_rate} onChange={(e) => setForm({ ...form, tax_rate: Number(e.target.value) })}>
            {[0.05, 0.1, 0.15, 0.2, 0.25, 0.3].map((r) => <option key={r} value={r}>{Math.round(r * 100)}%</option>)}
          </select>
        </Field>
      )}
    </div>
  );
}

export default function Onboarding() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    profile_type: user?.profile_type || "student", monthly_income: "", income_day: 1, living: "hostel", tax_rate: 0.1,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const r = await api.patch("/auth/profile", { ...form, monthly_income: Number(form.monthly_income) });
      setUser(r.user);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen px-4 py-10">
      <div className="max-w-2xl mx-auto">
        <Logo />
        <h1 className="text-3xl font-bold mt-8">Set up FinSight for you, {user?.name?.split(" ")[0]}</h1>
        <p className="text-muted mt-2">Three quick answers. Your dashboard, categories and budgets adapt to them, and you can change them later in Settings.</p>
        <form onSubmit={submit} className="panel p-5 sm:p-6 mt-6 space-y-5">
          <ProfileFields form={form} setForm={setForm} />
          {error && <p className="text-sm text-bad" role="alert">{error}</p>}
          <button className="btn-primary w-full h-11" disabled={busy}>{busy ? "Setting up…" : "Finish setup"}</button>
        </form>
      </div>
    </div>
  );
}
