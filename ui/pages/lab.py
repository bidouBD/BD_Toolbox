"""
Page: 视频实验室 (Video Lab)
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

import re
import subprocess
import threading
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    SubtitleLabel, CaptionLabel, PushButton,
    InfoBar, InfoBarPosition,
)

from core.ffmpeg_runner import FFmpegRunner, get_ffmpeg_path
from core.utils import get_video_info, generate_output_path
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, ActionButton,
)
from ui.theme import small_font


LAB_TOOLS = [
    ("cropdetect",  "✂️", "自动黑边裁切",  "自动检测视频黑边并移除（如电影画幅转全屏）"),
    ("volumenorm",  "🔊", "音量标准化",    "一键平衡视频音量，解决声音忽大忽小的问题"),
    ("autorotate",  "🔄", "画面旋转修复",  "物理级旋转像素，纠正倒置或侧翻的视频画面"),
    ("silencecut",  "🔇", "静音智能剪辑",  "自动识别并切除无声片段，提升视频紧凑度（Vlog神器）"),
]

_STYLE_TOOL_NORMAL = (
    "PushButton {"
    "  background: transparent;"
    "  border: 1px solid #D1D5DB;"
    "  border-radius: 10px;"
    "  color: #374151;"
    "}"
    "PushButton:hover { background: #E5E7EB; }"
)
_STYLE_TOOL_ACTIVE = (
    "PushButton {"
    "  background-color: #D6F5EE;"
    "  border: none;"
    "  border-radius: 10px;"
    "  color: #007A64;"
    "  font-weight: bold;"
    "}"
)


class LabPage(QWidget):
    run_done_signal = pyqtSignal(bool)
    crop_done_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LabPage")
        self.run_done_signal.connect(self._handle_run_done)
        self.crop_done_signal.connect(self._apply_crop)
        self._runner = None
        self._input_path = None
        self._current_tool = "cropdetect"
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 0, 30, 30)
        root.setSpacing(12)

        title = SubtitleLabel("🧪 视频实验室", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(20)
        root.addWidget(title)

        # Card 1: Tool selection
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(16, 14, 16, 12)
        c1_lay.setSpacing(10)

        tool_row = QHBoxLayout()
        tool_row.setSpacing(12)
        self.tool_btns: dict[str, PushButton] = {}
        for key, icon, name, desc in LAB_TOOLS:
            btn = PushButton(f"{icon} {name}", c1)
            btn.setFixedSize(170, 44)
            btn.setFont(QFont("Microsoft YaHei UI", 12))
            btn.setStyleSheet(_STYLE_TOOL_NORMAL)
            btn.clicked.connect(lambda checked=False, k=key: self._select_tool(k))
            tool_row.addWidget(btn)
            self.tool_btns[key] = btn
        tool_row.addStretch()
        c1_lay.addLayout(tool_row)

        self._tool_desc = CaptionLabel(LAB_TOOLS[0][3], c1)
        self._tool_desc.setFont(small_font())
        c1_lay.addWidget(self._tool_desc)

        c1.layout().addLayout(c1_lay)
        root.addWidget(c1)
        self._select_tool("cropdetect")

        # Card 2: File + action
        c2 = SectionCard(self)
        c2_lay = QVBoxLayout()
        c2_lay.setContentsMargins(16, 14, 16, 14)
        c2_lay.setSpacing(8)

        self._file_sel = FileSelector(
            c2, label="选择处理文件", on_change=self._on_file_selected
        )
        c2_lay.addWidget(self._file_sel)

        self._out_dir = OutputDirSelector(c2)
        c2_lay.addWidget(self._out_dir)

        self._progress = ProgressRow(c2)
        c2_lay.addWidget(self._progress)

        self._action_btn = ActionButton(c2, start_text="⚡  一键实验室处理")
        self._action_btn.clicked.connect(self._on_action)
        c2_lay.addWidget(self._action_btn)

        c2.layout().addLayout(c2_lay)
        root.addWidget(c2)

        self._log = LogBox(self)
        root.addWidget(self._log, 1)

    def _select_tool(self, key: str):
        self._current_tool = key
        for k, btn in self.tool_btns.items():
            btn.setStyleSheet(_STYLE_TOOL_ACTIVE if k == key else _STYLE_TOOL_NORMAL)
        for k, _, _, d in LAB_TOOLS:
            if k == key:
                self._tool_desc.setText(d)

    def _on_file_selected(self, path: str):
        self._input_path = path

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return
        if not self._input_path:
            InfoBar.warning("提示", "请先选择视频文件",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
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
                log_callback=self._log.append,
                progress_callback=self._progress.set,
                done_callback=self._on_done,
            )
            if info:
                self._runner.set_duration(info["duration"])
            self._runner.run(cmd)

    def _build_tool_command(self):
        inp = self._input_path
        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, f"_{self._current_tool}", Path(inp).suffix)
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        if self._current_tool == "volumenorm":
            return ["ffmpeg", "-y", "-i", inp, "-af", "loudnorm", "-c:v", "copy", out_path]
        elif self._current_tool == "autorotate":
            return ["ffmpeg", "-y", "-i", inp, "-vf", "transpose=1",
                    "-metadata:s:v:0", "rotate=0", out_path]
        elif self._current_tool == "silencecut":
            return ["ffmpeg", "-y", "-i", inp,
                    "-af", "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-30dB",
                    out_path]
        return None

    def _handle_cropdetect(self):
        self._log.append("🔍 正在检测黑边，请稍候...")
        cmd = [
            get_ffmpeg_path(), "-ss", "00:00:10", "-i", self._input_path,
            "-vframes", "100", "-vf", "cropdetect", "-f", "null", "-",
        ]

        def run_detect():
            p = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                universal_newlines=True, encoding="utf-8",
            )
            detected = None
            for line in p.stderr:
                if "crop=" in line:
                    m = re.search(r"crop=([0-9:]+)", line)
                    if m:
                        detected = m.group(1)
            p.wait()
            self.crop_done_signal.emit(detected)

        threading.Thread(target=run_detect, daemon=True).start()

    def _apply_crop(self, crop_val: str | None):
        if not crop_val:
            self._log.append("❌ 未检测到明显黑边。")
            self._action_btn.set_running(False)
            return

        self._log.append(f"✅ 检测到裁剪区域: {crop_val}")
        out_path = generate_output_path(
            self._input_path, "_cropped", Path(self._input_path).suffix
        )
        if self._out_dir.get():
            out_path = str(Path(self._out_dir.get()) / Path(out_path).name)

        final_cmd = ["ffmpeg", "-y", "-i", self._input_path,
                     "-vf", f"crop={crop_val}", out_path]
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        self._runner.run(final_cmd)

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")
