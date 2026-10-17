import logging
import time

import requests
from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.gis_client import (GisError, buffer_point, get_layer_metadata,
                            query_features)
from app.schemas import (ErrorResponse, GeometryQuery, NearbyRequest,
                         ParcelQuery, ParcelResult)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="GIS Backend", version="0.1.0",
              description="FastAPI backend exposing ArcGIS REST operations to a web frontend.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,      # approved frontend only
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- logging middleware (method, path, status, duration - no secrets) ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path,
             response.status_code, (time.perf_counter() - start) * 1000)
    return response


# ---------- upstream error translation ----------
def _error(status, code, detail):
    return JSONResponse(status_code=status, content={"error": code, "detail": detail})


@app.exception_handler(requests.Timeout)
async def timeout_handler(request: Request, exc):
    log.error("ArcGIS timeout on %s %s", request.method, request.url.path)
    return _error(504, "gateway_timeout", "ArcGIS service timed out")


@app.exception_handler(requests.ConnectionError)
async def connection_handler(request: Request, exc):
    log.error("ArcGIS unreachable on %s", request.url.path)
    return _error(502, "bad_gateway", "ArcGIS service unavailable")


@app.exception_handler(requests.HTTPError)
async def http_error_handler(request: Request, exc):
    log.error("ArcGIS HTTP error on %s: %s", request.url.path, exc)
    return _error(502, "bad_gateway", "ArcGIS service returned an error")


@app.exception_handler(GisError)
async def gis_error_handler(request: Request, exc: GisError):
    log.error("ArcGIS error on %s: %s", request.url.path, exc)
    return _error(502, "bad_gateway", "Invalid response from ArcGIS")


# ---------- helpers (ArcGIS-specific logic stays out of route handlers) ----------
def _quote(value: str) -> str:
    return value.replace("'", "''")


def build_where(block_number=None, zoning=None) -> str:
    clauses = []
    if block_number:
        clauses.append(f"{settings.block_field} = '{_quote(block_number)}'")
    if zoning:
        clauses.append(f"{settings.zoning_field} = '{_quote(zoning)}'")
    return " AND ".join(clauses) or "1=1"


def _result(features, include_geometry=False) -> ParcelResult:
    items = []
    for f in features:
        item = dict(f["attributes"])
        if include_geometry and "geometry" in f:
            item["geometry"] = f["geometry"]
        items.append(item)
    return ParcelResult(count=len(items), features=items)


# ---------- routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": app.version}


@app.get("/layer/metadata")
def layer_metadata():
    meta = get_layer_metadata(settings.arcgis_layer_url)
    return {"name": meta.get("name"), "geometryType": meta.get("geometryType"),
            "maxRecordCount": meta.get("maxRecordCount"),
            "fields": [{"name": f["name"], "type": f["type"]} for f in meta.get("fields", [])]}


@app.post("/parcels/query", response_model=ParcelResult,
          responses={502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
def query_parcels(q: ParcelQuery):
    features = query_features(settings.arcgis_layer_url,
                              where=build_where(q.block_number, q.zoning),
                              out_fields=settings.out_fields,
                              return_geometry=q.include_geometry, page_size=q.page_size)
    return _result(features, q.include_geometry)


@app.post("/parcels/query/geometry", response_model=ParcelResult,
          responses={502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
def query_parcels_by_geometry(q: GeometryQuery):
    if q.envelope:
        geometry, gtype = q.envelope.model_dump(), "esriGeometryEnvelope"
        geometry["spatialReference"] = {"wkid": q.wkid}
    else:
        geometry = {"rings": [[list(p) for p in q.ring]], "spatialReference": {"wkid": q.wkid}}
        gtype = "esriGeometryPolygon"
    features = query_features(settings.arcgis_layer_url, geometry=geometry, geometry_type=gtype,
                              in_sr=q.wkid, out_fields=settings.out_fields,
                              return_geometry=q.include_geometry, page_size=q.page_size)
    return _result(features, q.include_geometry)


@app.post("/parcels/nearby", response_model=ParcelResult,
          responses={502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
def parcels_nearby(req: NearbyRequest):
    polygon = buffer_point(settings.arcgis_geometry_url, req.x, req.y, req.distance_m)
    features = query_features(settings.arcgis_layer_url, geometry=polygon,
                              geometry_type="esriGeometryPolygon", in_sr=4326,
                              out_fields=settings.out_fields)
    return _result(features)


@app.get("/parcels/{parcel_id}", response_model=ParcelResult)
def get_parcel(parcel_id: str = Path(..., max_length=30, pattern=r"^[A-Za-z0-9\-_]+$"),
               include_geometry: bool = False):
    features = query_features(settings.arcgis_layer_url,
                              where=f"{settings.id_field} = '{_quote(parcel_id)}'",
                              out_fields=settings.out_fields, return_geometry=include_geometry)
    if not features:
        raise HTTPException(status_code=404, detail=f"Parcel {parcel_id} not found")
    return _result(features, include_geometry)
