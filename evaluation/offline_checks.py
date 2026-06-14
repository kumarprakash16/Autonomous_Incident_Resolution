from __future__ import annotations

from agents import orchestrate_incident
from config import DEFAULT_INCIDENT
from models import IncidentInput


def run_offline_check() -> dict[str, object]:
    result = orchestrate_incident(
        IncidentInput(**DEFAULT_INCIDENT),
        approval_status="approved",
        approved_by="offline-check",
    )
    return {
        "status": result.execution.status,
        "evidence_count": len(result.evidence),
        "confidence": result.rca.confidence,
        "total_latency_ms": result.metrics.total_workflow_latency_ms,
    }
