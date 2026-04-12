"""
Page: 视频实验室 (Video Lab)
Collection of experimental and automated video processing tools.
Includes: auto crop detector, volume normalization, auto rotation fix, silence detection.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import re
import subprocess

from core.ffmpeg_runner import FFmpegRunner, get_ffmpeg_path
from core.utils import get_video_info, generate_output_path, human_size
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, ActionButton,
)
from ui.theme import body_font, heading_font, small_font

LAB_TOOLS = [
    ("cropdetect",  "✂️", "自动黑边裁切", "自动检测视频黑边并移除（如电影画幅转全屏）"),
    ("volumenorm", "🔊", "音量标准化", "一键平衡视频音量，解决声音忽大忽小的问题"),
    ("autorotate", "🔄", "画面旋转修复", "物理级旋转像素，纠正倒置或侧翻的视频画面"),
    ("silencecut", "🔇", "静音智能剪辑", "自动识别并切除无声片段，提升视频紧凑度（Vlog神器）"),
]

class LabPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self._runner = None
        self._input_path = None
        self._current_tool = "cropdetect"
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame, text="🧪 视频实验室",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=["#111827", "#F9FAFB"], anchor="w",
        ).place(relx=0, rely=0.5, anchor="w")

        # ── Card 1: Tool Selection ────────────────────────────────
        c1 = SectionCard(self)
        c1.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        tool_frame = ctk.CTkFrame(c1, fg_color="transparent")
        tool_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        
        self.tool_btns = {}
        for i, (key, icon, name, desc) in enumerate(LAB_TOOLS):
            btn = ctk.CTkButton(
                tool_frame, text=f"{icon} {name}", 
                width=170, height=44, corner_radius=10,
                fg_color="transparent", border_width=1,
                border_color=["#D1D5DB", "#374151"],
                text_color=["#374151", "#D1D5DB"],
                hover_color=["#E5E7EB", "#2D3748"],
                command=lambda k=key: self._select_tool(k)
            )
            btn.grid(row=0, column=i, padx=8)
            self.tool_btns[key] = btn
        
        self._tool_desc = ctk.CTkLabel(
            c1, text=LAB_TOOLS[0][3], font=small_font(),
            text_color=["#6B7280", "#9CA3AF"], anchor="w"
        )
        self._tool_desc.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        self._select_tool("cropdetect")

        # ── Card 2: File & Action ─────────────────────────────────
        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)

        self._file_sel = FileSelector(c2, label="选择处理文件", on_change=self._on_file_selected)
        self._file_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=16)

        self._out_dir = OutputDirSelector(c2)
        self._out_dir.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))

        self._progress = ProgressRow(c2)
        self._progress.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        self._action_btn = ActionButton(c2, start_text="⚡  一键实验室处理", command=self._on_action)
        self._action_btn.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))

        # ── Logbox ────────────────────────────────────────────────
        self._log = LogBox(self)
        self._log.grid(row=5, column=0, sticky="nsew", padx=24, pady=(0, 20))

    def _select_tool(self, key):
        self._current_tool = key
        for k, btn in self.tool_btns.items():
            if k == key:
                btn.configure(fg_color=["#D6F5EE", "#064E3B"], border_width=0, text_color=["#007A64", "#34D399"])
            else:
                btn.configure(fg_color="transparent", border_width=1, text_color=["#374151", "#D1D5DB"])
        
        for k, i, n, d in LAB_TOOLS:
            if k == key:
                self._tool_desc.configure(text=d)

    def _on_file_selected(self, path):
        self._input_path = path

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return

        if not self._input_path:
            messagebox.showwarning("提示", "请先选择视频文件")
            return

        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)

        if self._current_tool == "cropdetect":
            self._handle_cropdetect()
        else:
            cmd = self._build_tool_command()
            info = get_video_info(self._input_path)
            self._runner = FFmpegRunner(
                log_callback=self._log.append, progress_callback=self._progress.set, done_callback=self._on_done
            )
            if info: self._runner.set_duration(info['duration'])
            self._runner.run(cmd)

    def _build_tool_command(self):
        inp = self._input_path
        out_dir = self._out_dir.get()
        suffix = f"_{self._current_tool}"
        out_path = generate_output_path(inp, suffix, Path(inp).suffix)
        if out_dir: out_path = str(Path(out_dir) / Path(out_path).name)

        if self._current_tool == "volumenorm":
            return ["ffmpeg", "-y", "-i", inp, "-af", "loudnorm", "-c:v", "copy", out_path]
        elif self._current_tool == "autorotate":
            return ["ffmpeg", "-y", "-i", inp, "-vf", "transpose=1", "-metadata:s:v:0", "rotate=0", out_path]
        elif self._current_tool == "silencecut":
            # Just a simple silenceremove demo for now
            return ["ffmpeg", "-y", "-i", inp, "-af", "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-30dB", out_path]
        return None

    def _handle_cropdetect(self):
        self._log.append("🔍 正在检测黑边，请稍候...")
        # Step 1: Detect
        cmd = [get_ffmpeg_path(), "-ss", "00:00:10", "-i", self._input_path, "-vframes", "100", "-vf", "cropdetect", "-f", "null", "-"]
        
        def run_detect():
            p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, universal_newlines=True, encoding='utf-8')
            detected = None
            for line in p.stderr:
                if "crop=" in line:
                    m = re.search(r"crop=([0-9:]+)", line)
                    if m: detected = m.group(1)
            p.wait()
            self.after(0, lambda: self._apply_crop(detected))

        import threading
        threading.Thread(target=run_detect, daemon=True).start()

    def _apply_crop(self, crop_val):
        if not crop_val:
            self._log.append("❌ 未检测到明显黑边。")
            self._action_btn.set_running(False)
            return

        self._log.append(f"✅ 检测到裁剪区域: {crop_val}")
        out_path = generate_output_path(self._input_path, "_cropped", Path(self._input_path).suffix)
        if self._out_dir.get():
            out_path = str(Path(self._out_dir.get()) / Path(out_path).name)
        
        final_cmd = ["ffmpeg", "-y", "-i", self._input_path, "-vf", f"crop={crop_val}", out_path]
        self._runner = FFmpegRunner(
            log_callback=self._log.append, progress_callback=self._progress.set, done_callback=self._on_done
        )
        self._runner.run(final_cmd)

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
