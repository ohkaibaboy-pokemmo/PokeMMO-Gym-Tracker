import tkinter as tk


def amount_only(value):
    """Return the numeric portion of a formatted money value."""
    value = str(value or "0").strip()
    if value[:1] in {"¥", "$"}:
        return value[1:]
    return value


def install_game_money_style(app):
    """Keep the project-owned coin stack with a normal `$` amount label.

    We experimented with a custom outlined dollar glyph based on the in-game HUD,
    but the regular UI glyph is cleaner at the dashboard's range of scale values.
    The primary display therefore remains deliberately simple:

        [coin stack] [$68,112]

    The coin stack is still our own pixel recreation; no extracted client bitmap
    is bundled.
    """
    shell = getattr(app, "_dashboard_shell", None)
    if shell is None:
        return None

    # DashboardShell already owns a live `$`-formatted StringVar. Restore it in
    # case this module is installed after an older experimental money treatment.
    shell.run_money_label.configure(textvariable=shell.run_money_var)

    original_apply_theme = shell.apply_theme
    original_apply_scale = shell.apply_scale

    def draw_coin_stack_only():
        theme = app.theme()
        canvas = shell.coin_icon
        try:
            canvas.delete("all")
            canvas.configure(bg=theme["card_bg"])
            width = max(16, int(float(canvas.cget("width"))))
            height = max(18, int(float(canvas.cget("height"))))
        except (tk.TclError, ValueError):
            return

        gold = theme["money"]
        shadow = theme["money_shadow"]
        scale_x = width / 20.0
        scale_y = height / 24.0

        def rect(x1, y1, x2, y2, fill):
            canvas.create_rectangle(
                round(x1 * scale_x),
                round(y1 * scale_y),
                round(x2 * scale_x),
                round(y2 * scale_y),
                fill=fill,
                outline="",
            )

        rect(2, 3, 14, 7, gold)
        rect(1, 8, 15, 12, gold)
        rect(3, 13, 16, 17, gold)
        rect(6, 18, 18, 22, gold)
        rect(3, 6, 12, 8, shadow)
        rect(2, 11, 13, 13, shadow)
        rect(4, 16, 14, 18, shadow)

    # DashboardShell calls this dynamically on theme/scale changes.
    shell._draw_coin_icon = draw_coin_stack_only

    def apply_theme(*args, **kwargs):
        result = original_apply_theme(*args, **kwargs)
        draw_coin_stack_only()
        return result

    def apply_scale(factor=1.0):
        original_apply_scale(factor)
        try:
            factor = float(factor)
            shell.coin_icon.configure(
                width=max(16, int(round(20 * factor))),
                height=max(18, int(round(24 * factor))),
            )
            # Tight but not touching: the amount begins immediately after the
            # small stack with one logical pixel of breathing room.
            shell.coin_icon.pack_configure(
                padx=(0, max(1, int(round(2 * factor))))
            )
            shell.run_money_label.pack_configure(padx=0)
        except (tk.TclError, TypeError, ValueError):
            pass
        draw_coin_stack_only()

    shell.apply_theme = apply_theme
    shell.apply_scale = apply_scale
    apply_scale(getattr(app, "ui_scale_factor", lambda: 1.0)())
    return shell
