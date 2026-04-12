"""
Page: 视频压缩
Targeted compression to reduce file size while maintaining quality.
Enhanced with VBR, 2-Pass, HW Encoders, ONE-CLICK SMART RATIO, and SLIDERS.
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


ENCODERS_COMP = [
    "libx264 (H.264/软编)", "libx265 (H.265/软编)", 
    "h264_nvenc (Nvidia/硬编)", "hevc_nvenc (Nvidia/硬编)",
    "h264_qsv (Intel/硬编)", "hevc_qsv (Intel/硬编)",
    "h264_amf (AMD/硬编)", "hevc_amf (AMD/硬编)",
]
# Define ratios with explicit keys
RATIOS_CONFIG = {
    "手动调节 (不限制)": 1.0,
    "3/4 (原画质微降)": 0.75,
    "1/2 (高清/推荐)": 0.5,
    "1/3 (平衡体积)": 0.33,
    "1/4 (极致压缩)": 0.25
}
RATIO_OPTS = list(RATIOS_CONFIG.keys())
ENCODE_MODES_COMP = ["画面质量 (CRF)", "指定目标码率 (VBR/ABR)"]
SCALING_OPTS = ["保持原始分辨率", "缩放至 1080p", "缩放至 720p", "缩放至 480p"]
FRAMERATES = ["保持原始", "60", "50", "30", "25", "24", "15"]
PRESETS = ["ultrafast", "superfast", "veryfast (推荐)", "faster", "fast", "medium (默认)", "slow", "veryslow"]
AUDIO_OPTS = ["保持原始", "重新编码 (AAC 128k)", "移除音频"]


class CompressPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=["#F2F4F8", "#1F2937"], corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self._runner = None
        self._input_path = None
        self._video_info = None
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        title_frame.grid(row=0, column=0, sticky="ew", **pad)
        title_frame.grid_propagate(False)
        ctk.CTkLabel(
            title_frame, text="📉 视频压缩",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=18, weight="bold"),
            text_color=["#111827", "#F9FAFB"], anchor="w",
        ).place(relx=0, rely=0.5, anchor="w")

        # ── Card 1: File selection ────────────────────────────────
        c1 = SectionCard(self)
        c1.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self._file_sel = FileSelector(c1, label="选择压缩源文件", on_change=self._on_file_selected)
        self._file_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=16)

        self._info_lbl = ctk.CTkLabel(c1, text="", font=small_font(), text_color=["#9CA3AF", "#6B7280"])
        self._info_lbl.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # ── Card 2: Options ───────────────────────────────────────
        c2 = SectionCard(self)
        c2.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        c2.grid_columnconfigure((0, 1, 2), weight=1)

        # Row 0: Ratio (One-Click)
        self._ratio = LabeledOption(c2, "✨一键比例:", RATIO_OPTS, default="手动调节 (不限制)", width=180)
        self._ratio.grid(row=0, column=0, padx=16, pady=14, sticky="w")
        self._ratio.menu.configure(command=self._on_ratio_change)

        self._encoder = LabeledOption(c2, "核心编码器:", ENCODERS_COMP, default="libx265 (H.265/软编)", width=165)
        self._encoder.grid(row=0, column=1, padx=16, pady=14, sticky="w")

        self._mode = LabeledOption(c2, "编码模式:", ENCODE_MODES_COMP, default="指定目标码率 (VBR/ABR)", width=180)
        self._mode.grid(row=0, column=2, padx=16, pady=14, sticky="w")
        self._mode.menu.configure(command=self._on_mode_change)

        # Row 1: Sliders, Scaling, 2-Pass
        self._val_container = ctk.CTkFrame(c2, fg_color="transparent")
        self._val_container.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")
        
        self._crf_slider = LabeledSlider(self._val_container, "质量系数 (CRF):", from_=0, to=51, default=28, slider_width=255)
        # hidden by default

        self._br_slider = LabeledSlider(self._val_container, "手动码率 (kbps):", from_=100, to=40000, number_of_steps=399, default=2000, unit="k", on_change=self._update_estimation, slider_width=255)
        self._br_slider.pack(side="left")

        self._2pass = LabeledCheckBox(c2, "2-Pass 增强:", default=False, width=160)
        self._2pass.grid(row=1, column=1, padx=16, pady=(0, 14), sticky="w")

        self._scale = LabeledOption(c2, "分辨率缩放:", SCALING_OPTS, default="保持原始分辨率", width=168)
        self._scale.grid(row=1, column=2, padx=16, pady=(0, 14), sticky="w")

        # Row 2: Preset, FPS, Audio
        self._preset = LabeledOption(c2, "编码预设:", PRESETS, default="medium (默认)", width=200)
        self._preset.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="w")

        self._fps = LabeledOption(c2, "目标帧率:", FRAMERATES, default="保持原始", width=180)
        self._fps.grid(row=2, column=1, padx=16, pady=(0, 14), sticky="w")

        self._audio = LabeledOption(c2, "音频处理:", AUDIO_OPTS, default="重新编码 (AAC 128k)", width=180)
        self._audio.grid(row=2, column=2, padx=16, pady=(0, 14), sticky="w")

        # ── Card 3: Output dir + action ───────────────────────────
        c3 = SectionCard(self)
        c3.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 10))
        c3.grid_columnconfigure(0, weight=1)

        self._out_dir = OutputDirSelector(c3)
        self._out_dir.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))

        self._est_lbl = ctk.CTkLabel(c3, text="预估体积: ~0 MB", font=small_font(), text_color="#00B894", anchor="w")
        self._est_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 10))

        self._progress = ProgressRow(c3)
        self._progress.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))

        self._action_btn = ActionButton(c3, start_text="⚡  开始智能压缩", command=self._on_action)
        self._action_btn.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

        self._log = LogBox(self)
        self._log.grid(row=5, column=0, sticky="nsew", padx=24, pady=(0, 20))
        
        # Init visibility
        self._on_mode_change(self._mode.get())

    def _on_ratio_change(self, opt):
        if opt != "手动调节 (不限制)":
            self._mode.set("指定目标码率 (VBR/ABR)")
            self._on_mode_change("指定目标码率 (VBR/ABR)")
            self._br_slider.configure(state="disabled")
            # Update estimation for auto ratio
            if self._video_info:
                r_val = RATIOS_CONFIG.get(opt, 1.0)
                br = int(self._video_info['bitrate'] * r_val / 1000)
                self._update_estimation(br)
        else:
            self._br_slider.configure(state="normal")
            self._on_mode_change(self._mode.get())
            self._update_estimation(self._br_slider.get())

    def _on_mode_change(self, mode):
        if "CRF" in mode:
            self._br_slider.pack_forget()
            self._est_lbl.grid_forget()
            self._crf_slider.pack(side="left")
            self._ratio.menu.configure(state="disabled")
            self._2pass.configure(state="disabled")
        else:
            self._crf_slider.pack_forget()
            self._br_slider.pack(side="left")
            self._est_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 10))
            self._ratio.menu.configure(state="normal")
            self._2pass.configure(state="normal")
            self._update_estimation(self._br_slider.get())

    def _on_file_selected(self, path):
        self._input_path = path
        self._video_info = get_video_info(path)
        if self._video_info:
            size_str = human_size(path)
            br = self._video_info.get('bitrate', 0)
            br_mbps = (br / 1000000) if br else 0
            self._info_lbl.configure(text=f"📄 {Path(path).name}  ·  原体积: {size_str}  ·  估计码率: {br_mbps:.2f} Mbps")
            self._update_estimation(self._br_slider.get())

    def _update_estimation(self, br_kbps):
        if not self._video_info or "指定目标码率" not in self._mode.get():
            self._est_lbl.configure(text="")
            return
        dur = self._video_info.get('duration', 0)
        # Size = (Bitrate * Duration) / 8 / 1024 / 1024 -> MB
        # br_kbps is in kilobits per second
        size_mb = (br_kbps * dur) / 8 / 1024
        self._est_lbl.configure(text=f"预估体积: ~{size_mb:.1f} MB")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop(); self._action_btn.set_running(False); return
        if not self._input_path:
            messagebox.showwarning("提示", "请先选择源文件"); return

        cmds = self._build_commands()
        if not cmds: return
        
        self._log.clear(); self._progress.reset(); self._action_btn.set_running(True)
        self._runner = FFmpegRunner(
            log_callback=self._log.append, progress_callback=self._progress.set, done_callback=self._on_done
        )
        if self._video_info: self._runner.set_duration(self._video_info['duration'])
        self._runner.run(cmds)

    def _build_commands(self):
        inp = self._input_path
        enc = self._encoder.get().split()[0]
        mode = self._mode.get()
        ratio_opt = self._ratio.get()
        scale = self._scale.get()
        use_2pass = self._2pass.get()
        preset = self._preset.get().split()[0]
        fps = self._fps.get()
        audio = self._audio.get()

        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, "_compressed", Path(inp).suffix)
        if out_dir: out_path = str(Path(out_dir) / Path(out_path).name)

        v_args = ["-c:v", enc]
        
        # Calculate bitrates
        if "CRF" in mode:
            v_args += ["-crf", str(self._crf_slider.get())]
        else:
            if ratio_opt != "手动调节 (不限制)":
                if not self._video_info or not self._video_info.get('bitrate'):
                    messagebox.showerror("错误", "无法识别视频码率，请改用手动调节模式。")
                    return None
                
                r_val = RATIOS_CONFIG.get(ratio_opt, 1.0)
                # Video bitrate should be slightly less than total target to account for audio
                # We also subtract a small margin (5%) for container overhead to improve accuracy
                total_target_br = int(self._video_info['bitrate'] * r_val * 0.95)
                # Substract estimated audio (128k) but don't go below 100k
                video_target_br = max(100000, total_target_br - 128000)
                
                v_args += ["-b:v", str(video_target_br)]
                # Add strict constraints to force the encoder to obey the limit
                v_args += ["-maxrate:v", str(int(video_target_br * 1.2)), "-bufsize:v", str(int(video_target_br * 2))]
                
                self._log.append(f"🔮 智能计算: 比例={ratio_opt}, 原始码率={self._video_info['bitrate']//1000}k, 目标视频码率={video_target_br//1000}k")
            else:
                br_kbps = self._br_slider.get()
                v_args += ["-b:v", f"{br_kbps}k", "-maxrate:v", f"{int(br_kbps*1.2)}k", "-bufsize:v", f"{int(br_kbps*2)}k"]

        if "nvenc" not in enc and "qsv" not in enc and "amf" not in enc:
            v_args += ["-preset", preset]

        if fps != "保持原始": v_args += ["-r", fps]

        vf = []
        if "1080p" in scale: vf.append("scale=1920:-2")
        elif "720p" in scale: vf.append("scale=1280:-2")
        elif "480p" in scale: vf.append("scale=854:-2")
        if vf: v_args += ["-vf", ",".join(vf)]

        if audio == "移除音频": a_args = ["-an"]
        elif audio == "重新编码 (AAC 128k)": a_args = ["-c:a", "aac", "-b:a", "128k"]
        else: a_args = ["-c:a", "copy"]

        if not use_2pass or "CRF" in mode:
            return [["ffmpeg", "-y", "-i", inp] + v_args + a_args + [out_path]]
        else:
            p1 = ["ffmpeg", "-y", "-i", inp] + v_args + ["-pass", "1", "-an", "-f", "null", "NUL" if os.name == 'nt' else "/dev/null"]
            p2 = ["ffmpeg", "-y", "-i", inp] + v_args + ["-pass", "2"] + a_args + [out_path]
            return [p1, p2]

    def _on_done(self, success):
        self.after(0, self._action_btn.set_running, False)
