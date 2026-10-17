"""Reusable ArcGIS REST client: token handling, retries, timeouts, pagination, geometry, GP jobs."""
import json
import logging
import os
import threading
import time

import requests

log = logging.getLogger("gis_client")

RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = (5, 30)  # (connect, read) seconds
TOKEN_MINUTES = 60


def _verify():
    """TLS verification setting for every request.

    ARCGIS_VERIFY_SSL=false  -> skip verification (local/self-signed server only)
    ARCGIS_CA_BUNDLE=<path>  -> trust this certificate file
    otherwise                -> normal verification (REQUESTS_CA_BUNDLE is honoured)"""
    if os.environ.get("ARCGIS_VERIFY_SSL", "true").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("ARCGIS_CA_BUNDLE") or True


if not _verify():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.getLogger("gis_client").warning(
        "ARCGIS_VERIFY_SSL=false: TLS certificate checks are DISABLED")


def _referer():
    """Referer bound to the token. Defaults to scheme://host of ARCGIS_TOKEN_URL."""
    explicit = os.environ.get("ARCGIS_REFERER")
    if explicit:
        return explicit
    from urllib.parse import urlsplit
    parts = urlsplit(os.environ.get("ARCGIS_TOKEN_URL", ""))
    return f"{parts.scheme}://{parts.netloc}" if parts.netloc else None


