"""
Page: 视频合并
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import SubtitleLabel, CaptionLabel, InfoBar, InfoBarPosition

from core.ffmpeg_runner import FFmpegRunner
from core.utils import generate_output_path
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, ActionButton,
)
from ui.theme import small_font


class MergePage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MergePage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 20)
        root.setSpacing(10)

        title = SubtitleLabel("🧩 视频合并", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(12)
        root.addWidget(title)

        # Card 1: Files
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(10, 10, 10, 10)
        c1_lay.setSpacing(6)

        self._file_sel = FileSelector(
            c1, label="选择多个视频文件",
            multiple=True,
            on_change=self._on_files_selected,
        )
        c1_lay.addWidget(self._file_sel)

        self._info_lbl = CaptionLabel(
            "请确保所有合并文件的分辨率和格式一致，以获得最佳效果。", c1
        )
        self._info_lbl.setFont(small_font())
        c1_lay.addWidget(self._info_lbl)
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

        self._action_btn = ActionButton(c2, start_text="⚡  开始合并")
        self._action_btn.clicked.connect(self._on_action)
        c2_lay.addWidget(self._action_btn)

        c2.layout().addLayout(c2_lay)
        root.addWidget(c2)

        self._log = LogBox(self)
        root.addWidget(self._log, 1)

    def _on_files_selected(self, paths):
        self._info_lbl.setText(f"已选择 {len(paths)} 个文件待合并")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return

        paths = self._file_sel.get()
        if not paths or len(paths) < 2:
            InfoBar.warning("提示", "请选择至少两个文件！",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        list_file = Path(tempfile.gettempdir()) / "ffmpeg_merge_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in paths:
                res_p = str(p).replace("\\", "/")
                f.write(f"file '{res_p}'\n")

        out_dir = self._out_dir.get()
        out_path = generate_output_path(paths[0], "_merged")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", str(list_file), "-c", "copy", out_path]

        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        self._runner.run(cmd)

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")
