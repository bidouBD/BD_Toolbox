"""
Page 1: 格式转换
Enhanced with VBR, 2-Pass, Hardware Encoders, SLIDER CONTROLS, and AUTO-BITRATE.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import os

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton, LabeledCheckBox, LabeledSlider
)
from ui.theme import body_font, heading_font, small_font


VIDEO_FORMATS = ["mp4", "mkv", "avi", "mov", "flv", "webm", "wmv", "ts", "m4v", "gif"]
ENCODERS = [
    "libx264 (H.264/软编)", "libx265 (H.265/软编)", 
    "h264_nvenc (Nvidia/硬编)", "hevc_nvenc (Nvidia/硬编)",
    "h264_qsv (Intel/硬编)", "hevc_qsv (Intel/硬编)",
    "h264_amf (AMD/硬编)", "hevc_amf (AMD/硬编)",
    "复制原流 (无需重新编码)"
]
ENCODE_MODES = ["画面质量 (CRF)", "目标码率 (VBR/ABR)"]
FRAMERATES = ["保持原始", "60", "50", "30", "25", "24", "15"]
PRESETS = ["ultrafast", "superfast", "veryfast (推荐)", "faster", "fast", "medium (默认)", "slow", "veryslow"]
AUDIO_OPTS = ["保持原始", "重新编码 (AAC 192k)", "移除音频"]


class ConvertPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self._runner = None
        self._input_path = None
        self._input_paths = []
        self._video_info = None
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame, text="🎬 格式转换",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=["#111827", "#F9FAFB"], anchor="w",
        ).place(relx=0, rely=0.5, anchor="w")

        # ── Card 1: File selection ────────────────────────────────
        c1 = SectionCard(self)
        c1.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self._file_sel = FileSelector(c1, label="选择源文件", multiple=True, on_change=self._on_file_selected)
        self._file_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        
        self._info_lbl = ctk.CTkLabel(c1, text="", font=small_font(), text_color=["#9CA3AF", "#6B7280"])
        self._info_lbl.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # ── Card 2: Options ───────────────────────────────────────
        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure((0, 1, 2), weight=1)

        # Row 0
        self._fmt = LabeledOption(c2, "输出格式:", VIDEO_FORMATS, default="mp4", width=140)
        self._fmt.grid(row=0, column=0, padx=16, pady=14, sticky="w")

        self._encoder = LabeledOption(c2, "核心编码器:", ENCODERS, default="libx264 (H.264/软编)", width=220)
        self._encoder.grid(row=0, column=1, padx=16, pady=14, sticky="w")

        self._mode = LabeledOption(c2, "编码模式:", ENCODE_MODES, default="目标码率 (VBR/ABR)", width=180)
        self._mode.grid(row=0, column=2, padx=16, pady=14, sticky="w")
        self._mode.menu.configure(command=self._on_mode_change)

        # Row 1: Sliders, Auto-BR, 2-Pass
        self._val_container = ctk.CTkFrame(c2, fg_color="transparent")
        self._val_container.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")
        
        self._crf_slider = LabeledSlider(self._val_container, "质量系数 (CRF):", from_=0, to=51, default=23)
        self._crf_slider.pack(side="left")

        self._br_slider = LabeledSlider(self._val_container, "目标码率 (kbps):", from_=500, to=40000, number_of_steps=79, default=4000, unit="k")
        # Hidden by default
        
        self._auto_br = LabeledCheckBox(c2, "匹配原始码率:", default=False)
        self._auto_br.grid(row=1, column=1, padx=16, pady=(0, 14), sticky="w")
        self._auto_br.check.configure(command=self._on_auto_br_change)

        self._2pass = None # Removed from UI

        self._audio = LabeledOption(c2, "音频处理:", AUDIO_OPTS, default="保持原始", width=160)
        self._audio.grid(row=1, column=2, padx=16, pady=(0, 14), sticky="w")

        # ── Card 3: Output dir + action ───────────────────────────
        c3 = SectionCard(self)
        c3.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 10))
        c3.grid_columnconfigure(0, weight=1)

        self._out_dir = OutputDirSelector(c3)
        self._out_dir.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        self._progress = ProgressRow(c3)
        self._progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self._action_btn = ActionButton(c3, start_text="⚡  开始执行转换", command=self._on_action)
        self._action_btn.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        self._log = LogBox(self)
        self._log.grid(row=5, column=0, sticky="nsew", padx=24, pady=(0, 20))

        # Initial visibility
        self._on_mode_change(self._mode.get())

    def _on_mode_change(self, mode):
        if "CRF" in mode:
            self._br_slider.pack_forget()
            self._crf_slider.pack(side="left")
            self._auto_br.configure(state="disabled")
        else:
            self._crf_slider.pack_forget()
            self._br_slider.pack(side="left")
            self._auto_br.configure(state="normal")
            # Sync slider state with auto_br checkbox
            self._on_auto_br_change()

    def _on_auto_br_change(self):
        if self._auto_br.get():
            self._br_slider.configure(state="disabled")
        else:
            self._br_slider.configure(state="normal")

    def _on_file_selected(self, paths):
        if not paths:
            self._input_paths = []
            self._input_path = None
            self._info_lbl.configure(text="")
            return
        if isinstance(paths, str): paths = [paths]
        self._input_paths = paths
        self._input_path = paths[0]
        self._video_info = get_video_info(self._input_path)
        if self._video_info:
            size_str = human_size(self._input_path)
            br = self._video_info.get('bitrate', 0)
            br_mbps = (br / 1000000) if br else 0
            if len(paths) > 1:
                self._info_lbl.configure(text=f"📁 已选择 {len(paths)} 个文件 (首个: {Path(self._input_path).name})")
            else:
                self._info_lbl.configure(text=f"📄 {Path(self._input_path).name}  ·  原体积: {size_str}  ·  原码率: {br_mbps:.2f} Mbps")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop(); self._action_btn.set_running(False); return
        if not hasattr(self, '_input_paths') or not self._input_paths:
            messagebox.showwarning("提示", "请先选择源文件"); return

        all_cmds = []
        total_duration = 0
        for p in self._input_paths:
            self._input_path = p
            self._video_info = get_video_info(p)
            if self._video_info:
                total_duration += self._video_info.get('duration', 0)
            cmds = self._build_commands()
            if cmds:
                all_cmds.extend(cmds)

        if not all_cmds: return

        self._log.clear(); self._progress.reset(); self._action_btn.set_running(True)
        self._runner = FFmpegRunner(
            log_callback=self._log.append, progress_callback=self._progress.set, done_callback=self._on_done
        )
        if total_duration > 0: self._runner.set_duration(total_duration)
        self._runner.run(all_cmds)

    def _build_commands(self):
        inp = self._input_path
        fmt = self._fmt.get()
        enc = self._encoder.get().split()[0]
        mode = self._mode.get()
        audio = self._audio.get()
        use_2pass = False

        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, "_conv", f".{fmt}")
        if out_dir: out_path = str(Path(out_dir) / Path(out_path).name)

        if enc == "复制原流":
            return [["ffmpeg", "-y", "-i", inp, "-c", "copy", out_path]]

        v_args = ["-c:v", enc]
        if "CRF" in mode:
            v_args += ["-crf", str(self._crf_slider.get())]
        else:
            if self._auto_br.get() and self._video_info and self._video_info['bitrate']:
                br = self._video_info['bitrate']
                v_args += ["-b:v", f"{br}", "-maxrate:v", f"{int(br*1.2)}", "-bufsize:v", f"{int(br*2)}"]
                self._log.append(f"ℹ 已启用自动比特率匹配: {br // 1000}k")
            else:
                br_kbps = self._br_slider.get()
                v_args += ["-b:v", f"{br_kbps}k", "-maxrate:v", f"{int(br_kbps*1.2)}k", "-bufsize:v", f"{int(br_kbps*2)}k"]
        
        if "nvenc" not in enc and "qsv" not in enc and "amf" not in enc:
            v_args += ["-preset", "medium"]
        
        if audio == "移除音频": a_args = ["-an"]
        elif audio == "重新编码 (AAC 192k)": a_args = ["-c:a", "aac", "-b:a", "192k"]
        else: a_args = ["-c:a", "copy"]

        return [["ffmpeg", "-y", "-i", inp] + v_args + a_args + [out_path]]

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
