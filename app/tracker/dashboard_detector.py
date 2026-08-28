import re
import tkinter as tk
from tkinter import ttk


_TIMESTAMP_RE = re.compile(r"^(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<text>.*)$")
DETECTOR_VIEWPORT_BASE_HEIGHT = 124
DETECTOR_VIEWPORT_MIN_HEIGHT = 98
DETECTOR_ROW_BASE_HEIGHT = 28
DETECTOR_ROW_GAP_BASE = 3
DETECTOR_VIRTUAL_WIDTH = 10000


def detector_viewport_height(factor=1.0):
    """Return the compact Detector viewport height for an explicit UI scale."""
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    return max(DETECTOR_VIEWPORT_MIN_HEIGHT, int(round(DETECTOR_VIEWPORT_BASE_HEIGHT * factor)))


def detector_row_height(factor=1.0):
    """Return one lightweight Canvas event-row height."""
    try:
        factor = max(0.85, float(factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0
    return max(24, int(round(DETECTOR_ROW_BASE_HEIGHT * factor)))


def detector_row_gap(factor=1.0):
    try:
        factor = max(0.85, float(factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0
    return max(2, int(round(DETECTOR_ROW_GAP_BASE * factor)))


def detector_content_height(event_count, factor=1.0):
    """Return the vertical scroll extent for Canvas-rendered Detector events."""
    try:
        count = max(0, int(event_count))
    except (TypeError, ValueError):
        count = 0
    if count == 0:
        return detector_viewport_height(factor)
    row = detector_row_height(factor)
    gap = detector_row_gap(factor)
    return count * row + max(0, count - 1) * gap


def classify_event(text, level="info"):
    """Return a dashboard event kind and short badge label."""
    lowered = str(text or "").lower()
    level = str(level or "info").lower()

    if "payout:" in lowered or " got $" in lowered or "got ¥" in lowered:
        return "pay", "PAY"
    if "gym win:" in lowered:
        return "success", "GYM"
    if "challenged by" in lowered or "defeated leader" in lowered or "battle" in lowered:
        return "battle", "BATTLE"
    if level == "success":
        return "success", "WIN"
    if level == "warn":
        return "warn", "WARN"
    return "info", "INFO"


class DashboardDetector:
    """First-class recent-event dashboard panel for the v0.6 Full view.

    The history surface is deliberately a *single Canvas*. The previous version
    embedded a Frame inside the Canvas and created several Tk widgets per event.
    Live Windows resize testing showed the same widget-reflow tearing that the old
    Full Gym Route had exhibited. Canvas primitives keep Detector history passive
    and cheap while the native Clear button remains a normal accessible control.

    The whole Detector is packed from the bottom before the flexible Gym Route.
    This makes the route surrender vertical space first while resizing instead of
    transiently squeezing/clipping the Detector viewport.
    """

    MAX_HISTORY = 200

    def __init__(self, app, shell):
        self.app = app
        self.shell = shell
        self.legacy_frame = shell.detector_frame
        self.legacy_text = app.event_text
        self.events = []
        self.factor = 1.0
        self._content_height = detector_viewport_height(1.0)
        self._empty_resize_after_id = None

        self.container = tk.Frame(app, bd=0, highlightthickness=1)
        # Reserve the lower dashboard first. Header/controls stay native widgets,
        # while the already-scrollable Gym Route is the only large flexible area.
        before = getattr(shell, "control_panel", None)
        pack_kwargs = dict(side="bottom", fill="x", padx=20, pady=(0, 14))
        if before is not None:
            pack_kwargs["before"] = before
        self.container.pack(**pack_kwargs)
        try:
            self.legacy_frame.pack_forget()
        except tk.TclError:
            pass

        self.header = tk.Frame(self.container, bd=0)
        self.header.pack(fill="x", padx=12, pady=(9, 7))

        self.heading_group = tk.Frame(self.header, bd=0)
        self.heading_group.pack(side="left", fill="x", expand=True)

        self.title = tk.Label(
            self.heading_group,
            text="Detector",
            font=("Segoe UI Semibold", 11),
            anchor="w",
        )
        self.title.pack(side="left")

        self.subtitle = tk.Label(
            self.heading_group,
            text="Recent Tracker Activity",
            font=("Segoe UI Semibold", 8),
            anchor="w",
        )
        self.subtitle.pack(side="left", padx=(10, 0), pady=(2, 0))

        self.actions = tk.Frame(self.header, bd=0)
        self.actions.pack(side="right")

        self.clear_button = ttk.Button(self.actions, text="Clear", command=self.clear)
        self.clear_button.pack(side="right")

        self.live_chip = tk.Frame(self.actions, bd=0, highlightthickness=1)
        self.live_chip.pack(side="right", padx=(0, 8))
        self.live_dot = tk.Canvas(
            self.live_chip,
            width=10,
            height=10,
            bd=0,
            highlightthickness=0,
            takefocus=False,
        )
        self.live_dot.pack(side="left", padx=(7, 3), pady=5)
        self.live = tk.Label(
            self.live_chip,
            text="LIVE LOG",
            font=("Segoe UI Semibold", 7),
            anchor="e",
        )
        self.live.pack(side="left", padx=(0, 7), pady=4)

        self.body_shell = tk.Frame(self.container, bd=0, highlightthickness=1)
        self.body_shell.pack(fill="x", padx=10, pady=(0, 10))

        self.body_canvas = tk.Canvas(
            self.body_shell,
            bd=0,
            highlightthickness=0,
            takefocus=False,
            xscrollincrement=0,
        )
        # Kept as the temporary/native fallback; dashboard_scrollbar_integration
        # replaces it with the project-owned themed scrollbar after installation.
        self.body_scrollbar = ttk.Scrollbar(
            self.body_shell,
            orient="vertical",
            command=self.body_canvas.yview,
        )
        self.body_canvas.configure(yscrollcommand=self.body_scrollbar.set)
        self.body_scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self.body_canvas.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        self.body_canvas.bind("<Configure>", self._canvas_configured, add="+")
        self._bind_wheel(self.body_canvas)

        self._seed_from_legacy()
        self._wrap_add_event()
        self.apply_scale(1.0)
        self.apply_theme()
        self._scroll_to_latest()
        app.theme_var.trace_add("write", lambda *_args: app.after_idle(self.apply_theme))
        app._dashboard_detector = self

    def _seed_from_legacy(self):
        try:
            content = self.legacy_text.get("1.0", "end-1c")
        except tk.TclError:
            return
        for line in content.splitlines()[-self.MAX_HISTORY :]:
            match = _TIMESTAMP_RE.match(line.strip())
            if not match:
                continue
            text = match.group("text")
            kind, badge = classify_event(text)
            self.events.append(
                {
                    "time": match.group("time"),
                    "text": text,
                    "kind": kind,
                    "badge": badge,
                }
            )

    def _wrap_add_event(self):
        original = self.app.add_event
        if getattr(original, "_dashboard_detector_wrapped", False):
            return

        def add_with_dashboard(ts, text, level="info"):
            result = original(ts, text, level)
            self.add_event(ts, text, level)
            return result

        add_with_dashboard._dashboard_detector_wrapped = True
        self.app.add_event = add_with_dashboard

    def add_event(self, ts, text, level="info"):
        try:
            timestamp = ts.strftime("%H:%M:%S")
        except Exception:
            timestamp = str(ts or "")
        kind, badge = classify_event(text, level)
        self.events.append(
            {
                "time": timestamp,
                "text": str(text),
                "kind": kind,
                "badge": badge,
            }
        )
        self.events = self.events[-self.MAX_HISTORY :]
        self._render(scroll_latest=True)

    def clear(self):
        self.events.clear()
        try:
            self.legacy_text.configure(state="normal")
            self.legacy_text.delete("1.0", "end")
            self.legacy_text.configure(state="disabled")
        except tk.TclError:
            pass
        self._render()

    def _canvas_configured(self, event):
        # Event rows have fixed left-hand rails and oversized clipped backgrounds,
        # so normal resize does not require rebuilding them. Only the explicit
        # vertical scroll extent changes with viewport width. Empty-state content
        # is centred and therefore gets one coalesced repaint after width changes.
        try:
            self.body_canvas.configure(
                scrollregion=(0, 0, max(1, int(event.width)), max(1, self._content_height))
            )
        except tk.TclError:
            return
        if self.events:
            return
        if self._empty_resize_after_id is not None:
            return
        try:
            self._empty_resize_after_id = self.app.after_idle(self._render_empty_after_resize)
        except tk.TclError:
            self._empty_resize_after_id = None

    def _render_empty_after_resize(self):
        self._empty_resize_after_id = None
        if not self.events:
            self._render()

    def _bind_wheel(self, widget):
        try:
            widget.bind("<MouseWheel>", self._mousewheel, add="+")
        except tk.TclError:
            pass

    def _mousewheel(self, event):
        try:
            units = int(-1 * (event.delta / 120))
            if units:
                self.body_canvas.yview_scroll(units, "units")
        except tk.TclError:
            pass
        return "break"

    def _scroll_to_latest(self):
        try:
            self.app.after_idle(lambda: self.body_canvas.yview_moveto(1.0))
        except tk.TclError:
            pass

    def _badge_colour(self, kind, theme):
        return {
            "pay": theme["detector_pay"],
            "battle": theme["detector_battle"],
            "success": theme["detector_success"],
            "warn": theme["detector_warn"],
            "info": theme["detector_info"],
        }.get(kind, theme["detector_info"])

    def _badge_background(self, kind, theme):
        return {
            "pay": theme["waiting_bg"],
            "battle": theme["cooldown_bg"],
            "success": theme["ready_bg"],
            "warn": theme["waiting_bg"],
            "info": theme["panel"],
        }.get(kind, theme["panel"])

    def _render_empty(self, theme):
        canvas = self.body_canvas
        try:
            width = max(1, canvas.winfo_width())
            height = max(1, canvas.winfo_height())
        except tk.TclError:
            return
        cx = width / 2.0
        cy = height / 2.0
        marker = max(20, int(round(24 * self.factor)))
        gap = max(8, int(round(10 * self.factor)))
        text_x = cx - 85 * self.factor
        marker_x = text_x - gap - marker / 2.0
        canvas.create_oval(
            marker_x - marker / 2,
            cy - marker / 2,
            marker_x + marker / 2,
            cy + marker / 2,
            outline=theme["card_border"],
            width=2,
        )
        inner = marker * 0.12
        canvas.create_oval(
            marker_x - inner,
            cy - inner,
            marker_x + inner,
            cy + inner,
            fill=theme["live"],
            outline="",
        )
        canvas.create_text(
            text_x,
            cy - max(7, int(round(7 * self.factor))),
            text="Waiting for tracker events",
            anchor="w",
            font=("Segoe UI Semibold", max(8, int(round(9 * self.factor)))),
            fill=theme["text"],
        )
        canvas.create_text(
            text_x,
            cy + max(8, int(round(9 * self.factor))),
            text="Battles, gym results and payouts will appear here.",
            anchor="w",
            font=("Segoe UI", max(7, int(round(8 * self.factor)))),
            fill=theme["muted"],
        )

    def _render_event_row(self, event, y, theme):
        canvas = self.body_canvas
        row_h = detector_row_height(self.factor)
        accent = self._badge_colour(event["kind"], theme)
        badge_bg = self._badge_background(event["kind"], theme)
        s = lambda value, minimum=1: max(minimum, int(round(value * self.factor)))

        # Draw well past the viewport edge. The explicit scrollregion remains the
        # actual viewport width, so horizontal resizing only clips more/less of
        # the existing primitives instead of forcing every row to re-layout.
        canvas.create_rectangle(
            0,
            y,
            DETECTOR_VIRTUAL_WIDTH,
            y + row_h,
            fill=theme["card_bg"],
            outline=theme["card_border"],
            width=1,
        )
        accent_w = s(3, 2)
        canvas.create_rectangle(
            0,
            y + 1,
            accent_w,
            y + row_h - 1,
            fill=accent,
            outline="",
        )

        badge_x1 = accent_w + s(8, 6)
        badge_w = s(52, 44)
        badge_y1 = y + s(5, 4)
        badge_y2 = y + row_h - s(5, 4)
        canvas.create_rectangle(
            badge_x1,
            badge_y1,
            badge_x1 + badge_w,
            badge_y2,
            fill=badge_bg,
            outline="",
        )
        canvas.create_text(
            badge_x1 + badge_w / 2,
            y + row_h / 2,
            text=event["badge"],
            anchor="center",
            font=("Segoe UI Semibold", max(7, int(round(7 * self.factor)))),
            fill=accent,
        )

        time_x = badge_x1 + badge_w + s(10, 8)
        canvas.create_text(
            time_x,
            y + row_h / 2,
            text=event["time"],
            anchor="w",
            font=("Consolas", max(7, int(round(8 * self.factor)))),
            fill=theme["muted"],
        )
        message_x = time_x + s(78, 66)
        canvas.create_text(
            message_x,
            y + row_h / 2,
            text=event["text"],
            anchor="w",
            font=("Segoe UI", max(7, int(round(8 * self.factor)))),
            fill=theme["text"],
        )

    def _render(self, scroll_latest=False):
        theme = self.app.theme()
        try:
            old_view = self.body_canvas.yview()
            width = max(1, self.body_canvas.winfo_width())
            self.body_canvas.delete("all")
        except tk.TclError:
            return

        if not self.events:
            self._content_height = detector_viewport_height(self.factor)
            self._render_empty(theme)
        else:
            row_h = detector_row_height(self.factor)
            gap = detector_row_gap(self.factor)
            y = 0
            for event in self.events:
                self._render_event_row(event, y, theme)
                y += row_h + gap
            self._content_height = detector_content_height(len(self.events), self.factor)

        try:
            self.body_canvas.configure(
                scrollregion=(0, 0, width, max(1, self._content_height)),
                yscrollincrement=max(1, detector_row_height(self.factor)),
            )
        except tk.TclError:
            pass

        if scroll_latest:
            self._scroll_to_latest()
        else:
            try:
                self.app.after_idle(lambda value=old_view[0]: self.body_canvas.yview_moveto(value))
            except tk.TclError:
                pass

    def _draw_live_dot(self):
        theme = self.app.theme()
        canvas = self.live_dot
        try:
            canvas.delete("all")
            canvas.configure(bg=theme["card_bg"])
            width = int(float(canvas.cget("width")))
            height = int(float(canvas.cget("height")))
        except (tk.TclError, ValueError):
            return
        inset = max(1, int(round(min(width, height) * 0.2)))
        canvas.create_oval(
            inset,
            inset,
            width - inset,
            height - inset,
            fill=theme["live"],
            outline="",
        )

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.container.configure(
                bg=theme["card_bg"],
                highlightbackground=theme["card_border"],
            )
            for frame in (self.header, self.heading_group, self.actions):
                frame.configure(bg=theme["card_bg"])
            self.title.configure(bg=theme["card_bg"], fg=theme["text"])
            self.subtitle.configure(bg=theme["card_bg"], fg=theme["muted"])
            self.live_chip.configure(
                bg=theme["card_bg"],
                highlightbackground=theme["card_border"],
            )
            self.live.configure(bg=theme["card_bg"], fg=theme["live"])
            self.body_shell.configure(
                bg=theme["panel_dark"],
                highlightbackground=theme["card_border"],
            )
            self.body_canvas.configure(bg=theme["panel_dark"])
        except tk.TclError:
            return
        self._draw_live_dot()
        self._render()

    def apply_scale(self, factor=1.0):
        try:
            self.factor = float(factor)
        except (TypeError, ValueError):
            self.factor = 1.0
        s = lambda value, minimum=1: max(minimum, int(round(value * self.factor)))
        try:
            self.container.pack_configure(
                padx=s(20),
                pady=(0, s(14)),
            )
            self.header.pack_configure(
                padx=s(12),
                pady=(s(9), s(7)),
            )
            self.body_shell.pack_configure(
                padx=s(10),
                pady=(0, s(10)),
            )
            self.body_canvas.configure(height=detector_viewport_height(self.factor))
            self.title.configure(font=("Segoe UI Semibold", s(11, 9)))
            self.subtitle.configure(font=("Segoe UI Semibold", s(8, 7)))
            self.live.configure(font=("Segoe UI Semibold", s(7, 7)))
            dot = s(10, 8)
            self.live_dot.configure(width=dot, height=dot)
        except tk.TclError:
            pass
        self._draw_live_dot()
        self._render()


def install_dashboard_detector(app):
    shell = getattr(app, "_dashboard_shell", None)
    if shell is None:
        return None
    app._dashboard_detector = DashboardDetector(app, shell)
    return app._dashboard_detector
