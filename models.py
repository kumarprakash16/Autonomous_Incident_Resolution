from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class IncidentInput:
    service: str
    alert: str
    logs: str
    severity: str = "P2"
    environment: str = "production"


@dataclass
class DetectedIncident:
    service: str
    normalized_summary: str
    severity: str
    environment: str
    severity_score: float
    signal_keywords: list[str] = field(default_factory=list)


@dataclass
class RetrievedDocument:
    doc_id: str
    title: str
    source_type: str
    path: str
    content: str
    score: float


@dataclass
class RCAResult:
    root_cause: str
    confidence: float
    reasoning: str
    contributing_factors: list[str]
    model_used: str
    offline_fallback: bool


@dataclass
class Recommendation:
    action_summary: str
    steps: list[str]
    risk_level: str
    rollback_plan: str
    requires_approval: bool = True


@dataclass
class ApprovalDecision:
    status: str
    approved_by: str = ""
    notes: str = ""


@dataclass
class ExecutionResult:
    status: str
    actions_executed: list[str]
    details: str
    started_at: str = ""
    completed_at: str = ""


@dataclass
class WorkflowMetrics:
    detection_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    rca_latency_ms: float = 0.0
    recommendation_latency_ms: float = 0.0
    total_workflow_latency_ms: float = 0.0
    similarity_score: float = 0.0
    rca_confidence_score: float = 0.0


@dataclass
class IncidentResult:
    incident: IncidentInput
    detected: DetectedIncident
    evidence: list[RetrievedDocument]
    rca: RCAResult
    recommendation: Recommendation
    approval: ApprovalDecision
    execution: ExecutionResult
    metrics: WorkflowMetrics
    explanation: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
