"""
Reusable widgets: FileSelector, LogBox, SectionCard, ProgressRow, etc.
"""

import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from ui.theme import C, font, heading_font, body_font, small_font, mono_font


# ── Card / Section wrapper ─────────────────────────────────────────────────────

class SectionCard(ctk.CTkFrame):
    """A rounded card frame acting as a visual section container."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            corner_radius=12,
            fg_color=["#FFFFFF", "#283548"],
            border_width=1,
            border_color=["#E2E5EE", "#374151"],
            **kwargs,
        )


# ── File selector ──────────────────────────────────────────────────────────────

class FileSelector(ctk.CTkFrame):
    """
    A horizontal row with a browse button and a label showing the selected path.
    Supports drag-and-drop via tkinterdnd2 if available.
    """

    def __init__(
        self,
        parent,
        label="选择文件",
        filetypes=None,
        multiple=False,
        on_change=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._filetypes = filetypes or [("所有文件", "*.*")]
        self._multiple = multiple
        self._on_change = on_change
        self._paths = []

        self.grid_columnconfigure(1, weight=1)

        # Browse button
        self.btn = ctk.CTkButton(
            self,
            text=f"📂  {label}",
            width=130,
            height=38,
            corner_radius=8,
            font=body_font(),
            fg_color=["#00B894", "#00C9A7"],
            hover_color=["#00A07E", "#00B894"],
            text_color="#FFFFFF",
            command=self._browse,
        )
        self.btn.grid(row=0, column=0, padx=(0, 10))

        # Path display
        self.lbl = ctk.CTkLabel(
            self,
            text="暂未选择任何文件...",
            anchor="w",
            font=body_font(),
            text_color=["#9CA3AF", "#6B7280"],
        )
        self.lbl.grid(row=0, column=1, sticky="ew")

    def _browse(self):
        if self._multiple:
            paths = filedialog.askopenfilenames(filetypes=self._filetypes)
            if paths:
                self._paths = list(paths)
                self.lbl.configure(
                    text=f"已选 {len(self._paths)} 个文件",
                    text_color=["#111827", "#F3F4F6"],
                )
                if self._on_change:
                    self._on_change(self._paths)
        else:
            path = filedialog.askopenfilename(filetypes=self._filetypes)
            if path:
                self._paths = [path]
                # Truncate display
                display = path if len(path) <= 60 else "…" + path[-57:]
                self.lbl.configure(
                    text=display,
                    text_color=["#111827", "#F3F4F6"],
                )
                if self._on_change:
                    self._on_change(path)

    def get(self):
        """Return selected path(s): str if single, list if multiple."""
        if self._multiple:
            return self._paths
        return self._paths[0] if self._paths else None

    def set_path(self, path):
        self._paths = [path] if path else []
        display = path if path and len(path) <= 60 else ("…" + path[-57:] if path else "暂未选择任何文件...")
        self.lbl.configure(
            text=display,
            text_color=["#111827", "#F3F4F6"] if path else ["#9CA3AF", "#6B7280"],
        )

    def clear(self):
        self._paths = []
        self.lbl.configure(text="暂未选择任何文件...", text_color=["#9CA3AF", "#6B7280"])


# ── Output dir selector ────────────────────────────────────────────────────────

class OutputDirSelector(ctk.CTkFrame):
    """Directory selector row."""

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._path = None

        self.grid_columnconfigure(1, weight=1)

        self.btn = ctk.CTkButton(
            self,
            text="📁  输出目录",
            width=130,
            height=38,
            corner_radius=8,
            font=body_font(),
            fg_color=["#6366F1", "#818CF8"],
            hover_color=["#4F46E5", "#6366F1"],
            text_color="#FFFFFF",
            command=self._browse,
        )
        self.btn.grid(row=0, column=0, padx=(0, 10))

        self.lbl = ctk.CTkLabel(
            self,
            text="默认：与源文件相同目录",
            anchor="w",
            font=body_font(),
            text_color=["#9CA3AF", "#6B7280"],
        )
        self.lbl.grid(row=0, column=1, sticky="ew")

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self._path = path
            display = path if len(path) <= 60 else "…" + path[-57:]
            self.lbl.configure(text=display, text_color=["#111827", "#F3F4F6"])
            if self._on_change:
                self._on_change(path)

    def get(self):
        return self._path


# ── Log box ────────────────────────────────────────────────────────────────────

class LogBox(ctk.CTkFrame):
    """
    Scrollable log output box with title header.
    Thread-safe via after() scheduling.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            corner_radius=12,
            fg_color=["#F8F9FC", "#151E2B"],
            border_width=1,
            border_color=["#E2E5EE", "#374151"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title bar
        title_bar = ctk.CTkFrame(
            self,
            fg_color=["#EEF0F7", "#1A2535"],
            corner_radius=0,
            height=36,
        )
        title_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        title_bar.grid_columnconfigure(1, weight=1)
        title_bar.grid_propagate(False)

        ctk.CTkLabel(
            title_bar,
            text="📋  运行日志",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12, weight="bold"),
            text_color=["#4B5563", "#9CA3AF"],
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=0, sticky="w")

        # Clear button
        self.clear_btn = ctk.CTkButton(
            title_bar,
            text="清空",
            width=48,
            height=22,
            corner_radius=4,
            font=small_font(),
            fg_color="transparent",
            hover_color=["#E5E7EB", "#2D3748"],
            text_color=["#6B7280", "#9CA3AF"],
            border_width=1,
            border_color=["#D1D5DB", "#4B5563"],
            command=self.clear,
        )
        self.clear_btn.grid(row=0, column=1, padx=10, pady=6, sticky="e")

        # Text area
        self.textbox = ctk.CTkTextbox(
            self,
            font=mono_font(),
            fg_color=["#F8F9FC", "#151E2B"],
            text_color=["#374151", "#A0AEC0"],
            wrap="word",
            corner_radius=0,
            border_width=0,
            scrollbar_button_color=["#D1D5DB", "#4B5563"],
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.textbox.configure(state="disabled")

    def append(self, msg: str):
        """Append a line to the log (call from any thread)."""
        self.after(0, self._append_safe, msg)

    def _append_safe(self, msg: str):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", msg + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self.after(0, self._clear_safe)

    def _clear_safe(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")


# ── Progress bar row ───────────────────────────────────────────────────────────

class ProgressRow(ctk.CTkFrame):
    """Thin progress bar + percentage label."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.bar = ctk.CTkProgressBar(
            self,
            height=8,
            corner_radius=4,
            fg_color=["#E2E5EE", "#374151"],
            progress_color=["#00B894", "#00C9A7"],
        )
        self.bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.bar.set(0)

        self.pct_label = ctk.CTkLabel(
            self,
            text="0%",
            width=38,
            font=small_font(),
            text_color=["#6B7280", "#9CA3AF"],
            anchor="e",
        )
        self.pct_label.grid(row=0, column=1, sticky="e")

    def set(self, value: float):
        """value: 0.0–1.0"""
        self.after(0, self._set_safe, value)

    def _set_safe(self, value: float):
        self.bar.set(value)
        self.pct_label.configure(text=f"{int(value * 100)}%")

    def reset(self):
        self.set(0.0)


# ── Labeled option row ─────────────────────────────────────────────────────────

class LabeledOption(ctk.CTkFrame):
    """Label + OptionMenu in a horizontal row with a subtle card background."""

    def __init__(self, parent, label, values, default=None, width=160, **kwargs):
        super().__init__(
            parent,
            fg_color=["#F2F4F8", "#1A2535"],
            corner_radius=8,
            border_width=1,
            border_color=["#E2E5EE", "#374151"],
            **kwargs,
        )

        ctk.CTkLabel(
            self,
            text=label,
            font=body_font(),
            text_color=["#374151", "#D1D5DB"],
            anchor="w",
        ).grid(row=0, column=0, padx=(12, 8), pady=8, sticky="w")

        self._var = ctk.StringVar(value=default or (values[0] if values else ""))
        self.menu = ctk.CTkOptionMenu(
            self,
            values=values,
            variable=self._var,
            width=width,
            height=32,
            corner_radius=6,
            font=body_font(),
            fg_color=["#FFFFFF", "#283548"],
            button_color=["#00B894", "#00C9A7"],
            button_hover_color=["#00A07E", "#00B894"],
            dropdown_fg_color=["#FFFFFF", "#283548"],
            dropdown_hover_color=["#F3F4F6", "#374151"],
            text_color=["#111827", "#F3F4F6"],
            dynamic_resizing=False,
        )
        self.menu.grid(row=0, column=1, padx=(0, 6), pady=6, sticky="w")

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(value)


# ── Labeled entry row ──────────────────────────────────────────────────────────

class LabeledEntry(ctk.CTkFrame):
    """Label + Entry in a horizontal row with a subtle card background."""

    def __init__(self, parent, label, placeholder="", width=130, **kwargs):
        super().__init__(
            parent,
            fg_color=["#F2F4F8", "#1A2535"],
            corner_radius=8,
            border_width=1,
            border_color=["#E2E5EE", "#374151"],
            **kwargs,
        )

        ctk.CTkLabel(
            self,
            text=label,
            font=body_font(),
            text_color=["#374151", "#D1D5DB"],
            anchor="w",
        ).grid(row=0, column=0, padx=(12, 8), pady=8, sticky="w")

        self._var = ctk.StringVar()
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self._var,
            placeholder_text=placeholder,
            width=width,
            height=32,
            corner_radius=6,
            font=body_font(),
            fg_color=["#FFFFFF", "#1F2937"],
            border_color=["#D1D5DB", "#4B5563"],
            text_color=["#111827", "#F3F4F6"],
        )
        self.entry.grid(row=0, column=1, padx=(0, 6), pady=6, sticky="w")

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(str(value))


# ── Start / Stop button ────────────────────────────────────────────────────────

class ActionButton(ctk.CTkButton):
    """The big 'Start Processing' / 'Stop' button."""

    def __init__(self, parent, start_text="⚡  开始处理", stop_text="⏹  停止", **kwargs):
        self._start_text = start_text
        self._stop_text = stop_text
        super().__init__(
            parent,
            text=start_text,
            height=48,
            corner_radius=10,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold"),
            fg_color=["#00B894", "#00C9A7"],
            hover_color=["#00A07E", "#00B894"],
            text_color="#FFFFFF",
            **kwargs,
        )
        self._running = False

    def set_running(self, running: bool):
        self._running = running
        if running:
            self.configure(
                text=self._stop_text,
                fg_color=["#EF4444", "#EF4444"],
                hover_color=["#DC2626", "#DC2626"],
            )
        else:
            self.configure(
                text=self._start_text,
                fg_color=["#00B894", "#00C9A7"],
                hover_color=["#00A07E", "#00B894"],
            )

    @property
    def running(self):
        return self._running


# ── Labeled CheckBox row ────────────────────────────────────────────────────────

class LabeledCheckBox(ctk.CTkFrame):
    """A label with a checkbox in a row."""

    def __init__(self, parent, label, default=False, **kwargs):
        super().__init__(
            parent,
            fg_color=["#F2F4F8", "#1A2535"],
            corner_radius=8,
            border_width=1,
            border_color=["#E2E5EE", "#374151"],
            **kwargs,
        )

        ctk.CTkLabel(
            self,
            text=label,
            font=body_font(),
            text_color=["#374151", "#D1D5DB"],
            anchor="w",
        ).grid(row=0, column=0, padx=(12, 8), pady=8, sticky="w")

        self._var = ctk.BooleanVar(value=default)
        self.check = ctk.CTkCheckBox(
            self,
            text="",
            variable=self._var,
            width=24,
            height=24,
            corner_radius=4,
            checkbox_width=20,
            checkbox_height=20,
            border_width=2,
            fg_color=["#00B894", "#00C9A7"],
            hover_color=["#00A07E", "#00B894"],
            border_color=["#D1D5DB", "#4B5563"],
        )
        self.check.grid(row=0, column=1, padx=(0, 6), pady=6, sticky="w")

    def configure(self, **kwargs):
        if "state" in kwargs:
            state = kwargs.pop("state")
            self.check.configure(state=state)
            if state == "disabled":
                self.configure(fg_color=["#E5E7EB", "#2D3748"])
            else:
                self.configure(fg_color=["#F2F4F8", "#1A2535"])
        super().configure(**kwargs)

    def get(self):
        return self._var.get()

    def set(self, value: bool):
        self._var.set(value)


# ── Labeled Slider row ─────────────────────────────────────────────────────────

class LabeledSlider(ctk.CTkFrame):
    """A label with a slider and value display in a row."""

    def __init__(self, parent, label, from_=0, to=100, number_of_steps=100, default=50, unit="", on_change=None, slider_width=200, **kwargs):
        super().__init__(
            parent,
            fg_color=["#F2F4F8", "#1A2535"],
            corner_radius=8,
            border_width=1,
            border_color=["#E2E5EE", "#374151"],
            **kwargs,
        )
        self._on_change_callback = on_change

        ctk.CTkLabel(
            self,
            text=label,
            font=body_font(),
            text_color=["#374151", "#D1D5DB"],
            anchor="w",
        ).grid(row=0, column=0, padx=(12, 8), pady=(8, 0), sticky="w")

        # Container for entry and unit
        self._val_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._val_frame.grid(row=0, column=1, padx=(0, 12), pady=(8, 0), sticky="e")

        self._val_entry = ctk.CTkEntry(
            self._val_frame,
            width=50,
            height=20,
            font=small_font(),
            text_color=["#00B894", "#00C9A7"],
            fg_color="transparent",
            border_width=0,
            justify="right"
        )
        self._val_entry.pack(side="left")
        self._val_entry.insert(0, f"{default}")
        
        # Unit label緊跟輸入框
        self._unit_lbl = ctk.CTkLabel(
            self._val_frame, text=unit, font=small_font(), text_color=["#9CA3AF", "#6B7280"]
        )
        self._unit_lbl.pack(side="left", padx=(2, 0))

        self._val_entry.bind("<Return>", lambda e: self._on_entry_change())
        self._val_entry.bind("<FocusOut>", lambda e: self._on_entry_change())

        self._var = ctk.DoubleVar(value=default)
        self.slider = ctk.CTkSlider(
            self,
            from_=from_,
            to=to,
            number_of_steps=number_of_steps,
            variable=self._var,
            width=slider_width,
            command=self._on_change,
            fg_color=["#E2E5EE", "#374151"],
            progress_color=["#00B894", "#00C9A7"],
            button_color=["#00B894", "#00C9A7"],
            button_hover_color=["#00A07E", "#00B894"],
        )
        self.slider.grid(row=1, column=0, columnspan=2, padx=12, pady=(4, 10), sticky="ew")
        self._unit = unit
        self._min_val = from_
        self._max_val = to

    def configure(self, **kwargs):
        if "state" in kwargs:
            state = kwargs.pop("state")
            self.slider.configure(state=state)
            self._val_entry.configure(state=state)
            if state == "disabled":
                self.configure(fg_color=["#E5E7EB", "#2D3748"])
            else:
                self.configure(fg_color=["#F2F4F8", "#1A2535"])
        super().configure(**kwargs)

    def _on_change(self, val):
        self._val_entry.delete(0, "end")
        self._val_entry.insert(0, str(int(val)))
        if self._on_change_callback:
            self._on_change_callback(int(val))

    def _on_entry_change(self):
        try:
            val = int(self._val_entry.get())
            val = max(self._min_val, min(self._max_val, val))
            self._var.set(val)
            self._val_entry.delete(0, "end")
            self._val_entry.insert(0, str(val))
            if self._on_change_callback:
                self._on_change_callback(val)
        except ValueError:
            self._val_entry.delete(0, "end")
            self._val_entry.insert(0, str(int(self._var.get())))

    def get(self):
        return int(self._var.get())

    def set(self, value):
        self._var.set(value)
        self._val_entry.delete(0, "end")
        self._val_entry.insert(0, str(int(value)))
