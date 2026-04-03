from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat_router, dashboard_router, upload_router


app = FastAPI(title="AI Dashboard Generator with Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

