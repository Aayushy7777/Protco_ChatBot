# Terminal 1 - Backend Server (Running on port 8888)
cd BACKEND
python -m uvicorn app.main:app --host 0.0.0.0 --port 8888

# Terminal 2 - Frontend Server
cd FRONTEND
npm run dev

# Note: 
# - Backend API: http://localhost:8888
# - Frontend (dev): http://localhost:5173 (or 5174, 3000)
# - Swagger Docs: http://localhost:8888/docs
# - Health Check: http://localhost:8888/health
