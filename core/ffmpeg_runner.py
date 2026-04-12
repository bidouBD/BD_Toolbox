import subprocess
import threading
import os
import re
import sys
from pathlib import Path


def get_resource_path(relative_path):
    """Robust path getter for PyInstaller and dev environments."""
    if getattr(sys, 'frozen', False):
        # 1. Check sys._MEIPASS (bundled root, often _internal in new versions)
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            path = Path(meipass) / relative_path
            if path.exists(): return str(path)

        # 2. Check executable parent (manual placement)
        exe_path = Path(sys.executable).parent / relative_path
        if exe_path.exists(): return str(exe_path)
    else:
        # Development environment
        base_dir = Path(__file__).parent.parent
        return str(base_dir / relative_path)
    
    return relative_path

def get_ffmpeg_path():
    """Get the path to ffmpeg executable."""
    # Priority: bin/ffmpeg.exe, then system PATH
    p = get_resource_path(os.path.join("bin", "ffmpeg.exe"))
    return p if os.path.exists(p) else 'ffmpeg'

def get_ffprobe_path():
    """Get the path to ffprobe executable."""
    p = get_resource_path(os.path.join("bin", "ffprobe.exe"))
    return p if os.path.exists(p) else 'ffprobe'


class FFmpegRunner:
    """Runs FFmpeg commands in a background thread and reports progress."""

    def __init__(self, log_callback=None, progress_callback=None, done_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.done_callback = done_callback
        self.process = None
        self.running = False
        self._total_duration = None

    def set_duration(self, seconds):
        self._total_duration = seconds

    def run(self, cmd_or_list):
        """Start FFmpeg command(s) in background thread. cmd_or_list can be a list of strings or a list of list of strings."""
        if self.running:
            return
        self.running = True
        
        # Normalize to list of lists
        if isinstance(cmd_or_list, list) and cmd_or_list and isinstance(cmd_or_list[0], str):
            commands = [cmd_or_list]
        else:
            commands = cmd_or_list
            
        thread = threading.Thread(target=self._execute_sequential, args=(commands,), daemon=True)
        thread.start()

    def _execute_sequential(self, commands):
        try:
            for i, cmd in enumerate(commands):
                if len(commands) > 1:
                    self._log(f"\n📦 执行第 {i+1}/{len(commands)} 步...")
                
                ffmpeg = get_ffmpeg_path()
                resolved_cmd = list(cmd)
                if resolved_cmd and resolved_cmd[0] in ('ffmpeg', 'ffmpeg.exe'):
                    resolved_cmd[0] = ffmpeg

                self._log(f"▶ {' '.join(resolved_cmd)}")
                self._log("─" * 60)

                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

                self.process = subprocess.Popen(
                    resolved_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=creation_flags,
                )

                for line in self.process.stdout:
                    line = line.rstrip('\n\r')
                    if line.strip():
                        self._log(line)
                        # Only parse progress for the last command if multiple, or weighted?
                        # For simplicity, parse for all, but maybe user wants specific handling.
                        self._parse_progress(line)

                self.process.wait()
                rc = self.process.returncode
                if rc != 0:
                    self._log(f"❌ 步骤 {i+1} 失败（返回码 {rc}）")
                    if self.done_callback:
                        self.done_callback(False)
                    return

            self._log("─" * 60)
            self._log("✅ 所有处理已完成！")
            if self.done_callback:
                self.done_callback(True)

        except Exception as e:
            self._log(f"❌ 运行时错误: {e}")
            if self.done_callback:
                self.done_callback(False)
        finally:
            self.running = False

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _parse_progress(self, line):
        if self.progress_callback and 'time=' in line:
            m = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line)
            if m:
                h, mi, s = m.groups()
                elapsed = int(h) * 3600 + int(mi) * 60 + float(s)
                pct = 0.0
                if self._total_duration and self._total_duration > 0:
                    pct = min(elapsed / self._total_duration, 1.0)
                self.progress_callback(pct)

    def stop(self):
        """Terminate the running FFmpeg process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self._log("⏹ 已停止处理")
        self.running = False
