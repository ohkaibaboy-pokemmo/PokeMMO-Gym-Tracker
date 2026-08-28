import tkinter as tk

from .dashboard_scrollbar import DashboardScrollbar


def _wrap_component(component, scrollbar):
    """Keep a custom scrollbar synced with an existing dashboard component."""
    original_theme = component.apply_theme
    if not getattr(original_theme, "_dashboard_scrollbar_wrapped", False):
        def themed(*args, **kwargs):
            result = original_theme(*args, **kwargs)
            scrollbar.apply_theme()
            return result

        themed._dashboard_scrollbar_wrapped = True
        component.apply_theme = themed

    original_scale = component.apply_scale
    if not getattr(original_scale, "_dashboard_scrollbar_wrapped", False):
        def scaled(factor=1.0, *args, **kwargs):
            result = original_scale(factor, *args, **kwargs)
            scrollbar.apply_scale(factor)
            return result

        scaled._dashboard_scrollbar_wrapped = True
        component.apply_scale = scaled


def install_dashboard_scrollbars(app):
    """Replace bright native Windows scrollbars on Full dashboard surfaces."""
    installed = []

    gym_list = getattr(app, "_dashboard_gym_list", None)
    if gym_list is not None and not hasattr(gym_list, "_dashboard_scrollbar"):
        try:
            gym_list.scrollbar.pack_forget()
        except (AttributeError, tk.TclError):
            pass
        scrollbar = DashboardScrollbar(gym_list.body, gym_list.canvas, app, logical_width=10)
        scrollbar.pack(side="right", fill="y", padx=(2, 2), pady=2)
        gym_list._dashboard_scrollbar = scrollbar
        _wrap_component(gym_list, scrollbar)
        installed.append(scrollbar)

    detector = getattr(app, "_dashboard_detector", None)
    if detector is not None and not hasattr(detector, "_dashboard_scrollbar"):
        try:
            detector.body_scrollbar.pack_forget()
        except (AttributeError, tk.TclError):
            pass
        scrollbar = DashboardScrollbar(detector.body_shell, detector.body_canvas, app, logical_width=10)
        scrollbar.pack(side="right", fill="y", padx=(2, 4), pady=4)
        detector._dashboard_scrollbar = scrollbar
        _wrap_component(detector, scrollbar)
        installed.append(scrollbar)

    # Match the current scale immediately when this layer is installed after the
    # dashboard components have already had their initial 1.0x pass.
    factor = 1.0
    try:
        raw = str(app.ui_scale_var.get()).lower().replace("×", "x").strip()
        factor = float(raw[:-1] if raw.endswith("x") else raw)
    except Exception:
        pass
    for scrollbar in installed:
        scrollbar.apply_scale(factor)
        scrollbar.apply_theme()

    app._dashboard_scrollbars = installed
    return installed
