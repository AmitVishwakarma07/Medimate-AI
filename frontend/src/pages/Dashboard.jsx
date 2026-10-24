import { CalendarDays, Droplets, Heart, Moon, Sparkles, Stethoscope } from "lucide-react";
import { api } from "../services/api";
import { fmtDate, fmtValue, today } from "../services/format";
import { LABELS } from "../services/format";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../hooks/useAuth.jsx";
import { Empty, ErrorBox, PageHead, SampleBadge, Spinner } from "../components/ui.jsx";
import { TrendChart, seriesFor } from "../components/charts.jsx";
import RecordForm from "../components/RecordForm.jsx";

export default function Dashboard({ go }) {
  const { user } = useAuth();
  const { data, error, loading, reload } = useAsync(async () => {
    const [summary, records, appts, recs] = await Promise.all([
      api.summary(), api.listRecords({ limit: 200 }), api.listAppointments(), api.recommendations(),
    ]);
    return { summary, records, appts, recs };
  });

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} onRetry={reload} />;
  const { summary, records, appts, recs } = data;
  const L = summary.latest;
  const upcoming = appts.filter((a) => a.status === "scheduled" && a.appt_date >= today()).slice(0, 3);

  const Stat = ({ icon: Icon, label, rec }) => (
    <div className="card stat">
      <div className="label"><Icon size={16} /> {label}</div>
      <div className="value">{rec ? fmtValue(rec) : "-"}</div>
      <div className="muted">{rec ? <>{fmtDate(rec.recorded_date)} {rec.is_sample && <SampleBadge />}</> : "No data yet"}</div>
    </div>
  );

  return (
    <>
      <PageHead title={`Welcome, ${user.name.split(" ")[0]}`} subtitle="Your personal health dashboard" />
      {summary.has_sample_data && <div className="notice">Some records shown here are fictional <strong>SAMPLE data</strong> from demo mode.</div>}
      <div className="grid stats">
        <div className="card stat">
          <div className="label"><Stethoscope size={16} /> Total entries</div>
          <div className="value">{summary.total}</div>
          <div className="muted">recorded health entries</div>
        </div>
        <Stat icon={Heart} label="Latest heart rate" rec={L.heart_rate} />
        <Stat icon={Heart} label="Latest blood pressure" rec={L.blood_pressure} />
        <Stat icon={Droplets} label="Daily water intake" rec={L.water} />
        <Stat icon={Moon} label="Sleep duration" rec={L.sleep} />
      </div>

      <div className="grid two">
        <div className="card">
          <h2>Add a measurement</h2>
          <RecordForm onSaved={reload} />
        </div>
        <div className="card">
          <h2>Heart rate trend</h2>
          <TrendChart data={seriesFor(records, "heart_rate").slice(-14)} unit="bpm" height={220}
                      series={[{ key: "value", name: "Heart rate", color: "#2563eb" }]} />
          <p className="muted">Trends are informational and should be interpreted in context.</p>
        </div>
      </div>

      <div className="grid two">
        <div className="card">
          <h2>Recent records</h2>
          {records.length === 0 ? <Empty title="No records yet" hint="Add your first measurement using the form." /> :
            records.slice(0, 5).map((r) => (
              <div className="list-item" key={r.id}>
                <span><strong>{LABELS[r.record_type]}</strong> {r.is_sample && <SampleBadge />}<br /><span className="muted">{fmtDate(r.recorded_date)}</span></span>
                <span>{fmtValue(r)}</span>
              </div>
            ))}
          <button className="btn secondary small" onClick={() => go("records")}>All records</button>
        </div>
        <div className="card">
          <h2>Upcoming appointments</h2>
          {upcoming.length === 0 ? <Empty icon={CalendarDays} title="No upcoming appointments" /> :
            upcoming.map((a) => (
              <div className="list-item" key={a.id}>
                <span><strong>{a.title}</strong><br /><span className="muted">{a.provider}</span></span>
                <span>{fmtDate(a.appt_date)} {a.appt_time}</span>
              </div>
            ))}
          <button className="btn secondary small" onClick={() => go("appointments")}>Manage appointments</button>
        </div>
      </div>

      <div className="card">
        <h2><Sparkles size={18} /> Wellness suggestions</h2>
        <div className="grid two">
          {recs.recommendations.slice(0, 4).map((r) => (
            <div key={r.key} className={`card rec ${r.completed ? "done" : ""}`} style={{ marginBottom: 0 }}>
              <h3>{r.title}</h3><p className="muted">Why: {r.why}</p>
            </div>
          ))}
        </div>
        {recs.needs_more_info.length > 0 && <div className="info">{recs.needs_more_info[0]} <button className="chip" onClick={() => go("settings")}>Open settings</button></div>}
      </div>
    </>
  );
}
