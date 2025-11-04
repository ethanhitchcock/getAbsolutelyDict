from __future__ import annotations

import logging
from typing import Callable, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..models import AppState

logger = logging.getLogger(__name__)


STATE_COLOURS = {
    AppState.IDLE: "#4caf50",
    AppState.RECORDING: "#f44336",
    AppState.PROCESSING: "#ff9800",
    AppState.ERROR: "#f44336",
}


class TrayController:
    def __init__(
        self,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._tray = QSystemTrayIcon()
        self._menu = QMenu()
        self._tray.setContextMenu(self._menu)

        self._start_action = self._menu.addAction("Start Recording")
        self._start_action.triggered.connect(on_start)
        self._stop_action = self._menu.addAction("Stop Recording")
        self._stop_action.triggered.connect(on_stop)
        self._menu.addSeparator()
        settings_action = self._menu.addAction("Settings")
        settings_action.triggered.connect(on_open_settings)
        quit_action = self._menu.addAction("Quit")
        quit_action.triggered.connect(on_quit)
        self._tray.activated.connect(self._on_activated)
        self._icons: Dict[AppState, QIcon] = {
            state: self._create_icon(colour) for state, colour in STATE_COLOURS.items()
        }
        self.update_state(AppState.IDLE)
        self._tray.show()

    def update_state(self, state: AppState, tooltip: str | None = None) -> None:
        icon = self._icons.get(state)
        if icon:
            self._tray.setIcon(icon)
        if tooltip:
            self._tray.setToolTip(tooltip)
        else:
            self._tray.setToolTip(f"GetDict - {state.value.title()}")
        self._start_action.setEnabled(state in {AppState.IDLE, AppState.ERROR})
        self._stop_action.setEnabled(state == AppState.RECORDING)

    def show_message(self, title: str, message: str, level: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        logger.info("Tray message: %s - %s", title, message)
        self._tray.showMessage(title, message, level)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._menu.popup(QCursor.pos())

    @staticmethod
    def _create_icon(colour: str) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        qcolour = QColor(colour)
        painter.setBrush(qcolour)
        painter.setPen(qcolour)
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        return QIcon(pixmap)
