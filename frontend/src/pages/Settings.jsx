import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { api } from "../services/api";
import { GOAL_LABELS } from "../services/format";
import { useAuth } from "../hooks/useAuth.jsx";
import { useToast } from "../hooks/useToast.jsx";
import { useAsync } from "../hooks/useAsync";
import { PageHead } from "../components/ui.jsx";
import PrivacyNotice from "../components/PrivacyNotice.jsx";

export default function Settings() {
  const { user, setUser, logout, clearSession } = useAuth();
  const { notify } = useToast();
  const { data: status } = useAsync(() => api.chatStatus());
  const [f, setF] = useState({ name: user.name, goals: user.goals, activity_level: user.activity_level || "", has_restrictions: user.has_restrictions, ai_consent: user.ai_consent });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => setErr(""), [f]);
  const [pw, setPw] = useState({ current: "", next: "" });
  const [pwErr, setPwErr] = useState("");
  const [delPw, setDelPw] = useState("");
  const [delErr, setDelErr] = useState("");

  async function changePassword(e) {
    e.preventDefault();
    setPwErr("");
    if (pw.next.length < 10) return setPwErr("New password must be at least 10 characters.");
    try {
      await api.changePassword(pw.current, pw.next);
      setPw({ current: "", next: "" });
      notify("Password changed");
    } catch (ex) { setPwErr(ex.message); }
  }
  async function exportData() {
    try { await api.exportMyData(); notify("Your data was downloaded"); } catch (ex) { notify(ex.message, "error"); }
  }
  async function deleteAccount(e) {
    e.preventDefault();
    setDelErr("");
    if (!delPw) return setDelErr("Enter your password to confirm.");
    if (!window.confirm("This permanently deletes your account and ALL your records. This cannot be undone. Continue?")) return;
    try {
      await api.deleteAccount(delPw);
      clearSession();
    } catch (ex) { setDelErr(ex.message); }
  }

  const toggleGoal = (g) => setF({ ...f, goals: f.goals.includes(g) ? f.goals.filter((x) => x !== g) : [...f.goals, g] });

  async function save(e) {
    e.preventDefault();
    if (!f.name.trim()) return setErr("Name cannot be empty.");
    setBusy(true);
    try {
      const body = { name: f.name.trim(), goals: f.goals, has_restrictions: f.has_restrictions, ai_consent: f.ai_consent };
      if (f.activity_level) body.activity_level = f.activity_level;
      setUser(await api.updateProfile(body));
      notify("Settings saved");
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHead title="Profile & Settings" subtitle={user.email} />
      <form className="card" onSubmit={save} noValidate>
        <h2>Your profile</h2>
        <label htmlFor="pn">Name</label>
        <input id="pn" value={f.name} maxLength={80} onChange={(e) => setF({ ...f, name: e.target.value })} />

        <h3 style={{ marginTop: "1rem" }}>Lifestyle goals</h3>
        <p className="muted">Used only to personalise your wellness suggestions.</p>
        {Object.entries(GOAL_LABELS).map(([k, v]) => (
          <label className="check" key={k}><input type="checkbox" checked={f.goals.includes(k)} onChange={() => toggleGoal(k)} /> {v}</label>
        ))}

        <h3 style={{ marginTop: "1rem" }}>Activity level (optional)</h3>
        <select value={f.activity_level} onChange={(e) => setF({ ...f, activity_level: e.target.value })} aria-label="Activity level">
          <option value="">Prefer not to say</option><option value="sedentary">Mostly sitting</option>
          <option value="light">Light activity</option><option value="moderate">Moderate activity</option><option value="active">Very active</option>
        </select>
        <label className="check" style={{ marginTop: ".8rem" }}>
          <input type="checkbox" checked={f.has_restrictions} onChange={(e) => setF({ ...f, has_restrictions: e.target.checked })} />
          I have dietary or medical restrictions (we will not suggest diet or exercise changes)
        </label>

        <h3 style={{ marginTop: "1rem" }}>Privacy: external AI</h3>
        <label className="check">
          <input type="checkbox" checked={f.ai_consent} onChange={(e) => setF({ ...f, ai_consent: e.target.checked })} />
          Allow my typed chatbot questions to be sent to an external AI service
        </label>
        <p className="muted">
          {status?.external_ai_available
            ? "An external AI is configured on this server. Only the question you type is sent - never your health records."
            : "No external AI is configured on this server, so the built-in rule-based helper is always used and nothing leaves the app."}
        </p>
        {err && <div className="error" role="alert">{err}</div>}
        <button className="btn" disabled={busy}>{busy ? "Saving..." : "Save settings"}</button>
      </form>

      <div className="card">
        <h2>Change password</h2>
        <form onSubmit={changePassword} noValidate>
          <div className="form-grid">
            <div><label htmlFor="cp1">Current password</label><input id="cp1" type="password" autoComplete="current-password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} /></div>
            <div><label htmlFor="cp2">New password (10+ characters)</label><input id="cp2" type="password" autoComplete="new-password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} /></div>
          </div>
          {pwErr && <div className="error" role="alert">{pwErr}</div>}
          <button className="btn secondary" style={{ marginTop: ".7rem" }}>Change password</button>
        </form>
      </div>

      <div className="card">
        <h2>Your data and privacy</h2>
        <PrivacyNotice />
        <div className="row" style={{ marginTop: ".6rem" }}>
          <button className="btn secondary" onClick={exportData}>Download all my data (JSON)</button>
          <button className="btn danger" onClick={logout}><LogOut size={16} /> Log out</button>
        </div>
      </div>

      <div className="card" style={{ border: "1px solid var(--danger)" }}>
        <h2>Delete my account</h2>
        <p className="muted">Permanently removes your account and every record, reminder and setting. This cannot be undone. Consider downloading your data first.</p>
        <form onSubmit={deleteAccount} noValidate>
          <label htmlFor="dp">Confirm with your password</label>
          <input id="dp" type="password" autoComplete="current-password" value={delPw} onChange={(e) => setDelPw(e.target.value)} />
          {delErr && <div className="error" role="alert">{delErr}</div>}
          <button className="btn danger" style={{ marginTop: ".7rem" }}>Delete my account and all data</button>
        </form>
      </div>
    </>
  );
}
