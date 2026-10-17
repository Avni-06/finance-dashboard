import { useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { useTheme } from "../lib/useTheme";
import { Panel, Field, Segmented } from "../components/ui";
import { ProfileFields } from "./Onboarding";

export default function Settings() {
  const { user, setUser, isDemo, isAdmin } = useAuth();
  const { theme, toggle } = useTheme();
  const [form, setForm] = useState({
    name: user.name, profile_type: user.profile_type || "student", monthly_income: user.monthly_income || "",
    income_day: user.income_day || 1, living: user.living || "hostel", tax_rate: user.tax_rate ?? 0.1,
  });
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [busy, setBusy] = useState(false);

  const saveProfile = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api.patch("/auth/profile", { ...form, monthly_income: Number(form.monthly_income || 0) });
      setUser(r.user);
      toast.success("Profile saved");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  };

  const savePassword = async (e) => {
    e.preventDefault();
    try {
      await api.patch("/auth/password", pw);
      setPw({ current_password: "", new_password: "" });
      toast.success("Password changed");
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div className="space-y-5 max-w-2xl">
      <h1 className="text-2xl sm:text-3xl font-bold">Settings</h1>

      <Panel title="Appearance">
        <Segmented label="Theme" value={theme} onChange={(v) => v !== theme && toggle()}
          options={[{ value: "dark", label: "Dark" }, { value: "light", label: "Light" }]} />
      </Panel>

      {!isAdmin && (
        <Panel title="Profile" subtitle={isDemo ? "Demo profiles can't be edited." : "Changing your profile type switches your categories and dashboard."}>
          <form onSubmit={saveProfile} className="space-y-4">
            <fieldset disabled={isDemo} className="space-y-4">
              <Field label="Name" htmlFor="s-name">
                <input id="s-name" className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </Field>
              <ProfileFields form={form} setForm={setForm} />
            </fieldset>
            {!isDemo && <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>}
          </form>
        </Panel>
      )}

      {!isDemo && (
        <Panel title="Password">
          <form onSubmit={savePassword} className="space-y-4">
            <Field label="Current password" htmlFor="pw-cur">
              <input id="pw-cur" type="password" className="input" autoComplete="current-password" required
                value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} />
            </Field>
            <Field label="New password" htmlFor="pw-new" hint="At least 8 characters with a letter and a number.">
              <input id="pw-new" type="password" className="input" autoComplete="new-password" required minLength={8}
                value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} />
            </Field>
            <button className="btn-secondary">Change password</button>
          </form>
        </Panel>
      )}

      <p className="text-sm text-muted">Signed in as {user.email}</p>
    </div>
  );
}
