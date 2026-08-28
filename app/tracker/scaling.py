import re
import tkinter as tk
from tkinter import font as tkfont, ttk


UI_SCALE_FACTORS = {
    "0.85×": 0.85,
    "1.0×": 1.0,
    "1.25×": 1.25,
    "1.5×": 1.5,
    "1.75×": 1.75,
    "2.0×": 2.0,
}
DEFAULT_UI_SCALE = "1.0×"


def normalise_scale(value):
    if value in UI_SCALE_FACTORS:
        return value
    try:
        numeric = float(str(value).replace("×", "").strip())
    except Exception:
        return DEFAULT_UI_SCALE
    return min(UI_SCALE_FACTORS, key=lambda label: abs(UI_SCALE_FACTORS[label] - numeric))


def factor_for(app):
    var = getattr(app, "ui_scale_var", None)
    value = var.get() if var is not None else app.state_data.get("ui_scale", DEFAULT_UI_SCALE)
    return UI_SCALE_FACTORS.get(normalise_scale(value), 1.0)


def scaled(value, factor, minimum=1):
    return max(minimum, int(round(value * factor)))


def create_font(root, **options):
    """Create a tkinter.font.Font using Font's `root` argument.

    tkinter.font.Font does not accept `master` as the Tk owner. Keeping font
    construction behind this helper prevents Windows startup regressions where
    `master=` is interpreted as an invalid Tcl font option.
    """
    return tkfont.Font(root=root, **options)


