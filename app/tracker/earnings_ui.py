from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from .constants import APP_NAME, GYMS
from .earnings import (
    DEFAULT_EARNINGS_SETTINGS,
    format_yen,
    parse_yen_input,
    projection_rows,
    reset_run,
    route_base_total,
    summarize_run,
)
from .state import save_state


def _factor(app):
    getter = getattr(app, "ui_scale_factor", None)
    if callable(getter):
        try:
            return float(getter())
        except Exception:
            pass
    return 1.0


def _s(value, factor, minimum=1):
    return max(minimum, int(round(value * factor)))


class EarningsWindow(tk.Toplevel):
    def __init__(self, controller):
        super().__init__(controller.app)
        self.controller = controller
        self.app = controller.app
        self.title("Earnings Calculator")
        self.geometry("650x470")
        self.minsize(610, 430)
        self.transient(self.app)

        settings = self.app.state_data.setdefault("earnings_settings", dict(DEFAULT_EARNINGS_SETTINGS))
        self.amulet_var = tk.StringVar(value=str(settings.get("amulet_price", 0)))
        self.riches75_var = tk.StringVar(value=str(settings.get("riches_75_price", 0)))
        self.riches100_var = tk.StringVar(value=str(settings.get("riches_100_price", 0)))
        self.donator_var = tk.BooleanVar(value=bool(settings.get("donator", False)))

        self.route_var = tk.StringVar()
        self.base_var = tk.StringVar()
        self.actual_var = tk.StringVar()
        self.progress_var = tk.StringVar()
        self.remaining_var = tk.StringVar()
        self.projection_vars = {}

        self._build()
        for var in (self.amulet_var, self.riches75_var, self.riches100_var):
            var.trace_add("write", self._settings_changed)
        self.donator_var.trace_add("write", self._settings_changed)
        self.refresh()
        self.app.apply_theme()
        self._apply_custom_theme()

    def _build(self):
        header = tk.Frame(self)
        header.pack(fill="x", padx=14, pady=(14, 8))
        tk.Label(header, text="Route Earnings", font=("Segoe UI Semibold", 15)).pack(side="left")
        tk.Label(
            header,
            text="Offline • actual payouts from chat log",
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        summary = tk.LabelFrame(self, text="Current route / run", bd=1, relief="groove")
        summary.pack(fill="x", padx=14, pady=(0, 10))
        for label, variable in (
            ("Route", self.route_var),
            ("Base payout", self.base_var),
            ("Actual detected this run", self.actual_var),
            ("Route gym payouts", self.progress_var),
            ("Remaining base payout", self.remaining_var),
        ):
            row = tk.Frame(summary)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=label, width=24, anchor="w").pack(side="left")
            tk.Label(row, textvariable=variable, font=("Segoe UI Semibold", 9), anchor="w").pack(side="left")

        settings = tk.LabelFrame(self, text="Charm comparison settings", bd=1, relief="groove")
        settings.pack(fill="x", padx=14, pady=(0, 10))

        top = tk.Frame(settings)
        top.pack(fill="x", padx=10, pady=(7, 4))
        ttk.Checkbutton(top, text="Donator Status (+5%)", variable=self.donator_var).pack(side="left")
        tk.Label(top, text="Charm prices are entered manually — no market API calls.", font=("Segoe UI", 8)).pack(side="right")

        prices = tk.Frame(settings)
        prices.pack(fill="x", padx=10, pady=(0, 8))
        for index, (label, var) in enumerate((
            ("Amulet Coin", self.amulet_var),
            ("Riches 75%", self.riches75_var),
            ("Riches 100%", self.riches100_var),
        )):
            group = tk.Frame(prices)
            group.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 8, 0))
            tk.Label(group, text=label, anchor="w").pack(fill="x")
            tk.Entry(group, textvariable=var, justify="right").pack(fill="x", pady=(2, 0))

        projection = tk.LabelFrame(self, text="Projected route value", bd=1, relief="groove")
        projection.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        headings = tk.Frame(projection)
        headings.pack(fill="x", padx=10, pady=(6, 2))
        tk.Label(headings, text="Option", width=22, anchor="w", font=("Segoe UI Semibold", 9)).pack(side="left")
        tk.Label(headings, text="Gross", width=16, anchor="e", font=("Segoe UI Semibold", 9)).pack(side="left")
        tk.Label(headings, text="Charm cost", width=16, anchor="e", font=("Segoe UI Semibold", 9)).pack(side="left")
        tk.Label(headings, text="Net", width=16, anchor="e", font=("Segoe UI Semibold", 9)).pack(side="left")

        for name in ("No charm", "Amulet Coin", "Riches Charm 75%", "Riches Charm 100%"):
            row = tk.Frame(projection)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=name, width=22, anchor="w").pack(side="left")
            gross = tk.StringVar()
            price = tk.StringVar()
            net = tk.StringVar()
            tk.Label(row, textvariable=gross, width=16, anchor="e").pack(side="left")
            tk.Label(row, textvariable=price, width=16, anchor="e").pack(side="left")
            tk.Label(row, textvariable=net, width=16, anchor="e", font=("Segoe UI Semibold", 9)).pack(side="left")
            self.projection_vars[name] = (gross, price, net)

        footer = tk.Frame(self)
        footer.pack(fill="x", padx=14, pady=(0, 12))
        tk.Label(
            footer,
            text="Actual detected payouts already include whatever charm/Donator effect PokeMMO awarded.",
            font=("Segoe UI", 8),
        ).pack(side="left")
        ttk.Button(footer, text="Reset run earnings", command=self.controller.reset_selected_run).pack(side="right")

    def _settings_changed(self, *_args):
        settings = self.app.state_data.setdefault("earnings_settings", {})
        settings["amulet_price"] = parse_yen_input(self.amulet_var.get())
        settings["riches_75_price"] = parse_yen_input(self.riches75_var.get())
        settings["riches_100_price"] = parse_yen_input(self.riches100_var.get())
        settings["donator"] = bool(self.donator_var.get())
        save_state(self.app.state_data)
        self.refresh()
        self.controller.refresh()

    def refresh(self):
        route_name = self.app.route_var.get()
        route = self.controller.route_leaders()
        base = route_base_total(route)
        aggregate = self.controller.aggregate_summary(route)

        self.route_var.set(route_name)
        self.base_var.set(format_yen(base))
        self.actual_var.set(format_yen(aggregate["total"]))
        self.progress_var.set(self.controller.progress_text(aggregate, route))
        self.remaining_var.set(format_yen(aggregate["remaining_base"]))

        settings = self.app.state_data.setdefault("earnings_settings", dict(DEFAULT_EARNINGS_SETTINGS))
        for row in projection_rows(base, settings):
            gross, price, net = self.projection_vars[row["name"]]
            gross.set(format_yen(row["gross"]))
            price.set("—" if row["price"] == 0 and row["name"] == "No charm" else format_yen(row["price"]))
            net.set(format_yen(row["net"]))

        self._apply_custom_theme()

    def _apply_custom_theme(self):
        theme = self.app.theme()
        try:
            self.configure(bg=theme["bg"])
        except tk.TclError:
            return


