export const LABELS = {
  heart_rate: "Heart rate", blood_pressure: "Blood pressure", sleep: "Sleep",
  water: "Water intake", weight: "Weight", activity: "Activity",
};
export const UNITS = { heart_rate: "bpm", blood_pressure: "mmHg", sleep: "hours", water: "litres", weight: "kg", activity: "minutes" };
export const GOAL_LABELS = {
  better_sleep: "Better sleep", hydration: "Hydration", be_active: "Be more active",
  balanced_diet: "Balanced diet", manage_stress: "Manage stress",
};
export const today = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time
export const fmtValue = (r) => (r.record_type === "blood_pressure" ? `${r.value}/${r.value2} mmHg` : `${r.value} ${r.unit}`);
export const fmtDate = (d) => new Date(d + "T00:00:00").toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
