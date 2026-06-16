from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from config import METRICS_DIR
from models import DetectedIncident, RetrievedDocument, WorkflowMetrics


logger = logging.getLogger(__name__)


def compute_retrieval_accuracy(
    detected: DetectedIncident,
    evidence: list[RetrievedDocument],
) -> float:
    if not evidence:
        return 0.0
    relevance_terms = {
        detected.service.lower(),
        *[term.lower() for term in detected.symptoms],
        *[term.lower() for term in detected.raw_keywords[:5]],
    }
    relevance_terms = {term for term in relevance_terms if term}
    relevant_count = 0
    for doc in evidence:
        content = f"{doc.title}\n{doc.content}".lower()
        if any(term in content for term in relevance_terms):
            relevant_count += 1
    return round(relevant_count / len(evidence), 4)


def store_metrics(
    metrics: WorkflowMetrics,
    report_id: str,
    metrics_dir: Path = METRICS_DIR,
) -> Path:
    metrics_dir.mkdir(parents=True, exist_ok=True)
    path = metrics_dir / "workflow_metrics.jsonl"
    record = {
        "report_id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metrics": asdict(metrics),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    logger.info("Stored workflow metrics report_id=%s path=%s", report_id, path)
    return path
