"""Keep scaling from resurrecting intentionally hidden Full-dashboard widgets.

The explicit scaling controller captures baseline pack/grid padding early in app
startup. Later presentation layers deliberately retire some legacy widgets with
``pack_forget`` / ``grid_forget``. Calling ``pack_configure`` or ``grid_configure``
on one of those unmanaged widgets maps it again, which can duplicate the live-log
status and bring back the retired earnings card.

This guard preserves the existing scaling controller and only suppresses padding
re-application while a captured widget is not currently managed by the same
geometry manager. If a widget is legitimately managed again later, it will once
again participate in normal scaling.
"""

import tkinter as tk


def layout_manager_matches(widget, expected_manager):
    """Return True only when ``widget`` is actively using the captured manager."""
    try:
        return bool(widget.winfo_exists()) and widget.winfo_manager() == expected_manager
    except (tk.TclError, AttributeError):
        return False


class LayoutVisibilityGuard:
    def __init__(self, app):
        self.app = app
        self.scaling = getattr(app, "_scaling_controller", None)
        if self.scaling is None:
            raise RuntimeError("Layout visibility guard requires the scaling controller")
        self._install()
        app._layout_visibility_guard = self

    def _install(self):
        original = self.scaling._apply_full_layout_padding
        if getattr(original, "_layout_visibility_guarded", False):
            return

        def guarded_apply_full_layout_padding():
            base_layout = self.scaling._base_layout
            held = {}
            for key, entry in list(base_layout.items()):
                try:
                    widget, manager, _config = entry
                except (TypeError, ValueError):
                    continue
                if not layout_manager_matches(widget, manager):
                    held[key] = base_layout.pop(key)
            try:
                return original()
            finally:
                # Restore the captured baseline metadata without remapping the
                # widgets. Future legitimate re-management can still scale them.
                base_layout.update(held)

        guarded_apply_full_layout_padding._layout_visibility_guarded = True
        self.scaling._apply_full_layout_padding = guarded_apply_full_layout_padding


def install_layout_visibility_guard(app):
    existing = getattr(app, "_layout_visibility_guard", None)
    if existing is not None:
        return existing
    return LayoutVisibilityGuard(app)
