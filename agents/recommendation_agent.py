from __future__ import annotations

from models import RCAResult, Recommendation, RetrievedDocument


def recommend_actions(rca: RCAResult, evidence: list[RetrievedDocument]) -> Recommendation:
    text = (rca.root_cause + " " + " ".join(doc.content for doc in evidence)).lower()
    if any(term in text for term in ["memory", "heap", "outofmemory", "oom"]):
        steps = [
            "Shift 25% of checkout traffic away from unhealthy payment-service pods.",
            "Restart only pods showing heap exhaustion after draining in-flight requests.",
            "Increase heap headroom to the approved runbook limit.",
            "Watch p95 latency, 5xx rate, and memory usage for 10 minutes.",
        ]
        rollback = "Restore original traffic weights and revert heap override if error rate rises."
        summary = "Drain and restart memory-saturated payment-service pods with guarded monitoring."
        risk = "medium"
    elif any(term in text for term in ["database", "connection pool", "db"]):
        steps = [
            "Reduce worker concurrency for the affected service.",
            "Recycle saturated connection pools.",
            "Check database health and slow-query dashboard.",
            "Escalate to DBA if pool saturation persists beyond 10 minutes.",
        ]
        rollback = "Restore worker concurrency after connection pool utilization normalizes."
        summary = "Relieve database pool pressure and verify downstream health."
        risk = "medium"
    else:
        steps = [
            "Open the service runbook and validate current health checks.",
            "Restart one unhealthy replica at a time.",
            "Compare current deploy version against the last known good version.",
            "Escalate if the service does not recover after the first safe action.",
        ]
        rollback = "Stop automation and restore the previous service version if health worsens."
        summary = "Apply conservative service recovery with staged verification."
        risk = "low"

    return Recommendation(
        action_summary=summary,
        steps=steps,
        risk_level=risk,
        rollback_plan=rollback,
        requires_approval=True,
    )
