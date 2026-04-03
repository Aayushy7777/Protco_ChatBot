"""RAG (Retrieval-Augmented Generation) pipeline for document retrieval and context building."""

import logging
import hashlib
from typing import List, Dict, Any
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.db.vector_store import get_vector_store
from app.services.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Handle document ingestion, chunking, embedding, and retrieval."""

    def __init__(self):
        """Initialize RAG pipeline."""
        self.vector_store = get_vector_store()
        self.embeddings = get_embeddings_service()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
        )
        logger.info("RAG pipeline initialized")

    def ingest_csv(self, filename: str, df: pd.DataFrame) -> int:
        """
        Ingest CSV data into vector store.
        
        Args:
            filename: Name of the CSV file
            df: Pandas DataFrame
            
        Returns:
            Number of chunks ingested
        """
        # Convert DataFrame to text format
        documents = []
        metadatas = []
        ids = []

        # Create schema document
        schema_text = self._create_schema_document(filename, df)
        documents.append(schema_text)
        metadatas.append({"source": filename, "type": "schema"})
        ids.append(self._generate_id(filename, "schema"))

        # Create row documents with sampling for large files
        sample_size = min(100, len(df))
        sample_df = df.sample(n=sample_size, random_state=42)

        for idx, row in sample_df.iterrows():
            row_text = self._create_row_document(filename, row)
            documents.append(row_text)
            metadatas.append({"source": filename, "type": "row", "row_index": int(idx)})
            ids.append(self._generate_id(filename, f"row_{idx}"))

        # Chunk documents
        all_chunks = []
        all_metadata = []
        all_ids = []

        for doc, metadata in zip(documents, metadatas):
            chunks = self.splitter.split_text(doc)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({**metadata, "chunk_index": i})
                all_ids.append(self._generate_id(metadata["source"], f"{metadata['type']}_{metadata.get('row_index', 0)}_{i}"))

        # Store in vector database
        self.vector_store.add_documents(all_chunks, all_metadata, all_ids)
        logger.info(f"Ingested {len(all_chunks)} chunks from {filename}")
        return len(all_chunks)

    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query
            top_k: Number of top results (defaults to config)
            
        Returns:
            List of relevantdocuments with metadata
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        results = self.vector_store.search(query, top_k=top_k)
        logger.debug(f"Retrieved {len(results)} documents for query: {query[:50]}...")
        return results

    def build_context(self, query: str, results: List[Dict[str, Any]] = None) -> str:
        """
        Build context string from retrieval results.
        
        Args:
            query: User query
            results: Pre-computed results (or will retrieve)
            
        Returns:
            Formatted context string
        """
        if results is None:
            results = self.retrieve(query)

        if not results:
            return "No relevant documents found."

        context_parts = ["Retrieved Context:\n"]
        for i, result in enumerate(results, 1):
            doc = result["document"]
            metadata = result["metadata"]
            context_parts.append(f"\n[Document {i}] (from {metadata.get('source', 'unknown')})")
            context_parts.append(doc)

        return "\n".join(context_parts)

    def _create_schema_document(self, filename: str, df: pd.DataFrame) -> str:
        """Create a text representation of DataFrame schema."""
        schema_lines = [f"File: {filename}", "Schema:"]

        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].notna().sum()
            schema_lines.append(f"  - {col} ({dtype}, {non_null} non-null values)")

        if len(df) > 0:
            schema_lines.append(f"\nDataFrame has {len(df)} rows and {len(df.columns)} columns.")

        return "\n".join(schema_lines)

    def _create_row_document(self, filename: str, row: pd.Series) -> str:
        """Create a text representation of a DataFrame row."""
        row_text = f"Data from {filename}:\n"
        for col, value in row.items():
            row_text += f"{col}: {value}\n"
        return row_text

    def _generate_id(self, filename: str, doc_id: str) -> str:
        """Generate unique ID for a document."""
        combined = f"{filename}_{doc_id}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def clear_collection(self) -> None:
        """Clear all documents from vector store."""
        self.vector_store.clear()
        logger.info("Vector store cleared")


# Global RAG pipeline instance
rag_pipeline: RAGPipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline instance."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline()
    return rag_pipeline
