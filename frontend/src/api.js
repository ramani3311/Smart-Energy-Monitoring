// Thin wrapper around the FastAPI backend.
//
// Local dev: VITE_API_BASE_URL is unset, so BASE falls back to "/api",
//   which Vite's dev server proxies to http://127.0.0.1:8000 (see
//   vite.config.js). Nothing to configure.
//
// Production (Vercel, frontend + backend as two separate projects):
//   set VITE_API_BASE_URL to your backend's full URL, e.g.
//   https://your-backend.vercel.app/api
//
// Optional write protection: if the backend has DASHBOARD_API_KEY set,
// also set VITE_DASHBOARD_API_KEY to the same value so mutating requests
// (add/edit/delete node, relay, weather refresh) are authorized.

const BASE = import.meta.env.VITE_API_BASE_URL || "/api";
const API_KEY = import.meta.env.VITE_DASHBOARD_API_KEY || "";

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (API_KEY) headers["Authorization"] = `Bearer ${API_KEY}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {
      // ignore
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export function getSummary() {
  return request("/dashboard/summary");
}

export function getNodes({ search = "", sortBy = "", order = "desc", filter = "all" } = {}) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (sortBy) params.set("sort_by", sortBy);
  if (order) params.set("order", order);
  if (filter) params.set("filter", filter);
  return request(`/nodes?${params.toString()}`);
}

export function getNodeDetail(nodeId) {
  return request(`/nodes/${encodeURIComponent(nodeId)}`);
}

export function setRelay(nodeId, state) {
  return request(`/nodes/${encodeURIComponent(nodeId)}/relay`, {
    method: "POST",
    body: JSON.stringify({ state }),
  });
}

export function refreshWeather(nodeId) {
  return request(`/nodes/${encodeURIComponent(nodeId)}/weather/refresh`, {
    method: "POST",
  });
}

// --- Node management (Add / Edit / Remove) ---

export function createNode(payload) {
  return request("/nodes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateNode(nodeId, payload) {
  return request(`/nodes/${encodeURIComponent(nodeId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteNode(nodeId) {
  return request(`/nodes/${encodeURIComponent(nodeId)}`, {
    method: "DELETE",
  });
}
