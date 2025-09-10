#!/usr/bin/env python3
import asyncio
import atexit
import os
import tempfile
import threading
import time
import webbrowser
from typing import Optional

import edge_tts
import pygame
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -----------------------
# Config / Defaults
# -----------------------
APP_NAME = "Humanizer"
DEFAULT_VOICE = "en-US-EricNeural"
AUDIO_SUFFIX = ".mp3"  # edge-tts default streaming (mp3 bytes)
LIVE_PREVIEW_DEBOUNCE = 0.6  # seconds to wait after slider move before preview
DONATE_URL = "https://www.every.org/@dev.nayem"

VOICE_OPTIONS = [
    ("en-US-EricNeural", "Male", "English (US)"),
    ("en-US-JennyNeural", "Female", "English (US)"),
    ("en-GB-RyanNeural", "Male", "English (UK)"),
    ("fr-FR-DeniseNeural", "Female", "French (France)"),
    ("ja-JP-KeitaNeural", "Male", "Japanese"),
    ("zh-CN-XiaoxiaoNeural", "Female", "Chinese (Mandarin)"),
]


# -----------------------
# Audio player (pygame)
# -----------------------
class AudioPlayer:
    def __init__(self):
        self.available = False
        self.current_temp_file: Optional[str] = None
        self.volume = 1.0
        try:
            pygame.mixer.init()
            self.available = True
        except Exception as e:
            print("[Audio] Warning:", e)
            self.available = False
        atexit.register(self.cleanup)

    def play_bytes(self, audio_bytes: bytes):
        """Save to temp file and stream with pygame.mixer.music"""
        if not self.available:
            print("[Audio] Not available: skipping playback.")
            return
        self.stop()
        fd, path = tempfile.mkstemp(suffix=AUDIO_SUFFIX)
        os.close(fd)
        with open(path, "wb") as f:
            f.write(audio_bytes)
        self.current_temp_file = path
        try:
            pygame.mixer.music.load(self.current_temp_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
        except Exception as e:
            print("[Audio] Playback error:", e)

    def stop(self):
        try:
            if self.available and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self._delete_temp()

    def set_volume(self, v: float):
        self.volume = max(0.0, min(1.0, v))
        try:
            if self.available:
                pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def _delete_temp(self):
        if self.current_temp_file and os.path.exists(self.current_temp_file):
            try:
                os.remove(self.current_temp_file)
            except Exception:
                pass
        self.current_temp_file = None

    def cleanup(self):
        self.stop()
        try:
            if self.available:
                pygame.mixer.quit()
        except Exception:
            pass


# -----------------------
# TTS helper (edge-tts)
# -----------------------
async def synthesize_bytes_async(text: str, voice: str, rate: str, pitch: str, style: Optional[str] = None) -> bytes:
    """
    Uses edge-tts to stream audio bytes. Returns raw MP3 bytes.
    style currently mapped into SSML via `style` attribute if provided.
    """
    ssml = None
    if style:
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"><voice name="{voice}"><mstts:express-as style="{style}">{text}</mstts:express-as></voice></speak>'

    audio = b""
    try:
        if ssml:
            communicator = edge_tts.Communicate(ssml, voice, rate=rate, pitch=pitch)
        else:
            communicator = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)

        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
    except Exception as e:
        print("[TTS] synthesize error:", e)
    return audio


def synthesize_bytes(text: str, voice: str, rate: str, pitch: str, style: Optional[str] = None) -> bytes:
    """Synchronous wrapper that runs the async code in a new event loop (safe from background threads)."""
    return asyncio.run(synthesize_bytes_async(text, voice, rate, pitch, style))


