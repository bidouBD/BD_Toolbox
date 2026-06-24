"""
Page: 烧录字幕
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

import os
import shutil
import tempfile

from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import SubtitleLabel, InfoBar, InfoBarPosition

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, ActionButton,
)


class SubtitlesPage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SubtitlesPage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._video_path = None
        self._subtitle_path = None
        self._temp_subtitle = None  # tracks any ASCII-safe temp copy
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 20)
        root.setSpacing(10)

        title = SubtitleLabel("💬 烧录字幕", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(12)
        root.addWidget(title)

        # Card 1: Files
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(10, 10, 10, 10)
        c1_lay.setSpacing(10)

        self._v_sel = FileSelector(
            c1, label="选择视频文件",
            on_change=lambda p: setattr(self, "_video_path", p),
        )
        c1_lay.addWidget(self._v_sel)

        self._s_sel = FileSelector(
            c1, label="选择字幕文件 (.srt/.ass)",
            filetypes=[("字幕文件", "*.srt *.ass"), ("所有文件", "*.*")],
            on_change=lambda p: setattr(self, "_subtitle_path", p),
        )
        c1_lay.addWidget(self._s_sel)
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

        self._action_btn = ActionButton(c2, start_text="⚡  开始烧录字幕")
        self._action_btn.clicked.connect(self._on_action)
        c2_lay.addWidget(self._action_btn)

        c2.layout().addLayout(c2_lay)
        root.addWidget(c2)

        self._log = LogBox(self)
        root.addWidget(self._log, 1)

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return
        if not self._video_path or not self._subtitle_path:
            InfoBar.warning("提示", "请选择视频和字幕文件！",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        out_dir = self._out_dir.get()
        out_path = generate_output_path(self._video_path, "_with_subs")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        info = get_video_info(self._video_path)

        srt_filter_path = _prepare_subtitle_path(self._subtitle_path)
        srt_p = _escape_subtitle_filter_path(srt_filter_path)
        cmd = ["ffmpeg", "-y", "-i", self._video_path,
               "-vf", f"subtitles='{srt_p}'", "-c:a", "copy", out_path]

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


def _prepare_subtitle_path(path: str) -> str:
    """On Windows, copy the subtitle to a pure-ASCII temp path to work around
    FFmpeg's inability to handle multibyte characters in the subtitles filter.
    Returns the original path unchanged on non-Windows platforms."""
    if os.name != "nt":
        return path
    # Check whether the path is already pure ASCII
    try:
        path.encode("ascii")
        return path  # no non-ASCII characters — safe to use directly
    except UnicodeEncodeError:
        pass
    # Copy to a temp file with an ASCII-safe name
    suffix = Path(path).suffix  # e.g. '.srt'
    tmp = tempfile.NamedTemporaryFile(
        suffix=suffix, prefix="bdtoolbox_sub_", delete=False
    )
    tmp.close()
    shutil.copy2(path, tmp.name)
    return tmp.name


def _escape_subtitle_filter_path(path) -> str:
    """Escape paths embedded inside FFmpeg's subtitles filter argument."""
    return (
        str(path)
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )
