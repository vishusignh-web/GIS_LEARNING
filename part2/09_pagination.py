# Topic 9: pagination and object ID batching
import gis_client
from config import LAYER_URL

meta = gis_client.get_layer_metadata(LAYER_URL)
total = gis_client.query_count(LAYER_URL)
print("Server maxRecordCount:", meta["maxRecordCount"], "| total records:", total)

paged = gis_client.query_features(LAYER_URL, page_size=1000)   # server caps each page
print("Pagination returned :", len(paged))

batched = gis_client.query_by_object_ids(LAYER_URL, batch_size=4)
print("Object-ID batching  :", len(batched))

ids_paged = {f["attributes"]["OBJECTID"] for f in paged}
ids_batched = {f["attributes"]["OBJECTID"] for f in batched}
assert len(paged) == total == len(batched), "counts differ"
assert ids_paged == ids_batched and len(ids_paged) == total, "duplicates or gaps"
print("OK: all records retrieved once, no duplicates")
