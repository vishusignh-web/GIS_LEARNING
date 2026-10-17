# Topic 6: ArcGIS REST Services Directory
from config import BASE, LAYER_URL
import gis_client

root = gis_client.get_services_directory(BASE)
print("Folders :", root.get("folders"))
print("Services:", [f"{s['name']} ({s['type']})" for s in root.get("services", [])])

meta = gis_client.get_layer_metadata(LAYER_URL)
print("\nLayer            :", meta["name"])
print("Spatial reference:", meta["spatialReference"])
print("Capabilities     :", meta["capabilities"])
print("maxRecordCount   :", meta["maxRecordCount"], "| supportsPagination:", meta.get("supportsPagination"))
print("Fields           :", [f["name"] for f in meta["fields"]])
print("Query operation  :", f"{LAYER_URL}/query")
print("\nTip: open", BASE, "in a browser and try the Query page for your layer.")
