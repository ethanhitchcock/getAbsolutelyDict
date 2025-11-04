from __future__ import annotations

import json
from pathlib import Path

from getdict.settings import Settings


def test_settings_roundtrip(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_file = config_dir / "settings.json"

    def fake_path() -> Path:
        return config_file

    monkeypatch.setattr(Settings, "_config_path", staticmethod(fake_path))

    settings = Settings()
    settings.api_key = "test-key"
    settings.hotkey.modifier = "ctrl+shift"
    settings.hotkey.key = "space"
    settings.save()

    assert config_file.exists()
    with config_file.open() as fh:
        raw = json.load(fh)
    assert raw["api_key"] == "test-key"

    loaded = Settings.load()
    assert loaded.api_key == "test-key"
    assert loaded.hotkey.modifier == "ctrl+shift"
    assert loaded.hotkey.key == "space"
