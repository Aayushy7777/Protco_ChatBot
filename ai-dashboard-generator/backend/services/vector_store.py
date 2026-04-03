from __future__ import annotations

import os
from typing import Any, Dict, List

import chromadb
from langchain_ollama import OllamaEmbeddings


class VectorStoreService:
    def __init__(self, persist_dir: str = "./chroma_data", ollama_base_url: str = "http://localhost:11434") -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        os.environ.setdefault("OLLAMA_BASE_URL", ollama_base_url)
        self.emb = OllamaEmbeddings(model="nomic-embed-text")

    def create_embeddings(self, rows: List[str]) -> List[List[float]]:
        return self.emb.embed_documents(rows)

    def store_data(self, dataset_name: str, rows: List[str]) -> None:
        coll = self.client.get_or_create_collection(name=dataset_name)
        vectors = self.create_embeddings(rows)
        ids = [f"{dataset_name}_{i}" for i in range(len(rows))]
        coll.upsert(ids=ids, documents=rows, embeddings=vectors)

    def similarity_search(self, dataset_name: str, query: str, k: int = 6) -> List[Dict[str, Any]]:
        coll = self.client.get_or_create_collection(name=dataset_name)
        qv = self.emb.embed_query(query)
        res = coll.query(query_embeddings=[qv], n_results=k)
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        return [{"text": d, "score": float(s)} for d, s in zip(docs, dists)]

