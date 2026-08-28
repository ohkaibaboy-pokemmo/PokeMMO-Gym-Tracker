"""Final Full-dashboard action-row grouping.

The release-polish row previously read visually as Button / Checkbutton / Button
on the left because Character Export sat between Manage Routes and Hide unknown.
Keep route/view controls together on the left and move Export beside the other
file/log utilities on the right.
"""

import tkinter as tk
from tkinter import ttk


RIGHT_ACTION_VISUAL_ORDER = (
    "Replay Log File",
    "Choose Log Folder",
    "Export",
    "Calculator",
    "Reset Run",
)


def right_action_visual_order():
    """Return the intended left-to-right order for right-side action buttons."""
    return RIGHT_ACTION_VISUAL_ORDER


class DashboardActionGrouping:
    def __init__(self, app):
        self.app = app
        self.polish = getattr(app, "_dashboard_final_polish", None)
        if self.polish is None:
            raise RuntimeError("Action grouping requires dashboard final polish")
        self.apply()
        app._dashboard_action_grouping = self

    def _action_widgets(self):
        actions, widgets = self.polish._action_widgets()
        return actions, widgets

    @staticmethod
    def _button_key(text):
        if text in ("Export...", "Export…"):
            return "Export"
        return text

    def apply(self):
        actions, widgets = self._action_widgets()
        if actions is None:
            return

        buttons = {}
        hide_unknown = None
        for widget in widgets:
            try:
                text = str(widget.cget("text") or "")
            except (tk.TclError, AttributeError):
                continue
            if isinstance(widget, ttk.Button):
                buttons[self._button_key(text)] = widget
            elif isinstance(widget, ttk.Checkbutton) and "Hide unknown" in text:
                hide_unknown = widget

        for widget in widgets:
            try:
                widget.pack_forget()
            except tk.TclError:
                pass

        # Route/view controls remain a compact left-side pair. Moving Export away
        # removes the awkward Button / Checkbutton / Button rhythm.
        manage_routes = buttons.get("Manage Routes")
        if manage_routes is not None:
            manage_routes.pack(side="left")
        if hide_unknown is not None:
            hide_unknown.pack(side="left", padx=(10, 0))

        # Tk packs side=right items from the outer edge inward, so iterate the
        # desired visual order in reverse to produce the declared left-to-right row.
        right_widgets = [buttons.get(name) for name in RIGHT_ACTION_VISUAL_ORDER]
        for index, widget in enumerate(reversed(right_widgets)):
            if widget is None:
                continue
            # Slightly larger separation before Calculator/Reset Run keeps the
            # file/log cluster visually distinct from money/run actions.
            name = self._button_key(str(widget.cget("text") or ""))
            if name == "Reset Run":
                padx = (0, 0)
            elif name == "Calculator":
                padx = (0, 7)
            elif name == "Export":
                padx = (0, 14)
            else:
                padx = (0, 7)
            widget.pack(side="right", padx=padx)


def install_dashboard_action_grouping(app):
    existing = getattr(app, "_dashboard_action_grouping", None)
    if existing is not None:
        return existing
    return DashboardActionGrouping(app)
