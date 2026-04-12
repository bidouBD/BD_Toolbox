"""
Page: 视频合并
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import tempfile

from core.ffmpeg_runner import FFmpegRunner
from core.utils import generate_output_path
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, ActionButton,
)
from ui.theme import body_font, heading_font, small_font


class MergePage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._runner = None
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame,
            text="🧩视频合并",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=["#111827", "#F9FAFB"],
            anchor="w",
        ).place(relx=0, rely=0.5, anchor="w")

        c1 = SectionCard(self)
        c1.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self._file_sel = FileSelector(
            c1,
            label="选择多个视频文件",
            multiple=True,
            on_change=self._on_files_selected,
        )
        self._file_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._info_lbl = ctk.CTkLabel(
            c1, text="请确保所有合并文件的分辨率和格式一致，以获得最佳效果。",
            font=small_font(), text_color=["#9CA3AF", "#6B7280"], anchor="w"
        )
        self._info_lbl.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)

        self._out_dir = OutputDirSelector(c2)
        self._out_dir.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._progress = ProgressRow(c2)
        self._progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self._action_btn = ActionButton(c2, start_text="⚡  开始合并", command=self._on_action)
        self._action_btn.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        self._log = LogBox(self)
        self._log.grid(row=4, column=0, sticky="nsew", padx=24, pady=(0, 20))

    def _on_files_selected(self, paths):
        self._info_lbl.configure(text=f"已选择 {len(paths)} 个文件待合并")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return

        paths = self._file_sel.get()
        if not paths or len(paths) < 2:
            messagebox.showwarning("提示", "请选择至少两个文件！")
            return

        list_file = Path(tempfile.gettempdir()) / "ffmpeg_merge_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in paths:
                res_p = str(p).replace('\\', '/')
                f.write(f"file '{res_p}'\n")

        out_dir = self._out_dir.get()
        out_path = generate_output_path(paths[0], "_merged")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", out_path]
        
        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        self._runner.run(cmd)

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
        self.after(0, self._progress.set, 1.0 if success else 0.0)
