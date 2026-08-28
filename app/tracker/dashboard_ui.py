import tkinter as tk
from tkinter import ttk

from .constants import DISPLAY_MODES, REGIONS
from .themes import THEMES
from .ui import RouteEditor


class DashboardShell:
    """v0.6 full-view dashboard shell.

    Phase A deliberately reuses the proven Treeview, detector and tracker engine.
    Later v0.6 phases replace the gym rows themselves. Keeping this layer
    presentation-only gives us a safe path back to the v0.5.5 UI while the new
    dashboard is screenshot-tested on Windows.
    """

    def __init__(self, app):
        self.app = app
        self.presentation = getattr(app, "_presentation", None)
        self.earnings = getattr(app, "_earnings_controller", None)
        self.table_frame = app.tree.master
        self.detector_frame = app.event_text.master
        self.manual_frame = self._find_manual_frame()
        self._money_traces = []
        self._theme_after_id = None

        self._capture_combo_values()
        self._hide_legacy_full_header()
        self._build_header()
        self._build_controls()
        self._polish_existing_body()
        self._wrap_theme()
        self.apply_theme()

        app.theme_var.trace_add("write", self._theme_changed)
        app._dashboard_shell = self

    def _find_manual_frame(self):
        for child in self.app.winfo_children():
            if not isinstance(child, tk.Frame):
                continue
            for grandchild in child.winfo_children():
                try:
                    if isinstance(grandchild, ttk.Button) and grandchild.cget("text") == "Mark Selected Defeated Now":
                        return child
                except tk.TclError:
                    pass
        return None

    def _capture_combo_values(self):
        def values(widget, fallback):
            try:
                return tuple(widget["values"])
            except Exception:
                return tuple(fallback)

        self.character_values = values(self.app.char_combo, ())
        self.route_values = values(self.app.route_combo, ("All gyms",))
        self.region_values = values(self.app.region_combo, REGIONS)
        self.display_values = values(self.app.display_combo, DISPLAY_MODES)

    def _hide_legacy_full_header(self):
        """Hide only the old root-level chrome above the proven table.

        Nothing is destroyed. During v0.6 development this keeps the old widgets
        alive for rollback/debugging while the visible Full view uses the new
        dashboard shell.
        """
        keep = {self.table_frame, self.detector_frame}
        if self.manual_frame is not None:
            keep.add(self.manual_frame)

        for child in self.app.winfo_children():
            if child in keep or not isinstance(child, tk.Frame):
                continue
            try:
                child.pack_forget()
            except tk.TclError:
                pass

        if self.presentation is not None:
            try:
                self.presentation.status_strip.pack_forget()
            except (AttributeError, tk.TclError):
                pass
        if self.earnings is not None:
            try:
                self.earnings.strip.pack_forget()
            except (AttributeError, tk.TclError):
                pass

    def _build_header(self):
        self.header = tk.Frame(self.app, bd=0)
        self.header.pack(fill="x", padx=20, pady=(14, 8), before=self.table_frame)

        self.title_row = tk.Frame(self.header, bd=0)
        self.title_row.pack(fill="x", pady=(0, 10))
        self.title_label = tk.Label(
            self.title_row,
            text="Gym Rerun Tracker",
            font=("Segoe UI Semibold", 15),
            anchor="w",
        )
        self.title_label.pack(side="left")
        self.subtitle_label = tk.Label(
            self.title_row,
            text="Cooldowns  •  5-rule  •  routes  •  earnings",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.subtitle_label.pack(side="left", padx=(12, 0), pady=(3, 0))
        self.live_label = tk.Label(
            self.title_row,
            textvariable=self.app.status_var,
            font=("Segoe UI", 9),
            anchor="e",
        )
        self.live_label.pack(side="right")

        self.summary = tk.Frame(self.header, bd=0)
        self.summary.pack(fill="x")
        # Unknown remains a meaningful row state, but it is not an operational
        # dashboard metric. Give the reclaimed space to run earnings instead.
        for index in range(4):
            self.summary.columnconfigure(index, weight=(4 if index == 3 else 1), uniform="summary")

        self.stat_cards = {}
        specs = (
            ("ready", "READY"),
            ("waiting", "WAITING"),
            ("cooldown", "COOLDOWN"),
        )
        for column, (key, label) in enumerate(specs):
            card = tk.Frame(self.summary, bd=0, highlightthickness=1)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 8))
            caption = tk.Label(card, text=label, font=("Segoe UI Semibold", 8), anchor="w")
            caption.pack(fill="x", padx=12, pady=(9, 1))
            count_var = self._status_var(key)
            count = tk.Label(card, textvariable=count_var, font=("Segoe UI Semibold", 18), anchor="w")
            count.pack(fill="x", padx=12, pady=(0, 9))
            self.stat_cards[key] = {
                "frame": card,
                "caption": caption,
                "count": count,
                "var": count_var,
            }

        self.earnings_card = tk.Frame(self.summary, bd=0, highlightthickness=1)
        self.earnings_card.grid(row=0, column=3, sticky="nsew")
        self.earnings_title = tk.Label(
            self.earnings_card,
            text="RUN EARNINGS",
            font=("Segoe UI Semibold", 8),
            anchor="w",
        )
        self.earnings_title.pack(fill="x", padx=12, pady=(8, 2))

        earnings_body = tk.Frame(self.earnings_card, bd=0)
        earnings_body.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        earnings_body.columnconfigure(0, weight=2)
        for column in (1, 2, 3, 4):
            earnings_body.columnconfigure(column, weight=1)

        primary = tk.Frame(earnings_body, bd=0)
        primary.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14))
        self.coin_icon = tk.Canvas(primary, width=32, height=28, bd=0, highlightthickness=0)
        self.coin_icon.pack(side="left", padx=(0, 7))
        self.run_money_var = self._money_var(self._earnings_var("actual_var"))
        self.run_money_label = tk.Label(
            primary,
            textvariable=self.run_money_var,
            font=("Segoe UI Semibold", 15),
            anchor="w",
        )
        self.run_money_label.pack(side="left")

        metrics = (
            ("ROUTE BASE", "base_var", True),
            ("ACTUAL RUN", "actual_var", True),
            ("ROUTE GYMS", "gyms_var", False),
            ("OTHER PAYOUTS", "other_var", True),
        )
        self.earnings_metrics = []
        for column, (caption_text, attr, is_money) in enumerate(metrics, 1):
            group = tk.Frame(earnings_body, bd=0)
            group.grid(row=0, column=column, rowspan=2, sticky="w", padx=(6, 0))
            caption = tk.Label(group, text=caption_text, font=("Segoe UI", 7), anchor="w")
            caption.pack(anchor="w")
            source = self._earnings_var(attr)
            variable = self._money_var(source) if is_money else source
            value = tk.Label(group, textvariable=variable, font=("Segoe UI Semibold", 9), anchor="w")
            value.pack(anchor="w", pady=(2, 0))
            self.earnings_metrics.append((group, caption, value))

    def _status_var(self, key):
        if self.presentation is not None:
            try:
                return self.presentation.cards[key]["count_var"]
            except (AttributeError, KeyError):
                pass
        return tk.StringVar(master=self.app, value="0")

    def _earnings_var(self, name):
        if self.earnings is not None:
            variable = getattr(self.earnings, name, None)
            if variable is not None:
                return variable
        return tk.StringVar(master=self.app, value="0")

    @staticmethod
    def _as_dollar(value):
        value = str(value or "0").strip()
        if value.startswith("¥"):
            return "$" + value[1:]
        if value.startswith("$"):
            return value
        if value == "—":
            return value
        return "$" + value

    def _money_var(self, source):
        target = tk.StringVar(master=self.app, value=self._as_dollar(source.get()))

        def changed(*_args):
            target.set(self._as_dollar(source.get()))

        trace_id = source.trace_add("write", changed)
        self._money_traces.append((source, trace_id))
        return target

    def _build_controls(self):
        self.control_panel = tk.Frame(self.app, bd=0, highlightthickness=1)
        self.control_panel.pack(fill="x", padx=20, pady=(0, 8), before=self.table_frame)

        filters = tk.Frame(self.control_panel, bd=0)
        filters.pack(fill="x", padx=10, pady=(9, 5))
        for column in range(6):
            filters.columnconfigure(column, weight=1, uniform="dashboard_filters")

        self.char_combo = self._filter_group(
            filters, 0, "Character", self.app.character_var, self.character_values
        )
        self.region_combo = self._filter_group(
            filters, 1, "Region", self.app.region_var, self.region_values
        )

        route_group = tk.Frame(filters, bd=0)
        route_group.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        route_label = tk.Label(route_group, text="Route / order", font=("Segoe UI", 8), anchor="w")
        route_label.pack(fill="x", pady=(0, 3))
        self.route_combo = ttk.Combobox(
            route_group,
            textvariable=self.app.route_var,
            state="readonly",
            values=self.route_values,
            style="Readable.TCombobox",
        )
        self.route_combo.pack(fill="x")
        self.route_combo.bind("<<ComboboxSelected>>", self.app.filters_changed)

        self.display_combo = self._filter_group(
            filters, 3, "Display", self.app.display_var, self.display_values
        )

        self.ui_scale_host = tk.Frame(filters, bd=0)
        self.ui_scale_host.grid(row=0, column=4, sticky="ew", padx=(0, 8))
        # scaling.py installs the actual UI Scale selector here.
        self.app.ui_scale_host = self.ui_scale_host

        theme_group = tk.Frame(filters, bd=0)
        theme_group.grid(row=0, column=5, sticky="ew")
        theme_label = tk.Label(theme_group, text="Theme", font=("Segoe UI", 8), anchor="w")
        theme_label.pack(fill="x", pady=(0, 3))
        self.theme_combo = ttk.Combobox(
            theme_group,
            textvariable=self.app.theme_var,
            state="readonly",
            values=tuple(THEMES.keys()),
            style="Readable.TCombobox",
        )
        self.theme_combo.pack(fill="x")
        self.theme_combo.bind("<<ComboboxSelected>>", self.app.theme_changed)

        actions = tk.Frame(self.control_panel, bd=0)
        actions.pack(fill="x", padx=10, pady=(0, 9))
        ttk.Button(actions, text="Manage Routes", command=lambda: RouteEditor(self.app)).pack(side="left")
        ttk.Checkbutton(
            actions,
            text="Hide unknown",
            variable=self.app.hide_unknown_var,
            command=self.app.view_options_changed,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(actions, text="Reset Run", command=self._reset_run).pack(side="right")
        ttk.Button(actions, text="Calculator", command=self._open_calculator).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Compact View", command=self.app.open_compact_view).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Choose Log Folder", command=self.app.choose_log_folder).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="Replay Log File", command=self.app.replay_log).pack(side="right", padx=(0, 6))

        # Core tracker refresh methods write values through these public widget
        # references. Point them at the visible dashboard controls.
        self.app.char_combo = self.char_combo
        self.app.region_combo = self.region_combo
        self.app.route_combo = self.route_combo
        self.app.display_combo = self.display_combo
        self.app.theme_combo = self.theme_combo

    def _filter_group(self, parent, column, label_text, variable, values):
        group = tk.Frame(parent, bd=0)
        group.grid(row=0, column=column, sticky="ew", padx=(0, 8))
        label = tk.Label(group, text=label_text, font=("Segoe UI", 8), anchor="w")
        label.pack(fill="x", pady=(0, 3))
        combo = ttk.Combobox(
            group,
            textvariable=variable,
            state="readonly",
            values=values,
            style="Readable.TCombobox",
        )
        combo.pack(fill="x")
        if label_text in {"Character", "Region"}:
            combo.bind("<<ComboboxSelected>>", self.app.filters_changed)
        elif label_text == "Display":
            combo.bind("<<ComboboxSelected>>", self.app.view_options_changed)
        return combo

    def _open_calculator(self):
        if self.earnings is not None:
            self.earnings.open_calculator()

    def _reset_run(self):
        if self.earnings is not None:
            self.earnings.reset_selected_run()

    def _polish_existing_body(self):
        try:
            self.table_frame.pack_configure(padx=20, pady=(0, 8))
            self.table_frame.configure(highlightthickness=1, bd=0)
        except tk.TclError:
            pass

        if self.manual_frame is not None:
            try:
                self.manual_frame.pack_configure(padx=20, pady=(0, 8))
            except tk.TclError:
                pass

        try:
            self.detector_frame.configure(text="Detector", bd=0, relief="flat", highlightthickness=1)
            self.detector_frame.pack_configure(fill="both", expand=False, padx=20, pady=(0, 14))
            self.app.event_text.configure(height=5)
        except tk.TclError:
            pass

    def _wrap_theme(self):
        original = self.app.apply_theme
        if getattr(original, "_dashboard_wrapped", False):
            return

        def apply_with_dashboard(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_theme()
            return result

        apply_with_dashboard._dashboard_wrapped = True
        self.app.apply_theme = apply_with_dashboard

    def _theme_changed(self, *_args):
        if self._theme_after_id is not None:
            try:
                self.app.after_cancel(self._theme_after_id)
            except tk.TclError:
                pass
        self._theme_after_id = self.app.after_idle(self._after_theme_change)

    def _after_theme_change(self):
        self._theme_after_id = None
        self.apply_theme()

    def apply_scale(self, factor=1.0):
        try:
            size = max(22, int(round(32 * float(factor))))
            height = max(20, int(round(28 * float(factor))))
            self.coin_icon.configure(width=size, height=height)
        except (tk.TclError, ValueError, TypeError):
            pass
        self._draw_coin_icon()

    def _draw_coin_icon(self):
        theme = self.app.theme()
        canvas = self.coin_icon
        try:
            canvas.delete("all")
            canvas.configure(bg=theme["card_bg"])
            width = max(24, int(canvas.cget("width")))
            height = max(20, int(canvas.cget("height")))
        except tk.TclError:
            return

        gold = theme["money"]
        shadow = theme["money_shadow"]
        scale_x = width / 32.0
        scale_y = height / 28.0

        def rect(x1, y1, x2, y2, fill):
            canvas.create_rectangle(
                round(x1 * scale_x), round(y1 * scale_y),
                round(x2 * scale_x), round(y2 * scale_y),
                fill=fill, outline=""
            )

        # Original pixel-style money-stack mark inspired by the game's compact
        # HUD language; it does not embed or copy game sprite pixels.
        rect(2, 5, 15, 9, gold)
        rect(1, 10, 16, 14, gold)
        rect(3, 15, 17, 19, gold)
        rect(7, 20, 19, 24, gold)
        rect(3, 8, 13, 10, shadow)
        rect(2, 13, 14, 15, shadow)
        rect(4, 18, 15, 20, shadow)
        canvas.create_text(
            round(24 * scale_x), round(16 * scale_y),
            text="$", fill=gold,
            font=("Segoe UI Semibold", max(7, round(10 * min(scale_x, scale_y))))
        )

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.header.configure(bg=theme["bg"])
            self.title_row.configure(bg=theme["bg"])
            self.title_label.configure(bg=theme["bg"], fg=theme["text"])
            self.subtitle_label.configure(bg=theme["bg"], fg=theme["muted"])
            self.live_label.configure(bg=theme["bg"], fg=theme["live"])
            self.summary.configure(bg=theme["bg"])

            status_colours = {
                "ready": theme["ready"],
                "waiting": theme["waiting"],
                "cooldown": theme["cooldown"],
            }
            status_backgrounds = {
                "ready": theme["ready_bg"],
                "waiting": theme["waiting_bg"],
                "cooldown": theme["cooldown_bg"],
            }
            for key, widgets in self.stat_cards.items():
                widgets["frame"].configure(
                    bg=status_backgrounds[key],
                    highlightbackground=theme["card_border"],
                )
                widgets["caption"].configure(bg=status_backgrounds[key], fg=status_colours[key])
                widgets["count"].configure(bg=status_backgrounds[key], fg=status_colours[key])

            self.earnings_card.configure(bg=theme["card_bg"], highlightbackground=theme["card_border"])
            self.earnings_title.configure(bg=theme["card_bg"], fg=theme["text"])
            earnings_body = self.earnings_title.master.winfo_children()[-1]
            earnings_body.configure(bg=theme["card_bg"])
            for child in earnings_body.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=theme["card_bg"])
                    for label in child.winfo_children():
                        if isinstance(label, tk.Label):
                            label.configure(bg=theme["card_bg"], fg=theme["text"])
            self.run_money_label.configure(bg=theme["card_bg"], fg=theme["money"])
            for _group, caption, value in self.earnings_metrics:
                caption.configure(bg=theme["card_bg"], fg=theme["muted"])
                value.configure(bg=theme["card_bg"], fg=theme["text"])

            self.control_panel.configure(bg=theme["card_bg"], highlightbackground=theme["card_border"])
            for child in self.control_panel.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=theme["card_bg"])
                    for group in child.winfo_children():
                        if isinstance(group, tk.Frame):
                            group.configure(bg=theme["card_bg"])
                            for widget in group.winfo_children():
                                if isinstance(widget, tk.Label):
                                    widget.configure(bg=theme["card_bg"], fg=theme["muted"])

            self.table_frame.configure(bg=theme["card_bg"], highlightbackground=theme["card_border"])
            if self.manual_frame is not None:
                self.manual_frame.configure(bg=theme["bg"])
            self.detector_frame.configure(
                bg=theme["card_bg"], fg=theme["text"], highlightbackground=theme["card_border"]
            )
            self.app.event_text.configure(bg=theme["panel_dark"], fg=theme["text"])
        except tk.TclError:
            pass
        self._draw_coin_icon()


def install_dashboard(app):
    app._dashboard_shell = DashboardShell(app)
    return app._dashboard_shell
