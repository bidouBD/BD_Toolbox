"""
Page 1: 视频转换
Enhanced with VBR, 2-Pass, Hardware Encoders, SLIDER CONTROLS, and AUTO-BITRATE.
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CaptionLabel, InfoBar, InfoBarPosition,
)

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
    LabeledCheckBox, LabeledSlider,
)
from ui.theme import body_font, small_font


VIDEO_FORMATS = ["mp4", "mkv", "avi", "mov", "flv", "webm", "wmv", "ts", "m4v", "gif"]
ENCODERS = [
    "libx264 (H.264/软编)", "libx265 (H.265/软编)",
    "h264_nvenc (Nvidia/硬编)", "hevc_nvenc (Nvidia/硬编)",
    "h264_qsv (Intel/硬编)", "hevc_qsv (Intel/硬编)",
    "h264_amf (AMD/硬编)", "hevc_amf (AMD/硬编)",
    "复制原流 (无需重新编码)",
]
ENCODE_MODES = ["画面质量 (CRF)", "目标码率 (VBR/ABR)"]
FRAMERATES = ["保持原始", "60", "50", "30", "25", "24", "15"]
AUDIO_OPTS = ["保持原始", "重新编码 (AAC 192k)", "移除音频"]


class ConvertPage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConvertPage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._input_path = None
        self._input_paths: list[str] = []
        self._video_info = None
        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 0, 30, 30)
        root.setSpacing(12)
        
        # Will force layout refresh after all widgets are added
        self._root_layout = root

        # Title
        title = SubtitleLabel("🔄 视频转换", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(20)
        root.addWidget(title)

        # ── Card 1: File selection ────────────────────────────────────────────
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
        c2_lay = QGridLayout()
        c2_lay.setContentsMargins(20, 15, 20, 15)
        c2_lay.setHorizontalSpacing(15)
        c2_lay.setVerticalSpacing(12)
        c2_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._fmt = LabeledOption(c2, "输出格式:", VIDEO_FORMATS, default="mp4")
        c2_lay.addWidget(self._fmt, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        
        self._encoder = LabeledOption(c2, "核心编码器:", ENCODERS, default="libx264 (H.264/软编)")
        c2_lay.addWidget(self._encoder, 0, 1, Qt.AlignmentFlag.AlignVCenter)
        
        self._mode = LabeledOption(c2, "编码模式:", ENCODE_MODES, default="目标码率 (VBR/ABR)")
        self._mode.menu.currentTextChanged.connect(self._on_mode_change)
        c2_lay.addWidget(self._mode, 0, 2, Qt.AlignmentFlag.AlignVCenter)

        # FIX for layout-shift on first dark-mode switch: Use QStackedWidget
        self._slider_stack = QStackedWidget(c2)
        self._slider_stack.setMinimumHeight(90)

        self._crf_slider = LabeledSlider(
            self._slider_stack, "质量系数 (CRF):", from_=0, to=51, default=23, unit="")
        self._br_slider = LabeledSlider(
            self._slider_stack, "目标码率 (kbps):", from_=500, to=40000,
            number_of_steps=79, default=4000, unit="k")
        
        self._slider_stack.addWidget(self._crf_slider)
        self._slider_stack.addWidget(self._br_slider)

        # Move slider to row 1, spanning 2 columns for better width
        c2_lay.addWidget(self._slider_stack, 1, 0, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        self._auto_br = LabeledCheckBox(c2, "匹配原始码率:", default=False)
        self._auto_br.check.checkedChanged.connect(lambda _: self._on_auto_br_change())
        # Ensure it aligns with the mode option above it (column 2)
        c2_lay.addWidget(self._auto_br, 1, 2, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._audio = LabeledOption(c2, "音频处理:", AUDIO_OPTS, default="保持原始")
        c2_lay.addWidget(self._audio, 2, 0, Qt.AlignmentFlag.AlignVCenter)

        c2.layout().addLayout(c2_lay)
        root.addWidget(c2)

        # ── Card 3: Output + action ───────────────────────────────────────────
        c3 = SectionCard(self)
        c3_lay = QVBoxLayout()
        c3_lay.setContentsMargins(16, 14, 16, 14)
        c3_lay.setSpacing(8)

        self._out_dir = OutputDirSelector(c3)
        c3_lay.addWidget(self._out_dir)

        self._progress = ProgressRow(c3)
        c3_lay.addWidget(self._progress)

        self._action_btn = ActionButton(c3, start_text="⚡  开始转换")
        self._action_btn.clicked.connect(self._on_action)
        c3_lay.addWidget(self._action_btn)

        c3.layout().addLayout(c3_lay)
        root.addWidget(c3)

        # Log
        self._log = LogBox(self)
        root.addWidget(self._log, 1)

        # Initial mode
        self._on_mode_change(self._mode.get())
        
        # Force style refresh after all UI elements are created
        QTimer.singleShot(50, self._refresh_styles)
    
    def _refresh_styles(self):
        """Force re-layout and style polish to fix initialization issues."""
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_mode_change(self, mode: str):
        if "CRF" in mode:
            self._slider_stack.setCurrentWidget(self._crf_slider)
            self._auto_br.configure(state="disabled")
        else:
            self._slider_stack.setCurrentWidget(self._br_slider)
            self._auto_br.configure(state="normal")
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
                    f"📄 {Path(self._input_path).name}  ·  原体积: {size_str}  ·  原码率: {br_mbps:.2f} Mbps"
                )

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
        fmt = self._fmt.get()
        enc = self._encoder.get().split()[0]
        mode = self._mode.get()
        audio = self._audio.get()

        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, "_conv", f".{fmt}")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        if enc == "复制原流":
            return [["ffmpeg", "-y", "-i", inp, "-c", "copy", out_path]]

        v_args = ["-c:v", enc]
        if "CRF" in mode:
            v_args += ["-crf", str(self._crf_slider.get())]
        else:
            if self._auto_br.get() and self._video_info and self._video_info.get("bitrate"):
                br = self._video_info["bitrate"]
                v_args += ["-b:v", str(br), "-maxrate:v", str(int(br * 1.2)),
                           "-bufsize:v", str(int(br * 2))]
                self._log.append(f"ℹ 已启用自动比特率匹配: {br // 1000}k")
            else:
                br_kbps = self._br_slider.get()
                v_args += ["-b:v", f"{br_kbps}k",
                           "-maxrate:v", f"{int(br_kbps * 1.2)}k",
                           "-bufsize:v", f"{int(br_kbps * 2)}k"]

        if "nvenc" not in enc and "qsv" not in enc and "amf" not in enc:
            v_args += ["-preset", "medium"]

        if audio == "移除音频":
            a_args = ["-an"]
        elif audio == "重新编码 (AAC 192k)":
            a_args = ["-c:a", "aac", "-b:a", "192k"]
        else:
            a_args = ["-c:a", "copy"]

        return [["ffmpeg", "-y", "-i", inp] + v_args + a_args + [out_path]]

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")
