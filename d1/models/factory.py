"""Factory helpers for assembling chat models."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

from .local import LocalPetChatModel

load_dotenv()

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore[assignment]


@dataclass(slots=True, frozen=True)
class ChatModelSettings:
    """Declarative config for the preferred chat model."""

    model_name: str = "grok-4-fast"
    temperature: float = 0.6
    base_url: str | None = None
    api_key: str | None = None


def _build_grok_model(settings: ChatModelSettings) -> BaseChatModel | None:
    """Return a ChatOpenAI client pointed at the Grok deployment."""
    if ChatOpenAI is None:
        return None

    base_url = settings.base_url or getenv("GROK_BASE_URL")
    api_key = settings.api_key or getenv("GROK_AUTH_TOKEN")
    if not base_url or not api_key:
        return None

    return ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        max_retries=2,
    )


def create_chat_model(settings: ChatModelSettings) -> BaseChatModel:
    """Return the Grok LLM when possible, otherwise a local fallback."""
    grok_model = _build_grok_model(settings)
    if grok_model is not None:
        return grok_model
    return LocalPetChatModel()


__all__ = ["ChatModelSettings", "create_chat_model"]
