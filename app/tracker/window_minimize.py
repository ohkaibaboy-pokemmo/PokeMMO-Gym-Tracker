import tkinter as tk

from .state import save_state


def install_compact_minimize(compact_window_cls):
    """Add reliable taskbar minimising to the frameless Compact window.

    Full view is the normal Tk root and already has native Windows minimise
    behaviour. Compact is an override-redirect Toplevel owned by that root, so
    Windows deliberately omits it from the taskbar. Rather than trying to force
    an owned utility window into the taskbar, Compact uses the hidden root as a
    taskbar surrogate while minimised. Restoring that taskbar entry immediately
    hands control back to the existing frameless/topmost Compact window.
    """

    original_init = compact_window_cls.__init__
    if getattr(original_init, "_compact_taskbar_minimise", False):
        return compact_window_cls

    original_paint_controls = compact_window_cls.paint_controls

    def paint_minimise_button(self, hovered=False):
        button = getattr(self, "min_button", None)
        if button is None:
            return
        self._min_hover = bool(hovered)
        try:
            theme = self.app.theme()
            button.configure(
                bg=theme["selected"] if hovered else theme["heading"],
                highlightbackground=theme["border"],
            )
            button.delete("all")
            width = int(button.cget("width"))
            height = int(button.cget("height"))
            y = max(4, int(round(height * 0.67)))
            margin = max(7, int(round(width * 0.30)))
            button.create_line(
                margin,
                y,
                width - margin,
                y,
                fill=theme["text"],
                width=max(1, int(round(getattr(self, "scale_factor", 1.0) * 2))),
            )
        except tk.TclError:
            pass

    def paint_controls_with_minimise(self):
        original_paint_controls(self)
        paint_minimise_button(self, getattr(self, "_min_hover", False))

    def restore_from_taskbar(self):
        if not getattr(self, "_compact_taskbar_minimised", False):
            return
        try:
            self._compact_taskbar_minimised = False
            self.app._compact_taskbar_arming = False

            # Hide the surrogate root before bringing Compact back so the Full
            # dashboard never replaces Compact on screen during the restore.
            self.app.withdraw()
            try:
                self.app.attributes("-alpha", 1.0)
            except tk.TclError:
                pass

            self.deiconify()
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            self.lift()
            self.after_idle(self.paint_controls)
        except tk.TclError:
            pass

    def minimise_to_taskbar(self):
        if getattr(self, "_compact_taskbar_minimised", False):
            return
        try:
            self.app.state_data["compact_geometry"] = self.geometry()
            save_state(self.app.state_data)

            self._compact_taskbar_minimised = True
            self.attributes("-topmost", False)
            self.withdraw()

            # The root is a genuine top-level application window, so Windows
            # will always give its iconified state a normal taskbar button. Keep
            # it transparent during the tiny deiconify -> iconify transition so
            # the Full dashboard cannot flash on screen.
            self.app._compact_taskbar_arming = True
            try:
                self.app.attributes("-alpha", 0.0)
            except tk.TclError:
                pass
            self.app.deiconify()
            self.app.update_idletasks()
            self.app.iconify()
            self.app.after_idle(lambda: setattr(self.app, "_compact_taskbar_arming", False))
        except tk.TclError:
            self._compact_taskbar_minimised = False
            self.app._compact_taskbar_arming = False
            try:
                self.app.withdraw()
                self.app.attributes("-alpha", 1.0)
                self.deiconify()
                self.overrideredirect(True)
                self.attributes("-topmost", True)
            except tk.TclError:
                pass

    def init_with_minimise(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._min_hover = False
        self._compact_taskbar_minimised = False

        try:
            self.min_button = tk.Canvas(
                self.dragbar,
                width=getattr(self, "control_width", 34),
                height=getattr(self, "control_height", 23),
                bd=1,
                relief="solid",
                highlightthickness=0,
                cursor="hand2",
                takefocus=False,
            )
            # close and restore/full are already packed on the right. Packing the
            # minimise control afterwards with side=right places it immediately
            # to their left: [ — ][ □ ][ X ].
            scale = getattr(self, "_scale", lambda value, minimum=1: value)
            self.min_button.pack(
                side="right",
                padx=(0, scale(4)),
                pady=scale(3),
            )
            self.min_button.bind("<Button-1>", lambda _event: self._minimise_to_taskbar())
            self.min_button.bind("<Enter>", lambda _event: self._paint_minimise_button(True))
            self.min_button.bind("<Leave>", lambda _event: self._paint_minimise_button(False))
            self.paint_controls()

            # Bind the root once. The callback always resolves the current
            # app.compact_window, so it remains valid if Compact is closed and
            # opened again later in the same session.
            if not getattr(self.app, "_compact_taskbar_restore_bound", False):
                self.app._compact_taskbar_restore_bound = True
                self.app._compact_taskbar_arming = False

                def root_mapped(_event=None, app=self.app):
                    if getattr(app, "_compact_taskbar_arming", False):
                        return
                    compact = getattr(app, "compact_window", None)
                    if (
                        compact is not None
                        and compact.winfo_exists()
                        and getattr(compact, "_compact_taskbar_minimised", False)
                    ):
                        compact.after_idle(compact._restore_from_taskbar)

                self.app.bind("<Map>", root_mapped, add="+")
        except tk.TclError:
            # Compact must still open even if a platform does not support the
            # taskbar adaptation exactly like Windows does.
            pass

    init_with_minimise._compact_taskbar_minimise = True
    paint_controls_with_minimise._compact_taskbar_minimise = True

    compact_window_cls.__init__ = init_with_minimise
    compact_window_cls.paint_controls = paint_controls_with_minimise
    compact_window_cls._paint_minimise_button = paint_minimise_button
    compact_window_cls._minimise_to_taskbar = minimise_to_taskbar
    compact_window_cls._restore_from_taskbar = restore_from_taskbar
    return compact_window_cls
