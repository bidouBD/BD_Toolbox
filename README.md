# BD Toolbox

BD Toolbox 是一款基于 Python、PyQt6 与 PyQt-Fluent-Widgets 构建的现代化 FFmpeg 图形工具箱。项目通过清晰的桌面 GUI 封装常用 FFmpeg/ffprobe 工作流，帮助用户更直观地完成视频转换、压缩、裁切、合并、音频处理、字幕处理与实验性修复任务。

本次更新重点完成了 UI 框架重构：项目已由此前的 Tkinter/ttk 风格实现迁移到 PyQt6 体系，并使用 qfluentwidgets 构建更稳定、更现代的 Fluent 风格界面。

---

## 核心功能

### 视频转换

- 支持 MP4、MKV、AVI、MOV、FLV、WebM、WMV、TS、M4V、GIF 等常见输出格式。
- 支持 libx264、libx265、NVIDIA NVENC、Intel QSV、AMD AMF 等编码器选项。
- 支持 CRF 画质模式与 VBR/ABR 目标码率模式。
- 支持批量选择源文件并连续处理。

### 视频压缩

- 提供 3/4、1/2、1/3、1/4 等比例压缩预设。
- 支持手动码率、CRF、2-Pass、分辨率缩放、帧率调整和音频处理。
- 自动读取视频时长、码率和体积，用于估算压缩后文件大小。

### 音频与字幕

- 支持从视频中提取音频。
- 支持常见音频转码处理。
- 支持字幕烧录与字幕流提取相关工作流。

### 剪辑、合并与 GIF

- 支持视频裁切，可选择快速模式或精确模式。
- 支持多视频合并。
- 支持将视频片段导出为 GIF。

### Video Lab

- 集成自动裁黑边、音量标准化、旋转修复、静音检测等进阶 FFmpeg 实验功能。

---

## 本次 UI 重构更新

- UI 框架从 Tkinter/ttk 迁移到 PyQt6。
- 引入 PyQt-Fluent-Widgets，重构主窗口、导航栏、页面布局和控件风格。
- 使用 `FluentWindow` 管理侧边导航，功能页拆分为转换、压缩、音频、裁切、合并、GIF、字幕、实验室等模块。
- 新增浅色/深色主题切换，并优化主题切换时的控件刷新和布局稳定性。
- 重构通用控件，包括文件选择器、输出目录选择器、日志框、进度条、参数滑块、选项下拉框和操作按钮。
- 优化批量处理体验，转换与压缩页面支持多文件选择和顺序执行。
- 调整打包依赖，项目依赖更新为 PyQt6、PyQt6-Fluent-Widgets、PyQt6-Frameless-Window 与 darkdetect。

---

## 技术栈

- 核心处理：FFmpeg / ffprobe
- GUI 框架：PyQt6
- Fluent UI：PyQt6-Fluent-Widgets
- 窗口增强：PyQt6-Frameless-Window
- 主题检测：darkdetect
- 打包工具：PyInstaller

---

## 项目结构

```text
BD_Toolbox/
├── core/                 # FFmpeg 执行、工具函数与路径解析
├── ui/
│   ├── pages/            # 各功能页
│   ├── theme.py          # 字体与主题配置
│   └── widgets.py        # 通用 PyQt 控件
├── bin/                  # 本地 FFmpeg/ffprobe 放置目录，不随源码仓库提交
├── main.py               # 程序入口
├── build_app.py          # PyInstaller 打包入口
├── build.spec            # 打包配置
├── requirements.txt      # Python 依赖
└── README.md
```

---

## 安装与运行

### 1. 准备环境

建议使用 Python 3.10 或更高版本。

```bash
pip install -r requirements.txt
```

### 2. 准备 FFmpeg

将 `ffmpeg.exe` 和 `ffprobe.exe` 放入项目根目录下的 `bin/` 文件夹，或确保它们已经加入系统 `PATH`。

macOS/Linux 下二进制文件不带 `.exe` 后缀：

```text
bin/
├── ffmpeg
└── ffprobe
```

macOS 也可以用 Homebrew 安装：

```bash
brew install ffmpeg
```

程序会优先使用项目 `bin/` 中的二进制；如果不存在，会继续查找系统 `PATH`，以及 macOS 常见路径 `/opt/homebrew/bin`、`/usr/local/bin`、`/usr/bin`。如果要把 `.app` 发给没有安装 FFmpeg 的用户，建议仍然内置 `bin/ffmpeg` 和 `bin/ffprobe`。

### 3. 启动程序

```bash
python main.py
```

macOS 首次运行建议：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

如果 macOS 提示 Qt 平台插件或窗口权限问题，先确认当前 Python 环境安装的是 PyQt6 与 PyQt6-Fluent-Widgets，并从终端启动查看完整报错。

---

## 打包

项目提供了 PyInstaller 打包脚本：

```bash
python build_app.py
```

macOS 打包需在 macOS 本机执行：

```bash
python3 build_app.py
```

打包结果会输出到 `dist/BD_Toolbox/`；macOS 下会生成 `dist/BD_Toolbox.app`。如果需要 macOS 原生图标，可在项目根目录放置 `bd_toolbox.icns`。`build/`、`dist/`、虚拟环境、缓存文件、日志文件和本地 FFmpeg 二进制文件不会提交到源码仓库。

---

## 下载

如果不想自行配置 Python 环境，可以前往 GitHub Releases 下载已打包版本：

[BD Toolbox Releases](https://github.com/bidouBD/BD_Toolbox/releases)

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)。

---

## 开源协议

本项目集成并调用 FFmpeg。FFmpeg 本身遵循其对应的 LGPL/GPL 协议，详情请参考 [FFmpeg 官网](https://ffmpeg.org/)。

BD Toolbox 的 GUI 部分代码按项目仓库声明的开源协议发布。
