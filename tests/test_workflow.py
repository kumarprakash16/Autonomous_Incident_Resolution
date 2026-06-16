from __future__ import annotations

from agents import orchestrate_incident
from agents.rca_agent import analyze_root_cause
from config import DEFAULT_INCIDENT, Settings
from llm.base import BaseLLM, LLMResponse
from llm import LLMClient
from models import DetectedIncident, IncidentInput, RetrievedDocument
from rag import RagRetriever


def test_offline_pipeline_completes() -> None:
    result = orchestrate_incident(IncidentInput(**DEFAULT_INCIDENT))
    assert result.rca.root_cause
    assert result.evidence
    assert result.execution.status == "Awaiting human approval"


def test_rag_returns_ranked_evidence() -> None:
    docs = RagRetriever().retrieve("payment-service OutOfMemoryError heap retry storm", top_k=3)
    assert docs
    assert docs[0].score >= docs[-1].score
    assert any("payment" in doc.content.lower() for doc in docs)


class InvalidThenValidLLM(BaseLLM):
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        self.calls += 1
        if self.calls == 1:
            return LLMResponse("not json", "fake-model", "fake")
        return LLMResponse(
            (
                '{"root_cause":"heap pressure","confidence":0.7,'
                '"reasoning":"logs and evidence match","contributing_factors":["oom"]}'
            ),
            "fake-model",
            "fake",
        )


def test_gemini_falls_back_when_key_missing() -> None:
    client = LLMClient(
        Settings(
            llm_provider="gemini",
            request_timeout_seconds=0.05,
        )
    )
    text, model, offline = client.complete("hello", "fallback")
    assert text == "fallback"
    assert model == "offline-deterministic-rca"
    assert offline is True


def test_rca_retries_until_strict_json() -> None:
    provider = InvalidThenValidLLM()
    incident = IncidentInput(**DEFAULT_INCIDENT)
    detected = DetectedIncident(
        service="payment-service",
        normalized_summary="P1 payment-service memory incident",
        severity="P1",
        environment="production",
        severity_score=0.9,
        symptoms=["memory pressure"],
        signal_keywords=["memory pressure"],
        raw_keywords=["outofmemory"],
    )
    evidence = [
        RetrievedDocument(
            doc_id="incident_json:INC-2026-001",
            title="Payment service heap exhaustion",
            source_type="incident_history",
            path="data/incidents/payment-memory-leak.json",
            content="OutOfMemoryError heap exhausted",
            score=0.9,
            rerank_score=0.95,
        )
    ]
    result = analyze_root_cause(
        incident,
        detected,
        evidence,
        llm_client=LLMClient(Settings(llm_provider="gemini"), provider=provider),
    )
    assert provider.calls == 2
    assert result.root_cause == "heap pressure"
    assert result.confidence >= 0.7


def test_rejection_prevents_execution() -> None:
    result = orchestrate_incident(
        IncidentInput(**DEFAULT_INCIDENT),
        approval_status="rejected",
        approved_by="tester",
    )
    assert result.execution.status == "Blocked by human reviewer"
    assert result.execution.actions_executed == []


def test_approval_runs_simulation() -> None:
    result = orchestrate_incident(
        IncidentInput(**DEFAULT_INCIDENT),
        approval_status="approved",
        approved_by="tester",
    )
    assert result.execution.status == "Resolved (simulated)"
    assert result.execution.actions_executed
