"""Split the Full dashboard earnings block into one KPI plus one detail card.

Live design review found that Run Earnings now visually matches Ready/Waiting/
Cooldown, but its old combined card still made it structurally different. This
layer preserves the proven variables/accounting and replaces only the visible
header composition:

Ready | Waiting | Cooldown | Run Earnings | Run Details

The first four cards share the same headline KPI grammar. Supporting earnings
metrics live in one wider horizontal card to the right.
"""

import tkinter as tk

from .scaling import factor_for, scaled


HEADLINE_COLUMNS = (0, 1, 2, 3)
DETAIL_COLUMN = 4
# The fifth headline KPI added by NEXT READY reduced the physical width available
# to this supporting card. Live Windows review then clipped both "Route gyms" and
# its All-characters value (for example "31 payouts"). Keep Run Details visibly
# wider than a headline card so all four supporting metrics have usable width.
DETAIL_WEIGHT = 4
DETAILS_TITLE_COLOURS = {
    "Dark": "#8FAEBF",
    "PokeMMO": "#91ADB6",
    "Light": "#557487",
}
DETAIL_METRIC_LABELS = (
    "Route base",
    "Actual run",
    "Route gyms",
    "Other payouts",
)
# Build 38 proved the outer breathing room was not the real vertical clipping
# source: on Windows the tiny caption widget can still occupy almost the full old
# 13px offset, so the value widget may paint over the caption's lowest antialiased
# pixels. Keep the 2px top inset but open the caption/value separation by 3px and
# grow the group by 4px so values retain comfortable bottom breathing room.
DETAIL_METRIC_VALUE_Y_BASE = 16
DETAIL_METRIC_TOP_PADDING_BASE = 2
DETAIL_METRIC_GROUP_HEIGHT_BASE = 40
# With five headline KPIs, the old 12px inter-metric gutters also consumed too
# much of the Run Details card. Eight pixels keeps the four groups visually
# separated while giving long captions/values more room. Cap scaled gutters so
# UI scaling does not reintroduce horizontal clipping.
DETAIL_METRIC_COLUMN_GAP_BASE = 8
DETAIL_METRIC_COLUMN_GAP_MAX = 10
# Matching grid rows still left RUN DETAILS a couple of pixels below neighbouring
# KPI titles under Windows font metrics, so lift it slightly within the upper row.
DETAILS_TITLE_BASELINE_LIFT_BASE = 2


def earnings_summary_column_weights():
    """Return the adopted four-headline-plus-detail grid proportions."""
    return (1, 1, 1, 1, DETAIL_WEIGHT)


def run_details_title_colour(theme_name="Dark"):
    """Return a restrained non-semantic accent for the Run Details heading."""
    return DETAILS_TITLE_COLOURS.get(str(theme_name), DETAILS_TITLE_COLOURS["Dark"])


def run_details_metric_labels():
    """Return secondary labels that read below, not alongside, the card title."""
    return DETAIL_METRIC_LABELS


def run_details_metric_top_padding(factor=1.0):
    """Return the small scale-aware inset that prevents top-edge text clipping."""
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    factor = max(0.85, factor)
    return max(2, int(round(DETAIL_METRIC_TOP_PADDING_BASE * factor)))


def run_details_metric_column_gap(factor=1.0):
    """Return a compact scale-aware horizontal gutter for Run Details metrics."""
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    factor = max(0.85, factor)
    return min(
        DETAIL_METRIC_COLUMN_GAP_MAX,
        max(6, int(round(DETAIL_METRIC_COLUMN_GAP_BASE * factor))),
    )


def run_details_metric_geometry(factor=1.0):
    """Return label/value geometry with safe Windows line separation."""
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    factor = max(0.85, factor)
    top_padding = run_details_metric_top_padding(factor)
    label_value_gap = max(15, int(round(DETAIL_METRIC_VALUE_Y_BASE * factor)))
    value_y = top_padding + label_value_gap
    group_height = max(36, int(round(DETAIL_METRIC_GROUP_HEIGHT_BASE * factor)))
    return value_y, group_height


def run_details_title_baseline_lift(factor=1.0):
    """Return the small Windows baseline correction for the Run Details title."""
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    factor = max(0.85, factor)
    return max(1, int(round(DETAILS_TITLE_BASELINE_LIFT_BASE * factor)))


