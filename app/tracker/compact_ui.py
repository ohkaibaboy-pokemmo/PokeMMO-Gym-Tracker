import re
import tkinter as tk
from tkinter import ttk

from .constants import DISPLAY_MODES, REGIONS
from .state import save_state


COMPACT_LAYOUT_VERSION = 5
DEFAULT_WIDTH = 440
DEFAULT_HEIGHT = 440
MIN_WIDTH = 410
MIN_HEIGHT = 350

_PROGRESS_RE = re.compile(
    r"Ready\s+(?P<ready>\d+)/(?P<total>\d+)\s+•\s+"
    r"Waiting\s+(?P<waiting>\d+)\s+•\s+"
    r"Cooldown\s+(?P<cooldown>\d+)\s+•\s+"
    r"Unknown\s+(?P<unknown>\d+)",
    re.IGNORECASE,
)


def _factor(app):
    getter = getattr(app, "ui_scale_factor", None)
    if callable(getter):
        try:
            return float(getter())
        except Exception:
            pass
    return 1.0


def _s(app, value, minimum=1):
    return max(minimum, int(round(value * _factor(app))))


def _compact_geometry(app):
    """Return compact geometry and migrate older compact layouts once."""
    default_width = _s(app, DEFAULT_WIDTH, MIN_WIDTH)
    default_height = _s(app, DEFAULT_HEIGHT, MIN_HEIGHT)
    min_width = _s(app, MIN_WIDTH, MIN_WIDTH)
    min_height = _s(app, MIN_HEIGHT, MIN_HEIGHT)

    value = app.state_data.get("compact_geometry") or f"{default_width}x{default_height}"
    match = re.match(r"^(\d+)x(\d+)(.*)$", value)
    if not match:
        width, height, position = default_width, default_height, ""
    else:
        width = int(match.group(1))
        height = int(match.group(2))
        position = match.group(3)

    layout_version = int(app.state_data.get("compact_layout_version", 1) or 1)
    if layout_version < COMPACT_LAYOUT_VERSION:
        width = default_width
        height = default_height
        app.state_data["compact_layout_version"] = COMPACT_LAYOUT_VERSION
        app.state_data["compact_geometry"] = f"{width}x{height}{position}"
        save_state(app.state_data)

    width = max(min_width, width)
    height = max(min_height, height)
    return f"{width}x{height}{position}"


def _as_dollar(value):
    value = str(value or "0").strip()
    if value.startswith("¥"):
        return "$" + value[1:]
    if value.startswith("$"):
        return value
    if value == "—":
        return value
    return "$" + value


def compact_progress_values(value):
    """Return Ready/Waiting/Cooldown/Unknown/Total from shared progress text."""
    match = _PROGRESS_RE.search(str(value or ""))
    if not match:
        return {
            "ready": "0",
            "waiting": "0",
            "cooldown": "0",
            "unknown": "0",
            "total": "0",
        }
    return match.groupdict()


