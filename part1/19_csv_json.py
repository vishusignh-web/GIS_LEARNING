# Topic 19: text, CSV and JSON files
import csv
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"

with open(DATA / "parcels.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["area"] = float(r["area"])          # CSV values are always text

summary = {"count": len(rows), "total_area": sum(r["area"] for r in rows)}
with open(DATA / "summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(summary)

r1 = [r for r in rows if r["zoning"] == "R1"]
with open(DATA / "parcels_r1.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["parcel_id", "area", "zoning"])
    writer.writeheader()
    writer.writerows(r1)
print("Wrote", len(r1), "R1 parcels")

with open(DATA / "summary.json", encoding="utf-8") as f:
    print("Read back:", json.load(f))
