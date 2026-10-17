# Topic 8: attribute and spatial queries
import gis_client
from config import LAYER_URL

envelope = {"xmin": 55.20, "ymin": 25.14, "xmax": 55.235, "ymax": 25.17,
            "spatialReference": {"wkid": 4326}}

print("Attribute query (R1, ID/AREA/ZONING only):")
for f in gis_client.query_features(LAYER_URL, where="ZONING = 'R1'", out_fields="PARCEL_ID,AREA,ZONING"):
    print("  ", f["attributes"])

print("\nSpatial query (envelope):")
feats = gis_client.query_features(LAYER_URL, geometry=envelope, geometry_type="esriGeometryEnvelope",
                                  in_sr=4326, out_fields="PARCEL_ID,AREA", order_by="AREA DESC")
print("  ", [(f["attributes"]["PARCEL_ID"], f["attributes"]["AREA"]) for f in feats])

print("\nCount only:", gis_client.query_count(LAYER_URL, "ZONING = 'C1'"))
print("Count in envelope:", gis_client.query_count(LAYER_URL, geometry=envelope,
                                                   geometry_type="esriGeometryEnvelope", in_sr=4326))
