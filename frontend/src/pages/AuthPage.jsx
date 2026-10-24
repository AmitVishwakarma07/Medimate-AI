import { useState } from "react";
import { HeartPulse } from "lucide-react";
import { useAuth } from "../hooks/useAuth.jsx";
import PrivacyNotice from "../components/PrivacyNotice.jsx";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const [agree, setAgree] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (mode === "register" && !f.name.trim()) return setErr("Please enter your name.");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.email.trim())) return setErr("Enter a valid email address.");
    if (mode === "register" && f.password.length < 10) return setErr("Password must be at least 10 characters.");
    if (mode === "login" && !f.password) return setErr("Enter your password.");
    if (mode === "register" && !agree) return setErr("Please read the privacy notice and tick the box to continue.");
    setBusy(true);
    try {
      if (mode === "login") await login({ email: f.email, password: f.password });
      else await register({ name: f.name, email: f.email, password: f.password });
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <div className="brand" style={{ justifyContent: "center" }}><HeartPulse /> MediMate AI</div>
        <h2 style={{ textAlign: "center" }}>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <form onSubmit={submit} noValidate>
          {mode === "register" && (
            <div style={{ marginBottom: ".7rem" }}>
              <label htmlFor="name">Name</label>
              <input id="name" value={f.name} onChange={set("name")} autoComplete="name" />
            </div>
          )}
          <div style={{ marginBottom: ".7rem" }}>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={f.email} onChange={set("email")} autoComplete="email" />
          </div>
          <div style={{ marginBottom: ".7rem" }}>
            <label htmlFor="password">Password{mode === "register" ? " (at least 10 characters)" : ""}</label>
            <input id="password" type="password" value={f.password} onChange={set("password")}
                   autoComplete={mode === "login" ? "current-password" : "new-password"} />
          </div>
          {mode === "register" && (
            <>
              <details style={{ marginBottom: ".5rem" }}>
                <summary>Read the privacy notice</summary>
                <PrivacyNotice />
              </details>
              <label className="check">
                <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
                I have read the privacy notice and agree to my data being processed as described.
              </label>
            </>
          )}
          {err && <div className="error" role="alert">{err}</div>}
          <button className="btn" style={{ width: "100%", justifyContent: "center", marginTop: ".5rem" }} disabled={busy}>
            {busy ? "Please wait..." : mode === "login" ? "Log in" : "Register"}
          </button>
        </form>
        <p style={{ textAlign: "center", marginTop: ".8rem" }}>
          {mode === "login" ? "New here? " : "Already registered? "}
          <button className="chip" onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(""); }}>
            {mode === "login" ? "Create an account" : "Log in"}
          </button>
        </p>
        <p className="footer-note">
          MediMate AI is a personal wellness tracker. It is not a medical device and does not diagnose, prescribe, or
          replace a healthcare professional. In an emergency contact your local emergency services.
        </p>
      </div>
    </div>
  );
}
