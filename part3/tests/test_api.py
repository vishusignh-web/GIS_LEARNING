"""Run with:  pytest -q   (no ArcGIS server needed - upstream calls are mocked)"""
import requests
from fastapi.testclient import TestClient

from app import main
from app.gis_client import GisError

client = TestClient(main.app)

FEATURE = {"attributes": {"PARCEL_ID": "P1", "AREA": 150.0, "ZONING": "R1", "BLOCK_NO": "11"},
           "geometry": {"rings": [[[0, 0], [0, 1], [1, 1], [0, 0]]]}}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_docs_available():
    assert client.get("/docs").status_code == 200
    assert "/parcels/query" in client.get("/openapi.json").json()["paths"]


def test_query_valid(monkeypatch):
    seen = {}

    def fake(url, **kw):
        seen.update(kw)
        return [FEATURE]
    monkeypatch.setattr(main, "query_features", fake)
    r = client.post("/parcels/query", json={"block_number": "11", "zoning": "R1"})
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert seen["where"] == "BLOCK_NO = '11' AND ZONING = 'R1'"
    assert "geometry" not in r.json()["features"][0]


def test_query_empty(monkeypatch):
    monkeypatch.setattr(main, "query_features", lambda url, **kw: [])
    r = client.post("/parcels/query", json={"block_number": "ZZZ"})
    assert r.status_code == 200 and r.json() == {"count": 0, "features": []}


def test_invalid_input_422():
    assert client.post("/parcels/query", json={"page_size": 0}).status_code == 422
    assert client.post("/parcels/query", json={"page_size": 5000}).status_code == 422
    assert client.post("/parcels/query", json={"block_number": "1'; DROP"}).status_code == 422


def test_sql_quote_escaped():
    assert main.build_where(block_number="A B") == "BLOCK_NO = 'A B'"
    assert main._quote("O'Brien") == "O''Brien"


def test_geometry_validation():
    open_ring = {"ring": [[0, 0], [0, 10], [10, 10], [10, 0]]}
    assert client.post("/parcels/query/geometry", json=open_ring).status_code == 422
    assert client.post("/parcels/query/geometry", json={}).status_code == 422
    bad_env = {"envelope": {"xmin": 5, "ymin": 0, "xmax": 1, "ymax": 1}}
    assert client.post("/parcels/query/geometry", json=bad_env).status_code == 422


def test_geometry_valid(monkeypatch):
    monkeypatch.setattr(main, "query_features", lambda url, **kw: [FEATURE])
    ring = {"ring": [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]], "include_geometry": True}
    r = client.post("/parcels/query/geometry", json=ring)
    assert r.status_code == 200 and "geometry" in r.json()["features"][0]


def test_parcel_not_found(monkeypatch):
    monkeypatch.setattr(main, "query_features", lambda url, **kw: [])
    assert client.get("/parcels/P999").status_code == 404


def test_nearby(monkeypatch):
    monkeypatch.setattr(main, "buffer_point", lambda *a, **k: {"rings": [[[0, 0]]]})
    monkeypatch.setattr(main, "query_features", lambda url, **kw: [FEATURE])
    assert client.post("/parcels/nearby", json={"x": 55.2, "y": 25.1}).json()["count"] == 1
    assert client.post("/parcels/nearby", json={"x": 999, "y": 25.1}).status_code == 422


def _raises(exc):
    def fake(*a, **k):
        raise exc
    return fake


def test_upstream_timeout_504(monkeypatch):
    monkeypatch.setattr(main, "query_features", _raises(requests.Timeout("slow")))
    r = client.post("/parcels/query", json={})
    assert r.status_code == 504 and r.json()["error"] == "gateway_timeout"


def test_upstream_down_502(monkeypatch):
    monkeypatch.setattr(main, "query_features", _raises(requests.ConnectionError("down")))
    assert client.post("/parcels/query", json={}).status_code == 502


def test_upstream_arcgis_error_502_hides_details(monkeypatch):
    monkeypatch.setattr(main, "query_features", _raises(GisError("ArcGIS error 499: Token Required")))
    r = client.post("/parcels/query", json={})
    assert r.status_code == 502
    assert "Token" not in r.text           # internal details are not leaked to the browser


def test_cors_allows_only_configured_origin():
    ok = client.get("/health", headers={"Origin": "http://localhost:3000"})
    bad = client.get("/health", headers={"Origin": "http://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in bad.headers
