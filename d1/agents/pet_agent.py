"""LangChain-backed agent that powers the virtual pet."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Self

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnablePassthrough

from ..models import ChatModelSettings, LocalPetChatModel, create_chat_model
from ..prompts import SYSTEM_PROMPT

type ChainInput = dict[str, str]
type HistoryFactory = Callable[[], BaseChatMessageHistory]

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class PetAgent:
    """Wraps a LangChain conversation chain for the pet."""

    config: ChatModelSettings = field(default_factory=ChatModelSettings)
    llm: BaseChatModel | None = None
    history_factory: HistoryFactory = ChatMessageHistory
    _chat_history: BaseChatMessageHistory = field(init=False, repr=False)
    _prompt: ChatPromptTemplate = field(init=False, repr=False)
    _chain: Runnable[ChainInput, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        llm = self.llm or create_chat_model(self.config)
        self._chat_history = self.history_factory()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{user_input}"),
            ]
        )
        self._configure_chain(llm)

    def _configure_chain(self, llm: BaseChatModel) -> None:
        self.llm = llm
        self._chain = (
            RunnablePassthrough.assign(chat_history=lambda _: self._chat_history.messages) | self._prompt | self.llm
        )

    def _switch_to_local_fallback(self) -> None:
        logger.warning("Remote chat model failed; switching to local fallback.")
        self._configure_chain(LocalPetChatModel())

    def _needs_local_fallback(self, exc: Exception) -> bool:
        return isinstance(exc, AttributeError) and "model_dump" in str(exc)

    def respond(self, user_input: str) -> str:
        """Return the agent's reply for user_input."""
        self._chat_history.add_user_message(user_input)
        try:
            result = self._chain.invoke({"user_input": user_input})
        except Exception as exc:
            if self._needs_local_fallback(exc):
                logger.exception("Falling back to local chat model due to upstream failure.")
                self._switch_to_local_fallback()
                result = self._chain.invoke({"user_input": user_input})
            else:
                raise
        content = getattr(result, "content", result)
        reply = content if isinstance(content, str) else str(content)
        self._chat_history.add_ai_message(reply)
        return reply.strip()

    def reset(self) -> Self:
        """Clear the running conversation and allow chaining."""
        self._chat_history.clear()
        return self


__all__ = ["PetAgent"]
