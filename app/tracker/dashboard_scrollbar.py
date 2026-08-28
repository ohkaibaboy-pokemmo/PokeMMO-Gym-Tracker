import tkinter as tk


def scrollbar_thumb_geometry(height, first, last, factor=1.0, padding=2):
    """Return (top, bottom) for the dashboard's minimal vertical scrollbar thumb."""
    try:
        height = max(1, int(height))
        first = max(0.0, min(1.0, float(first)))
        last = max(first, min(1.0, float(last)))
        factor = max(0.85, float(factor or 1.0))
    except (TypeError, ValueError):
        return int(padding), max(int(padding) + 1, int(height) - int(padding))

    padding = max(1, int(round(padding * factor)))
    track_top = padding
    track_bottom = max(track_top + 1, height - padding)
    track_length = max(1, track_bottom - track_top)
    span = max(0.0, min(1.0, last - first))

    if span >= 0.999:
        return track_top, track_bottom

    minimum = max(14, int(round(22 * factor)))
    thumb_length = min(track_length, max(minimum, int(round(track_length * span))))
    travel = max(0, track_length - thumb_length)
    maximum_first = max(1e-9, 1.0 - span)
    position = (first / maximum_first) * travel
    top = track_top + int(round(position))
    return top, min(track_bottom, top + thumb_length)


class DashboardScrollbar(tk.Canvas):
    """Small theme-aware scrollbar used by the v0.6 dashboard surfaces.

    Native Windows scrollbars remain very bright under some Tk themes, which
    clashes with the dashboard. This intentionally simple Canvas control keeps
    scrolling local/passive while matching Dark, Light and PokeMMO surfaces.
    """

    def __init__(self, parent, target, app, logical_width=10):
        self.target = target
        self.app = app
        self.logical_width = logical_width
        self.factor = 1.0
        self.first = 0.0
        self.last = 1.0
        self._drag_offset = None
        self._hovered = False

        super().__init__(
            parent,
            width=logical_width,
            # Canvas defaults to a surprisingly tall requested height on Windows.
            # The scrollbar is always packed fill='y', so request only 1px here and
            # let the parent viewport decide the real height. Without this, the
            # Detector body can grow from its intended ~124px to ~275px.
            height=1,
            bd=0,
            highlightthickness=0,
            takefocus=False,
            cursor="hand2",
        )
        target.configure(yscrollcommand=self.set)
        self.bind("<Configure>", lambda _event: self._draw(), add="+")
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")
        self.bind("<Button-1>", self._press, add="+")
        self.bind("<B1-Motion>", self._drag, add="+")
        self.bind("<ButtonRelease-1>", self._release, add="+")

    def set(self, first, last):
        try:
            self.first = float(first)
            self.last = float(last)
        except (TypeError, ValueError):
            self.first, self.last = 0.0, 1.0
        self._draw()

    def _theme(self):
        try:
            return self.app.theme()
        except Exception:
            return {
                "panel_dark": "#0d1318",
                "card_bg": "#141c22",
                "control_border": "#34434e",
                "muted": "#9ba7ae",
            }

    def apply_theme(self):
        self._draw()

    def apply_scale(self, factor=1.0):
        try:
            self.factor = max(0.85, float(factor or 1.0))
        except (TypeError, ValueError):
            self.factor = 1.0
        try:
            self.configure(width=max(8, int(round(self.logical_width * self.factor))))
        except tk.TclError:
            pass
        self._draw()

    def _geometry(self):
        try:
            height = max(1, self.winfo_height())
        except tk.TclError:
            height = 1
        return scrollbar_thumb_geometry(height, self.first, self.last, self.factor)

    def _draw(self):
        theme = self._theme()
        trough = theme.get("panel_dark", theme.get("card_bg", "#111111"))
        thumb = theme.get("muted") if self._hovered else theme.get("control_border", theme.get("muted"))
        try:
            self.delete("all")
            self.configure(bg=trough)
            width = max(1, self.winfo_width())
            height = max(1, self.winfo_height())
            top, bottom = scrollbar_thumb_geometry(height, self.first, self.last, self.factor)
            if self.last - self.first >= 0.999:
                return
            inset = max(1, int(round(2 * self.factor)))
            self.create_rectangle(
                inset,
                top,
                max(inset + 1, width - inset),
                bottom,
                fill=thumb,
                outline="",
            )
        except tk.TclError:
            pass

    def _enter(self, _event=None):
        self._hovered = True
        self._draw()

    def _leave(self, _event=None):
        self._hovered = False
        # Do not cancel an active thumb drag just because the pointer strays a few
        # pixels outside this deliberately narrow custom scrollbar. Tk keeps the
        # button grab until release, so retaining the offset gives normal native-
        # scrollbar behaviour: drag continues until ButtonRelease-1.
        self._draw()

    def _press(self, event):
        top, bottom = self._geometry()
        if top <= event.y <= bottom:
            self._drag_offset = event.y - top
            return "break"
        try:
            self.target.yview_scroll(-1 if event.y < top else 1, "pages")
        except tk.TclError:
            pass
        return "break"

    def _drag(self, event):
        if self._drag_offset is None:
            return "break"
        try:
            height = max(1, self.winfo_height())
        except tk.TclError:
            return "break"

        top, bottom = scrollbar_thumb_geometry(height, self.first, self.last, self.factor)
        thumb_length = max(1, bottom - top)
        padding = max(1, int(round(2 * self.factor)))
        track_length = max(1, height - (2 * padding))
        travel = max(1, track_length - thumb_length)
        span = max(0.0, min(1.0, self.last - self.first))
        maximum_first = max(0.0, 1.0 - span)
        raw = event.y - self._drag_offset - padding
        position = max(0.0, min(float(travel), float(raw)))
        first = (position / travel) * maximum_first
        try:
            self.target.yview_moveto(first)
        except tk.TclError:
            pass
        return "break"

    def _release(self, _event=None):
        self._drag_offset = None
        return "break"
