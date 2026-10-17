// All calls go to the FastAPI backend. ArcGIS URLs and tokens never reach the browser.
const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Cannot reach the backend. Is it running on " + BASE + "?");
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    /* non-JSON response */
  }
  if (!response.ok) {
    // 422 = validation (FastAPI list of problems), 502/504 = ArcGIS unavailable or timed out
    if (response.status === 422 && Array.isArray(body?.detail)) {
      const msg = body.detail.map((d) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ");
      throw new Error("Invalid input: " + msg);
    }
    const label = { 502: "ArcGIS unavailable", 504: "ArcGIS timed out", 404: "Not found" }[response.status];
    throw new Error(`${label || "Request failed"} (${response.status})${body?.detail && typeof body.detail === "string" ? ": " + body.detail : ""}`);
  }
  return body;
}

const post = (path, data) => request(path, { method: "POST", body: JSON.stringify(data) });

export const getHealth = () => request("/health");
export const getLayerMetadata = () => request("/layer/metadata");
export const queryParcels = (q) => post("/parcels/query", q);
export const queryByEnvelope = (q) => post("/parcels/query/geometry", q);
export const queryNearby = (q) => post("/parcels/nearby", q);
export const getParcel = (id) => request(`/parcels/${encodeURIComponent(id)}`);
