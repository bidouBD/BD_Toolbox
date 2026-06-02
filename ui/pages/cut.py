"""
Page: 视频裁切
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    SubtitleLabel, CaptionLabel, BodyLabel, LineEdit,
    PushButton, InfoBar, InfoBarPosition,
)

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size, format_time, parse_time
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
)
from ui.theme import body_font, small_font, mono_font


CUT_MODES = [
    "快速模式（流复制，速度快，可能有误差）",
    "精确模式（重新编码，精确到帧）",
]


class CutPage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CutPage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._input_path = None
        self._duration = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 20)
        root.setSpacing(10)

        title = SubtitleLabel("🕒 视频裁切", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(12)
        root.addWidget(title)

        # Card 1: File
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(10, 10, 10, 10)
        c1_lay.setSpacing(6)

        self._file_sel = FileSelector(
            c1, label="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.mkv *.avi *.mov *.flv *.webm *.wmv *.ts *.m4v"),
                ("所有文件", "*.*"),
            ],
            on_change=self._on_file_selected,
        )
        c1_lay.addWidget(self._file_sel)

        self._file_info = CaptionLabel("", c1)
        self._file_info.setFont(small_font())
        c1_lay.addWidget(self._file_info)
        c1.layout().addLayout(c1_lay)
        root.addWidget(c1)

        # Card 2: Time options
        c2 = SectionCard(self)
        c2_lay = QVBoxLayout()
        c2_lay.setContentsMargins(16, 14, 16, 14)
        c2_lay.setSpacing(10)

        # Start / End time row
        time_row = QHBoxLayout()
        time_row.setSpacing(16)

        start_lbl = BodyLabel("开始时间:", c2)
        start_lbl.setFont(body_font())
        time_row.addWidget(start_lbl)

        self._start_entry = LineEdit(c2)
        self._start_entry.setPlaceholderText("00:00:00")
        self._start_entry.setFixedSize(120, 36)
        self._start_entry.setFont(mono_font())
        time_row.addWidget(self._start_entry)

        time_row.addSpacing(20)

        end_lbl = BodyLabel("结束时间:", c2)
        end_lbl.setFont(body_font())
        time_row.addWidget(end_lbl)

        self._end_entry = LineEdit(c2)
        self._end_entry.setPlaceholderText("00:00:00")
        self._end_entry.setFixedSize(120, 36)
        self._end_entry.setFont(mono_font())
        time_row.addWidget(self._end_entry)
        time_row.addStretch()
        c2_lay.addLayout(time_row)

        # Hint + fill button row
        hint_row = QHBoxLayout()
        hint_row.setSpacing(16)

        self._dur_hint = CaptionLabel("ℹ 选择文件后显示时长", c2)
        self._dur_hint.setFont(small_font())
        hint_row.addWidget(self._dur_hint)

        self._fill_end_btn = PushButton("填入视频总时长", c2)
        self._fill_end_btn.setFixedSize(130, 30)
        self._fill_end_btn.setFont(small_font())
        self._fill_end_btn.clicked.connect(self._fill_end)
        hint_row.addWidget(self._fill_end_btn)
        hint_row.addStretch()
        c2_lay.addLayout(hint_row)

        # Mode
        self._mode = LabeledOption(
            c2, "裁切模式:", CUT_MODES,
            default="快速模式（流复制，速度快，可能有误差）", width=360,
        )
        c2_lay.addWidget(self._mode)

        c2.layout().addLayout(c2_lay)
        root.addWidget(c2)

        # Card 3: Output + action
        c3 = SectionCard(self)
        c3_lay = QVBoxLayout()
        c3_lay.setContentsMargins(16, 14, 16, 14)
        c3_lay.setSpacing(8)

        self._out_dir = OutputDirSelector(c3)
        c3_lay.addWidget(self._out_dir)

        self._progress = ProgressRow(c3)
        c3_lay.addWidget(self._progress)

        self._action_btn = ActionButton(c3, start_text="⚡  开始裁切")
        self._action_btn.clicked.connect(self._on_action)
        c3_lay.addWidget(self._action_btn)

        c3.layout().addLayout(c3_lay)
        root.addWidget(c3)

        self._log = LogBox(self)
        root.addWidget(self._log, 1)

    def _on_file_selected(self, path: str):
        self._input_path = path
        size = human_size(path)
        info = get_video_info(path)
        if info:
            dur = info["duration"]
            self._duration = dur
            h = int(dur // 3600); m = int((dur % 3600) // 60); s = int(dur % 60)
            dur_str = f"{h:02d}:{m:02d}:{s:02d}"
            self._dur_hint.setText(f"⏱ 视频总时长: {dur_str}")
            self._dur_hint.setStyleSheet("color: #059669;")
            self._file_info.setText(
                f"📄 {Path(path).name}  ·  {size}  ·  时长 {dur_str}"
            )
        else:
            self._dur_hint.setText("ℹ 无法读取时长，请手动输入")
            self._dur_hint.setStyleSheet("")
            self._file_info.setText(f"📄 {Path(path).name}  ·  {size}")

    def _fill_end(self):
        if self._duration:
            self._end_entry.setText(format_time(self._duration))

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return
        if not self._input_path:
            InfoBar.warning("提示", "请先选择视频文件！",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        start_str = self._start_entry.text().strip() or "00:00:00"
        end_str = self._end_entry.text().strip()
        if not end_str:
            InfoBar.warning("提示", "请输入结束时间！",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        try:
            start_sec = parse_time(start_str)
            end_sec = parse_time(end_str)
        except Exception:
            InfoBar.error("错误", "时间格式错误，请使用 HH:MM:SS 格式",
                          duration=3000, parent=self,
                          position=InfoBarPosition.TOP)
            return

        if end_sec <= start_sec:
            InfoBar.error("错误", "结束时间必须大于开始时间！",
                          duration=3000, parent=self,
                          position=InfoBarPosition.TOP)
            return

        cmd = self._build_command(start_str, end_str)
        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)

        clip_dur = end_sec - start_sec
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        self._runner.set_duration(clip_dur)
        self._runner.run(cmd)

    def _build_command(self, start_str: str, end_str: str):
        inp = self._input_path
        mode = self._mode.get()
        fast = "快速模式" in mode

        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, "_cut", Path(inp).suffix)
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        if fast:
            cmd = ["ffmpeg", "-y", "-ss", start_str, "-to", end_str,
                   "-i", inp, "-c", "copy", out_path]
        else:
            cmd = ["ffmpeg", "-y", "-i", inp,
                   "-ss", start_str, "-to", end_str,
                   "-c:v", "libx264", "-c:a", "aac",
                   "-avoid_negative_ts", "1", out_path]
        return cmd

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")
