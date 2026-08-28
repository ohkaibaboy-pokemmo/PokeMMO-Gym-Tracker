"""Promote Compact View to a dedicated Full-view mode switch."""

import tkinter as tk
from tkinter import ttk


def _walk(root):
    stack = [root]
    while stack:
        widget = stack.pop()
        yield widget
        try:
            stack.extend(widget.winfo_children())
        except tk.TclError:
            pass


def install_dashboard_compact_button(app):
    """Move Compact View out of the action row and into the title bar.

    Compact is a view/mode change rather than a utility action, so it gets a
    dedicated top-right button. The live log indicator remains visible directly
    to its left.
    """
    shell = getattr(app, "_dashboard_shell", None)
    if shell is None:
        return None

    # Hide the original action-row copy without disturbing the other controls.
    for widget in _walk(shell.control_panel):
        if not isinstance(widget, ttk.Button):
            continue
        try:
            if widget.cget("text") == "Compact View":
                widget.pack_forget()
                break
        except tk.TclError:
            pass

    try:
        shell.live_label.pack_forget()
    except tk.TclError:
        pass

    shell.compact_view_button = ttk.Button(
        shell.title_row,
        text="Compact View",
        command=app.open_compact_view,
    )
    # Pack the mode button first so it owns the far-right edge; live status then
    # sits immediately to its left.
    shell.compact_view_button.pack(side="right")
    shell.live_label.pack(side="right", padx=(0, 12))

    app.compact_view_button = shell.compact_view_button
    return shell.compact_view_button
