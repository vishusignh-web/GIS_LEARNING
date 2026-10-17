# Topic 21: Python foundations practical application
# Run:  python 21_parcel_summary.py [path/to/parcels.csv]
import csv
import sys
from pathlib import Path

DEFAULT = Path(__file__).parent / "data" / "parcels.csv"

def read_parcels(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def summarize(parcels):
    if not parcels:
        raise ValueError("No parcel records found")
    areas = [float(p["area"]) for p in parcels]
    return {
        "count": len(areas),
        "total": round(sum(areas), 2),
        "largest": max(areas),
        "zones": sorted({p["zoning"] for p in parcels}),
    }

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    try:
        result = summarize(read_parcels(path))
    except FileNotFoundError:
        print(f"{path} not found")
        return 1
    except (ValueError, KeyError) as e:
        print("Bad data:", e)
        return 1
    print(result)
    assert result == {"count": 3, "total": 1475.75, "largest": 725.0, "zones": ["C1", "R1"]} or path != DEFAULT
    return 0

if __name__ == "__main__":
    sys.exit(main())
