# Topic 2: create the project folder structure (run once, in an empty location)
# Then in a terminal:  python -m venv .venv  ->  activate  ->  pip install requests  ->  pip freeze > requirements.txt
from pathlib import Path

root = Path("gis_service_project")
for folder in ["src", "data", "config", "tests"]:
    (root / folder).mkdir(parents=True, exist_ok=True)
(root / "requirements.txt").touch()
print("Created:", *sorted(str(p) for p in root.iterdir()), sep="\n  ")