class EarningsController:
    """Full-view earnings integration; compact mode intentionally stays clean."""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.base_var = tk.StringVar()
        self.actual_var = tk.StringVar()
        self.gyms_var = tk.StringVar()
        self.other_var = tk.StringVar()
        self._theme_job = None
        self.metric_groups = []
        self.metric_captions = []
        self.metric_values = []

        self._build_strip()
        self._wrap_refresh()
        app.theme_var.trace_add("write", self._theme_changed)
        self.refresh()
        self.apply_theme()
        self.apply_scale(_factor(app))

    def _build_strip(self):
        self.strip = tk.Frame(self.app, bd=0, highlightthickness=1)
        self.strip.pack(fill="x", padx=10, pady=(0, 7), before=self.app.view_controls)

        self.earnings_label = tk.Label(self.strip, text="Earnings", font=("Segoe UI Semibold", 10))
        self.earnings_label.pack(side="left", padx=(10, 14), pady=7)
        for label, variable in (
            ("Route base", self.base_var),
            ("Actual run", self.actual_var),
            ("Route gyms", self.gyms_var),
            ("Other payouts", self.other_var),
        ):
            group = tk.Frame(self.strip)
            group.pack(side="left", padx=(0, 18), pady=5)
            caption = tk.Label(group, text=label, font=("Segoe UI", 8))
            caption.pack(anchor="w")
            value_label = tk.Label(group, textvariable=variable, font=("Segoe UI Semibold", 9))
            value_label.pack(anchor="w")
            self.metric_groups.append(group)
            self.metric_captions.append(caption)
            self.metric_values.append(value_label)

        self.calculator_button = ttk.Button(self.strip, text="Calculator…", command=self.open_calculator)
        self.calculator_button.pack(side="right", padx=(6, 8), pady=6)
        self.reset_button = ttk.Button(self.strip, text="Reset run", command=self.reset_selected_run)
        self.reset_button.pack(side="right", pady=6)

    def apply_scale(self, factor=None):
        factor = float(factor or _factor(self.app))
        try:
            self.strip.pack_configure(
                padx=_s(10, factor),
                pady=(0, _s(7, factor)),
            )
            self.earnings_label.configure(
                font=("Segoe UI Semibold", _s(10, factor, 8))
            )
            self.earnings_label.pack_configure(
                padx=(_s(10, factor), _s(14, factor)),
                pady=_s(7, factor),
            )
            for group, caption, value_label in zip(
                self.metric_groups, self.metric_captions, self.metric_values
            ):
                group.pack_configure(
                    padx=(0, _s(18, factor)),
                    pady=_s(5, factor),
                )
                caption.configure(font=("Segoe UI", _s(8, factor, 7)))
                value_label.configure(
                    font=("Segoe UI Semibold", _s(9, factor, 7))
                )
            self.calculator_button.pack_configure(
                padx=(_s(6, factor), _s(8, factor)),
                pady=_s(6, factor),
            )
            self.reset_button.pack_configure(pady=_s(6, factor))
        except tk.TclError:
            pass

    def _wrap_refresh(self):
        original_refresh = self.app.refresh_table

        def refresh_with_earnings(*args, **kwargs):
            result = original_refresh(*args, **kwargs)
            self.refresh()
            return result

        self.app.refresh_table = refresh_with_earnings

    def _theme_changed(self, *_args):
        if self._theme_job is not None:
            try:
                self.app.after_cancel(self._theme_job)
            except tk.TclError:
                pass
        self._theme_job = self.app.after_idle(self._after_theme_change)

    def _after_theme_change(self):
        self._theme_job = None
        self.apply_theme()
        self.apply_scale(_factor(self.app))
        if self.window is not None and self.window.winfo_exists():
            self.window._apply_custom_theme()

    def route_leaders(self):
        route = self.app.current_route_leaders()
        if route is None:
            return [leader for _region, _gym, leader in GYMS]
        return route

    def selected_characters(self):
        selected = self.app.character_var.get()
        chars = self.app.state_data.get("characters", {})
        if selected == "All characters":
            return list(chars.items())
        char = chars.get(selected)
        return [(selected, char)] if char is not None else []

    def aggregate_summary(self, route=None):
        route = route or self.route_leaders()
        summaries = []
        for _name, char in self.selected_characters():
            if char is not None:
                summaries.append(summarize_run(char, route))

        if not summaries:
            return {
                "total": 0,
                "route_gym_total": 0,
                "other_total": 0,
                "gym_count": 0,
                "route_count": len(route),
                "remaining_base": route_base_total(route),
            }

        completed = set()
        total = route_gym_total = other_total = gym_count = 0
        for summary in summaries:
            total += summary["total"]
            route_gym_total += summary["route_gym_total"]
            other_total += summary["other_total"]
            gym_count += summary["gym_count"]
            completed.update(summary["completed_leaders"])

        # With one selected character, remaining base is exact for the current run.
        # In All-characters view, show route leaders not completed by any selected
        # character rather than multiplying the route projection by account count.
        remaining = [leader for leader in route if leader not in completed]
        return {
            "total": total,
            "route_gym_total": route_gym_total,
            "other_total": other_total,
            "gym_count": gym_count,
            "route_count": len(route),
            "remaining_base": route_base_total(remaining),
        }

    def progress_text(self, summary, route):
        if self.app.character_var.get() == "All characters":
            return f"{summary['gym_count']} payouts"
        return f"{summary['gym_count']}/{len(route)}"

    def refresh(self):
        route = self.route_leaders()
        base = route_base_total(route)
        summary = self.aggregate_summary(route)
        self.base_var.set(format_yen(base))
        self.actual_var.set(format_yen(summary["total"]))
        self.gyms_var.set(self.progress_text(summary, route))
        self.other_var.set(format_yen(summary["other_total"]))

        if self.window is not None and self.window.winfo_exists():
            self.window.refresh()

    def reset_selected_run(self):
        selected = self.app.character_var.get()
        if selected == "All characters":
            messagebox.showinfo(APP_NAME, "Choose a specific character before resetting run earnings.", parent=self.app)
            return
        char = self.app.state_data.get("characters", {}).get(selected)
        if char is None:
            messagebox.showinfo(APP_NAME, "No tracked data exists for this character yet.", parent=self.app)
            return
        reset_run(char, datetime.now())
        save_state(self.app.state_data)
        self.refresh()
        if self.window is not None and self.window.winfo_exists():
            self.window.refresh()

    def open_calculator(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self.window.refresh()
            return
        self.window = EarningsWindow(self)

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.strip.configure(bg=theme["panel"], highlightbackground=theme["border"])
            self.earnings_label.configure(bg=theme["panel"], fg=theme["text"])
            for group, caption, value_label in zip(
                self.metric_groups, self.metric_captions, self.metric_values
            ):
                group.configure(bg=theme["panel"])
                caption.configure(bg=theme["panel"], fg=theme["muted"])
                value_label.configure(bg=theme["panel"], fg=theme["text"])
        except tk.TclError:
            pass


def install_earnings(app):
    app._earnings_controller = EarningsController(app)
    return app._earnings_controller
