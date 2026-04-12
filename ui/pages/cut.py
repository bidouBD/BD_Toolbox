"""
Page 3: 视频裁切
Trim video by start/end time. Fast mode (stream copy) or precise mode (re-encode).
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size, format_time, parse_time
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, LabeledEntry, ActionButton,
)
from ui.theme import body_font, small_font, heading_font


CUT_MODES = ["快速模式（流复制，速度快，可能有误差）", "精确模式（重新编码，精确到帧）"]


class CutPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._runner = None
        self._input_path = None
        self._duration = None
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame,
            text="🕒视频裁切",
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

        # ── Card 2: Time options ──────────────────────────────────
        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure(3, weight=1)

        # Start time
        ctk.CTkLabel(
            c2, text="开始时间:", font=body_font(),
            text_color=["#374151", "#D1D5DB"], anchor="w"
        ).grid(row=0, column=0, padx=(16, 6), pady=14, sticky="w")

        self._start_entry = ctk.CTkEntry(
            c2, placeholder_text="00:00:00", width=120, height=36, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=["#FFFFFF", "#1F2937"],
            border_color=["#D1D5DB", "#4B5563"],
            text_color=["#111827", "#F3F4F6"],
        )
        self._start_entry.grid(row=0, column=1, padx=(0, 20), pady=14)

        # End time
        ctk.CTkLabel(
            c2, text="结束时间:", font=body_font(),
            text_color=["#374151", "#D1D5DB"], anchor="w"
        ).grid(row=0, column=2, padx=(0, 6), pady=14, sticky="w")

        self._end_entry = ctk.CTkEntry(
            c2, placeholder_text="00:00:00", width=120, height=36, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=["#FFFFFF", "#1F2937"],
            border_color=["#D1D5DB", "#4B5563"],
            text_color=["#111827", "#F3F4F6"],
        )
        self._end_entry.grid(row=0, column=3, padx=(0, 16), pady=14, sticky="w")

        # Duration hint + fill button
        self._dur_hint = ctk.CTkLabel(
            c2, text="ℹ 选择文件后显示时长", font=small_font(),
            text_color=["#9CA3AF", "#6B7280"], anchor="w"
        )
        self._dur_hint.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="w")

        self._fill_end_btn = ctk.CTkButton(
            c2,
            text="填入视频总时长",
            width=130, height=30,
            corner_radius=6,
            font=small_font(),
            fg_color=["#E5E7EB", "#374151"],
            hover_color=["#D1D5DB", "#4B5563"],
            text_color=["#374151", "#D1D5DB"],
            command=self._fill_end,
        )
        self._fill_end_btn.grid(row=1, column=2, padx=0, pady=(0, 12), sticky="w")

        # Mode
        self._mode = LabeledOption(
            c2, "裁切模式:", CUT_MODES,
            default="快速模式（流复制，速度快，可能有误差）", width=360
        )
        self._mode.grid(row=2, column=0, columnspan=4, padx=16, pady=(0, 14), sticky="w")

        # ── Card 3: Output + action ───────────────────────────────
        c3 = SectionCard(self)
        c3.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 10))
        c3.grid_columnconfigure(0, weight=1)

        self._out_dir = OutputDirSelector(c3)
        self._out_dir.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._progress = ProgressRow(c3)
        self._progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self._action_btn = ActionButton(c3, start_text="⚡  开始裁切", command=self._on_action)
        self._action_btn.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        # ── Log ───────────────────────────────────────────────────
        self._log = LogBox(self)
        self._log.grid(row=4, column=0, sticky="nsew", padx=24, pady=(0, 20))

    def _on_file_selected(self, path):
        self._input_path = path
        size = human_size(path)
        info = get_video_info(path)
        if info:
            dur = info['duration']
            self._duration = dur
            h = int(dur // 3600); m = int((dur % 3600) // 60); s = int(dur % 60)
            dur_str = f"{h:02d}:{m:02d}:{s:02d}"
            self._dur_hint.configure(
                text=f"⏱ 视频总时长: {dur_str}",
                text_color=["#059669", "#34D399"],
            )
            self._file_info.configure(
                text=f"📄 {Path(path).name}  ·  {size}  ·  时长 {dur_str}"
            )
        else:
            self._dur_hint.configure(
                text="ℹ 无法读取时长，请手动输入",
                text_color=["#9CA3AF", "#6B7280"],
            )
            self._file_info.configure(text=f"📄 {Path(path).name}  ·  {size}")

    def _fill_end(self):
        if self._duration:
            self._end_entry.delete(0, "end")
            self._end_entry.insert(0, format_time(self._duration))

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return

        if not self._input_path:
            messagebox.showwarning("提示", "请先选择视频文件！")
            return

        start_str = self._start_entry.get().strip() or "00:00:00"
        end_str   = self._end_entry.get().strip()
        if not end_str:
            messagebox.showwarning("提示", "请输入结束时间！")
            return

        try:
            start_sec = parse_time(start_str)
            end_sec   = parse_time(end_str)
        except Exception:
            messagebox.showerror("错误", "时间格式错误，请使用 HH:MM:SS 格式")
            return

        if end_sec <= start_sec:
            messagebox.showerror("错误", "结束时间必须大于开始时间！")
            return

        cmd = self._build_command(start_str, end_str)
        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)

        clip_dur = end_sec - start_sec
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        self._runner.set_duration(clip_dur)
        self._runner.run(cmd)

    def _build_command(self, start_str, end_str):
        inp  = self._input_path
        mode = self._mode.get()
        fast = "快速模式" in mode

        out_dir  = self._out_dir.get()
        suffix   = "_cut"
        ext      = Path(inp).suffix
        out_path = generate_output_path(inp, suffix, ext)
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        if fast:
            # Place -ss before -i for fast seek
            cmd = ["ffmpeg", "-y", "-ss", start_str, "-to", end_str,
                   "-i", inp, "-c", "copy", out_path]
        else:
            # Precise: decode then re-encode from start
            cmd = ["ffmpeg", "-y", "-i", inp,
                   "-ss", start_str, "-to", end_str,
                   "-c:v", "libx264", "-c:a", "aac",
                   "-avoid_negative_ts", "1", out_path]
        return cmd

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
        self.after(0, self._progress.set, 1.0 if success else 0.0)
