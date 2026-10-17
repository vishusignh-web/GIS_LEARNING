# Topic 14: errors, logging, timeouts, retries
import logging
import requests
import gis_client
from config import BASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("demo")

# 1. Temporary failure: the 'Flaky' service returns HTTP 503 twice, then succeeds
requests.get(BASE.replace("/arcgis/rest/services", "") + "/mock/reset")
body = gis_client.request_json(f"{BASE}/Flaky/FeatureServer/0/query",
                               {"where": "1=1", "resultRecordCount": 1}, retries=4, backoff=0.2)
log.info("Flaky service recovered, features: %d", len(body["features"]))

# 2. ArcGIS JSON error inside an HTTP 200 response (not retried)
try:
    gis_client.request_json(f"{BASE}/Parcels/FeatureServer/0/query", {"where": "bad sql"})
except gis_client.GisError as e:
    log.error("ArcGIS error handled: %s", e)

# 3. Timeout: the 'Slow' service waits 3 seconds, we allow 1
try:
    gis_client.request_json(f"{BASE}/Slow/FeatureServer/0/query", {"where": "1=1"},
                            retries=2, backoff=0.1, timeout=(2, 1))
except requests.Timeout:
    log.error("Slow service timed out after 2 attempts")

# 4. Unreachable server
try:
    gis_client.request_json("http://127.0.0.1:9/arcgis", {"where": "1=1"}, retries=2, backoff=0.1)
except requests.ConnectionError:
    log.error("Service unreachable after 2 attempts")
