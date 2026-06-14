from __future__ import annotations

from datetime import datetime, timezone

from models import ApprovalDecision, ExecutionResult, Recommendation


def simulate_execution(
    recommendation: Recommendation,
    approval: ApprovalDecision,
) -> ExecutionResult:
    if approval.status == "pending":
        return ExecutionResult(
            status="Awaiting human approval",
            actions_executed=[],
            details="No remediation actions were executed because approval is pending.",
        )
    if approval.status == "rejected":
        return ExecutionResult(
            status="Blocked by human reviewer",
            actions_executed=[],
            details="The recommended remediation was rejected; automation stayed read-only.",
        )

    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    completed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return ExecutionResult(
        status="Resolved (simulated)",
        actions_executed=recommendation.steps,
        details=(
            "Simulation completed successfully. Health checks recovered and error rate returned "
            "below the demo threshold."
        ),
        started_at=started_at,
        completed_at=completed_at,
    )
