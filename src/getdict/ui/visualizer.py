from __future__ import annotations

from collections import deque
from typing import Deque

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget


class WaveformVisualizer(QWidget):
    """Siri-style waveform visualizer with translucent background."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self._amplitudes: Deque[float] = deque(maxlen=60)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(33)
        self.resize(1000, 400)
        self._colors = [
            QColor(203, 36, 128, 160),
            QColor(41, 200, 192, 160),
            QColor(24, 137, 218, 160),
        ]

    def push_amplitude(self, amplitude: float) -> None:
        clamped = max(0.01, min(1.0, amplitude))
        self._amplitudes.append(clamped)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QRadialGradient(self.rect().center(), self.width() * 0.75)
        gradient.setColorAt(0.0, QColor(24, 33, 88))
        gradient.setColorAt(1.0, QColor(3, 4, 20))
        painter.fillRect(self.rect(), gradient)

        if not self._amplitudes:
            return

        width = self.width()
        height = self.height()
        baseline = height / 2
        steps = len(self._amplitudes)
        spacing = width / max(steps - 1, 1)
        for index, color in enumerate(self._colors):
            path = QPainterPath()
            path.moveTo(0, baseline)
            for i, amp in enumerate(self._amplitudes):
                x = i * spacing
                offset = (index + 1) * 12
                y = baseline - (amp * (120 - offset))
                path.lineTo(x, y)
            path.lineTo(width, baseline)
            for i, amp in reversed(list(enumerate(self._amplitudes))):
                x = i * spacing
                offset = (index + 1) * 12
                y = baseline + (amp * (120 - offset))
                path.lineTo(x, y)
            path.closeSubpath()
            painter.setBrush(color)
            painter.setPen(color.lighter(150))
            painter.drawPath(path)
