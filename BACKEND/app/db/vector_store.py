"""Vector store abstraction for ChromaDB."""

import logging
from pathlib import Path
from typing import List, Dict, Any
import chromadb

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector store for document retrieval."""

    def __init__(self, persist_dir: str = None):
        """Initialize vector store with ChromaDB backend."""
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Use new Chroma API with persistent client
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection_name = "csv_documents"
        logger.info(f"Vector store initialized at {self.persist_dir}")

    def get_or_create_collection(self) -> chromadb.Collection:
        """Get or create the document collection."""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.debug(f"Got existing collection: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Created new collection: {self.collection_name}")
        return collection

    def add_documents(
        self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]
    ) -> None:
        """Add documents to the vector store."""
        collection = self.get_or_create_collection()
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Added {len(documents)} documents to vector store")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        collection = self.get_or_create_collection()
        results = collection.query(query_texts=[query], n_results=top_k)

        # Format results
        if not results["documents"] or not results["documents"][0]:
            return []

        formatted_results = []
        for i, doc in enumerate(results["documents"][0]):
            formatted_results.append(
                {
                    "document": doc,
                    "distance": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                }
            )
        return formatted_results

    def delete_collection(self) -> None:
        """Delete the current collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Error deleting collection: {e}")

    def clear(self) -> None:
        """Clear all documents from the collection."""
        collection = self.get_or_create_collection()
        ids = collection.get(include=[])["ids"]
        if ids:
            collection.delete(ids=ids)
            logger.info(f"Cleared {len(ids)} documents from vector store")


# Global vector store instance
vector_store: VectorStore = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store
