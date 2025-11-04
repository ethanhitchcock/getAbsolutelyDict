from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from ..models import Hotkey
from ..settings import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("GetDict Settings")
        self.setModal(True)
        self._settings = settings

        self._api_key = QLineEdit(self)
        if settings.api_key:
            self._api_key.setText(settings.api_key)
            self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            self._api_key.setPlaceholderText("OpenAI API Key")
            self._api_key.setEchoMode(QLineEdit.EchoMode.Password)

        self._hotkey = QLineEdit(self)
        self._hotkey.setText(str(settings.hotkey))

        self._visualizer = QCheckBox("Show waveform visualizer", self)
        self._visualizer.setChecked(settings.ui.show_visualizer)

        layout = QFormLayout(self)
        layout.addRow("API Key", self._api_key)
        layout.addRow("Hotkey", self._hotkey)
        layout.addRow("", self._visualizer)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def accept(self) -> None:  # type: ignore[override]
        api_key = self._api_key.text().strip() or None
        hotkey_text = self._hotkey.text().strip()
        if "+" not in hotkey_text:
            QMessageBox.warning(self, "Invalid hotkey", "Use format MODIFIER+KEY, e.g. ctrl+alt+space")
            return
        parts = hotkey_text.split("+")
        modifier = "+".join(parts[:-1])
        key = parts[-1]
        self._settings.api_key = api_key
        self._settings.hotkey = Hotkey(modifier=modifier, key=key)
        self._settings.ui.show_visualizer = self._visualizer.isChecked()
        self._settings.save()
        super().accept()
