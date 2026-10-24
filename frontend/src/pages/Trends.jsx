import { useState } from "react";
import { api } from "../services/api";
import { today } from "../services/format";
import { useAsync } from "../hooks/useAsync";
import { ErrorBox, PageHead, Spinner } from "../components/ui.jsx";
import { TrendChart, seriesFor } from "../components/charts.jsx";

function startDate(days) {
  if (!days) return "";
  const d = new Date();
  d.setDate(d.getDate() - Number(days));
  return d.toLocaleDateString("en-CA");
}

export default function Trends() {
  const [days, setDays] = useState("30");
  const { data: records, error, loading, reload } = useAsync(
    () => api.listRecords({ start_date: startDate(days), end_date: today(), limit: 2000 }), [days]);

  return (
    <>
      <PageHead title="Health Trends" subtitle="Charts are built from your saved records">
        <div>
          <label htmlFor="range">Time range</label>
          <select id="range" value={days} onChange={(e) => setDays(e.target.value)}>
            <option value="7">Last 7 days</option><option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option><option value="">All time</option>
          </select>
        </div>
      </PageHead>
      <div className="info">
        These charts are informational only. They are not a diagnosis or a disease prediction, and numbers should be
        interpreted in context by a qualified healthcare professional.
      </div>
      {loading ? <Spinner /> : error ? <ErrorBox message={error} onRetry={reload} /> : (
        <div className="grid two">
          <div className="card"><h2>Heart rate over time</h2>
            <TrendChart data={seriesFor(records, "heart_rate")} unit="bpm" series={[{ key: "value", name: "Heart rate", color: "#2563eb" }]} emptyHint="Add heart rate records." /></div>
          <div className="card"><h2>Blood pressure over time</h2>
            <TrendChart data={seriesFor(records, "blood_pressure")} unit="mmHg" series={[{ key: "value", name: "Systolic", color: "#2563eb" }, { key: "value2", name: "Diastolic", color: "#14b8a6" }]} emptyHint="Add blood pressure records." /></div>
          <div className="card"><h2>Sleep duration over time</h2>
            <TrendChart data={seriesFor(records, "sleep")} unit="hours" series={[{ key: "value", name: "Sleep", color: "#6366f1" }]} emptyHint="Add sleep records." /></div>
          <div className="card"><h2>Daily water intake</h2>
            <TrendChart kind="bar" data={seriesFor(records, "water")} unit="litres" series={[{ key: "value", name: "Water", color: "#14b8a6" }]} emptyHint="Add water intake records." /></div>
        </div>
      )}
    </>
  );
}
