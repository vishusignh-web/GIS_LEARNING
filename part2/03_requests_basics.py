# Topic 3: the requests library
import requests
from config import LAYER_URL

url = f"{LAYER_URL}/query"
params = {"where": "1=1", "outFields": "*", "resultRecordCount": 2, "f": "json"}

with requests.Session() as session:
    r = session.get(url, params=params, timeout=(5, 30))
    print("GET  status:", r.status_code)
    print("Content-Type:", r.headers.get("Content-Type"))
    print("Final URL   :", r.url)
    print("JSON keys   :", list(r.json().keys()))
    print("Text (first 80 chars):", r.text[:80])

    p = session.post(url, data=params, timeout=(5, 30))
    print("POST status:", p.status_code, "| same feature count:",
          len(p.json()["features"]) == len(r.json()["features"]))
