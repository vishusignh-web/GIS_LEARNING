# Topic 11: GeometryServer - buffer a location, then query nearby features
import gis_client
from config import GEOMETRY_URL, LAYER_URL

polygon = gis_client.buffer_point(GEOMETRY_URL, x=55.225, y=25.152, meters=800)
ring = polygon["rings"][0]
print("Buffer ring vertices:", len(ring), "| closed:", ring[0] == ring[-1])

nearby = gis_client.query_features(LAYER_URL, geometry=polygon, geometry_type="esriGeometryPolygon",
                                   in_sr=4326, out_fields="PARCEL_ID,AREA")
print(f"{len(nearby)} features nearby:", [f["attributes"]["PARCEL_ID"] for f in nearby])

print("Project 4326 -> 3857:", gis_client.project_points(GEOMETRY_URL, [{"x": 55.27, "y": 25.20}], 4326, 3857))
print("Areas:", gis_client.areas_and_lengths(GEOMETRY_URL, [polygon])["areas"])
