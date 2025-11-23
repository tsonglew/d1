"""Rule-based chat model that keeps the pet reactive offline."""

from __future__ import annotations

from collections.abc import Sequence
from random import choice
from typing import override

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

type ChatMessages = Sequence[BaseMessage]


class LocalPetChatModel(BaseChatModel):
    """Deterministic, friendly responses without relying on remote APIs."""

    @property
    @override
    def _llm_type(self) -> str:  # pragma: no cover - langchain hook
        return "local-pet"

    @override
    def _generate(  # pragma: no cover - langchain hook
        self,
        messages: ChatMessages,
        stop: Sequence[str] | None = None,
        run_manager=None,
        **kwargs,
    ) -> ChatResult:
        last_user = next(
            (message.content.strip() for message in reversed(messages) if isinstance(message, HumanMessage)),
            "",
        )

        reply = self._craft_reply(last_user)
        generation = ChatGeneration(message=AIMessage(content=reply))
        return ChatResult(generations=[generation])

    def _craft_reply(self, user_text: str) -> str:
        if not user_text:
            return "Pixel is here and ready to play! Meow!"

        lowered = user_text.casefold()
        match lowered:
            case text if "joke" in text:
                return "Pixel wiggles whiskers: Why did the cat sit on the computer? To keep an eye on the mouse! :3"
            case text if any(keyword in text for keyword in ("tired", "break")):
                return "Nap buddies? Pixel suggests a big stretch and a sip of water before continuing. *purr*"
            case text if any(greeting in text for greeting in ("hello", "hi")):
                return "Hii! Pixel does a flip in the air and waves paws excitedly!"
            case _:
                templates = [
                    "Pixel paws at the screen: {cue} *chirp*",
                    "Pixel tilts head: {cue} nya~",
                    "Pixel fluffs tail: {cue} purrr!",
                ]
                cue = f"I heard you mention '{user_text[:40]}'. Let's keep going together!"
                return choice(templates).format(cue=cue)


__all__ = ["LocalPetChatModel"]
