# Topic 2: label resource, endpoint, operation and parameters
from urllib.parse import urlparse, parse_qs
from config import LAYER_URL

url = f"{LAYER_URL}/query?where=ZONING%3D%27R1%27&outFields=*&f=json"
u = urlparse(url)
parts = u.path.strip("/").split("/")

print("Server   :", f"{u.scheme}://{u.netloc}")
print("Service  :", "/".join(parts[:-3]))
print("Resource :", "/".join(parts[-3:-1]), "(layer 0 of the FeatureServer)")
print("Operation:", parts[-1])
print("Params   :", {k: v[0] for k, v in parse_qs(u.query).items()})
print()
print("query          -> read-only, idempotent (repeat safely)")
print("applyEdits     -> NOT idempotent (repeating may create duplicates)")
print("Stateless      -> every request carries all it needs (where, fields, token)")
