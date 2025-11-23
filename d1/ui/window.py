"""Qt window that renders the animated pet and chat interface."""

from __future__ import annotations

import contextlib
from html import escape
from typing import Final

from PySide6.QtCore import QEvent, Qt, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..agents import PetAgent
from .worker import AgentWorker


class DesktopPetWindow(QWidget):
    """Window containing the animated pet label and chat controls."""

    _WELCOME: Final[str] = "Pixel is awake and bouncing on your desktop!"

    def __init__(self, agent: PetAgent | None = None) -> None:
        super().__init__()
        self._agent = agent or PetAgent()
        self._threads: list[QThread] = []

        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Pixel the Desktop Pet")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setFixedWidth(360)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        self.pet_label = QLabel("=^.^=")
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_label.setFont(QFont("Segoe UI Emoji", 36))
        self.pet_label.setStyleSheet("QLabel { background-color: #fef3c7; border-radius: 16px; padding: 12px; }")

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet("QTextEdit { background: #1f2937; color: #f9fafb; border-radius: 12px; }")
        self.chat_view.setMinimumHeight(200)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask Pixel something...")
        self.input_box.returnPressed.connect(self._handle_send)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._handle_send)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._handle_reset)

        input_row.addWidget(self.input_box, stretch=1)
        input_row.addWidget(self.send_button)
        input_row.addWidget(self.reset_button)

        main_layout.addWidget(self.pet_label)
        main_layout.addWidget(self.chat_view)
        main_layout.addLayout(input_row)

        self.setLayout(main_layout)
        self._append_message("Pixel", self._WELCOME)

    def _handle_send(self) -> None:
        text = self.input_box.text().strip()
        if not text:
            return

        self._append_message("You", text)
        self.input_box.clear()
        self._set_waiting(True)
        self._start_worker(text)

    def _handle_reset(self) -> None:
        self._agent.reset()
        self.chat_view.clear()
        self._append_message("Pixel", "Fresh start! Pixel shakes off the sleepies.")

    def _start_worker(self, user_text: str) -> None:
        worker = AgentWorker(self._agent, user_text)
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.responded.connect(lambda reply: self._append_message("Pixel", reply))
        worker.errored.connect(self._handle_worker_error)
        worker.finished.connect(lambda: self._cleanup_worker(thread, worker))

        thread.start()
        self._threads.append(thread)

    def _cleanup_worker(self, thread: QThread, worker: AgentWorker) -> None:
        thread.quit()
        thread.wait()
        worker.deleteLater()
        thread.deleteLater()
        with contextlib.suppress(ValueError):
            self._threads.remove(thread)
        self._set_waiting(False)

    def _handle_worker_error(self, details: str) -> None:
        self._append_message("Pixel", f"Something went wrong:\n{details}")

    def _append_message(self, speaker: str, message: str) -> None:
        safe_speaker = escape(speaker)
        safe_message = escape(message).replace("\n", "<br>")
        self.chat_view.append(f"<b>{safe_speaker}:</b> {safe_message}")

    def _set_waiting(self, waiting: bool) -> None:
        self.send_button.setDisabled(waiting)
        self.reset_button.setDisabled(waiting)
        self.input_box.setDisabled(waiting)
        self.pet_label.setText("=^o^=" if waiting else "=^.^=")

    def closeEvent(self, event: QEvent) -> None:  # pragma: no cover - UI hook
        for thread in self._threads:
            thread.quit()
            thread.wait(200)
            thread.deleteLater()
        self._threads.clear()
        super().closeEvent(event)


__all__ = ["DesktopPetWindow"]
