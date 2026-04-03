"""Embeddings service using HuggingFace sentence transformers."""

import logging
from typing import List
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using sentence transformers."""

    def __init__(self, model_name: str = None):
        """Initialize embeddings service."""
        self.model_name = model_name or settings.EMBEDDINGS_MODEL
        logger.info(f"Loading embeddings model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Embeddings model loaded successfully")

    def embed_text(self, text: str) -> List[float]:
        """Convert text to embedding vector."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()


# Global embeddings service instance
embeddings_service: EmbeddingsService = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create global embeddings service instance."""
    global embeddings_service
    if embeddings_service is None:
        embeddings_service = EmbeddingsService()
    return embeddings_service
