"""Keep Compact's route viewport aligned to complete Treeview rows.

Compact is intentionally small, but a default window height that lands halfway
through the final Treeview row looks unfinished.  Windows does not always expose
final Treeview geometry on the first idle callback, so the snap is based on the
actual last visible row after layout has settled and retries briefly if geometry
is not ready yet.
"""

import tkinter as tk


TREE_BORDER_INSET = 2
MAX_SNAP_ATTEMPTS = 8
SNAP_RETRY_MS = 60
INITIAL_SNAP_DELAY_MS = 80


def compact_route_snap_delta(tree_height, first_row_y, row_height, border_inset=TREE_BORDER_INSET):
    """Legacy arithmetic helper: pixels needed for a whole-row viewport."""
    try:
        tree_height = int(tree_height)
        first_row_y = int(first_row_y)
        row_height = int(row_height)
        border_inset = max(0, int(border_inset))
    except (TypeError, ValueError):
        return 0
    if tree_height <= 0 or first_row_y < 0 or row_height <= 0:
        return 0

    usable = tree_height - border_inset - first_row_y
    if usable <= 0:
        return 0
    remainder = usable % row_height
    return 0 if remainder == 0 else row_height - remainder


def compact_partial_row_growth(
    tree_height,
    row_y,
    row_height,
    border_inset=TREE_BORDER_INSET,
):
    """Return pixels needed to finish one actually visible partial final row."""
    try:
        tree_height = int(tree_height)
        row_y = int(row_y)
        row_height = int(row_height)
        border_inset = max(0, int(border_inset))
    except (TypeError, ValueError):
        return 0
    if tree_height <= 0 or row_y < 0 or row_height <= 0:
        return 0

    visible_bottom = max(0, tree_height - border_inset)
    if row_y >= visible_bottom:
        return 0
    row_bottom = row_y + row_height
    return max(0, row_bottom - visible_bottom)


def _retry_snap(window):
    try:
        window.after(SNAP_RETRY_MS, lambda: _snap_route_height(window))
    except tk.TclError:
        pass


def _snap_route_height(window):
    attempts = int(getattr(window, "_compact_route_snap_attempts", 0) or 0)
    if attempts >= MAX_SNAP_ATTEMPTS:
        return
    window._compact_route_snap_attempts = attempts + 1

    try:
        # Force pending pack/grid work to settle before reading Treeview bboxes.
        window.update_idletasks()
        tree = window.tree
        tree.update_idletasks()

        tree_height = int(tree.winfo_height())
        if tree_height <= 1:
            _retry_snap(window)
            return

        items = tuple(tree.get_children())
        if not items:
            return

        partial_delta = 0
        saw_visible_row = False
        for item in items:
            bbox = tree.bbox(item)
            if not bbox or len(bbox) != 4:
                continue
            _x, row_y, _width, row_height = bbox
            if row_height <= 0:
                continue
            if row_y >= tree_height - TREE_BORDER_INSET:
                continue
            saw_visible_row = True
            partial_delta = max(
                partial_delta,
                compact_partial_row_growth(tree_height, row_y, row_height),
            )

        if not saw_visible_row:
            _retry_snap(window)
            return
        if partial_delta <= 0:
            return

        width = int(window.winfo_width())
        height = int(window.winfo_height())
        x = int(window.winfo_x())
        y = int(window.winfo_y())
        target_height = height + partial_delta

        # Complete the row even near the bottom of the desktop. If necessary,
        # nudge the frameless Compact window upward by only the overflow amount.
        screen_height = int(window.winfo_screenheight())
        target_y = y
        if target_y >= 0 and target_y + target_height > screen_height:
            target_y = max(0, screen_height - target_height)

        window.geometry(f"{width}x{target_height}+{x}+{target_y}")
        _retry_snap(window)
    except (tk.TclError, TypeError, ValueError):
        _retry_snap(window)


def install_compact_row_snap(compact_window_cls):
    """Snap Compact's initial route viewport to complete rows once per opening."""
    original_init = compact_window_cls.__init__
    if getattr(original_init, "_compact_row_snap", False):
        return compact_window_cls

    def init_with_row_snap(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._compact_route_snap_attempts = 0
        try:
            # after_idle proved too early on Windows build 19: the Treeview could
            # still report pre-final geometry and the visible half-row survived.
            self.after(INITIAL_SNAP_DELAY_MS, lambda: _snap_route_height(self))
        except tk.TclError:
            pass

    init_with_row_snap._compact_row_snap = True
    compact_window_cls.__init__ = init_with_row_snap
    compact_window_cls._snap_route_height = _snap_route_height
    return compact_window_cls
