# Terminal 1 - Backend Server
cd backend 
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend Server
cd frontend
npm run dev
