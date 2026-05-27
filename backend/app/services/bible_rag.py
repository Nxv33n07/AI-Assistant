"""
Bible RAG (Retrieval-Augmented Generation) service.

Indexes a curated corpus of ~250 key Scripture passages using
sentence-transformers embeddings + ChromaDB.  On cold start it builds
and persists the index; subsequent starts load from disk instantly.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class BibleRAG:
    def __init__(self, verses_file: str, persist_dir: str):
        self.verses_file = verses_file
        self.persist_dir = persist_dir
        self._collection = None
        self._ef = None

    async def initialize(self) -> None:
        """Build or load the ChromaDB index."""
        try:
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            self._ef = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = client.get_or_create_collection(
                name="bible_verses",
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )

            # If collection is empty, index the curated verse corpus
            if self._collection.count() == 0:
                await self._index_verses()

            logger.info(f"Bible RAG ready — {self._collection.count()} verses indexed")
        except Exception as e:
            logger.error(f"ChromaDB initialisation failed: {e}. Falling back to keyword search.")
            self._collection = None

    async def _index_verses(self) -> None:
        if not os.path.exists(self.verses_file):
            logger.warning(f"Verses file not found: {self.verses_file}")
            return

        with open(self.verses_file) as f:
            verses = json.load(f)

        docs, ids, metadatas = [], [], []
        for i, v in enumerate(verses):
            text = f"{v['reference']}: {v['text']}"
            docs.append(text)
            ids.append(f"v{i}")
            metadatas.append({
                "reference": v["reference"],
                "book": v.get("book", ""),
                "topics": ",".join(v.get("topics", [])),
                "translation": v.get("translation", "KJV"),
            })

        # Batch insert
        batch = 100
        for start in range(0, len(docs), batch):
            self._collection.add(
                documents=docs[start:start + batch],
                ids=ids[start:start + batch],
                metadatas=metadatas[start:start + batch],
            )
        logger.info(f"Indexed {len(docs)} verses into ChromaDB")

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Semantic search; returns a list of {reference, text, translation}."""
        if self._collection is None:
            return self._keyword_fallback(query, top_k)
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, self._collection.count()),
            )
            hits = []
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                # doc = "Reference: text"  strip the reference prefix
                text = doc.split(": ", 1)[-1] if ": " in doc else doc
                hits.append({
                    "reference": meta["reference"],
                    "text": text,
                    "translation": meta.get("translation", "KJV"),
                })
            return hits
        except Exception as e:
            logger.warning(f"RAG search error: {e}")
            return []

    def _keyword_fallback(self, query: str, top_k: int) -> list[dict]:
        """Simple keyword overlap fallback when ChromaDB is unavailable."""
        if not os.path.exists(self.verses_file):
            return []
        with open(self.verses_file) as f:
            verses = json.load(f)

        query_words = set(query.lower().split())
        scored = []
        for v in verses:
            combined = (v["reference"] + " " + v["text"] + " " + " ".join(v.get("topics", []))).lower()
            score = sum(1 for w in query_words if w in combined)
            if score > 0:
                scored.append((score, v))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"reference": v["reference"], "text": v["text"], "translation": v.get("translation", "KJV")}
            for _, v in scored[:top_k]
        ]


_rag_instance: Optional[BibleRAG] = None


def get_rag() -> Optional[BibleRAG]:
    return _rag_instance


def set_rag(instance: BibleRAG) -> None:
    global _rag_instance
    _rag_instance = instance
