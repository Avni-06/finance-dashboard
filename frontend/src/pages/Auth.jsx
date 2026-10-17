import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { Field, Logo } from "../components/ui";
import { PROFILE_OPTIONS } from "./Onboarding";

function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="min-h-screen grid place-items-center px-4 py-10">
      <div className="w-full max-w-md">
        <Link to="/"><Logo /></Link>
        <h1 className="text-3xl font-bold mt-8">{title}</h1>
        <p className="text-muted mt-1.5">{subtitle}</p>
        <div className="panel p-5 sm:p-6 mt-6">{children}</div>
        <p className="text-sm text-muted mt-5 text-center">{footer}</p>
      </div>
    </div>
  );
}

export function DemoButtons({ className = "" }) {
  const { demo } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState("");
  const go = async (p) => {
    setBusy(p);
    try {
      await demo(p);
      navigate("/app");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy("");
    }
  };
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {PROFILE_OPTIONS.map((o) => (
        <button key={o.value} type="button" className={o.value === "student" ? "btn-primary" : "btn-secondary"}
          disabled={Boolean(busy)} onClick={() => go(o.value)}>
          {busy === o.value ? "Opening…" : `${o.label} demo`}
        </button>
      ))}
    </div>
  );
}

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const user = await login(form.email, form.password);
      navigate(user.role === "admin" ? "/app/admin" : user.onboarded ? "/app" : "/onboarding");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Welcome back" subtitle="Log in to see where your money went."
      footer={<>New here? <Link to="/register" className="text-ink font-semibold underline underline-offset-2">Create an account</Link></>}>
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email" htmlFor="l-email">
          <input id="l-email" className="input" type="email" autoComplete="email" required value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label="Password" htmlFor="l-pw">
          <input id="l-pw" className="input" type="password" autoComplete="current-password" required value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Field>
        {error && <p className="text-sm text-bad" role="alert">{error}</p>}
        <button className="btn-primary w-full h-11" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
      </form>
      <div className="mt-5 pt-5 border-t border-line">
        <p className="text-sm text-muted mb-3">Just looking? Open a demo with 6 months of sample data.</p>
        <DemoButtons />
      </div>
    </AuthShell>
  );
}

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", profile_type: "student" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await register(form);
      navigate("/onboarding");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Create your account" subtitle="Free, and your data stays yours."
      footer={<>Already have an account? <Link to="/login" className="text-ink font-semibold underline underline-offset-2">Log in</Link></>}>
      <form onSubmit={submit} className="space-y-4">
        <Field label="Name" htmlFor="r-name">
          <input id="r-name" className="input" autoComplete="name" required minLength={2} maxLength={60} value={form.name} onChange={set("name")} />
        </Field>
        <Field label="Email" htmlFor="r-email">
          <input id="r-email" className="input" type="email" autoComplete="email" required value={form.email} onChange={set("email")} />
        </Field>
        <Field label="Password" htmlFor="r-pw" hint="At least 8 characters with a letter and a number.">
          <input id="r-pw" className="input" type="password" autoComplete="new-password" required minLength={8} value={form.password} onChange={set("password")} />
        </Field>
        <Field label="I am a" htmlFor="r-type">
          <select id="r-type" className="input" value={form.profile_type} onChange={set("profile_type")}>
            <option value="student">Student</option>
            <option value="employee">Salaried employee</option>
            <option value="freelancer">Freelancer</option>
          </select>
        </Field>
        {error && <p className="text-sm text-bad" role="alert">{error}</p>}
        <button className="btn-primary w-full h-11" disabled={busy}>{busy ? "Creating account…" : "Create account"}</button>
      </form>
    </AuthShell>
  );
}
