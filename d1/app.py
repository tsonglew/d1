"""Application bootstrap helpers."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui import DesktopPetWindow, DuckOverlayWindow


def run_app(*, window: DesktopPetWindow | None = None) -> None:
    """Entrypoint used by main.py."""
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True

    chat_window = window or DesktopPetWindow()
    chat_window.hide()

    duck_overlay = DuckOverlayWindow()

    duck_overlay.destroyed.connect(chat_window.close)
    duck_overlay.show()

    # Keep references alive for the duration of the app.
    setattr(app, "_duck_overlay", duck_overlay)
    setattr(app, "_chat_window", chat_window)

    if owns_app:
        sys.exit(app.exec())
