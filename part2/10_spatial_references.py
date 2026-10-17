# Topic 10: spatial references and geometries
import json
import requests
import gis_client
from config import LAYER_URL

point = {"x": 55.27, "y": 25.20, "spatialReference": {"wkid": 4326}}
envelope = {"xmin": 55.2, "ymin": 25.1, "xmax": 55.3, "ymax": 25.3, "spatialReference": {"wkid": 4326}}
polyline = {"paths": [[[55.2, 25.1], [55.3, 25.2]]], "spatialReference": {"wkid": 4326}}
polygon = {"rings": [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]], "spatialReference": {"wkid": 4326}}
multipoint = {"points": [[1, 2], [3, 4]], "spatialReference": {"wkid": 4326}}
for name, g in [("point", point), ("envelope", envelope), ("polyline", polyline),
                ("polygon", polygon), ("multipoint", multipoint)]:
    print(f"{name:<10}", json.dumps(g))

body = requests.post(f"{LAYER_URL}/query", data={
    "where": "1=1", "geometry": json.dumps(envelope), "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,      # spatial reference of the filter geometry
    "outSR": 4326,     # spatial reference of returned geometries
    "returnGeometry": "true", "outFields": "OBJECTID", "f": "json"}, timeout=30).json()
print("\nResponse spatialReference:", body["spatialReference"])
ring = body["features"][0]["geometry"]["rings"][0]
print("First returned ring closed:", ring[0] == ring[-1])
print("Tip: a wrong inSR (e.g. 3857 with degree values) returns empty or wrong results.")
