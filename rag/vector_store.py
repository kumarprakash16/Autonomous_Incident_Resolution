from __future__ import annotations

import math
import pickle
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import faiss
from sentence_transformers import SentenceTransformer
from models import RetrievedDocument


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./:-]+")


@dataclass
class CorpusDocument:
    doc_id: str
    title: str
    source_type: str
    path: Path
    content: str
    metadata: dict[str, Any] | None = None


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
                metadata=doc.metadata or {},
            )
            for score, doc in ranked
            if score > 0
        ]


class FaissVectorIndex:
    backend_name = "faiss-bge"

    def __init__(
        self,
        documents: list[CorpusDocument],
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        index_dir: Path | None = None,
    ):
        

        self.documents = documents
        self.embedding_model = embedding_model
        self.index_dir = index_dir
        self.model = SentenceTransformer(embedding_model)
        self.faiss = faiss
        self.index = self._load_or_build()

    @classmethod
    def is_available(cls) -> bool:
        try:
            # import faiss  # noqa: F401
            # import sentence_transformers  # noqa: F401
            return True
        except Exception:
            return False

    def search(self, query: str, top_k: int = 4) -> list[RetrievedDocument]:
        if not self.documents:
            return []
        query_embedding = self.model.encode([_bge_query(query)], normalize_embeddings=True)
        scores, indexes = self.index.search(query_embedding, min(top_k, len(self.documents)))
        results: list[RetrievedDocument] = []
        for score, doc_index in zip(scores[0], indexes[0]):
            if doc_index < 0:
                continue
            doc = self.documents[int(doc_index)]
            results.append(
                RetrievedDocument(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    source_type=doc.source_type,
                    path=str(doc.path),
                    content=doc.content,
                    score=round(float(score), 4),
                    metadata=doc.metadata or {},
                )
            )
        return results

    def rebuild(self) -> None:
        self.index = self._build()
        self._save()

    def _load_or_build(self):
        if self.index_dir:
            index_path = self.index_dir / "index.faiss"
            meta_path = self.index_dir / "documents.pkl"
            if index_path.exists() and meta_path.exists():
                try:
                    with meta_path.open("rb") as handle:
                        stored_docs = pickle.load(handle)
                    if [doc.doc_id for doc in stored_docs] == [doc.doc_id for doc in self.documents]:
                        return self.faiss.read_index(str(index_path))
                except Exception:
                    pass
        index = self._build()
        self._save()
        return index

    def _build(self):
        texts = [_bge_passage(doc.content) for doc in self.documents]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        dimension = embeddings.shape[1]
        index = self.faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        return index

    def _save(self) -> None:
        if not self.index_dir:
            return
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.faiss.write_index(self.index, str(self.index_dir / "index.faiss"))
        with (self.index_dir / "documents.pkl").open("wb") as handle:
            pickle.dump(self.documents, handle)


class FaissReadyIndex(LexicalVectorIndex):
    """Compatibility alias retained for older imports."""

    backend_name = "faiss-compatible-fallback"

    @classmethod
    def is_available(cls) -> bool:
        try:
            # import faiss  # noqa: F401

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


def _bge_query(text: str) -> str:
    return f"Represent this sentence for searching relevant passages: {text}"


def _bge_passage(text: str) -> str:
    return text
