"""Tiny local mock of ArcGIS REST services so all Part 2 / Part 3 exercises run offline.

    python mock_arcgis.py                 # serves http://127.0.0.1:8080
    MOCK_TOKEN=secret123 python mock_arcgis.py   # Secure layer requires this token

Endpoints (under /arcgis/rest/services):
  Parcels|Secure|Flaky|Slow/FeatureServer/0[/query]   12 parcels, maxRecordCount=5
  Utilities/Geometry/GeometryServer/{buffer,project,areasAndLengths}
  Tools/GPServer/Buffer/{submitJob,execute,jobs/<id>[/results/<name>]}
  /mock/reset  resets the 'Flaky' failure counter
"""
import json
import math
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.getenv("MOCK_PORT", "8080"))
MAX_RECORDS = 5
SR = {"wkid": 4326, "latestWkid": 4326}
FIELDS = [
    {"name": "OBJECTID", "type": "esriFieldTypeOID", "alias": "OBJECTID"},
    {"name": "PARCEL_ID", "type": "esriFieldTypeString", "alias": "Parcel ID", "length": 20},
    {"name": "AREA", "type": "esriFieldTypeDouble", "alias": "Area (m2)"},
    {"name": "ZONING", "type": "esriFieldTypeString", "alias": "Zoning", "length": 10,
     "domain": {"type": "codedValue", "name": "ZoningDomain", "codedValues": [
         {"name": "Residential", "code": "R1"}, {"name": "Commercial", "code": "C1"}]}},
    {"name": "BLOCK_NO", "type": "esriFieldTypeString", "alias": "Block", "length": 10},
]


def _make_features():
    out = []
    for i in range(1, 13):
        x, y, s = 55.20 + 0.005 * i, 25.15, 0.004
        out.append({
            "attributes": {"OBJECTID": i, "PARCEL_ID": f"P{i}", "AREA": 100.0 + 50 * i,
                           "ZONING": "R1" if i % 2 else "C1", "BLOCK_NO": str(10 + i % 3)},
            "geometry": {"rings": [[[x, y], [x, y + s], [x + s, y + s], [x + s, y], [x, y]]]},
        })
    return out


FEATURES = _make_features()
JOBS = {}
STATE = {"flaky_hits": 0}


def _error(code, message, details=None):
    return {"error": {"code": code, "message": message, "details": details or []}}


