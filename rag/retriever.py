from __future__ import annotations

from pathlib import Path

from config import DATASET_DIR
from models import RetrievedDocument
from rag.vector_store import CorpusDocument, FaissReadyIndex, LexicalVectorIndex


SOURCE_TYPES = {
    "incidents": "incident_history",
    "sops": "sop",
    "rca_reports": "rca_report",
    "runbooks": "runbook",
}


class RagRetriever:
    def __init__(self, dataset_dir: Path = DATASET_DIR):
        self.dataset_dir = dataset_dir
        self.documents = self._load_documents()
        index_cls = FaissReadyIndex if FaissReadyIndex.is_available() else LexicalVectorIndex
        self.index = index_cls(self.documents)

    @property
    def backend_name(self) -> str:
        return self.index.backend_name

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedDocument]:
        return self.index.search(query, top_k=top_k)

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
                    )
                )
        return documents


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        clean = line.strip().lstrip("#").strip()
        if clean:
            return clean
    return fallback
