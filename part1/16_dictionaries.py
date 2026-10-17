# Topic 16: dictionaries and GIS records
parcels = [
    {"parcel_id": "P1", "area": 450.5, "zoning": "R1", "vacant": True},
    {"parcel_id": "P2", "area": 725.0, "zoning": "C1", "vacant": False,
     "owner": {"name": "A. Khan", "type": "Private"}},
]
parcels[0]["area"] = 460.0
print(parcels[0].get("owner", "Unknown"))
print("Owner name:", parcels[1]["owner"]["name"])

for key, value in parcels[0].items():
    print(key, "=", value)

print("Vacant IDs:", [p["parcel_id"] for p in parcels if p["vacant"]])   #Vacant IDs: ['P1']
print("Keys:", list(parcels[0].keys()))                                   #Keys: ['parcel_id', 'area', 'zoning', 'vacant']
