from __future__ import annotations

from models import DetectedIncident, IncidentInput


SEVERITY_WEIGHTS = {"P0": 1.0, "P1": 0.88, "P2": 0.65, "P3": 0.35}
SIGNALS = {
    "memory": ["outofmemory", "heap", "memory", "oom"],
    "latency": ["latency", "p95", "timeout", "slow"],
    "database": ["connection pool", "db", "database", "deadlock"],
    "traffic": ["retry storm", "5xx", "error rate", "throttle"],
    "deployment": ["deploy", "release", "rollback", "version"],
}


def detect_incident(incident: IncidentInput) -> DetectedIncident:
    text = f"{incident.alert}\n{incident.logs}".lower()
    signal_keywords = [
        label
        for label, keywords in SIGNALS.items()
        if any(keyword in text for keyword in keywords)
    ]
    severity = incident.severity.upper().strip() or "P2"
    base_score = SEVERITY_WEIGHTS.get(severity, 0.55)
    signal_boost = min(0.12, len(signal_keywords) * 0.03)
    severity_score = min(1.0, base_score + signal_boost)
    summary = (
        f"{severity} incident on {incident.service} in {incident.environment}: "
        f"{incident.alert.strip()}"
    )
    return DetectedIncident(
        service=incident.service.strip(),
        normalized_summary=summary,
        severity=severity,
        environment=incident.environment.strip().lower(),
        severity_score=round(severity_score, 2),
        signal_keywords=signal_keywords,
    )
