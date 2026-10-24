import { useState } from "react";
import { CalendarDays, Pencil, Trash2, XCircle } from "lucide-react";
import { api } from "../services/api";
import { fmtDate, today } from "../services/format";
import { useAsync } from "../hooks/useAsync";
import { useToast } from "../hooks/useToast.jsx";
import { Empty, ErrorBox, PageHead, Spinner } from "../components/ui.jsx";

const blank = { title: "", provider: "", appt_date: "", appt_time: "", notes: "", status: "scheduled" };

export default function Appointments() {
  const { notify } = useToast();
  const { data: appts, error, loading, reload } = useAsync(() => api.listAppointments());
  const [f, setF] = useState(blank);
  const [editId, setEditId] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (!f.title.trim() || !f.provider.trim()) return setErr("Please enter the purpose and the doctor or clinic name.");
    if (!f.appt_date || !f.appt_time) return setErr("Please choose a date and a time.");
    const body = { ...f, title: f.title.trim(), provider: f.provider.trim(), notes: f.notes.trim() || null };
    setBusy(true);
    try {
      if (editId) await api.updateAppointment(editId, body); else await api.createAppointment(body);
      notify(editId ? "Appointment updated" : "Appointment saved");
      setF(blank); setEditId(null); reload();
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  }
  const edit = (a) => { setEditId(a.id); setF({ title: a.title, provider: a.provider, appt_date: a.appt_date, appt_time: a.appt_time, notes: a.notes || "", status: a.status }); window.scrollTo({ top: 0, behavior: "smooth" }); };
  async function cancel(a) {
    try { await api.updateAppointment(a.id, { ...a, notes: a.notes, status: "cancelled" }); notify("Appointment cancelled"); reload(); }
    catch (e) { notify(e.message, "error"); }
  }
  async function remove(a) {
    if (!window.confirm(`Delete "${a.title}"?`)) return;
    try { await api.deleteAppointment(a.id); notify("Appointment deleted"); reload(); } catch (e) { notify(e.message, "error"); }
  }

  return (
    <>
      <PageHead title="Appointments" subtitle="Your personal appointment reminders" />
      <div className="notice"><strong>Reminders only:</strong> this app does not book anything with a hospital or doctor. It simply keeps your own appointment reminders.</div>
      <div className="card">
        <h2>{editId ? "Edit appointment" : "New appointment reminder"}</h2>
        <form onSubmit={submit} noValidate>
          <div className="form-grid">
            <div><label htmlFor="at">Purpose / title</label><input id="at" maxLength={120} value={f.title} onChange={set("title")} /></div>
            <div><label htmlFor="ap">Doctor or clinic name</label><input id="ap" maxLength={120} value={f.provider} onChange={set("provider")} /></div>
            <div><label htmlFor="ad">Date</label><input id="ad" type="date" min={editId ? undefined : today()} value={f.appt_date} onChange={set("appt_date")} /></div>
            <div><label htmlFor="am">Time</label><input id="am" type="time" value={f.appt_time} onChange={set("appt_time")} /></div>
            <div><label htmlFor="as">Status</label>
              <select id="as" value={f.status} onChange={set("status")}>
                <option value="scheduled">Scheduled</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option>
              </select></div>
          </div>
          <div style={{ marginTop: ".8rem" }}><label htmlFor="an">Notes (optional)</label><input id="an" maxLength={500} value={f.notes} onChange={set("notes")} /></div>
          {err && <div className="error" role="alert">{err}</div>}
          <div className="row" style={{ marginTop: ".8rem" }}>
            <button className="btn" disabled={busy}>{busy ? "Saving..." : editId ? "Save changes" : "Create appointment"}</button>
            {editId && <button type="button" className="btn secondary" onClick={() => { setEditId(null); setF(blank); setErr(""); }}>Cancel edit</button>}
          </div>
        </form>
      </div>
      <div className="card">
        <h2>Your appointments</h2>
        {loading ? <Spinner /> : error ? <ErrorBox message={error} onRetry={reload} /> :
          appts.length === 0 ? <Empty icon={CalendarDays} title="No appointments yet" hint="Add an appointment reminder above." /> :
            appts.map((a) => (
              <div className="list-item" key={a.id}>
                <span>
                  <strong>{a.title}</strong> <span className={`badge ${a.status}`}>{a.status}</span><br />
                  <span className="muted">{a.provider} - {fmtDate(a.appt_date)} at {a.appt_time}{a.notes ? ` - ${a.notes}` : ""}</span>
                </span>
                <span className="row">
                  <button className="btn secondary small" onClick={() => edit(a)}><Pencil size={14} /> Edit</button>
                  {a.status === "scheduled" && <button className="btn secondary small" onClick={() => cancel(a)}><XCircle size={14} /> Cancel</button>}
                  <button className="btn danger small" onClick={() => remove(a)} aria-label="Delete appointment"><Trash2 size={14} /></button>
                </span>
              </div>
            ))}
      </div>
    </>
  );
}
