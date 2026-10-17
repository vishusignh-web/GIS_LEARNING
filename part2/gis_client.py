"""Reusable ArcGIS REST client (Topics 14 and 15)."""
import json
import logging
import os
import time

import requests

log = logging.getLogger("gis_client")

RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = (5, 30)  # (connect, read) seconds


class GisError(Exception):
    """ArcGIS returned an error body, or an unusable response."""


def _headers():
    token = os.environ.get("ARCGIS_TOKEN")  # supplied via environment, never source code
    return {"X-Esri-Authorization": f"Bearer {token}"} if token else {}


def request_json(url, params=None, method="POST", retries=3, backoff=1.0,
                 timeout=DEFAULT_TIMEOUT):
    """Send a request, retry temporary failures, and return parsed JSON.

    Raises requests.Timeout / ConnectionError / HTTPError for transport problems
    and GisError for ArcGIS JSON errors. Parameters are never logged because
    they may contain secrets."""
    data = {**(params or {}), "f": "json"}
    for attempt in range(1, retries + 1):
        try:
            if method == "GET":
                r = requests.get(url, params=data, headers=_headers(), timeout=timeout)
            else:
                r = requests.post(url, data=data, headers=_headers(), timeout=timeout)
            if r.status_code in RETRY_STATUS:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            try:
                body = r.json()
            except ValueError as exc:
                raise GisError("Response was not valid JSON") from exc
            if isinstance(body, dict) and "error" in body:
                err = body["error"]
                # ArcGIS reports errors with HTTP 200; do not retry (e.g. 498/499 token errors)
                raise GisError(f"ArcGIS error {err.get('code')}: {err.get('message')}")
            return body
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            if attempt == retries:
                raise
            time.sleep(backoff * 2 ** (attempt - 1))  # 1s, 2s, 4s...


# ---------- metadata ----------
def get_services_directory(base_url):
    return request_json(base_url, method="GET")


def get_layer_metadata(layer_url):
    return request_json(layer_url, method="GET")


# ---------- queries ----------
def _query_params(where, out_fields, geometry, geometry_type, in_sr, out_sr,
                  return_geometry, order_by=None):
    params = {"where": where, "outFields": out_fields,
              "returnGeometry": str(return_geometry).lower()}
    if geometry is not None:
        params.update({"geometry": json.dumps(geometry),
                       "geometryType": geometry_type,
                       "inSR": in_sr, "spatialRel": "esriSpatialRelIntersects"})
    if out_sr:
        params["outSR"] = out_sr
    if order_by:
        params["orderByFields"] = order_by
    return params


def query_count(layer_url, where="1=1", **geom):
    params = _query_params(where, "*", geom.get("geometry"), geom.get("geometry_type"),
                           geom.get("in_sr"), None, False)
    params["returnCountOnly"] = "true"
    return request_json(f"{layer_url}/query", params)["count"]


def query_features(layer_url, where="1=1", out_fields="*", geometry=None,
                   geometry_type=None, in_sr=None, out_sr=None,
                   return_geometry=False, page_size=1000, order_by=None):
    """Query a layer and automatically retrieve every page."""
    features, offset = [], 0
    while True:
        params = _query_params(where, out_fields, geometry, geometry_type, in_sr,
                               out_sr, return_geometry, order_by)
        params.update({"resultOffset": offset, "resultRecordCount": page_size})
        body = request_json(f"{layer_url}/query", params)
        if not isinstance(body.get("features"), list):
            raise GisError("Response has no 'features' list")
        batch = body["features"]
        features.extend(batch)
        if not body.get("exceededTransferLimit") or not batch:
            return features
        offset += len(batch)


def query_object_ids(layer_url, where="1=1"):
    body = request_json(f"{layer_url}/query", {"where": where, "returnIdsOnly": "true"})
    return body.get("objectIds") or []


def query_by_object_ids(layer_url, batch_size=500, where="1=1", out_fields="*",
                        id_field="OBJECTID"):
    """Fallback when the service does not support pagination."""
    ids, seen, out = query_object_ids(layer_url, where), set(), []
    for i in range(0, len(ids), batch_size):
        chunk = ids[i:i + batch_size]
        body = request_json(f"{layer_url}/query", {
            "objectIds": ",".join(map(str, chunk)), "outFields": out_fields})
        for feat in body.get("features", []):
            oid = feat["attributes"].get(id_field)
            if oid not in seen:
                seen.add(oid)
                out.append(feat)
    return out


# ---------- GeometryServer ----------
def buffer_point(geometry_url, x, y, meters, wkid=4326):
    body = request_json(f"{geometry_url}/buffer", {
        "geometries": json.dumps({"geometryType": "esriGeometryPoint",
                                  "geometries": [{"x": x, "y": y}]}),
        "inSR": wkid, "outSR": wkid, "bufferSR": 3857,
        "distances": meters, "unit": 9001})
    geoms = body.get("geometries")
    if not geoms:
        raise GisError("Buffer returned no geometry")
    polygon = geoms[0]
    polygon["spatialReference"] = {"wkid": wkid}
    return polygon


def project_points(geometry_url, points, in_wkid, out_wkid):
    body = request_json(f"{geometry_url}/project", {
        "geometries": json.dumps({"geometryType": "esriGeometryPoint", "geometries": points}),
        "inSR": in_wkid, "outSR": out_wkid})
    return body.get("geometries", [])


def areas_and_lengths(geometry_url, polygons, wkid=4326):
    return request_json(f"{geometry_url}/areasAndLengths", {
        "polygons": json.dumps(polygons), "sr": wkid})


# ---------- GPServer ----------
FINAL_STATES = {"esriJobSucceeded", "esriJobFailed", "esriJobCancelled", "esriJobTimedOut"}


def run_gp_job(task_url, params, poll_seconds=1.0, max_wait=60):
    job = request_json(f"{task_url}/submitJob", params)
    job_id = job["jobId"]
    deadline = time.time() + max_wait
    while True:
        status = request_json(f"{task_url}/jobs/{job_id}", method="GET")
        state = status["jobStatus"]
        log.info("Job %s: %s", job_id, state)
        if state in FINAL_STATES:
            break
        if time.time() > deadline:
            raise TimeoutError(f"GP job {job_id} did not finish within {max_wait}s")
        time.sleep(poll_seconds)
    if state != "esriJobSucceeded":
        msgs = [m.get("description") for m in status.get("messages", [])]
        raise GisError(f"GP job ended with {state}: {msgs}")
    results = {}
    for name in status.get("results", {}):
        results[name] = request_json(f"{task_url}/jobs/{job_id}/results/{name}", method="GET")
    return results
