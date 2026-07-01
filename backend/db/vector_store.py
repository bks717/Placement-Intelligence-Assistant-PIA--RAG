"""
ChromaDB Vector Store Wrapper

Provides a unified interface for storing and querying document chunks
with embeddings and metadata. Supports metadata pre-filtering for
company/doc_type scoped retrieval.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import Optional
from loguru import logger

from backend.config import settings


class VectorStore:
    """Wrapper around ChromaDB for chunk storage and similarity search."""

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None
        self._embedding_model: Optional[SentenceTransformer] = None

    def initialize(self):
        """Initialize ChromaDB client and embedding model."""
        logger.info(f"Initializing ChromaDB at: {settings.chroma_persist_dir}")
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="pia_chunks",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self._embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info(
            f"Vector store ready. Collection has {self._collection.count()} chunks."
        )

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self.initialize()
        return self._collection

    @property
    def embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            self.initialize()
        return self._embedding_model

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embedding_model.encode(text).tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        return self.embedding_model.encode(texts).tolist()

    def add_chunks(
        self,
        chunk_ids: list[str],
        texts: list[str],
        metadatas: list[dict],
        embeddings: Optional[list[list[float]]] = None,
    ):
        """
        Add document chunks to the vector store.

        Args:
            chunk_ids: Unique IDs for each chunk
            texts: Raw text content of each chunk
            metadatas: Metadata dicts (company, doc_type, page, source_file)
            embeddings: Pre-computed embeddings (computed if not provided)
        """
        if embeddings is None:
            embeddings = self.embed_texts(texts)

        # ChromaDB has a batch limit — process in batches of 500
        batch_size = 500
        for i in range(0, len(chunk_ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=chunk_ids[i:end],
                documents=texts[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end],
            )
        logger.info(f"Added/updated {len(chunk_ids)} chunks in vector store.")

    def similarity_search(
        self,
        query: str,
        top_k: int = 20,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        Perform dense similarity search with optional metadata filtering.

        Metadata filtering happens BEFORE retrieval — cuts search space,
        doesn't post-filter results.

        Args:
            query: Search query text
            top_k: Number of results to return
            where: ChromaDB where clause for metadata filtering
                   e.g., {"company": "ProcDNA"} or
                   {"$and": [{"company": "ProcDNA"}, {"doc_type": "interview_experience"}]}

        Returns:
            List of dicts with keys: id, text, metadata, distance
        """
        query_embedding = self.embed_text(query)

        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self.collection.count() or top_k),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_params["where"] = where

        results = self.collection.query(**query_params)

        # Flatten results into list of dicts
        chunks = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                chunks.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })
        return chunks

    def get_all_chunks(
        self,
        where: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Get all chunks matching a metadata filter (for BM25 index building).

        Args:
            where: ChromaDB where clause
            limit: Maximum number of chunks to return

        Returns:
            List of dicts with keys: id, text, metadata
        """
        get_params = {
            "include": ["documents", "metadatas"],
        }
        if where:
            get_params["where"] = where
        if limit:
            get_params["limit"] = limit

        results = self.collection.get(**get_params)

        chunks = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                chunks.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                })
        return chunks

    def delete_by_source(self, source_file: str):
        """Delete all chunks from a specific source file."""
        self.collection.delete(where={"source_file": source_file})
        logger.info(f"Deleted chunks from source: {source_file}")

    def get_stats(self) -> dict:
        """Get collection statistics."""
        count = self.collection.count()
        return {"total_chunks": count}

    def reset(self):
        """Delete all data (use with caution)."""
        if self._client:
            self._client.delete_collection("pia_chunks")
            self._collection = self._client.get_or_create_collection(
                name="pia_chunks",
                metadata={"hnsw:space": "cosine"},
            )
            logger.warning("Vector store reset — all chunks deleted.")


# Singleton instance
vector_store = VectorStore()
