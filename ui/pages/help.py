"""
Help documentation page for BD Toolbox.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

from qfluentwidgets import SubtitleLabel, isDarkTheme


HELP_HTML = """
<h1>BD Toolbox 帮助文档</h1>
<p class="lead">
这份文档面向第一次接触 FFmpeg 参数的新用户，也给想学习实现逻辑的高级用户提供代码阅读线索。
如果你只想快速完成视频处理，优先阅读“快速上手”和对应功能页的参数说明；如果你想理解程序如何生成命令，再看“命令行映射”和“实现代码入口”。
</p>

<h2>1. 快速上手</h2>
<ol>
  <li><b>选择功能页：</b>格式转换、视频压缩、音频提取、裁切、合并、GIF、字幕或实验室。</li>
  <li><b>选择输入文件：</b>可批量的页面会提示“支持批量处理”，程序会按顺序为每个文件生成 FFmpeg 命令。</li>
  <li><b>设置参数：</b>不确定时保留默认值。默认值通常偏向兼容性和稳定质量。</li>
  <li><b>选择输出目录：</b>不选时默认输出到源文件所在目录，并在文件名后加上功能后缀。</li>
  <li><b>点击开始：</b>日志区会显示执行过程，进度条根据视频时长估算处理进度。</li>
</ol>

<h2>2. FFmpeg 命令的基本结构</h2>
<pre>ffmpeg [全局参数] {[输入文件参数] -i 输入文件地址}... {[输出文件参数] 输出文件地址}...</pre>
<ul>
  <li><code>-y</code>：全局参数，输出文件已存在时直接覆盖。</li>
  <li><code>-i input.mp4</code>：指定输入文件。多个输入就写多个 <code>-i</code>。</li>
  <li><code>-c:v</code>：视频编码器，例如 <code>libx264</code>、<code>libx265</code>、<code>h264_nvenc</code>。</li>
  <li><code>-c:a</code>：音频编码器，例如 <code>aac</code>、<code>libmp3lame</code>。</li>
  <li><code>-c copy</code>：直接复制音视频流，不重新编码，速度最快且不损画质，但格式兼容性受源文件限制。</li>
  <li><code>-vf</code> / <code>-af</code>：视频滤镜 / 音频滤镜，例如缩放、裁切、音量标准化。</li>
</ul>
<p>示例：把 MP4 转成 AVI，同时指定码率和编码器。</p>
<pre>ffmpeg -i input.mp4 -b:v 500k -c:v libx264 output.avi</pre>

<h2>3. 视频转换页参数</h2>
<table>
  <tr><th>GUI 参数</th><th>对应命令</th><th>新人怎么选</th><th>进阶说明</th></tr>
  <tr><td>输出格式</td><td>输出文件后缀</td><td>日常分享选 MP4；网页透明动图可选 WebM/GIF。</td><td>封装格式决定容器，不等同于编码格式。</td></tr>
  <tr><td>核心编码器</td><td><code>-c:v</code></td><td>兼容优先选 libx264；体积优先选 libx265；有显卡可尝试 nvenc/qsv/amf。</td><td>硬件编码速度快，但同码率画质通常不如软件编码细腻。</td></tr>
  <tr><td>编码模式：CRF</td><td><code>-crf</code></td><td>H.264 常用 18-23；数值越小画质越高、文件越大。</td><td>CRF 是恒定质量模式，适合不强制文件大小的场景。</td></tr>
  <tr><td>编码模式：VBR/ABR</td><td><code>-b:v</code>、<code>-maxrate:v</code>、<code>-bufsize:v</code></td><td>想控制体积或平台要求码率时使用。</td><td>程序会用目标码率、峰值码率和缓冲区约束码率波动。</td></tr>
  <tr><td>匹配原始码率</td><td>读取 ffprobe 码率后生成码率参数</td><td>不懂码率但想接近原视频质量时开启。</td><td>并不代表无损，只是用源文件码率作为目标参考。</td></tr>
  <tr><td>音频处理</td><td><code>-c:a copy</code>、<code>-c:a aac -b:a 192k</code>、<code>-an</code></td><td>保留原始最省事；兼容性问题时选 AAC；不需要声音选移除。</td><td><code>copy</code> 不重编码，速度快但目标容器必须支持源音频格式。</td></tr>
</table>

