"""
Page: 视频压缩
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    SubtitleLabel, CaptionLabel, InfoBar, InfoBarPosition,
)

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
    LabeledCheckBox, LabeledSlider,
)
from ui.theme import small_font


ENCODERS_COMP = [
    "libx264 (H.264/软编)", "libx265 (H.265/软编)",
    "h264_nvenc (Nvidia/硬编)", "hevc_nvenc (Nvidia/硬编)",
    "h264_qsv (Intel/硬编)", "hevc_qsv (Intel/硬编)",
    "h264_amf (AMD/硬编)", "hevc_amf (AMD/硬编)",
]
RATIOS_CONFIG = {
    "手动调节 (不限制)":  1.0,
    "3/4 (原画质微降)":   0.75,
    "1/2 (高清/推荐)":    0.5,
    "1/3 (平衡体积)":     0.33,
    "1/4 (极致压缩)":     0.25,
}
RATIO_OPTS = list(RATIOS_CONFIG.keys())
ENCODE_MODES_COMP = ["画面质量 (CRF)", "指定目标码率 (VBR/ABR)"]
SCALING_OPTS = ["保持原始分辨率", "缩放至 1080p", "缩放至 720p", "缩放至 480p"]
FRAMERATES = ["保持原始", "60", "50", "30", "25", "24", "15"]
PRESETS = ["ultrafast", "superfast", "veryfast (推荐)", "faster", "fast",
           "medium (默认)", "slow", "veryslow"]
AUDIO_OPTS = ["保持原始", "重新编码 (AAC 128k)", "移除音频"]


class CompressPage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompressPage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._input_path = None
        self._input_paths: list[str] = []
        self._video_info = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 0, 30, 30)
        root.setSpacing(12)

        title = SubtitleLabel("📉 视频压缩", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(20)
        root.addWidget(title)

        # ── Card 1: File ──────────────────────────────────────────────────────
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(10, 10, 10, 10)
        c1_lay.setSpacing(12)

        self._file_sel = FileSelector(
            c1, label="选择视频源文件 (支持批量处理)", multiple=True,
            on_change=self._on_file_selected,
        )
        self._file_sel.btn.setMinimumWidth(240)
        c1_lay.addWidget(self._file_sel)

        self._info_lbl = CaptionLabel("", c1)
        self._info_lbl.setObjectName("VideoInfoLabel")
        self._info_lbl.setFont(small_font())
        self._info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1_lay.addWidget(self._info_lbl)
        c1.layout().addLayout(c1_lay)
        root.addWidget(c1)

        # ── Card 2: Options ───────────────────────────────────────────────────
        c2 = SectionCard(self)
        g = QGridLayout()
        g.setContentsMargins(20, 15, 20, 15)
        g.setHorizontalSpacing(15)
        g.setVerticalSpacing(12)

        # Row 0: dropdowns
        self._ratio = LabeledOption(c2, "✨一键比例:", RATIO_OPTS, default="手动调节 (不限制)")
        self._ratio.menu.currentTextChanged.connect(self._on_ratio_change)
        g.addWidget(self._ratio, 0, 0)

        self._encoder = LabeledOption(c2, "核心编码器:", ENCODERS_COMP, default="libx265 (H.265/软编)")
        g.addWidget(self._encoder, 0, 1)

        self._mode = LabeledOption(c2, "编码模式:", ENCODE_MODES_COMP, default="指定目标码率 (VBR/ABR)")
        self._mode.menu.currentTextChanged.connect(self._on_mode_change)
        g.addWidget(self._mode, 0, 2)

        # Row 1: sliders + 2pass + scale
        #
        # FIX for layout-shift on first dark-mode switch:
        # Previously _crf_slider and _br_slider lived side-by-side in a plain
        # QHBoxLayout inside _val_container.  When one was hidden via hide(),
        # the container shrank, changing grid row 1's height.  After the first
        # theme switch triggered unpolish/polish across the whole window, Qt
        # recalculated all sizeHints and the grid rows jumped.
        #
        # Solution: use QStackedWidget.  It always reserves space for its
        # largest child, so switching pages never changes the row height.

        self._slider_stack = QStackedWidget(c2)
        # Give the stack an explicit minimum height matching the taller slider
        # (spinbox 34px + spacing 8px + slider handle ~20px + margins 8px ≈ 90px)
        self._slider_stack.setMinimumHeight(90)

        self._crf_slider = LabeledSlider(
            self._slider_stack, "质量系数 (CRF):", from_=0, to=51, default=28, unit="")
        self._br_slider = LabeledSlider(
            self._slider_stack, "手动码率 (kbps):", from_=100, to=40000,
            number_of_steps=399, default=2000, unit="k",
            on_change=self._update_estimation)

        self._slider_stack.addWidget(self._crf_slider)   # index 0
        self._slider_stack.addWidget(self._br_slider)    # index 1

        g.addWidget(self._slider_stack, 1, 0, Qt.AlignmentFlag.AlignVCenter)

        self._2pass = LabeledCheckBox(c2, "2-Pass 增强:", default=False)
        g.addWidget(self._2pass, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        self._scale = LabeledOption(c2, "分辨率缩放:", SCALING_OPTS, default="保持原始分辨率")
        g.addWidget(self._scale, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        # Row 2: more dropdowns
        self._preset = LabeledOption(c2, "编码预设:", PRESETS, default="medium (默认)")
        g.addWidget(self._preset, 2, 0, Qt.AlignmentFlag.AlignVCenter)

        self._fps = LabeledOption(c2, "目标帧率:", FRAMERATES, default="保持原始")
        g.addWidget(self._fps, 2, 1, Qt.AlignmentFlag.AlignVCenter)

        self._audio = LabeledOption(c2, "音频处理:", AUDIO_OPTS, default="重新编码 (AAC 128k)")
        g.addWidget(self._audio, 2, 2, Qt.AlignmentFlag.AlignVCenter)

        c2.layout().addLayout(g)
        root.addWidget(c2)

        # ── Card 3: Output + action ───────────────────────────────────────────
        c3 = SectionCard(self)
        c3_lay = QVBoxLayout()
        c3_lay.setContentsMargins(16, 14, 16, 14)
        c3_lay.setSpacing(8)

        self._out_dir = OutputDirSelector(c3)
        c3_lay.addWidget(self._out_dir)

        self._est_lbl = CaptionLabel("预估体积: ~0 MB", c3)
        self._est_lbl.setFont(small_font())
        self._est_lbl.setStyleSheet("color: #00B894;")
        c3_lay.addWidget(self._est_lbl)

        self._progress = ProgressRow(c3)
        c3_lay.addWidget(self._progress)

        self._action_btn = ActionButton(c3, start_text="⚡  开始压缩")
        self._action_btn.clicked.connect(self._on_action)
        c3_lay.addWidget(self._action_btn)

        c3.layout().addLayout(c3_lay)
        root.addWidget(c3)

        self._log = LogBox(self)
        root.addWidget(self._log, 1)

        # Apply the initial mode (determines which slider page is visible)
        self._on_mode_change(self._mode.get())

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_ratio_change(self, opt: str):
        if opt != "手动调节 (不限制)":
            self._mode.set("指定目标码率 (VBR/ABR)")
            self._on_mode_change("指定目标码率 (VBR/ABR)")
            self._br_slider.configure(state="disabled")
            if self._video_info:
                r_val = RATIOS_CONFIG.get(opt, 1.0)
                br = int(self._video_info["bitrate"] * r_val / 1000)
                self._update_estimation(br)
        else:
            self._br_slider.configure(state="normal")
            self._on_mode_change(self._mode.get())
            self._update_estimation(self._br_slider.get())

    def _on_mode_change(self, mode: str):
        if "CRF" in mode:
            # Show CRF slider (stack index 0)
            self._slider_stack.setCurrentWidget(self._crf_slider)
            self._est_lbl.hide()
            self._ratio.configure(state="disabled")
            self._2pass.configure(state="disabled")
        else:
            # Show bitrate slider (stack index 1)
            self._slider_stack.setCurrentWidget(self._br_slider)
            self._est_lbl.show()
            self._ratio.configure(state="normal")
            self._2pass.configure(state="normal")
            self._update_estimation(self._br_slider.get())

    def _on_file_selected(self, paths):
        if not paths:
            self._input_paths = []
            self._input_path = None
            self._info_lbl.setText("")
            return
        if isinstance(paths, str):
            paths = [paths]
        self._input_paths = paths
        self._input_path = paths[0]
        self._video_info = get_video_info(self._input_path)
        if self._video_info:
            size_str = human_size(self._input_path)
            br = self._video_info.get("bitrate", 0)
            br_mbps = (br / 1_000_000) if br else 0
            if len(paths) > 1:
                self._info_lbl.setText(
                    f"📁 已选择 {len(paths)} 个文件 (首个: {Path(self._input_path).name})"
                )
            else:
                self._info_lbl.setText(
                    f"📄 {Path(self._input_path).name}  ·  原体积: {size_str}"
                    f"  ·  估计码率: {br_mbps:.2f} Mbps"
                )
            self._update_estimation(self._br_slider.get())

    def _update_estimation(self, br_kbps):
        if not self._video_info or "指定目标码率" not in self._mode.get():
            self._est_lbl.setText("")
            return
        dur = self._video_info.get("duration", 0)
        size_mb = (br_kbps * dur) / 8 / 1024
        self._est_lbl.setText(f"预估体积: ~{size_mb:.1f} MB")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return
        if not self._input_paths:
            InfoBar.warning("提示", "请先选择源文件",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        all_cmds = []
        total_duration = 0
        for p in self._input_paths:
            self._input_path = p
            self._video_info = get_video_info(p)
            if self._video_info:
                total_duration += self._video_info.get("duration", 0)
            cmds = self._build_commands()
            if cmds:
                all_cmds.extend(cmds)

        if not all_cmds:
            return

        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)

        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        if total_duration > 0:
            self._runner.set_duration(total_duration)
        self._runner.run(all_cmds)

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
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        v_args = ["-c:v", enc]

        if "CRF" in mode:
            v_args += ["-crf", str(self._crf_slider.get())]
        else:
            if ratio_opt != "手动调节 (不限制)":
                if not self._video_info or not self._video_info.get("bitrate"):
                    InfoBar.error("错误", "无法识别视频码率，请改用手动调节模式。",
                                  duration=4000, parent=self,
                                  position=InfoBarPosition.TOP)
                    return None
                r_val = RATIOS_CONFIG.get(ratio_opt, 1.0)
                total_target_br = int(self._video_info["bitrate"] * r_val * 0.95)
                video_target_br = max(100_000, total_target_br - 128_000)
                v_args += ["-b:v", str(video_target_br),
                           "-maxrate:v", str(int(video_target_br * 1.2)),
                           "-bufsize:v", str(int(video_target_br * 2))]
                self._log.append(
                    f"🔮 智能计算: 比例={ratio_opt}, 原始码率="
                    f"{self._video_info['bitrate']//1000}k, "
                    f"目标视频码率={video_target_br//1000}k"
                )
            else:
                br_kbps = self._br_slider.get()
                v_args += ["-b:v", f"{br_kbps}k",
                           "-maxrate:v", f"{int(br_kbps * 1.2)}k",
                           "-bufsize:v", f"{int(br_kbps * 2)}k"]

        if "nvenc" not in enc and "qsv" not in enc and "amf" not in enc:
            v_args += ["-preset", preset]

        if fps != "保持原始":
            v_args += ["-r", fps]

        vf = []
        if "1080p" in scale:  vf.append("scale=1920:-2")
        elif "720p" in scale: vf.append("scale=1280:-2")
        elif "480p" in scale: vf.append("scale=854:-2")
        if vf:
            v_args += ["-vf", ",".join(vf)]

        if audio == "移除音频":
            a_args = ["-an"]
        elif audio == "重新编码 (AAC 128k)":
            a_args = ["-c:a", "aac", "-b:a", "128k"]
        else:
            a_args = ["-c:a", "copy"]

        if not use_2pass or "CRF" in mode:
            return [["ffmpeg", "-y", "-i", inp] + v_args + a_args + [out_path]]
        else:
            null_out = "NUL" if os.name == "nt" else "/dev/null"
            p1 = ["ffmpeg", "-y", "-i", inp] + v_args + ["-pass", "1", "-an", "-f", "null", null_out]
            p2 = ["ffmpeg", "-y", "-i", inp] + v_args + ["-pass", "2"] + a_args + [out_path]
            return [p1, p2]

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")