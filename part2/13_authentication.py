# Topic 13: tokens read from the environment (never from source code)
# Mock server default token is "secret123" (set MOCK_TOKEN to change it).
# Run:  ARCGIS_TOKEN=secret123 python 13_authentication.py
import os
import requests
from config import SECURE_LAYER_URL

token = os.environ.get("ARCGIS_TOKEN")
if token:
    print("Token loaded from environment, starts with:", token[:4] + "****")   # never print it fully
else:
    print("ARCGIS_TOKEN is not set - expecting an authentication error below")

headers = {"X-Esri-Authorization": f"Bearer {token}"} if token else {}
data = requests.post(f"{SECURE_LAYER_URL}/query",
                     data={"where": "1=1", "resultRecordCount": 1, "f": "json"},
                     headers=headers, timeout=30).json()

if "error" in data:
    code = data["error"].get("code")
    if code in (498, 499):
        print(f"Token missing/invalid/expired (code {code}): renew it using your approved flow")
    else:
        print("ArcGIS error:", code, data["error"].get("message"))
else:
    print("Secured query OK, features:", len(data["features"]))
