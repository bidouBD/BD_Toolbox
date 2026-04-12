"""
Left sidebar navigation with animated hover and sun/moon theme toggle.
"""

import customtkinter as ctk
from ui.theme import font, body_font, small_font


# (key, icon, label)
NAV_ITEMS_CORE = [
    ("convert",  "🎬", "视频转换"),
    ("compress", "📉", "视频压缩"),
    ("audio",    "🎵", "音频提取"),
    ("cut",      "🕒", "视频裁切"),
]

NAV_ITEMS_ADV = [
    ("merge",    "🧩", "视频合并"),
    ("gif",      "🎦", "导出 GIF"),
    ("subtitle", "💬", "烧录字幕"),
]

NAV_ITEMS_LAB = [
    ("lab",      "🧪", "视频实验室"),
]

NAV_ITEMS = NAV_ITEMS_CORE + NAV_ITEMS_ADV + NAV_ITEMS_LAB


class NavButton(ctk.CTkFrame):
    """Single navigation item with hover animation."""

    def __init__(self, parent, icon, label, command, **kwargs):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=10,
            cursor="hand2",
            **kwargs,
        )
        self.grid_columnconfigure(1, weight=1)
        self._command = command
        self._active = False

        self._icon_lbl = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(family="Segoe UI Emoji", size=18),
            width=24,
            anchor="center",
            bg_color="transparent"
        )
        self._icon_lbl.grid(row=0, column=0, padx=(12, 4), pady=10)

        self._text_lbl = ctk.CTkLabel(
            self,
            text=label,
            font=body_font(),
            anchor="w",
            text_color=["#4B5563", "#D1D5DB"],
            bg_color="transparent"
        )
        self._text_lbl.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        # Bind click + hover
        for w in (self, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_click(self, _e=None):
        self._command()

    def _on_enter(self, _e=None):
        if not self._active:
            self.configure(fg_color=["#ECEEF5", "#1F2F40"])

    def _on_leave(self, _e=None):
        if not self._active:
            self.configure(fg_color="transparent")

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(fg_color=["#D6F5EE", "#064E3B"])
            self._text_lbl.configure(
                text_color=["#007A64", "#34D399"],
                font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            )
            self._icon_lbl.configure(text_color=["#007A64", "#34D399"])
        else:
            self.configure(fg_color="transparent")
            self._text_lbl.configure(
                text_color=["#4B5563", "#D1D5DB"],
                font=body_font(),
            )
            self._icon_lbl.configure(text_color=["#374151", "#CCE3FA"])


class Sidebar(ctk.CTkFrame):
    """Full left sidebar with logo, navigation, and theme toggle."""

    def __init__(self, parent, navigate_cb, toggle_theme_cb, **kwargs):
        super().__init__(
            parent,
            width=220,
            corner_radius=0,
            fg_color=["#E8EBF2", "#111827"],
            border_width=0,
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._navigate_cb = navigate_cb
        self._toggle_theme_cb = toggle_theme_cb
        self._nav_buttons: dict[str, NavButton] = {}
        self._current_key = None
        self._is_dark = False

        self._build()

    def _build(self):
        # ── Logo ──────────────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=72)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        logo_frame.grid_propagate(False)
        logo_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            logo_frame,
            text="⚡ FFmpeg Studio",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold"),
            text_color=["#111827", "#F9FAFB"],
            anchor="w",
        ).grid(row=0, column=0, padx=20, pady=22, sticky="w")

        # Divider
        ctk.CTkFrame(
            self, height=1, fg_color=["#D1D5DB", "#374151"], corner_radius=0
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=0)

        # ── Navigation ────────────────────────────────────────────────────────
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=12)
        nav_frame.grid_columnconfigure(0, weight=1)

        # Basic Section
        ctk.CTkLabel(
            nav_frame, text="  🚀 基础处理", font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            text_color=["#3b5b99", "#8BA9F5"], anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=50, pady=(5, 5))

        curr_row = 1
        for i, (key, icon, label) in enumerate(NAV_ITEMS_CORE):
            btn = NavButton(
                nav_frame,
                icon=icon,
                label=label,
                command=lambda k=key: self._navigate_cb(k),
            )
            btn.grid(row=curr_row, column=0, sticky="ew", pady=2)
            self._nav_buttons[key] = btn
            curr_row += 1

        # Advanced Section
        ctk.CTkLabel(
            nav_frame, text="  💎 进阶功能", font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            text_color=["#3b5b99", "#8BA9F5"], anchor="w"
        ).grid(row=curr_row, column=0, sticky="ew", padx=50, pady=(15, 5))
        curr_row += 1

        for i, (key, icon, label) in enumerate(NAV_ITEMS_ADV):
            btn = NavButton(
                nav_frame,
                icon=icon,
                label=label,
                command=lambda k=key: self._navigate_cb(k),
            )
            btn.grid(row=curr_row, column=0, sticky="ew", pady=2)
            self._nav_buttons[key] = btn
            curr_row += 1

        # Lab Section
        ctk.CTkLabel(
            nav_frame, text="  🧪 视频实验室", font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            text_color=["#3b5b99", "#8BA9F5"], anchor="w"
        ).grid(row=curr_row, column=0, sticky="ew", padx=50, pady=(15, 5))
        curr_row += 1

        for i, (key, icon, label) in enumerate(NAV_ITEMS_LAB):
            btn = NavButton(
                nav_frame,
                icon=icon,
                label=label,
                command=lambda k=key: self._navigate_cb(k),
            )
            btn.grid(row=curr_row, column=0, sticky="ew", pady=2)
            self._nav_buttons[key] = btn
            curr_row += 1

        # ── Footer divider ────────────────────────────────────────────────────
        ctk.CTkFrame(
            self, height=1, fg_color=["#D1D5DB", "#374151"], corner_radius=0
        ).grid(row=3, column=0, sticky="ew", padx=16, pady=0)

        # ── Theme toggle ──────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent", height=64)
        footer.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)

        self._theme_btn = ctk.CTkButton(
            footer,
            text="☀  浅色模式",
            width=160,
            height=36,
            corner_radius=18,
            font=body_font(),
            fg_color=["#DDE0EB", "#1F2937"],
            hover_color=["#C9CDD9", "#2D3748"],
            text_color=["#374151", "#D1D5DB"],
            command=self._on_toggle,
        )
        self._theme_btn.grid(row=0, column=0, padx=20, pady=14)

    def _on_toggle(self):
        self._is_dark = not self._is_dark
        self._toggle_theme_cb()
        self._update_toggle_label()
        # Explicitly re-apply active state to ensure all widgets refresh their colors
        if self._current_key:
            self.set_active(self._current_key)

    def _update_toggle_label(self):
        if self._is_dark:
            self._theme_btn.configure(text="🌙  深色模式")
        else:
            self._theme_btn.configure(text="☀  浅色模式")

    def set_active(self, key: str):
        self._current_key = key
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == key)

    def sync_theme(self, is_dark: bool):
        self._is_dark = is_dark
        self._update_toggle_label()