def _bbox(geom):
    if "xmin" in geom:
        return geom["xmin"], geom["ymin"], geom["xmax"], geom["ymax"]
    pts = [p for ring in geom.get("rings", []) for p in ring]
    if "x" in geom:
        pts = [[geom["x"], geom["y"]]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def run_query(p):
    feats = list(FEATURES)
    where = p.get("where", "1=1").strip()
    if where != "1=1":
        for cond in re.split(r"\s+AND\s+", where, flags=re.I):
            m = re.match(r"^(\w+)\s*=\s*'((?:[^']|'')*)'$", cond.strip())
            if not m or m.group(1) not in {f["name"] for f in FIELDS}:
                return _error(400, "Unable to complete operation.", ["Invalid or unsupported where clause"])
            field, value = m.group(1), m.group(2).replace("''", "'")
            feats = [f for f in feats if str(f["attributes"][field]) == value]
    if p.get("objectIds"):
        ids = {int(i) for i in p["objectIds"].split(",")}
        feats = [f for f in feats if f["attributes"]["OBJECTID"] in ids]
    if p.get("geometry"):
        try:
            gx0, gy0, gx1, gy1 = _bbox(json.loads(p["geometry"]))
        except (ValueError, KeyError):
            return _error(400, "Unable to complete operation.", ["Invalid geometry"])
        def hit(f):
            x0, y0, x1, y1 = _bbox(f["geometry"])
            return not (x1 < gx0 or x0 > gx1 or y1 < gy0 or y0 > gy1)
        feats = [f for f in feats if hit(f)]
    if p.get("returnCountOnly") == "true":
        return {"count": len(feats)}
    if p.get("returnIdsOnly") == "true":
        return {"objectIdFieldName": "OBJECTID", "objectIds": [f["attributes"]["OBJECTID"] for f in feats]}
    if p.get("orderByFields"):
        parts = p["orderByFields"].split()
        feats.sort(key=lambda f: f["attributes"].get(parts[0]), reverse=len(parts) > 1 and parts[1].upper() == "DESC")
    offset = int(p.get("resultOffset", 0))
    n = min(int(p.get("resultRecordCount", MAX_RECORDS)), MAX_RECORDS)
    page = feats[offset:offset + n]
    out_fields = p.get("outFields", "*")
    keep = None if out_fields in ("*", "") else {c.strip() for c in out_fields.split(",")}
    result = []
    for f in page:
        item = {"attributes": {k: v for k, v in f["attributes"].items() if keep is None or k in keep}}
        if p.get("returnGeometry", "true") == "true":
            item["geometry"] = f["geometry"]
        result.append(item)
    body = {"objectIdFieldName": "OBJECTID", "geometryType": "esriGeometryPolygon",
            "spatialReference": {"wkid": int(p["outSR"])} if p.get("outSR") else SR, "features": result}
    if offset + n < len(feats):
        body["exceededTransferLimit"] = True
    return body


def layer_metadata(name):
    return {"id": 0, "name": name, "type": "Feature Layer", "geometryType": "esriGeometryPolygon",
            "capabilities": "Query", "maxRecordCount": MAX_RECORDS,
            "supportsPagination": True, "objectIdField": "OBJECTID",
            "displayField": "PARCEL_ID", "extent": {"xmin": 55.2, "ymin": 25.15, "xmax": 55.27,
                                                     "ymax": 25.17, "spatialReference": SR},
            "spatialReference": SR, "fields": FIELDS}


def web_mercator(lon, lat):
    return (lon * 111319.49079327357,
            math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137.0)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("mock: " + fmt % args + "\n")

    def _send(self, body, status=200):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _params(self):
        parsed = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        if self.command == "POST":
            length = int(self.headers.get("Content-Length", 0))
            params.update({k: v[0] for k, v in parse_qs(self.rfile.read(length).decode()).items()})
        return parsed.path.rstrip("/"), params

    def do_GET(self):
        self.route()

    def do_POST(self):
        self.route()

    def route(self):
        path, p = self._params()
        base = "/arcgis/rest/services"
        if path == "/mock/reset":
            STATE["flaky_hits"] = 0
            return self._send({"reset": True})
        if path == base:
            return self._send({"currentVersion": 11.2, "folders": ["Utilities", "Tools"],
                               "services": [{"name": n, "type": "FeatureServer"} for n in ("Parcels", "Secure", "Flaky", "Slow")]})
        m = re.match(rf"^{base}/(Parcels|Secure|Flaky|Slow)/FeatureServer/0(/query)?$", path)
        if m:
            name, is_query = m.group(1), bool(m.group(2))
            if name == "Secure":
                token = os.getenv("MOCK_TOKEN", "secret123")
                if self.headers.get("X-Esri-Authorization") != f"Bearer {token}":
                    return self._send(_error(499, "Token Required"))   # HTTP 200 + error body, like ArcGIS
            if name == "Flaky" and STATE["flaky_hits"] < 2:
                STATE["flaky_hits"] += 1
                return self._send({"message": "temporarily unavailable"}, 503)
            if name == "Slow":
                time.sleep(3)
            return self._send(run_query(p) if is_query else layer_metadata(name))
        if path.startswith(f"{base}/Utilities/Geometry/GeometryServer"):
            op = path.rsplit("/", 1)[-1]
            return self._geometry(op, p)
        m = re.match(rf"^{base}/Tools/GPServer/Buffer(.*)$", path)
        if m:
            return self._gp(m.group(1), p)
        self._send(_error(404, "Service not found"), 404)

    def _geometry(self, op, p):
        try:
            if op == "buffer":
                g = json.loads(p["geometries"])["geometries"][0]
                d = float(p["distances"]) / 111320.0
                x, y = g["x"], g["y"]
                ring = [[x - d, y - d], [x - d, y + d], [x + d, y + d], [x + d, y - d], [x - d, y - d]]
                return self._send({"geometries": [{"rings": [ring]}]})
            if op == "project":
                pts = json.loads(p["geometries"])["geometries"]
                if int(p["inSR"]) == 4326 and int(p["outSR"]) == 3857:
                    out = [dict(zip(("x", "y"), web_mercator(q["x"], q["y"]))) for q in pts]
                else:
                    out = pts
                return self._send({"geometries": out})
            if op == "areasAndLengths":
                polys = json.loads(p["polygons"])
                areas = []
                for poly in polys:
                    ring = poly["rings"][0]
                    areas.append(abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:]))) / 2)
                return self._send({"areas": areas, "lengths": [0] * len(areas)})
        except (KeyError, ValueError, IndexError):
            pass
        self._send(_error(400, "Unable to complete operation.", ["Invalid geometry parameters"]))

    def _gp(self, sub, p):
        if sub == "":
            return self._send({"name": "Buffer", "executionType": "esriExecutionTypeAsynchronous",
                               "parameters": [{"name": "Input_Distance", "dataType": "GPDouble",
                                               "direction": "esriGPParameterDirectionInput"},
                                              {"name": "Output_Result", "dataType": "GPString",
                                               "direction": "esriGPParameterDirectionOutput"}]})
        if sub == "/execute":
            return self._send({"results": [{"paramName": "Output_Result", "dataType": "GPString",
                                            "value": f"done: distance={p.get('Input_Distance')}"}], "messages": []})
        if sub == "/submitJob":
            job_id = f"j{len(JOBS) + 1}"
            JOBS[job_id] = {"t": time.time(), "distance": p.get("Input_Distance")}
            return self._send({"jobId": job_id, "jobStatus": "esriJobSubmitted"})
        m = re.match(r"^/jobs/(\w+)(?:/results/(\w+))?$", sub)
        if m and m.group(1) in JOBS:
            job = JOBS[m.group(1)]
            if m.group(2):
                return self._send({"paramName": m.group(2), "dataType": "GPString",
                                   "value": f"done: distance={job['distance']}"})
            done = time.time() - job["t"] > 2
            body = {"jobId": m.group(1), "jobStatus": "esriJobSucceeded" if done else "esriJobExecuting",
                    "messages": [{"type": "esriJobMessageTypeInformative", "description": "Started"}]}
            if done:
                body["results"] = {"Output_Result": {"paramUrl": "results/Output_Result"}}
            return self._send(body)
        self._send(_error(404, "Job not found"), 404)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Mock ArcGIS server on http://127.0.0.1:{PORT}/arcgis/rest/services  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