<h2>4. 视频压缩页参数</h2>
<table>
  <tr><th>GUI 参数</th><th>对应命令</th><th>新人怎么选</th><th>进阶说明</th></tr>
  <tr><td>一键比例</td><td>按源码率比例计算 <code>-b:v</code></td><td>推荐先试 1/2；仍太大再选 1/3 或 1/4。</td><td>复杂画面、运动画面需要更高码率，比例越低越容易糊。</td></tr>
  <tr><td>编码器</td><td><code>-c:v</code></td><td>追求兼容选 H.264；追求体积选 H.265。</td><td>H.265 相同观感下通常更小，但旧设备和剪辑软件可能不支持。</td></tr>
  <tr><td>CRF</td><td><code>-crf</code></td><td>H.264 选 20-23；H.265 选 24-28 可作为起点。</td><td>CRF 越低越清晰，0 接近无损，51 极低质量。</td></tr>
  <tr><td>手动码率</td><td><code>-b:v</code></td><td>720p 可从 1500k-3000k 试起，1080p 可从 4000k-8000k 试起。</td><td>最终体积约等于码率乘时长，页面会显示估算值。</td></tr>
  <tr><td>2-Pass 增强</td><td><code>-pass 1</code> / <code>-pass 2</code></td><td>文件大小要求严格时开启，普通压缩不用开。</td><td>两遍编码更接近目标码率，但耗时接近翻倍。</td></tr>
  <tr><td>分辨率缩放</td><td><code>-vf scale=...</code></td><td>手机分享可选 720p；大屏观看保留原始或 1080p。</td><td><code>-2</code> 会自动计算偶数尺寸，避免编码器报错。</td></tr>
  <tr><td>编码预设</td><td><code>-preset</code></td><td>默认 medium；赶时间选 veryfast；追求压缩效率选 slow。</td><td>越慢通常同体积画质越好，但收益递减。</td></tr>
  <tr><td>目标帧率</td><td><code>-r</code></td><td>不确定就保持原始。</td><td>强改帧率可能造成卡顿或音画不同步。</td></tr>
</table>

<h2>5. 音频、裁切、合并与字幕</h2>
<ul>
  <li><b>音频提取：</b><code>-vn</code> 表示不要视频流，只输出音频。MP3 使用 <code>libmp3lame</code>，AAC 使用 <code>aac</code>，无损可选 FLAC/WAV。</li>
  <li><b>音频码率：</b>128k 适合语音，192k 适合多数音乐和视频，320k 文件更大但保留更多细节。</li>
  <li><b>采样率：</b>保持原始最稳。常见值有 44100 Hz 和 48000 Hz。</li>
  <li><b>声道：</b>立体声是 2 声道，单声道是 1 声道。语音素材可转单声道减小体积。</li>
  <li><b>视频裁切：</b>快速模式用 <code>-c copy</code>，速度快但可能只能切到关键帧；精确模式会重新编码，时间点更准。</li>
  <li><b>视频合并：</b>通常使用 concat 列表。要无损合并，多个视频的编码、分辨率、帧率、音频参数最好一致。</li>
  <li><b>字幕烧录：</b>“烧录”会把字幕画进视频画面，兼容性好，但导出后不能关闭字幕。</li>
</ul>

<h2>6. 实验室功能</h2>
<table>
  <tr><th>功能</th><th>核心命令/滤镜</th><th>用途</th></tr>
  <tr><td>自动黑边裁切</td><td><code>cropdetect</code> + <code>crop</code></td><td>先检测黑边区域，再按检测值裁掉黑边。</td></tr>
  <tr><td>音量标准化</td><td><code>-af loudnorm</code></td><td>让视频音量更接近统一响度，适合忽大忽小的素材。</td></tr>
  <tr><td>画面旋转修复</td><td><code>-vf transpose=1</code></td><td>把错误方向的视频真正旋转像素，并清理旋转元数据。</td></tr>
  <tr><td>静音智能剪辑</td><td><code>silenceremove</code></td><td>按阈值移除静音片段，适合语音、录屏、Vlog 粗剪。</td></tr>
</table>

