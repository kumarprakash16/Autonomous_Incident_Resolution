from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets"
DATA_DIR = BASE_DIR / "data"
METRICS_DIR = DATA_DIR / "metrics"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "gemini"
    gemini_model: str = "gemini-2.5-flash-lite"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    request_timeout_seconds: float = 20.0
    top_k: int = 5
    candidate_k: int = 12
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"
    dataset_dir: Path = DATASET_DIR
    json_data_dir: Path = DATA_DIR
    faiss_index_dir: Path = FAISS_INDEX_DIR
    metrics_dir: Path = METRICS_DIR
    allow_offline_fallback: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "gemini").strip().lower(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            request_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
            top_k=int(os.getenv("RAG_TOP_K", "5")),
            candidate_k=int(os.getenv("RAG_CANDIDATE_K", "12")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
            reranker_model=os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base"),
            dataset_dir=Path(os.getenv("DATASET_DIR", str(DATASET_DIR))),
            json_data_dir=Path(os.getenv("JSON_DATA_DIR", str(DATA_DIR))),
            faiss_index_dir=Path(os.getenv("FAISS_INDEX_DIR", str(FAISS_INDEX_DIR))),
            metrics_dir=Path(os.getenv("METRICS_DIR", str(METRICS_DIR))),
            allow_offline_fallback=os.getenv("ALLOW_OFFLINE_FALLBACK", "true")
            .strip()
            .lower()
            == "true",
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
