# 📊 Project Status & Architecture

**Last Updated**: April 7, 2026  
**Status**: ✅ Production Ready with AI Integration

---

## 🎯 Current Architecture

```
CSV CHAT AGENT
├── 📡 Mission Control (Port 3000)
│   ├── Agent orchestration dashboard
│   ├── Real-time status monitoring
│   ├── Agent management & task dispatch
│   └── Security & RBAC
│
├── 🤖 Backend (Port 8010)  
│   ├── CSV/Excel upload & processing
│   ├── Pandas data analysis
│   ├── RAG chatbot (LangChain + ChromaDB)
│   ├── Auto-generated dashboards
│   └── FastAPI REST endpoints
│
└── 🧠 Ollama (Port 11434)
    ├── Local LLM inference
    ├── Models: llama3.1, nomic-embed-text
    └── Zero cloud dependencies
```

---

## 🚀 Quick Start

### **Option A: One-Click Start**
```bash
START_ALL.bat
# Opens automatically to http://localhost:3000
```

### **Option B: Manual Start**
```powershell
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Backend
cd ai-dashboard-generator\backend
start-backend.bat

# Terminal 3: Start Mission Control
cd mission-control
pnpm dev
```

---

## ✅ Service Status Checklist

| Service | Port | Status | Health Check |
|---------|------|--------|--------------|
| Mission Control | 3000 | ✅ Running | http://localhost:3000 |
| Backend API | 8010 | ✅ Running | http://localhost:8010/health |
| Ollama | 11434 | ✅ Running | ollama list (models loaded) |

**Check in Mission Control Dashboard:**
- Go to "CSV Chat Dashboard" panel
- All 3 status lights should be 🟢 green

---

## 📁 Key Directories

| Directory | Purpose |
|-----------|---------|
| `mission-control/` | Main orchestration dashboard (Next.js) |
| `ai-dashboard-generator/backend/` | CSV analysis & RAG chatbot (FastAPI) |
| `ai_env/` | Python virtual environment |
| `chroma_data/` | ChromaDB vector database for embeddings |
| `docker/` | Docker deployment configs |

---

## 💡 Main Features

### 📊 CSV Dashboard
- Upload CSV/Excel files
- Auto-generate KPI charts
- AI-powered data insights
- Real-time table filtering

### 💬 AI Chat Analysis
- Query uploaded data in natural language
- RAG-powered (retrieval-augmented generation)
- Context-aware conversations
- Historical data memory

### 🎛️ Mission Control
- Agent fleet management
- Task dispatching & tracking
- Real-time monitoring
- Workflow orchestration

---

## 🔧 API Endpoints

### Backend (8010)
```
POST   /upload          Upload CSV file
POST   /chat            Query chatbot or generate dashboard
GET    /dashboard       Last generated dashboard
GET    /health          Health check
POST   /api/chat        Chat about dataset
```

### Mission Control (3000)
```
GET    /api/status      System status & metrics
GET    /api/agents      Agent list & status
POST   /api/tasks       Dispatch new task
GET    /api/dashboard   Dashboard data
```

---

## 📝 Configuration Files

- `.env` - Environment variables (ports, URLs, API keys)
- `ai-dashboard-generator/requirements.txt` - Python dependencies
- `mission-control/package.json` - Node dependencies
- `docker-compose.yml` - Docker orchestration

---

## 🧪 Testing

### Backend Health
```bash
curl http://localhost:8010/health
```

### Ollama Models
```bash
ollama list
```

### API Documentation
- Backend Swagger: `http://localhost:8010/docs`
- Mission Control Explore: `http://localhost:3000/api`

---

## 🛠️ Troubleshooting

### Ollama not found?
```bash
ollama serve
ollama pull llama3.1
ollama pull nomic-embed-text
```

### Backend won't connect?
```bash
cd ai-dashboard-generator\backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8010
```

### Port already in use?
```powershell
# Port 3000
Get-Process -Name node | Stop-Process -Force

# Port 8010
Get-Process -Name python | Stop-Process -Force

# Port 11434
Get-Process -Name ollama | Stop-Process -Force
```

### Mission Control errors?
- Check `.env` file for correct backend URL (8010)
- Ensure database is initialized: `pnpm db:init`
- Clear `.next` cache: `rm -r .next`

---

## 📈 Recent Updates

✅ Fixed Windows cross-platform issues in Mission Control  
✅ Enhanced API status endpoint for Windows compatibility  
✅ Improved service health monitoring  
✅ Consolidated documentation  

---

## 🔒 Security Notes

- **Local LLM**: No data sent to external APIs
- **SQLite Database**: Single-file, self-contained
- **RBAC**: Mission Control has role-based access controls
- **Environment**: Sensitive values in `.env` (never committed)

---

## 📚 Additional Resources

- **API Docs**: http://localhost:8010/docs
- **Mission Control Docs**: `mission-control/README.md`
- **Full Feature List**: See `README.md`
- **Troubleshooting**: Check `SETUP_GUIDE.md`

---

## 🎯 Next Steps

1. ✅ Start services (`START_ALL.bat`)
2. ✅ Verify green status lights in Mission Control
3. ✅ Upload a CSV file
4. ✅ Ask questions in the chat
5. ✅ Generate insights

**Questions?** Check individual component READMEs or run `START_ALL.bat --help`
