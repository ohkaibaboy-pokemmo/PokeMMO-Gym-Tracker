"""Full-view resize safety policy for the v0.6 dashboard.

Live Windows validation showed that the old rich-row Tk widget tree tore visibly
while the root window was resized. The Gym Route is now a lightweight Canvas
renderer, so this module no longer throttles/debounces row work or monkey-patches
per-row refresh methods.

Full remains normally resizable. A practical scale-aware minimum keeps the
Detector and lower dashboard available, while a bounded Gym Route requested
height at that minimum leaves room for the lower dashboard. Enlarging the window
naturally reveals more of the already-rendered Canvas route. The route body also
reserves any fractional-row remainder below the Canvas so the last visible gym is
always a complete row rather than an awkward clipped sliver.
"""

import tkinter as tk

from .scaling import factor_for


FULL_BASE_WIDTH = 1280
FULL_BASE_HEIGHT = 800
SCREEN_WIDTH_MARGIN = 40
SCREEN_HEIGHT_MARGIN = 80
FULL_WINDOW_RESIZABLE = (True, True)
GYM_VIEWPORT_BASE_HEIGHT = 190
GYM_VIEWPORT_MIN_HEIGHT = 160


def gym_viewport_height(factor=1.0):
    try:
        factor = float(factor)
    except (TypeError, ValueError):
        factor = 1.0
    return max(GYM_VIEWPORT_MIN_HEIGHT, int(round(GYM_VIEWPORT_BASE_HEIGHT * factor)))


def full_route_bottom_gap(viewport_height, row_height):
    """Return bottom padding needed to expose only complete Full-route rows."""
    try:
        viewport_height = max(0, int(viewport_height))
        row_height = max(1, int(row_height))
    except (TypeError, ValueError):
        return 0
    if viewport_height < row_height:
        return 0
    return viewport_height % row_height


def dashboard_minimum_size(factor=1.0, screen_width=1920, screen_height=1080):
    """Return the safe Full-view minimum, capped to the current screen."""
    try:
        factor = max(1.0, float(factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0
    try:
        screen_width = max(1024, int(screen_width))
        screen_height = max(700, int(screen_height))
    except (TypeError, ValueError):
        screen_width, screen_height = 1920, 1080

    desired_width = int(round(FULL_BASE_WIDTH * factor))
    desired_height = int(round(FULL_BASE_HEIGHT * factor))
    maximum_width = max(1000, screen_width - SCREEN_WIDTH_MARGIN)
    maximum_height = max(640, screen_height - SCREEN_HEIGHT_MARGIN)
    return min(desired_width, maximum_width), min(desired_height, maximum_height)


class DashboardResizeSmoothing:
    """Compatibility-named controller that owns the Full resize safety policy."""

    def __init__(self, app):
        self.app = app
        self.gym_list = getattr(app, "_dashboard_gym_list", None)
        self._minimum_after_id = None
        self._route_row_gap = None

        self._install_route_row_snap()
        self.apply_window_policy()

        scale_var = getattr(app, "ui_scale_var", None)
        if scale_var is not None:
            scale_var.trace_add("write", self._scale_changed)
        app._dashboard_resize_smoothing = self

    def _install_route_row_snap(self):
        gym = self.gym_list or getattr(self.app, "_dashboard_gym_list", None)
        if gym is None:
            return
        try:
            gym.body.bind("<Configure>", self._route_body_configured, add="+")
            self.app.after_idle(self._snap_route_rows)
        except tk.TclError:
            pass

    def _route_body_configured(self, event):
        self._snap_route_rows(getattr(event, "height", None))

    def _snap_route_rows(self, body_height=None):
        gym = self.gym_list or getattr(self.app, "_dashboard_gym_list", None)
        if gym is None:
            return
        try:
            if body_height is None:
                body_height = gym.body.winfo_height()
            gap = full_route_bottom_gap(body_height, gym.row_height)
            if gap == self._route_row_gap:
                return
            self._route_row_gap = gap
            # Keep the Canvas and scrollbar ending on the same clean row edge.
            # The unused remainder stays as normal route-card background below.
            gym.canvas.pack_configure(pady=(0, gap))
            gym.scrollbar.pack_configure(pady=(0, gap))
        except tk.TclError:
            pass

    def _scale_changed(self, *_args):
        if self._minimum_after_id is not None:
            return
        try:
            self._minimum_after_id = self.app.after_idle(self._apply_after_scale)
        except tk.TclError:
            self._minimum_after_id = None

    def _apply_after_scale(self):
        self._minimum_after_id = None
        self._route_row_gap = None
        self.apply_window_policy()
        self._snap_route_rows()

    def _apply_viewport_budget(self, factor):
        gym = self.gym_list or getattr(self.app, "_dashboard_gym_list", None)
        if gym is None:
            return
        try:
            # Requested height only. Because the route body is expand=True, a
            # taller root gives the Canvas the extra space and reveals more rows.
            gym.canvas.configure(height=gym_viewport_height(factor))
        except tk.TclError:
            pass

    def apply_window_policy(self):
        try:
            self.app.update_idletasks()
            factor = factor_for(self.app)
            screen_width = self.app.winfo_screenwidth()
            screen_height = self.app.winfo_screenheight()
            min_width, min_height = dashboard_minimum_size(factor, screen_width, screen_height)
            self._apply_viewport_budget(factor)
            self.app.minsize(min_width, min_height)
            self.app.resizable(*FULL_WINDOW_RESIZABLE)

            # Preserve larger saved geometry, but never reopen below the safe
            # floor or beyond the usable screen bounds.
            if self.app.state() == "normal":
                current_width = max(1, self.app.winfo_width())
                current_height = max(1, self.app.winfo_height())
                max_width = max(min_width, screen_width - SCREEN_WIDTH_MARGIN)
                max_height = max(min_height, screen_height - SCREEN_HEIGHT_MARGIN)
                target_width = min(max_width, max(min_width, current_width))
                target_height = min(max_height, max(min_height, current_height))
                current_x = self.app.winfo_x()
                current_y = self.app.winfo_y()
                max_x = max(0, screen_width - target_width)
                max_y = max(0, screen_height - target_height)
                target_x = min(max(0, current_x), max_x)
                target_y = min(max(0, current_y), max_y)
                if (
                    target_width != current_width
                    or target_height != current_height
                    or target_x != current_x
                    or target_y != current_y
                ):
                    self.app.geometry(f"{target_width}x{target_height}+{target_x}+{target_y}")
            self.app.after_idle(self._snap_route_rows)
        except tk.TclError:
            pass

    def apply_minimum(self):
        self.apply_window_policy()


def install_dashboard_resize_smoothing(app):
    existing = getattr(app, "_dashboard_resize_smoothing", None)
    if existing is not None:
        return existing
    return DashboardResizeSmoothing(app)
