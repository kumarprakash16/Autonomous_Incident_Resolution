from __future__ import annotations

import json

from agents import orchestrate_incident
from config import DEFAULT_INCIDENT
from models import IncidentInput


def main() -> None:
    incident = IncidentInput(**DEFAULT_INCIDENT)
    pending = orchestrate_incident(incident)
    approved = orchestrate_incident(
        incident,
        approval_status="approved",
        approved_by="demo-operator",
        approval_notes="Approved for simulated remediation.",
    )
    print("=== Pending Review ===")
    print(json.dumps(pending.to_dict(), indent=2))
    print("\n=== Approved Simulation ===")
    print(json.dumps(approved.to_dict(), indent=2))


if __name__ == "__main__":
    main()
