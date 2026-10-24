// All communication with the FastAPI backend goes through this file (Fetch API).
// Login uses an httpOnly cookie set by the server, so no token is ever stored in JavaScript.
const BASE = import.meta.env.VITE_API_URL || ""; // empty = same origin (Vite dev proxy / production proxy)
let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };
const AUTH_PATHS = ["/api/auth/login", "/api/auth/register"];

async function request(path, { method = "GET", body, raw = false } = {}) {
  // X-Requested-With is the CSRF defence the server checks on state-changing requests.
  const headers = { "X-Requested-With": "MediMate" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(BASE + path, {
      method, headers, credentials: "include", body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }
  if (res.status === 401 && !AUTH_PATHS.includes(path)) onUnauthorized(); // session expired
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { msg = (await res.json()).error?.message || msg; } catch { /* not JSON */ }
    throw new Error(msg);
  }
  if (raw) return res;
  if (res.status === 204) return null;
  return res.json();
}

async function download(path, filename) {
  const res = await request(path, { raw: true });
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

const qs = (p = {}) => {
  const s = new URLSearchParams(Object.entries(p).filter(([, v]) => v !== "" && v != null)).toString();
  return s ? `?${s}` : "";
};

export const api = {
  register: (b) => request("/api/auth/register", { method: "POST", body: b }),
  login: (b) => request("/api/auth/login", { method: "POST", body: b }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  exportMyData: () => download("/api/account/export", "medimate_my_data.json"),
  changePassword: (current_password, new_password) =>
    request("/api/account/password", { method: "PUT", body: { current_password, new_password } }),
  deleteAccount: (password) => request("/api/account", { method: "DELETE", body: { password } }),
  publicConfig: () => request("/api/config"),
  profile: () => request("/api/profile"),
  updateProfile: (b) => request("/api/profile", { method: "PUT", body: b }),
  summary: () => request("/api/health-records/summary"),
  listRecords: (p) => request(`/api/health-records${qs(p)}`),
  createRecord: (b) => request("/api/health-records", { method: "POST", body: b }),
  updateRecord: (id, b) => request(`/api/health-records/${id}`, { method: "PUT", body: b }),
  deleteRecord: (id) => request(`/api/health-records/${id}`, { method: "DELETE" }),
  loadDemo: () => request("/api/health-records/demo-data", { method: "POST" }),
  clearDemo: () => request("/api/health-records/demo-data", { method: "DELETE" }),
  downloadCsv: () => download("/api/health-records/export.csv", "medimate_records.csv"),
  listAppointments: () => request("/api/appointments"),
  createAppointment: (b) => request("/api/appointments", { method: "POST", body: b }),
  updateAppointment: (id, b) => request(`/api/appointments/${id}`, { method: "PUT", body: b }),
  deleteAppointment: (id) => request(`/api/appointments/${id}`, { method: "DELETE" }),
  chatStatus: () => request("/api/chat/status"),
  chat: (message) => request("/api/chat", { method: "POST", body: { message } }),
  recommendations: () => request("/api/recommendations"),
  markRecommendation: (key, completed) => request(`/api/recommendations/${key}`, { method: "PUT", body: { completed } }),
};
