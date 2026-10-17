# Topic 1: HTTP fundamentals - inspect a request and its response
import requests
from config import LAYER_URL

params = {"where": "1=1", "outFields": "*", "f": "json", "resultRecordCount": 1}
r = requests.get(f"{LAYER_URL}/query", params=params, timeout=(5, 30))

print("Method      :", r.request.method)
print("URL         :", r.url)
print("Parameters  :", list(params))
print("Status      :", r.status_code, r.reason)
print("Content-Type:", r.headers.get("Content-Type"))
print("Uses HTTPS  :", r.url.startswith("https://"), "(use HTTPS for real services)")
print("Response is :", type(r.json()).__name__)
