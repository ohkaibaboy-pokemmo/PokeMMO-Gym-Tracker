import tkinter as tk
from tkinter import ttk

from .scaling import UI_SCALE_FACTORS, UIScalingController, factor_for


def combobox_popdown_listbox_path(popdown_path):
    """Return Tk's internal Listbox path for one ttk Combobox popdown."""
    return f"{popdown_path}.f.l"


def configure_combobox_popup_font(widget):
    """Force a ttk Combobox's Windows popdown to use its field font.

    On Windows the dropdown Listbox is a Tcl-created child outside the normal
    widget tree. Styling/configuring the ttk Combobox therefore scales the field
    correctly while the opened menu can retain an oversized system/default font.
    Configure that popdown Listbox explicitly so field + choices always share the
    same app-controlled UI scale.
    """
    try:
        font_spec = widget.cget("font")
        popdown = widget.tk.call("ttk::combobox::PopdownWindow", str(widget))
        listbox = combobox_popdown_listbox_path(popdown)
        widget.tk.call(listbox, "configure", "-font", font_spec)
        return True
    except (tk.TclError, AttributeError):
        return False


class DashboardScalingController(UIScalingController):
    """v0.6 scaling adapter for dashboard-owned presentation components."""

    def _install_selector(self):
        host = getattr(self.app, "ui_scale_host", None)
        if host is None:
            return super()._install_selector()

        self.scale_label = tk.Label(host, text="UI Scale", font=("Segoe UI", 8), anchor="w")
        self.scale_label.pack(fill="x", pady=(0, 3))
        self.scale_combo = ttk.Combobox(
            host,
            textvariable=self.scale_var,
            state="readonly",
            values=tuple(UI_SCALE_FACTORS.keys()),
            style="Readable.TCombobox",
        )
        self.scale_combo.pack(fill="x")

        self._theme_scale_selector()

        dashboard = getattr(self.app, "_dashboard_shell", None)
        if dashboard is not None:
            try:
                sections = [
                    child
                    for child in dashboard.control_panel.winfo_children()
                    if isinstance(child, tk.Frame)
                ]
                if len(sections) >= 2:
                    filters, actions = sections[0], sections[1]
                    filters.pack_configure(pady=(10, 9))
                    actions.pack_configure(pady=(2, 11))
            except tk.TclError:
                pass

    def _theme_scale_selector(self):
        try:
            theme = self.app.theme()
            host = getattr(self.app, "ui_scale_host", None)
            if host is not None:
                host.configure(bg=theme["card_bg"])
            if hasattr(self, "scale_label"):
                self.scale_label.configure(bg=theme["card_bg"], fg=theme["muted"])
        except tk.TclError:
            pass

    def _apply_comboboxes(self, root=None):
        # The generic scaling controller correctly sizes the visible field. The
        # Windows popup is a Tcl-created Listbox outside the widget tree, so give
        # it the exact same font explicitly after every scale/map pass.
        super()._apply_comboboxes(root)
        root = root or self.app
        for widget in self._walk(root):
            if isinstance(widget, ttk.Combobox):
                configure_combobox_popup_font(widget)

    def _apply_component_scaling(self):
        super()._apply_component_scaling()
        factor = factor_for(self.app)
        dashboard = getattr(self.app, "_dashboard_shell", None)
        if dashboard is not None and hasattr(dashboard, "apply_scale"):
            dashboard.apply_scale(factor)
        gym_list = getattr(self.app, "_dashboard_gym_list", None)
        if gym_list is not None and hasattr(gym_list, "apply_scale"):
            gym_list.apply_scale(factor)
        center_chrome = getattr(self.app, "_dashboard_center_chrome", None)
        if center_chrome is not None and hasattr(center_chrome, "apply_scale"):
            center_chrome.apply_scale(factor)
        detector = getattr(self.app, "_dashboard_detector", None)
        if detector is not None and hasattr(detector, "apply_scale"):
            detector.apply_scale(factor)
        self._theme_scale_selector()


def install_dashboard_scaling(app):
    app._scaling_controller = DashboardScalingController(app)
    return app._scaling_controller
