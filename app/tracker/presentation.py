import math
import re
import tkinter as tk
from tkinter import ttk

from .constants import GYMS
from .state import state_dir


_PROGRESS_RE = re.compile(
    r"Ready\s+(?P<ready>\d+)/(?P<total>\d+)\s+•\s+"
    r"Waiting\s+(?P<waiting>\d+)\s+•\s+"
    r"Cooldown\s+(?P<cooldown>\d+)\s+•\s+"
    r"Unknown\s+(?P<unknown>\d+)"
)

# Logical column order must remain aligned with tracker.ui's inserted values.
# displaycolumns below controls the user-facing order independently.
_TABLE_COLUMNS = {
    "position": ("#", 42, "center"),
    "region": ("Region", 88, "center"),
    "gym": ("Gym", 140, "center"),
    "leader": ("Leader", 120, "center"),
    "cooldown": ("Cooldown", 118, "center"),
    "rule": ("5-rule", 72, "center"),
    "last": ("Last Defeated", 150, "center"),
    "status": ("Status", 190, "center"),
}

# Tk's special #0 tree column owns the row image and is always physically first.
# The remaining visible columns follow the scan order requested for rerun use.
_DISPLAY_COLUMNS = (
    "position",
    "leader",
    "gym",
    "region",
    "rule",
    "cooldown",
    "last",
    "status",
)

# Share spare maximized-window width across descriptive columns instead of
# dumping it into one oversized field. Numeric/time columns stay compact.
_STRETCH_COLUMNS = {"region", "gym", "leader", "last", "status"}

_BADGE_SIZE = 30
_MAX_CUSTOM_SPRITE = 32


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


