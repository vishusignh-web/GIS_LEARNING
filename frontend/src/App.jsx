import { useEffect, useState } from "react";
import {
  getHealth, getLayerMetadata, getParcel,
  queryByEnvelope, queryNearby, queryParcels,
} from "./api.js";

const num = (v) => (v === "" ? NaN : Number(v));

function ResultsTable({ result }) {
  if (!result) return null;
  if (result.count === 0) return <p className="muted">No records matched.</p>;
  const columns = Object.keys(result.features[0]).filter((k) => k !== "geometry");
  return (
    <>
      <p><strong>{result.count}</strong> record{result.count === 1 ? "" : "s"}</p>
      <div className="scroll">
        <table>
          <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {result.features.map((f, i) => (
              <tr key={i}>{columns.map((c) => <td key={c}>{String(f[c] ?? "")}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function AttributeForm({ run }) {
  const [block, setBlock] = useState("");
  const [zoning, setZoning] = useState("");
  const [geometry, setGeometry] = useState(false);
  const [parcelId, setParcelId] = useState("");
  return (
    <>
      <form onSubmit={(e) => { e.preventDefault(); run(() => queryParcels({
        block_number: block || null, zoning: zoning || null, include_geometry: geometry })); }}>
        <label>Block number<input value={block} onChange={(e) => setBlock(e.target.value)} placeholder="e.g. 11" /></label>
        <label>Zoning<input value={zoning} onChange={(e) => setZoning(e.target.value)} placeholder="e.g. R1" /></label>
        <label className="check"><input type="checkbox" checked={geometry} onChange={(e) => setGeometry(e.target.checked)} /> Include geometry</label>
        <button type="submit">Search</button>
      </form>
      <form onSubmit={(e) => { e.preventDefault(); run(() => getParcel(parcelId.trim())); }}>
        <label>Parcel ID<input value={parcelId} onChange={(e) => setParcelId(e.target.value)} placeholder="e.g. P3" required /></label>
        <button type="submit">Find parcel</button>
      </form>
    </>
  );
}

function EnvelopeForm({ run }) {
  const [v, setV] = useState({ xmin: "55.20", ymin: "25.14", xmax: "55.215", ymax: "25.17" });
  const set = (k) => (e) => setV({ ...v, [k]: e.target.value });
  return (
    <form onSubmit={(e) => { e.preventDefault(); run(() => queryByEnvelope({
      wkid: 4326, envelope: { xmin: num(v.xmin), ymin: num(v.ymin), xmax: num(v.xmax), ymax: num(v.ymax) } })); }}>
      {["xmin", "ymin", "xmax", "ymax"].map((k) => (
        <label key={k}>{k}<input type="number" step="any" value={v[k]} onChange={set(k)} required /></label>
      ))}
      <button type="submit">Query envelope</button>
    </form>
  );
}

function NearbyForm({ run }) {
  const [v, setV] = useState({ x: "55.225", y: "25.152", distance_m: "800" });
  const set = (k) => (e) => setV({ ...v, [k]: e.target.value });
  return (
    <form onSubmit={(e) => { e.preventDefault(); run(() => queryNearby({
      x: num(v.x), y: num(v.y), distance_m: num(v.distance_m) })); }}>
      <label>X (longitude)<input type="number" step="any" value={v.x} onChange={set("x")} required /></label>
      <label>Y (latitude)<input type="number" step="any" value={v.y} onChange={set("y")} required /></label>
      <label>Distance (m)<input type="number" step="any" value={v.distance_m} onChange={set("distance_m")} required /></label>
      <button type="submit">Find nearby</button>
    </form>
  );
}

export default function App() {
  const [health, setHealth] = useState("checking");
  const [meta, setMeta] = useState(null);
  const [tab, setTab] = useState("attribute");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getHealth().then(() => setHealth("online")).catch(() => setHealth("offline"));
    getLayerMetadata().then(setMeta).catch(() => setMeta(null));
  }, []);

  async function run(fn) {
    setLoading(true); setError(""); setResult(null);
    try {
      setResult(await fn());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const tabs = { attribute: "By attribute", envelope: "By envelope", nearby: "Nearby" };
  return (
    <main>
      <header>
        <h1>GIS Parcel Explorer</h1>
        <span className={`badge ${health}`}>Backend: {health}</span>
      </header>
      {meta && <p className="muted">Layer: <strong>{meta.name}</strong> ({meta.geometryType}), {meta.fields.length} fields</p>}

      <nav>
        {Object.entries(tabs).map(([k, label]) => (
          <button key={k} className={tab === k ? "active" : ""} onClick={() => { setTab(k); setResult(null); setError(""); }}>{label}</button>
        ))}
      </nav>

      <section className="panel">
        {tab === "attribute" && <AttributeForm run={run} />}
        {tab === "envelope" && <EnvelopeForm run={run} />}
        {tab === "nearby" && <NearbyForm run={run} />}
      </section>

      {loading && <p className="muted">Loading...</p>}
      {error && <p className="error" role="alert">{error}</p>}
      <ResultsTable result={result} />
    </main>
  );
}
