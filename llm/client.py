from __future__ import annotations

import json
import logging
import re
from typing import Any

from config import Settings
from llm.base import BaseLLM, LLMResponse
from llm.providers import OfflineLLM, build_llm


logger = logging.getLogger(__name__)
JSON_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class LLMClient:
    def __init__(self, settings: Settings | None = None, provider: BaseLLM | None = None):
        self.settings = settings or Settings.from_env()
        self.provider = provider or build_llm(self.settings)
        self.offline_provider = OfflineLLM()

    def complete(self, prompt: str, fallback_text: str = "", system_prompt: str = "") -> tuple[str, str, bool]:
        try:
            response = self.provider.complete(prompt, system_prompt=system_prompt)
            if response.text:
                return response.text, response.model, response.offline_fallback
        except Exception as exc:
            logger.warning("LLM provider failed; falling back if allowed: %s", exc)
            if not self.settings.allow_offline_fallback:
                raise

        if fallback_text:
            return fallback_text, self.offline_provider.model_name, True
        response = self.offline_provider.complete(prompt, system_prompt=system_prompt)
        return response.text, response.model, True

    def complete_response(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        text, model, offline = self.complete(prompt, system_prompt=system_prompt)
        return LLMResponse(text=text, model=model, provider=self.settings.llm_provider, offline_fallback=offline)


def parse_json_strict(text: str) -> dict[str, Any]:
    candidate = text.strip()
    match = JSON_BLOCK.search(candidate)
    if match:
        candidate = match.group(1).strip()
    return json.loads(candidate)
