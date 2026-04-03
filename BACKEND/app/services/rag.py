from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List

import chromadb
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from app.core.config import settings


def _collection_name_for_filename(filename: str) -> str:
    # Chroma collection names cannot be empty; keep it deterministic.
    stem = Path(filename).stem
    return stem or "data"


def ingest_file(filename: str, df: pd.DataFrame) -> int:
    """
    Chunks df into 50-row text blocks, embeds with nomic-embed-text,
    stores in ChromaDB collection named after the filename.
    """
    collection_name = _collection_name_for_filename(filename)
    Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)

    # Clear any prior data for this collection to avoid duplicates.
    client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    # `OllamaEmbeddings` in `langchain-ollama` accepts only `model=...`.
    # It relies on the `OLLAMA_BASE_URL` env var for the endpoint.
    os.environ.setdefault("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL)

    embeddings = OllamaEmbeddings(
        model=settings.EMBED_MODEL,
    )

    documents: List[Document] = []
    n_rows = len(df)
    chunk_size = 50
    for start in range(0, n_rows, chunk_size):
        end = min(n_rows, start + chunk_size)
        chunk_df = df.iloc[start:end].copy()

        text = chunk_df.to_csv(index=False)
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source_file": filename,
                    "row_start": int(start),
                    "row_end": int(end - 1),
                },
            )
        )

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=settings.CHROMA_PATH,
        collection_name=collection_name,
    )
    vectorstore.persist()
    return len(documents)


def get_retriever(filename: str):
    """
    Loads the ChromaDB collection and returns a LangChain retriever with k=6.
    """
    collection_name = _collection_name_for_filename(filename)

    # Ensure the Ollama endpoint is discoverable by `OllamaEmbeddings`.
    os.environ.setdefault("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL)

    embeddings = OllamaEmbeddings(
        model=settings.EMBED_MODEL,
    )

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PATH,
    )
    return vectorstore.as_retriever(search_kwargs={"k": 6})

