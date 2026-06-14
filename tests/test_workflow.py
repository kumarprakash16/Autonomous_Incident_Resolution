from __future__ import annotations

from agents import orchestrate_incident
from config import DEFAULT_INCIDENT, Settings
from llm import LLMClient
from models import IncidentInput
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


def test_vllm_falls_back_when_endpoint_fails() -> None:
    client = LLMClient(
        Settings(
            use_vllm=True,
            vllm_base_url="http://127.0.0.1:9/v1/chat/completions",
            request_timeout_seconds=0.05,
        )
    )
    text, model, offline = client.complete("hello", "fallback")
    assert text == "fallback"
    assert model == "offline-deterministic-rca"
    assert offline is True


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
