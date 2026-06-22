import PyInstaller.__main__
import os
import shutil

def build():
    # bin is recommended for distributable builds because macOS Finder apps do
    # not always inherit the user's shell PATH. Source runs can still use PATH.
    if not os.path.exists("bin"):
        ffmpeg_ok = shutil.which("ffmpeg") and shutil.which("ffprobe")
        if ffmpeg_ok:
            print("⚠️ 未找到 bin 目录，将不会内置 FFmpeg；当前机器可通过 PATH 调用。")
        else:
            print("⚠️ 未找到 bin 目录，且 PATH 中未检测到 ffmpeg/ffprobe。")
            print("   打包仍会继续，但目标机器需要自行安装 FFmpeg 或把二进制放入 bin。")

    print("🚀 正在打包...")
    
    # 直接运行 spec 文件
    PyInstaller.__main__.run([
        'build.spec',
        '--noconfirm',
        '--clean'
    ])
    
    print("\n✨ 打包完成！")
    import sys
    if sys.platform == "win32":
        print("📂 结果路径: dist/BD_Toolbox/BD_Toolbox.exe")
    elif sys.platform == "darwin":
        print("📂 结果路径: dist/BD_Toolbox/BD_Toolbox.app")
    else:
        print("📂 结果路径: dist/BD_Toolbox/BD_Toolbox")

if __name__ == "__main__":
    build()
