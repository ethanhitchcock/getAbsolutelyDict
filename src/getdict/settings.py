from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict

from platformdirs import user_config_path

from .models import Hotkey


CONFIG_DIR_NAME = "getdict"
CONFIG_FILE_NAME = "settings.json"


@dataclass
class AudioSettings:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "float32"
    block_size: int = 1024


@dataclass
class TranscriptionSettings:
    provider: str = "openai"
    model: str = "whisper-1"
    language: str | None = None
    temperature: float = 0.0
    api_base_url: str | None = None


@dataclass
class UISettings:
    show_visualizer: bool = True
    autostart: bool = False


@dataclass
class Settings:
    api_key: str | None = None
    hotkey: Hotkey = field(default_factory=lambda: Hotkey(modifier="ctrl+alt", key="space"))
    audio: AudioSettings = field(default_factory=AudioSettings)
    transcription: TranscriptionSettings = field(default_factory=TranscriptionSettings)
    ui: UISettings = field(default_factory=UISettings)

    @classmethod
    def load(cls) -> "Settings":
        config_path = cls._config_path()
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            return cls()
        with config_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, Any] = json.load(fh)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Settings":
        hotkey_data = data.get("hotkey", {})
        hotkey = Hotkey(**hotkey_data)
        audio = AudioSettings(**data.get("audio", {}))
        transcription = TranscriptionSettings(**data.get("transcription", {}))
        ui = UISettings(**data.get("ui", {}))
        return cls(
            api_key=data.get("api_key"),
            hotkey=hotkey,
            audio=audio,
            transcription=transcription,
            ui=ui,
        )

    def save(self) -> None:
        config_path = self._config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as fh:
            json.dump(self._to_dict(), fh, indent=2)

    def _to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["hotkey"] = asdict(self.hotkey)
        data["audio"] = asdict(self.audio)
        data["transcription"] = asdict(self.transcription)
        data["ui"] = asdict(self.ui)
        return data

    @staticmethod
    def _config_path() -> Path:
        return user_config_path(CONFIG_DIR_NAME) / CONFIG_FILE_NAME
