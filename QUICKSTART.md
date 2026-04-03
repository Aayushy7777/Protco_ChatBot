# 📋 CSV Chat Agent v2.0 - Quick Reference

## 🚀 Quick Start (5 minutes)

### 1. Install & Setup
```bash
# Windows
setup.bat

# macOS/Linux
bash setup.sh
```

### 2. Start Ollama (Terminal 1)
```bash
ollama serve
```

### 3. Start Backend (Terminal 2)
```bash
cd BACKEND
python -m uvicorn app.main:app --reload
```

### 4. Verify Setup (Terminal 3 - optional)
```bash
python verify_setup.py
```

### 5. Access API
- 📊 Swagger Docs: http://localhost:8000/docs
- 🏥 Health Check: http://localhost:8000/health

---

## 🔌 API Endpoints

### Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What were the top 5 companies?",
    "active_file": "sales.csv",
    "all_files": ["sales.csv"]
  }'
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## 📁 Project Structure

```
CSV CHAT AGENT/
├── BACKEND/
│   ├── app/
│   │   ├── core/         ← Config & logging
│   │   ├── db/           ← Vector store
│   │   ├── services/     ← RAG, embeddings, agent
│   │   ├── routes/       ← API endpoints
│   │   ├── models/       ← Data schemas
│   │   └── main.py       ← FastAPI app
│   ├── openclaw/         ← Agent config & tools
│   ├── data/             ← CSV storage & embeddings
│   ├── logs/             ← Application logs
│   ├── requirements.txt
│   ├── .env              ← Configuration
│   └── .env.example
├── FRONTEND/
├── docker/
├── PRODUCTION_ARCHITECTURE.md
├── MIGRATION_GUIDE.md
└── verify_setup.py
```

---

## ⚙️ Configuration

Edit `BACKEND/.env`:

```env
# LLM
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=llama3.1:8b
INTENT_MODEL=mistral:7b

# Vector Store
VECTOR_STORE_TYPE=chroma
CHUNK_SIZE=500
TOP_K_RETRIEVAL=5

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 🔄 Agent Pipeline

```
User Query
    ↓
Intent Classifier (mistral:7b)
    ├→ CHART (visualization)
    ├→ TABLE (raw data)
    ├→ STATS (statistics)
    ├→ DASHBOARD (overview)
    └→ CHAT (conversation)
    ↓
RAG Retrieval (if enabled)
    ├→ Query embedding
    ├→ Similarity search
    └→ Context building
    ↓
Tool Selection
    ├→ retriever_tool
    ├→ csv_processor_tool
    └→ aggregation_tool
    ↓
LLM Generation (llama3.1:8b)
    ↓
Response Assembly
```

---

## 📊 Key Technologies

| Component | Technology | Details |
|-----------|-----------|---------|
| Web Server | FastAPI | Async, production-ready |
| Vector DB | ChromaDB | Persistent embeddings |
| Embeddings | Sentence Transformers | HuggingFace (L6-v2) |
| LLM | Ollama | Local inference |
| Config | Pydantic | Type-safe settings |
| Logging | JSON/Structured | ELK compatible |

---

## 🧪 Testing Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```
Response: `{"status": "ok", "ollama_status": "ready", ...}`

### 2. Chat Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "active_file": "",
    "all_files": []
  }'
```
Response:
```json
{
  "intent": "CHAT",
  "answer": "Chat response...",
  "context_used": null,
  "error": null
}
```

### 3. Swagger UI
Visit: **http://localhost:8000/docs**

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `PRODUCTION_ARCHITECTURE.md` | Full architecture guide |
| `MIGRATION_GUIDE.md` | v1.0 → v2.0 migration |
| `verify_setup.py` | Setup validation script |
| `setup.sh` / `setup.bat` | Automated setup |

---

## 🐛 Troubleshooting

### Ollama Not Found
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Import Errors
```bash
# From BACKEND directory
python -m pip install -r requirements.txt

# Verify
python verify_setup.py
```

### Slow First Query
This is normal! First query:
1. Loads embeddings model (~80MB) - 10-30s
2. Initializes ChromaDB - 5-10s
3. Runs inference - 1-3s

Subsequent queries are <100ms.

---

## 🎯 Common Tasks

### View Logs
```bash
# All logs
tail -f BACKEND/logs/app.log

# Errors only
tail -f BACKEND/logs/error.log
```

### Clear Vector Store
```bash
rm -rf BACKEND/data/vector_store/chroma_db
```

### Update Configuration
Edit `BACKEND/.env` and restart:
```bash
# Ctrl+C to stop current process
python -m uvicorn app.main:app --reload
```

### Check Dependencies
```bash
python verify_setup.py
```

---

## 📈 Performance Tips

✅ **Cache embeddings** - Reused automatically  
✅ **Use appropriate chunk size** - 500 chars recommended  
✅ **Limit RAG results** - TOP_K_RETRIEVAL=5  
✅ **Monitor logs** - JSON format for parsing  
✅ **Health checks** - Endpoints monitored every 30s  

---

## 🚀 Production Deployment

### Docker Compose
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Environment
```bash
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Monitoring
- Health endpoint: `/health`
- Logs: `BACKEND/logs/`
- Metrics: Add to OpenTelemetry (future)

---

## 📞 Support

- 📖 Docs: `/docs` (Swagger UI)
- 🏥 Health: GET `/health`
- 🐛 Issues: Check logs in `BACKEND/logs/`

---

**CSV Chat Agent v2.0** | April 2026  
**Status:** Production-ready with OpenClaw + RAG
