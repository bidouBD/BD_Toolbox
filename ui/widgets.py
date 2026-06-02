"""
Reusable widgets for BD Toolbox (PyQt6 + qfluentwidgets).
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFileDialog,
    QSizePolicy, QGridLayout, QComboBox, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPolygon

from qfluentwidgets import (
    PushButton, PrimaryPushButton, LineEdit,
    Slider, ProgressBar,
    BodyLabel, CaptionLabel, StrongBodyLabel,
    PlainTextEdit, SpinBox, isDarkTheme,
    SwitchButton,
)
from ui.theme import body_font, small_font, mono_font, font


# ── Helpers ───────────────────────────────────────────────────────────────────

def _label_emphasis_style() -> str:
    """Vertical-bar accent style for parameter labels."""
    color = "#1C1F2E" if not isDarkTheme() else "#E5E7EB"
    return (
        f"color: {color};"
        "border-left: 3px solid #00B894;"
        "padding-left: 8px;"
        "font-weight: 500;"
    )


# ─────────────────────────────────────────────────────────────────────────────
# SectionCard
# ─────────────────────────────────────────────────────────────────────────────

class SectionCard(QFrame):
    """
    Styled card container using QFrame.

    Previous implementation extended CardWidget, whose internal paintEvent
    drew competing borders/backgrounds that shifted on theme change.
    QFrame + pure stylesheet gives us full, deterministic control.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self._apply_style()

        # Auto-refresh when theme changes
        try:
            from qfluentwidgets import qconfig
            qconfig.themeChanged.connect(lambda _: self._apply_style())
        except Exception:
            pass

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(8)

    def _apply_style(self):
        if isDarkTheme():
            bg, border = "#283548", "#374151"
        else:
            bg, border = "#FFFFFF", "#E2E5EE"
        self.setStyleSheet(f"""
            #SectionCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)


# ─────────────────────────────────────────────────────────────────────────────
# FlatComboBox — 原生 QComboBox，完全无动画层、无玻璃效果
# ─────────────────────────────────────────────────────────────────────────────

def _combo_stylesheet() -> str:
    """Generate a theme-aware stylesheet for FlatComboBox."""
    if isDarkTheme():
        bg            = "#3C3C3C"
        bg_item_hover = "#4A4A4A"
        border        = "#555555"
        text          = "#F3F4F6"
        arrow_hover   = "#00C9A7"
        bg_pressed    = "#3C3C3C"  # Keep same as bg to avoid stuck background color bug
        drop_bg       = "#2D2D2D"
        drop_border   = "#555555"
        indicator     = "#00C9A7"
    else:
        bg            = "#FFFFFF"
        bg_item_hover = "#F0FDF9"
        border        = "#D1D5DB"
        text          = "#1C1F2E"
        arrow_hover   = "#00B894"
        bg_pressed    = "#FFFFFF"  # Keep same as bg to avoid stuck background color bug
        drop_bg       = "#FFFFFF"
        drop_border   = "#D1D5DB"
        indicator     = "#00B894"

    return f"""
        QComboBox {{
            background-color: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 0 10px;
            font-size: 12px;
            font-family: "Microsoft YaHei UI";
        }}
        QComboBox:hover {{
            border-color: {arrow_hover};
        }}
        /* FIX: :pressed and :on (popup-open) keep the accent border so the
           colour does not "flash back" to the normal border on click. */
        QComboBox:pressed, QComboBox:on {{
            background-color: {bg_pressed};
            border: 1px solid {arrow_hover};
        }}
        QComboBox:focus {{
            border: 1px solid {arrow_hover};
        }}
        QComboBox:disabled {{ opacity: 0.45; }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 30px;
            border: none;
            margin-right: 2px;
        }}
        QComboBox::down-arrow {{
            image: none;
            width: 0px;
            height: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {drop_bg};
            color: {text};
            border: 1px solid {drop_border};
            border-radius: 8px;
            outline: none;
            selection-background-color: {bg_item_hover};
            selection-color: {text};
            padding: 4px;
            show-decoration-selected: 1;
            font-size: 13px;
            font-family: "Microsoft YaHei UI";
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 28px;
            padding: 6px 12px 6px 16px;
            border-left: 3px solid transparent;
            border-radius: 4px;
            font-size: 13px;
            font-family: "Microsoft YaHei UI";
            margin: 2px 0px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {bg_item_hover};
            border-left-color: transparent;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {bg_item_hover};
            border-left-color: {indicator};
        }}
    """


class FlatComboBox(QComboBox):
    """Plain QComboBox styled to match the app theme — zero animation artefacts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self.setStyleSheet(_combo_stylesheet())
        self.setMaxVisibleItems(15)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Ensure this widget itself is fully opaque
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        item_font = QFont("Microsoft YaHei UI", 12)
        self.setFont(item_font)

        from PyQt6.QtWidgets import QStyledItemDelegate
        class TallItemDelegate(QStyledItemDelegate):
            def sizeHint(self, option, index):
                size = super().sizeHint(option, index)
                size.setHeight(34)
                return size
        self.setItemDelegate(TallItemDelegate(self))

        # ── Auto-refresh stylesheet on theme change ────────────────────────
        # Without this, switching themes left the combo boxes with stale colours
        # (light palette in dark mode and vice versa).
        try:
            from qfluentwidgets import qconfig
            qconfig.themeChanged.connect(lambda _: self.setStyleSheet(_combo_stylesheet()))
        except Exception:
            pass

    def showPopup(self):
        """
        FIX for popup-window flicker / transparency artefacts.

        The popup container created internally by Qt is a separate top-level
        QWidget.  If it inherited WA_TranslucentBackground from an earlier
        glass-effect pass, its background would be transparent, producing the
        "flicker / disappear" effect the user reported.  We force it opaque
        immediately after Qt creates it.
        """
        super().showPopup()
        view = self.view()
        if view:
            popup_win = view.window()
            popup_win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            popup_win.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
            # Re-apply background colour so the forced-opaque window is not black
            bg = "#2D2D2D" if isDarkTheme() else "#FFFFFF"
            popup_win.setStyleSheet(f"background: {bg};")

    def paintEvent(self, event):
        """Draw the combo box then paint a crisp chevron arrow on top."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        arrow_color = "#C0C4CC" if isDarkTheme() else "#6B7280"
        rect = self.rect()
        ax = rect.right() - 16
        ay = rect.center().y()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(arrow_color))
        painter.drawPolygon(QPolygon([
            QPoint(ax - 4, ay - 2),
            QPoint(ax + 4, ay - 2),
            QPoint(ax,     ay + 3),
        ]))
        painter.end()

    @property
    def currentTextChanged(self):
        return super().currentTextChanged


# ─────────────────────────────────────────────────────────────────────────────
# FileSelector
# ─────────────────────────────────────────────────────────────────────────────

class FileSelector(QWidget):
    pathChanged = pyqtSignal(object)

    def __init__(self, parent=None, label="选择文件",
                 filetypes=None, multiple=False, on_change=None):
        super().__init__(parent)
        self._filetypes = filetypes or [("所有文件", "*.*")]
        self._multiple  = multiple
        self._paths: list[str] = []
        if on_change:
            self.pathChanged.connect(on_change)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.btn = PrimaryPushButton(f"📂  {label}", self)
        self.btn.setFixedHeight(34)
        self.btn.setFont(body_font())
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._browse)
        lay.addWidget(self.btn)

        self.lbl = LineEdit(self)
        self.lbl.setReadOnly(True)
        self.lbl.setPlaceholderText("暂未选择任何文件...")
        self.lbl.setFixedHeight(34)
        lay.addWidget(self.lbl, 1)

    def _browse(self):
        f = ";;".join(f"{d} ({p})" for d, p in self._filetypes)
        if self._multiple:
            paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", f)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", f)
            paths = [path] if path else []

        if paths:
            self._paths = paths
            display = (
                f"已选 {len(paths)} 个文件: " + ", ".join(Path(x).name for x in paths)
                if self._multiple else paths[0]
            )
            self.lbl.setText(display)
            self.pathChanged.emit(paths if self._multiple else paths[0])

    def get(self):
        return self._paths if self._multiple else (self._paths[0] if self._paths else None)

    def set_path(self, p):
        self._paths = [p] if p else []
        self.lbl.setText(str(p) if p else "")

    def clear(self):
        self._paths = []
        self.lbl.clear()


# ─────────────────────────────────────────────────────────────────────────────
# LabeledSlider
# ─────────────────────────────────────────────────────────────────────────────

class LabeledSlider(QWidget):
    def __init__(self, parent=None, label="", from_=0, to=100000,
                 number_of_steps=100, default=2000, unit="kbps",
                 on_change=None, slider_width=240, width=150):
        super().__init__(parent)
        self._on_change = on_change

        lay = QGridLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setHorizontalSpacing(15)
        lay.setVerticalSpacing(8)

        lbl = BodyLabel(label, self)
        lbl.setFont(body_font())
        lbl.setStyleSheet(_label_emphasis_style())
        lay.addWidget(lbl, 0, 0,
                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        edit_lay = QVBoxLayout()
        edit_lay.setContentsMargins(0, 0, 0, 0)
        edit_lay.setSpacing(8)

        self.spin = SpinBox(self)
        self.spin.setRange(from_, to)
        self.spin.setValue(default)
        self.spin.setMinimumWidth(180)
        self.spin.setMaximumWidth(220)
        self.spin.setFixedHeight(34)
        self.spin.setFont(small_font())
        if unit:
            self.spin.setSuffix(f" {unit}")

        def _hide_spin_buttons():
            for attr in ("upButton", "downButton"):
                btn = getattr(self.spin, attr, None)
                if btn:
                    btn.setFixedSize(0, 0)
        QTimer.singleShot(0, _hide_spin_buttons)

        edit_lay.addWidget(self.spin)

        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(from_, to)
        self.slider.setValue(default)
        self.slider.setMinimumWidth(slider_width)
        edit_lay.addWidget(self.slider)

        lay.addLayout(edit_lay, 0, 1,
                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lay.setColumnStretch(2, 1)

        self.slider.valueChanged.connect(self._sync_spin)
        self.spin.valueChanged.connect(self._sync_slider)

    def _sync_spin(self, v):
        self.spin.blockSignals(True)
        self.spin.setValue(v)
        self.spin.blockSignals(False)
        if self._on_change:
            self._on_change(v)

    def _sync_slider(self, v):
        self.slider.blockSignals(True)
        self.slider.setValue(v)
        self.slider.blockSignals(False)
        if self._on_change:
            self._on_change(v)

    def get(self):
        return self.slider.value()

    def set(self, v):
        try:
            val = int(v)
            self.slider.setValue(val)
            self.spin.setValue(val)
        except (TypeError, ValueError):
            pass

    def configure(self, **k):
        if "state" in k:
            enabled = k["state"] != "disabled"
            self.slider.setEnabled(enabled)
            self.spin.setEnabled(enabled)


# ─────────────────────────────────────────────────────────────────────────────
# LabeledOption
# ─────────────────────────────────────────────────────────────────────────────

class LabeledOption(QWidget):
    def __init__(self, parent=None, label="", values=None, default=None, width=160):
        super().__init__(parent)

        lay = QGridLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setHorizontalSpacing(15)
        lay.setVerticalSpacing(8)

        lbl = BodyLabel(label, self)
        lbl.setFont(body_font())
        lbl.setStyleSheet(_label_emphasis_style())
        lay.addWidget(lbl, 0, 0,
                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.menu = FlatComboBox(self)
        self.menu.setMinimumWidth(max(180, width))
        self.menu.setFixedHeight(34)
        self.menu.addItems(values or [])
        if default:
            self.menu.setCurrentText(default)
        lay.addWidget(self.menu, 0, 1, 1, 1,
                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lay.setColumnStretch(2, 1)

    def get(self):
        return self.menu.currentText()

    def set(self, v):
        self.menu.setCurrentText(v)

    def configure(self, **k):
        if "state" in k:
            self.menu.setEnabled(k["state"] != "disabled")

    def refresh_theme(self):
        """Manually re-apply stylesheet (kept for compatibility; auto-refresh
        via qconfig.themeChanged is now the primary mechanism in FlatComboBox)."""
        self.menu.setStyleSheet(_combo_stylesheet())


# ─────────────────────────────────────────────────────────────────────────────
# ActionButton
# ─────────────────────────────────────────────────────────────────────────────

class ActionButton(PrimaryPushButton):
    _STYLE_START = """
        PrimaryPushButton {
            background-color: #00B894; color: white; border-radius: 8px;
            font-size: 14px; font-weight: bold; border: none; padding: 10px;
        }
        PrimaryPushButton:hover   { background-color: #00A07E; }
        PrimaryPushButton:pressed { background-color: #008D6F; }
    """
    _STYLE_STOP = """
        PrimaryPushButton {
            background-color: #EF4444; color: white; border-radius: 8px;
            font-size: 14px; font-weight: bold; border: none; padding: 10px;
        }
        PrimaryPushButton:hover   { background-color: #DC2626; }
        PrimaryPushButton:pressed { background-color: #B91C1C; }
    """

    def __init__(self, parent=None, start_text="⚡  开始处理", stop_text="⏹  停止", **kwargs):
        super().__init__(parent=parent)
        self._start_text = start_text
        self._stop_text  = stop_text
        self._running    = False
        self.setText(start_text)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._STYLE_START)

    def set_running(self, running: bool):
        self._running = running
        self.setText(self._stop_text if running else self._start_text)
        self.setStyleSheet(self._STYLE_STOP if running else self._STYLE_START)

    @property
    def running(self):
        return self._running


# ─────────────────────────────────────────────────────────────────────────────
# OutputDirSelector
# ─────────────────────────────────────────────────────────────────────────────

class OutputDirSelector(QWidget):
    def __init__(self, parent=None, on_change=None):
        super().__init__(parent)
        self._path     = None
        self._on_change = on_change

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.btn = PrimaryPushButton("📁  输出目录", self)
        self.btn.setFixedSize(130, 32)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._browse)
        lay.addWidget(self.btn)

        self.lbl = BodyLabel("默认：与源文件相同目录", self)
        self._update_hint_color()
        lay.addWidget(self.lbl, 1)

        try:
            from qfluentwidgets import qconfig
            qconfig.themeChanged.connect(lambda _: self._update_hint_color())
        except Exception:
            pass

    def _update_hint_color(self):
        if not self._path:
            c = "#9CA3AF" if isDarkTheme() else "#6B7280"
            self.lbl.setStyleSheet(f"color: {c};")

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if p:
            self._path = p
            self.lbl.setText(p)
            c = "#E5E7EB" if isDarkTheme() else "#111827"
            self.lbl.setStyleSheet(f"color: {c};")
            if self._on_change:
                self._on_change(p)

    def get(self):
        return self._path


# ─────────────────────────────────────────────────────────────────────────────
# LogBox
# ─────────────────────────────────────────────────────────────────────────────

class LogBox(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._hdr = QWidget()
        self._hdr.setFixedHeight(40)
        hl = QHBoxLayout(self._hdr)
        hl.setContentsMargins(15, 0, 15, 0)
        hl.addWidget(StrongBodyLabel("📋 运行日志"))
        hl.addStretch()

        clear_btn = PushButton("清空日志")
        clear_btn.setFixedSize(90, 30)
        clear_btn.setFont(small_font())
        clear_btn.setStyleSheet("margin-right: 5px;")
        clear_btn.clicked.connect(self.clear)
        hl.addWidget(clear_btn)
        lay.addWidget(self._hdr)

        self.box = PlainTextEdit(self)
        self.box.setReadOnly(True)
        self.box.setFont(mono_font())
        lay.addWidget(self.box, 1)
        self.log_signal.connect(self.box.appendPlainText)

        self._apply_log_theme()
        try:
            from qfluentwidgets import qconfig
            qconfig.themeChanged.connect(lambda _: self._apply_log_theme())
        except Exception:
            pass

    def _apply_log_theme(self):
        if isDarkTheme():
            hdr_bg, box_bg, box_border = "rgba(255,255,255,0.04)", "#151E2B", "#374151"
        else:
            hdr_bg, box_bg, box_border = "rgba(0,0,0,0.03)", "#FFFFFF", "rgba(0,0,0,0.05)"
        self._hdr.setStyleSheet(f"background: {hdr_bg}; border-radius: 8px 8px 0 0;")
        self.box.setStyleSheet(
            f"background: {box_bg};"
            f"border: 1px solid {box_border};"
            "border-top: none;"
            "border-radius: 0 0 8px 8px;"
        )

    def append(self, t):
        self.log_signal.emit(t)

    def clear(self):
        self.box.clear()


# ─────────────────────────────────────────────────────────────────────────────
# ProgressRow
# ─────────────────────────────────────────────────────────────────────────────

class ProgressRow(QWidget):
    progress_signal = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.bar = ProgressBar(self)
        self.bar.setRange(0, 100)
        self.bar.setFixedHeight(6)
        lay.addWidget(self.bar, 1)

        self.lbl = CaptionLabel("0%", self)
        self.lbl.setFixedWidth(35)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(self.lbl)

        self.progress_signal.connect(self._update_ui)

    def _update_ui(self, v: int):
        self.bar.setValue(min(100, max(0, v)))
        self.lbl.setText(f"{v}%")

    def set(self, v: float):
        self.progress_signal.emit(int(v * 100))

    def reset(self):
        self.set(0.0)


# ─────────────────────────────────────────────────────────────────────────────
# LabeledEntry
# ─────────────────────────────────────────────────────────────────────────────

class LabeledEntry(QWidget):
    def __init__(self, parent=None, label="", placeholder="", width=120):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)

        lbl = BodyLabel(label, self)
        lbl.setFont(body_font())
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(lbl)

        self.entry = LineEdit(self)
        self.entry.setPlaceholderText(placeholder)
        self.entry.setFixedWidth(width)
        self.entry.setFixedHeight(34)
        lay.addWidget(self.entry)

    def get(self):
        return self.entry.text()

    def set(self, v):
        self.entry.setText(str(v))


# ─────────────────────────────────────────────────────────────────────────────
# LabeledCheckBox
# ─────────────────────────────────────────────────────────────────────────────

class LabeledCheckBox(QWidget):
    def __init__(self, parent=None, label="", default=False):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(10)

        lbl = BodyLabel(label, self)
        lbl.setFont(body_font())
        lbl.setStyleSheet(_label_emphasis_style())
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self.check = SwitchButton(self)
        self.check.setChecked(default)
        self.check.setFixedHeight(34)
        lay.addWidget(self.check, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch()

    def get(self) -> bool:
        return self.check.isChecked()

    def set(self, v: bool):
        self.check.setChecked(v)

    def configure(self, **k):
        if "state" in k:
            self.check.setEnabled(k["state"] != "disabled")