# 📊 AI Dashboard Generator Backend

> **This is the current active backend.** It powers the CSV Chat Agent analysis and RAG chatbot through Mission Control.

---

## 🎯 Quick Links

- **Main Project Setup** → [../README.md](../README.md)
- **Current Status & Troubleshooting** → [../STATUS.md](../STATUS.md)  
- **Quick Start Guide** → [../QUICK_START.txt](../QUICK_START.txt)
- **Mission Control Docs** → [../mission-control/README.md](../mission-control/README.md)

---

## 🚀 Start This Backend

### Option A: Automated (Recommended)
```bash
# From root directory
START_ALL.bat    # Windows
./start.sh       # macOS/Linux
```

### Option B: Manual
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8010
```

### Option C: Start Ollama First
```bash
# Terminal 1: Ollama service
ollama serve
ollama pull llama3.1 nomic-embed-text

# Terminal 2: Backend API  
cd ai-dashboard-generator/backend
python -m uvicorn app:app --port 8010
```

---

## 📡 API Endpoints

The backend runs on `http://localhost:8010` and provides:

```
POST   /upload                  Upload CSV/Excel files
POST   /chat                    Query the RAG chatbot
GET    /health                  Service health check
GET    /docs                    Interactive Swagger UI
GET    /redoc                   ReDoc API documentation
```

**Full API Docs**: http://localhost:8010/docs (when running)

---

## 🔧 Core Components

| File | Purpose |
|------|---------|
| `app.py` | FastAPI application & routes |
| `services/` | Business logic (upload, chat, analysis) |
| `models/` | Data models & schemas |
| `utils/` | Helper functions |
| `requirements.txt` | Python dependencies |

---

## 📚 Key Features

✅ **Multi-CSV Upload** - Upload and analyze multiple files  
✅ **RAG Chatbot** - LangChain + ChromaDB embeddings  
✅ **Smart Analysis** - Auto-detects columns, metrics, aggregations  
✅ **Ollama Integration** - Local LLM, no API costs  
✅ **Health Monitoring** - Real-time service health checks  

---

## 🛠️ Configuration

Edit `app.py` to customize:
- `UPLOAD_DIR` - Where CSV files are stored
- `OLLAMA_BASE_URL` - LLM endpoint (default: http://localhost:11434)
- `CORS_ORIGINS` - Allowed frontend origins
- Model selection - Change default embedding/generation models

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8010 in use | `Get-Process python \| Stop-Process` |
| Ollama not found | Start: `ollama serve` |
| Import errors | Run: `pip install -r requirements.txt` |
| CORS errors | Check `CORS_ORIGINS` in `app.py` |

**More help?** → See [../STATUS.md](../STATUS.md#-troubleshooting)

---

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pandas API Reference](https://pandas.pydata.org/docs/)
- [Ollama Models](https://ollama.ai/library)
- [LangChain Docs](https://python.langchain.com/)

---

**Status**: ✅ Active Production  
**Version**: 2.0.0  
**Port**: 8010  
**Last Updated**: April 7, 2026

