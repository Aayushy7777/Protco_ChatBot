# 🚀 CSV Chat Agent - Production Architecture (v2.0)

Advanced AI agent for CSV analysis with **OpenClaw orchestration**, **RAG pipeline**, and **Vector embeddings**.

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          FastAPI Backend (async, production-ready)           │
│  - /api/chat      → Chat endpoint                           │
│  - /api/upload    → File upload                             │
│  - /health        → Health check                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│        OpenClaw Agent Orchestrator (Brain Layer)            │
│  - Intent Classification                                    │
│  - Tool Selection & Routing                                 │
│  - Context Management                                       │
│  - Response Assembly                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   ┌────────┐   ┌──────────┐   ┌──────────┐
   │ RAG    │   │ CSV Tool │   │Analytics │
   │Retriever    │Processor │   │Tool      │
   └────┬───┘   └──────────┘   └──────────┘
        │
        ↓
┌─────────────────────────────────────────────────────────────┐
│              Embeddings Service                              │
│      (Sentence Transformers - HuggingFace)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Vector Store (ChromaDB)                         │
│  - Persistent storage of embeddings                         │
│  - Fast similarity search                                   │
│  - Document retrieval                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ↓                             ↓
┌──────────────┐            ┌──────────────┐
│  Ollama LLM  │            │  Ollama LLM  │
│ (llama3.1)   │            │ (mistral:7b) │
│ (qwen:7b)    │            │ (qwen:7b)    │
└──────────────┘            └──────────────┘
```

## 📁 Folder Structure

```
CSV CHAT AGENT/
│
├── BACKEND/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── __init__.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py               # Chat endpoint
│   │   │   ├── upload.py             # File upload
│   │   │   └── health.py             # Health check
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── openclaw_agent.py     # ⭐ Agent orchestrator
│   │   │   ├── rag_pipeline.py       # ⭐ RAG implementation
│   │   │   ├── embeddings.py         # ⭐ Embeddings service
│   │   │   └── csv_processor.py      # CSV processing
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Configuration (Pydantic)
│   │   │   └── logger.py             # Structured logging
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── vector_store.py       # ⭐ ChromaDB wrapper
│   │   │
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schema.py             # Pydantic models
│   │
│   ├── openclaw/
│   │   ├── agent_config.yaml         # ⭐ Agent configuration
│   │   └── tools/
│   │       ├── retriever_tool.py
│   │       ├── csv_tool.py
│   │       └── aggregation_tool.py
│   │
│   ├── data/
│   │   ├── raw/                      # Uploaded CSVs
│   │   ├── processed/                # Processed data
│   │   └── vector_store/             # ChromaDB storage
│   │       └── chroma_db/
│   │
│   ├── logs/                         # Application logs
│   │   ├── app.log
│   │   └── error.log
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment config
│   ├── .env.example                  # Config template
│   └── main.py                       # Backward compat (links to app/)
│
├── FRONTEND/
│   ├── src/
│   ├── components/
│   └── package.json
│
├── docker/
│   ├── Dockerfile                    # Production Docker image
│   └── docker-compose.yml            # Multi-container setup
│
└── README.md                         # This file
```

## 🔧 Key Components

### 1. **OpenClaw Agent Orchestrator** (`services/openclaw_agent.py`)

The "brain" of the system. Routes user queries through a sophisticated pipeline:

```
User Query
    ↓
Intent Classification (fast, deterministic)
    ↓
RAG Retrieval (if enabled)
    ↓
Tool Selection & Routing
    ↓
LLM Generation
    ↓
Response Assembly
```

**Intent Types:**
- `CHART` → Generate visualization
- `TABLE` → Return raw data
- `STATS` → Calculate statistics
- `DASHBOARD` → Multi-widget dashboard
- `CHAT` → General conversation

### 2. **RAG Pipeline** (`services/rag_pipeline.py`)

Retrieval-Augmented Generation for context-aware responses:

- **Document Ingestion**: CSV → Chunks → Embeddings → Vector Store
- **Retrieval**: Query → Similar Documents → Context
- **Context Building**: Format retrieved docs for LLM

### 3. **Vector Store** (`db/vector_store.py`)

ChromaDB-based persistent storage for embeddings:

```python
# Add documents
vector_store.add_documents(
    documents=["fact1", "fact2"],
    metadatas=[{"source": "sales.csv"}, ...],
    ids=["doc_1", "doc_2"]
)