<h2>7. 常用 FFmpeg 案例</h2>
<pre>格式转换：ffmpeg -i video.qsv -c:v libx264 -c:a aac -crf 23 output.mp4
快速剪辑：ffmpeg -i source.mp4 -ss 00:00:10 -to 00:00:30 -c copy clip.mp4
提取音频：ffmpeg -i input.mp4 -vn -c:a libmp3lame output.mp3
调整音量：ffmpeg -i audio.mp3 -af "volume=1.5" louder.mp3
缩放分辨率：ffmpeg -i input.mp4 -vf "scale=1280:720" output.mp4
裁剪画面：ffmpeg -i source.mp4 -vf "crop=320:240:0:0" cropped.mp4
压缩 720p：ffmpeg -i input.mp4 -vf "scale=1280:720" -preset slow -crf 20 output.mp4
直播推流：ffmpeg -re -i input.mp4 -c:v libx264 -c:a aac -f flv rtmp://server/live/stream</pre>

<h2>8. 常见错误与排查</h2>
<ul>
  <li><b>ffmpeg command not found：</b>FFmpeg 没安装或没有配置到 Path。检查 FFmpeg 的 <code>bin</code> 目录是否在环境变量中。</li>
  <li><b>Error while opening encoder：</b>指定编码器不可用，例如选择 <code>libx265</code> 但当前 FFmpeg 没编译 x265 支持。换编码器或安装完整版本 FFmpeg。</li>
  <li><b>Invalid argument：</b>参数、路径或引号可能有误。路径含空格时必须正确加引号，参数名也要逐字核对。</li>
  <li><b>播放异常或画质很差：</b>码率过低、CRF 数值过高、目标格式不支持当前编码都可能导致问题。</li>
  <li><b>剪辑后音画不同步：</b>优先尝试精确模式，或保持源视频帧率，不要强行修改 <code>-r</code>。</li>
</ul>

"""


class HelpPage(QWidget):
    """Scrollable in-app help document."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpPage")
        self._build()
        self._apply_theme()
        try:
            from qfluentwidgets import qconfig
            qconfig.themeChanged.connect(lambda _: self._apply_theme())
        except Exception:
            pass

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 0, 30, 30)
        root.setSpacing(12)

        title = SubtitleLabel("帮助文档", self)
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        root.addSpacing(20)
        root.addWidget(title)

        self._doc = QTextBrowser(self)
        self._doc.setOpenExternalLinks(False)
        self._doc.setHtml(HELP_HTML)
        self._doc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root.addWidget(self._doc, 1)

    def _apply_theme(self):
        if isDarkTheme():
            bg = "#151E2B"
            panel = "#1F2937"
            text = "#E5E7EB"
            muted = "#A7B0BE"
            border = "#374151"
            code_bg = "#111827"
            accent = "#00C9A7"
        else:
            bg = "#F6F8FB"
            panel = "#FFFFFF"
            text = "#1C1F2E"
            muted = "#5B6472"
            border = "#E2E5EE"
            code_bg = "#F3F6FA"
            accent = "#00B894"

        self._doc.setStyleSheet(f"""
            QTextBrowser {{
                background: {panel};
                color: {text};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 18px 22px;
                font-family: "Microsoft YaHei UI";
                font-size: 14px;
                selection-background-color: {accent};
            }}
            QTextBrowser QScrollBar:vertical {{
                background: {bg};
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }}
            QTextBrowser QScrollBar::handle:vertical {{
                background: {border};
                min-height: 36px;
                border-radius: 5px;
            }}
        """)
        self._doc.document().setDefaultStyleSheet(f"""
            body {{
                color: {text};
                font-family: "Microsoft YaHei UI";
                line-height: 1.55;
            }}
            h1 {{
                color: {text};
                font-size: 24px;
                margin: 0 0 10px 0;
            }}
            h2 {{
                color: {text};
                font-size: 18px;
                margin: 24px 0 10px 0;
                padding-left: 10px;
                border-left: 4px solid {accent};
            }}
            p, li {{
                color: {text};
                font-size: 14px;
            }}
            .lead {{
                color: {muted};
                font-size: 14px;
            }}
            code {{
                background: {code_bg};
                color: {accent};
                padding: 2px 5px;
                border-radius: 4px;
                font-family: Consolas, "Microsoft YaHei UI";
            }}
            pre {{
                background: {code_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 12px;
                white-space: pre-wrap;
                font-family: Consolas, "Microsoft YaHei UI";
                font-size: 13px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 8px;
            }}
            th {{
                background: {code_bg};
                color: {text};
                font-weight: 600;
            }}
            th, td {{
                border: 1px solid {border};
                padding: 8px;
                vertical-align: top;
                color: {text};
            }}
        """)
        self._doc.setHtml(HELP_HTML)