class FullViewPresentation:
    """Presentation-only decoration for the full tracker window.

    The underlying log parser, cooldown logic, trainer logic, routes and state are
    intentionally untouched. Vanilla behaviour remains owned by tracker.ui.
    """

    def __init__(self, app):
        self.app = app
        self.cards = {}
        self._leader_images = {}
        self._theme_after_id = None
        self.title_label = None

        self._retitle()
        self._install_status_cards()
        self._tighten_table()
        self._build_leader_images()
        self._wrap_row_values()
        self._wrap_refresh_table()
        self._decorate_rows()

        app.progress_var.trace_add("write", self._progress_changed)
        app.theme_var.trace_add("write", self._theme_changed)
        self._update_cards()
        self.apply_theme()
        self.apply_scale(_factor(app))

        # Rebuild once through the wrapped presentation functions so expired
        # timers immediately use the rerun-friendly post-cooldown display.
        self.app.refresh_table()

    def _walk(self, widget):
        yield widget
        for child in widget.winfo_children():
            yield from self._walk(child)

    def _retitle(self):
        for widget in self._walk(self.app):
            if not isinstance(widget, tk.Label):
                continue
            try:
                if widget.cget("text") != "Gym Cooldown Info":
                    continue
                widget.configure(text="Gym Rerun Tracker")
                self.title_label = widget
                self.subtitle = tk.Label(
                    widget.master,
                    text="Cooldowns  •  5-rule  •  routes",
                    font=("Segoe UI", 9),
                )
                self.subtitle.pack(side="left", padx=(12, 0), pady=(3, 0))
                return
            except tk.TclError:
                continue

    def _install_status_cards(self):
        # Compact view still consumes the original progress string. Hide only
        # the Full-view label and replace it with quick-scan status cards.
        for child in self.app.view_controls.winfo_children():
            if not isinstance(child, tk.Label):
                continue
            try:
                if str(child.cget("textvariable") or "") == str(self.app.progress_var):
                    child.pack_forget()
            except tk.TclError:
                pass

        self.status_strip = tk.Frame(self.app)
        self.status_strip.pack(
            fill="x",
            padx=10,
            pady=(0, 7),
            before=self.app.view_controls,
        )

        specs = (
            ("ready", "Ready"),
            ("waiting", "Waiting"),
            ("cooldown", "Cooldown"),
            ("unknown", "Unknown"),
        )
        for index, (key, label) in enumerate(specs):
            card = tk.Frame(self.status_strip, bd=0, highlightthickness=1)
            card.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0 if index == 0 else 4, 0),
            )
            count_var = tk.StringVar(value="0")
            count = tk.Label(
                card,
                textvariable=count_var,
                font=("Segoe UI Semibold", 15),
                anchor="w",
            )
            count.pack(side="left", padx=(10, 6), pady=5)
            caption = tk.Label(
                card,
                text=label,
                font=("Segoe UI", 9),
                anchor="w",
            )
            caption.pack(side="left", pady=(8, 5))
            self.cards[key] = {
                "index": index,
                "frame": card,
                "count_var": count_var,
                "count": count,
                "caption": caption,
            }

    def _tighten_table(self):
        tree = self.app.tree

        columns = tuple(_TABLE_COLUMNS.keys())
        tree.configure(
            columns=columns,
            displaycolumns=_DISPLAY_COLUMNS,
            show=("tree", "headings"),
        )

        tree.heading("#0", text="")
        tree.column(
            "#0",
            width=42,
            minwidth=42,
            stretch=False,
            anchor="center",
        )

        for column, (label, width, anchor) in _TABLE_COLUMNS.items():
            tree.heading(column, text=label, anchor="center")
            tree.column(
                column,
                width=width,
                minwidth=width,
                stretch=(column in _STRETCH_COLUMNS),
                anchor=anchor,
            )

        self._apply_tree_style()

    def _apply_tree_style(self):
        theme = self.app.theme()
        factor = _factor(self.app)
        style = ttk.Style(self.app)
        style.configure("Treeview", rowheight=_s(34, factor, 28))

        # The clam theme otherwise supplies a very light active heading state on
        # Windows. Keep header text/background readable and stable on hover.
        style.configure(
            "Treeview.Heading",
            background=theme["heading"],
            foreground=theme["text"],
            relief="flat",
            font=("Segoe UI Semibold", _s(10, factor, 8)),
        )
        style.map(
            "Treeview.Heading",
            background=[("pressed", theme["heading"]), ("active", theme["heading"])],
            foreground=[("pressed", theme["text"]), ("active", theme["text"])],
        )

    def apply_scale(self, factor=None):
        """Scale the dashboard chrome that sits above the Treeview.

        ttk table dimensions are handled by the central scaling controller; this
        method owns the title/subtitle and status-card fonts/padding so the full
        view does not look like two different UI scales stitched together.
        """
        factor = float(factor or _factor(self.app))
        try:
            if self.title_label is not None:
                self.title_label.configure(font=("Segoe UI Semibold", _s(15, factor, 11)))
            if hasattr(self, "subtitle"):
                self.subtitle.configure(font=("Segoe UI", _s(9, factor, 7)))
                self.subtitle.pack_configure(
                    padx=(_s(12, factor), 0),
                    pady=(_s(3, factor), 0),
                )

            self.status_strip.pack_configure(
                padx=_s(10, factor),
                pady=(0, _s(7, factor)),
            )
            for widgets in self.cards.values():
                index = widgets["index"]
                widgets["frame"].pack_configure(
                    padx=(0 if index == 0 else _s(4, factor), 0)
                )
                widgets["count"].configure(
                    font=("Segoe UI Semibold", _s(15, factor, 10))
                )
                widgets["count"].pack_configure(
                    padx=(_s(10, factor), _s(6, factor)),
                    pady=_s(5, factor),
                )
                widgets["caption"].configure(
                    font=("Segoe UI", _s(9, factor, 7))
                )
                widgets["caption"].pack_configure(
                    pady=(_s(8, factor), _s(5, factor))
                )
        except tk.TclError:
            pass
        self._apply_tree_style()

    def _wrap_row_values(self):
        """Prefer the most actionable post-cooldown text.

        While the 18-hour timer is running, Cooldown remains HH:MM:SS. Once the
        timer has expired, a gym that still needs rematch battles keeps the useful
        "Need N battles" message. A fully ready gym shows 00:00:00 so the Status
        column remains the single place that says READY.
        """
        original_row_values = self.app.row_values

        def row_values_with_actionable_expired_timer(*args, **kwargs):
            values = list(original_row_values(*args, **kwargs))
            if len(values) >= 7:
                status = str(values[6])
                if status.startswith("READY"):
                    values[3] = "00:00:00"
                # WAITING deliberately keeps tracker.ui's "Need N battle(s)" text.
            return tuple(values)

        self.app.row_values = row_values_with_actionable_expired_timer

    def _wrap_refresh_table(self):
        """Attach leader images before Tk gets a chance to repaint the table.

        tracker.ui rebuilds its rows every second so cooldown text stays live.
        Decorating the rebuilt rows in the same event turn prevents image flicker.
        """
        original_refresh = self.app.refresh_table

        def refresh_with_images(*args, **kwargs):
            result = original_refresh(*args, **kwargs)
            self._decorate_rows()
            return result

        self.app.refresh_table = refresh_with_images

    def _progress_changed(self, *_args):
        self._update_cards()

    def _theme_changed(self, *_args):
        if self._theme_after_id is not None:
            try:
                self.app.after_cancel(self._theme_after_id)
            except tk.TclError:
                pass
        self._theme_after_id = self.app.after_idle(self._after_theme_change)

    def _after_theme_change(self):
        self._theme_after_id = None
        self._apply_tree_style()
        self._build_leader_images()
        self._decorate_rows()
        self.apply_theme()
        self.apply_scale(_factor(self.app))

    def _update_cards(self):
        match = _PROGRESS_RE.search(self.app.progress_var.get())
        if not match:
            return
        for key in ("ready", "waiting", "cooldown", "unknown"):
            self.cards[key]["count_var"].set(match.group(key))

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.status_strip.configure(bg=theme["bg"])
        except tk.TclError:
            return

        if hasattr(self, "subtitle"):
            self.subtitle.configure(bg=theme["bg"], fg=theme["muted"])

        colours = {
            "ready": theme["ready"],
            "waiting": theme["waiting"],
            "cooldown": theme["accent"],
            "unknown": theme["unknown"],
        }
        for key, widgets in self.cards.items():
            widgets["frame"].configure(
                bg=theme["panel"],
                highlightbackground=theme["border"],
            )
            widgets["count"].configure(
                bg=theme["panel"],
                fg=colours[key],
            )
            widgets["caption"].configure(
                bg=theme["panel"],
                fg=theme["muted"],
            )

        self._apply_tree_style()

    @staticmethod
    def _leader_seed(leader):
        return sum((index + 1) * ord(char) for index, char in enumerate(leader))

    @staticmethod
    def _sprite_filename(leader):
        slug = re.sub(r"[^a-z0-9]+", "_", leader.lower()).strip("_")
        return f"{slug}.png"

    def _build_leader_images(self):
        theme = self.app.theme()
        custom_dir = state_dir() / "leader_sprites"
        custom_dir.mkdir(parents=True, exist_ok=True)

        accents = [
            theme["accent"],
            theme["ready"],
            theme["waiting"],
            theme["selected"],
            theme["muted"],
        ]

        images = {}
        for _region, _gym, leader in GYMS:
            custom_path = custom_dir / self._sprite_filename(leader)
            custom = self._load_custom_sprite(custom_path)
            if custom is not None:
                images[leader] = custom
                continue

            seed = self._leader_seed(leader)
            images[leader] = self._make_pixel_badge(
                accent=accents[seed % len(accents)],
                background=theme["panel"],
                inner=theme["heading"],
                face=theme["text"],
                detail=theme["panel_dark"],
                shirt=theme["selected"],
                variant=seed,
            )

        # Keep strong references for as long as the presentation exists. Tk drops
        # PhotoImages immediately if Python garbage-collects the last reference.
        self._leader_images = images

    def _load_custom_sprite(self, path):
        if not path.exists():
            return None
        try:
            image = tk.PhotoImage(master=self.app, file=str(path))
            factor = max(
                1,
                math.ceil(image.width() / _MAX_CUSTOM_SPRITE),
                math.ceil(image.height() / _MAX_CUSTOM_SPRITE),
            )
            if factor > 1:
                image = image.subsample(factor, factor)
            return image
        except (tk.TclError, OSError):
            return None

    def _make_pixel_badge(
        self,
        *,
        accent,
        background,
        inner,
        face,
        detail,
        shirt,
        variant,
    ):
        image = tk.PhotoImage(
            master=self.app,
            width=_BADGE_SIZE,
            height=_BADGE_SIZE,
        )
        image.put(background, to=(0, 0, _BADGE_SIZE, _BADGE_SIZE))
        image.put(inner, to=(2, 2, 28, 28))

        # Original generic pixel marker used only as a fallback when the user has
        # not supplied a local leader sprite. It does not reproduce game artwork.
        hair_left = 6 + (variant % 3)
        hair_right = 24 - ((variant // 3) % 3)
        image.put(accent, to=(hair_left, 5, hair_right, 11))
        image.put(accent, to=(6, 9, 9, 17))
        image.put(accent, to=(21, 9, 24, 17))
        image.put(face, to=(9, 10, 21, 19))
        eye_y = 13 + (variant % 2)
        image.put(detail, to=(11, eye_y, 13, eye_y + 2))
        image.put(detail, to=(17, eye_y, 19, eye_y + 2))
        image.put(shirt, to=(7, 20, 23, 26))
        if variant % 2:
            image.put(accent, to=(13, 20, 17, 26))
        else:
            image.put(accent, to=(9, 20, 12, 26))
            image.put(accent, to=(18, 20, 21, 26))
        return image

    def _decorate_rows(self):
        tree = self.app.tree
        for item in tree.get_children():
            image = self._leader_images.get(item)
            try:
                tree.item(item, image=image if image is not None else "")
            except tk.TclError:
                pass


def install_presentation(app):
    """Install the full-view presentation layer and keep it alive."""
    app._presentation = FullViewPresentation(app)
    return app._presentation
