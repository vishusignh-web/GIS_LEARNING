# Topic 17: integration exercise - spatial query -> validate -> CSV + JSON + error report
import csv
import json
import logging
import sys
from pathlib import Path
import gis_client
from config import LAYER_URL

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("export")

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
ENVELOPE = {"xmin": 55.20, "ymin": 25.14, "xmax": 55.27, "ymax": 25.17, "spatialReference": {"wkid": 4326}}
FIELDS = ["PARCEL_ID", "AREA", "ZONING"]


def validate(feature):
    a = feature.get("attributes", {})
    if not a.get("PARCEL_ID"):
        return "missing PARCEL_ID"
    if not isinstance(a.get("AREA"), (int, float)) or a["AREA"] <= 0:
        return "invalid AREA"
    return None


def main():
    try:
        feats = gis_client.query_features(LAYER_URL, out_fields=",".join(FIELDS),
                                          geometry=ENVELOPE, geometry_type="esriGeometryEnvelope",
                                          in_sr=4326, return_geometry=True, page_size=5)
    except Exception as e:
        log.error("Query failed: %s", e)
        return 1

    good, bad = [], []
    for f in feats:
        problem = validate(f)
        (bad if problem else good).append((f, problem))

    with open(DATA / "export.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(f["attributes"] for f, _ in good)
    with open(DATA / "export.json", "w", encoding="utf-8") as fh:
        json.dump({"valid": [f for f, _ in good],
                   "rejected": [{"feature": f, "reason": r} for f, r in bad]}, fh, indent=2)

    log.info("Total %d | valid %d | rejected %d", len(feats), len(good), len(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
