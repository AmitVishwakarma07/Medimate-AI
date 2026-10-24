import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity } from "lucide-react";
import { Empty } from "./ui.jsx";

// One chart point per saved record of the given type, oldest first.
export function seriesFor(records, type) {
  return records
    .filter((r) => r.record_type === type)
    .sort((a, b) => a.recorded_date.localeCompare(b.recorded_date) || a.id - b.id)
    .map((r) => ({ date: r.recorded_date.slice(5), full: r.recorded_date, value: r.value, value2: r.value2 }));
}

export function TrendChart({ data, series, kind = "line", unit, height = 240, emptyHint }) {
  if (!data.length) return <Empty icon={Activity} title="No data yet" hint={emptyHint || "Add records to see this chart."} />;
  const Chart = kind === "bar" ? BarChart : LineChart;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" fontSize={12} />
        <YAxis fontSize={12} unit={unit ? ` ` : ""} domain={kind === "bar" ? [0, "auto"] : ["auto", "auto"]} />
        <Tooltip formatter={(v, name) => [`${v} ${unit || ""}`, name]} labelFormatter={(_, p) => p?.[0]?.payload?.full || ""} />
        {series.length > 1 && <Legend />}
        {series.map((s) =>
          kind === "bar" ? (
            <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} radius={[4, 4, 0, 0]} />
          ) : (
            <Line key={s.key} dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={2.5} dot={{ r: 3 }} type="monotone" />
          )
        )}
      </Chart>
    </ResponsiveContainer>
  );
}
