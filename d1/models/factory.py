"""Factory helpers for assembling chat models."""

from __future__ import annotations

import logging
import sys
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

logger = logging.getLogger(__name__)
_PY314_OR_NEWER = sys.version_info >= (3, 14)
_warned_py314: bool = False


@dataclass(slots=True, frozen=True)
class ChatModelSettings:
    """Declarative config for the preferred chat model."""

    model_name: str = "grok-4-fast"
    temperature: float = 0.6
    base_url: str | None = None
    api_key: str | None = None


def _runtime_supports_remote() -> bool:
    global _warned_py314
    if not _PY314_OR_NEWER:
        return True
    if not _warned_py314:
        version = ".".join(str(i) for i in sys.version_info[:3])
        logger.warning(
            "Python %s is incompatible with the Grok chat backend; using the local fallback model.",
            version,
        )
        _warned_py314 = True
    return False


def _build_grok_model(settings: ChatModelSettings) -> BaseChatModel | None:
    """Return a ChatOpenAI client pointed at the Grok deployment."""
    if ChatOpenAI is None or not _runtime_supports_remote():
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
