from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from agents.approval_agent import decide_approval
from agents.detection_agent import detect_incident
from agents.execution_agent import simulate_execution
from agents.rca_agent import analyze_root_cause
from agents.recommendation_agent import recommend_actions
from agents.retrieval_agent import retrieve_evidence
from config import Settings
from evaluation.metrics import compute_retrieval_accuracy, store_metrics
from llm import LLMClient
from models import IncidentInput, IncidentResult, WorkflowMetrics
from rag import RagRetriever


logger = logging.getLogger(__name__)


def orchestrate_incident(
    incident: IncidentInput,
    approval_status: str = "pending",
    approved_by: str = "",
    approval_notes: str = "",
    settings: Settings | None = None,
) -> IncidentResult:
    settings = settings or Settings.from_env()
    report_id = f"inc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    total_start = perf_counter()
    logger.info("Starting incident workflow report_id=%s service=%s", report_id, incident.service)

    detection_start = perf_counter()
    detected = detect_incident(incident)
    detection_latency = _elapsed_ms(detection_start)

    retrieval_start = perf_counter()
    retriever = RagRetriever(settings=settings)
    evidence = retrieve_evidence(incident, detected, retriever=retriever, settings=settings)
    retrieval_latency = _elapsed_ms(retrieval_start)

    rca_start = perf_counter()
    rca = analyze_root_cause(incident, detected, evidence, llm_client=LLMClient(settings))
    rca_latency = _elapsed_ms(rca_start)

    recommendation_start = perf_counter()
    recommendation = recommend_actions(rca, evidence)
    recommendation_latency = _elapsed_ms(recommendation_start)

    approval = decide_approval(approval_status, approved_by=approved_by, notes=approval_notes)
    execution = simulate_execution(recommendation, approval)

    similarity = max((doc.score for doc in evidence), default=0.0)
    rerank_score = max((doc.rerank_score for doc in evidence), default=0.0)
    retrieval_accuracy = compute_retrieval_accuracy(detected, evidence)
    metrics = WorkflowMetrics(
        detection_latency_ms=detection_latency,
        retrieval_latency_ms=retrieval_latency,
        rca_latency_ms=rca_latency,
        recommendation_latency_ms=recommendation_latency,
        total_workflow_latency_ms=_elapsed_ms(total_start),
        similarity_score=round(similarity, 4),
        rerank_score=round(rerank_score, 4),
        rca_confidence_score=rca.confidence,
        retrieval_accuracy=retrieval_accuracy,
    )
    store_metrics(metrics, report_id, metrics_dir=settings.metrics_dir)
    explanation = [
        f"Detection classified the incident as {detected.severity} with signals: "
        f"{', '.join(detected.signal_keywords) or 'general degradation'}.",
        f"RAG used {retriever.backend_name} and returned {len(evidence)} reranked evidence documents.",
        f"RCA used {rca.model_used}; offline fallback={rca.offline_fallback}.",
        f"Execution status: {execution.status}.",
    ]

    return IncidentResult(
        incident=incident,
        detected=detected,
        evidence=evidence,
        rca=rca,
        recommendation=recommendation,
        approval=approval,
        execution=execution,
        metrics=metrics,
        explanation=explanation,
        report_id=report_id,
    )


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)
