# 更新日志

## 2026-06-24

### 缺陷修复

- **字幕烧录：Windows 含中文目录路径导致 FFmpeg Invalid argument** (`ui/pages/subtitle.py`)
  - 在 Windows 下，当字幕文件路径含有中文或其他非 ASCII 字符时，直接传入 `subtitles` filter 会导致 FFmpeg 报 `Invalid argument` 错误。

- **视频压缩：2-Pass 临时文件未清理** (`core/ffmpeg_runner.py`)
  - FFmpeg 在 2-Pass 第一步会生成 `ffmpeg2pass-*.log` 和 `ffmpeg2pass-*.log.mbtree` 临时文件，处理完成后不会自动删除。


- **音频提取：WAV 格式码率判断逻辑冗余** (`ui/pages/audio.py`)
  - `_build_command` 中 `if not lossless and fmt not in ("wav",)` 条件冗余：WAV 已被包含在 `lossless` 列表中，`fmt not in ("wav",)` 在 `not lossless` 为真时永远不会匹配到 WAV。

- **视频合并：concat 路径转义在 Windows 路径中无效** (`ui/pages/merge.py`)
  - 原函数使用 Bash 风格的单引号转义（`'\''`），在 Windows 的 FFmpeg concat 列表文件中不被识别，会导致含单引号路径的文件合并失败。

## 2026-06-22

### 新增功能
- **帮助页上线**：新增“帮助文档”页面，全面覆盖 FFmpeg 基础语法、GUI 常用参数解释（CRF/VBR/ABR等）、常见功能处理案例以及典型报错排查指导。
- **添加 bin 文件夹指引**：在项目中加入了 `bin/` 文件夹并附带 `请将ffmpeg与ffprobe放在此处.txt` 引导文件，指引合作开发者和用户放置对应平台的 FFmpeg 二进制文件，同时通过 `.gitignore` 规则过滤实际的二进制文件上传。

### 多端适配 & 跨平台优化
- **双端二进制路径搜索优化** (`core/ffmpeg_runner.py`, `core/utils.py`)：
  - FFmpeg/ffprobe 在寻找可执行文件时，优先检索项目内的 `bin` 文件夹；若不存在，再依次扫描 macOS 常见安装路径 `/opt/homebrew/bin`、`/usr/local/bin`、`/usr/bin` 以及系统 `PATH` 环境变量。
- **打包配置（PyInstaller）强健化** (`build.spec`, `build_app.py`)：
  - 重构了 `build.spec`，使用 `sysconfig` 动态解析 Python 环境下的 `site-packages` 资源目录。
  - 在 `build.spec` 中设定 `bin` 文件夹及 `.ico`/`.icns`/`.png` 图标文件**存在时才进行打包**，避免在缺少部分资源文件时导致打包直接失败中断。
  - 修改 `build_app.py`，当检测到本地没有 `bin` 文件夹时**不再直接强行退出**，而是通过控制台警告提示用户（允许继续通过系统的 PATH 或自定义路径进行打包运行）。
- **应用图标 macOS 适配** (`main.py`)：
  - 在 macOS 系统下运行时，窗口图标加载逻辑**优先尝试寻找并加载** `bd_toolbox.icns` / `bd_toolbox.png`，在未找到时再向后兼容加载 `.ico` 图标。

### 缺陷修复 & 健壮性提升
- **路径转义安全增强** (`ui/pages/merge.py`, `ui/pages/subtitle.py`)：
  - 针对视频合并（Concat 拼接）和字幕烧录（Subtitles Filter 滤镜参数），进行了更严格的特殊字符（如空格、单引号、反斜杠及冒号）路径转义过滤，极大地降低了 macOS/Linux 在中文、空格、单引号路径下运行时 FFmpeg 报错崩溃的概率。

## 2026-06-02

### UI 重构

- 将桌面界面由此前的 Tkinter/ttk 风格实现重构为 PyQt6。
- 引入 PyQt6-Fluent-Widgets，统一主窗口、侧边导航、功能页和控件视觉风格。
- 拆分并整理功能页面：视频转换、视频压缩、音频处理、视频裁切、视频合并、GIF 导出、字幕处理、Video Lab。
- 重构通用 UI 组件，包括文件选择、输出目录、日志窗口、进度条、滑块、下拉选项和执行按钮。
- 优化浅色/深色主题切换，减少控件闪烁、布局跳动和下拉框透明残影问题。
- 转换与压缩页面加入批量文件处理流程。
- 更新依赖到 PyQt6、PyQt6-Fluent-Widgets、PyQt6-Frameless-Window 与 darkdetect。

### 仓库整理

- 更新 README，说明 PyQt6 重构后的功能、依赖、运行方式和打包方式。
- 补充 `.gitignore` 规则，避免提交虚拟环境、构建产物、缓存、日志和 FFmpeg 二次编码临时文件。
- 保留 PyInstaller `.spec` 配置文件，确保打包脚本所需文件可进入仓库。
