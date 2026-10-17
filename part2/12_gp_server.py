# Topic 12: GPServer - submit job, poll, fetch results
import logging
import gis_client
from config import GP_TASK_URL

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

task = gis_client.get_layer_metadata(GP_TASK_URL)   # GET with f=json
print("Execution type:", task["executionType"])
print("Parameters    :", [p["name"] for p in task["parameters"]])

results = gis_client.run_gp_job(GP_TASK_URL, {"Input_Distance": 500}, poll_seconds=1, max_wait=30)
print("Job results   :", results)

sync = gis_client.request_json(f"{GP_TASK_URL}/execute", {"Input_Distance": 250})
print("Synchronous   :", sync["results"][0]["value"])
