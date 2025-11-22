"""Application bootstrap helpers."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .ui import DesktopPetWindow


def run_app(*, window: DesktopPetWindow | None = None) -> None:
    """Entrypoint used by main.py."""
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True

    desktop_window = window or DesktopPetWindow()
    desktop_window.show()

    if owns_app:
        sys.exit(app.exec())
