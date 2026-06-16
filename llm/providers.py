from __future__ import annotations

import json
import logging
import os
from typing import Any

from config import Settings
from llm.base import BaseLLM, LLMResponse

try:
    import requests
except Exception:  # pragma: no cover - dependency guard.
    requests = None


logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    provider_name = "gemini"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()

    def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        if requests is None or not self.api_key:
            reason = "requests is unavailable" if requests is None else "GEMINI_API_KEY is not set"
            raise RuntimeError(f"Gemini provider unavailable: {reason}")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        response = requests.post(
            url,
            params={"key": self.api_key},
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
        return LLMResponse(
            text=text,
            model=self.settings.gemini_model,
            provider=self.provider_name,
        )


class OllamaLLM(BaseLLM):
    provider_name = "ollama"

    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        if requests is None:
            raise RuntimeError("Ollama provider unavailable: requests is not installed")

        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        response = requests.post(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return LLMResponse(
            text=str(data.get("response", "")).strip(),
            model=self.settings.ollama_model,
            provider=self.provider_name,
        )


class OfflineLLM(BaseLLM):
    provider_name = "offline"

    def __init__(self, model_name: str = "offline-deterministic-rca"):
        self.model_name = model_name

    def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        text = json.dumps(
            {
                "root_cause": "Insufficient evidence for a live-model RCA; use retrieved evidence and human review.",
                "confidence": 0.35,
                "reasoning": "The configured LLM provider was unavailable, so the workflow used a deterministic fallback.",
                "contributing_factors": ["llm_unavailable"],
            }
        )
        return LLMResponse(
            text=text,
            model=self.model_name,
            provider=self.provider_name,
            offline_fallback=True,
        )


def build_llm(settings: Settings | None = None) -> BaseLLM:
    settings = settings or Settings.from_env()
    providers: dict[str, type[BaseLLM]] = {
        "gemini": GeminiLLM,
        "ollama": OllamaLLM,
    }
    provider_cls = providers.get(settings.llm_provider)
    if provider_cls is None:
        raise ValueError(f"Unsupported LLM_PROVIDER={settings.llm_provider!r}")
    return provider_cls(settings)
