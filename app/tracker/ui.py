import re
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .constants import (
    APP_NAME,
    APP_VERSION,
    BUILTIN_ROUTES,
    DISPLAY_MODES,
    GYMS,
    REGIONS,
    REQUIRED_OTHER_TRAINERS,
)
from .core import canonical_leader, gym_for_leader, gym_label
from .engine import TrackerEngine
from .logs import ChatLiveTailer, auto_log_candidates
from .state import load_state, save_state
from .themes import THEMES


def normalise_compact_geometry(value):
    value = value or "560x450"
    match = re.match(r"^(\d+)x(\d+)(.*)$", value)
    if not match:
        return "560x450"
    width = max(540, int(match.group(1)))
    height = max(350, int(match.group(2)))
    return f"{width}x{height}{match.group(3)}"


def status_code(values):
    status = str(values[6])
    if status.startswith("READY"):
        return "READY"
    if status.startswith("COOLDOWN"):
        return "COOLDOWN"
    if status.startswith("WAITING"):
        return "WAITING"
    return "UNKNOWN"


class RouteEditor(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Custom Routes")
        self.geometry("860x520")
        self.minsize(760, 440)
        self.transient(app)
        self.grab_set()
        self.route_name = tk.StringVar()
        self.available_items = [(gym_label(region, gym, leader), leader) for region, gym, leader in GYMS]
        self.selected_leaders = []
        self._build()
        self._refresh_saved_routes()
        self._refresh_lists()
        app.apply_theme()

    def _build(self):
        head = tk.Frame(self)
        head.pack(fill="x", padx=12, pady=10)
        tk.Label(head, text="Route name").pack(side="left")
        tk.Entry(head, textvariable=self.route_name, width=28).pack(side="left", padx=(6, 10))
        ttk.Button(head, text="Save Route", command=self.save_route).pack(side="left")
        ttk.Button(head, text="Delete Saved", command=self.delete_route).pack(side="left", padx=6)

        saved = tk.Frame(self)
        saved.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(saved, text="Saved route").pack(side="left")
        self.saved_combo = ttk.Combobox(saved, state="readonly", width=30, style="Readable.TCombobox")
        self.saved_combo.pack(side="left", padx=(6, 10))
        self.saved_combo.bind("<<ComboboxSelected>>", self.load_saved_route)
        ttk.Button(saved, text="New / Clear", command=self.clear_route).pack(side="left")

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        left = tk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Available gyms").pack(anchor="w")
        self.available = tk.Listbox(left, exportselection=False)
        self.available.pack(fill="both", expand=True, pady=(4, 0))
        self.available.bind("<Double-1>", lambda _event: self.add_selected())

        middle = tk.Frame(body)
        middle.pack(side="left", fill="y", padx=10, pady=55)
        ttk.Button(middle, text="Add →", command=self.add_selected).pack(fill="x", pady=3)
        ttk.Button(middle, text="← Remove", command=self.remove_selected).pack(fill="x", pady=3)
        ttk.Separator(middle, orient="horizontal").pack(fill="x", pady=10)
        ttk.Button(middle, text="Move Up", command=lambda: self.move_selected(-1)).pack(fill="x", pady=3)
        ttk.Button(middle, text="Move Down", command=lambda: self.move_selected(1)).pack(fill="x", pady=3)

        right = tk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Route order").pack(anchor="w")
        self.route_list = tk.Listbox(right, exportselection=False)
        self.route_list.pack(fill="both", expand=True, pady=(4, 0))
        self.route_list.bind("<Double-1>", lambda _event: self.remove_selected())

    def _refresh_saved_routes(self):
        names = sorted(self.app.state_data.get("custom_routes", {}).keys(), key=str.lower)
        self.saved_combo["values"] = names
        if self.saved_combo.get() not in names:
            self.saved_combo.set("")

    def _refresh_lists(self):
        selected = set(self.selected_leaders)
        self.available.delete(0, "end")
        for label, leader in self.available_items:
            if leader not in selected:
                self.available.insert("end", label)
        self.route_list.delete(0, "end")
        for index, leader in enumerate(self.selected_leaders, 1):
            mapped = gym_for_leader(leader)
            label = gym_label(*mapped) if mapped else leader
            self.route_list.insert("end", f"{index:02d}. {label}")

    def _available_leader_at(self, index):
        selected = set(self.selected_leaders)
        remaining = [(label, leader) for label, leader in self.available_items if leader not in selected]
        return remaining[index][1] if 0 <= index < len(remaining) else None

    def add_selected(self):
        selection = self.available.curselection()
        if not selection:
            return
        leader = self._available_leader_at(selection[0])
        if leader and leader not in self.selected_leaders:
            self.selected_leaders.append(leader)
            self._refresh_lists()
            self.route_list.selection_set("end")

    def remove_selected(self):
        selection = self.route_list.curselection()
        if not selection:
            return
        index = selection[0]
        self.selected_leaders.pop(index)
        self._refresh_lists()
        if self.selected_leaders:
            self.route_list.selection_set(min(index, len(self.selected_leaders) - 1))

    def move_selected(self, delta):
        selection = self.route_list.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + delta
        if 0 <= new_index < len(self.selected_leaders):
            self.selected_leaders[index], self.selected_leaders[new_index] = self.selected_leaders[new_index], self.selected_leaders[index]
            self._refresh_lists()
            self.route_list.selection_set(new_index)
            self.route_list.see(new_index)

    def clear_route(self):
        self.route_name.set("")
        self.saved_combo.set("")
        self.selected_leaders = []
        self._refresh_lists()

    def load_saved_route(self, _event=None):
        name = self.saved_combo.get()
        route = self.app.state_data.get("custom_routes", {}).get(name)
        if route is None:
            return
        self.route_name.set(name)
        self.selected_leaders = [canonical_leader(leader) for leader in route if gym_for_leader(canonical_leader(leader))]
        self._refresh_lists()

    def save_route(self):
        name = self.route_name.get().strip()
        if not name:
            messagebox.showinfo(APP_NAME, "Give the route a name first.", parent=self)
            return
        if name in BUILTIN_ROUTES or name == "All gyms":
            messagebox.showinfo(APP_NAME, "That name is reserved for a built-in route.", parent=self)
            return
        if not self.selected_leaders:
            messagebox.showinfo(APP_NAME, "Add at least one gym to the route.", parent=self)
            return
        self.app.state_data.setdefault("custom_routes", {})[name] = self.selected_leaders[:]
        save_state(self.app.state_data)
        self.app.refresh_route_choices(select=name)
        self._refresh_saved_routes()
        self.saved_combo.set(name)
        messagebox.showinfo(APP_NAME, f"Saved route: {name}", parent=self)

    def delete_route(self):
        name = self.saved_combo.get() or self.route_name.get().strip()
        if not name or name not in self.app.state_data.get("custom_routes", {}):
            return
        if not messagebox.askyesno(APP_NAME, f"Delete custom route '{name}'?", parent=self):
            return
        self.app.state_data["custom_routes"].pop(name, None)
        if self.app.route_var.get() == name:
            self.app.route_var.set("All gyms")
        save_state(self.app.state_data)
        self.app.refresh_route_choices()
        self.clear_route()
        self._refresh_saved_routes()


class CompactWindow(tk.Toplevel):
    CONTROL_WIDTH = 38
    CONTROL_HEIGHT = 25

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.geometry(normalise_compact_geometry(app.state_data.get("compact_geometry")))
        self.minsize(540, 350)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._drag_dx = 0
        self._drag_dy = 0
        self._max_hover = False
        self._close_hover = False

        self.chrome = tk.Frame(self, bd=1, relief="solid")
        self.chrome.pack(fill="both", expand=True)
        self.dragbar = tk.Frame(self.chrome, height=30, cursor="fleur")
        self.dragbar.pack(fill="x")
        self.dragbar.pack_propagate(False)
        self.drag_title = tk.Label(self.dragbar, text="Gym Tracker", font=("Segoe UI Semibold", 10), cursor="fleur")
        self.drag_title.pack(side="left", padx=(8, 0))
        self.live_label = tk.Label(self.dragbar, textvariable=app.status_var, font=("Segoe UI", 8), cursor="fleur")
        self.live_label.pack(side="left", padx=(10, 0))

        # With side=right, packing Close first keeps it on the far-right edge.
        self.close_button = self._make_control(self._close_app, self._paint_close_button)
        self.close_button.pack(side="right", padx=(5, 6), pady=3)
        self.max_button = self._make_control(app.restore_full_view, self._paint_max_button)
        self.max_button.pack(side="right", pady=3)

        # Paint both controls immediately in their normal, inactive state.
        # During construction App.compact_window has not been assigned yet, so
        # App.apply_theme() cannot reliably reach this window on the first pass.
        self.paint_controls()

        for widget in (self.dragbar, self.drag_title, self.live_label):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)

        body = tk.Frame(self.chrome)
        body.pack(fill="both", expand=True, padx=8, pady=(7, 8))
        row1 = tk.Frame(body)
        row1.pack(fill="x", pady=(0, 5))
        tk.Label(row1, text="Character").pack(side="left")
        self.char_combo = ttk.Combobox(row1, textvariable=app.character_var, state="readonly", width=16, style="Readable.TCombobox")
        self.char_combo.pack(side="left", padx=(5, 12))
        self.char_combo.bind("<<ComboboxSelected>>", self._filters_changed)
        tk.Label(row1, text="Region").pack(side="left")
        self.region_combo = ttk.Combobox(row1, textvariable=app.region_var, state="readonly", width=10, values=REGIONS, style="Readable.TCombobox")
        self.region_combo.pack(side="left", padx=(5, 0))
        self.region_combo.bind("<<ComboboxSelected>>", self._filters_changed)

        row2 = tk.Frame(body)
        row2.pack(fill="x", pady=(0, 5))
        tk.Label(row2, text="Route").pack(side="left")
        self.route_combo = ttk.Combobox(row2, textvariable=app.route_var, state="readonly", width=35, style="Readable.TCombobox")
        self.route_combo.pack(side="left", padx=(5, 0), fill="x", expand=True)
        self.route_combo.bind("<<ComboboxSelected>>", self._filters_changed)

        row3 = tk.Frame(body)
        row3.pack(fill="x", pady=(0, 6))
        tk.Label(row3, textvariable=app.progress_var, font=("Segoe UI", 8)).pack(side="left")
        self.display_combo = ttk.Combobox(row3, textvariable=app.display_var, state="readonly", width=16, values=DISPLAY_MODES, style="Readable.TCombobox")
        self.display_combo.pack(side="right")
        self.display_combo.bind("<<ComboboxSelected>>", app.view_options_changed)
        tk.Label(row3, text="Display").pack(side="right", padx=(8, 4))

        table = tk.Frame(body)
        table.pack(fill="both", expand=True)
        columns = ("position", "gym", "cooldown", "rule")
        self.tree = ttk.Treeview(table, columns=columns, show="headings", selectmode="none", height=10)
        for column, label, width, anchor in [
            ("position", "#", 38, "center"), ("gym", "Gym", 180, "w"),
            ("cooldown", "Cooldown", 125, "center"), ("rule", "5-rule", 70, "center"),
        ]:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor, stretch=(column == "gym"))
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.refresh()
        app.apply_theme()

    def _make_control(self, command, painter):
        canvas = tk.Canvas(self.dragbar, width=self.CONTROL_WIDTH, height=self.CONTROL_HEIGHT, bd=1, relief="solid", highlightthickness=0, cursor="hand2", takefocus=False)
        canvas.bind("<Button-1>", lambda _event: command())
        canvas.bind("<Enter>", lambda _event: painter(True))
        canvas.bind("<Leave>", lambda _event: painter(False))
        return canvas

    def _paint_control_background(self, canvas, hovered):
        theme = self.app.theme()
        canvas.configure(bg=theme["selected"] if hovered else theme["heading"], highlightbackground=theme["border"])
        canvas.delete("all")
        return theme

    def _paint_max_button(self, hovered=False):
        self._max_hover = hovered
        theme = self._paint_control_background(self.max_button, hovered)
        self.max_button.create_rectangle(12, 6, 26, 19, outline=theme["text"], width=2)

    def _paint_close_button(self, hovered=False):
        self._close_hover = hovered
        theme = self._paint_control_background(self.close_button, hovered)
        self.close_button.create_line(13, 7, 25, 18, fill=theme["text"], width=2)
        self.close_button.create_line(25, 7, 13, 18, fill=theme["text"], width=2)

    def paint_controls(self):
        self._paint_max_button(self._max_hover)
        self._paint_close_button(self._close_hover)

    def _start_drag(self, event):
        self._drag_dx = event.x_root - self.winfo_x()
        self._drag_dy = event.y_root - self.winfo_y()

    def _drag(self, event):
        self.geometry(f"+{event.x_root - self._drag_dx}+{event.y_root - self._drag_dy}")

    def _close_app(self):
        self.app.on_close()

    def _filters_changed(self, _event=None):
        self.app.filters_changed()
        self.refresh()

    def refresh(self):
        try:
            self.char_combo["values"] = tuple(self.app.char_combo["values"])
            self.route_combo["values"] = tuple(self.app.route_combo["values"])
        except Exception:
            pass
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.app.tree.get_children():
            values = self.app.tree.item(item, "values")
            tags = self.app.tree.item(item, "tags")
            if len(values) >= 8:
                self.tree.insert("", "end", iid=item, values=(values[0], values[2], values[4], values[5]), tags=tags)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state_data = load_state()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(self.state_data.get("window", {}).get("geometry", "1100x650"))
        self.minsize(900, 520)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.tailer = None
        self.compact_window = None
        self.status_var = tk.StringVar(value="Not connected")
        self.character_var = tk.StringVar(value=self.state_data.get("selected_character", "All characters"))
        self.region_var = tk.StringVar(value=self.state_data.get("region_filter", "All"))
        self.route_var = tk.StringVar(value=self.state_data.get("route_selection", "All gyms"))
        self.display_var = tk.StringVar(value=self.state_data.get("display_filter", "Remaining"))
        self.hide_unknown_var = tk.BooleanVar(value=bool(self.state_data.get("hide_unknown", False)))
        self.theme_var = tk.StringVar(value=self.state_data.get("theme", "Dark"))
        if self.theme_var.get() not in THEMES:
            self.theme_var.set("Dark")
        self.progress_var = tk.StringVar(value="")
        self.engine = TrackerEngine(self.state_data, on_event=self.add_event, on_change=self.on_data_changed)
        self.make_styles()
        self.build_ui()
        self.refresh_route_choices()
        self.auto_configure_log_folder()
        self.refresh_characters()
        self.refresh_table()
        self.apply_theme()
        self.bind("<Control-m>", lambda _event: self.open_compact_view())
        self.after(500, self.tick)

    def theme(self):
        return THEMES.get(self.theme_var.get(), THEMES["Dark"])

    def make_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

    def build_ui(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(top, text="Gym Cooldown Info", font=("Segoe UI Semibold", 15)).pack(side="left")
        tk.Label(top, textvariable=self.status_var, font=("Segoe UI", 9)).pack(side="right")

        controls = tk.Frame(self)
        controls.pack(fill="x", padx=10, pady=(0, 5))
        tk.Label(controls, text="Character").pack(side="left")
        self.char_combo = ttk.Combobox(controls, textvariable=self.character_var, state="readonly", width=20, style="Readable.TCombobox")
        self.char_combo.pack(side="left", padx=(5, 12))
        self.char_combo.bind("<<ComboboxSelected>>", self.filters_changed)
        tk.Label(controls, text="Region").pack(side="left")
        self.region_combo = ttk.Combobox(controls, textvariable=self.region_var, state="readonly", width=11, values=REGIONS, style="Readable.TCombobox")
        self.region_combo.pack(side="left", padx=(5, 12))
        self.region_combo.bind("<<ComboboxSelected>>", self.filters_changed)
        ttk.Button(controls, text="Compact view", command=self.open_compact_view).pack(side="right", padx=(8, 0))
        ttk.Button(controls, text="Choose Log Folder", command=self.choose_log_folder).pack(side="right", padx=(6, 0))
        ttk.Button(controls, text="Replay Log File", command=self.replay_log).pack(side="right", padx=(6, 0))

        route_controls = tk.Frame(self)
        route_controls.pack(fill="x", padx=10, pady=(0, 5))
        tk.Label(route_controls, text="Route / order").pack(side="left")
        self.route_combo = ttk.Combobox(route_controls, textvariable=self.route_var, state="readonly", width=31, style="Readable.TCombobox")
        self.route_combo.pack(side="left", padx=(5, 8))
        self.route_combo.bind("<<ComboboxSelected>>", self.filters_changed)
        ttk.Button(route_controls, text="Manage Custom Routes…", command=lambda: RouteEditor(self)).pack(side="left")
        tk.Label(route_controls, text="Route filters + sorts the table.", font=("Segoe UI", 8)).pack(side="left", padx=10)

        self.view_controls = tk.Frame(self)
        self.view_controls.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(self.view_controls, textvariable=self.progress_var, font=("Segoe UI", 8)).pack(side="left")
        self.theme_combo = ttk.Combobox(self.view_controls, textvariable=self.theme_var, state="readonly", width=11, values=list(THEMES.keys()), style="Readable.TCombobox")
        self.theme_combo.pack(side="right")
        self.theme_combo.bind("<<ComboboxSelected>>", self.theme_changed)
        tk.Label(self.view_controls, text="Theme").pack(side="right", padx=(12, 4))
        self.display_combo = ttk.Combobox(self.view_controls, textvariable=self.display_var, state="readonly", width=19, values=DISPLAY_MODES, style="Readable.TCombobox")
        self.display_combo.pack(side="right")
        self.display_combo.bind("<<ComboboxSelected>>", self.view_options_changed)
        tk.Label(self.view_controls, text="Display").pack(side="right", padx=(10, 4))
        ttk.Checkbutton(self.view_controls, text="Hide unknown", variable=self.hide_unknown_var, command=self.view_options_changed).pack(side="right", padx=(10, 0))

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10)
        columns = ("position", "region", "gym", "leader", "cooldown", "rule", "last", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        labels = {"position": "#", "region": "Region", "gym": "Gym", "leader": "Leader", "cooldown": "Cooldown", "rule": "5-rule", "last": "Last Defeated", "status": "Status"}
        widths = {"position": 42, "region": 90, "gym": 165, "leader": 125, "cooldown": 125, "rule": 80, "last": 155, "status": 190}
        for column in columns:
            self.tree.heading(column, text=labels[column])
            self.tree.column(column, width=widths[column], anchor="center" if column in {"position", "cooldown", "rule"} else "w", stretch=(column in {"gym", "status"}))
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        manual = tk.Frame(self)
        manual.pack(fill="x", padx=10, pady=7)
        ttk.Button(manual, text="Mark Selected Defeated Now", command=self.manual_defeated).pack(side="left")
        ttk.Button(manual, text="Mark Selected Ready", command=self.manual_ready).pack(side="left", padx=6)
        ttk.Button(manual, text="Forget Selected", command=self.manual_forget).pack(side="left")
        tk.Label(manual, text="Unknown normal trainers are deliberately not counted until verified or learned from repeat wins.", font=("Segoe UI", 8)).pack(side="right")

        detector = tk.LabelFrame(self, text="Detector", font=("Segoe UI Semibold", 9), bd=1, relief="groove")
        detector.pack(fill="x", padx=10, pady=(0, 10))
        self.event_text = tk.Text(detector, height=6, relief="flat", font=("Consolas", 9), state="disabled")
        self.event_text.pack(fill="x", padx=6, pady=6)
        self.event_text.tag_configure("success", foreground="#9fd18b")
        self.event_text.tag_configure("warn", foreground="#f0c674")
        self.event_text.tag_configure("info", foreground="#dcdcdc")

    def apply_theme(self):
        if not self.winfo_exists():
            return
        theme = self.theme()
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background=theme["bg"], foreground=theme["text"])
        style.configure("TButton", background=theme["heading"], foreground=theme["text"], padding=6, bordercolor=theme["border"])
        style.map("TButton", background=[("active", theme["selected"])], foreground=[("active", theme["text"])])
        style.configure("TCheckbutton", background=theme["bg"], foreground=theme["text"])
        style.configure("TScrollbar", background=theme["heading"], troughcolor=theme["panel_dark"], bordercolor=theme["border"])
        style.configure("Treeview", background=theme["panel"], fieldbackground=theme["panel"], foreground=theme["text"], rowheight=26, borderwidth=0, font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", theme["selected"])], foreground=[("selected", theme["text"])])
        style.configure("Treeview.Heading", background=theme["heading"], foreground=theme["text"], relief="flat", font=("Segoe UI Semibold", 10))
        style.configure("Readable.TCombobox", fieldbackground=theme["field_bg"], background=theme["field_bg"], foreground=theme["field_fg"], arrowcolor=theme["field_fg"], padding=3)
        style.map("Readable.TCombobox", fieldbackground=[("readonly", theme["field_bg"])], foreground=[("readonly", theme["field_fg"])], selectbackground=[("readonly", theme["field_bg"])], selectforeground=[("readonly", theme["field_fg"])])
        self.option_add("*TCombobox*Listbox.background", theme["field_bg"])
        self.option_add("*TCombobox*Listbox.foreground", theme["field_fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", theme["selected"])
        self.option_add("*TCombobox*Listbox.selectForeground", theme["text"])
        self._theme_widget_tree(self, theme)
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self._theme_widget_tree(self.compact_window, theme)
            self.compact_window.paint_controls()
        self._retag_trees(self, theme)
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self._retag_trees(self.compact_window, theme)

    def _theme_widget_tree(self, widget, theme):
        try:
            if isinstance(widget, tk.LabelFrame):
                widget.configure(bg=theme["bg"], fg=theme["text"], highlightbackground=theme["border"])
            elif isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame)):
                widget.configure(bg=theme["bg"])
            elif isinstance(widget, tk.Label):
                foreground = theme["text"]
                textvariable = str(widget.cget("textvariable") or "")
                if textvariable in {str(self.status_var), str(self.progress_var)}:
                    foreground = theme["accent"]
                widget.configure(bg=theme["bg"], fg=foreground)
            elif isinstance(widget, tk.Text):
                widget.configure(bg=theme["panel_dark"], fg=theme["text"], insertbackground=theme["text"])
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=theme["panel_dark"], fg=theme["text"], selectbackground=theme["selected"], selectforeground=theme["text"], highlightbackground=theme["border"])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=theme["field_bg"], fg=theme["field_fg"], insertbackground=theme["field_fg"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._theme_widget_tree(child, theme)
        if isinstance(widget, CompactWindow):
            try:
                widget.chrome.configure(bg=theme["bg"], highlightbackground=theme["border"])
                widget.dragbar.configure(bg=theme["heading"])
                widget.drag_title.configure(bg=theme["heading"], fg=theme["text"])
                widget.live_label.configure(bg=theme["heading"], fg=theme["accent"])
            except tk.TclError:
                pass

    @staticmethod
    def _retag_trees(widget, theme):
        if isinstance(widget, ttk.Treeview):
            widget.tag_configure("next", background=theme["next_bg"], foreground=theme["text"])
            widget.tag_configure("unknown", foreground=theme["unknown"])
            widget.tag_configure("ready", foreground=theme["ready"])
            widget.tag_configure("waiting", foreground=theme["waiting"])
        for child in widget.winfo_children():
            App._retag_trees(child, theme)

    def theme_changed(self, _event=None):
        self.state_data["theme"] = self.theme_var.get()
        save_state(self.state_data)
        self.apply_theme()
        self.refresh_table()

    def auto_configure_log_folder(self):
        saved = self.state_data.get("log_folder")
        if saved and Path(saved).exists():
            self.start_watching(Path(saved))
            return
        candidates = auto_log_candidates()
        if candidates:
            self.state_data["log_folder"] = str(candidates[0])
            save_state(self.state_data)
            self.start_watching(candidates[0])
        else:
            self.status_var.set("Choose your PokeMMO log folder")

    def start_watching(self, folder: Path):
        if self.tailer:
            self.tailer.close()
        self.tailer = ChatLiveTailer(folder, self.engine, on_status=self.status_var.set)
        self.status_var.set("Looking for chat_*.log…")
        self.tailer.poll()

    def choose_log_folder(self):
        folder = filedialog.askdirectory(title="Choose PokeMMO logs folder")
        if not folder:
            return
        self.state_data["log_folder"] = folder
        save_state(self.state_data)
        self.start_watching(Path(folder))

    def replay_log(self):
        initial = self.state_data.get("log_folder") or str(Path.home())
        path = filedialog.askopenfilename(title="Replay a PokeMMO chat log", initialdir=initial, filetypes=[("PokeMMO chat logs", "chat*.log"), ("PokeMMO logs", "*.log"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.engine.replay_file(Path(path))
            self.refresh_characters()
            self.refresh_table()
            messagebox.showinfo(APP_NAME, "Replay complete. Previously processed victories are automatically de-duplicated.")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not replay log:\n{exc}")

    def add_event(self, ts, text, level="info"):
        self.event_text.configure(state="normal")
        self.event_text.insert("end", f"{ts.strftime('%H:%M:%S')}  {text}\n", level)
        self.event_text.see("end")
        self.event_text.configure(state="disabled")

    def on_data_changed(self):
        self.refresh_characters()
        self.refresh_table()

    def refresh_characters(self):
        characters = sorted(self.state_data.get("characters", {}).keys(), key=str.lower)
        values = ["All characters"] + characters
        self.char_combo["values"] = values
        if self.character_var.get() not in values:
            self.character_var.set(characters[-1] if characters else "All characters")
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self.compact_window.refresh()

    def selected_characters(self):
        selected = self.character_var.get()
        characters = self.state_data.get("characters", {})
        if selected == "All characters":
            return list(characters.items())
        if selected in characters:
            return [(selected, characters[selected])]
        return []

    def merged_record(self, leader):
        selected = self.selected_characters()
        if not selected:
            return None, None
        if len(selected) == 1:
            name, char = selected[0]
            return name, char.get("gyms", {}).get(leader)
        best = None
        best_name = None
        for name, char in selected:
            record = char.get("gyms", {}).get(leader)
            if not record:
                continue
            try:
                defeated_at = datetime.fromisoformat(record.get("defeated_at", ""))
            except Exception:
                defeated_at = datetime.min
            if best is None or defeated_at > best[0]:
                best = (defeated_at, record)
                best_name = name
        return best_name, best[1] if best else None

    def row_values(self, region, gym, leader, now):
        char_name, record = self.merged_record(leader)
        if not record:
            return (f"[ {region} ]", gym, leader, "—", "—", "—", "UNKNOWN")
        if record.get("manual_ready"):
            last = self.fmt_last(record.get("defeated_at"))
            status = "READY" + (f" ({char_name})" if self.character_var.get() == "All characters" else "")
            return (f"[ {region} ]", gym, leader, "Ready", "5/5", last, status)
        try:
            ready_at = datetime.fromisoformat(record["ready_at"])
        except Exception:
            ready_at = now
        remaining = ready_at - now
        other = min(REQUIRED_OTHER_TRAINERS, int(record.get("other_trainers", 0)))
        last = self.fmt_last(record.get("defeated_at"))
        if remaining.total_seconds() > 0:
            seconds = int(remaining.total_seconds())
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            cooldown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            status = "COOLDOWN"
        elif other < REQUIRED_OTHER_TRAINERS:
            needed = REQUIRED_OTHER_TRAINERS - other
            cooldown = f"Need {needed} battle" + ("s" if needed != 1 else "")
            status = "WAITING"
        else:
            cooldown = "Ready"
            status = "READY"
        if self.character_var.get() == "All characters" and char_name:
            status += f" ({char_name})"
        return (f"[ {region} ]", gym, leader, cooldown, f"{other}/5", last, status)

    @staticmethod
    def fmt_last(value):
        if not value:
            return "—"
        try:
            return datetime.fromisoformat(value).strftime("%d/%m %H:%M:%S")
        except Exception:
            return "—"

    def refresh_route_choices(self, select=None):
        custom = sorted(self.state_data.get("custom_routes", {}).keys(), key=str.lower)
        values = ["All gyms"] + list(BUILTIN_ROUTES.keys()) + custom
        self.route_combo["values"] = values
        desired = select or self.route_var.get()
        if desired not in values:
            desired = "All gyms"
        self.route_var.set(desired)
        self.state_data["route_selection"] = desired
        save_state(self.state_data)
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self.compact_window.route_combo["values"] = values
        if hasattr(self, "tree"):
            self.refresh_table()

    def filters_changed(self, _event=None):
        self.state_data["selected_character"] = self.character_var.get()
        self.state_data["region_filter"] = self.region_var.get()
        self.state_data["route_selection"] = self.route_var.get()
        save_state(self.state_data)
        self.refresh_table()

    def view_options_changed(self, _event=None):
        self.state_data["display_filter"] = self.display_var.get()
        self.state_data["hide_unknown"] = bool(self.hide_unknown_var.get())
        save_state(self.state_data)
        self.refresh_table()

    def current_route_leaders(self):
        selected = self.route_var.get()
        if selected == "All gyms":
            return None
        if selected in BUILTIN_ROUTES:
            return [canonical_leader(leader) for leader in BUILTIN_ROUTES[selected]]
        custom = self.state_data.get("custom_routes", {}).get(selected)
        return [canonical_leader(leader) for leader in custom] if custom is not None else None

    def ordered_gyms(self):
        route = self.current_route_leaders()
        if route is None:
            return GYMS[:]
        by_leader = {leader: (region, gym, leader) for region, gym, leader in GYMS}
        return [by_leader[leader] for leader in route if leader in by_leader]

    def _include_status(self, code):
        if self.hide_unknown_var.get() and code == "UNKNOWN":
            return False
        mode = self.display_var.get()
        if mode == "All":
            return True
        if mode == "Remaining":
            return code != "COOLDOWN"
        if mode == "Ready only":
            return code == "READY"
        if mode == "Cooldowns / blocked":
            return code in {"COOLDOWN", "WAITING"}
        if mode == "Known only":
            return code != "UNKNOWN"
        return True

    def refresh_table(self):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        region_filter = self.region_var.get()
        route_selected = self.route_var.get() != "All gyms"
        now = datetime.now()
        rows = []
        stats = {"READY": 0, "COOLDOWN": 0, "WAITING": 0, "UNKNOWN": 0}
        for position, (region, gym, leader) in enumerate(self.ordered_gyms(), 1):
            if region_filter != "All" and region != region_filter:
                continue
            values = self.row_values(region, gym, leader, now)
            code = status_code(values)
            stats[code] += 1
            rows.append((position, region, gym, leader, values, code))
        total = len(rows)
        self.progress_var.set(f"Ready {stats['READY']}/{total}  •  Waiting {stats['WAITING']}  •  Cooldown {stats['COOLDOWN']}  •  Unknown {stats['UNKNOWN']}")
        next_leader = None
        if route_selected:
            for _position, _region, _gym, leader, _values, code in rows:
                if code != "COOLDOWN":
                    next_leader = leader
                    break
        for position, _region, _gym, leader, values, code in rows:
            if not self._include_status(code):
                continue
            tags = []
            if code == "UNKNOWN":
                tags.append("unknown")
            elif code == "READY":
                tags.append("ready")
            elif code == "WAITING":
                tags.append("waiting")
            if leader == next_leader:
                tags.insert(0, "next")
            route_position = f"{position:02d}" if route_selected else ""
            self.tree.insert("", "end", iid=leader, values=(route_position,) + tuple(values), tags=tuple(tags))
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self.compact_window.refresh()

    def get_selected_leader(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def ensure_manual_character(self):
        selected = self.character_var.get()
        if selected != "All characters":
            return selected
        characters = sorted(self.state_data.get("characters", {}).keys(), key=str.lower)
        if len(characters) == 1:
            return characters[0]
        messagebox.showinfo(APP_NAME, "Choose a specific character first.")
        return None

    def manual_defeated(self):
        leader = self.get_selected_leader()
        player = self.ensure_manual_character()
        if leader and player:
            self.engine.record_victory(datetime.now(), player, f"Leader {leader}")

    def manual_ready(self):
        leader = self.get_selected_leader()
        player = self.ensure_manual_character()
        if not leader or not player:
            return
        char = self.engine.get_char(player)
        now = datetime.now()
        record = char["gyms"].setdefault(leader, {"defeated_at": now.isoformat(), "ready_at": now.isoformat(), "other_trainers": REQUIRED_OTHER_TRAINERS, "qualifying_events": [], "manual_ready": True})
        record["manual_ready"] = True
        record["other_trainers"] = REQUIRED_OTHER_TRAINERS
        save_state(self.state_data)
        self.refresh_table()

    def manual_forget(self):
        leader = self.get_selected_leader()
        player = self.ensure_manual_character()
        if not leader or not player:
            return
        char = self.state_data.get("characters", {}).get(player, {})
        char.get("gyms", {}).pop(leader, None)
        save_state(self.state_data)
        self.refresh_table()

    def open_compact_view(self):
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self.compact_window.deiconify()
            self.compact_window.lift()
            return
        self.compact_window = CompactWindow(self)
        self.withdraw()
        self.state_data["compact_mode"] = True
        save_state(self.state_data)

    def restore_full_view(self):
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self.state_data["compact_geometry"] = self.compact_window.geometry()
            self.compact_window.destroy()
        self.compact_window = None
        self.state_data["compact_mode"] = False
        save_state(self.state_data)
        self.deiconify()
        self.lift()
        self.apply_theme()

    def tick(self):
        try:
            if self.tailer:
                self.tailer.poll()
            self.refresh_table()
        except Exception as exc:
            self.status_var.set(f"Watcher error: {exc}")
        self.after(1000, self.tick)

    def on_close(self):
        if self.tailer:
            self.tailer.close()
        if self.compact_window is not None and self.compact_window.winfo_exists():
            self.state_data["compact_geometry"] = self.compact_window.geometry()
            self.compact_window.destroy()
            self.compact_window = None
        self.state_data.setdefault("window", {})["geometry"] = self.geometry()
        self.state_data["selected_character"] = self.character_var.get()
        self.state_data["region_filter"] = self.region_var.get()
        self.state_data["route_selection"] = self.route_var.get()
        self.state_data["display_filter"] = self.display_var.get()
        self.state_data["hide_unknown"] = bool(self.hide_unknown_var.get())
        self.state_data["theme"] = self.theme_var.get()
        self.state_data["compact_mode"] = False
        save_state(self.state_data)
        self.destroy()
