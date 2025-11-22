"""LangChain-backed agent that powers the virtual pet."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Self

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnablePassthrough

from ..models import ChatModelSettings, create_chat_model
from ..prompts import SYSTEM_PROMPT

type ChainInput = dict[str, str]
type HistoryFactory = Callable[[], BaseChatMessageHistory]


@dataclass(slots=True, kw_only=True)
class PetAgent:
    """Wraps a LangChain conversation chain for the pet."""

    config: ChatModelSettings = field(default_factory=ChatModelSettings)
    llm: BaseChatModel | None = None
    history_factory: HistoryFactory = ChatMessageHistory
    _chat_history: BaseChatMessageHistory = field(init=False, repr=False)
    _chain: Runnable[ChainInput, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = create_chat_model(self.config)
        self._chat_history = self.history_factory()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{user_input}"),
            ]
        )
        self._chain = (
            RunnablePassthrough.assign(
                chat_history=lambda _: self._chat_history.messages
            )
            | prompt
            | self.llm
        )

    def respond(self, user_input: str) -> str:
        """Return the agent's reply for user_input."""
        self._chat_history.add_user_message(user_input)
        result = self._chain.invoke({"user_input": user_input})
        content = getattr(result, "content", result)
        reply = content if isinstance(content, str) else str(content)
        self._chat_history.add_ai_message(reply)
        return reply.strip()

    def reset(self) -> Self:
        """Clear the running conversation and allow chaining."""
        self._chat_history.clear()
        return self


__all__ = ["PetAgent"]

