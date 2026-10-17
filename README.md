# Python REST API & ArcGIS Service Development: Complete Code (Parts 1-3 + React Frontend)

Runnable code for every topic in the syllabus. All scripts were executed and verified.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Part 1: Python foundations (`part1/`)
Scripts `01_...py` to `21_...py`, one per topic. Run from inside `part1/`:
```bash
cd part1
python 01_hello_gis.py
echo "P-1001 Residential 450.5" | python 05_input_multiple_values.py   # or just run it and type
python 21_parcel_summary.py
```
`03_git_basics.sh` is a shell script; `02_setup_project.py` creates a sample project tree.

## Part 2: ArcGIS REST services (`part2/`)
Exercises `01_...py` to `17_...py`, plus:
- `gis_client.py`: reusable client (retries, timeouts, pagination, buffer/project, GP jobs)
- `config.py`: settings from environment / `.env`
- `mock_arcgis.py`: local mock of FeatureServer, GeometryServer and GPServer, so everything runs offline

```bash
cd part2
bash run_all.sh                          # starts the mock, runs all 17 exercises
# or manually, in two terminals:
python mock_arcgis.py                    # terminal 1
ARCGIS_TOKEN=secret123 python 13_authentication.py   # terminal 2
```

**Using a real ArcGIS service:** create `part2/.env` (never commit it):
```
ARCGIS_LAYER_URL=https://<server>/arcgis/rest/services/<Service>/FeatureServer/0
ARCGIS_GEOMETRY_URL=https://<server>/arcgis/rest/services/Utilities/Geometry/GeometryServer
ARCGIS_TOKEN=<token from your approved auth flow>
```
Then change field names (`PARCEL_ID`, `AREA`, `ZONING`) in the scripts to match your layer.
Use only sample or approved services.

## Part 3: FastAPI backend (`part3/`)
```bash
cd part3
python -m pytest -q                      # 14 tests, no ArcGIS needed

# live run against the mock:
(cd ../part2 && python mock_arcgis.py) &
uvicorn app.main:app --reload            # run from the part3 folder
```
Open http://127.0.0.1:8000/docs. Endpoints: `GET /health`, `GET /version`, `GET /layer/metadata`,
`POST /parcels/query`, `POST /parcels/query/geometry`, `POST /parcels/nearby`, `GET /parcels/{id}`.

Upstream failures become `502 Bad Gateway` or `504 Gateway Timeout` with safe messages.
Copy `.env.example` to `.env` for real services. ArcGIS tokens stay on the server.

> If you see `Could not import module "main"`, you are running uvicorn from the wrong folder.
> Run `uvicorn app.main:app` from `part3/` (the folder that contains `app/`).

## Frontend (`frontend/`): React + Vite
A small web app that calls the FastAPI backend: attribute search, parcel lookup, envelope query and
nearby search. ArcGIS URLs and tokens never reach the browser.

Requires Node.js 18+. Run in a third terminal (backend and, for demos, the mock must be running):
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The backend `.env` must allow this origin:
`ALLOWED_ORIGINS=["http://localhost:5173"]`. To point at a different backend, copy
`frontend/.env.example` to `frontend/.env` and set `VITE_API_URL`.

## Run the full stack on Windows (3 PowerShell windows, venv active in the first two)
```powershell
# 1  (part2)  python mock_arcgis.py          <- skip when using your real ArcGIS server
# 2  (part3)  uvicorn app.main:app --reload
# 3  (frontend)  npm run dev
```
With the mock, the default sample searches work: Block `11`, Zoning `R1`, the default envelope, and Nearby.
