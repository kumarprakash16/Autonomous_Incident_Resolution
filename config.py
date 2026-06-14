from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets"


@dataclass(frozen=True)
class Settings:
    use_vllm: bool = False
    vllm_base_url: str = "http://localhost:8000/v1/chat/completions"
    vllm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    request_timeout_seconds: float = 8.0
    top_k: int = 4

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            use_vllm=os.getenv("USE_VLLM", "false").strip().lower() == "true",
            vllm_base_url=os.getenv(
                "VLLM_BASE_URL", "http://localhost:8000/v1/chat/completions"
            ),
            vllm_model=os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
            request_timeout_seconds=float(os.getenv("VLLM_TIMEOUT_SECONDS", "8")),
            top_k=int(os.getenv("RAG_TOP_K", "4")),
        )


DEFAULT_INCIDENT = {
    "service": "payment-service",
    "alert": "P1: checkout error rate above 18% and p95 latency over 4s",
    "logs": (
        "2026-06-14T09:12:01Z ERROR payment-service OutOfMemoryError heap exhausted\n"
        "2026-06-14T09:12:04Z WARN gateway retry storm detected for checkout requests\n"
        "2026-06-14T09:12:08Z ERROR payment-service db connection pool exhausted"
    ),
    "severity": "P1",
    "environment": "production",
}
