# Topic 20: errors, testing and debugging
import csv
from pathlib import Path

DATA = Path(__file__).parent / "data"

def load_areas(path):
    areas = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for line_no, row in enumerate(csv.DictReader(f), start=2):
                try:
                    area = float(row["area"])
                    if area <= 0:
                        print(f"Line {line_no}: area must be positive ({area})")
                        continue
                    areas.append(area)
                except KeyError:
                    print(f"Line {line_no}: missing 'area' column")
                except (ValueError, TypeError):
                    print(f"Line {line_no}: invalid area '{row.get('area')}'")
    except FileNotFoundError:
        print(f"File not found: {path}")
    else:
        print(f"Loaded {len(areas)} areas")
    finally:
        print("Finished reading")
    return areas

load_areas(DATA / "missing.csv")
load_areas(DATA / "parcels.csv")

bad = DATA / "bad.csv"
bad.write_text("parcel_id,area\nP1,abc\nP2,-5\nP3,100\nP4,\n", encoding="utf-8")
print(load_areas(bad))
