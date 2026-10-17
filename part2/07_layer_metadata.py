# Topic 7: Feature Service structure
import gis_client
from config import LAYER_URL

meta = gis_client.get_layer_metadata(LAYER_URL)
print("Name        :", meta.get("name"))
print("Geometry    :", meta.get("geometryType"))
print("Capabilities:", meta.get("capabilities"))
print("OID field   :", meta.get("objectIdField"), "| display field:", meta.get("displayField"))
print()
for field in meta.get("fields", []):
    line = f"{field['name']:<12} {field['type']}"
    domain = field.get("domain")
    if domain and domain.get("type") == "codedValue":
        codes = {c["code"]: c["name"] for c in domain["codedValues"]}
        line += f"  domain={codes}"
    print(line)