class GisError(Exception):
    """ArcGIS returned an error body, or an unusable response."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


# ---------- authentication ----------
_token_cache = {"value": None, "expires": 0.0}
_token_lock = threading.Lock()


def clear_token_cache():
    with _token_lock:
        _token_cache.update(value=None, expires=0.0)


def get_token():
    """Return a token, or None for public services.

    Order: a ready-made ARCGIS_TOKEN, else generate one from ARCGIS_USERNAME /
    ARCGIS_PASSWORD at ARCGIS_TOKEN_URL (cached, renewed 60 s before expiry).
    The password and token are never logged."""
    static = os.environ.get("ARCGIS_TOKEN")
    if static and not static.lower().startswith("http"):
        return static
    url = os.environ.get("ARCGIS_TOKEN_URL")
    user = os.environ.get("ARCGIS_USERNAME")
    pwd = os.environ.get("ARCGIS_PASSWORD")
    if not (url and user and pwd):
        return None
    with _token_lock:
        if _token_cache["value"] and time.time() < _token_cache["expires"] - 60:
            return _token_cache["value"]
        r = requests.post(url, data={"username": user, "password": pwd,
                                     "client": "referer", "referer": _referer(),
                                     "expiration": TOKEN_MINUTES,
                                     "f": "json"}, timeout=DEFAULT_TIMEOUT,
                          verify=_verify())
        r.raise_for_status()
        body = r.json()
        if "token" not in body:
            msg = (body.get("error") or {}).get("message", "unknown error")
            raise GisError(f"Token request failed: {msg}")
        _token_cache.update(value=body["token"], expires=body["expires"] / 1000)  # ms -> s
        log.info("New ArcGIS token obtained")
        return body["token"]


def _headers():
    token = get_token()
    if not token:
        return {}
    headers = {"X-Esri-Authorization": f"Bearer {token}"}
    if _referer():
        headers["Referer"] = _referer()   # must match the referer the token was issued for
    return headers


# ---------- core request ----------
def request_json(url, params=None, method="POST", retries=3, backoff=1.0,
                 timeout=DEFAULT_TIMEOUT):
    """Send a request, retry temporary failures, return parsed JSON.

    Raises requests.Timeout / ConnectionError / HTTPError for transport problems
    and GisError for ArcGIS JSON errors. Parameters are never logged because
    they may contain secrets."""
    data = {**(params or {}), "f": "json"}
    token_retried = False
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            if method == "GET":
                r = requests.get(url, params=data, headers=_headers(), timeout=timeout,
                                 verify=_verify())
            else:
                r = requests.post(url, data=data, headers=_headers(), timeout=timeout,
                                  verify=_verify())
            if r.status_code in RETRY_STATUS:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            try:
                body = r.json()
            except ValueError as exc:
                raise GisError("Response was not valid JSON") from exc
            if isinstance(body, dict) and "error" in body:
                err = body["error"]
                code = err.get("code")
                if code in (498, 499) and not token_retried and get_token():
                    token_retried = True       # expired token: renew once and retry
                    clear_token_cache()
                    attempt -= 1
                    continue
                raise GisError(f"ArcGIS error {code}: {err.get('message')}", code)
            return body
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            if attempt == retries:
                raise
            time.sleep(backoff * 2 ** (attempt - 1))


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
        params.update({"geometry": json.dumps(geometry), "geometryType": geometry_type,
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


_pagination_cache = {}


def supports_pagination(layer_url):
    """True if the layer accepts resultOffset/resultRecordCount (cached per layer).

    Some layers (e.g. file-geodatabase backed MapServer layers) report
    advancedQueryCapabilities.supportsPagination = false and reject paging."""
    if layer_url not in _pagination_cache:
        caps = (get_layer_metadata(layer_url).get("advancedQueryCapabilities") or {})
        _pagination_cache[layer_url] = bool(caps.get("supportsPagination", True))
        log.info("Layer pagination supported: %s", _pagination_cache[layer_url])
    return _pagination_cache[layer_url]


def query_features(layer_url, where="1=1", out_fields="*", geometry=None,
                   geometry_type=None, in_sr=None, out_sr=None,
                   return_geometry=False, page_size=1000, order_by=None):
    """Query a layer and automatically retrieve every page.

    Uses resultOffset paging when the layer supports it. Otherwise it sends one
    plain query, and if the server says more records exist than it will return
    (exceededTransferLimit) it fetches them in batches by object ID."""
    paged = supports_pagination(layer_url)
    base = _query_params(where, out_fields, geometry, geometry_type, in_sr, out_sr,
                         return_geometry, order_by if paged else None)
    if not paged:
        body = request_json(f"{layer_url}/query", base)
        if not isinstance(body.get("features"), list):
            raise GisError("Response has no 'features' list")
        if not body.get("exceededTransferLimit"):
            return body["features"]
        return query_by_object_ids(layer_url, base_params=base)
    features, offset = [], 0
    while True:
        params = dict(base)
        params.update({"resultOffset": offset, "resultRecordCount": page_size})
        body = request_json(f"{layer_url}/query", params)
        if not isinstance(body.get("features"), list):
            raise GisError("Response has no 'features' list")
        batch = body["features"]
        features.extend(batch)
        if not body.get("exceededTransferLimit") or not batch:
            return features
        offset += len(batch)


def query_object_ids(layer_url, where="1=1", base_params=None):
    params = {k: v for k, v in (base_params or {}).items()
              if k in ("where", "geometry", "geometryType", "inSR", "spatialRel")}
    params.setdefault("where", where)
    params["returnIdsOnly"] = "true"
    body = request_json(f"{layer_url}/query", params)
    return body.get("objectIds") or []


def query_by_object_ids(layer_url, batch_size=500, where="1=1", out_fields="*",
                        id_field="OBJECTID", base_params=None):
    """Fallback when the service does not support pagination.

    base_params (optional) are the original query parameters, so geometry
    filters, outFields, returnGeometry and outSR are kept for every batch."""
    ids, seen, out = query_object_ids(layer_url, where, base_params), set(), []
    keep = {k: v for k, v in (base_params or {}).items()
            if k in ("outFields", "returnGeometry", "outSR")}
    keep.setdefault("outFields", out_fields)
    if base_params and id_field == "OBJECTID":
        id_field = None          # unknown OID name: dedupe on the id list instead
    for i in range(0, len(ids), batch_size):
        chunk = ids[i:i + batch_size]
        body = request_json(f"{layer_url}/query", {
            **keep, "objectIds": ",".join(map(str, chunk))})
        for feat in body.get("features", []):
            if id_field:
                oid = feat["attributes"].get(id_field)
                if oid in seen:
                    continue
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