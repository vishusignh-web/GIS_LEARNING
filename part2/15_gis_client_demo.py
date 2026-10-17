# Topic 15: using the reusable gis_client module
import gis_client
from config import GEOMETRY_URL, LAYER_URL

meta = gis_client.get_layer_metadata(LAYER_URL)
print("Layer:", meta["name"])

feats = gis_client.query_features(LAYER_URL, where="ZONING = 'R1'", out_fields="PARCEL_ID,AREA", page_size=2)
print("R1 parcels (retrieved in pages of 2):", len(feats))
print("IDs:", [f["attributes"]["PARCEL_ID"] for f in feats])

poly = gis_client.buffer_point(GEOMETRY_URL, 55.225, 25.152, 500)
print("Buffer polygon keys:", list(poly))