class CompactWindow(tk.Toplevel):
    """Always-on-top v0.6 mini dashboard for active reruns.

    Compact shares Full view's visual language while prioritising the route queue.
    Filters stay small, status information is intentionally glanceable, and most
    of the available height belongs to the live gym list.
    """

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.scale_factor = _factor(app)
        self._scale = lambda value, minimum=1: max(
            minimum, int(round(value * self.scale_factor))
        )
        self.control_width = self._scale(34, 30)
        self.control_height = self._scale(23, 20)

        self.geometry(_compact_geometry(app))
        self.minsize(
            self._scale(MIN_WIDTH, MIN_WIDTH),
            self._scale(MIN_HEIGHT, MIN_HEIGHT),
        )
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._drag_dx = 0
        self._drag_dy = 0
        self._max_hover = False
        self._close_hover = False

        self.ready_var = tk.StringVar(master=self, value="0")
        self.waiting_var = tk.StringVar(master=self, value="0")
        self.cooldown_var = tk.StringVar(master=self, value="0")
        self.unknown_var = tk.StringVar(master=self, value="0")
        self.run_money_var = tk.StringVar(master=self, value="$0")
        self.live_short_var = tk.StringVar(master=self, value="● LIVE")

        self.chrome = tk.Frame(self, bd=0, highlightthickness=1)
        self.chrome.pack(fill="both", expand=True)

        self._build_titlebar()
        self._build_body()

        self._configure_compact_style()
        self.refresh()
        app.apply_theme()
        # App.apply_theme cannot reliably reach the new Toplevel until App has
        # assigned app.compact_window. Restore purpose-built card colours here.
        self._apply_dashboard_theme()
        self.paint_controls()
        self.after_idle(self._resize_table_columns)

    def _build_titlebar(self):
        self.dragbar = tk.Frame(
            self.chrome,
            height=self._scale(30, 26),
            cursor="fleur",
        )
        self.dragbar.pack(fill="x")
        self.dragbar.pack_propagate(False)

        self.drag_title = tk.Label(
            self.dragbar,
            text="Gym Tracker",
            font=("Segoe UI Semibold", 10),
            cursor="fleur",
        )
        self.drag_title.pack(side="left", padx=(self._scale(9), 0))

        self.live_label = tk.Label(
            self.dragbar,
            textvariable=self.live_short_var,
            font=("Segoe UI Semibold", 7),
            cursor="fleur",
        )
        self.live_label.pack(side="left", padx=(self._scale(8), 0))

        self.close_button = self._make_control(
            self._close_app,
            self._paint_close_button,
        )
        self.close_button.pack(
            side="right",
            padx=(self._scale(4), self._scale(5)),
            pady=self._scale(3),
        )
        self.max_button = self._make_control(
            self.app.restore_full_view,
            self._paint_max_button,
        )
        self.max_button.pack(side="right", pady=self._scale(3))

        for widget in (self.dragbar, self.drag_title, self.live_label):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)

    def _build_body(self):
        self.body = tk.Frame(self.chrome)
        self.body.pack(
            fill="both",
            expand=True,
            padx=self._scale(7),
            pady=(self._scale(5), self._scale(7)),
        )

        self._build_filter_card()
        self._build_status_card()
        self._build_route_card()

    def _build_filter_card(self):
        self.filter_card = tk.Frame(self.body, bd=0, highlightthickness=1)
        self.filter_card.pack(fill="x", pady=(0, self._scale(5)))

        self.filters = tk.Frame(self.filter_card, bd=0)
        self.filters.pack(
            fill="x",
            padx=self._scale(7),
            pady=self._scale(6),
        )
        self.filters.columnconfigure(1, weight=3, uniform="compact_fields")
        self.filters.columnconfigure(3, weight=2, uniform="compact_fields")

        self.filter_labels = []

        def filter_label(text, row, column):
            label = tk.Label(
                self.filters,
                text=text,
                anchor="e",
                font=("Segoe UI", 8),
            )
            label.grid(
                row=row,
                column=column,
                sticky="e",
                padx=(0, self._scale(4)),
                pady=(0, self._scale(4)) if row == 0 else 0,
            )
            self.filter_labels.append(label)
            return label

        filter_label("Character", 0, 0)
        self.char_combo = ttk.Combobox(
            self.filters,
            textvariable=self.app.character_var,
            state="readonly",
            style="Readable.TCombobox",
        )
        self.char_combo.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, self._scale(8)),
            pady=(0, self._scale(4)),
        )
        self.char_combo.bind("<<ComboboxSelected>>", self._filters_changed)

        filter_label("Region", 0, 2)
        self.region_combo = ttk.Combobox(
            self.filters,
            textvariable=self.app.region_var,
            state="readonly",
            values=REGIONS,
            style="Readable.TCombobox",
        )
        self.region_combo.grid(
            row=0,
            column=3,
            sticky="ew",
            pady=(0, self._scale(4)),
        )
        self.region_combo.bind("<<ComboboxSelected>>", self._filters_changed)

        filter_label("Route", 1, 0)
        self.route_combo = ttk.Combobox(
            self.filters,
            textvariable=self.app.route_var,
            state="readonly",
            style="Readable.TCombobox",
        )
        self.route_combo.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, self._scale(8)),
        )
        self.route_combo.bind("<<ComboboxSelected>>", self._filters_changed)

        filter_label("Display", 1, 2)
        self.display_combo = ttk.Combobox(
            self.filters,
            textvariable=self.app.display_var,
            state="readonly",
            values=DISPLAY_MODES,
            style="Readable.TCombobox",
        )
        self.display_combo.grid(row=1, column=3, sticky="ew")
        self.display_combo.bind(
            "<<ComboboxSelected>>",
            self.app.view_options_changed,
        )

    def _build_status_card(self):
        self.status_card = tk.Frame(self.body, bd=0, highlightthickness=1)
        self.status_card.pack(fill="x", pady=(0, self._scale(5)))

        # Compact metrics are deliberately one-line tiles. They keep the useful
        # dashboard colour coding while giving the route queue most of the height.
        self.metrics = tk.Frame(self.status_card, bd=0)
        self.metrics.pack(
            fill="x",
            padx=self._scale(5),
            pady=(self._scale(5), self._scale(3)),
        )
        for column in range(4):
            self.metrics.columnconfigure(column, weight=1, uniform="compact_status")

        specs = (
            ("ready", "READY", self.ready_var),
            ("waiting", "WAIT", self.waiting_var),
            ("cooldown", "CD", self.cooldown_var),
            ("unknown", "UNKNOWN", self.unknown_var),
        )
        self.metric_widgets = {}
        for column, (key, caption_text, variable) in enumerate(specs):
            tile = tk.Frame(self.metrics, bd=0, highlightthickness=1)
            tile.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0, self._scale(3)) if column < 3 else 0,
            )

            caption = tk.Label(
                tile,
                text=caption_text,
                font=("Segoe UI Semibold", 6),
                anchor="w",
            )
            caption.pack(
                side="left",
                padx=(self._scale(5), self._scale(2)),
                pady=self._scale(4),
            )

            value = tk.Label(
                tile,
                textvariable=variable,
                font=("Segoe UI Semibold", 10),
                anchor="e",
            )
            value.pack(
                side="right",
                padx=(self._scale(2), self._scale(5)),
                pady=self._scale(3),
            )
            self.metric_widgets[key] = {
                "frame": tile,
                "caption": caption,
                "value": value,
            }

        self.run_strip = tk.Frame(self.status_card, bd=0)
        self.run_strip.pack(
            fill="x",
            padx=self._scale(7),
            pady=(0, self._scale(4)),
        )
        self.run_caption = tk.Label(
            self.run_strip,
            text="RUN",
            font=("Segoe UI Semibold", 6),
            anchor="w",
        )
        self.run_caption.pack(side="left")

        self.money_group = tk.Frame(self.run_strip, bd=0)
        self.money_group.pack(side="right")
        self.coin_icon = tk.Canvas(
            self.money_group,
            width=self._scale(15, 13),
            height=self._scale(15, 13),
            bd=0,
            highlightthickness=0,
            takefocus=False,
        )
        self.coin_icon.pack(side="left", padx=(0, self._scale(2)))
        self.run_money = tk.Label(
            self.money_group,
            textvariable=self.run_money_var,
            font=("Segoe UI Semibold", 9),
            anchor="e",
        )
        self.run_money.pack(side="left")

    def _build_route_card(self):
        self.route_card = tk.Frame(self.body, bd=0, highlightthickness=1)
        self.route_card.pack(fill="both", expand=True)

        self.route_header = tk.Frame(self.route_card, bd=0)
        self.route_header.pack(
            fill="x",
            padx=self._scale(8),
            pady=(self._scale(5), self._scale(4)),
        )
        self.route_title = tk.Label(
            self.route_header,
            text="Route queue",
            font=("Segoe UI Semibold", 10),
            anchor="w",
        )
        self.route_title.pack(side="left")
        self.route_name = tk.Label(
            self.route_header,
            textvariable=self.app.route_var,
            width=24,
            font=("Segoe UI", 7),
            anchor="e",
        )
        self.route_name.pack(side="right")

        self.table = tk.Frame(self.route_card, bd=0)
        self.table.pack(
            fill="both",
            expand=True,
            padx=self._scale(6),
            pady=(0, self._scale(6)),
        )
        columns = ("position", "gym", "cooldown", "rule")
        self.tree = ttk.Treeview(
            self.table,
            columns=columns,
            show="headings",
            selectmode="none",
            height=11,
            style="Compact.Treeview",
        )
        for column, label, width in [
            ("position", "#", self._scale(34, 30)),
            ("gym", "Gym", self._scale(150, 125)),
            ("cooldown", "Cooldown", self._scale(104, 90)),
            ("rule", "5-rule", self._scale(60, 52)),
        ]:
            self.tree.heading(column, text=label, anchor="center")
            self.tree.column(
                column,
                width=width,
                minwidth=width,
                anchor="center",
                stretch=False,
            )
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(
            self.table,
            orient="vertical",
            command=self.tree.yview,
        )
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.bind("<Configure>", self._resize_table_columns, add="+")

    def _refresh_live(self):
        status = str(self.app.status_var.get() or "").strip()
        lowered = status.lower()
        if lowered.startswith("live") or "chat_" in lowered:
            self.live_short_var.set("● LIVE")
        elif "looking" in lowered:
            self.live_short_var.set("● WATCH")
        else:
            self.live_short_var.set("● LOG")

    def _refresh_status_metrics(self):
        values = compact_progress_values(self.app.progress_var.get())
        self.ready_var.set(values["ready"])
        self.waiting_var.set(values["waiting"])
        self.cooldown_var.set(values["cooldown"])
        self.unknown_var.set(values["unknown"])

    def _refresh_money(self):
        earnings = getattr(self.app, "_earnings_controller", None)
        source = getattr(earnings, "actual_var", None) if earnings is not None else None
        self.run_money_var.set(
            _as_dollar(source.get()) if source is not None else "$0"
        )

    def _draw_coin_icon(self):
        theme = self.app.theme()
        canvas = self.coin_icon
        try:
            canvas.delete("all")
            canvas.configure(bg=theme["card_bg"])
            width = max(13, int(float(canvas.cget("width"))))
            height = max(13, int(float(canvas.cget("height"))))
        except (tk.TclError, ValueError):
            return

        gold = theme["money"]
        shadow = theme["money_shadow"]
        sx = width / 17.0
        sy = height / 17.0

        def rect(x1, y1, x2, y2, fill):
            canvas.create_rectangle(
                round(x1 * sx),
                round(y1 * sy),
                round(x2 * sx),
                round(y2 * sy),
                fill=fill,
                outline="",
            )

        rect(2, 2, 11, 5, gold)
        rect(1, 6, 12, 9, gold)
        rect(3, 10, 14, 13, gold)
        rect(6, 14, 16, 16, gold)
        rect(3, 4, 10, 6, shadow)
        rect(2, 8, 11, 10, shadow)
        rect(4, 12, 13, 14, shadow)

    def _resize_table_columns(self, event=None):
        try:
            width = int(
                event.width if event is not None else self.tree.winfo_width()
            )
        except Exception:
            return
        if width <= 1:
            return

        position_width = self._scale(36, 30)
        rule_width = self._scale(62, 52)
        cooldown_width = self._scale(112, 94)
        allowance = self._scale(5)
        gym_width = max(
            self._scale(130, 110),
            width - position_width - cooldown_width - rule_width - allowance,
        )

        self.tree.column(
            "position",
            width=position_width,
            minwidth=position_width,
            anchor="center",
            stretch=False,
        )
        self.tree.column(
            "gym",
            width=gym_width,
            minwidth=self._scale(130, 110),
            anchor="center",
            stretch=False,
        )
        self.tree.column(
            "cooldown",
            width=cooldown_width,
            minwidth=self._scale(98, 84),
            anchor="center",
            stretch=False,
        )
        self.tree.column(
            "rule",
            width=rule_width,
            minwidth=self._scale(56, 48),
            anchor="center",
            stretch=False,
        )

    def _configure_compact_style(self):
        style = ttk.Style(self.app)
        theme = self.app.theme()
        style.configure(
            "Compact.Treeview",
            rowheight=self._scale(27, 23),
            font=("Segoe UI", self._scale(9, 7)),
            background=theme["panel_dark"],
            fieldbackground=theme["panel_dark"],
            foreground=theme["text"],
            borderwidth=0,
        )
        style.map(
            "Compact.Treeview",
            background=[("selected", theme["selected"])],
            foreground=[("selected", theme["text"])],
        )
        style.configure(
            "Compact.Treeview.Heading",
            background=theme["heading"],
            foreground=theme["text"],
            relief="flat",
            font=("Segoe UI Semibold", self._scale(8, 7)),
        )
        style.map(
            "Compact.Treeview.Heading",
            background=[
                ("active", theme["heading"]),
                ("pressed", theme["heading"]),
            ],
            foreground=[
                ("active", theme["text"]),
                ("pressed", theme["text"]),
            ],
        )

    def _apply_dashboard_theme(self):
        theme = self.app.theme()
        try:
            self.configure(bg=theme["bg"])
            self.chrome.configure(
                bg=theme["bg"],
                highlightbackground=theme["card_border"],
            )
            self.dragbar.configure(bg=theme["heading"])
            self.drag_title.configure(bg=theme["heading"], fg=theme["text"])
            self.live_label.configure(bg=theme["heading"], fg=theme["live"])
            self.body.configure(bg=theme["bg"])

            self.filter_card.configure(
                bg=theme["card_bg"],
                highlightbackground=theme["card_border"],
            )
            self.filters.configure(bg=theme["card_bg"])
            for label in self.filter_labels:
                label.configure(bg=theme["card_bg"], fg=theme["muted"])

            self.status_card.configure(
                bg=theme["card_bg"],
                highlightbackground=theme["card_border"],
            )
            self.metrics.configure(bg=theme["card_bg"])
            metric_colours = {
                "ready": (theme["ready_bg"], theme["ready"]),
                "waiting": (theme["waiting_bg"], theme["waiting"]),
                "cooldown": (theme["cooldown_bg"], theme["cooldown"]),
                "unknown": (theme["unknown_bg"], theme["unknown"]),
            }
            for key, widgets in self.metric_widgets.items():
                background, foreground = metric_colours[key]
                widgets["frame"].configure(
                    bg=background,
                    highlightbackground=theme["card_border"],
                )
                widgets["caption"].configure(
                    bg=background,
                    fg=foreground,
                )
                widgets["value"].configure(
                    bg=background,
                    fg=foreground,
                )

            self.run_strip.configure(bg=theme["card_bg"])
            self.run_caption.configure(
                bg=theme["card_bg"],
                fg=theme["muted"],
            )
            self.money_group.configure(bg=theme["card_bg"])
            self.run_money.configure(
                bg=theme["card_bg"],
                fg=theme["money"],
            )

            self.route_card.configure(
                bg=theme["card_bg"],
                highlightbackground=theme["card_border"],
            )
            self.route_header.configure(bg=theme["card_bg"])
            self.route_title.configure(
                bg=theme["card_bg"],
                fg=theme["text"],
            )
            self.route_name.configure(
                bg=theme["card_bg"],
                fg=theme["muted"],
            )
            self.table.configure(bg=theme["panel_dark"])
        except tk.TclError:
            pass
        self._draw_coin_icon()
        self._configure_compact_style()

    def _make_control(self, command, painter):
        canvas = tk.Canvas(
            self.dragbar,
            width=self.control_width,
            height=self.control_height,
            bd=0,
            highlightthickness=1,
            cursor="hand2",
            takefocus=False,
        )
        canvas.bind("<Button-1>", lambda _event: command())
        canvas.bind("<Enter>", lambda _event: painter(True))
        canvas.bind("<Leave>", lambda _event: painter(False))
        return canvas

    def _paint_control_background(self, canvas, hovered):
        theme = self.app.theme()
        canvas.configure(
            bg=theme["selected"] if hovered else theme["heading"],
            highlightbackground=theme["card_border"],
        )
        canvas.delete("all")
        return theme

    def _paint_max_button(self, hovered=False):
        self._max_hover = hovered
        theme = self._paint_control_background(self.max_button, hovered)
        self.max_button.create_rectangle(
            self._scale(10),
            self._scale(5),
            self._scale(23),
            self._scale(17),
            outline=theme["text"],
            width=max(1, self._scale(2)),
        )

    def _paint_close_button(self, hovered=False):
        self._close_hover = hovered
        theme = self._paint_control_background(self.close_button, hovered)
        width = max(1, self._scale(2))
        self.close_button.create_line(
            self._scale(11),
            self._scale(6),
            self._scale(23),
            self._scale(17),
            fill=theme["text"],
            width=width,
        )
        self.close_button.create_line(
            self._scale(23),
            self._scale(6),
            self._scale(11),
            self._scale(17),
            fill=theme["text"],
            width=width,
        )

    def paint_controls(self):
        self._paint_max_button(self._max_hover)
        self._paint_close_button(self._close_hover)
        self._apply_dashboard_theme()

    def _start_drag(self, event):
        self._drag_dx = event.x_root - self.winfo_x()
        self._drag_dy = event.y_root - self.winfo_y()

    def _drag(self, event):
        self.geometry(
            f"+{event.x_root - self._drag_dx}+{event.y_root - self._drag_dy}"
        )

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

        self._refresh_live()
        self._refresh_status_metrics()
        self._refresh_money()

        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.app.tree.get_children():
            values = self.app.tree.item(item, "values")
            tags = self.app.tree.item(item, "tags")
            if len(values) >= 8:
                self.tree.insert(
                    "",
                    "end",
                    iid=item,
                    values=(values[0], values[2], values[4], values[5]),
                    tags=tags,
                )
        self._apply_dashboard_theme()
        self.after_idle(self._resize_table_columns)
