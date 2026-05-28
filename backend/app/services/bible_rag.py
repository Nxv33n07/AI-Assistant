"""
Bible RAG service — BM25-based retrieval over a curated corpus of key Scripture passages.

BM25 is used instead of a vector DB to stay within Render free-tier memory limits
(512 MB). The curated 112-verse corpus covers all major theological topics; a full
31K-verse index with neural embeddings is the natural production upgrade.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class BibleRAG:
    def __init__(self, verses_file: str, persist_dir: str = None, api_key: str = None):
        self.verses_file = verses_file
        self._bm25 = None
        self._verses: list[dict] = []

    async def initialize(self) -> None:
        try:
            from rank_bm25 import BM25Okapi

            if not os.path.exists(self.verses_file):
                logger.warning(f"Verses file not found: {self.verses_file}")
                return

            with open(self.verses_file) as f:
                self._verses = json.load(f)

            corpus = [
                (
                    v["reference"]
                    + " "
                    + v["text"]
                    + " "
                    + " ".join(v.get("topics", []))
                ).lower().split()
                for v in self._verses
            ]
            self._bm25 = BM25Okapi(corpus)
            logger.info(f"Bible RAG ready — {len(self._verses)} verses indexed with BM25")
        except Exception as e:
            logger.error(f"BM25 initialisation failed: {e}. Falling back to keyword search.")
            self._bm25 = None

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """BM25 retrieval; falls back to keyword overlap if BM25 unavailable."""
        if self._bm25 is None or not self._verses:
            return self._keyword_fallback(query, top_k)

        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        return [
            {
                "reference": self._verses[i]["reference"],
                "text": self._verses[i]["text"],
                "translation": self._verses[i].get("translation", "KJV"),
            }
            for i in top_indices
            if scores[i] > 0
        ]

    def _keyword_fallback(self, query: str, top_k: int) -> list[dict]:
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