# -----------------------
# UI / Application
# -----------------------
class HumanizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("860x720")
        self.root.configure(bg="#0b0b0b")
        try:
            self.root.attributes("-alpha", 0.97)
        except Exception:
            pass

        # fonts & style
        self.FONT_TITLE = ("Segoe UI", 28, "bold")
        self.FONT_SUB = ("Segoe UI", 11, "bold")
        self.FONT_BODY = ("Segoe UI", 12)
        self.player = AudioPlayer()
        self.last_audio_bytes = b""
        self.live_preview_enabled = tk.BooleanVar(value=False)
        self._live_preview_timer = None
        self._last_slider_change = 0.0
        self._synthesis_lock = threading.Lock()

        self._build_ui()

    def _build_ui(self):
        # Root container
        root_frame = tk.Frame(self.root, bg="#0f0f0f", bd=0, relief="flat")
        root_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(root_frame, bg="#0f0f0f")
        header.pack(fill="x", pady=(8, 14))

        tk.Label(header, text="HUMANIZER", font=self.FONT_TITLE, fg="#ffffff", bg="#0f0f0f").pack(side="left")

        # Donate clickable link
        donate_label = tk.Label(
            header,
            text="donate ♥",
            font=self.FONT_SUB,
            fg="#8be9fd",
            bg="#0f0f0f",
            cursor="hand2"
        )
        donate_label.pack(side="left", padx=16)
        donate_label.bind("<Button-1>", lambda e: webbrowser.open_new(DONATE_URL))

        # Main area split
        content = tk.Frame(root_frame, bg="#0b0b0b")
        content.pack(fill="both", expand=True)

        left = tk.Frame(content, bg="#0b0b0b")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(content, bg="#0b0b0b", width=320)
        right.pack(side="right", fill="y")

        # Left: Text Editor
        editor_card = tk.Frame(left, bg="#111213", bd=1, relief="flat", highlightbackground="#222226", highlightthickness=1)
        editor_card.pack(fill="both", expand=True)
        tk.Label(editor_card, text="Script / Text", font=self.FONT_SUB, fg="#ffffff", bg="#111213").pack(anchor="nw", padx=12, pady=(12, 6))
        self.text_input = tk.Text(editor_card, height=18, wrap="word", font=self.FONT_BODY,
                                  bg="#0e0e10", fg="#ffffff", insertbackground="#ffffff", bd=0, padx=12, pady=12)
        self.text_input.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Sample buttons
        sample_frame = tk.Frame(left, bg="#0b0b0b")
        sample_frame.pack(fill="x", pady=(8, 0))
        tk.Button(sample_frame, text="Sample: Intro", font=self.FONT_SUB, bg="#1f2937", fg="#ffffff", relief="flat",
                  command=lambda: self._set_sample("Welcome to Humanizer. This is a quick demo of voice generation.")).pack(side="left", padx=6)
        tk.Button(sample_frame, text="Sample: Dramatic", font=self.FONT_SUB, bg="#1f2937", fg="#ffffff", relief="flat",
                  command=lambda: self._set_sample("In a world where code meets voice, every line becomes a story.")).pack(side="left", padx=6)

        # Right: Controls
        controls_card = tk.Frame(right, bg="#0f0f10", bd=1, relief="flat", highlightbackground="#222226", highlightthickness=1)
        controls_card.pack(fill="y", expand=False, pady=0, padx=(0, 0))

        # Voice selector
        tk.Label(controls_card, text="Voice", font=self.FONT_SUB, fg="#ffffff", bg="#0f0f10").pack(anchor="w", padx=12, pady=(12, 0))
        voices = [f"{v[0]} | {v[1]} | {v[2]}" for v in VOICE_OPTIONS]
        self.voice_combo = ttk.Combobox(controls_card, values=voices, state="readonly", font=self.FONT_BODY, width=36)
        self.voice_combo.set(voices[0])
        self.voice_combo.pack(padx=12, pady=8)

        # Rate slider
        tk.Label(controls_card, text="Rate (%)", font=self.FONT_SUB, fg="#ffffff", bg="#0f0f10").pack(anchor="w", padx=12, pady=(10, 0))
        self.rate_var = tk.IntVar(value=0)
        self.rate_scale = ttk.Scale(controls_card, from_=-50, to=50, orient="horizontal", variable=self.rate_var, command=self._on_slider_change)
        self.rate_scale.pack(fill="x", padx=12, pady=6)
        self.rate_label = tk.Label(controls_card, text="0%", font=self.FONT_BODY, fg="#bdbdbd", bg="#0f0f10")
        self.rate_label.pack(anchor="e", padx=12)

        # Pitch slider
        tk.Label(controls_card, text="Pitch (Hz)", font=self.FONT_SUB, fg="#ffffff", bg="#0f0f10").pack(anchor="w", padx=12, pady=(10, 0))
        self.pitch_var = tk.IntVar(value=0)
        self.pitch_scale = ttk.Scale(controls_card, from_=-24, to=24, orient="horizontal", variable=self.pitch_var, command=self._on_slider_change)
        self.pitch_scale.pack(fill="x", padx=12, pady=6)
        self.pitch_label = tk.Label(controls_card, text="0Hz", font=self.FONT_BODY, fg="#bdbdbd", bg="#0f0f10")
        self.pitch_label.pack(anchor="e", padx=12)

        # Volume slider
        tk.Label(controls_card, text="Volume", font=self.FONT_SUB, fg="#ffffff", bg="#0f0f10").pack(anchor="w", padx=12, pady=(10, 0))
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_scale = ttk.Scale(controls_card, from_=0.0, to=1.0, orient="horizontal", variable=self.volume_var, command=self._on_volume_change)
        self.volume_scale.pack(fill="x", padx=12, pady=6)
        self.volume_label = tk.Label(controls_card, text="100%", font=self.FONT_BODY, fg="#bdbdbd", bg="#0f0f10")
        self.volume_label.pack(anchor="e", padx=12)

        # Speaking style
        tk.Label(controls_card, text="Speaking Style", font=self.FONT_SUB, fg="#ffffff", bg="#0f0f10").pack(anchor="w", padx=12, pady=(10, 0))
        self.style_combo = ttk.Combobox(controls_card, values=["none", "cheerful", "angry", "empathetic", "sad", "assistant"], state="readonly", font=self.FONT_BODY)
        self.style_combo.set("none")
        self.style_combo.pack(fill="x", padx=12, pady=6)

        # Live preview
        live_frame = tk.Frame(controls_card, bg="#0f0f10")
        live_frame.pack(fill="x", padx=12, pady=(8, 6))
        tk.Checkbutton(live_frame, text="Live Preview (auto on slider release)", variable=self.live_preview_enabled, fg="#ffffff", bg="#0f0f10", selectcolor="#0f0f10", font=self.FONT_BODY).pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(controls_card, bg="#0f0f10")
        btn_frame.pack(fill="x", padx=12, pady=12)

        self.generate_btn = tk.Button(btn_frame, text="🎙 Generate & Play", font=self.FONT_SUB, bg="#00c853", fg="#000000", relief="flat", command=self.on_generate)
        self.generate_btn.pack(fill="x", pady=(0, 6))

        self.preview_btn = tk.Button(btn_frame, text="🔊 Quick Preview", font=self.FONT_SUB, bg="#2962ff", fg="#ffffff", relief="flat", command=self.on_quick_preview)
        self.preview_btn.pack(fill="x", pady=(0, 6))

        inner = tk.Frame(btn_frame, bg="#0f0f10")
        inner.pack(fill="x")
        self.stop_btn = tk.Button(inner, text="⏹ Stop", font=self.FONT_SUB, bg="#d32f2f", fg="#ffffff", relief="flat", command=self.on_stop)
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.save_btn = tk.Button(inner, text="💾 Save Audio", font=self.FONT_SUB, bg="#3f51b5", fg="#ffffff", relief="flat", command=self.on_save, state="disabled")
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

        # Status
        self.status_label = tk.Label(controls_card, text="Ready", font=self.FONT_BODY, fg="#8be9fd", bg="#0f0f10")
        self.status_label.pack(anchor="w", padx=12, pady=(0, 8))
        self.progress = ttk.Progressbar(controls_card, mode="indeterminate")

        # Key bindings
        self.root.bind("<Return>", lambda e: self.on_generate())

    # -----------------------
    # UI Helpers
    # -----------------------
    def _set_sample(self, text: str):
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", text)

    def _on_slider_change(self, _evt=None):
        self.rate_label.config(text=f"{int(self.rate_var.get())}%")
        self.pitch_label.config(text=f"{int(self.pitch_var.get())}Hz")
        self._last_slider_change = time.time()

        if self.live_preview_enabled.get():
            if self._live_preview_timer and self._live_preview_timer.is_alive():
                return
            def waiter():
                while True:
                    time.sleep(0.12)
                    if time.time() - self._last_slider_change >= LIVE_PREVIEW_DEBOUNCE:
                        self._start_background_synthesis(short_preview=True)
                        break
            self._live_preview_timer = threading.Thread(target=waiter, daemon=True)
            self._live_preview_timer.start()

    def _on_volume_change(self, _evt=None):
        v = float(self.volume_var.get())
        self.volume_label.config(text=f"{int(v * 100)}%")
        self.player.set_volume(v)

    # -----------------------
    # Synthesis
    # -----------------------
    def _start_background_synthesis(self, short_preview: bool = False):
        if self._synthesis_lock.locked():
            return
        def worker():
            with self._synthesis_lock:
                try:
                    self.root.after(0, lambda: self._set_ui_busy(True))
                    text = self.text_input.get("1.0", "end-1c").strip()
                    if short_preview:
                        preview_text = (text.split(".")[0][:120] + "...") if text else "This is a preview."
                        text_to_send = preview_text
                    else:
                        text_to_send = text or "Hello from Humanizer."

                    voice = self.voice_combo.get().split(" | ")[0]
                    rate = f"{'+' if int(self.rate_var.get()) >=0 else ''}{int(self.rate_var.get())}%"
                    pitch = f"{'+' if int(self.pitch_var.get()) >=0 else ''}{int(self.pitch_var.get())}Hz"
                    style = self.style_combo.get() if self.style_combo.get() != "none" else None

                    self.root.after(0, lambda: self._set_status("Generating audio..."))
                    self.root.after(0, lambda: self.progress.pack(fill="x", padx=12, pady=(0,8)))
                    self.progress.start(10)

                    audio_bytes = synthesize_bytes(text_to_send, voice=voice, rate=rate, pitch=pitch, style=style)
                    if audio_bytes:
                        self.last_audio_bytes = audio_bytes
                        self.root.after(0, lambda: self.save_btn.config(state="normal"))
                        self.player.play_bytes(audio_bytes)
                        if short_preview:
                            self.root.after(0, lambda: self._set_status("Live preview playing"))
                        else:
                            self.root.after(0, lambda: self._set_status("Audio ready & playing"))
                    else:
                        self.root.after(0, lambda: self._set_status("Error generating audio"))
                except Exception as e:
                    print("[Worker] error:", e)
                    self.root.after(0, lambda: self._set_status("Error: " + str(e)))
                finally:
                    self.root.after(0, lambda: (self.progress.stop(), self.progress.forget(), self._set_ui_busy(False)))
        threading.Thread(target=worker, daemon=True).start()

    def on_generate(self):
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Input required", "Please enter some text to generate.")
            return
        self._start_background_synthesis(short_preview=False)

    def on_quick_preview(self):
        self._start_background_synthesis(short_preview=True)

    def on_stop(self):
        self.player.stop()
        self._set_status("Stopped.")

    def on_save(self):
        if not self.last_audio_bytes:
            messagebox.showwarning("Nothing to save", "Generate audio first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=AUDIO_SUFFIX, filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(self.last_audio_bytes)
                messagebox.showinfo("Saved", "Audio saved successfully.")
            except Exception as e:
                messagebox.showerror("Save error", str(e))

    # -----------------------
    # Helpers
    # -----------------------
    def _set_status(self, txt: str):
        self.status_label.config(text=txt)

    def _set_ui_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        widgets = [self.generate_btn, self.preview_btn, self.voice_combo, self.style_combo]
        for w in widgets:
            try:
                w.config(state=state)
            except Exception:
                pass
        try:
            self.stop_btn.config(state="normal")
        except Exception:
            pass

    def close(self):
        self.player.cleanup()


# -----------------------
# Entry point
# -----------------------
def main():
    root = tk.Tk()
    app = HumanizerApp(root)
    try:
        root.protocol("WM_DELETE_WINDOW", lambda: (app.close(), root.destroy()))
        root.mainloop()
    finally:
        app.close()


if __name__ == "__main__":
    main()
