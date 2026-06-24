"""
Page: 音频提取/转换
PyQt6 + qfluentwidgets rewrite — logic identical to original.
"""

from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    SubtitleLabel, CaptionLabel, InfoBar, InfoBarPosition,
)

from core.ffmpeg_runner import FFmpegRunner
from core.utils import get_video_info, generate_output_path, human_size
from ui.widgets import (
    SectionCard, FileSelector, OutputDirSelector,
    LogBox, ProgressRow, LabeledOption, ActionButton,
)
from ui.theme import small_font


AUDIO_FORMATS  = ["mp3", "aac", "flac", "wav", "ogg", "m4a", "opus", "wma"]
BITRATES_LOSSY = ["64k", "96k", "128k", "160k", "192k (推荐)", "256k", "320k (最高质量)"]
SAMPLE_RATES   = ["保持原始", "44100 Hz", "48000 Hz", "22050 Hz", "16000 Hz"]
CHANNELS       = ["保持原始", "立体声 (2ch)", "单声道 (1ch)"]


class AudioPage(QWidget):
    run_done_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AudioPage")
        self.run_done_signal.connect(self._handle_run_done)
        self._runner = None
        self._input_path = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 20)
        root.setSpacing(10)

        title = SubtitleLabel("🎵 音频提取/转换", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(12)
        root.addWidget(title)

        # Card 1: File
        c1 = SectionCard(self)
        c1_lay = QVBoxLayout()
        c1_lay.setContentsMargins(10, 10, 10, 10)
        c1_lay.setSpacing(12)

        self._file_sel = FileSelector(
            c1, label="选择视频源文件 (支持批量拖拽)",
            filetypes=[
                ("视频文件", "*.mp4 *.mkv *.avi *.mov *.flv *.webm *.wmv *.ts *.m4v"),
                ("所有文件", "*.*"),
            ],
            on_change=self._on_file_selected,
        )
        self._file_sel.btn.setMinimumWidth(240)
        c1_lay.addWidget(self._file_sel)

        self._file_info = CaptionLabel("", c1)
        self._file_info.setFont(small_font())
        self._file_info.setStyleSheet("color: #8C8C8C;")
        c1_lay.addWidget(self._file_info)
        c1.layout().addLayout(c1_lay)
        root.addWidget(c1)

        # Card 2: Options
        c2 = SectionCard(self)
        g = QGridLayout()
        g.setContentsMargins(16, 14, 16, 14)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        self._fmt = LabeledOption(c2, "输出格式:", AUDIO_FORMATS, default="mp3", width=140)
        self._fmt.menu.currentTextChanged.connect(self._on_format_change)
        g.addWidget(self._fmt, 0, 0)

        self._bitrate = LabeledOption(c2, "音频码率:", BITRATES_LOSSY,
                                      default="192k (推荐)", width=180)
        g.addWidget(self._bitrate, 0, 1)

        self._sample = LabeledOption(c2, "采样率:", SAMPLE_RATES,
                                     default="保持原始", width=160)
        g.addWidget(self._sample, 0, 2)

        self._channels = LabeledOption(c2, "声道:", CHANNELS,
                                       default="保持原始", width=168)
        g.addWidget(self._channels, 1, 0)

        self._hint_lbl = CaptionLabel("", c2)
        self._hint_lbl.setFont(small_font())
        self._hint_lbl.setStyleSheet("color: #059669;")
        g.addWidget(self._hint_lbl, 1, 1, 1, 2)

        c2.layout().addLayout(g)
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

        self._action_btn = ActionButton(c3, start_text="⚡  提取音频")
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
        dur_str = ""
        if info:
            dur = info["duration"]
            h = int(dur // 3600); m = int((dur % 3600) // 60); s = int(dur % 60)
            dur_str = f"  ·  时长 {h:02d}:{m:02d}:{s:02d}"
        self._file_info.setText(f"📄 {Path(path).name}  ·  {size}{dur_str}")

    def _on_format_change(self, fmt: str):
        lossless = fmt in ("flac", "wav")
        if lossless:
            self._hint_lbl.setText("✨ 无损格式：码率选项将被忽略")
            self._bitrate.configure(state="disabled")
        else:
            self._hint_lbl.setText("")
            self._bitrate.configure(state="normal")

    def _on_action(self):
        if self._runner and self._runner.running:
            self._runner.stop()
            self._action_btn.set_running(False)
            return
        if not self._input_path:
            InfoBar.warning("提示", "请先选择输入文件！",
                            duration=3000, parent=self,
                            position=InfoBarPosition.TOP)
            return

        cmd = self._build_command()
        if not cmd:
            return

        self._log.clear()
        self._progress.reset()
        self._action_btn.set_running(True)

        info = get_video_info(self._input_path)
        self._runner = FFmpegRunner(
            log_callback=self._log.append,
            progress_callback=self._progress.set,
            done_callback=self._on_done,
        )
        if info:
            self._runner.set_duration(info["duration"])
        self._runner.run(cmd)

    def _build_command(self):
        inp = self._input_path
        fmt = self._fmt.get()
        bitrate_raw = self._bitrate.get().split()[0]
        sample = self._sample.get()
        ch = self._channels.get()
        lossless = fmt in ("flac", "wav")

        out_dir = self._out_dir.get()
        out_path = generate_output_path(inp, "_audio", f".{fmt}")
        if out_dir:
            out_path = str(Path(out_dir) / Path(out_path).name)

        cmd = ["ffmpeg", "-y", "-i", inp, "-vn"]

        if fmt == "mp3":
            cmd += ["-c:a", "libmp3lame"]
        elif fmt in ("aac", "m4a"):
            cmd += ["-c:a", "aac"]
        elif fmt == "ogg":
            cmd += ["-c:a", "libvorbis"]
        elif fmt == "opus":
            cmd += ["-c:a", "libopus"]
        elif fmt == "flac":
            cmd += ["-c:a", "flac"]
        elif fmt == "wav":
            cmd += ["-c:a", "pcm_s16le"]
        else:
            cmd += ["-c:a", "copy"]

        if not lossless:
            cmd += ["-b:a", bitrate_raw]

        if sample != "保持原始":
            cmd += ["-ar", sample.split()[0]]

        if ch == "立体声 (2ch)":
            cmd += ["-ac", "2"]
        elif ch == "单声道 (1ch)":
            cmd += ["-ac", "1"]

        cmd.append(out_path)
        return cmd

    def _on_done(self, success: bool):
        self.run_done_signal.emit(success)

    def _handle_run_done(self, success: bool):
        self._action_btn.set_running(False)
        if success:
            self._progress.set(1.0)
        else:
            self._log.append("\n❌ 处理被中断或发生错误！")
