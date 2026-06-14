from __future__ import annotations

from models import ApprovalDecision


def decide_approval(status: str = "pending", approved_by: str = "", notes: str = "") -> ApprovalDecision:
    normalized = status.strip().lower()
    if normalized not in {"pending", "approved", "rejected"}:
        normalized = "pending"
    return ApprovalDecision(status=normalized, approved_by=approved_by, notes=notes)
