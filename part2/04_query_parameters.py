# Topic 4: query parameters and request bodies
import requests
from config import LAYER_URL

CONFIG = {"layer_url": LAYER_URL, "timeout": (5, 30)}


def query_layer(where, out_fields="*", return_geometry=False):
    params = {"where": where, "outFields": out_fields,
              "returnGeometry": str(return_geometry).lower(), "f": "json"}
    # ArcGIS query operations expect form-encoded data (data=), not a JSON body (json=)
    r = requests.post(f"{CONFIG['layer_url']}/query", data=params, timeout=CONFIG["timeout"])
    r.raise_for_status()
    return r.json()


result = query_layer("ZONING = 'R1'", "PARCEL_ID,AREA,ZONING")
print("Returned:", len(result["features"]), "| exceededTransferLimit:", result.get("exceededTransferLimit"))
print("(True means more records exist - see Topic 9 for pagination)")
print("First  :", result["features"][0]["attributes"])

# URL encoding is done for you - see it with a GET:
r = requests.get(f"{LAYER_URL}/query", params={"where": "ZONING = 'R1' AND AREA > 200", "f": "json"})
print("Encoded URL:", r.url)
