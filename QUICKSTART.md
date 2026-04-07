## Quick Start Guide

### 1. Prerequisites
- Python 3.8+
- Ollama running locally (`ollama serve`)
- Virtual environment: `ai_env`

### 2. Setup Backend
```bash
cd ai-dashboard/backend
python -m uvicorn main:app --port 8011 --host 127.0.0.1
```

### 3. Upload & Query
```bash
# Upload CSV
curl -F "file=@data.csv" http://127.0.0.1:8011/upload

# Ask question
curl -X POST http://127.0.0.1:8011/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Top 5 customers by amount"}'
```

### Environment Setup
Copy `.env.example` to `.env` in `ai-dashboard/backend/`:
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
PORT=8011
```

See README_SETUP.md for detailed instructions.
