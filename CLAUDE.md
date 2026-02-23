# CLAUDE.md

## Session Summary

### 2026-02-23 — Korean STT CLI (ko-whisper-cli)

Built a macOS Korean speech-to-text CLI tool using faster-whisper + Whisper large-v3.

**Branch:** `claude/korean-stt-cli-KMolq`

**What was created:**

- `ko_whisper_cli/config.py` — default constants (model, device, VAD params, language)
- `ko_whisper_cli/stt_core.py` — WhisperModel loader with in-process cache, `transcribe_file()`
- `ko_whisper_cli/cli.py` — click CLI exposing `ko-stt` command with options: `--output`, `--prompt`, `--model`, `--device`, `--compute-type`, `--beam-size`, `--best-of`, `--temperature`, `--no-vad`
- `pyproject.toml` — package definition; registers `ko-stt` console script entry point
- `plan.md` — full project plan (Korean)
- `README.md` — installation and usage guide (Korean)
- `.gitignore` — excludes `.venv/`, build artifacts, model cache, audio files

**Key design decisions:**

- Default device: `mps` (Apple Silicon), compute type: `float16`
- Default model: `large-v3`; `large-v3-turbo` available via `--model`
- Language hardcoded to `ko`; VAD enabled by default with 500ms silence threshold
- Model instances cached in `_model_cache` dict keyed by `(model_name, device, compute_type)`

**Install & run:**

```bash
uv sync
# or: python -m venv .venv && source .venv/bin/activate && pip install -e .
ko-stt meeting.m4a
```

---

### 2026-02-23 — Press-to-Record GUI (ko-stt-gui)

Added a tkinter-based GUI that lets the user hold a button to record and auto-transcribes on release.

**Branch:** `claude/korean-stt-cli-KMolq`

**What was created / changed:**

- `ko_whisper_cli/gui.py` — `RecorderApp(tk.Tk)` GUI with:
  - Hold-to-record button (press → record via `sounddevice`, release → transcribe)
  - Audio captured at 16 kHz mono float32, saved to a temp WAV via `scipy.io.wavfile`
  - Transcription runs on a daemon thread to keep the UI responsive
  - Scrollable result text area with Copy / Clear actions
  - Dark-themed colour palette
- `pyproject.toml` — added `sounddevice`, `numpy`, `scipy` dependencies; registered `ko-stt-gui` console script entry point

**Key design decisions:**

- `tkinter` chosen (stdlib) to avoid heavy GUI framework dependencies
- `sounddevice.InputStream` with a callback accumulates frames while the button is held
- Temp WAV is deleted after transcription succeeds or fails (finally block)
- All defaults reuse existing `config.py` constants — no new config surface

**Run the GUI:**

```bash
uv sync
# or: pip install -e .
ko-stt-gui
```
