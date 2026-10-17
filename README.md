# Python REST API

# Setup  Part 1: mock ArcGIS 
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
``
#cd part2 && python mock_arcgis.py

# Terminal 3: backend
cd part3 && uvicorn app.main:app --reload

# Terminal 3: frontend 
cd frontend && npm install && npm run dev



