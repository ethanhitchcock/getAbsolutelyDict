# GetDict

GetDict is a lightweight desktop dictation assistant that lives in the system tray. Press and hold a global hotkey to capture audio, submit it to OpenAI Whisper for transcription, and automatically paste the recognised text into the active application. A Siri-style waveform visualiser reflects microphone input while you speak.

## Features

- 🖱️ **Global hotkey** (default: `ctrl+alt+space`) starts/stops recording from anywhere.
- 🎙️ **Low-latency audio capture** using `sounddevice`, encoded to FLAC before upload.
- 🤖 **Whisper transcription** with automatic retries and configurable model settings.
- 📝 **Automatic text insertion** at the cursor position with clipboard preservation.
- 🪟 **System tray app** with state-aware icon, notifications, and settings dialog.
- 🌊 **Siri-inspired waveform overlay** rendered with PySide6.
- 🔐 **Configurable API key and preferences** stored in the user config directory.

## Quick Start

### 1. Install dependencies

Create a virtual environment (recommended) and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Configure environment

Run the app once to generate `settings.json`, then open the tray menu → **Settings** to provide your OpenAI API key and optionally customise the hotkey or visualiser.

### 3. Launch GetDict

```bash
python -m getdict
```

A tray icon will appear indicating GetDict is ready. Hold the configured hotkey to start dictating. Release it to trigger transcription; the recognised text is pasted into the focused application.

## Tray States

| State       | Colour | Description |
|-------------|--------|-------------|
| Idle        | Green  | Ready for the next recording. |
| Recording   | Red    | Microphone capture in progress. |
| Processing  | Orange | Audio uploading/transcription running. |
| Error       | Red    | An issue occurred – check the notification for details. |

## Settings

Settings are stored at:

- **Windows:** `%APPDATA%\\getdict\\settings.json`
- **macOS/Linux:** `~/.config/getdict/settings.json`

The JSON schema looks like:

```json
{
  "api_key": "sk-…",
  "hotkey": { "modifier": "ctrl+alt", "key": "space" },
  "audio": { "sample_rate": 16000, "channels": 1, "dtype": "float32", "block_size": 1024 },
  "transcription": { "provider": "openai", "model": "whisper-1", "language": null, "temperature": 0.0, "api_base_url": null },
  "ui": { "show_visualizer": true, "autostart": false }
}
```

Most options can be updated through the Settings dialog accessible from the tray icon.

## Architecture Overview

```
+-----------------------+    +----------------------+    +------------------------+
| Hotkey Listener       | -> | Audio Recorder       | -> | FLAC File (temp folder) |
| (pynput)              |    | (sounddevice)        |    +------------------------+
+-----------------------+             |                               |
                                      v                               v
                           +--------------------+        +-------------------------+
                           | Siri-style Visual  |        | Transcription Client    |
                           | Overlay (PySide6)  |        | (OpenAI Whisper API)    |
                           +--------------------+        +-------------------------+
                                                                     |
                                                                     v
                                                     +-----------------------------+
                                                     | Text Insertion (pyperclip + |
                                                     | synthetic paste key event)  |
                                                     +-----------------------------+
```

- **UI Layer:** PySide6 system tray controller, notifications, settings dialog, and waveform overlay.
- **Input Layer:** `pynput` global hotkey listener triggers the recorder.
- **Audio Pipeline:** `sounddevice` streams PCM frames, `soundfile` encodes FLAC.
- **Transcription:** OpenAI Whisper API with exponential-backoff retries.
- **Insertion:** Clipboard-preserving paste using OS-appropriate shortcut.

## Testing

Run automated tests with:

```bash
pytest
```

The current suite covers configuration persistence. GUI, audio, and transcription flows should be exercised manually on target platforms.

## Manual QA Checklist

1. Launch the app and confirm the tray icon appears.
2. Open Settings, configure the API key, and toggle the visualiser.
3. Hold the hotkey – the tray should turn red and the waveform animate.
4. Release the hotkey – tray shows orange while transcribing, then a notification with the recognised snippet.
5. Verify the text is pasted into the active application and clipboard contents are restored.
6. Disconnect networking to confirm error notifications appear and recording recovers.

## Packaging Notes

- Bundle the application with PyInstaller or Briefcase for distribution.
- Register the app for auto-start via OS-specific mechanisms (Task Scheduler / LaunchAgent) if the autostart flag is enabled.
- Sign binaries before distribution for best OS compatibility.

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| No transcription occurs | Confirm the OpenAI API key is set and has sufficient quota. |
| Hotkey does nothing | Ensure no other application uses the same shortcut; change it via Settings. |
| Visualiser not visible | Enable the visualiser toggle or check that the overlay is not behind other windows. |
| Text not inserted | Some secure fields block paste operations – try changing focus or granting accessibility permissions (macOS). |

## License

This repository ships with an MVP implementation and is intended for internal evaluation. Please obtain appropriate permissions before redistribution.
