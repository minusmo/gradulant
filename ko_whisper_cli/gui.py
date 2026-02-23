# ko_whisper_cli/gui.py
"""Press-to-record GUI for Korean STT."""

import os
import tempfile
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile

from .stt_core import transcribe_file
from .config import (
    DEFAULT_MODEL_NAME,
    DEFAULT_DEVICE,
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_LANGUAGE,
    DEFAULT_BEAM_SIZE,
    DEFAULT_BEST_OF,
    DEFAULT_TEMPERATURE,
    DEFAULT_VAD_FILTER,
    DEFAULT_VAD_PARAMETERS,
)

SAMPLE_RATE = 16_000

# ── colours ───────────────────────────────────────────────────────────────────
BG = "#1e1e2e"
SURFACE = "#2a2a3e"
RED = "#e74c3c"
RED_DARK = "#c0392b"
GREY = "#7f8c8d"
TEXT_FG = "#ecf0f1"
ACCENT = "#3498db"


class RecorderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ko-stt 녹음기")
        self.resizable(False, False)
        self.configure(bg=BG)

        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=BG, padx=24, pady=24)
        outer.pack()

        # Title
        tk.Label(
            outer,
            text="🎙  한국어 음성 인식",
            font=("", 16, "bold"),
            bg=BG,
            fg=TEXT_FG,
        ).pack(pady=(0, 4))

        # Status label
        self.status_var = tk.StringVar(value="버튼을 누르는 동안 녹음됩니다")
        tk.Label(
            outer,
            textvariable=self.status_var,
            font=("", 11),
            bg=BG,
            fg=GREY,
        ).pack(pady=(0, 16))

        # Record button
        self.record_btn = tk.Button(
            outer,
            text="● 누르고 있는 동안 녹음",
            font=("", 15, "bold"),
            width=22,
            height=2,
            bg=RED,
            fg="white",
            activebackground=RED_DARK,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
        )
        self.record_btn.bind("<ButtonPress-1>", self._on_press)
        self.record_btn.bind("<ButtonRelease-1>", self._on_release)
        self.record_btn.pack(pady=(0, 20))

        # Transcription output
        tk.Label(
            outer,
            text="변환 결과",
            font=("", 10),
            bg=BG,
            fg=GREY,
            anchor="w",
        ).pack(fill=tk.X)

        self.text_area = scrolledtext.ScrolledText(
            outer,
            width=56,
            height=14,
            font=("", 12),
            wrap=tk.WORD,
            bg=SURFACE,
            fg=TEXT_FG,
            insertbackground=TEXT_FG,
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        self.text_area.pack(pady=(4, 12))

        # Action buttons
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack()

        for label, cmd in [("복사", self._copy_text), ("지우기", self._clear_text)]:
            tk.Button(
                btn_row,
                text=label,
                font=("", 11),
                width=10,
                bg=SURFACE,
                fg=TEXT_FG,
                activebackground=GREY,
                relief=tk.FLAT,
                cursor="hand2",
                command=cmd,
            ).pack(side=tk.LEFT, padx=6)

    # ── recording ─────────────────────────────────────────────────────────────

    def _on_press(self, _event: tk.Event) -> None:
        if self._recording:
            return
        self._recording = True
        self._frames = []

        self.status_var.set("녹음 중… (손 떼면 변환 시작)")
        self.record_btn.config(text="■ 녹음 중 (손 떼세요)", bg=GREY)

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,  # noqa: ARG002
        time,  # noqa: ARG002
        status,  # noqa: ARG002
    ) -> None:
        if self._recording:
            self._frames.append(indata.copy())

    def _on_release(self, _event: tk.Event) -> None:
        if not self._recording:
            return
        self._recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.record_btn.config(text="처리 중…", bg=GREY, state=tk.DISABLED)
        self.status_var.set("Whisper 변환 중…")

        threading.Thread(target=self._transcribe, daemon=True).start()

    # ── transcription ─────────────────────────────────────────────────────────

    def _transcribe(self) -> None:
        tmp_path: str | None = None
        try:
            if self._frames:
                audio = np.concatenate(self._frames, axis=0).flatten()
            else:
                audio = np.zeros(SAMPLE_RATE, dtype="float32")

            audio_int16 = (audio * 32_767).clip(-32_768, 32_767).astype(np.int16)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
                tmp_path = fh.name
            wavfile.write(tmp_path, SAMPLE_RATE, audio_int16)

            text, _info = transcribe_file(
                tmp_path,
                model_name=DEFAULT_MODEL_NAME,
                device=DEFAULT_DEVICE,
                compute_type=DEFAULT_COMPUTE_TYPE,
                initial_prompt=DEFAULT_INITIAL_PROMPT,
                language=DEFAULT_LANGUAGE,
                beam_size=DEFAULT_BEAM_SIZE,
                best_of=DEFAULT_BEST_OF,
                temperature=DEFAULT_TEMPERATURE,
                vad_filter=DEFAULT_VAD_FILTER,
                vad_parameters=DEFAULT_VAD_PARAMETERS,
            )

            self.after(0, self._show_result, text)
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._show_error, str(exc))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _show_result(self, text: str) -> None:
        self.text_area.insert(tk.END, text.strip() + "\n")
        self.text_area.see(tk.END)
        self.status_var.set("완료!  버튼을 눌러 계속 녹음하세요")
        self.record_btn.config(
            text="● 누르고 있는 동안 녹음", bg=RED, state=tk.NORMAL
        )

    def _show_error(self, msg: str) -> None:
        messagebox.showerror("오류", msg)
        self.status_var.set("오류 발생 — 다시 시도하세요")
        self.record_btn.config(
            text="● 누르고 있는 동안 녹음", bg=RED, state=tk.NORMAL
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _copy_text(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.text_area.get("1.0", tk.END).strip())

    def _clear_text(self) -> None:
        self.text_area.delete("1.0", tk.END)


def main() -> None:
    app = RecorderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
