"""Small final-pass dashboard polish found during Windows release validation.

This module intentionally sits on top of the already-live-confirmed Canvas dashboard.
It does not replace the underlying tracker model or redraw architecture. It only
clarifies current-run semantics, improves chrome hierarchy, and fixes a few native
Windows ttk/focus rough edges observed immediately before vanilla live testing.
"""

from datetime import datetime
import tkinter as tk
from tkinter import ttk

from .earnings import GYM_BASE_PAYOUTS
from .scaling import factor_for, scaled
from .state import save_state


REGION_COLOURS_DARK = {
    # Kanto deliberately uses a cool neutral instead of red: region accents are
    # navigation aids, not warning/error semantics.
    "Kanto": "#A6B7C3",
    "Johto": "#D7A946",
    "Hoenn": "#65A5E8",
    "Sinnoh": "#9785E6",
    "Unova": "#62B5A3",
}
REGION_COLOURS_POKEMMO = {
    "Kanto": "#B4C2C8",
    "Johto": "#D6B45C",
    "Hoenn": "#79AFC6",
    "Sinnoh": "#A79AC4",
    "Unova": "#7AB7A7",
}
REGION_COLOURS_LIGHT = {
    "Kanto": "#5C7180",
    "Johto": "#8A6100",
    "Hoenn": "#2F6FAF",
    "Sinnoh": "#624DB1",
    "Unova": "#247765",
}

FILTER_LABELS = {
    "Character": "◉  Character",
    "Region": "⌖  Region",
    "Route / order": "≡  Route / order",
    "Display": "▤  Display",
    "UI Scale": "↕  UI Scale",
    "Theme": "◆  Theme",
}
CARD_LABELS = {
    "ready": "READY",
    "waiting": "WAITING",
    "cooldown": "COOLDOWN",
}
KPI_ICON_BASE_SIZE = 30


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def migrate_known_only_state(state):
    """Collapse the old duplicate Known-only mode into All + Hide unknown."""
    if not isinstance(state, dict) or state.get("display_filter") != "Known only":
        return False
    state["display_filter"] = "All"
    state["hide_unknown"] = True
    return True


def payout_is_current(record, character):
    """Return True only when the row payout belongs to the current run window."""
    if not isinstance(record, dict) or not isinstance(character, dict):
        return False
    payout_at = _parse_dt(record.get("payout_at"))
    run_started = _parse_dt(character.get("earnings", {}).get("run_started_at"))
    return bool(payout_at and run_started and payout_at >= run_started)


def current_run_row_payout(leader, record, character):
    """Return (amount, actual_this_run) for the Full payout column.

    Historical empirical payouts remain in state, but after Reset Run the dashboard
    returns to the muted route/base value. Gold therefore means "paid this run",
    which matches the Run Earnings card instead of implying old money is current.
    """
    base = int(GYM_BASE_PAYOUTS.get(leader, 0))
    if payout_is_current(record, character):
        try:
            return int(record.get("payout")), True
        except (TypeError, ValueError):
            pass
    return base, False


def region_colour(region, theme_name="Dark"):
    text = str(region or "").replace("[", "").replace("]", "").strip()
    if str(theme_name) == "Light":
        palette = REGION_COLOURS_LIGHT
    elif str(theme_name) == "PokeMMO":
        palette = REGION_COLOURS_POKEMMO
    else:
        palette = REGION_COLOURS_DARK
    return palette.get(text)


def _walk(root):
    stack = [root]
    while stack:
        widget = stack.pop()
        yield widget
        try:
            stack.extend(widget.winfo_children())
        except tk.TclError:
            pass


