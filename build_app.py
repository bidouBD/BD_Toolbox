import PyInstaller.__main__
import os

def build():
    # 彻底检查 bin 目录
    if not os.path.exists("bin"):
        print("❌ 错误：未找到 bin 目录，请确保 ffmpeg 二进制文件已放入。")
        return

    print("🚀 正在打包...")
    
    # 直接运行 spec 文件
    PyInstaller.__main__.run([
        'build.spec',
        '--noconfirm',
        '--clean'
    ])
    
    print("\n✨ 打包完成！")
    print("📂 结果路径: dist/BD_Toolbox/BD_Toolbox.exe")

if __name__ == "__main__":
    build()
