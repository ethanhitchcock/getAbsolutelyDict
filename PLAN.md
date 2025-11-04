# Implementation Plan

1. **Project Scaffolding**
   - Introduce a `pyproject.toml` configured for Poetry-compatible builds using standard build backend.
   - Add a `src/getdict` package with `__main__.py` entry point for `python -m getdict` launches.
   - Provide `requirements.txt` for quick environment setup without Poetry.

2. **Configuration Management**
   - Implement `settings.py` to manage persisted configuration (API key, hotkey, audio + transcription options) stored in the user config directory using JSON.
   - Create a `models.py` housing dataclasses/enums for application state and statuses shared between modules.

3. **Audio Capture Pipeline**
   - Build `audio.py` with an asynchronous recorder powered by `sounddevice` capturing 16 kHz mono audio into a temporary FLAC file, exposing start/stop semantics and waveform callbacks for the visualiser.

4. **Hotkey Handling**
   - Add `hotkeys.py` that uses `pynput` to detect a configurable chord (default Ctrl+Alt) and notifies the app when recording should start or stop.

5. **Transcription Client**
   - Implement `transcription.py` to call the OpenAI Whisper API (or local fallback if offline), with retry/backoff, returning transcribed text plus timing metrics.

6. **Text Injection**
   - Create `insertion.py` capable of pasting the transcribed text into the last focused window using clipboard preservation and simulated key presses (`pyperclip` + `pynput`).

7. **Tray Application + UI**
   - Develop `tray.py` using PySide6 `QSystemTrayIcon` representing Idle/Recording/Processing/Error states with status colour changes and actions for settings, toggle start/stop, and quit.
   - Add `visualizer.py` to render the Siri-style waveform on a transparent `QWidget` overlay fed by audio amplitudes.
   - Provide `settings_dialog.py` for editing hotkeys and API credentials.

8. **Application Orchestration**
   - Implement `app.py` coordinating modules: initialise settings, run tray UI, manage lifecycle of hotkey listener, recorder, transcriber, and insertion.
   - Provide logging configuration and graceful shutdown handling.

9. **Documentation & Packaging**
   - Update `README.md` with setup instructions, feature overview, configuration guide, and troubleshooting tips.
   - Add `.gitignore` tuned for Python + Qt build artefacts.

10. **Testing & QA**
    - Supply minimal smoke tests (e.g., configuration load/save) in `tests/` to exercise core non-GUI logic.
    - Document manual QA steps in README.

