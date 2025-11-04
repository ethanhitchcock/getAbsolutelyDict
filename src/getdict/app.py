from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from .audio import AudioRecorder
from .hotkeys import HotkeyListener
from .insertion import insert_text
from .models import AppState, RecordingError, TranscriptionError, TranscriptionRequest
from .settings import Settings
from .transcription import TranscriptionClient
from .ui.settings_dialog import SettingsDialog
from .ui.tray import TrayController
from .ui.visualizer import WaveformVisualizer

logger = logging.getLogger(__name__)


class GetDictController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings.load()
        self.state = AppState.IDLE
        self._visualizer: WaveformVisualizer | None = None
        self._recorder = AudioRecorder(self.settings.audio, waveform_callback=self._handle_amplitude)
        self._transcription_client = TranscriptionClient(self.settings)
        self._tray = TrayController(
            on_start=self.start_recording,
            on_stop=self.stop_recording,
            on_open_settings=self.open_settings,
            on_quit=self.quit,
        )
        self._hotkeys = HotkeyListener(
            self.settings.hotkey,
            on_start=self.start_recording,
            on_stop=self.stop_recording,
        )
        self._hotkeys.start()
        self._processing_thread: threading.Thread | None = None
        QTimer.singleShot(0, self._initialise_visualizer)

    def _initialise_visualizer(self) -> None:
        if self.settings.ui.show_visualizer:
            self._visualizer = WaveformVisualizer()
            self._visualizer.show()
        elif self._visualizer:
            self._visualizer.close()
            self._visualizer = None

    def _handle_amplitude(self, amplitude: float) -> None:
        if self._visualizer:
            self._visualizer.push_amplitude(amplitude)

    def update_state(self, state: AppState, tooltip: str | None = None) -> None:
        logger.debug("State transition: %s -> %s", self.state, state)
        self.state = state
        self._tray.update_state(state, tooltip)

    def start_recording(self) -> None:
        if self.state == AppState.RECORDING:
            return
        if not self._transcription_client.is_configured:
            self._tray.show_message("Configuration required", "Set your OpenAI API key in Settings before recording.")
            return
        try:
            self._recorder.start()
        except RecordingError as exc:
            logger.exception("Failed to start recording: %s", exc)
            self.update_state(AppState.ERROR, tooltip="Recording error")
            self._tray.show_message("Recording failed", str(exc))
            return
        self.update_state(AppState.RECORDING, "Listening...")

    def stop_recording(self) -> None:
        if self.state != AppState.RECORDING:
            return
        try:
            result = self._recorder.stop()
        except RecordingError as exc:
            logger.exception("Failed to stop recording: %s", exc)
            self.update_state(AppState.ERROR, "Recording error")
            self._tray.show_message("Recording error", str(exc))
            return
        self.update_state(AppState.PROCESSING, "Transcribing...")
        self._processing_thread = threading.Thread(target=self._process_audio, args=(result.path,), daemon=True)
        self._processing_thread.start()

    def _process_audio(self, audio_path: Path) -> None:
        try:
            request = TranscriptionRequest(audio_path=audio_path)
            transcription = self._transcription_client.transcribe(request)
        except (TranscriptionError, Exception) as exc:
            logger.exception("Transcription failed: %s", exc)
            self.update_state(AppState.ERROR, "Transcription failed")
            self._tray.show_message("Transcription failed", str(exc))
            return
        try:
            insertion = insert_text(transcription.text)
            if not insertion.success:
                self.update_state(AppState.ERROR, insertion.message or "Insertion failed")
                self._tray.show_message("Insertion failed", insertion.message or "Unable to insert text")
                return
            self.update_state(AppState.IDLE, "Ready")
            preview = transcription.text.strip()
            if len(preview) > 120:
                preview = preview[:117] + "…"
            if not preview:
                preview = "(No text recognised)"
            self._tray.show_message("Transcription complete", preview)
        finally:
            try:
                audio_path.unlink(missing_ok=True)
            except Exception:  # pragma: no cover
                logger.debug("Unable to delete temporary audio file %s", audio_path)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings)
        if dialog.exec():
            self._hotkeys.stop()
            self._hotkeys = HotkeyListener(
                self.settings.hotkey,
                on_start=self.start_recording,
                on_stop=self.stop_recording,
            )
            self._hotkeys.start()
            QTimer.singleShot(0, self._initialise_visualizer)
            self._transcription_client = TranscriptionClient(self.settings)
            self.update_state(AppState.IDLE, "Ready")

    def quit(self) -> None:
        logger.info("Shutting down application")
        self._hotkeys.stop()
        QApplication.quit()


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    controller = GetDictController()
    sys.exit(app.exec())
