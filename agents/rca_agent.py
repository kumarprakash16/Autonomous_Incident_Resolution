from __future__ import annotations

import json
import logging
from typing import Any

from llm import LLMClient, parse_json_strict
from models import DetectedIncident, IncidentInput, RCAResult, RetrievedDocument


logger = logging.getLogger(__name__)
REQUIRED_KEYS = {"root_cause", "confidence", "reasoning", "contributing_factors"}


def analyze_root_cause(
    incident: IncidentInput,
    detected: DetectedIncident,
    evidence: list[RetrievedDocument],
    llm_client: LLMClient | None = None,
) -> RCAResult:
    llm_client = llm_client or LLMClient()
    fallback = _fallback_rca(incident, detected, evidence)
    prompt = _build_prompt(incident, detected, evidence)
    parsed, model_used, offline = _complete_json_with_retries(
        llm_client=llm_client,
        prompt=prompt,
        fallback=fallback,
        retries=2,
    )

    root_cause = parsed.get("root_cause") or fallback["root_cause"]
    reasoning = parsed.get("reasoning") or fallback["reasoning"]
    factors = parsed.get("contributing_factors") or fallback["contributing_factors"]
    if isinstance(factors, str):
        factors = [factors]

    confidence = float(parsed.get("confidence", fallback["confidence"]))
    if evidence:
        confidence = min(0.96, confidence + max(doc.score for doc in evidence) * 0.12)

    return RCAResult(
        root_cause=root_cause,
        confidence=round(confidence, 2),
        reasoning=reasoning,
        contributing_factors=factors,
        model_used=model_used,
        offline_fallback=offline,
    )


def _complete_json_with_retries(
    llm_client: LLMClient,
    prompt: str,
    fallback: dict[str, Any],
    retries: int,
) -> tuple[dict[str, Any], str, bool]:
    system_prompt = (
        "You are a production incident RCA agent. Return only valid JSON with keys "
        "root_cause, confidence, reasoning, contributing_factors. Do not include markdown."
    )
    last_error = ""
    model_used = "offline-deterministic-rca"
    offline = True
    current_prompt = prompt
    for attempt in range(retries + 1):
        text, model_used, offline = llm_client.complete(
            current_prompt,
            json.dumps(fallback),
            system_prompt=system_prompt,
        )
        try:
            parsed = parse_json_strict(text)
            _validate_rca_json(parsed)
            return parsed, model_used, offline
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Invalid RCA JSON attempt=%s error=%s", attempt + 1, last_error)
            current_prompt = (
                f"{prompt}\n\nPrevious response was invalid JSON because: {last_error}.\n"
                f"Return exactly this schema with no extra text: {json.dumps(fallback)}"
            )
    return fallback, model_used, True


def _validate_rca_json(payload: dict[str, Any]) -> None:
    missing = REQUIRED_KEYS - set(payload)
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")
    if not isinstance(payload["contributing_factors"], list):
        raise ValueError("contributing_factors must be a list")
    confidence = float(payload["confidence"])
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")


def _fallback_rca(
    incident: IncidentInput,
    detected: DetectedIncident,
    evidence: list[RetrievedDocument],
) -> dict[str, object]:
    text = f"{incident.alert}\n{incident.logs}\n" + "\n".join(doc.content for doc in evidence)
    lowered = text.lower()
    if any(term in lowered for term in ["outofmemory", "heap", "memory leak", "oom"]):
        root_cause = "Memory pressure in payment-service exhausted heap and cascaded into retry storms."
        factors = ["heap exhaustion", "retry amplification", "connection pool saturation"]
        confidence = 0.82
    elif any(term in lowered for term in ["connection pool", "database", "db"]):
        root_cause = "Database connection pool saturation is blocking application requests."
        factors = ["connection pool exhaustion", "slow downstream dependency"]
        confidence = 0.74
    elif any(term in lowered for term in ["deploy", "release", "rollback"]):
        root_cause = "A recent deployment likely introduced a regression affecting request handling."
        factors = ["recent release", "elevated error rate"]
        confidence = 0.7
    else:
        root_cause = "The incident is likely caused by resource saturation in the affected service."
        factors = detected.signal_keywords or ["resource saturation"]
        confidence = 0.62

    evidence_titles = ", ".join(doc.title for doc in evidence[:2]) or "no matching document"
    return {
        "root_cause": root_cause,
        "confidence": confidence,
        "reasoning": (
            f"The alert and logs match {evidence_titles}. "
            f"Signals detected: {', '.join(detected.signal_keywords) or 'general service degradation'}."
        ),
        "contributing_factors": factors,
    }


def _build_prompt(
    incident: IncidentInput,
    detected: DetectedIncident,
    evidence: list[RetrievedDocument],
) -> str:
    evidence_block = "\n\n".join(
        f"[{doc.doc_id}] {doc.title}\nscore={doc.score}; rerank_score={doc.rerank_score}\n{doc.content}"
        for doc in evidence
    )
    return f"""
Return JSON with keys root_cause, confidence, reasoning, contributing_factors.

Incident:
service={incident.service}
severity={detected.severity}
environment={detected.environment}
alert={incident.alert}
logs={incident.logs}

Retrieved evidence:
{evidence_block}
""".strip()
