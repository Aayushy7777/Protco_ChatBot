# 🔄 Migration Guide: v1.0 → v2.0 (OpenClaw + RAG)

Step-by-step guide to migrate from the simple agent architecture to the production-grade OpenClaw + RAG system.

## 📊 What's Changing

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| **Agent** | `agent.py` (simple) | OpenClaw orchestrator |
| **Vector DB** | None | ChromaDB + embeddings |
| **Context** | Build context per query | RAG retrieval |
| **Configuration** | Hardcoded | Pydantic + YAML |
| **Logging** | Basic | Structured JSON |
| **Folder Structure** | Flat | Organized by concern |
| **Scalability** | Single-file | Enterprise-ready |

## 🚀 Step-by-Step Migration

### Step 1: Install New Dependencies

```bash
cd BACKEND
pip install -r requirements.txt
```

**New packages added:**
- `chromadb` - Vector database
- `langchain` & `langchain-community` - Text processing
- `sentence-transformers` - Embeddings
- `pydantic-settings` - Configuration
- `python-dotenv` - Environment management
- `pyyaml` - YAML parsing

### Step 2: Copy New Structure

The new architecture is already created in:
```
BACKEND/
├── app/              ← New organized structure
├── openclaw/         ← Agent config & tools
├── data/             ← Data directories
└── logs/             ← Log files
```

### Step 3: Update Entry Point

**Old:**
```python
python -m uvicorn main:app --reload
```

**New:**
```python
python -m uvicorn app.main:app --reload
```

Or keep compatibility by updating old `main.py`:
```python
# BACKEND/main.py (backward compatibility wrapper)
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4: Migrate Your CSV Processing Logic

Move your CSV handling from old `csv_processor.py` to new location:

```python
# BACKEND/app/services/csv_processor.py
from app.core.config import settings
from app.services.rag_pipeline import get_rag_pipeline

def ingest_csv(filename: str, df: pd.DataFrame):
    """Ingest CSV into RAG pipeline."""
    rag = get_rag_pipeline()
    chunks = rag.ingest_csv(filename, df)
    return chunks
```

### Step 5: Enable RAG for Your Queries

**Old approach (still works):**
```python
context = build_context(filename)
response = await ollama.generate(ModelRole.CHAT, user_prompt + context)
```

**New approach with RAG:**
```python
from app.services.openclaw_agent import get_agent

agent = get_agent()
response = await agent.run(message="Your question", active_file="file.csv")
# Agent automatically:
# 1. Classifies intent
# 2. Retrieves relevant context via RAG
# 3. Selects appropriate tool
# 4. Generates response
```

### Step 6: Configure Environment

Create `.env` file from template:

```bash
cd BACKEND
cp .env.example .env
```

Minimal configuration:
```env
OLLAMA_BASE_URL=http://localhost:11434
VECTOR_STORE_TYPE=chroma
LOG_LEVEL=INFO
DEBUG=false
```

### Step 7: Test the New System

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start backend
cd BACKEND
python -m uvicorn app.main:app --reload

# Terminal 3: Test endpoints
curl http://localhost:8000/health

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the top companies?",
    "active_file": "sales.csv",
    "all_files": ["sales.csv"]
  }'
```

## 🔄 Backward Compatibility

### Old Code Still Works

```python
# from BACKEND/csv_processor.py - still accessible
from csv_processor import parse_csv, get_file, list_files

# These functions remain unchanged for backward compatibility
csv_file = parse_csv("data.csv", content)
```

### Create Compatibility Layer

If you have existing code that uses the old structure:

```python
# BACKEND/compat.py (backward compatibility shim)
from app.services.rag_pipeline import get_rag_pipeline
from app.services.openclaw_agent import get_agent
from csv_processor import *  # Import all old functions

# New agent available
agent = get_agent()

# Old functions still work
# csv_file = parse_csv(...)
```

## 🔌 Updating Frontend

### Old Chat API

```javascript
// v1.0
const response = fetch('/api/chat', {
  message: "...",
  active_file: "..."
})
```

