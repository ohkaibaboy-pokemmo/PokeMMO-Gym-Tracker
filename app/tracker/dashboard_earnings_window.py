"""Dashboard-styled offline earnings calculator for v0.6.

This module intentionally consumes the existing EarningsController and earnings
maths rather than duplicating them. It changes presentation only: dashboard
cards, theme-aware inputs and $ formatting.
"""

import tkinter as tk
from tkinter import ttk

from .earnings import (
    DEFAULT_EARNINGS_SETTINGS,
    parse_yen_input,
    projection_rows,
    route_base_total,
)
from .state import save_state


def format_dashboard_currency(value):
    """Presentation-only currency formatter used by the v0.6 dashboard."""
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return "—"
    return f"${amount:,}"


class DashboardEarningsWindow(tk.Toplevel):
    def __init__(self, controller):
        super().__init__(controller.app)
        self.controller = controller
        self.app = controller.app
        self.title("Earnings Calculator")
        self.geometry("760x590")
        self.minsize(700, 540)
        self.transient(self.app)

        settings = self.app.state_data.setdefault(
            "earnings_settings", dict(DEFAULT_EARNINGS_SETTINGS)
        )
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
        self._themed_frames = []
        self._card_frames = []
        self._muted_labels = []
        self._money_labels = []
        self._normal_labels = []
        self._entries = []

        self._build()
        for variable in (self.amulet_var, self.riches75_var, self.riches100_var):
            variable.trace_add("write", self._settings_changed)
        self.donator_var.trace_add("write", self._settings_changed)
        self.app.theme_var.trace_add("write", lambda *_args: self.after_idle(self._apply_custom_theme))

        self.refresh()
        self._apply_custom_theme()

    def _frame(self, parent, card=False):
        frame = tk.Frame(parent, bd=0, highlightthickness=1 if card else 0)
        self._themed_frames.append(frame)
        if card:
            self._card_frames.append(frame)
        return frame

    def _label(self, parent, text="", variable=None, font=("Segoe UI", 9), muted=False, money=False, **kwargs):
        label = tk.Label(parent, text=text, textvariable=variable, font=font, **kwargs)
        if muted:
            self._muted_labels.append(label)
        elif money:
            self._money_labels.append(label)
        else:
            self._normal_labels.append(label)
        return label

    def _build(self):
        self.root_body = self._frame(self)
        self.root_body.pack(fill="both", expand=True, padx=18, pady=16)

        header = self._frame(self.root_body)
        header.pack(fill="x", pady=(0, 12))
        self._label(
            header,
            text="Route Earnings",
            font=("Segoe UI Semibold", 16),
            anchor="w",
        ).pack(side="left")
        self._label(
            header,
            text="Offline calculator  •  actual payouts from chat log",
            font=("Segoe UI", 9),
            muted=True,
            anchor="w",
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        summary = self._frame(self.root_body, card=True)
        summary.pack(fill="x", pady=(0, 12))
        summary.columnconfigure(0, weight=2)
        for col in range(1, 5):
            summary.columnconfigure(col, weight=1)

        route_group = self._summary_metric(summary, 0, "ROUTE", self.route_var, money=False, large=True)
        route_group.grid(row=0, column=0, sticky="nsew", padx=12, pady=11)
        for column, (caption, variable, money) in enumerate(
            (
                ("ROUTE BASE", self.base_var, True),
                ("ACTUAL RUN", self.actual_var, True),
                ("ROUTE GYMS", self.progress_var, False),
                ("REMAINING BASE", self.remaining_var, True),
            ),
            1,
        ):
            group = self._summary_metric(summary, column, caption, variable, money=money)
            group.grid(row=0, column=column, sticky="nsew", padx=(0, 12), pady=11)

        settings_card = self._frame(self.root_body, card=True)
        settings_card.pack(fill="x", pady=(0, 12))
        settings_header = self._frame(settings_card)
        settings_header.pack(fill="x", padx=12, pady=(10, 8))
        self._label(
            settings_header,
            text="Charm comparison",
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(side="left")
        ttk.Checkbutton(
            settings_header,
            text="Donator Status (+5%)",
            variable=self.donator_var,
        ).pack(side="right")

        price_row = self._frame(settings_card)
        price_row.pack(fill="x", padx=12, pady=(0, 11))
        for column in range(3):
            price_row.columnconfigure(column, weight=1, uniform="price")
        for column, (caption, variable) in enumerate(
            (
                ("Amulet Coin", self.amulet_var),
                ("Riches Charm 75%", self.riches75_var),
                ("Riches Charm 100%", self.riches100_var),
            )
        ):
            group = self._frame(price_row)
            group.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
            self._label(group, text=caption, font=("Segoe UI", 8), muted=True, anchor="w").pack(fill="x")
            input_row = self._frame(group)
            input_row.pack(fill="x", pady=(4, 0))
            self._label(input_row, text="$", font=("Segoe UI Semibold", 10), money=True).pack(side="left", padx=(0, 5))
            entry = tk.Entry(
                input_row,
                textvariable=variable,
                justify="right",
                relief="flat",
                bd=0,
                highlightthickness=1,
                font=("Segoe UI", 10),
            )
            entry.pack(side="left", fill="x", expand=True, ipady=5)
            self._entries.append(entry)

        note = self._label(
            settings_card,
            text="Prices are entered manually. The tracker makes no market/API requests.",
            font=("Segoe UI", 8),
            muted=True,
            anchor="w",
        )
        note.pack(fill="x", padx=12, pady=(0, 10))

        projection = self._frame(self.root_body, card=True)
        projection.pack(fill="both", expand=True, pady=(0, 12))
        title_row = self._frame(projection)
        title_row.pack(fill="x", padx=12, pady=(10, 7))
        self._label(
            title_row,
            text="Projected route value",
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(side="left")
        self._label(
            title_row,
            text="Net = gross payout − manual charm cost",
            font=("Segoe UI", 8),
            muted=True,
            anchor="e",
        ).pack(side="right")

        self.projection_table = self._frame(projection)
        self.projection_table.pack(fill="both", expand=True, padx=12, pady=(0, 11))
        widths = (3, 2, 2, 2)
        for column, weight in enumerate(widths):
            self.projection_table.columnconfigure(column, weight=weight, uniform="projection")

        for column, heading in enumerate(("OPTION", "GROSS", "CHARM COST", "NET")):
            self._label(
                self.projection_table,
                text=heading,
                font=("Segoe UI Semibold", 8),
                muted=True,
                anchor="w" if column == 0 else "e",
            ).grid(row=0, column=column, sticky="ew", padx=8, pady=(5, 7))

        self.projection_rows = []
        for row_index, name in enumerate(
            ("No charm", "Amulet Coin", "Riches Charm 75%", "Riches Charm 100%"),
            1,
        ):
            row_frame = self._frame(self.projection_table)
            row_frame.grid(row=row_index, column=0, columnspan=4, sticky="nsew", pady=(0, 1))
            for column, weight in enumerate(widths):
                row_frame.columnconfigure(column, weight=weight, uniform="projection_row")
            name_label = self._label(row_frame, text=name, anchor="w", font=("Segoe UI", 9))
            name_label.grid(row=0, column=0, sticky="ew", padx=8, pady=7)
            gross = tk.StringVar()
            price = tk.StringVar()
            net = tk.StringVar()
            self._label(row_frame, variable=gross, anchor="e", font=("Segoe UI", 9)).grid(row=0, column=1, sticky="ew", padx=8)
            self._label(row_frame, variable=price, anchor="e", font=("Segoe UI", 9), muted=True).grid(row=0, column=2, sticky="ew", padx=8)
            net_label = self._label(row_frame, variable=net, anchor="e", font=("Segoe UI Semibold", 9), money=True)
            net_label.grid(row=0, column=3, sticky="ew", padx=8)
            self.projection_vars[name] = (gross, price, net)
            self.projection_rows.append(row_frame)

        footer = self._frame(self.root_body)
        footer.pack(fill="x")
        self._label(
            footer,
            text="Detected payouts already include whatever charm/Donator effect PokeMMO awarded.",
            font=("Segoe UI", 8),
            muted=True,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            footer,
            text="Reset run earnings",
            command=self.controller.reset_selected_run,
        ).pack(side="right")

    def _summary_metric(self, parent, column, caption, variable, money=False, large=False):
        group = self._frame(parent)
        self._label(group, text=caption, font=("Segoe UI Semibold", 7), muted=True, anchor="w").pack(fill="x")
        self._label(
            group,
            variable=variable,
            font=("Segoe UI Semibold", 12 if large else 10),
            money=money,
            anchor="w",
        ).pack(fill="x", pady=(3, 0))
        return group

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
        self.base_var.set(format_dashboard_currency(base))
        self.actual_var.set(format_dashboard_currency(aggregate["total"]))
        self.progress_var.set(self.controller.progress_text(aggregate, route))
        self.remaining_var.set(format_dashboard_currency(aggregate["remaining_base"]))

        settings = self.app.state_data.setdefault(
            "earnings_settings", dict(DEFAULT_EARNINGS_SETTINGS)
        )
        for row in projection_rows(base, settings):
            gross, price, net = self.projection_vars[row["name"]]
            gross.set(format_dashboard_currency(row["gross"]))
            price.set(
                "—"
                if row["price"] == 0 and row["name"] == "No charm"
                else format_dashboard_currency(row["price"])
            )
            net.set(format_dashboard_currency(row["net"]))

        self._apply_custom_theme()

    def _apply_custom_theme(self):
        theme = self.app.theme()
        try:
            self.configure(bg=theme["bg"])
            for frame in self._themed_frames:
                frame.configure(bg=theme["bg"])
            for card in self._card_frames:
                card.configure(
                    bg=theme["card_bg"],
                    highlightbackground=theme["card_border"],
                )
                self._theme_descendants(card, theme["card_bg"])
            for label in self._normal_labels:
                parent_bg = self._parent_background(label, theme)
                label.configure(bg=parent_bg, fg=theme["text"])
            for label in self._muted_labels:
                parent_bg = self._parent_background(label, theme)
                label.configure(bg=parent_bg, fg=theme["muted"])
            for label in self._money_labels:
                parent_bg = self._parent_background(label, theme)
                label.configure(bg=parent_bg, fg=theme["money"])
            for entry in self._entries:
                entry.configure(
                    bg=theme["field_bg"],
                    fg=theme["field_fg"],
                    insertbackground=theme["field_fg"],
                    highlightbackground=theme["control_border"],
                    highlightcolor=theme["accent"],
                )
            for index, row in enumerate(self.projection_rows):
                row.configure(bg=theme["panel_dark"] if index % 2 else theme["card_bg"])
                self._theme_row_labels(row, theme)
        except tk.TclError:
            pass

    def _parent_background(self, widget, theme):
        parent = widget.master
        try:
            return parent.cget("bg")
        except tk.TclError:
            return theme["bg"]

    def _theme_descendants(self, widget, background):
        for child in widget.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=background)
                self._theme_descendants(child, background)

    def _theme_row_labels(self, row, theme):
        background = row.cget("bg")
        for child in row.winfo_children():
            if not isinstance(child, tk.Label):
                continue
            if child in self._money_labels:
                child.configure(bg=background, fg=theme["money"])
            elif child in self._muted_labels:
                child.configure(bg=background, fg=theme["muted"])
            else:
                child.configure(bg=background, fg=theme["text"])


def install_dashboard_earnings_window(app):
    controller = getattr(app, "_earnings_controller", None)
    if controller is None:
        return None

    def open_dashboard_calculator():
        if controller.window is not None and controller.window.winfo_exists():
            controller.window.deiconify()
            controller.window.lift()
            controller.window.focus_force()
            controller.window.refresh()
            return
        controller.window = DashboardEarningsWindow(controller)

    controller.open_calculator = open_dashboard_calculator
    return controller
