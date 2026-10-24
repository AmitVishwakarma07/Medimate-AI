import { useState } from "react";
import { Plus, Save } from "lucide-react";
import { api } from "../services/api";
import { LABELS, UNITS, today } from "../services/format";
import { useToast } from "../hooks/useToast.jsx";

export default function RecordForm({ initial, onSaved, onCancel }) {
  const { notify } = useToast();
  const [f, setF] = useState(
    initial
      ? { record_type: initial.record_type, value: String(initial.value), value2: initial.value2 == null ? "" : String(initial.value2), recorded_date: initial.recorded_date, notes: initial.notes || "" }
      : { record_type: "heart_rate", value: "", value2: "", recorded_date: today(), notes: "" }
  );
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const isBP = f.record_type === "blood_pressure";
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (f.value === "" || isNaN(Number(f.value))) return setErr("Enter a number for the measurement.");
    if (isBP && (f.value2 === "" || isNaN(Number(f.value2)))) return setErr("Enter the diastolic (lower) number too.");
    const body = {
      record_type: f.record_type, value: Number(f.value), value2: isBP ? Number(f.value2) : null,
      recorded_date: f.recorded_date, notes: f.notes.trim() || null,
    };
    setBusy(true);
    try {
      if (initial) await api.updateRecord(initial.id, body);
      else await api.createRecord(body);
      notify(initial ? "Record updated" : "Record saved");
      if (!initial) setF({ ...f, value: "", value2: "", notes: "" });
      onSaved();
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate>
      <div className="form-grid">
        <div>
          <label htmlFor="rtype">Record type</label>
          <select id="rtype" value={f.record_type} onChange={set("record_type")}>
            {Object.entries(LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="rval">{isBP ? "Systolic (upper)" : "Value"} ({isBP ? "mmHg" : UNITS[f.record_type]})</label>
          <input id="rval" type="number" step="any" value={f.value} onChange={set("value")} />
        </div>
        {isBP && (
          <div>
            <label htmlFor="rval2">Diastolic (lower) (mmHg)</label>
            <input id="rval2" type="number" step="any" value={f.value2} onChange={set("value2")} />
          </div>
        )}
        <div>
          <label htmlFor="rdate">Date</label>
          <input id="rdate" type="date" max={today()} value={f.recorded_date} onChange={set("recorded_date")} required />
        </div>
      </div>
      <div style={{ marginTop: ".8rem" }}>
        <label htmlFor="rnotes">Notes (optional)</label>
        <input id="rnotes" maxLength={500} value={f.notes} onChange={set("notes")} placeholder="e.g. measured after a walk" />
      </div>
      {err && <div className="error" role="alert">{err}</div>}
      <div className="row" style={{ marginTop: ".8rem" }}>
        <button className="btn" disabled={busy}>{initial ? <Save size={16} /> : <Plus size={16} />} {busy ? "Saving..." : initial ? "Save changes" : "Add record"}</button>
        {onCancel && <button type="button" className="btn secondary" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  );
}
