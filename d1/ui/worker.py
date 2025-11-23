"""Threaded worker for routing UI messages to the agent."""

from __future__ import annotations

import traceback
from typing import final

from PySide6.QtCore import QObject, Signal

from ..agents import PetAgent


@final
class AgentWorker(QObject):
    """Runs the LangChain call on a background thread."""

    finished = Signal()
    responded = Signal(str)
    errored = Signal(str)

    def __init__(self, agent: PetAgent, user_text: str) -> None:
        super().__init__()
        self._agent = agent
        self._user_text = user_text

    def run(self) -> None:
        try:
            reply = self._agent.respond(self._user_text)
            self.responded.emit(reply)
        except Exception:  # pragma: no cover - UI side effect
            self.errored.emit(traceback.format_exc())
        finally:
            self.finished.emit()


__all__ = ["AgentWorker"]
