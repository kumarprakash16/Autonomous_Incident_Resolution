from __future__ import annotations

import logging

from models import RCAResult, Recommendation, RetrievedDocument


logger = logging.getLogger(__name__)


def recommend_actions(rca: RCAResult, evidence: list[RetrievedDocument]) -> Recommendation:
    text = (rca.root_cause + " " + " ".join(doc.content for doc in evidence)).lower()
    if any(term in text for term in ["memory", "heap", "outofmemory", "oom"]):
        immediate = [
            "Shift 25% of checkout traffic away from unhealthy payment-service pods.",
            "Restart only pods showing heap exhaustion after draining in-flight requests.",
            "Increase heap headroom to the approved runbook limit.",
            "Watch p95 latency, 5xx rate, and memory usage for 10 minutes.",
        ]
        long_term = [
            "Profile heap allocation paths in the failing release.",
            "Add load-test coverage for checkout retry storms and sustained traffic spikes.",
            "Tune pod memory requests and limits from observed production headroom.",
        ]
        monitoring = [
            "Alert on heap usage growth rate before OOM conditions.",
            "Track retry amplification between gateway and payment-service.",
            "Correlate memory pressure with checkout p95 latency and 5xx rate.",
        ]
        rollback = "Restore original traffic weights and revert heap override if error rate rises."
        summary = "Drain and restart memory-saturated payment-service pods with guarded monitoring."
        risk = "medium"
    elif any(term in text for term in ["database", "connection pool", "db"]):
        immediate = [
            "Reduce worker concurrency for the affected service.",
            "Recycle saturated connection pools.",
            "Check database health and slow-query dashboard.",
            "Escalate to DBA if pool saturation persists beyond 10 minutes.",
        ]
        long_term = [
            "Right-size pool limits against database capacity.",
            "Review slow queries and retry behavior under downstream pressure.",
            "Add backpressure controls to prevent queue buildup.",
        ]
        monitoring = [
            "Alert on pool utilization, wait time, and timeout rate.",
            "Dashboard database saturation beside application 5xx rate.",
            "Record slow-query exemplars for RCA review.",
        ]
        rollback = "Restore worker concurrency after connection pool utilization normalizes."
        summary = "Relieve database pool pressure and verify downstream health."
        risk = "medium"
    else:
        immediate = [
            "Open the service runbook and validate current health checks.",
            "Restart one unhealthy replica at a time.",
            "Compare current deploy version against the last known good version.",
            "Escalate if the service does not recover after the first safe action.",
        ]
        long_term = [
            "Document the verified recovery path in the service runbook.",
            "Add regression tests for the observed failure mode.",
            "Review deployment guardrails for earlier blast-radius detection.",
        ]
        monitoring = [
            "Alert on service-level error budgets and dependency health.",
            "Add deploy markers to latency and error-rate dashboards.",
            "Track automated remediation outcomes for reviewer audit.",
        ]
        rollback = "Stop automation and restore the previous service version if health worsens."
        summary = "Apply conservative service recovery with staged verification."
        risk = "low"

    logger.info("Generated recommendation risk=%s action=%s", risk, summary)
    return Recommendation(
        action_summary=summary,
        immediate_mitigation=immediate,
        long_term_fix=long_term,
        monitoring_improvements=monitoring,
        risk_level=risk,
        rollback_plan=rollback,
        requires_approval=True,
    )
