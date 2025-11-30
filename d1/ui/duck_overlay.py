"""Overlay window rendering the animated duck pet."""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QMovie, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QMenu, QVBoxLayout, QWidget

from ..agents import PetAgent
from .worker import AgentWorker

logger = logging.getLogger(__name__)


class ChatBubbleWidget(QWidget):
    """Floating dialog bubble drawn with QPainter."""

    def __init__(self, text: str, *, parent: QWidget | None = None) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.BypassWindowManagerHint
        )
        super().__init__(parent)
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._border_width = 4
        self._border_radius = 16
        self._tail_height = 20
        self._tail_width = 32
        self._tail_offset = 40

        self._label = QLabel(text, self)
        self._label.setWordWrap(True)
        self._label.setStyleSheet("color: #222; font-size: 16px; font-weight: bold;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20 + self._tail_height)
        layout.addWidget(self._label)

        self.adjustSize()

    def setText(self, text: str) -> None:
        self._label.setText(text)
        self.adjustSize()
        self.update()

    def paintEvent(self, event) -> None:  # pragma: no cover - UI hook
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("black"))
        pen.setWidth(self._border_width)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("white")))

        rect_x = self._border_width / 2
        rect_y = self._border_width / 2
        rect_w = self.width() - self._border_width
        rect_h = self.height() - self._tail_height - self._border_width

        body_path = QPainterPath()
        body_path.addRoundedRect(QRectF(rect_x, rect_y, rect_w, rect_h), self._border_radius, self._border_radius)

        tail_path = QPainterPath()
        tail_start_x = rect_x + self._tail_offset
        tail_start_y = rect_y + rect_h
        p1 = QPointF(tail_start_x, tail_start_y)
        p2 = QPointF(tail_start_x + self._tail_width, tail_start_y)
        p3 = QPointF(tail_start_x - 10, tail_start_y + self._tail_height)
        tail_path.moveTo(p1)
        tail_path.lineTo(p3)
        tail_path.lineTo(p2)
        tail_path.closeSubpath()

        painter.drawPath(body_path.united(tail_path))


