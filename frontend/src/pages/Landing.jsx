import { Link, Navigate } from "react-router-dom";
import { Moon, Sun, Github } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../lib/useTheme";
import { Logo } from "../components/ui";
import RunwayTrack from "../components/RunwayTrack";
import { DemoButtons } from "./Auth";

// A fixed example so the hero shows the real runway component, not a screenshot
function sampleCycle() {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), 1);
  const next = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const elapsed = Math.round((today - start) / 86400000) + 1;
  const daysLeft = Math.max(Math.round((next - today) / 86400000), 1);
  const spent = 260 * elapsed;
  const left = 9000 - spent;
  return {
    cycle_start: iso(start), next_income: iso(next), days_left: daysLeft, budget: 9000, spent, left,
    daily_burn: 260, safe_to_spend_today: Math.max(left, 0) / daysLeft,
    runway_days: left / 260, status: left / 260 >= daysLeft ? "on_track" : left > 0 ? "at_risk" : "broke",
  };
}

const NARRATIONS = [
  { raw: "UPI/DR/412398765012/SWIGGY/YESB/swiggy@ybl/Payment", merchant: "Swiggy", cat: "Food & Canteen" },
  { raw: "NEFT CR-HDFC0000999-NOVA LABS-INTERNSHIP STIPEND", merchant: "Nova Labs", cat: "Stipend" },
  { raw: "UPI-SHARMA XEROX-sharmaxerox@okaxis-SBIN0001234-UPI", merchant: "Sharma Xerox", cat: "Books & Stationery" },
];

export default function Landing() {
  const { user } = useAuth();
  const { theme, toggle } = useTheme();
  if (user) return <Navigate to={user.role === "admin" ? "/app/admin" : user.onboarded ? "/app" : "/onboarding"} replace />;

  return (
    <div className="min-h-screen">
      <header className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-8 h-16">
        <Logo />
        <nav className="flex items-center gap-1 sm:gap-2">
          <button className="btn-ghost h-9 w-9 px-0" onClick={toggle} aria-label="Toggle theme">
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link to="/login" className="btn-ghost">Log in</Link>
          <Link to="/register" className="btn-secondary">Sign up</Link>
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-8">
        {/* Hero */}
        <section className="grid gap-10 lg:grid-cols-[1.05fr_1fr] lg:items-center pt-10 pb-16 sm:pt-16">
          <div>
            <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-[3.6rem] leading-[1.05] tracking-tight max-w-xl">
              Know if your pocket money will last the month.
            </h1>
            <p className="text-lg text-muted mt-5 max-w-lg">
              Import your bank statement and FinSight sorts every UPI payment, then tells you what's
              safe to spend today until your next allowance lands.
            </p>
            <div className="mt-8">
              <DemoButtons />
              <p className="text-sm text-muted mt-3">No sign-up needed for the demos. Each one has 6 months of sample data.</p>
            </div>
          </div>
          <div className="panel p-5 sm:p-6">
            <p className="text-sm font-semibold mb-4">Money runway</p>
            <RunwayTrack cycle={sampleCycle()} incomeLabel="allowance" compact />
          </div>
        </section>

        {/* What it does */}
        <section className="grid gap-5 md:grid-cols-3 pb-16">
          <div className="panel p-5">
            <h2 className="text-lg font-semibold">Reads messy bank statements</h2>
            <p className="text-sm text-muted mt-1.5">Junk header rows, debit and credit columns, UPI references. A rules + machine learning model turns them into merchants and categories.</p>
            <ul className="mt-4 space-y-3">
              {NARRATIONS.map((n) => (
                <li key={n.raw} className="text-xs">
                  <p className="text-muted truncate" title={n.raw}>{n.raw}</p>
                  <p className="mt-0.5"><span className="font-semibold text-sm">{n.merchant}</span> <span className="chip bg-raised text-muted ml-1">{n.cat}</span></p>
                </li>
              ))}
            </ul>
          </div>
          <div className="panel p-5">
            <h2 className="text-lg font-semibold">Built around how you earn</h2>
            <p className="text-sm text-muted mt-1.5">Students, salaried employees and freelancers each get their own categories and dashboard.</p>
            <dl className="mt-4 space-y-3 text-sm">
              <div><dt className="font-semibold">Students</dt><dd className="text-muted">Allowance runway, no-spend streaks, semester costs kept out of daily money.</dd></div>
              <div><dt className="font-semibold">Salaried</dt><dd className="text-muted">50/30/20 check, EMI load, payday countdown.</dd></div>
              <div><dt className="font-semibold">Freelancers</dt><dd className="text-muted">Income swings, tax to set aside, top clients.</dd></div>
            </dl>
          </div>
          <div className="panel p-5">
            <h2 className="text-lg font-semibold">A weekly report in plain words</h2>
            <p className="text-sm text-muted mt-1.5">Written by Llama 3.3 or Gemini from your totals only. Your descriptions and email never leave the server.</p>
            <blockquote className="mt-4 rounded-lg bg-raised/60 p-4 text-sm space-y-2">
              <p className="font-semibold">You spent ₹1,802 in the last 7 days, up 30% on the week before.</p>
              <p className="text-muted">Food & Canteen was 52% of it. ₹406 is left in that budget.</p>
              <p><span className="font-semibold">Try this:</span> a 2-day no-spend challenge, mess food and metro only.</p>
            </blockquote>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6 flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
          <p>FinSight. Built with React, Flask and scikit-learn.</p>
          <a className="inline-flex items-center gap-1.5 hover:text-ink" href="https://github.com/Avni-06/finance-dashboard" target="_blank" rel="noreferrer">
            <Github size={16} />Source code
          </a>
        </div>
      </footer>
    </div>
  );
}
