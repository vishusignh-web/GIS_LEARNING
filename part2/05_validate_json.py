# Topic 5: reading and validating JSON responses
import requests
from config import LAYER_URL


def get_features(data):
    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")
    if "error" in data:
        raise RuntimeError(f"ArcGIS error: {data['error']}")
    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError("Response has no 'features' list")
    return features


def run(where):
    data = requests.post(f"{LAYER_URL}/query", data={"where": where, "outFields": "PARCEL_ID", "f": "json"}).json()
    if data.get("exceededTransferLimit"):
        print(f"{where!r}: NOTE - more records exist than this page returned")
    try:
        features = get_features(data)
    except (ValueError, RuntimeError) as e:
        print(f"{where!r}: problem -> {e}")
        return
    if not features:
        print(f"{where!r}: No records matched")
    for f in features:
        print(f"{where!r}:", f["attributes"].get("PARCEL_ID"))


run("ZONING = 'R1'")
run("ZONING = 'NOPE'")        # empty result
run("this is not sql")        # ArcGIS error body