class DuckOverlayWindow(QWidget):
    """Frameless translucent widget that animates a duck across the screen."""

    duck_clicked = Signal()

    def __init__(
        self, *, asset_dir: Path | None = None, parent: QWidget | None = None, agent: PetAgent | None = None
    ) -> None:
        super().__init__(parent=parent)
        self._asset_dir = asset_dir or Path(__file__).resolve().parents[2] / "assets"
        self._agent = agent or PetAgent()
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
        self._current_movie: QMovie | None = None
        self._front_pixmap = self._load_pixmap("duck-frontend.png")
        self._chatbox_label = ChatBubbleWidget("Summoning cosmic quacks...", parent=None)
        self._chatbox_label.hide()
        self._chatbox_timer = QTimer(self)
        self._chatbox_timer.setSingleShot(True)
        self._chatbox_timer.timeout.connect(self._chatbox_label.hide)
        self.destroyed.connect(self._chatbox_label.close)
        self._action_prompts = {
            "click": (
                "A user taps you on their desktop seeking help. Introduce yourself as Nova the Super Duck of the "
                "Multiverse, offer immediate assistance on anything, and invite them to ask for specifics."
            ),
            "chat": (
                "The user opens a context menu and selects 'Chat'. Greet them warmly as Nova the Super Duck, summarize "
                "how you can help with life, code, or creativity, and politely ask what they'd like to do next."
            ),
            "joke": (
                "The user selects 'Joke' from a context menu. Reply as Nova the Super Duck with a single playful, "
                "cosmic-themed joke or pun (keep it under three sentences) and add a cheerful emoji."
            ),
            "touch": (
                "The user gently boops or pats Nova by choosing 'Touch'. React with delight, describe a cute physical "
                "animation, and invite them to keep interacting."
            ),
        }
        self._action_previews = {
            "click": "Nova is tuning in... 🪐",
            "chat": "Nova leans in to chat...",
            "joke": "Nova riffling through joke scrolls...",
            "touch": "Nova fluffs feathers from the boop!",
        }
        self._context_menu = QMenu(self)
        self._chat_action = self._context_menu.addAction("Chat with Nova")
        self._chat_action.triggered.connect(lambda: self._request_duck_reply("chat"))
        self._joke_action = self._context_menu.addAction("Tell me a joke")
        self._joke_action.triggered.connect(lambda: self._request_duck_reply("joke"))
        self._touch_action = self._context_menu.addAction("Touch Nova")
        self._touch_action.triggered.connect(lambda: self._request_duck_reply("touch"))
        self._context_menu.addSeparator()
        self._exit_action = self._context_menu.addAction("Exit")
        self._exit_action.triggered.connect(self._handle_exit)
        self._context_menu.aboutToHide.connect(self._handle_context_menu_closed)
        self._apply_movie(self._movies[1])
        self._is_dragging = False
        self._did_drag = False
        self._drag_offset = QPointF()
        self._is_paused = False
        self._threads: list[QThread] = []
        self._worker_threads: dict[AgentWorker, QThread] = {}
        self._is_generating = False
        self._menu_forced_pause = False

    def showEvent(self, event) -> None:  # pragma: no cover - UI hook
        super().showEvent(event)
        self._place_initial()
        if not self._timer.isActive():
            self._timer.start()

    def moveEvent(self, event) -> None:  # pragma: no cover - UI hook
        super().moveEvent(event)
        self._update_chatbox_position()

    def hideEvent(self, event) -> None:  # pragma: no cover - UI hook
        self._chatbox_label.hide()
        super().hideEvent(event)

    def mousePressEvent(self, event) -> None:  # pragma: no cover - UI hook
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._did_drag = False
            self._drag_offset = event.position()
            if not self._is_paused and self._timer.isActive():
                self._timer.stop()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # pragma: no cover - UI hook
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            global_pos = event.globalPosition()
            target_pos = global_pos - self._drag_offset
            self.move(int(target_pos.x()), int(target_pos.y()))
            if not self._did_drag:
                delta = event.position() - self._drag_offset
                if delta.manhattanLength() >= 1:
                    self._did_drag = True
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # pragma: no cover - UI hook
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            was_drag = self._did_drag
            self._is_dragging = False
            self._did_drag = False
            if was_drag:
                if not self._is_paused and not self._timer.isActive():
                    self._timer.start()
            else:
                self.duck_clicked.emit()
                self._toggle_pause()
                self._request_duck_reply()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:  # pragma: no cover - UI hook
        self._menu_forced_pause = not self._is_paused
        self._set_paused(True)
        self._context_menu.popup(event.globalPos())
        event.accept()

    def _load_movie(self, filename: str) -> QMovie:
        movie_path = (self._asset_dir / filename).resolve()
        movie = QMovie(str(movie_path))
        movie.setCacheMode(QMovie.CacheMode.CacheAll)
        return movie

    def _apply_movie(self, movie: QMovie) -> None:
        if self._current_movie and self._current_movie is not movie:
            self._current_movie.stop()
        self._current_movie = movie
        self._duck_label.setMovie(movie)
        movie.jumpToFrame(0)
        frame_size = movie.frameRect().size()
        if frame_size.isValid():
            self.resize(frame_size)
            self._duck_label.resize(frame_size)
        movie.start()
        self._update_chatbox_position()

    def _apply_pixmap(self, pixmap: QPixmap) -> None:
        if self._current_movie:
            self._current_movie.stop()
            self._current_movie = None
        self._duck_label.clear()
        self._duck_label.setPixmap(pixmap)
        size = pixmap.size()
        if size.isValid():
            self.resize(size)
            self._duck_label.resize(size)
        self._update_chatbox_position()

    def _load_pixmap(self, filename: str) -> QPixmap:
        pixmap_path = (self._asset_dir / filename).resolve()
        pixmap = QPixmap(str(pixmap_path))
        if pixmap.isNull():
            raise FileNotFoundError(f"Missing duck pixmap asset: {pixmap_path}")
        return pixmap

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

    def _toggle_pause(self) -> None:
        self._set_paused(not self._is_paused)

    def _set_paused(self, paused: bool) -> None:
        if self._is_paused == paused:
            return
        self._is_paused = paused
        if paused:
            self._timer.stop()
            self._apply_pixmap(self._front_pixmap)
            return

        self._apply_movie(self._movies[self._direction])
        if not self._timer.isActive():
            self._timer.start()

    def _update_chatbox_position(self) -> None:
        anchor = self._duck_label.rect().topRight()
        anchor_global = self._duck_label.mapToGlobal(anchor)
        label_size = self._chatbox_label.sizeHint()
        target_x = int(anchor_global.x())
        target_y = int(anchor_global.y() - label_size.height())
        self._chatbox_label.move(target_x, target_y)

    def _show_chatbox(self, *, auto_hide: bool = True) -> None:
        self._update_chatbox_position()
        self._chatbox_label.show()
        self._chatbox_label.raise_()
        if auto_hide:
            self._chatbox_timer.start(3000)
        else:
            self._chatbox_timer.stop()

    def _handle_exit(self) -> None:
        app = QGuiApplication.instance()
        if app is None:
            self.close()
            return
        app.quit()

    def _handle_context_menu_closed(self) -> None:
        if not self._menu_forced_pause:
            return
        self._menu_forced_pause = False
        self._set_paused(False)

    def _request_duck_reply(self, action: str = "click") -> None:
        if self._is_generating:
            return
        self._is_generating = True
        preview = self._action_previews.get(action, self._action_previews["click"])
        self._chatbox_label.setText(preview)
        self._show_chatbox(auto_hide=False)
        self._start_worker(self._build_action_prompt(action))

    def _build_action_prompt(self, action: str) -> str:
        return self._action_prompts.get(action, self._action_prompts["click"])

    def _start_worker(self, user_text: str) -> None:
        worker = AgentWorker(self._agent, user_text)
        thread = QThread(self)
        worker.moveToThread(thread)
        self._worker_threads[worker] = thread

        thread.started.connect(worker.run)
        worker.responded.connect(self._handle_agent_reply)
        worker.errored.connect(self._handle_agent_error)
        worker.finished.connect(self._handle_worker_finished)

        thread.start()
        self._threads.append(thread)

    def _handle_worker_finished(self) -> None:
        sender = self.sender()
        if not isinstance(sender, AgentWorker):
            return
        thread = self._worker_threads.pop(sender, None)
        if thread is None:
            return
        self._cleanup_worker(thread, sender)

    def _handle_agent_reply(self, reply: str) -> None:
        message = reply.strip() or "Nova is momentarily speechless, try again!"
        self._chatbox_label.setText(message)
        self._show_chatbox()

    def _handle_agent_error(self, details: str) -> None:
        logger.error("Duck agent failed:\n%s", details)
        self._chatbox_label.setText("My cosmic feathers got ruffled. Try again soon!")
        self._show_chatbox()

    def _cleanup_worker(self, thread: QThread, worker: AgentWorker) -> None:
        thread.quit()
        thread.wait()
        worker.deleteLater()
        thread.deleteLater()
        with contextlib.suppress(ValueError):
            self._threads.remove(thread)
        self._is_generating = False

    def closeEvent(self, event) -> None:  # pragma: no cover - UI hook
        for thread in self._threads:
            thread.quit()
            thread.wait(200)
            thread.deleteLater()
        self._threads.clear()
        super().closeEvent(event)


__all__ = ["DuckOverlayWindow"]
