import { Check, Sparkles } from "lucide-react";
import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { useToast } from "../hooks/useToast.jsx";
import { ErrorBox, PageHead, Spinner } from "../components/ui.jsx";

export default function Recommendations({ go }) {
  const { notify } = useToast();
  const { data, error, loading, reload } = useAsync(() => api.recommendations());

  async function toggle(r) {
    try { await api.markRecommendation(r.key, !r.completed); notify(r.completed ? "Marked as not done" : "Nice work!"); reload(); }
    catch (e) { notify(e.message, "error"); }
  }
  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} onRetry={reload} />;

  return (
    <>
      <PageHead title="Wellness Recommendations" subtitle="Small, achievable ideas based on your goals and records" />
      <div className="notice">{data.note}</div>
      {data.needs_more_info.length > 0 && (
        <div className="info">
          <strong>Help us personalise these:</strong>
          <ul>{data.needs_more_info.map((m) => <li key={m}>{m}</li>)}</ul>
          <button className="btn small" onClick={() => go("settings")}>Update my goals</button>
        </div>
      )}
      <div className="grid two">
        {data.recommendations.map((r) => (
          <div key={r.key} className={`card rec ${r.completed ? "done" : ""}`}>
            <h2><Sparkles size={16} /> {r.title}</h2>
            <p>{r.text}</p>
            <p className="muted"><strong>Why you see this:</strong> {r.why}</p>
            <button className={`btn small ${r.completed ? "secondary" : ""}`} onClick={() => toggle(r)}>
              <Check size={14} /> {r.completed ? "Completed - undo" : "Mark as done"}
            </button>
          </div>
        ))}
      </div>
    </>
  );
}
