"""
Page: 导出 GIF
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import SubtitleLabel, InfoBar, InfoBarPosition

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
)


class GifPage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GifPage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._input_path = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 20)
        root.setSpacing(10)

        title = SubtitleLabel("🖼️ 导出 GIF", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(12)
        root.addWidget(title)

        # Card 1: File + options
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(10, 10, 10, 10)
        c1_lay.setSpacing(10)

        self._file_sel = FileSelector(
            c1, label="选择视频源", on_change=self._on_file_selected
        )
        c1_lay.addWidget(self._file_sel)

        opt_row = QHBoxLayout()
        opt_row.setSpacing(20)
        self._gif_width = LabeledOption(
            c1, "宽度:", ["320", "480", "640", "800"], default="480", width=100
        )
        opt_row.addWidget(self._gif_width)

        self._gif_fps = LabeledOption(
            c1, "帧率:", ["5", "10", "15", "20", "24"], default="15", width=100
        )
        opt_row.addWidget(self._gif_fps)
        opt_row.addStretch()
        c1_lay.addLayout(opt_row)

        c1.layout().addLayout(c1_lay)
        root.addWidget(c1)

        # Card 2: Output + action
        c2 = SectionCard(self)
        c2_lay = QVBoxLayout()
        c2_lay.setContentsMargins(16, 14, 16, 14)
        c2_lay.setSpacing(8)

        self._out_dir = OutputDirSelector(c2)
        c2_lay.addWidget(self._out_dir)

        self._progress = ProgressRow(c2)
        c2_lay.addWidget(self._progress)

        self._action_btn = ActionButton(c2, start_text="⚡  开始导出 GIF")
        self._action_btn.clicked.connect(self._on_action)
        c2_lay.addWidget(self._action_btn)

        c2.layout().addLayout(c2_lay)
        root.addWidget(c2)

        self._log = LogBox(self)
        root.addWidget(self._log, 1)

    def _on_file_selected(self, path: str):
        self._input_path = path

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return
        if not self._input_path:
            InfoBar.warning("提示", "请选择视频源！",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        w = self._gif_width.get()
        fps = self._gif_fps.get()
        out_dir = self._out_dir.get()
        out_path = generate_output_path(self._input_path, "_out", ".gif")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        info = get_video_info(self._input_path)
        filters = (
            f"fps={fps},scale={w}:-1:flags=lanczos,"
            "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        )
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
            self._runner.set_duration(info["duration"])
        self._runner.run(cmd)

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")
