"""
Theme definitions for FFmpeg Studio.
All color/style constants for light and dark modes.
"""

import customtkinter as ctk

# ── Palette ────────────────────────────────────────────────────────────────────
COLORS = {
    "light": {
        "sidebar_bg":       "#E8EBF2",
        "main_bg":          "#F2F4F8",
        "card_bg":          "#FFFFFF",
        "card_border":      "#E2E5EE",
        "text_primary":     "#1C1F2E",
        "text_secondary":   "#6B7280",
        "text_hint":        "#9CA3AF",
        "accent":           "#00B894",
        "accent_hover":     "#00A07E",
        "accent_text":      "#FFFFFF",
        "nav_active":       "#D6F5EE",
        "nav_active_text":  "#007A64",
        "nav_hover":        "#ECEEF5",
        "nav_text":         "#4B5563",
        "btn_stop":         "#EF4444",
        "btn_stop_hover":   "#DC2626",
        "log_bg":           "#F8F9FC",
        "log_text":         "#374151",
        "log_border":       "#E2E5EE",
        "progress_track":   "#E2E5EE",
        "progress_fill":    "#00B894",
        "input_bg":         "#FFFFFF",
        "input_border":     "#D1D5DB",
        "dropdown_bg":      "#FFFFFF",
        "separator":        "#E5E7EB",
        "tag_bg":           "#EEF2FF",
        "tag_text":         "#4338CA",
        "title_text":       "#111827",
        "sun_icon":         "☀",
        "moon_icon":        "🌙",
    },
    "dark": {
        "sidebar_bg":       "#111827",
        "main_bg":          "#1F2937",
        "card_bg":          "#283548",
        "card_border":      "#374151",
        "text_primary":     "#F3F4F6",
        "text_secondary":   "#9CA3AF",
        "text_hint":        "#6B7280",
        "accent":           "#00C9A7",
        "accent_hover":     "#00B894",
        "accent_text":      "#FFFFFF",
        "nav_active":       "#064E3B",
        "nav_active_text":  "#34D399",
        "nav_hover":        "#1F2F40",
        "nav_text":         "#D1D5DB",
        "btn_stop":         "#EF4444",
        "btn_stop_hover":   "#DC2626",
        "log_bg":           "#151E2B",
        "log_text":         "#A0AEC0",
        "log_border":       "#374151",
        "progress_track":   "#374151",
        "progress_fill":    "#00C9A7",
        "input_bg":         "#1F2937",
        "input_border":     "#4B5563",
        "dropdown_bg":      "#283548",
        "separator":        "#374151",
        "tag_bg":           "#1E3A5F",
        "tag_text":         "#93C5FD",
        "title_text":       "#F9FAFB",
        "sun_icon":         "☀",
        "moon_icon":        "🌙",
    },
}

# Current mode holder
_mode = "light"

def get_mode():
    return ctk.get_appearance_mode().lower()

def C(key: str) -> str:
    """Get color for current mode."""
    mode = get_mode()
    return COLORS.get(mode, COLORS["light"]).get(key, "#FF00FF")

def apply_mode(new_mode: str):
    """Switch appearance mode."""
    ctk.set_appearance_mode(new_mode)

# ── Font helpers ───────────────────────────────────────────────────────────────
FONT_FAMILY = "Microsoft YaHei UI"

def font(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def title_font():
    return font(18, "bold")

def heading_font():
    return font(14, "bold")

def body_font():
    return font(13)

def small_font():
    return font(11)

def mono_font():
    return ctk.CTkFont(family="Consolas", size=12)
