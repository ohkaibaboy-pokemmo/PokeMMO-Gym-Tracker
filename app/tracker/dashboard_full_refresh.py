"""Full-view visual refresh for the v0.6 dashboard.

This layer intentionally touches only the Full-view header. Compact and Detector
remain unchanged. It reuses the existing dashboard status/earnings variables, so
no tracker or accounting behaviour is duplicated here.
"""

import tkinter as tk
from tkinter import ttk


class FullViewRefresh:
    def __init__(self, app):
        self.app = app
        self.shell = getattr(app, "_dashboard_shell", None)
        if self.shell is None:
            raise RuntimeError("Dashboard shell must be installed first")

        # Retire only the visible v0.6 header. Its variables/widgets stay alive as
        # the model/presentation source for this refreshed header.
        try:
            self.shell.header.pack_forget()
        except tk.TclError:
            pass

        self._money_traces = []
        self._build()
        # App.restore_full_view() calls app.apply_theme() after Compact is closed.
        # The legacy generic theme walker visits every Tk Label and can overwrite
        # the semantic KPI/money colours in this refreshed header. DashboardShell
        # already reapplies its own (now hidden) header afterwards, so this visible
        # refresh must also be the final theme pass every time app.apply_theme runs.
        self._wrap_app_theme()
        self.apply_theme()
        app.theme_var.trace_add("write", self._theme_changed)
        app._full_view_refresh = self

        # DashboardScalingController already calls shell.apply_scale(). Hook that
        # existing component point instead of introducing another scaling system.
        original_scale = self.shell.apply_scale
        if not getattr(original_scale, "_full_view_refresh_wrapped", False):
            def scale_with_refresh(factor=1.0):
                result = original_scale(factor)
                self.apply_scale(factor)
                return result

            scale_with_refresh._full_view_refresh_wrapped = True
            self.shell.apply_scale = scale_with_refresh

    def _wrap_app_theme(self):
        """Ensure semantic Full-header colours survive every global theme pass."""
        original = self.app.apply_theme
        if getattr(original, "_full_view_refresh_theme_wrapped", False):
            return

        def apply_with_full_refresh(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_theme()
            return result

        apply_with_full_refresh._full_view_refresh_theme_wrapped = True
        self.app.apply_theme = apply_with_full_refresh

    def _build(self):
        self.header = tk.Frame(self.app, bd=0)
        self.header.pack(
            fill="x",
            padx=20,
            pady=(14, 8),
            before=self.shell.control_panel,
        )
        self.header.columnconfigure(0, weight=0)
        self.header.columnconfigure(1, weight=1)

        # --- Brand / hero -----------------------------------------------------
        self.brand = tk.Frame(self.header, bd=0)
        self.brand.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 28))

        self.brand_icon = tk.Canvas(
            self.brand,
            width=68,
            height=68,
            bd=0,
            highlightthickness=0,
            takefocus=False,
        )
        self.brand_icon.pack(side="left", padx=(0, 14), pady=(1, 0))

        self.brand_text = tk.Frame(self.brand, bd=0)
        self.brand_text.pack(side="left", anchor="n", pady=(1, 0))
        self.title_label = tk.Label(
            self.brand_text,
            text="Gym Rerun Tracker",
            font=("Segoe UI Semibold", 20),
            anchor="w",
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            self.brand_text,
            text="Cooldowns  •  5-Rule  •  Routes  •  Earnings",
            font=("Segoe UI Semibold", 9),
            anchor="w",
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))

        # --- Full-view mode / live row ---------------------------------------
        self.mode_row = tk.Frame(self.header, bd=0)
        self.mode_row.grid(row=0, column=1, sticky="ew", pady=(0, 6))
        # Compact View is the primary mode action, so keep it on the outermost
        # top-right edge. The passive live-log status sits immediately to its left.
        self.compact_button = ttk.Button(
            self.mode_row,
            text="Compact View",
            command=self.app.open_compact_view,
        )
        self.compact_button.pack(side="right")
        self.live_label = tk.Label(
            self.mode_row,
            textvariable=self.app.status_var,
            font=("Segoe UI", 8),
            anchor="e",
        )
        self.live_label.pack(side="right", padx=(0, 10))
        self.app.compact_view_button = self.compact_button

        # --- Compact KPI row --------------------------------------------------
        self.summary = tk.Frame(self.header, bd=0)
        self.summary.grid(row=1, column=1, sticky="ew")
        for index in range(4):
            self.summary.columnconfigure(
                index,
                weight=(4 if index == 3 else 1),
                uniform="full_refresh_summary",
            )

        self.stat_cards = {}
        for column, (key, caption_text) in enumerate(
            (("ready", "READY"), ("waiting", "WAITING"), ("cooldown", "COOLDOWN"))
        ):
            card = tk.Frame(self.summary, bd=0, highlightthickness=1)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 7))
            caption = tk.Label(
                card,
                text=caption_text,
                font=("Segoe UI Semibold", 7),
                anchor="w",
            )
            caption.pack(fill="x", padx=10, pady=(6, 0))
            count = tk.Label(
                card,
                textvariable=self.shell.stat_cards[key]["var"],
                font=("Segoe UI Semibold", 15),
                anchor="w",
            )
            count.pack(fill="x", padx=10, pady=(0, 6))
            self.stat_cards[key] = {"frame": card, "caption": caption, "count": count}

        self.earnings_card = tk.Frame(self.summary, bd=0, highlightthickness=1)
        self.earnings_card.grid(row=0, column=3, sticky="nsew")
        self.earnings_card.columnconfigure(0, weight=2)
        self.earnings_card.columnconfigure(1, weight=3)

        self.earnings_primary = tk.Frame(self.earnings_card, bd=0)
        self.earnings_primary.grid(row=0, column=0, sticky="nsew", padx=(11, 12), pady=6)
        self.earnings_title = tk.Label(
            self.earnings_primary,
            text="RUN EARNINGS",
            font=("Segoe UI Semibold", 7),
            anchor="w",
        )
        self.earnings_title.pack(anchor="w")
        self.run_money_var = self._money_var(self.shell._earnings_var("actual_var"))
        self.run_money_label = tk.Label(
            self.earnings_primary,
            textvariable=self.run_money_var,
            font=("Segoe UI Semibold", 15),
            anchor="w",
        )
        self.run_money_label.pack(anchor="w", pady=(1, 0))

        self.earnings_metrics_host = tk.Frame(self.earnings_card, bd=0)
        self.earnings_metrics_host.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=5)
        self.earnings_metrics_host.columnconfigure(0, weight=1)
        self.earnings_metrics_host.columnconfigure(1, weight=1)

        metric_specs = (
            ("ROUTE BASE", "base_var", True),
            ("ACTUAL RUN", "actual_var", True),
            ("ROUTE GYMS", "gyms_var", False),
            ("OTHER PAYOUTS", "other_var", True),
        )
        self.earnings_metrics = []
        for index, (caption_text, attr, is_money) in enumerate(metric_specs):
            row, column = divmod(index, 2)
            group = tk.Frame(self.earnings_metrics_host, bd=0)
            group.grid(
                row=row,
                column=column,
                sticky="w",
                padx=(0, 12) if column == 0 else 0,
                pady=(0, 3) if row == 0 else 0,
            )
            caption = tk.Label(group, text=caption_text, font=("Segoe UI", 6), anchor="w")
            caption.pack(anchor="w")
            source = self.shell._earnings_var(attr)
            variable = self._money_var(source) if is_money else source
            value = tk.Label(group, textvariable=variable, font=("Segoe UI Semibold", 8), anchor="w")
            value.pack(anchor="w")
            self.earnings_metrics.append((group, caption, value, is_money))

    def _money_var(self, source):
        target = tk.StringVar(master=self.app, value=self.shell._as_dollar(source.get()))

        def changed(*_args):
            target.set(self.shell._as_dollar(source.get()))

        trace_id = source.trace_add("write", changed)
        self._money_traces.append((source, trace_id))
        return target

    def _theme_changed(self, *_args):
        try:
            self.app.after_idle(self.apply_theme)
        except tk.TclError:
            pass

    def apply_scale(self, factor=1.0):
        try:
            factor = float(factor)
        except (TypeError, ValueError):
            factor = 1.0
        size = max(50, int(round(68 * factor)))
        try:
            self.brand_icon.configure(width=size, height=size)
        except tk.TclError:
            pass
        self._draw_brand_icon()

    def _draw_brand_icon(self):
        """Draw the muted-grey Poké Ball mark used by the approved concept."""
        theme = self.app.theme()
        canvas = self.brand_icon
        try:
            canvas.delete("all")
            canvas.configure(bg=theme["bg"])
            width = max(48, int(canvas.cget("width")))
            height = max(48, int(canvas.cget("height")))
        except tk.TclError:
            return

        size = min(width, height)
        inset = max(3, round(size * 0.07))
        x1 = (width - size) / 2 + inset
        y1 = (height - size) / 2 + inset
        x2 = (width + size) / 2 - inset
        y2 = (height + size) / 2 - inset
        cy = (y1 + y2) / 2
        cx = (x1 + x2) / 2

        outer = "#3f4a52"
        edge = "#20292f"
        highlight = "#59646c"
        centre = "#748089"

        canvas.create_oval(x1, y1, x2, y2, fill=outer, outline=edge, width=max(2, round(size * 0.035)))
        band_h = max(6, round(size * 0.12))
        canvas.create_rectangle(x1 + 1, cy - band_h / 2, x2 - 1, cy + band_h / 2, fill=edge, outline="")
        radius = max(9, round(size * 0.18))
        canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=edge, outline="")
        inner = max(5, round(radius * 0.55))
        canvas.create_oval(cx - inner, cy - inner, cx + inner, cy + inner, fill=centre, outline=highlight, width=1)
        # A restrained upper highlight keeps the mark dimensional without making
        # it look like the red/white Poké Ball used by the executable icon.
        canvas.create_arc(
            x1 + 4,
            y1 + 4,
            x2 - 4,
            y2 - 4,
            start=25,
            extent=130,
            style="arc",
            outline=highlight,
            width=max(1, round(size * 0.025)),
        )

    def apply_theme(self):
        theme = self.app.theme()
        try:
            for frame in (self.header, self.brand, self.brand_text, self.mode_row, self.summary):
                frame.configure(bg=theme["bg"])
            self.title_label.configure(bg=theme["bg"], fg=theme["text"])
            self.subtitle_label.configure(bg=theme["bg"], fg=theme["muted"])
            self.live_label.configure(bg=theme["bg"], fg=theme["live"])

            colours = {
                "ready": theme["ready"],
                "waiting": theme["waiting"],
                "cooldown": theme["cooldown"],
            }
            for key, widgets in self.stat_cards.items():
                widgets["frame"].configure(
                    bg=theme["card_bg"],
                    highlightbackground=theme["card_border"],
                )
                widgets["caption"].configure(bg=theme["card_bg"], fg=colours[key])
                widgets["count"].configure(bg=theme["card_bg"], fg=colours[key])

            self.earnings_card.configure(
                bg=theme["card_bg"],
                highlightbackground=theme["card_border"],
            )
            for frame in (self.earnings_primary, self.earnings_metrics_host):
                frame.configure(bg=theme["card_bg"])
            self.earnings_title.configure(bg=theme["card_bg"], fg=theme["money"])
            self.run_money_label.configure(bg=theme["card_bg"], fg=theme["money"])
            for group, caption, value, is_money in self.earnings_metrics:
                group.configure(bg=theme["card_bg"])
                caption.configure(bg=theme["card_bg"], fg=theme["muted"])
                value.configure(
                    bg=theme["card_bg"],
                    fg=theme["money"] if is_money else theme["text"],
                )
        except tk.TclError:
            pass
        self._draw_brand_icon()


def install_full_view_refresh(app):
    existing = getattr(app, "_full_view_refresh", None)
    if existing is not None:
        return existing
    return FullViewRefresh(app)
