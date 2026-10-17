# Topic 16: write API results to CSV and JSON
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import gis_client
from config import LAYER_URL

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
FIELDS = ["PARCEL_ID", "AREA", "ZONING"]
WHERE = "ZONING = 'R1'"

features = gis_client.query_features(LAYER_URL, where=WHERE, out_fields=",".join(FIELDS), return_geometry=True)

with open(DATA / "parcels_out.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    for feat in features:
        writer.writerow({k: feat["attributes"].get(k) for k in FIELDS})   # stable columns

with open(DATA / "parcels_out.json", "w", encoding="utf-8") as f:
    json.dump({"exported_at": datetime.now(timezone.utc).isoformat(),
               "layer": LAYER_URL, "where": WHERE, "count": len(features),
               "features": features}, f, indent=2)

print(f"Wrote {len(features)} rows to {DATA}")
print((DATA / "parcels_out.csv").read_text())
