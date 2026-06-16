from __future__ import annotations

import logging
import re
from collections import Counter

from models import DetectedIncident, IncidentInput


logger = logging.getLogger(__name__)
SEVERITY_WEIGHTS = {"P0": 1.0, "P1": 0.88, "P2": 0.65, "P3": 0.35}
KEYWORD_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_.:-]{2,}")
SEVERITY_PATTERN = re.compile(r"\b(P[0-3])\b", re.IGNORECASE)
SYMPTOM_PATTERNS = {
    "memory pressure": re.compile(r"\b(outofmemory|oom|heap|memory)\b", re.I),
    "latency degradation": re.compile(r"\b(latency|p95|p99|timeout|slow)\b", re.I),
    "database contention": re.compile(r"\b(connection pool|database|db|deadlock|slow query)\b", re.I),
    "error-rate spike": re.compile(r"\b(5xx|error rate|exceptions?|retry storm)\b", re.I),
    "release regression": re.compile(r"\b(deploy|release|rollback|version|canary)\b", re.I),
}


def detect_incident(incident: IncidentInput) -> DetectedIncident:
    text = f"{incident.alert}\n{incident.logs}"
    severity = _extract_severity(incident, text)
    symptoms = [label for label, pattern in SYMPTOM_PATTERNS.items() if pattern.search(text)]
    raw_keywords = _extract_keywords(text)
    signal_keywords = sorted(set(symptoms + raw_keywords[:8]))
    base_score = SEVERITY_WEIGHTS.get(severity, 0.55)
    signal_boost = min(0.12, len(symptoms) * 0.03)
    severity_score = min(1.0, base_score + signal_boost)
    summary = (
        f"{severity} incident on {incident.service.strip()} in "
        f"{incident.environment.strip().lower()}: {incident.alert.strip()}"
    )
    logger.info("Detected incident service=%s severity=%s symptoms=%s", incident.service, severity, symptoms)
    return DetectedIncident(
        service=incident.service.strip(),
        normalized_summary=summary,
        severity=severity,
        environment=incident.environment.strip().lower(),
        severity_score=round(severity_score, 2),
        symptoms=symptoms,
        signal_keywords=signal_keywords,
        raw_keywords=raw_keywords,
    )


def _extract_severity(incident: IncidentInput, text: str) -> str:
    explicit = incident.severity.upper().strip()
    if explicit in SEVERITY_WEIGHTS:
        return explicit
    match = SEVERITY_PATTERN.search(text)
    return match.group(1).upper() if match else "P2"


def _extract_keywords(text: str) -> list[str]:
    stopwords = {
        "and",
        "the",
        "for",
        "with",
        "over",
        "above",
        "below",
        "error",
        "warn",
        "info",
        "production",
    }
    tokens = [token.lower() for token in KEYWORD_PATTERN.findall(text)]
    counts = Counter(token for token in tokens if token not in stopwords and not token.isdigit())
    return [token for token, _ in counts.most_common(15)]
