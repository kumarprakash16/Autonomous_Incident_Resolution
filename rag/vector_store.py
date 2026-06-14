from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from models import RetrievedDocument


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./:-]+")


@dataclass
class CorpusDocument:
    doc_id: str
    title: str
    source_type: str
    path: Path
    content: str


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class LexicalVectorIndex:
    """Dependency-light vector-search fallback with a FAISS-like search API."""

    backend_name = "lexical-fallback"

    def __init__(self, documents: list[CorpusDocument]):
        self.documents = documents
        self.term_vectors = [Counter(tokenize(doc.content)) for doc in documents]

    def search(self, query: str, top_k: int = 4) -> list[RetrievedDocument]:
        query_vector = Counter(tokenize(query))
        scored: list[tuple[float, CorpusDocument]] = []
        for doc, vector in zip(self.documents, self.term_vectors):
            scored.append((cosine_similarity(query_vector, vector), doc))

        ranked = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
        return [
            RetrievedDocument(
                doc_id=doc.doc_id,
                title=doc.title,
                source_type=doc.source_type,
                path=str(doc.path),
                content=doc.content,
                score=round(score, 4),
            )
            for score, doc in ranked
            if score > 0
        ]


class FaissReadyIndex(LexicalVectorIndex):
    """Keeps the project FAISS-compatible without requiring faiss-cpu for demos."""

    backend_name = "faiss-compatible-fallback"

    @classmethod
    def is_available(cls) -> bool:
        try:
            import faiss  # noqa: F401

            return True
        except Exception:
            return False


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in intersection)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
