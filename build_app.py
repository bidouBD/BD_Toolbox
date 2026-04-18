import PyInstaller.__main__
import os
import sys

def build():
    # 图标文件名
    icon_file = "bd_toolbox.ico"
    
    # 基础参数
    params = [
        'main.py',
        '--noconfirm',
        '--onedir',
        '--windowed',
        '--add-data', 'bin;bin',
        '--clean'
    ]
    
    # 如果图标存在，则添加图标参数
    if os.path.exists(icon_file):
        params.extend(['--add-data', f'{icon_file};.'])
        params.extend(['--icon', icon_file])
        print(f"✅ 检测到图标文件 {icon_file}，已加入打包参数。")
    else:
        print(f"⚠️ 未找到图标文件 {icon_file}，将使用默认图标。")

    print("🚀 开始打包程序...")
    PyInstaller.__main__.run(params)
    print("\n✨ 打包完成！结果保存在 dist 目录下。")

if __name__ == "__main__":
    build()