class UIScalingController:
    """Explicit app-controlled scaling without changing Tk's global DPI factor."""

    def __init__(self, app):
        self.app = app
        initial = normalise_scale(app.state_data.get("ui_scale", DEFAULT_UI_SCALE))
        self.scale_var = tk.StringVar(master=app, value=initial)
        app.ui_scale_var = self.scale_var
        app.ui_scale_factor = lambda: factor_for(app)
        app.scale_px = lambda value, minimum=1: scaled(value, factor_for(app), minimum)
        self._base_fonts = {}
        self._base_layout = {}
        self._last_factor = factor_for(app)
        self._map_jobs = {}
        self._install_selector()
        self._capture_tree(app)
        self._capture_full_layout(app)
        self._apply_all(resize_window=False)
        self.scale_var.trace_add("write", self._scale_changed)
        # New Toplevels (route editor, earnings window, compact view) are picked
        # up automatically when mapped and receive the same font/control scale.
        app.bind_all("<Map>", self._mapped, add="+")
        app._scaling_controller = self

    def _install_selector(self):
        frame = self.app.view_controls
        theme_label = None
        for child in frame.winfo_children():
            if isinstance(child, tk.Label):
                try:
                    if child.cget("text") == "Theme":
                        theme_label = child
                        break
                except tk.TclError:
                    pass

        # Re-pack Theme so UI Scale can sit immediately to its left while Theme
        # remains the right-most setup preference.
        if theme_label is not None:
            self.app.theme_combo.pack_forget()
            theme_label.pack_forget()
            self.app.theme_combo.pack(side="right")
            theme_label.pack(side="right", padx=(12, 4))

        self.scale_combo = ttk.Combobox(
            frame,
            textvariable=self.scale_var,
            state="readonly",
            width=7,
            values=tuple(UI_SCALE_FACTORS.keys()),
            style="Readable.TCombobox",
        )
        self.scale_combo.pack(side="right")
        self.scale_label = tk.Label(frame, text="UI Scale")
        self.scale_label.pack(side="right", padx=(12, 4))

    def _walk(self, root):
        stack = [root]
        while stack:
            widget = stack.pop()
            yield widget
            try:
                stack.extend(widget.winfo_children())
            except tk.TclError:
                pass

    def _font_details(self, widget):
        try:
            spec = widget.cget("font")
        except (tk.TclError, AttributeError):
            return None
        try:
            font = create_font(self.app, font=spec)
            actual = font.actual()
            size = int(actual.get("size", 0))
            if not size:
                return None
            return {
                "family": actual.get("family", "Segoe UI"),
                "size": abs(size),
                "weight": actual.get("weight", "normal"),
                "slant": actual.get("slant", "roman"),
                "underline": bool(actual.get("underline", False)),
                "overstrike": bool(actual.get("overstrike", False)),
            }
        except tk.TclError:
            return None

    def _capture_tree(self, root):
        for widget in self._walk(root):
            key = str(widget)
            if key in self._base_fonts:
                continue
            details = self._font_details(widget)
            if details is not None:
                self._base_fonts[key] = (widget, details)

    def _parse_padding(self, value):
        try:
            parts = self.app.tk.splitlist(value)
        except Exception:
            parts = (value,)
        parsed = []
        for part in parts:
            try:
                parsed.append(int(round(float(str(part)))))
            except Exception:
                return None
        return tuple(parsed) if parsed else None

    def _capture_full_layout(self, root):
        """Capture baseline Full-view pack/grid padding once at 1.0x geometry.

        Compact and other secondary windows already construct themselves with
        scale-aware dimensions, so they are deliberately excluded here.
        """
        stack = [root]
        while stack:
            widget = stack.pop()
            if widget is not root and isinstance(widget, tk.Toplevel):
                continue
            try:
                manager = widget.winfo_manager()
                if manager == "pack":
                    info = widget.pack_info()
                    config = {}
                    for key in ("padx", "pady", "ipadx", "ipady"):
                        if key in info:
                            parsed = self._parse_padding(info[key])
                            if parsed is not None:
                                config[key] = parsed
                    if config:
                        self._base_layout[str(widget)] = (widget, "pack", config)
                elif manager == "grid":
                    info = widget.grid_info()
                    config = {}
                    for key in ("padx", "pady", "ipadx", "ipady"):
                        if key in info:
                            parsed = self._parse_padding(info[key])
                            if parsed is not None:
                                config[key] = parsed
                    if config:
                        self._base_layout[str(widget)] = (widget, "grid", config)
                stack.extend(widget.winfo_children())
            except tk.TclError:
                pass

    def _scaled_padding(self, values, factor):
        scaled_values = tuple(scaled(value, factor, 0) for value in values)
        if len(scaled_values) == 1:
            return scaled_values[0]
        return scaled_values

    def _apply_full_layout_padding(self):
        factor = factor_for(self.app)
        dead = []
        for key, (widget, manager, config) in self._base_layout.items():
            try:
                if not widget.winfo_exists():
                    dead.append(key)
                    continue
                mapped = {
                    option: self._scaled_padding(values, factor)
                    for option, values in config.items()
                }
                if manager == "pack":
                    widget.pack_configure(**mapped)
                elif manager == "grid":
                    widget.grid_configure(**mapped)
            except (tk.TclError, AttributeError):
                pass
        for key in dead:
            self._base_layout.pop(key, None)

    def _apply_widget_fonts(self):
        factor = factor_for(self.app)
        dead = []
        for key, (widget, details) in self._base_fonts.items():
            try:
                if not widget.winfo_exists():
                    dead.append(key)
                    continue
                size = max(7, scaled(details["size"], factor))
                font = create_font(
                    self.app,
                    family=details["family"],
                    size=size,
                    weight=details["weight"],
                    slant=details["slant"],
                    underline=details["underline"],
                    overstrike=details["overstrike"],
                )
                widget.configure(font=font)
                # Keep a Python reference; otherwise Tk named fonts can disappear.
                widget._ui_scaled_font = font
            except (tk.TclError, AttributeError):
                pass
        for key in dead:
            self._base_fonts.pop(key, None)

    def _apply_styles(self):
        factor = factor_for(self.app)
        theme = self.app.theme()
        style = ttk.Style(self.app)
        style.configure(
            "TButton",
            font=("Segoe UI", scaled(9, factor, 7)),
            padding=scaled(6, factor, 3),
        )
        style.configure("TCheckbutton", font=("Segoe UI", scaled(9, factor, 7)))
        style.configure(
            "Readable.TCombobox",
            font=("Segoe UI", scaled(9, factor, 7)),
            padding=(scaled(4, factor, 2), scaled(3, factor, 2)),
            arrowsize=scaled(14, factor, 11),
        )
        style.configure(
            "Treeview",
            font=("Segoe UI", scaled(10, factor, 8)),
            rowheight=scaled(40, factor, 28),
        )
        style.configure(
            "Treeview.Heading",
            background=theme["heading"],
            foreground=theme["text"],
            font=("Segoe UI Semibold", scaled(10, factor, 8)),
        )
        style.configure(
            "Compact.Treeview",
            font=("Segoe UI", scaled(9, factor, 7)),
            rowheight=scaled(27, factor, 22),
        )
        style.configure(
            "Compact.Treeview.Heading",
            background=theme["heading"],
            foreground=theme["text"],
            font=("Segoe UI Semibold", scaled(9, factor, 7)),
        )

    def _apply_comboboxes(self, root=None):
        """ttk Comboboxes need direct font/arrow sizing on Windows.

        Styling Readable.TCombobox alone is not sufficient on every Windows DPI
        configuration; assigning the font to each widget makes the field text,
        list choice and physical control height visibly follow UI Scale.
        """
        factor = factor_for(self.app)
        font = create_font(
            self.app,
            family="Segoe UI",
            size=scaled(9, factor, 7),
        )
        root = root or self.app
        for widget in self._walk(root):
            if isinstance(widget, ttk.Combobox):
                try:
                    widget.configure(font=font)
                    widget._ui_combo_font = font
                except tk.TclError:
                    pass
        try:
            self.app.option_add("*TCombobox*Listbox.font", str(font))
        except tk.TclError:
            pass

    def _apply_known_top_labels(self):
        factor = factor_for(self.app)
        for widget in self._walk(self.app):
            if not isinstance(widget, tk.Label):
                continue
            try:
                text = str(widget.cget("text") or "")
                textvariable = str(widget.cget("textvariable") or "")
                if text in {"Character", "Region", "Route / order", "Display", "Theme", "UI Scale"}:
                    widget.configure(font=("Segoe UI", scaled(9, factor, 7)))
                elif text == "Route filters + sorts the table.":
                    widget.configure(font=("Segoe UI", scaled(8, factor, 7)))
                elif textvariable == str(self.app.status_var):
                    widget.configure(font=("Segoe UI", scaled(9, factor, 7)))
            except tk.TclError:
                pass

    def _apply_component_scaling(self):
        factor = factor_for(self.app)
        presentation = getattr(self.app, "_presentation", None)
        if presentation is not None and hasattr(presentation, "apply_scale"):
            presentation.apply_scale(factor)
        earnings = getattr(self.app, "_earnings_controller", None)
        if earnings is not None and hasattr(earnings, "apply_scale"):
            earnings.apply_scale(factor)

    def _apply_full_table_dimensions(self):
        factor = factor_for(self.app)
        tree = self.app.tree
        try:
            tree.column(
                "#0",
                width=scaled(46, factor, 36),
                minwidth=scaled(46, factor, 36),
                stretch=False,
                anchor="center",
            )
            bases = {
                "position": 42,
                "region": 88,
                "gym": 140,
                "leader": 120,
                "cooldown": 118,
                "rule": 72,
                "last": 150,
                "status": 190,
            }
            stretch = {"region", "gym", "leader", "last", "status"}
            for column, base in bases.items():
                width = scaled(base, factor, 34)
                tree.column(
                    column,
                    width=width,
                    minwidth=width,
                    stretch=(column in stretch),
                    anchor="center",
                )
        except tk.TclError:
            pass

    def _screen_limited_minimum(self, factor):
        try:
            screen_width = self.app.winfo_screenwidth()
            screen_height = self.app.winfo_screenheight()
        except tk.TclError:
            screen_width, screen_height = 1920, 1080
        width = min(scaled(900, factor, 760), max(760, screen_width - 80))
        height = min(scaled(520, factor, 440), max(440, screen_height - 120))
        return width, height

    def _resize_main_window(self, old_factor, new_factor):
        if old_factor <= 0 or abs(old_factor - new_factor) < 0.001:
            return
        try:
            if self.app.state() != "normal":
                return
            self.app.update_idletasks()
            width = self.app.winfo_width()
            height = self.app.winfo_height()
            x = self.app.winfo_x()
            y = self.app.winfo_y()
            ratio = new_factor / old_factor
            min_width, min_height = self._screen_limited_minimum(new_factor)
            max_width = max(min_width, self.app.winfo_screenwidth() - 40)
            max_height = max(min_height, self.app.winfo_screenheight() - 80)
            new_width = min(max_width, max(min_width, int(round(width * ratio))))
            new_height = min(max_height, max(min_height, int(round(height * ratio))))
            self.app.geometry(f"{new_width}x{new_height}+{x}+{y}")
        except tk.TclError:
            pass

    def _reset_compact_geometry(self):
        factor = factor_for(self.app)
        value = self.app.state_data.get("compact_geometry", "")
        match = re.match(r"^(\d+)x(\d+)(.*)$", value or "")
        position = match.group(3) if match else ""
        self.app.state_data["compact_geometry"] = (
            f"{scaled(440, factor, 410)}x{scaled(420, factor, 320)}{position}"
        )

    def _apply_all(self, resize_window=True):
        self._capture_tree(self.app)
        self._apply_widget_fonts()
        self._apply_styles()
        self._apply_comboboxes(self.app)
        self._apply_known_top_labels()
        self._apply_full_layout_padding()
        self._apply_component_scaling()
        self._apply_full_table_dimensions()
        try:
            factor = factor_for(self.app)
            self.app.minsize(*self._screen_limited_minimum(factor))
        except tk.TclError:
            pass

        if getattr(self.app, "_presentation", None) is not None:
            try:
                self.app._presentation._apply_tree_style()
                # The presentation style pass owns theme/hover state; restore
                # explicit scale values afterwards.
                self._apply_styles()
            except Exception:
                pass
        if getattr(self.app, "_leader_art_controller", None) is not None:
            try:
                self.app._leader_art_controller.rebuild()
                self._apply_styles()
                self._apply_full_table_dimensions()
            except Exception:
                pass

        new_factor = factor_for(self.app)
        if resize_window:
            self._resize_main_window(self._last_factor, new_factor)
            self._reset_compact_geometry()
        self._last_factor = new_factor

    def apply_to_window(self, window):
        self._capture_tree(window)
        self._apply_widget_fonts()
        self._apply_styles()
        self._apply_comboboxes(window)
        # Give purpose-built secondary windows proportionate minimum sizes.
        factor = factor_for(self.app)
        try:
            title = window.title()
            if title == "Earnings Calculator":
                window.minsize(scaled(610, factor, 520), scaled(430, factor, 360))
            elif title == "Custom Routes":
                window.minsize(scaled(760, factor, 650), scaled(440, factor, 380))
        except tk.TclError:
            pass

    def _apply_mapped(self, key, top):
        self._map_jobs.pop(key, None)
        try:
            if top.winfo_exists():
                self.apply_to_window(top)
        except tk.TclError:
            pass

    def _mapped(self, event):
        try:
            top = event.widget.winfo_toplevel()
            key = str(top)
        except Exception:
            return
        if key in self._map_jobs:
            return
        try:
            self._map_jobs[key] = self.app.after_idle(self._apply_mapped, key, top)
        except tk.TclError:
            pass

    def _scale_changed(self, *_args):
        value = normalise_scale(self.scale_var.get())
        if value != self.scale_var.get():
            self.scale_var.set(value)
            return
        self.app.state_data["ui_scale"] = value
        from .state import save_state

        save_state(self.app.state_data)
        self._apply_all(resize_window=True)
        # apply_theme() rewrites ttk colour/padding style values; restore the
        # scale-aware geometry afterwards so Theme changes and UI Scale agree.
        self.app.apply_theme()
        self._apply_styles()
        self._apply_comboboxes(self.app)
        self._apply_known_top_labels()
        self._apply_component_scaling()


def install_scaling(app):
    app._scaling_controller = UIScalingController(app)
    return app._scaling_controller
