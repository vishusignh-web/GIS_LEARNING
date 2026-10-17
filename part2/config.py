"""Central configuration for Part 2. Values come from environment variables
(or a .env file next to this file). Defaults point to the local mock server
(mock_arcgis.py) so every exercise runs offline. To use a real service,
set the variables in .env -- never hard-code tokens in source files."""
import os
from pathlib import Path


def _load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).parent / ".env")

BASE = os.getenv("ARCGIS_BASE_URL", "http://127.0.0.1:8080/arcgis/rest/services")
LAYER_URL = os.getenv("ARCGIS_LAYER_URL", f"{BASE}/Parcels/FeatureServer/0")
SECURE_LAYER_URL = os.getenv("ARCGIS_SECURE_LAYER_URL", f"{BASE}/Secure/FeatureServer/0")
GEOMETRY_URL = os.getenv("ARCGIS_GEOMETRY_URL", f"{BASE}/Utilities/Geometry/GeometryServer")
GP_TASK_URL = os.getenv("ARCGIS_GP_TASK_URL", f"{BASE}/Tools/GPServer/Buffer")
# ARCGIS_TOKEN is read by gis_client at call time (never printed or logged).
