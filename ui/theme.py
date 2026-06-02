"""
Theme definitions for BD Toolbox (PyQt6 + qfluentwidgets).
Color palette and font helpers.
"""

from PyQt6.QtGui import QFont, QColor
from qfluentwidgets import isDarkTheme
# ── Palette ────────────────────────────────────────────────────────────────────
COLORS = {
    "light": {
        "accent":           "#00B894",
        "accent_hover":     "#00A07E",
        "accent_text":      "#FFFFFF",
        "text_primary":     "#1C1F2E",
        "text_secondary":   "#6B7280",
        "text_hint":        "#9CA3AF",
        "card_bg":          "#FFFFFF",
        "card_border":      "#E2E5EE",
        "log_bg":           "#F8F9FC",
        "log_text":         "#374151",
        "btn_stop":         "#EF4444",
        "btn_stop_hover":   "#DC2626",
        "progress_track":   "#E2E5EE",
        "progress_fill":    "#00B894",
    },
    "dark": {
        "accent":           "#00C9A7",
        "accent_hover":     "#00B894",
        "accent_text":      "#FFFFFF",
        "text_primary":     "#F3F4F6",
        "text_secondary":   "#9CA3AF",
        "text_hint":        "#6B7280",
        "card_bg":          "#283548",
        "card_border":      "#374151",
        "log_bg":           "#151E2B",
        "log_text":         "#A0AEC0",
        "btn_stop":         "#EF4444",
        "btn_stop_hover":   "#DC2626",
        "progress_track":   "#374151",
        "progress_fill":    "#00C9A7",
    },
}

# ── Font System ──────────────────────────────────────────────────────────────
FONT_FAMILY = "Microsoft YaHei UI"

def font(size: int = 12, bold: bool = False) -> QFont:
    f = QFont()
    f.setFamily("Microsoft YaHei UI")
    f.setPointSize(size)
    if bold:
        f.setWeight(QFont.Weight.Bold)
    return f

def title_font() -> QFont:
    return font(16, bold=True)

def heading_font() -> QFont:
    return font(13, bold=True)

def body_font() -> QFont:
    return font(12)

def small_font() -> QFont:
    return font(11)

def mono_font() -> QFont:
    return QFont("Consolas", 10)
def hint_color() -> str:
    return "#8C8C8C" if not isDarkTheme() else "#9CA3AF"
