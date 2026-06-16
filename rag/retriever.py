from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from config import DATASET_DIR, Settings
from models import RetrievedDocument
from rag.vector_store import CorpusDocument, FaissVectorIndex, LexicalVectorIndex, tokenize


logger = logging.getLogger(__name__)


SOURCE_TYPES = {
    "incidents": "incident_history",
    "sops": "sop",
    "rca_reports": "rca_report",
    "runbooks": "runbook",
}


class RagRetriever:
    def __init__(self, settings: Settings | None = None, dataset_dir: Path = DATASET_DIR):
        self.settings = settings or Settings.from_env()
        self.dataset_dir = Path(dataset_dir or self.settings.dataset_dir)
        self.json_data_dir = self.settings.json_data_dir
        self.documents = self._load_documents()
        self.index = self._build_index()
        self.reranker = Reranker(self.settings.reranker_model)

    @property
    def backend_name(self) -> str:
        return self.index.backend_name

    def retrieve(self, query: str, top_k: int = 4, candidate_k: int | None = None) -> list[RetrievedDocument]:
        candidate_k = candidate_k or max(top_k, self.settings.candidate_k)
        candidates = self.index.search(query, top_k=candidate_k)
        return self.reranker.rerank(query, candidates, top_k=top_k)

    def reindex(self) -> None:
        self.documents = self._load_documents()
        self.index = self._build_index()
        rebuild = getattr(self.index, "rebuild", None)
        if callable(rebuild):
            rebuild()

    def _load_documents(self) -> list[CorpusDocument]:
        documents: list[CorpusDocument] = []
        for folder, source_type in SOURCE_TYPES.items():
            folder_path = self.dataset_dir / folder
            for path in sorted(folder_path.glob("*.md")) + sorted(folder_path.glob("*.txt")):
                content = path.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                title = _extract_title(content, path.stem.replace("_", " ").title())
                documents.append(
                    CorpusDocument(
                        doc_id=f"{source_type}:{path.stem}",
                        title=title,
                        source_type=source_type,
                        path=path,
                        content=content,
                        metadata={"format": path.suffix.lstrip(".")},
                    )
                )
        incidents_dir = self.json_data_dir / "incidents"
        for path in sorted(incidents_dir.glob("*.json")):
            documents.extend(_load_json_incident(path))
        return documents

    def _build_index(self):
        if FaissVectorIndex.is_available():
            try:
                return FaissVectorIndex(
                    self.documents,
                    embedding_model=self.settings.embedding_model,
                    index_dir=self.settings.faiss_index_dir,
                )
            except Exception as exc:
                logger.warning("FAISS/BGE index unavailable; using lexical fallback: %s", exc)
        return LexicalVectorIndex(self.documents)


class Reranker:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_name)
            self.backend_name = model_name
        except Exception as exc:
            logger.info("Cross-encoder reranker unavailable; using lexical reranker: %s", exc)
            self.backend_name = "lexical-reranker"

    def rerank(
        self,
        query: str,
        documents: list[RetrievedDocument],
        top_k: int,
    ) -> list[RetrievedDocument]:
        start = time.perf_counter()
        if not documents:
            return []
        if self._model is not None:
            pairs = [(query, doc.content) for doc in documents]
            scores = self._model.predict(pairs)
            for doc, score in zip(documents, scores):
                doc.rerank_score = round(float(score), 4)
        else:
            query_tokens = set(tokenize(query))
            for doc in documents:
                doc_tokens = set(tokenize(doc.content))
                overlap = len(query_tokens & doc_tokens) / max(1, len(query_tokens))
                doc.rerank_score = round((doc.score * 0.7) + (overlap * 0.3), 4)
        ranked = sorted(documents, key=lambda doc: (doc.rerank_score, doc.score), reverse=True)
        logger.debug("Reranked %s docs in %.2f ms", len(documents), (time.perf_counter() - start) * 1000)
        return ranked[:top_k]


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        clean = line.strip().lstrip("#").strip()
        if clean:
            return clean
    return fallback


def _load_json_incident(path: Path) -> list[CorpusDocument]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Skipping invalid JSON incident %s: %s", path, exc)
        return []
    items = payload if isinstance(payload, list) else [payload]
    documents: list[CorpusDocument] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        incident_id = str(item.get("id") or path.stem)
        title = str(item.get("title") or item.get("summary") or incident_id)
        fields = [
            f"id: {incident_id}",
            f"title: {title}",
            f"service: {item.get('service', '')}",
            f"severity: {item.get('severity', '')}",
            f"symptoms: {', '.join(item.get('symptoms', [])) if isinstance(item.get('symptoms'), list) else item.get('symptoms', '')}",
            f"root_cause: {item.get('root_cause', '')}",
            f"resolution: {item.get('resolution', '')}",
            f"logs: {item.get('logs', '')}",
        ]
        documents.append(
            CorpusDocument(
                doc_id=f"incident_json:{incident_id}",
                title=title,
                source_type="incident_history",
                path=path,
                content="\n".join(fields),
                metadata={key: value for key, value in item.items() if key != "logs"},
            )
        )
    return documents
