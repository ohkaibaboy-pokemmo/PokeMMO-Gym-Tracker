import tkinter as tk


def install_legacy_dashboard_guard(app):
    """Keep legacy presentation helpers alive without exposing stale UI."""

    def guard(controller, strip_name="strip"):
        strip = getattr(controller, strip_name, None)
        if strip is None:
            return

        def hide():
            try:
                strip.pack_forget()
            except Exception:
                pass

        hide()
        original = getattr(controller, "apply_scale", None)
        if callable(original) and not getattr(original, "_dashboard_hidden_guard", False):
            def guarded_apply_scale(*args, **kwargs):
                result = original(*args, **kwargs)
                hide()
                return result

            guarded_apply_scale._dashboard_hidden_guard = True
            controller.apply_scale = guarded_apply_scale

    presentation = getattr(app, "_presentation", None)
    if presentation is not None:
        guard(presentation, "status_strip")
    earnings = getattr(app, "_earnings_controller", None)
    if earnings is not None:
        guard(earnings, "strip")

    # The v0.5 footer described the old conservative allow-list model. v0.6 uses
    # opt-out semantics instead: detected trainer wins count unless an opponent is
    # explicitly excluded. Keep the visible guidance aligned with the actual rule.
    shell = getattr(app, "_dashboard_shell", None)
    manual_frame = getattr(shell, "manual_frame", None) if shell is not None else None
    if manual_frame is not None:
        for child in manual_frame.winfo_children():
            if not isinstance(child, tk.Label):
                continue
            try:
                text = str(child.cget("text") or "")
                if "normal trainers" in text.lower() or "verified" in text.lower():
                    child.configure(
                        text="Trainer wins count toward the 5-rule unless explicitly excluded."
                    )
            except tk.TclError:
                pass

    return app
