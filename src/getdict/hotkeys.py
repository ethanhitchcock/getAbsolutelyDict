from __future__ import annotations

import threading
from typing import Callable, Optional, Set

from pynput import keyboard

from .models import Hotkey


ALIASES = {
    "ctrl": {"ctrl", "control"},
    "alt": {"alt", "option"},
    "shift": {"shift"},
    "cmd": {"cmd", "win", "super"},
    "space": {"space", " "},
    "enter": {"enter", "return"},
}


def _canonical(token: str) -> str:
    token = token.strip().lower()
    for canonical, aliases in ALIASES.items():
        if token == canonical or token in aliases:
            return canonical
    return token


def _parse_modifier(modifier: str) -> Set[str]:
    return {_canonical(part) for part in modifier.split("+") if part.strip()}


def _parse_key(key: str) -> str:
    return _canonical(key)


def _key_name(key: keyboard.Key | keyboard.KeyCode) -> str:
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return _canonical(key.char)
        return _canonical(str(key))
    special_map = {
        "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
        "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
        "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
        "cmd": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r} if hasattr(keyboard.Key, "cmd_l") else {keyboard.Key.cmd},
        "space": {keyboard.Key.space},
        "enter": {keyboard.Key.enter},
    }
    for canonical, options in special_map.items():
        if key in options:
            return canonical
    if key.name:
        return _canonical(key.name)
    return _canonical(str(key))


class HotkeyListener:
    def __init__(
        self,
        hotkey: Hotkey,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        self._hotkey = hotkey
        self._on_start = on_start
        self._on_stop = on_stop
        self._listener: Optional[keyboard.Listener] = None
        self._pressed: Set[str] = set()
        self._lock = threading.Lock()
        self._active = False
        self._modifier_keys = _parse_modifier(hotkey.modifier)
        self._primary_key = _parse_key(hotkey.key)

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
        with self._lock:
            self._pressed.clear()
            self._active = False

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        key_name = _key_name(key)
        with self._lock:
            self._pressed.add(key_name)
            if self._is_hotkey_pressed() and not self._active:
                self._active = True
                self._on_start()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        key_name = _key_name(key)
        with self._lock:
            self._pressed.discard(key_name)
            if self._active and not self._is_hotkey_pressed():
                self._active = False
                self._on_stop()

    def _is_hotkey_pressed(self) -> bool:
        return self._modifier_keys.issubset(self._pressed) and self._primary_key in self._pressed
