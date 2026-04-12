"""
FFmpeg Studio — Main Entry Point
"""

import customtkinter as ctk
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from ui.theme import apply_mode, COLORS
from ui.sidebar import Sidebar
from ui.pages.convert import ConvertPage
from ui.pages.compress import CompressPage
from ui.pages.audio import AudioPage
from ui.pages.cut import CutPage
from ui.pages.merge import MergePage
from ui.pages.gif import GifPage
from ui.pages.subtitle import SubtitlesPage
from ui.pages.lab import LabPage

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BD Toolbox")
        self.geometry("1280x800")
        self.minsize(1100, 600)

        # Initial appearance
        self._is_dark = False
        apply_mode("light")
        self.configure(fg_color=["#F2F4F8", "#1F2937"])

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ────────────────────────────────────────────────────────
        self.sidebar = Sidebar(
            self,
            navigate_cb=self._show_page,
            toggle_theme_cb=self._toggle_theme
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Content Container ──────────────────────────────────────────────
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # ── Pages ──────────────────────────────────────────────────────────
        self.pages = {
            "convert":  ConvertPage(self.container),
            "compress": CompressPage(self.container),
            "audio":    AudioPage(self.container),
            "cut":      CutPage(self.container),
            "merge":    MergePage(self.container),
            "gif":      GifPage(self.container),
            "subtitle": SubtitlesPage(self.container),
            "lab":      LabPage(self.container),
        }

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # Start with default page
        self._show_page("convert")

    def _show_page(self, key):
        """Bring selected page to front."""
        for k, page in self.pages.items():
            if k == key:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_forget()

        self.sidebar.set_active(key)

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        mode = "dark" if self._is_dark else "light"
        apply_mode(mode)
        # Force update of colors if needed (CustomTkinter usually handles this well automatically)

if __name__ == "__main__":
    # Ensure bin directory exists for FFmpeg
    bin_path = Path(__file__).parent / "bin"
    if not bin_path.exists():
        bin_path.mkdir(parents=True, exist_ok=True)

    app = App()
    app.mainloop()