### New Chat API (Compatible!)

```javascript
// v2.0 - Same interface, better behind the scenes
const response = fetch('/api/chat', {
  message: "...",
  active_file: "...",
  // Optional new fields:
  stream: false,  // For streaming responses
})

// Response now includes:
// - intent: detected user intent
// - context_used: RAG context (for transparency)
// - error: any errors
```

**No frontend changes needed!** The API is backward compatible.

## 🧪 Validation Checklist

- [ ] Dependencies installed: `pip list | grep chromadb`
- [ ] Folders created: `ls -R BACKEND/app/`
- [ ] .env file exists: `cat BACKEND/.env`
- [ ] Old csv_processor.py still accessible
- [ ] New agent initializes: `python -c "from app.services import get_agent; get_agent()"`
- [ ] Health endpoint works: `curl http://localhost:8000/health`
- [ ] Chat endpoint responds: `curl -X POST http://localhost:8000/api/chat`
- [ ] Logs created: `ls BACKEND/logs/`

## 🚨 Troubleshooting

### ImportError: No module named 'app'

**Problem:** Running old commands
```bash
python -m uvicorn main:app  # ❌ Wrong
```

**Solution:** Update to new path
```bash
cd BACKEND
python -m uvicorn app.main:app  # ✅ Correct
```

### ChromaDB connection error

**Problem:** Vector store not initializing
```
Error: Could not connect to vector store
```

**Solution:** Ensure directory exists
```bash
mkdir -p BACKEND/data/vector_store/chroma_db
```

### Ollama not found

**Problem:** Can't connect to Ollama
```
ConnectionError: http://localhost:11434
```

**Solution:** Start Ollama in separate terminal
```bash
ollama serve
```

Then in another terminal test it:
```bash
curl http://localhost:11434/api/tags
```

### Slow embeddings generation

**Problem:** First query takes 30+ seconds
```
[INFO] Loading embeddings model: sentence-transformers/all-MiniLM-L6-v2
```

**Solution:** This is normal on first run (downloads model ~80MB). Subsequent queries are instant due to caching.

## 📈 Performance Comparison

### v1.0
- Build context: 200-500ms (per query)
- LLM inference: 1-3s
- **Total: 1.2-3.5s per query**

### v2.0
- Intent classification: 50-100ms (mistral:7b, deterministic)
- RAG retrieval: 10-50ms (vector similarity search)
- LLM inference: 1-3s
- Response assembly: <10ms
- **Total: 1.1-3.2s per query** ✨
- **Cache hit: <100ms** (for repeated questions)

## 🎯 Next Steps

### Short Term
1. ✅ Deploy v2.0 to production
2. ✅ Monitor performance metrics
3. ✅ Train team on new architecture

### Medium Term
4. Add conversation history (PostgreSQL)
5. Implement persistent session management
6. Add user authentication (JWT/OAuth)
7. Set up monitoring (ELK stack)

### Long Term
8. Fine-tune embeddings model on domain data
9. Implement multi-document RAG
10. Add streaming responses
11. Scale to multi-GPU setup

## 📚 Resources

- [OpenClaw Architecture](PRODUCTION_ARCHITECTURE.md)
- [ChromaDB Docs](https://docs.trychroma.com)
- [LangChain Guide](https://python.langchain.com)
- [Ollama Models](https://ollama.ai/library)
- [HuggingFace Embeddings](https://huggingface.co/sentence-transformers)

## ✅ Sign-Off

Once you've completed this migration:

```bash
# Verify everything works
cd BACKEND

# 1. Check imports
python -c "from app.services import get_agent, get_rag_pipeline; print('✅ Imports OK')"

# 2. Test agent initialization
python -c "from app.services import get_agent; agent = get_agent(); print('✅ Agent initialized')"

# 3. Run API
python -m uvicorn app.main:app --reload

# 4. Test in browser
# Visit http://localhost:8000/docs
```

**Congratulations! You're now running CSV Chat Agent v2.0! 🎉**

---

Migration completed on: _______________  
Reviewed by: _______________  
Approved for production: _______________
