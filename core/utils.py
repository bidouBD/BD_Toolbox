import subprocess
import os
import sys
from pathlib import Path


def get_resource_path(relative_path):
    """Robust path getter for PyInstaller and dev environments."""
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            path = Path(meipass) / relative_path
            if path.exists(): return str(path)
        exe_path = Path(sys.executable).parent / relative_path
        if exe_path.exists(): return str(exe_path)
    else:
        base_dir = Path(__file__).parent.parent
        return str(base_dir / relative_path)
    return relative_path

def get_ffprobe_path():
    p = get_resource_path(os.path.join("bin", "ffprobe.exe"))
    return p if os.path.exists(p) else 'ffprobe'


def get_video_info(filepath):
    """Get bitrate, duration, and dimensions using ffprobe."""
    try:
        ffprobe = get_ffprobe_path()
        result = subprocess.run(
            [
                ffprobe, '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=bitrate,width,height:format=duration,bit_rate',
                '-of', 'json',
                filepath,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        import json
        data = json.loads(result.stdout)
        
        # Duration from format
        duration = float(data.get('format', {}).get('duration', 0))
        # Bitrate can be in format or stream
        bitrate = int(data.get('format', {}).get('bit_rate', 0))
        if not bitrate and data.get('streams'):
            bitrate = int(data.get('streams', [{}])[0].get('bit_rate', 0))
        
        # Fallback: calculate bitrate if duration and size are known
        if not bitrate and duration > 0:
            file_size = os.path.getsize(filepath)
            bitrate = int((file_size * 8) / duration)
            
        return {
            "duration": duration,
            "bitrate": bitrate,
            "width": data.get('streams', [{}])[0].get('width') if data.get('streams') else None,
            "height": data.get('streams', [{}])[0].get('height') if data.get('streams') else None
        }
    except Exception:
        return None


def format_time(seconds):
    """Format seconds → HH:MM:SS"""
    if seconds is None:
        return "00:00:00"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_time(time_str):
    """Parse HH:MM:SS or MM:SS → seconds (float)."""
    try:
        parts = str(time_str).strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except Exception:
        return 0.0


def generate_output_path(input_path, suffix='_output', ext=None):
    """Generate a safe output path next to the input file."""
    p = Path(input_path)
    new_ext = ext if ext else p.suffix
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    candidate = p.parent / f"{p.stem}{suffix}{new_ext}"
    counter = 1
    while candidate.exists():
        candidate = p.parent / f"{p.stem}{suffix}_{counter}{new_ext}"
        counter += 1
    return str(candidate)


def human_size(path):
    """Return file size as human-readable string."""
    try:
        size = Path(path).stat().st_size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except Exception:
        return "未知"
