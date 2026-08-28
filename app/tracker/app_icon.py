import tkinter as tk

from .icon_spec import WINDOW_ICON_SIZES, icon_spans


def make_window_icon(master, size):
    """Render one native-size muted segmented emblem as a Tk PhotoImage."""
    image = tk.PhotoImage(master=master, width=size, height=size)
    for x1, y1, x2, y2, colour in icon_spans(size):
        image.put(colour, to=(x1, y1, x2, y2))
    return image


def install_app_icon(app):
    """Apply native icon sizes to the root window and future Tk toplevels."""
    try:
        images = tuple(make_window_icon(app, size) for size in WINDOW_ICON_SIZES)
        # Keep all PhotoImages alive for the lifetime of the application. Tk can
        # then choose the closest native frame instead of downscaling one 64px
        # source for every title-bar/taskbar use.
        app._app_icon_photos = images
        app.iconphoto(True, *images)
        return images
    except tk.TclError:
        return None
