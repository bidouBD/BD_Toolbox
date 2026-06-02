import sys
import os
from pathlib import Path
from PyQt6.QtGui import QIcon

# Must be before any Qt imports
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
try:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
except: pass

sys.path.insert(0, str(Path(__file__).parent))


class BDToolbox:
    """Wrapper to delay importing qfluentwidgets and pages until QApplication exists."""

    @staticmethod
    def create():
        from qfluentwidgets import (
            FluentWindow, NavigationItemPosition, FluentIcon,
            setTheme, Theme, isDarkTheme,
        )
        from ui.pages.convert import ConvertPage
        from ui.pages.compress import CompressPage
        from ui.pages.audio import AudioPage
        from ui.pages.cut import CutPage
        from ui.pages.merge import MergePage
        from ui.pages.gif import GifPage
        from ui.pages.subtitle import SubtitlesPage
        from ui.pages.lab import LabPage

        class MainWindow(FluentWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("BD Toolbox")
                self.resize(1280, 800)
                self.setMinimumSize(1100, 780)

                try:
                    self.windowEffect.removeBackgroundEffect(self.winId())
                except Exception:
                    pass

                # App icon
                try:
                    from core.ffmpeg_runner import get_resource_path
                    icon_path = get_resource_path("bd_toolbox.ico")
                    if os.path.exists(icon_path):
                        self.setWindowIcon(QIcon(icon_path))
                except Exception:
                    pass

                setTheme(Theme.LIGHT)
                self.navigationInterface.setExpandWidth(160)

                self._setup_navigation()

            # ── Navigation ────────────────────────────────────────────────────────

            def _setup_navigation(self):
                """Add all nav items. Called once from __init__."""
                from qfluentwidgets import NavigationItemPosition, FluentIcon
                from ui.pages.convert import ConvertPage
                from ui.pages.compress import CompressPage
                from ui.pages.audio import AudioPage
                from ui.pages.cut import CutPage
                from ui.pages.merge import MergePage
                from ui.pages.gif import GifPage
                from ui.pages.subtitle import SubtitlesPage
                from ui.pages.lab import LabPage

                # Group: Core Tools
                self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)
                self.addSubInterface(ConvertPage(self),  FluentIcon.VIDEO,    "视频转换")
                self.addSubInterface(CompressPage(self), FluentIcon.ZOOM,     "视频压缩")
                self.addSubInterface(AudioPage(self),    FluentIcon.MUSIC,    "音频提取")
                self.addSubInterface(CutPage(self),      FluentIcon.EDIT,     "视频裁切")

                # Group: Extended Features
                self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)
                self.addSubInterface(MergePage(self),    FluentIcon.LIBRARY,  "视频合并",
                                     position=NavigationItemPosition.SCROLL)
                self.addSubInterface(GifPage(self),      FluentIcon.PHOTO,    "导出 GIF",
                                     position=NavigationItemPosition.SCROLL)
                self.addSubInterface(SubtitlesPage(self),FluentIcon.DOCUMENT, "烧录字幕",
                                     position=NavigationItemPosition.SCROLL)

                # Group: Utilities
                self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)
                self.addSubInterface(LabPage(self),      FluentIcon.BROOM,    "视频实验室",
                                     position=NavigationItemPosition.SCROLL)

                # Bottom: theme toggle
                self.navigationInterface.addItem(
                    routeKey="theme_toggle",
                    icon=FluentIcon.CONSTRACT,
                    text="深色模式",
                    onClick=self._toggle_theme,
                    position=NavigationItemPosition.BOTTOM,
                )


            # ── Theme toggle ──────────────────────────────────────────────────────

            def _toggle_theme(self):
                from qfluentwidgets import setTheme, Theme, isDarkTheme
                if isDarkTheme():
                    setTheme(Theme.LIGHT)
                    # FIX: was `setText` with no argument (silent bug — setText is a method,
                    # not a call; the label never updated when switching back to light mode)
                    self.navigationInterface.widget("theme_toggle").setText("深色模式")
                else:
                    setTheme(Theme.DARK)
                    self.navigationInterface.widget("theme_toggle").setText("浅色模式")

                # ── Do NOT call unpolish/polish on the whole window here ──────────
                # qfluentwidgets already repaints every managed widget when setTheme()
                # fires its internal themeChanged signal. Cascading unpolish/polish
                # from the top-level window causes all children to recalculate their
                # sizeHint(), which is the root cause of the one-time layout shift.
                # FlatComboBox instances self-refresh via qconfig.themeChanged.

        return MainWindow()


def main():
    app = QApplication(sys.argv)

    from qfluentwidgets import setTheme, Theme, setThemeColor
    setThemeColor("#00B894")
    setTheme(Theme.LIGHT)

    app.setStyleSheet("""
        CaptionLabel#VideoInfoLabel { color: #8C8C8C; }
        PrimaryPushButton { padding: 0 20px; }
    """)

    window = BDToolbox.create()
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()