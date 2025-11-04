from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class AppState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


class RecordingError(Exception):
    """Raised when recording fails."""


class TranscriptionError(Exception):
    """Raised when transcription fails."""


@dataclass
class Hotkey:
    modifier: str
    key: str

    def __str__(self) -> str:
        return f"{self.modifier}+{self.key}"


@dataclass
class RecordingResult:
    path: Path
    duration_seconds: float


WaveformCallback = Callable[[float], None]


@dataclass
class TranscriptionRequest:
    audio_path: Path
    prompt: Optional[str] = None


@dataclass
class TranscriptionResult:
    text: str
    duration_seconds: float


@dataclass
class InsertionResult:
    success: bool
    message: Optional[str] = None
