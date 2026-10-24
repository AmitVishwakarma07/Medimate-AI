import { useState } from "react";
import { ClipboardList, Download, Pencil, Trash2 } from "lucide-react";
import { api } from "../services/api";
import { LABELS, fmtDate, fmtValue } from "../services/format";
import { useAsync } from "../hooks/useAsync";
import { useToast } from "../hooks/useToast.jsx";
import { Empty, ErrorBox, PageHead, SampleBadge, Spinner } from "../components/ui.jsx";
import RecordForm from "../components/RecordForm.jsx";

export default function Records() {
  const { notify } = useToast();
  const [filters, setFilters] = useState({ record_type: "", start_date: "", end_date: "" });
  const [editing, setEditing] = useState(null);
  const { data: records, error, loading, reload } = useAsync(() => api.listRecords(filters), [filters]);
  const { data: summary, reload: reloadSummary } = useAsync(() => api.summary());
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });
  const refresh = () => { reload(); reloadSummary(); };

  async function remove(r) {
    if (!window.confirm(`Delete this ${LABELS[r.record_type].toLowerCase()} record from ${fmtDate(r.recorded_date)}?`)) return;
    try { await api.deleteRecord(r.id); notify("Record deleted"); refresh(); } catch (e) { notify(e.message, "error"); }
  }
  const act = (fn, ok) => async () => { try { await fn(); notify(ok); refresh(); } catch (e) { notify(e.message, "error"); } };

  return (
    <>
      <PageHead title="Personal Health Records" subtitle="Only you can see your records">
        <button className="btn secondary" onClick={act(api.downloadCsv, "CSV downloaded")}><Download size={16} /> Export CSV</button>
      </PageHead>

      <div className="card">
        <h2>{editing ? "Edit record" : "Add a record"}</h2>
        <RecordForm key={editing?.id ?? "new"} initial={editing} onSaved={() => { setEditing(null); refresh(); }} onCancel={editing ? () => setEditing(null) : undefined} />
      </div>

      <div className="card">
        <div className="form-grid">
          <div><label htmlFor="ft">Type</label>
            <select id="ft" value={filters.record_type} onChange={set("record_type")}>
              <option value="">All types</option>
              {Object.entries(LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></div>
          <div><label htmlFor="fs">From</label><input id="fs" type="date" value={filters.start_date} onChange={set("start_date")} /></div>
          <div><label htmlFor="fe">To</label><input id="fe" type="date" value={filters.end_date} onChange={set("end_date")} /></div>
        </div>
        <div className="row" style={{ marginTop: ".6rem" }}>
          <button className="btn secondary small" onClick={() => setFilters({ record_type: "", start_date: "", end_date: "" })}>Clear filters</button>
          <button className="btn secondary small" onClick={act(api.loadDemo, "Sample data loaded")}>Load sample data (demo)</button>
          {summary?.has_sample_data && <button className="btn danger small" onClick={act(api.clearDemo, "Sample data removed")}>Remove sample data</button>}
        </div>
      </div>

      <div className="card">
        {loading ? <Spinner /> : error ? <ErrorBox message={error} onRetry={reload} /> :
          records.length === 0 ? <Empty icon={ClipboardList} title="No records found" hint="Add a record above, or change the filters." /> : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Date</th><th>Type</th><th>Value</th><th>Notes</th><th>Actions</th></tr></thead>
                <tbody>
                  {records.map((r) => (
                    <tr key={r.id}>
                      <td>{fmtDate(r.recorded_date)}</td>
                      <td>{LABELS[r.record_type]} {r.is_sample && <SampleBadge />}</td>
                      <td>{fmtValue(r)}</td>
                      <td className="wrap">{r.notes || "-"}</td>
                      <td>
                        <button className="btn secondary small" onClick={() => { setEditing(r); window.scrollTo({ top: 0, behavior: "smooth" }); }} aria-label="Edit record"><Pencil size={14} /></button>{" "}
                        <button className="btn danger small" onClick={() => remove(r)} aria-label="Delete record"><Trash2 size={14} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>
    </>
  );
}
