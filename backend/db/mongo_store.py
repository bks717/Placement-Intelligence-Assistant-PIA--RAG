"""
Structured Data Store

Stores structured/queryable facts (companies, interview questions, skills)
that don't need embedding search. Supports MongoDB or JSON-file fallback.

Why separate from vector DB: structured queries like "all SQL-tagged questions
for ProcDNA" are better served by a queryable store than by semantic search.
This is intentional hybrid storage, not redundancy.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Optional
from loguru import logger

from backend.config import settings


class JSONStore:
    """
    JSON-file-based structured store. Each collection is a JSON file.
    Works without any external database — good for local dev and demos.
    """

    def __init__(self, store_dir: Optional[str] = None):
        self.store_dir = Path(store_dir or settings.json_store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, list[dict]] = {}

    def _get_path(self, collection: str) -> Path:
        return self.store_dir / f"{collection}.json"

    def _load(self, collection: str) -> list[dict]:
        """Load a collection from disk (cached in memory)."""
        if collection not in self._cache:
            path = self._get_path(collection)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._cache[collection] = json.load(f)
            else:
                self._cache[collection] = []
        return self._cache[collection]

    def _save(self, collection: str):
        """Persist a collection to disk."""
        path = self._get_path(collection)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._cache.get(collection, []), f, indent=2, ensure_ascii=False)

    def insert(self, collection: str, document: dict) -> str:
        """Insert a document into a collection. Returns the document ID."""
        data = self._load(collection)
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        data.append(document)
        self._cache[collection] = data
        self._save(collection)
        return document["_id"]

    def insert_many(self, collection: str, documents: list[dict]) -> list[str]:
        """Insert multiple documents. Returns list of IDs."""
        data = self._load(collection)
        ids = []
        for doc in documents:
            if "_id" not in doc:
                doc["_id"] = str(uuid.uuid4())
            ids.append(doc["_id"])
            data.append(doc)
        self._cache[collection] = data
        self._save(collection)
        return ids

    def find(
        self,
        collection: str,
        query: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Find documents matching a query dict.
        Simple key-value matching (no nested queries).

        Args:
            collection: Collection name
            query: Dict of field-value pairs to match (AND logic)
            limit: Max results
        """
        data = self._load(collection)
        if not query:
            results = data
        else:
            results = []
            for doc in data:
                match = all(
                    doc.get(k) == v
                    for k, v in query.items()
                )
                if match:
                    results.append(doc)
        if limit:
            results = results[:limit]
        return results

    def find_one(self, collection: str, query: dict) -> Optional[dict]:
        """Find a single matching document."""
        results = self.find(collection, query, limit=1)
        return results[0] if results else None

    def update(self, collection: str, query: dict, update_fields: dict) -> int:
        """Update all matching documents. Returns count of updated docs."""
        data = self._load(collection)
        count = 0
        for doc in data:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update_fields)
                count += 1
        if count > 0:
            self._save(collection)
        return count

    def delete(self, collection: str, query: dict) -> int:
        """Delete all matching documents. Returns count of deleted docs."""
        data = self._load(collection)
        original_len = len(data)
        data = [
            doc for doc in data
            if not all(doc.get(k) == v for k, v in query.items())
        ]
        deleted = original_len - len(data)
        self._cache[collection] = data
        if deleted > 0:
            self._save(collection)
        return deleted

    def count(self, collection: str, query: Optional[dict] = None) -> int:
        """Count documents matching a query."""
        return len(self.find(collection, query))

    def distinct(self, collection: str, field: str) -> list:
        """Get distinct values for a field across all documents."""
        data = self._load(collection)
        values = set()
        for doc in data:
            if field in doc:
                val = doc[field]
                if isinstance(val, list):
                    values.update(val)
                else:
                    values.add(val)
        return sorted(values)

    def aggregate_field(self, collection: str, group_field: str, count_field: Optional[str] = None) -> dict:
        """
        Simple aggregation: group by a field and count occurrences.
        If count_field is provided, count distinct values of that field per group.
        """
        data = self._load(collection)
        groups: dict[str, int] = {}
        for doc in data:
            key = doc.get(group_field, "unknown")
            if isinstance(key, list):
                for k in key:
                    groups[k] = groups.get(k, 0) + 1
            else:
                groups[key] = groups.get(key, 0) + 1
        return groups

    def drop_collection(self, collection: str):
        """Delete an entire collection."""
        path = self._get_path(collection)
        if path.exists():
            os.remove(path)
        self._cache.pop(collection, None)
        logger.warning(f"Dropped collection: {collection}")

    def list_collections(self) -> list[str]:
        """List all collection names."""
        return [
            p.stem for p in self.store_dir.glob("*.json")
        ]

    def get_stats(self) -> dict:
        """Get store statistics."""
        collections = self.list_collections()
        stats = {}
        for col in collections:
            stats[col] = self.count(col)
        return stats


def get_structured_store() -> JSONStore:
    """
    Factory function — returns the appropriate structured store.
    Currently returns JSONStore. Can be extended to return MongoStore
    when settings.use_mongodb is True.
    """
    if settings.use_mongodb:
        try:
            from pymongo import MongoClient
            # If MongoDB support is needed in the future, implement MongoStore
            # with the same interface as JSONStore
            logger.warning(
                "MongoDB selected but MongoStore not yet implemented. "
                "Falling back to JSONStore."
            )
        except ImportError:
            logger.warning("pymongo not installed. Using JSONStore fallback.")

    return JSONStore()


# Singleton instance
structured_store = get_structured_store()
