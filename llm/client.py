from __future__ import annotations

import json
from typing import Any

from config import Settings

try:
    import requests
except Exception:  # pragma: no cover - exercised when dependencies are not installed.
    requests = None


class LLMClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()

    def complete(self, prompt: str, fallback_text: str) -> tuple[str, str, bool]:
        if not self.settings.use_vllm:
            return fallback_text, "offline-deterministic-rca", True
        if requests is None:
            return fallback_text, "offline-deterministic-rca", True

        payload: dict[str, Any] = {
            "model": self.settings.vllm_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an incident commander. Produce concise, safe RCA output "
                        "grounded only in the supplied incident and evidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }

        try:
            response = requests.post(
                self.settings.vllm_base_url,
                json=payload,
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"].strip()
            if text:
                return text, self.settings.vllm_model, False
        except Exception:
            pass

        return fallback_text, "offline-deterministic-rca", True

    @staticmethod
    def parse_json_or_text(text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"reasoning": text}
