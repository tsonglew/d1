"""Overlay window rendering the animated duck pet."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QMovie
from PySide6.QtWidgets import QLabel, QWidget


class DuckOverlayWindow(QWidget):
    """Frameless translucent widget that animates a duck across the screen."""

    duck_clicked = Signal()

    def __init__(self, *, asset_dir: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._asset_dir = asset_dir or Path(__file__).resolve().parents[2] / "assets"
        self._direction = 1
        self._speed_px = 3
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._animate_step)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )

        self._duck_label = QLabel(self)
        self._duck_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._duck_label.setStyleSheet("background: transparent;")

        self._movies = {
            1: self._load_movie("duck-right.gif"),
            -1: self._load_movie("duck-left.gif"),
        }
        self._apply_movie(self._movies[1])
        self._is_dragging = False
        self._drag_offset = QPointF()

    def showEvent(self, event) -> None:  # pragma: no cover - UI hook
        super().showEvent(event)
        self._place_initial()
        if not self._timer.isActive():
            self._timer.start()

    def mousePressEvent(self, event) -> None:  # pragma: no cover - UI hook
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_offset = event.position()
            if self._timer.isActive():
                self._timer.stop()
            self.duck_clicked.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # pragma: no cover - UI hook
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            global_pos = event.globalPosition()
            target_pos = global_pos - self._drag_offset
            self.move(int(target_pos.x()), int(target_pos.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # pragma: no cover - UI hook
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            if not self._timer.isActive():
                self._timer.start()
            event.accept()
        super().mouseReleaseEvent(event)

    def _load_movie(self, filename: str) -> QMovie:
        movie_path = (self._asset_dir / filename).resolve()
        movie = QMovie(str(movie_path))
        movie.setCacheMode(QMovie.CacheMode.CacheAll)
        return movie

    def _apply_movie(self, movie: QMovie) -> None:
        self._duck_label.setMovie(movie)
        movie.jumpToFrame(0)
        frame_size = movie.frameRect().size()
        if frame_size.isValid():
            self.resize(frame_size)
            self._duck_label.resize(frame_size)
        movie.start()

    def _place_initial(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        target_y = geom.bottom() - self.height() - 80
        target_x = geom.left() + (geom.width() // 2)
        self.move(QPoint(target_x, target_y))

    def _animate_step(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        geom = screen.availableGeometry()
        max_x = geom.right() - self.width()
        min_x = geom.left()

        new_x = self.x() + (self._direction * self._speed_px)
        if new_x <= min_x:
            new_x = min_x
            self._direction = 1
            self._apply_movie(self._movies[self._direction])
        elif new_x >= max_x:
            new_x = max_x
            self._direction = -1
            self._apply_movie(self._movies[self._direction])

        self.move(new_x, self.y())


__all__ = ["DuckOverlayWindow"]