# Search
results = vector_store.search("top revenue", top_k=5)
```

### 4. **Embeddings Service** (`services/embeddings.py`)

HuggingFace Sentence Transformers for semantic embeddings:

```python
embeddings = get_embeddings_service()
vector = embeddings.embed_text("Your text here")
```

### 5. **Configuration System** (`core/config.py`)

Pydantic-based configuration with environment variable support:

```python
from app.core.config import settings

print(settings.OLLAMA_BASE_URL)        # http://localhost:11434
print(settings.CHUNK_SIZE)             # 500
print(settings.TOP_K_RETRIEVAL)        # 5
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- Ollama (with models downloaded)
- Docker (optional)

### Local Setup

1. **Install dependencies:**
   ```bash
   cd BACKEND
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

3. **Ensure Ollama is running:**
   ```bash
   ollama serve
   ```

4. **Start backend:**
   ```bash
   cd BACKEND
   python -m uvicorn app.main:app --reload --port 8000
   ```

5. **Start frontend:**
   ```bash
   cd FRONTEND
   npm install && npm run dev
   ```

### Docker Setup

```bash
# Build and run all services
docker-compose -f docker/docker-compose.yml up -d

# Check logs
docker-compose -f docker/docker-compose.yml logs -f backend
```

## 📋 Configuration

Edit `.env` or `openclaw/agent_config.yaml`:

```yaml
# agent_config.yaml
agent:
  name: csv_chat_agent
  
llm:
  provider: ollama
  models:
    intent_classifier: mistral:7b
    chat: llama3.1:8b
    chart_generation: qwen2.5:7b

rag:
  enabled: true
  vector_store:
    type: chromadb
  chunking:
    chunk_size: 500
    chunk_overlap: 50
```

## 🔌 API Endpoints

### Chat
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "What were the top 5 companies?",
  "active_file": "sales.csv",
  "all_files": ["sales.csv"]
}

Response:
{
  "intent": "CHAT",
  "answer": "Based on the data...",
  "context_used": "Retrieved context from sales.csv",
  "error": null
}
```

### Upload
```bash
POST /api/upload
(multipart/form-data with file)
```

### Health
```bash
GET /health

Response:
{
  "status": "ok",
  "ollama_status": "ready",
  "vector_store_status": "ready"
}
```

## 📊 Production Best Practices

✅ **1. Async FastAPI**
- Non-blocking I/O
- High concurrency (10+ concurrent requests)

✅ **2. Structured Logging (JSON)**
- ELK stack compatible
- Better debugging

✅ **3. Vector Store Persistence**
- ChromaDB with parquet backend
- Fast retrieval without re-embedding

✅ **4. Configuration Management**
- Pydantic Settings
- Environment-based overrides

✅ **5. Error Handling**
- Comprehensive try-catch blocks
- Graceful degradation

✅ **6. Health Checks**
- Endpoint monitoring
- Docker health checks

✅ **7. Model Management**
- Lazy loading
- Hot swapping

✅ **8. Rate Limiting** (Coming soon)
- Prevent abuse

## 🧪 Testing

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/

# Load testing
locust -f tests/load.py
```

## 📈 Monitoring & Logs

**Logs Location:**
```
BACKEND/logs/
├── app.log          # All logs
└── error.log        # Errors only
```

**With ELK Stack:**
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

## 🔐 Security Best Practices

- [ ] API authentication (JWT/OAuth)
- [ ] Rate limiting
- [ ] Input validation
- [ ] CORS configuration
- [ ] Environment variable management
- [ ] Secret management (AWS Secrets Manager)

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/xyz`
2. Commit changes: `git commit -m "Add xyz"`
3. Push: `git push origin feature/xyz`
4. Open PR

## 📝 Changelog

### v2.0.0 (Current)
- ✨ OpenClaw agent orchestrator
- ✨ RAG pipeline with ChromaDB
- ✨ HuggingFace embeddings
- ✨ Production folder structure
- ✨ Docker Compose setup
- ✨ Pydantic configuration system
- ✨ Structured JSON logging

### v1.0.0
- Initial agent.py implementation

## 📞 Support

- Issues: GitHub Issues
- Docs: `/docs` (Swagger UI)
- Email: support@example.com

## 📜 License

MIT License - see LICENSE file

---

**Last Updated:** April 2026  
**Maintainer:** CSV Chat Agent Team
