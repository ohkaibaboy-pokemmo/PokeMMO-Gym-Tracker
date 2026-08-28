"""Gym-type markers placed directly beside Compact gym names.

Tk's Treeview only supports native item images in its special ``#0`` column. The
first Compact pass used that column before ``#`` and felt cramped. A second pass
overlaid only the icon while leaving each Gym name natively centred, which looked
better but could overlap long names such as the Striaton variants.

This version overlays the icon *and* Gym name as one fixed-width content group.
The group width is based on the widest visible Gym name and is centred inside the
Gym column. Every icon therefore shares one vertical rail, every Gym name starts
at the same x-position, and long names cannot run back underneath the icon.
"""

import tkinter as tk
import tkinter.font as tkfont

from .dashboard_gym_list import gym_type_for_leader


BASE_ICON_SIZE = 15
BASE_ICON_GAP = 5
CELL_INSET = 2
TREE_BORDER_INSET = 2


def compact_type_icon_size(scale_factor=1.0):
    try:
        factor = max(0.85, float(scale_factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0
    return max(13, int(round(BASE_ICON_SIZE * factor)))


def compact_type_icon_gap(scale_factor=1.0):
    try:
        factor = max(0.85, float(scale_factor or 1.0))
    except (TypeError, ValueError):
        factor = 1.0
    return max(4, int(round(BASE_ICON_GAP * factor)))


def compact_type_max_text_width(cell_width, scale_factor=1.0):
    """Maximum Gym-text width that keeps the icon+text group inside its cell."""
    icon_size = compact_type_icon_size(scale_factor)
    gap = compact_type_icon_gap(scale_factor)
    return max(1, int(cell_width) - icon_size - gap - (CELL_INSET * 2))


def compact_type_icon_x(cell_x, cell_width, widest_text_width, scale_factor=1.0):
    """Return the centred shared content-group x-position for the Gym column."""
    icon_size = compact_type_icon_size(scale_factor)
    gap = compact_type_icon_gap(scale_factor)
    text_width = min(
        max(0, int(widest_text_width)),
        compact_type_max_text_width(cell_width, scale_factor),
    )
    content_width = icon_size + gap + text_width
    return max(
        int(cell_x) + CELL_INSET,
        int(round(cell_x + (cell_width - content_width) / 2.0)),
    )


def compact_type_prepare_tree_values(values):
    """Blank native Gym text before insertion while preserving it for overlays.

    The Compact table is refreshed frequently. Keeping the native Gym cell blank
    from the outset prevents a transient second copy from flashing underneath the
    icon+text overlay.
    """
    prepared = list(values or ())
    gym = ""
    if len(prepared) > 1:
        gym = str(prepared[1])
        prepared[1] = ""
    return tuple(prepared), gym


def compact_type_visible_height(
    row_y,
    row_height,
    tree_height,
    border_inset=TREE_BORDER_INSET,
):
    """Return the drawable row height without crossing the Treeview border.

    A final Treeview row can be only partly visible. Overlay children must be
    clipped to that same visible slice so Gym, Cooldown and 5-rule all disappear
    together at the native viewport edge instead of the Gym overlay painting over
    the border or vanishing while the native columns remain visible.
    """
    try:
        row_y = int(row_y)
        row_height = int(row_height)
        tree_height = int(tree_height)
        border_inset = max(0, int(border_inset))
    except (TypeError, ValueError):
        return 0
    if row_y < 0 or row_height <= 0 or tree_height <= 0:
        return 0
    drawable_bottom = max(0, tree_height - border_inset)
    if row_y >= drawable_bottom:
        return 0
    return max(0, min(row_height, drawable_bottom - row_y))


def compact_type_row_fully_visible(
    row_y,
    row_height,
    tree_height,
    border_inset=TREE_BORDER_INSET,
):
    """Compatibility helper for tests/callers that need full-row visibility."""
    try:
        expected = int(row_height)
    except (TypeError, ValueError):
        return False
    return expected > 0 and compact_type_visible_height(
        row_y,
        row_height,
        tree_height,
        border_inset,
    ) == expected


def _row_background(window, leader):
    theme = window.app.theme()
    try:
        tags = set(window.tree.item(leader, "tags"))
    except tk.TclError:
        tags = set()
    if "next" in tags:
        return theme["selection_bg"]
    return theme["panel_dark"]


def _row_foreground(window, leader):
    theme = window.app.theme()
    try:
        tags = set(window.tree.item(leader, "tags"))
    except tk.TclError:
        tags = set()
    if "ready" in tags:
        return theme["ready"]
    if "waiting" in tags:
        return theme["waiting"]
    if "unknown" in tags:
        return theme["unknown"]
    return theme["text"]


def _gym_text(window, leader):
    names = getattr(window, "_compact_type_gym_names", {})
    if leader in names:
        return str(names[leader])
    try:
        values = tuple(window.tree.item(leader, "values"))
    except tk.TclError:
        return ""
    return str(values[1]) if len(values) > 1 else ""


def _font_for_compact_rows(window):
    size = window._scale(9, 7)
    try:
        return tkfont.Font(root=window, family="Segoe UI", size=size)
    except tk.TclError:
        return None


def _measure_gym_text(window, row_font, gym):
    if row_font is not None:
        try:
            return row_font.measure(gym)
        except tk.TclError:
            pass
    return max(20, len(gym) * window._scale(7, 6))


def _hide_group(groups, leader):
    group = groups.get(leader)
    if group is not None:
        try:
            group["frame"].place_forget()
        except tk.TclError:
            pass


def _clear_stale_groups(window, live_items):
    groups = getattr(window, "_compact_type_groups", {})
    live = set(live_items)
    for leader in tuple(groups):
        if leader in live:
            continue
        try:
            groups[leader]["frame"].destroy()
        except tk.TclError:
            pass
        groups.pop(leader, None)
    window._compact_type_groups = groups


def _bind_group_wheel(window, widget):
    widget.bind(
        "<MouseWheel>",
        lambda event, tree=window.tree: tree.yview_scroll(
            int(-1 * (event.delta / 120)), "units"
        ),
        add="+",
    )


def _place_compact_type_icons(window):
    controller = getattr(window.app, "_type_icon_overrides", None)
    if controller is None or not hasattr(window, "tree"):
        return

    try:
        items = tuple(window.tree.get_children())
    except tk.TclError:
        return

    _clear_stale_groups(window, items)
    groups = getattr(window, "_compact_type_groups", {})
    images = {}
    scale_factor = getattr(window, "scale_factor", 1.0)
    icon_size = compact_type_icon_size(scale_factor)
    gap = compact_type_icon_gap(scale_factor)
    row_font = _font_for_compact_rows(window)

    gym_text = {leader: _gym_text(window, leader) for leader in items}
    measured_widest = max(
        (_measure_gym_text(window, row_font, text) for text in gym_text.values()),
        default=0,
    )
    try:
        gym_cell_width = int(window.tree.column("gym", "width"))
    except (tk.TclError, TypeError, ValueError):
        gym_cell_width = measured_widest + icon_size + gap + (CELL_INSET * 2)
    widest_text_width = min(
        measured_widest,
        compact_type_max_text_width(gym_cell_width, scale_factor),
    )

    try:
        tree_height = int(window.tree.winfo_height())
    except (tk.TclError, TypeError, ValueError):
        tree_height = 0

    for leader in items:
        gym_type = gym_type_for_leader(leader)
        image = controller.image_for_type(gym_type, icon_size, icon_size, fallback=True)
        if image is None:
            _hide_group(groups, leader)
            continue

        try:
            bbox = window.tree.bbox(leader, "gym")
        except tk.TclError:
            bbox = ()
        if not bbox or len(bbox) != 4:
            _hide_group(groups, leader)
            continue

        x, y, width, height = bbox
        if width <= 0 or height <= 0:
            _hide_group(groups, leader)
            continue

        visible_height = compact_type_visible_height(y, height, tree_height)
        if visible_height <= 0:
            _hide_group(groups, leader)
            continue

        row_text_width = min(
            widest_text_width,
            compact_type_max_text_width(width, scale_factor),
        )
        row_group_width = icon_size + gap + row_text_width
        group_x = compact_type_icon_x(x, width, row_text_width, scale_factor)
        group_y = y
        background = _row_background(window, leader)
        foreground = _row_foreground(window, leader)
        gym = gym_text.get(leader, "")

        group = groups.get(leader)
        if group is None:
            frame = tk.Frame(
                window.tree,
                bd=0,
                highlightthickness=0,
                takefocus=False,
            )
            icon = tk.Label(
                frame,
                bd=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                takefocus=False,
            )
            text = tk.Label(
                frame,
                bd=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                anchor="w",
                font=("Segoe UI", window._scale(9, 7)),
                takefocus=False,
            )
            for widget in (frame, icon, text):
                _bind_group_wheel(window, widget)
            group = {"frame": frame, "icon": icon, "text": text}
            groups[leader] = group

        try:
            group["frame"].configure(bg=background)
            group["icon"].configure(image=image, bg=background)
            group["text"].configure(
                text=gym,
                bg=background,
                fg=foreground,
                font=("Segoe UI", window._scale(9, 7)),
            )
            # The frame is the clipping viewport for the overlay. Child widgets
            # retain full-row geometry, but Tk clips them to visible_height so a
            # partial final Gym row matches the native partial Cooldown/5-rule row.
            group["frame"].place(
                x=group_x,
                y=group_y,
                width=max(1, row_group_width),
                height=visible_height,
            )
            group["icon"].place(
                x=0,
                y=max(0, int(round((height - icon_size) / 2.0))),
                width=icon_size,
                height=icon_size,
            )
            group["text"].place(
                x=icon_size + gap,
                y=0,
                width=max(1, row_text_width),
                height=height,
            )
            group["frame"].lift()
        except tk.TclError:
            _hide_group(groups, leader)
            continue
        images[leader] = image

    window._compact_type_groups = groups
    window._compact_type_icon_images = images


def _schedule_compact_type_icon_layout(window):
    job = getattr(window, "_compact_type_icon_job", None)
    if job is not None:
        try:
            window.after_cancel(job)
        except tk.TclError:
            pass
    try:
        window._compact_type_icon_job = window.after_idle(
            lambda: _finish_compact_type_icon_layout(window)
        )
    except tk.TclError:
        window._compact_type_icon_job = None


def _finish_compact_type_icon_layout(window):
    window._compact_type_icon_job = None
    _place_compact_type_icons(window)


def _sync_compact_tree(window):
    """Sync Compact rows in place instead of deleting/reinserting every second.

    Cooldown text changes every second, but that should only update the affected
    native cells. Rebuilding the full Treeview caused visible 1.5x pulsing and also
    forced all icon/name overlays to be laid out again. This keeps stable rows and
    schedules overlay work only when row identity/order, Gym names or semantic tags
    actually change.
    """
    try:
        existing_order = list(window.tree.get_children())
        source_items = tuple(window.app.tree.get_children())
    except tk.TclError:
        return False

    desired_order = []
    captured_names = {}
    overlay_changed = False

    for item in source_items:
        try:
            values = tuple(window.app.tree.item(item, "values"))
            tags = tuple(window.app.tree.item(item, "tags"))
        except tk.TclError:
            continue
        if len(values) < 8:
            continue

        compact_values = (values[0], values[2], values[4], values[5])
        prepared, gym = compact_type_prepare_tree_values(compact_values)
        desired_order.append(item)
        captured_names[item] = gym

        if item not in existing_order:
            try:
                window.tree.insert(
                    "",
                    "end",
                    iid=item,
                    values=prepared,
                    tags=tags,
                )
            except tk.TclError:
                continue
            overlay_changed = True
            continue

        try:
            old_values = tuple(window.tree.item(item, "values"))
            old_tags = tuple(window.tree.item(item, "tags"))
            if old_values != prepared:
                window.tree.item(item, values=prepared)
            if old_tags != tags:
                window.tree.item(item, tags=tags)
                overlay_changed = True
        except tk.TclError:
            pass

    desired_set = set(desired_order)
    for item in existing_order:
        if item in desired_set:
            continue
        try:
            window.tree.delete(item)
        except tk.TclError:
            pass
        overlay_changed = True

    try:
        current_order = list(window.tree.get_children())
        if current_order != desired_order:
            for index, item in enumerate(desired_order):
                if item in window.tree.get_children():
                    window.tree.move(item, "", index)
            overlay_changed = True
    except tk.TclError:
        pass

    if captured_names != getattr(window, "_compact_type_gym_names", {}):
        overlay_changed = True
    window._compact_type_gym_names = captured_names
    return overlay_changed


def install_compact_type_icons(compact_cls):
    """Patch CompactWindow once so aligned type+Gym groups stay centred."""
    if getattr(compact_cls, "_type_icons_installed", False):
        return compact_cls

    original_build_route_card = compact_cls._build_route_card
    original_resize = compact_cls._resize_table_columns
    original_theme = compact_cls._apply_dashboard_theme

    def build_route_card_with_type_icons(self, *args, **kwargs):
        result = original_build_route_card(self, *args, **kwargs)
        self._compact_type_groups = {}
        self._compact_type_icon_images = {}
        self._compact_type_gym_names = {}
        self._compact_type_icon_job = None

        try:
            self.tree.configure(show="headings")
            original_yscroll = self.tree.cget("yscrollcommand")

            def yscroll_with_icon_layout(first, last):
                try:
                    self.scrollbar.set(first, last)
                except tk.TclError:
                    pass
                _schedule_compact_type_icon_layout(self)

            if original_yscroll:
                self.tree.configure(yscrollcommand=yscroll_with_icon_layout)
            self.tree.bind(
                "<Expose>",
                lambda _event: _schedule_compact_type_icon_layout(self),
                add="+",
            )
        except tk.TclError:
            pass
        return result

    def resize_with_type_icons(self, event=None):
        result = original_resize(self, event)
        _schedule_compact_type_icon_layout(self)
        return result

    def refresh_with_type_icons(self, *args, **kwargs):
        try:
            self.char_combo["values"] = tuple(self.app.char_combo["values"])
            self.route_combo["values"] = tuple(self.app.route_combo["values"])
        except Exception:
            pass

        self._refresh_live()
        self._refresh_status_metrics()
        self._refresh_money()

        if _sync_compact_tree(self):
            _schedule_compact_type_icon_layout(self)

    def theme_with_type_icons(self, *args, **kwargs):
        result = original_theme(self, *args, **kwargs)
        _schedule_compact_type_icon_layout(self)
        return result

    compact_cls._build_route_card = build_route_card_with_type_icons
    compact_cls._resize_table_columns = resize_with_type_icons
    compact_cls.refresh = refresh_with_type_icons
    compact_cls._apply_dashboard_theme = theme_with_type_icons
    compact_cls._type_icons_installed = True
    return compact_cls
