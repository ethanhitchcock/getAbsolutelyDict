from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf

from .models import RecordingError, RecordingResult, WaveformCallback
from .settings import AudioSettings

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Captures microphone input and writes it to a FLAC file."""

    def __init__(self, settings: AudioSettings, waveform_callback: Optional[WaveformCallback] = None) -> None:
        self._settings = settings
        self._waveform_callback = waveform_callback
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._start_time: float | None = None
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._temp_file: Optional[NamedTemporaryFile] = None

    def start(self) -> None:
        if self._stream is not None:
            raise RecordingError("Recorder already running")
        self._stop_event.clear()
        self._queue = queue.Queue()
        self._temp_file = NamedTemporaryFile(delete=False, suffix=".flac")
        self._start_time = time.monotonic()
        self._stream = sd.InputStream(
            samplerate=self._settings.sample_rate,
            channels=self._settings.channels,
            dtype=self._settings.dtype,
            blocksize=self._settings.block_size,
            callback=self._callback,
        )
        self._stream.start()
        self._recording_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._recording_thread.start()

    def stop(self) -> RecordingResult:
        if self._stream is None:
            raise RecordingError("Recorder is not running")
        self._stop_event.set()
        self._stream.stop()
        self._stream.close()
        self._stream = None
        if self._recording_thread:
            self._recording_thread.join()
        if self._temp_file is None:
            raise RecordingError("No recording file created")
        duration = 0.0
        if self._start_time is not None:
            duration = time.monotonic() - self._start_time
        return RecordingResult(path=Path(self._temp_file.name), duration_seconds=duration)

    def _callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:  # type: ignore[override]
        if status:
            logger.warning("Audio stream status: %s", status)
        # Copy the buffer to avoid referencing the original data once the callback returns
        self._queue.put(indata.copy())
        if self._waveform_callback:
            amplitude = float(np.abs(indata).mean())
            self._waveform_callback(amplitude)

    def _writer_loop(self) -> None:
        assert self._temp_file is not None
        with sf.SoundFile(
            self._temp_file.name,
            mode="w",
            samplerate=self._settings.sample_rate,
            channels=self._settings.channels,
            subtype="PCM_16",
            format="FLAC",
        ) as file:
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    data = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                file.write(data)
