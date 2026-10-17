Setup Instructions

1. Setup Python Environment

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

2. Start Mock ArcGIS Service

cd part2
python mock_arcgis.py

3. Start Backend

cd part3
uvicorn app.main:app --reload

4. Start Frontend

cd frontend
npm install
npm run dev

API Documentation: http://127.0.0.1:8000/docs

Frontend: http://localhost:5173
