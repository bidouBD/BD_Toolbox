"""
Page 2: 音频提取
Extract audio track from video files in multiple formats with quality control.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
)
from ui.theme import body_font, small_font


AUDIO_FORMATS  = ["mp3", "aac", "flac", "wav", "ogg", "m4a", "opus", "wma"]
BITRATES_LOSSY = ["64k", "96k", "128k", "160k", "192k (推荐)", "256k", "320k (最高质量)"]
SAMPLE_RATES   = ["保持原始", "44100 Hz", "48000 Hz", "22050 Hz", "16000 Hz"]
CHANNELS       = ["保持原始", "立体声 (2ch)", "单声道 (1ch)"]


class AudioPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._runner = None
        self._input_path = None
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame,
            text="🎵音频提取/转换",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=["#111827", "#F9FAFB"],
            anchor="w",
        ).place(relx=0, rely=0.5, anchor="w")

        # ── Card 1: File ──────────────────────────────────────────
        c1 = SectionCard(self)
        c1.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self._file_sel = FileSelector(
            c1,
            label="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.mkv *.avi *.mov *.flv *.webm *.wmv *.ts *.m4v"),
                ("所有文件", "*.*"),
            ],
            on_change=self._on_file_selected,
        )
        self._file_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._file_info = ctk.CTkLabel(
            c1, text="", font=small_font(),
            text_color=["#9CA3AF", "#6B7280"], anchor="w"
        )
        self._file_info.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # ── Card 2: Options ───────────────────────────────────────
        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure((0, 1, 2), weight=1)

        self._fmt = LabeledOption(c2, "输出格式:", AUDIO_FORMATS, default="mp3", width=140)
        self._fmt.grid(row=0, column=0, padx=16, pady=14, sticky="w")
        self._fmt.menu.configure(command=self._on_format_change)

        self._bitrate = LabeledOption(c2, "音频码率:", BITRATES_LOSSY, default="192k (推荐)", width=180)
        self._bitrate.grid(row=0, column=1, padx=16, pady=14, sticky="w")

        self._sample = LabeledOption(c2, "采样率:", SAMPLE_RATES, default="保持原始", width=160)
        self._sample.grid(row=0, column=2, padx=16, pady=14, sticky="w")

        self._channels = LabeledOption(c2, "声道:", CHANNELS, default="保持原始", width=168)
        self._channels.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")

        # Lossless hint
        self._hint_lbl = ctk.CTkLabel(
            c2, text="", font=small_font(),
            text_color=["#059669", "#34D399"], anchor="w"
        )
        self._hint_lbl.grid(row=1, column=1, columnspan=2, padx=16, pady=(0, 14), sticky="w")

        # ── Card 3: Output + action ───────────────────────────────
        c3 = SectionCard(self)
        c3.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 10))
        c3.grid_columnconfigure(0, weight=1)

        self._out_dir = OutputDirSelector(c3)
        self._out_dir.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._progress = ProgressRow(c3)
        self._progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self._action_btn = ActionButton(c3, start_text="⚡  提取音频", command=self._on_action)
        self._action_btn.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        # ── Log ───────────────────────────────────────────────────
        self._log = LogBox(self)
        self._log.grid(row=4, column=0, sticky="nsew", padx=24, pady=(0, 20))

    def _on_file_selected(self, path):
        self._input_path = path
        size = human_size(path)
        info = get_video_info(path)
        dur_str = ""
        if info:
            dur = info['duration']
            h = int(dur // 3600); m = int((dur % 3600) // 60); s = int(dur % 60)
            dur_str = f"  ·  时长 {h:02d}:{m:02d}:{s:02d}"
        self._file_info.configure(text=f"📄 {Path(path).name}  ·  {size}{dur_str}")

    def _on_format_change(self, fmt):
        lossless = fmt in ("flac", "wav")
        if lossless:
            self._hint_lbl.configure(text="✨ 无损格式：码率选项将被忽略")
            self._bitrate.menu.configure(state="disabled")
        else:
            self._hint_lbl.configure(text="")
            self._bitrate.menu.configure(state="normal")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return

        if not self._input_path:
            messagebox.showwarning("提示", "请先选择输入文件！")
            return

        cmd = self._build_command()
        if not cmd:
            return

        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)

        info = get_video_info(self._input_path)
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        if info:
            self._runner.set_duration(info['duration'])
        self._runner.run(cmd)

    def _build_command(self):
        inp  = self._input_path
        fmt  = self._fmt.get()
        bitrate_raw = self._bitrate.get().split()[0]
        sample = self._sample.get()
        ch = self._channels.get()
        lossless = fmt in ("flac", "wav")

        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, "_audio", f".{fmt}")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        cmd = ["ffmpeg", "-y", "-i", inp, "-vn"]

        if fmt == "mp3":
            cmd += ["-c:a", "libmp3lame"]
        elif fmt == "aac" or fmt == "m4a":
            cmd += ["-c:a", "aac"]
        elif fmt == "ogg":
            cmd += ["-c:a", "libvorbis"]
        elif fmt == "opus":
            cmd += ["-c:a", "libopus"]
        elif fmt == "flac":
            cmd += ["-c:a", "flac"]
        elif fmt == "wav":
            cmd += ["-c:a", "pcm_s16le"]
        else:
            cmd += ["-c:a", "copy"]

        if not lossless and fmt not in ("wav",):
            cmd += ["-b:a", bitrate_raw]

        if sample != "保持原始":
            rate = sample.split()[0]
            cmd += ["-ar", rate]

        if ch == "立体声 (2ch)":
            cmd += ["-ac", "2"]
        elif ch == "单声道 (1ch)":
            cmd += ["-ac", "1"]

        cmd.append(out_path)
        return cmd

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
        self.after(0, self._progress.set, 1.0 if success else 0.0)
