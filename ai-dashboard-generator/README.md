# AI Dashboard Generator with Chatbot

Production-ready full-stack project with:
- multi-CSV upload
- automatic schema understanding
- RAG chatbot (LangChain + Ollama + ChromaDB)
- natural-language dashboard generation
- dynamic React dashboard renderer (Plotly)

## Folder structure

```text
ai-dashboard-generator/
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── utils/
├── frontend/
│   └── src/
├── data/
├── requirements.txt
└── README.md
```

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start Ollama:

```bash
ollama serve
ollama pull llama3.1
ollama pull nomic-embed-text
```

Run backend:

```bash
uvicorn app:app --reload --port 8010
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open:
- Backend: `http://localhost:8010`
- Frontend: `http://localhost:5173`

## API endpoints

- `POST /upload` -> upload multiple CSV files
- `POST /chat` -> query chatbot or generate dashboard
- `GET /dashboard` -> last generated dashboard JSON
- `GET /health` -> service health

## Example queries

- "What is total revenue?"
- "Top 5 products?"
- "Show monthly trend"
- "Create dashboard with sales and category comparison"
