const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const inrPrecise = new Intl.NumberFormat("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 2 });

/** ₹12,34,567 (Indian grouping). */
export const money = (n, { precise = false } = {}) =>
  `₹${(precise ? inrPrecise : inr).format(Math.round((Number(n) || 0) * 100) / 100)}`;

/** ₹1.2L / ₹45k for tight spaces like chart axes. */
export const moneyShort = (n) => {
  const v = Math.abs(Number(n) || 0);
  const sign = n < 0 ? "-" : "";
  if (v >= 1e7) return `${sign}₹${(v / 1e7).toFixed(1).replace(/\.0$/, "")}Cr`;
  if (v >= 1e5) return `${sign}₹${(v / 1e5).toFixed(1).replace(/\.0$/, "")}L`;
  if (v >= 1e3) return `${sign}₹${(v / 1e3).toFixed(1).replace(/\.0$/, "")}k`;
  return `${sign}₹${Math.round(v)}`;
};

export const dateShort = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short" });

export const dateLong = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

export const monthLabel = (ym) => {
  const [y, m] = ym.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
};

export const currentMonth = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

export const shiftMonth = (ym, delta) => {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

export const todayISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

export const pct = (n) => (n === null || n === undefined ? "–" : `${n > 0 ? "+" : ""}${n}%`);

export const PROFILE_LABELS = { student: "Student", employee: "Employee", freelancer: "Freelancer" };
