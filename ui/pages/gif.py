"""
Page: 导出 GIF
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
)
from ui.theme import body_font, heading_font, small_font


class GifPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._runner = None
        self._input_path = None
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame,
            text="🖼️导出 GIF",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=["#111827", "#F9FAFB"],
            anchor="w",
        ).place(relx=0, rely=0.5, anchor="w")

        c1 = SectionCard(self)
        c1.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self._file_sel = FileSelector(c1, label="选择视频源", on_change=self._on_file_selected)
        self._file_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        opt_frame = ctk.CTkFrame(c1, fg_color="transparent")
        opt_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        self._gif_width = LabeledOption(opt_frame, "宽度:", ["320", "480", "640", "800"], default="480", width=100)
        self._gif_width.pack(side="left", padx=(0, 20))

        self._gif_fps = LabeledOption(opt_frame, "帧率:", ["5", "10", "15", "20", "24"], default="15", width=100)
        self._gif_fps.pack(side="left")

        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)

        self._out_dir = OutputDirSelector(c2)
        self._out_dir.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._progress = ProgressRow(c2)
        self._progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self._action_btn = ActionButton(c2, start_text="⚡  开始导出 GIF", command=self._on_action)
        self._action_btn.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        self._log = LogBox(self)
        self._log.grid(row=4, column=0, sticky="nsew", padx=24, pady=(0, 20))

    def _on_file_selected(self, path):
        self._input_path = path

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return

        if not self._input_path:
            messagebox.showwarning("提示", "请选择视频源！")
            return

        w = self._gif_width.get()
        fps = self._gif_fps.get()
        out_dir = self._out_dir.get()
        out_path = generate_output_path(self._input_path, "_out", ".gif")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        info = get_video_info(self._input_path)
        filters = f"fps={fps},scale={w}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        cmd = ["ffmpeg", "-y", "-i", self._input_path, "-vf", filters, out_path]

        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        if info:
            self._runner.set_duration(info['duration'])
        self._runner.run(cmd)

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
        self.after(0, self._progress.set, 1.0 if success else 0.0)