class DashboardEarningsSplit:
    def __init__(self, app):
        self.app = app
        self.full = getattr(app, "_full_view_refresh", None)
        self.polish = getattr(app, "_dashboard_final_polish", None)
        self.alignment = getattr(app, "_dashboard_kpi_alignment", None)
        if self.full is None or self.polish is None or self.alignment is None:
            raise RuntimeError("Earnings split requires Full refresh, polish and KPI alignment")

        self.metric_widgets = []
        self._build()
        self._wrap_theme()
        self._wrap_scale()
        self.apply_scale()
        self.apply_theme()
        app._dashboard_earnings_split = self

    def _configure_summary_columns(self):
        summary = self.full.summary
        for column in range(5):
            summary.columnconfigure(column, weight=0, minsize=0, uniform="")
        for column in HEADLINE_COLUMNS:
            summary.columnconfigure(column, weight=1, uniform="headline_kpi")
        summary.columnconfigure(DETAIL_COLUMN, weight=DETAIL_WEIGHT, uniform="")

    def _build(self):
        self._configure_summary_columns()

        # Retire the old mixed-purpose card but keep it alive as an implementation
        # detail so existing StringVar traces remain valid.
        self.legacy_earnings_card = self.full.earnings_card
        try:
            self.legacy_earnings_card.grid_forget()
        except tk.TclError:
            pass

        summary = self.full.summary

        # --- Headline Run Earnings KPI ---------------------------------------
        self.run_card = tk.Frame(summary, bd=0, highlightthickness=1)
        self.run_card.grid(row=0, column=3, sticky="nsew", padx=(0, 7))
        self.run_card.columnconfigure(1, weight=1)
        self.run_card.grid_rowconfigure(0, weight=1)
        self.run_card.grid_rowconfigure(1, weight=1)

        self.run_icon = tk.Canvas(
            self.run_card,
            width=40,
            height=40,
            bd=0,
            highlightthickness=0,
            takefocus=False,
        )
        self.run_icon.grid(row=0, column=0, rowspan=2, sticky="w", padx=(10, 8), pady=0)

        self.run_title = tk.Label(
            self.run_card,
            text="RUN EARNINGS",
            font=("Segoe UI Semibold", 7),
            anchor="w",
        )
        self.run_title.grid(row=0, column=1, sticky="sw", padx=(0, 10), pady=0)

        self.run_value = tk.Label(
            self.run_card,
            textvariable=self.full.run_money_var,
            font=("Segoe UI Semibold", 15),
            anchor="w",
        )
        self.run_value.grid(row=1, column=1, sticky="nw", padx=(0, 10), pady=0)

        # Point the already-proven final-polish/alignment layers at the new KPI.
        self.full.earnings_primary = self.run_card
        self.full.earnings_title = self.run_title
        self.full.run_money_label = self.run_value
        self.polish.kpi_icons["earnings"] = self.run_icon

        # --- Supporting Run Details card ------------------------------------
        self.details_card = tk.Frame(summary, bd=0, highlightthickness=1)
        self.details_card.grid(row=0, column=4, sticky="nsew")
        self.details_card.columnconfigure(0, weight=1)
        # Mirror the headline KPI row geometry so RUN DETAILS shares the same
        # vertical title baseline as READY / WAITING / COOLDOWN / RUN EARNINGS.
        self.details_card.grid_rowconfigure(0, weight=1)
        self.details_card.grid_rowconfigure(1, weight=1)

        self.details_title = tk.Label(
            self.details_card,
            text="RUN DETAILS",
            font=("Segoe UI Semibold", 7),
            anchor="w",
        )
        title_lift = run_details_title_baseline_lift(1.0)
        self.details_title.grid(row=0, column=0, sticky="sw", padx=11, pady=(0, title_lift))

        self.details_host = tk.Frame(self.details_card, bd=0)
        self.details_host.grid(row=1, column=0, sticky="nsew", padx=11, pady=0)
        for column in range(4):
            self.details_host.columnconfigure(column, weight=1, uniform="run_details")

        metric_specs = (
            (DETAIL_METRIC_LABELS[0], "base_var", True),
            (DETAIL_METRIC_LABELS[1], "actual_var", True),
            (DETAIL_METRIC_LABELS[2], "gyms_var", False),
            (DETAIL_METRIC_LABELS[3], "other_var", True),
        )
        top_padding = run_details_metric_top_padding(1.0)
        column_gap = run_details_metric_column_gap(1.0)
        value_y, group_height = run_details_metric_geometry(1.0)
        for column, (caption_text, attr, is_money) in enumerate(metric_specs):
            group = tk.Frame(self.details_host, bd=0, height=group_height)
            group.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0, column_gap) if column < 3 else 0,
            )
            group.grid_propagate(False)
            # Keep the caption itself in the same position; only the value starts
            # lower so Windows cannot overpaint the caption's descenders/edge pixels.
            caption = tk.Label(group, text=caption_text, font=("Segoe UI", 6), anchor="w")
            caption.place(x=0, y=top_padding)
            source = self.full.shell._earnings_var(attr)
            variable = self.full._money_var(source) if is_money else source
            value = tk.Label(group, textvariable=variable, font=("Segoe UI Semibold", 8), anchor="w")
            value.place(x=0, y=value_y)
            self.metric_widgets.append((group, caption, value, is_money))

        # Re-run alignment now that the earnings KPI has moved to its own card.
        self.alignment.apply()

    def _wrap_theme(self):
        original = self.polish.apply_theme
        if getattr(original, "_earnings_split_wrapped", False):
            return

        def apply_theme_with_split(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_theme()
            return result

        apply_theme_with_split._earnings_split_wrapped = True
        self.polish.apply_theme = apply_theme_with_split

    def _wrap_scale(self):
        original = self.polish.apply_scale
        if getattr(original, "_earnings_split_wrapped", False):
            return

        def apply_scale_with_split(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_scale()
            return result

        apply_scale_with_split._earnings_split_wrapped = True
        self.polish.apply_scale = apply_scale_with_split

    def apply_scale(self):
        factor = factor_for(self.app)
        top_padding = run_details_metric_top_padding(factor)
        column_gap = run_details_metric_column_gap(factor)
        value_y, group_height = run_details_metric_geometry(factor)
        title_lift = run_details_title_baseline_lift(factor)
        try:
            self.details_title.configure(font=("Segoe UI Semibold", scaled(7, factor, 6)))
            self.details_title.grid_configure(pady=(0, title_lift))
            for index, (group, caption, value, _is_money) in enumerate(self.metric_widgets):
                # Preserve the accepted fonts and caption position while keeping
                # enough horizontal room for longer labels/All-characters values.
                caption.configure(font=("Segoe UI", scaled(6, factor, 6)))
                value.configure(font=("Segoe UI Semibold", scaled(8, factor, 7)))
                group.configure(height=group_height)
                group.grid_configure(padx=(0, column_gap) if index < 3 else 0)
                caption.place_configure(x=0, y=top_padding)
                value.place_configure(x=0, y=value_y)
        except tk.TclError:
            pass
        # The KPI alignment layer owns headline icon/text geometry.
        try:
            self.alignment.apply()
        except (AttributeError, tk.TclError):
            pass

    def apply_theme(self):
        theme = self.app.theme()
        try:
            for card in (self.run_card, self.details_card):
                card.configure(bg=theme["card_bg"], highlightbackground=theme["card_border"])
            self.run_title.configure(bg=theme["card_bg"], fg=theme["money"])
            self.run_value.configure(bg=theme["card_bg"], fg=theme["money"])
            self.details_title.configure(
                bg=theme["card_bg"],
                fg=run_details_title_colour(self.app.theme_var.get()),
            )
            self.details_host.configure(bg=theme["card_bg"])
            for group, caption, value, is_money in self.metric_widgets:
                group.configure(bg=theme["card_bg"])
                caption.configure(bg=theme["card_bg"], fg=theme["muted"])
                value.configure(
                    bg=theme["card_bg"],
                    fg=theme["money"] if is_money else theme["text"],
                )
        except tk.TclError:
            pass
        try:
            self.polish._draw_kpi_icons()
        except (AttributeError, tk.TclError):
            pass


def install_dashboard_earnings_split(app):
    existing = getattr(app, "_dashboard_earnings_split", None)
    if existing is not None:
        return existing
    return DashboardEarningsSplit(app)
