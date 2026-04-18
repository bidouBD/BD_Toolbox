**BD Toolbox** 是一款基于 Python 和 CustomTkinter 开发的现代视频/音频处理平台。它旨在通过直观的 GUI 界面简化复杂的 FFmpeg 命令行操作，提供专业级的压制、转换与修复功能。

---

## ✨ 核心特性

### 1. 🎬 专业格式转换
*   **全格式支持**：支持 MP4, MKV, AVI, MOV, FLV, WebM, TS, M4V, GIF 等主流容器。
*   **硬件加速**：深度集成 **Nvidia NVENC**、**Intel QSV** 和 **AMD AMF** 硬件编码器，飞速导出。
*   **精准压制**：
    *   **CRF (画面质量)**：支持 0-51 的超广范围调节。
    *   **VBR/2-Pass**：支持目标比特率控制及二次编码，实现极致画质平衡。
*   **滑杆控制**：全新的 LabeledSlider 控件，比特率设置精确到 kbps。

### 2. 📉 智能视频压缩
*   **一键比例压缩**：内置 3/4, 1/2, 1/3, 1/4 四种预设比例，自动计算并匹配目标码率。
*   **智能兜底**：即便视频元数据缺失，系统也会根据算法自动反推码率，确保“所见即所得”的体积控制。
*   **分辨率缩放**：支持 1080p, 720p, 480p 一键降级。

### 3. 🛠️ 进阶处理工具
*   **字幕压制**：支持硬压字幕到视频，或从视频中提取字幕流。
*   **音频处理**：支持音频一键提取、AAC/MP3 转换。
*   **视频合并**：基于列表的高速视频合并。
*   **视频裁切**：提供“快速模式”（流复制）与“精确模式”（重编码）双重选择。
*   **GIF 导出**：高质量调色板生成算法，导出清晰、体积适中的动图。

### 4. 🧪 视频实验室 (Video Lab)
*   **自动裁切 (CropDetect)**：智能识别视频黑边并自动裁切。
*   **音量标准化 (Loudnorm)**：修正音量过大或过小，使音频达到统一标准。
*   **旋转修复**：修复录制角度异常的视频。
*   **静音检测剪辑**：自动检测并切除视频中的空白静音片段。

---

## 📥 软件下载

如果您不想配置 Python 环境，可以直接前往 **[GitHub Releases]([https://github.com//releases](https://github.com/bidouBD/BD_Toolbox/releases))** 下载打包好的压缩包。
- **绿色版**：解压即用，无需安装。
- **全集成**：内置所有环境依赖及 FFmpeg 核心。

---


## 🛠️ 技术栈

*   **核心引擎**: [FFmpeg](https://ffmpeg.org/) (ffmpeg/ffprobe)
*   **UI 框架**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (现代深色/浅色界面切换)
*   **并发处理**: 多线程异步执行，UI 永不卡死
*   **路径解析**: 兼容 PyInstaller `_internal` 结构的自研路径解析逻辑

---

## 最近更新
* 新增视频压缩与视频转换界面的批处理功能，快速进行批量处理。
* 完善了说明文档

---

## 📦 安装与运行

### 环境准备
1. 确保安装了 Python 3.10+。
2. 将 `ffmpeg.exe` 和 `ffprobe.exe` 放入项目的 `bin` 文件夹。
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 运行程序
```bash
python main.py
```

### 📦 自动化打包
推荐使用内置的打包脚本，它会自动配置图标及所有资源路径：
```bash
python build_app.py
```

---

## 📸 界面预览

<img width="1602" height="1039" alt="image" src="https://github.com/user-attachments/assets/ff8fd86e-d090-48d7-b97a-f63f29e92acc" />

---

##📝开发计划
* 1、AI助手：视频实验室添加基于LLM的全能处理功能，告诉AI你想实现的功能，自动转换为指令并执行
* 2、帮助手册：添加入门手册，帮助新手快速理解并上手工具箱

## ⚖️ 开源协议

本软件集成了 FFmpeg 项目 (https://ffmpeg.org)。 FFmpeg 的软件部分遵循其相应的 LGPL/GPL 协议。 
本软件的 GUI 部分代码采用GLP协议开源。 感谢 FFmpeg 社区的卓越贡献！