class DashboardFinalPolish:
    def __init__(self, app):
        self.app = app
        self.full = getattr(app, "_full_view_refresh", None)
        self.shell = getattr(app, "_dashboard_shell", None)
        self.gym_list = getattr(app, "_dashboard_gym_list", None)
        self.scaling = getattr(app, "_scaling_controller", None)
        if self.full is None or self.shell is None or self.gym_list is None:
            raise RuntimeError("Final polish requires the Full dashboard components")

        self.live_below = None
        self.kpi_icons = {}
        self._migrate_display_filter()
        self._decorate_header()
        self._decorate_kpis()
        self._decorate_filter_labels()
        self._group_action_buttons()
        self._wrap_row_payout()
        self._wrap_region_style()
        self._fix_combobox_arrow_map()
        self._fix_scale_focus()
        # FullViewRefresh already reapplies its semantic colours after the legacy
        # global theme walker. Final-polish colours must be the final pass after
        # that too, otherwise status metadata can turn blue and UNKNOWN regions
        # can fall back to purple after Compact -> Full.
        self._wrap_app_theme()
        self.apply_scale()
        self.apply_theme()

        app.theme_var.trace_add("write", lambda *_args: app.after_idle(self.apply_theme))
        scale_var = getattr(app, "ui_scale_var", None)
        if scale_var is not None:
            scale_var.trace_add("write", lambda *_args: app.after_idle(self.apply_scale))
        app._dashboard_final_polish = self

    def _wrap_app_theme(self):
        original = self.app.apply_theme
        if getattr(original, "_dashboard_final_polish_theme_wrapped", False):
            return

        def apply_with_final_polish(*args, **kwargs):
            result = original(*args, **kwargs)
            self.apply_theme()
            return result

        apply_with_final_polish._dashboard_final_polish_theme_wrapped = True
        self.app.apply_theme = apply_with_final_polish

    def _migrate_display_filter(self):
        changed = migrate_known_only_state(self.app.state_data)
        if self.app.display_var.get() == "Known only":
            self.app.display_var.set("All")
            self.app.hide_unknown_var.set(True)
            changed = True
        if changed:
            self.app.state_data["display_filter"] = "All"
            self.app.state_data["hide_unknown"] = True
            save_state(self.app.state_data)
            self.app.refresh_table()

    def _decorate_header(self):
        # The passive log status reads better as metadata beneath the subtitle,
        # leaving Compact View as the only top-right mode action.
        try:
            self.full.live_label.pack_forget()
        except tk.TclError:
            pass
        self.live_below = tk.Label(
            self.full.brand_text,
            textvariable=self.app.status_var,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.live_below.pack(anchor="w", pady=(3, 0))

    def _make_kpi_icon(self, parent):
        icon = tk.Canvas(
            parent,
            width=KPI_ICON_BASE_SIZE,
            height=KPI_ICON_BASE_SIZE,
            bd=0,
            highlightthickness=0,
            takefocus=False,
        )
        return icon

    def _decorate_kpis(self):
        # Every primary KPI uses one shared visual grammar from the art concept:
        # a substantial leading icon, then a two-line title/value text block.
        for key, title in CARD_LABELS.items():
            widgets = self.full.stat_cards.get(key)
            if not widgets:
                continue
            card = widgets["frame"]
            caption = widgets["caption"]
            count = widgets["count"]
            try:
                caption.pack_forget()
                count.pack_forget()
                card.columnconfigure(1, weight=1)
                icon = self._make_kpi_icon(card)
                icon.grid(row=0, column=0, rowspan=2, sticky="w", padx=(10, 8), pady=7)
                caption.configure(text=title)
                caption.grid(row=0, column=1, sticky="sw", padx=(0, 10), pady=(5, 0))
                count.grid(row=1, column=1, sticky="nw", padx=(0, 10), pady=(0, 5))
                self.kpi_icons[key] = icon
            except tk.TclError:
                pass

        # Run Earnings gets the same icon/title/value arrangement. The icon is a
        # project-owned stacked-coin mark matching the approved concept rather
        # than the temporary circular-dollar badge from build 21.
        try:
            self.full.earnings_title.pack_forget()
            self.full.run_money_label.pack_forget()
            self.full.earnings_primary.columnconfigure(1, weight=1)
            icon = self._make_kpi_icon(self.full.earnings_primary)
            icon.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 8), pady=3)
            self.full.earnings_title.grid(row=0, column=1, sticky="sw", pady=(0, 0))
            self.full.run_money_label.grid(row=1, column=1, sticky="nw", pady=(0, 0))
            self.kpi_icons["earnings"] = icon
        except tk.TclError:
            pass

    @staticmethod
    def _icon_size(canvas):
        try:
            return max(20, min(int(float(canvas.cget("width"))), int(float(canvas.cget("height")))))
        except (tk.TclError, TypeError, ValueError):
            return KPI_ICON_BASE_SIZE

    def _prepare_icon(self, canvas):
        theme = self.app.theme()
        try:
            canvas.delete("all")
            canvas.configure(bg=theme["card_bg"])
        except tk.TclError:
            pass
        return theme, self._icon_size(canvas)

    def _draw_ready_icon(self, canvas):
        theme, size = self._prepare_icon(canvas)
        pad = max(2, int(round(size * 0.13)))
        width = max(2, int(round(size * 0.08)))
        try:
            canvas.create_oval(
                pad, pad, size - pad, size - pad,
                fill=theme["ready_bg"], outline=theme["ready"], width=width,
            )
            canvas.create_line(
                size * 0.28, size * 0.52,
                size * 0.43, size * 0.67,
                size * 0.72, size * 0.35,
                fill=theme["ready"], width=max(2, int(round(size * 0.10))),
                capstyle="round", joinstyle="round",
            )
        except tk.TclError:
            pass

    def _draw_waiting_icon(self, canvas):
        theme, size = self._prepare_icon(canvas)
        x1, x2 = size * 0.24, size * 0.76
        top, bottom = size * 0.18, size * 0.82
        mid = size * 0.50
        line = max(2, int(round(size * 0.07)))
        try:
            canvas.create_line(x1, top, x2, top, fill=theme["waiting"], width=line)
            canvas.create_line(x1, bottom, x2, bottom, fill=theme["waiting"], width=line)
            canvas.create_polygon(
                x1 + 2, top + 3, x2 - 2, top + 3, size * 0.50, mid - 1,
                fill=theme["waiting"], outline="",
            )
            canvas.create_polygon(
                size * 0.50, mid + 1, x1 + 3, bottom - 3, x2 - 3, bottom - 3,
                fill=theme["waiting_bg"], outline=theme["waiting"], width=1,
            )
        except tk.TclError:
            pass

    def _draw_cooldown_icon(self, canvas):
        theme, size = self._prepare_icon(canvas)
        pad = max(2, int(round(size * 0.13)))
        width = max(2, int(round(size * 0.08)))
        cx = cy = size / 2.0
        try:
            canvas.create_oval(
                pad, pad, size - pad, size - pad,
                fill=theme["cooldown_bg"], outline=theme["cooldown"], width=width,
            )
            canvas.create_line(
                cx, cy, cx, size * 0.31,
                fill=theme["cooldown"], width=width, capstyle="round",
            )
            canvas.create_line(
                cx, cy, size * 0.68, size * 0.59,
                fill=theme["cooldown"], width=width, capstyle="round",
            )
            canvas.create_oval(
                cx - width, cy - width, cx + width, cy + width,
                fill=theme["cooldown"], outline="",
            )
        except tk.TclError:
            pass

    def _draw_earnings_icon(self, canvas):
        theme, size = self._prepare_icon(canvas)
        gold = theme["money"]
        shadow = theme["money_shadow"]
        sx = size / 32.0
        sy = size / 32.0

        def rect(x1, y1, x2, y2, fill):
            canvas.create_rectangle(
                round(x1 * sx), round(y1 * sy), round(x2 * sx), round(y2 * sy),
                fill=fill, outline="",
            )

        try:
            # Four offset stacks reproduce the simple chunky coin-stack silhouette
            # from the art concept without embedding any external/game asset.
            rect(4, 5, 20, 9, shadow)
            rect(3, 4, 19, 8, gold)
            rect(2, 11, 18, 15, shadow)
            rect(1, 10, 17, 14, gold)
            rect(5, 17, 21, 21, shadow)
            rect(4, 16, 20, 20, gold)
            rect(8, 23, 24, 27, shadow)
            rect(7, 22, 23, 26, gold)
        except tk.TclError:
            pass

    def _draw_kpi_icons(self):
        drawers = {
            "ready": self._draw_ready_icon,
            "waiting": self._draw_waiting_icon,
            "cooldown": self._draw_cooldown_icon,
            "earnings": self._draw_earnings_icon,
        }
        for key, canvas in self.kpi_icons.items():
            drawer = drawers.get(key)
            if drawer is not None:
                drawer(canvas)

    def _decorate_filter_labels(self):
        for widget in _walk(self.shell.control_panel):
            if not isinstance(widget, tk.Label):
                continue
            try:
                text = str(widget.cget("text") or "")
            except tk.TclError:
                continue
            replacement = FILTER_LABELS.get(text)
            if replacement:
                try:
                    widget.configure(text=replacement, font=("Segoe UI", 8))
                except tk.TclError:
                    pass

    def _action_widgets(self):
        frames = [child for child in self.shell.control_panel.winfo_children() if isinstance(child, tk.Frame)]
        if len(frames) < 2:
            return None, []
        actions = frames[1]
        return actions, list(actions.winfo_children())

    def _group_action_buttons(self):
        actions, widgets = self._action_widgets()
        if actions is None:
            return
        by_text = {}
        hide_unknown = None
        for widget in widgets:
            try:
                text = str(widget.cget("text") or "")
            except (tk.TclError, AttributeError):
                continue
            if isinstance(widget, ttk.Button):
                by_text[text] = widget
            elif isinstance(widget, ttk.Checkbutton) and "Hide unknown" in text:
                hide_unknown = widget

        # Repack into clear task groups: route/view controls on the left,
        # log utilities in the middle-right, money/run actions on the far right.
        for widget in widgets:
            try:
                widget.pack_forget()
            except tk.TclError:
                pass

        def left(name, padx=(0, 0)):
            widget = by_text.get(name)
            if widget is not None:
                widget.pack(side="left", padx=padx)

        def right(name, padx=(0, 0)):
            widget = by_text.get(name)
            if widget is not None:
                widget.pack(side="right", padx=padx)

        left("Manage Routes")
        if hide_unknown is not None:
            hide_unknown.pack(side="left", padx=(10, 0))
        # Character Export installs one of these spellings depending on platform/font.
        export = by_text.get("Export...") or by_text.get("Export…")
        if export is not None:
            export.pack(side="left", padx=(10, 0))

        right("Reset Run")
        right("Calculator", padx=(0, 7))
        right("Choose Log Folder", padx=(0, 14))
        right("Replay Log File", padx=(0, 7))

    def _selected_character(self, name):
        if not name:
            return None
        return self.app.state_data.get("characters", {}).get(name)

    def _wrap_row_payout(self):
        original = self.gym_list._row_payout
        if getattr(original, "_current_run_semantics", False):
            return

        def row_payout_current(leader):
            char_name, record = self.app.merged_record(leader)
            character = self._selected_character(char_name)
            amount, actual = current_run_row_payout(leader, record, character)
            from .dashboard_gym_list import format_dashboard_money
            return format_dashboard_money(amount), actual

        row_payout_current._current_run_semantics = True
        self.gym_list._row_payout = row_payout_current
        try:
            self.gym_list.refresh_from_model()
        except tk.TclError:
            pass

    def _apply_region_colour(self, row):
        colour = region_colour(row.data.get("region"), self.app.theme_var.get())
        if colour:
            try:
                self.gym_list.canvas.itemconfigure(row.items["region"], fill=colour)
            except tk.TclError:
                pass

    def _wrap_region_style(self):
        original_style = self.gym_list._apply_row_style
        if not getattr(original_style, "_region_accent", False):
            def style_with_region(row):
                result = original_style(row)
                self._apply_region_colour(row)
                return result

            style_with_region._region_accent = True
            self.gym_list._apply_row_style = style_with_region

        # A newly-created UNKNOWN row is initially styled before its region text is
        # populated. If only the region value then changes, the core renderer does
        # not need a full semantic restyle. Apply just the region colour at that
        # moment so UNKNOWN rows never sit purple until a later repaint.
        original_sync = self.gym_list._sync_row_content
        if not getattr(original_sync, "_region_accent", False):
            def sync_with_region(row, changed):
                result = original_sync(row, changed)
                if "region" in changed:
                    self._apply_region_colour(row)
                return result

            sync_with_region._region_accent = True
            self.gym_list._sync_row_content = sync_with_region

        for row in self.gym_list.rows.values():
            self._apply_region_colour(row)

    def _fix_combobox_arrow_map(self):
        try:
            theme = self.app.theme()
            arrow = theme["field_fg"]
            style = ttk.Style(self.app)
            style.map(
                "Readable.TCombobox",
                arrowcolor=[
                    ("disabled", theme["muted"]),
                    ("pressed", arrow),
                    ("active", arrow),
                    ("focus", arrow),
                    ("readonly", arrow),
                ],
            )
        except tk.TclError:
            pass

    def _fix_scale_focus(self):
        combo = getattr(self.scaling, "scale_combo", None) if self.scaling is not None else None
        if combo is None or getattr(combo, "_scale_focus_restore", False):
            return

        def restore(_event=None):
            def finish():
                try:
                    if self.app.state() == "normal":
                        self.app.lift()
                        self.app.focus_force()
                        combo.focus_set()
                except tk.TclError:
                    pass
            try:
                self.app.after(90, finish)
            except tk.TclError:
                pass

        combo.bind("<<ComboboxSelected>>", restore, add="+")
        combo._scale_focus_restore = True

    def apply_scale(self):
        factor = factor_for(self.app)
        try:
            if self.live_below is not None:
                self.live_below.configure(font=("Segoe UI", scaled(8, factor, 7)))
            icon_size = scaled(KPI_ICON_BASE_SIZE, factor, 24)
            for canvas in self.kpi_icons.values():
                canvas.configure(width=icon_size, height=icon_size)
        except tk.TclError:
            pass
        self._draw_kpi_icons()
        self._fix_combobox_arrow_map()

    def apply_theme(self):
        try:
            theme = self.app.theme()
            if self.live_below is not None:
                self.live_below.configure(bg=theme["bg"], fg=theme["live"])
            self._draw_kpi_icons()
            self._fix_combobox_arrow_map()
            for row in self.gym_list.rows.values():
                self._apply_region_colour(row)
        except tk.TclError:
            pass


def install_dashboard_final_polish(app):
    existing = getattr(app, "_dashboard_final_polish", None)
    if existing is not None:
        return existing
    return DashboardFinalPolish(app)
