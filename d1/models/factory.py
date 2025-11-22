"""Factory helpers for assembling chat models."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from langchain_core.language_models.chat_models import BaseChatModel

from .local import LocalPetChatModel

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore[assignment]


@dataclass(slots=True, frozen=True)
class ChatModelSettings:
    """Declarative config for the preferred chat model."""

    model_name: str = "gpt-4o-mini"
    temperature: float = 0.6


def create_chat_model(settings: ChatModelSettings) -> BaseChatModel:
    """Return an OpenAI LLM when possible, otherwise a local fallback."""
    if ChatOpenAI is not None and getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model=settings.model_name, temperature=settings.temperature, max_retries=2)
    return LocalPetChatModel()


__all__ = ["ChatModelSettings", "create_chat_model"]

