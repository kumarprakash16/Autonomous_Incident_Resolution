from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    offline_fallback: bool = False


class BaseLLM(ABC):
    provider_name = "base"

    @abstractmethod
    def complete(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Return a completion for the prompt."""
