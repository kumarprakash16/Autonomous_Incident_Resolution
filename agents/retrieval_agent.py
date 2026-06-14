from __future__ import annotations

from config import Settings
from models import DetectedIncident, IncidentInput, RetrievedDocument
from rag import RagRetriever


def retrieve_evidence(
    incident: IncidentInput,
    detected: DetectedIncident,
    retriever: RagRetriever | None = None,
    settings: Settings | None = None,
) -> list[RetrievedDocument]:
    settings = settings or Settings.from_env()
    retriever = retriever or RagRetriever()
    query = "\n".join(
        [
            detected.normalized_summary,
            "signals: " + ", ".join(detected.signal_keywords),
            incident.logs,
        ]
    )
    return retriever.retrieve(query, top_k=settings.top_k)
