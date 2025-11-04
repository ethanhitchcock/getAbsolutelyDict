from __future__ import annotations

import platform
import time
from contextlib import suppress

import pyperclip
from pynput import keyboard

from .models import InsertionResult

PASTE_DELAY = 0.1


def insert_text(text: str) -> InsertionResult:
    controller = keyboard.Controller()
    system = platform.system().lower()
    modifier = keyboard.Key.cmd if system == "darwin" else keyboard.Key.ctrl

    original_clipboard = None
    with suppress(Exception):
        original_clipboard = pyperclip.paste()
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:  # type: ignore[attr-defined]
        return InsertionResult(success=False, message=str(exc))

    time.sleep(PASTE_DELAY)
    with controller.pressed(modifier):
        controller.press('v')
        controller.release('v')
    time.sleep(PASTE_DELAY)

    if original_clipboard is not None:
        with suppress(Exception):
            pyperclip.copy(original_clipboard)
    return InsertionResult(success=True)
