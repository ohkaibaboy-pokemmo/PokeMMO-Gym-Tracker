import tkinter as tk

from .dashboard_table_alignment import full_leader_group_geometry
from .earnings import GYM_BASE_PAYOUTS


DASHBOARD_PORTRAIT_NUMERATOR = 4
DASHBOARD_PORTRAIT_DENOMINATOR = 3
ROW_HEIGHT_BASE = 58
HEADER_HEIGHT_BASE = 38

# Project-owned Full-view type markers. These deliberately avoid bundled/ripped
# game assets: each gym specialty gets a small coloured symbol drawn by Tk.
GYM_TYPES = {
    "Brock": "Rock",
    "Misty": "Water",
    "Lt. Surge": "Electric",
    "Erika": "Grass",
    "Koga": "Poison",
    "Sabrina": "Psychic",
    "Blaine": "Fire",
    "Falkner": "Flying",
    "Bugsy": "Bug",
    "Whitney": "Normal",
    "Morty": "Ghost",
    "Chuck": "Fighting",
    "Jasmine": "Steel",
    "Pryce": "Ice",
    "Clair": "Dragon",
    "Roxanne": "Rock",
    "Brawly": "Fighting",
    "Wattson": "Electric",
    "Flannery": "Fire",
    "Norman": "Normal",
    "Winona": "Flying",
    "Tate & Liza": "Psychic",
    "Juan": "Water",
    "Roark": "Rock",
    "Gardenia": "Grass",
    "Maylene": "Fighting",
    "Crasher Wake": "Water",
    "Fantina": "Ghost",
    "Byron": "Steel",
    "Candice": "Ice",
    "Volkner": "Electric",
    "Cilan": "Grass",
    "Chili": "Fire",
    "Cress": "Water",
    "Lenora": "Normal",
    "Burgh": "Bug",
    "Elesa": "Electric",
    "Clay": "Ground",
    "Skyla": "Flying",
    "Brycen": "Ice",
    "Iris": "Dragon",
}

TYPE_MARKERS = {
    "Normal": ("#9FA19F", "●"),
    "Fighting": ("#FF8000", "✦"),
    "Flying": ("#81B9EF", "➤"),
    "Poison": ("#9141CB", "☣"),
    "Ground": ("#915121", "▰"),
    "Rock": ("#AFA981", "◆"),
    "Bug": ("#91A119", "✣"),
    "Ghost": ("#704170", "◉"),
    "Steel": ("#60A1B8", "⬢"),
    "Fire": ("#E62829", "▲"),
    "Water": ("#2980EF", "≈"),
    "Grass": ("#3FA129", "❧"),
    "Electric": ("#FAC000", "ϟ"),
    "Psychic": ("#EF4179", "✧"),
    "Ice": ("#3DCEF3", "❄"),
    "Dragon": ("#5060E1", "◇"),
}

COLUMN_SPECS = (
    (0, "", 60, 0),
    (1, "#", 48, 0),
    (2, "Leader", 138, 2),
    (3, "Gym", 138, 2),
    (4, "Region", 92, 1),
    (5, "5-rule", 76, 0),
    (6, "Cooldown", 116, 0),
    (7, "Last Defeated", 148, 2),
    (8, "Status", 104, 0),
    (9, "Payout", 92, 0),
)


def gym_type_for_leader(leader):
    return GYM_TYPES.get(str(leader or ""), "")


def status_from_text(value):
    text = str(value or "UNKNOWN").strip().upper()
    if text.startswith("READY"):
        return "READY"
    if text.startswith("WAITING"):
        return "WAITING"
    if text.startswith("COOLDOWN"):
        return "COOLDOWN"
    return "UNKNOWN"


def payout_for_record(leader, record):
    """Return the best local payout value for a gym row."""
    if record:
        try:
            payout = record.get("payout")
            if payout is not None:
                return int(payout), True
        except (TypeError, ValueError, AttributeError):
            pass
    return int(GYM_BASE_PAYOUTS.get(leader, 0)), False


def format_dashboard_money(value):
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return "—"
    return f"${amount:,}" if amount else "—"


def dashboard_column_layout(total_width, factor=1.0):
    """Return ``[(left, right), ...]`` for the responsive Full-route columns."""
    try:
        width = max(1, int(total_width))
        factor = max(0.85, float(factor or 1.0))
    except (TypeError, ValueError):
        width, factor = 1012, 1.0

    minimums = [max(30, int(round(spec[2] * factor))) for spec in COLUMN_SPECS]
    minimum_total = sum(minimums)
    if width <= minimum_total:
        ratio = width / float(minimum_total)
        widths = [max(1, int(round(value * ratio))) for value in minimums]
        widths[-1] += width - sum(widths)
    else:
        widths = list(minimums)
        extra = width - minimum_total
        total_weight = sum(spec[3] for spec in COLUMN_SPECS)
        assigned = 0
        for index, spec in enumerate(COLUMN_SPECS):
            if not spec[3] or not total_weight:
                continue
            addition = int(round(extra * spec[3] / total_weight))
            widths[index] += addition
            assigned += addition
        # Rounding remainder belongs to the last flexible column (Last Defeated).
        flexible = [index for index, spec in enumerate(COLUMN_SPECS) if spec[3]]
        if flexible:
            widths[flexible[-1]] += extra - assigned

    result = []
    x = 0
    for value in widths:
        result.append((x, x + value))
        x += value
    if result:
        result[-1] = (result[-1][0], width)
    return result


def _rounded_box_points(x1, y1, x2, y2, radius):
    r = max(1, min(float(radius), (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    return (
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    )


class GymRow:
    """Lightweight row state for the single-Canvas Full Gym Route renderer."""

    def __init__(self, leader):
        self.leader = leader
        self.gym_type = gym_type_for_leader(leader)
        self.data = {}
        self.status_code = "UNKNOWN"
        self.is_next = False
        self.is_selected = False
        self.is_hovered = False
        self.payout_actual = False
        self.payout_text = "—"
        self.portrait = None
        self.type_image = None
        self.items = {}

    def update(self, values, tags, portrait, payout_text, payout_actual):
        position, region, gym, leader, cooldown, rule, last, status = values[:8]
        incoming = {
            "position": position or "—",
            "leader": leader,
            "gym": gym,
            "region": region,
            "rule": rule,
            "cooldown": cooldown,
            "last": last,
            "status": status,
        }
        changed = {key for key, value in incoming.items() if self.data.get(key) != value}
        self.data.update(incoming)

        new_status = status_from_text(status)
        if new_status != self.status_code:
            self.status_code = new_status
            changed.add("semantic")

        new_next = "next" in set(tags)
        if new_next != self.is_next:
            self.is_next = new_next
            changed.add("semantic")

        new_actual = bool(payout_actual)
        if new_actual != self.payout_actual:
            self.payout_actual = new_actual
            changed.add("semantic")
        if payout_text != self.payout_text:
            self.payout_text = payout_text
            changed.add("payout")

        if portrait is not self.portrait:
            self.portrait = portrait
            changed.add("portrait")
        return changed

    def set_selected(self, selected):
        selected = bool(selected)
        changed = selected != self.is_selected
        self.is_selected = selected
        return changed


class DashboardGymList:
    """Scrollable Full Gym Route rendered as Canvas primitives.

    The previous implementation embedded a Frame plus roughly a dozen Tk widgets
    for every visible gym. Windows had to reflow/repaint hundreds of child windows
    during a native resize, which produced the tearing seen in live validation.

    This implementation keeps the proven hidden Treeview as the model/selection
    source but renders all visible rows directly on one body Canvas. Vertical
    resizing becomes effectively free: Tk simply reveals more of the existing
    canvas. Horizontal resizing only moves Canvas item coordinates and does not
    construct/reflow child widgets.
    """

    COLUMN_SPECS = COLUMN_SPECS
    ROW_RENDERER = "canvas"

    def __init__(self, app, shell):
        self.app = app
        self.shell = shell
        self.legacy_frame = shell.table_frame
        self.rows = {}
        self.order = []
        self.selected_leader = None
        self.hovered_leader = None
        self.factor = 1.0
        self.row_height = ROW_HEIGHT_BASE
        self.header_height = HEADER_HEIGHT_BASE
        self._portrait_cache = {}
        self._wheel_bound = False
        self._layout_after_id = None
        self._last_layout_width = 0

        self.container = tk.Frame(app, bd=0, highlightthickness=1)
        before = shell.manual_frame if shell.manual_frame is not None else shell.detector_frame
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 8), before=before)
        try:
            self.legacy_frame.pack_forget()
        except tk.TclError:
            pass

        self.header = tk.Canvas(
            self.container,
            height=self.header_height,
            bd=0,
            highlightthickness=0,
            takefocus=False,
        )
        self.header.pack(fill="x", padx=1, pady=(1, 0))
        self._header_items = [
            self.header.create_text(0, 0, text=title, anchor="center")
            for _column, title, _minsize, _weight in self.COLUMN_SPECS
        ]

        self.body = tk.Frame(self.container, bd=0)
        self.body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            self.body,
            bd=0,
            highlightthickness=0,
            takefocus=False,
            yscrollincrement=self.row_height,
        )
        self.scrollbar = tk.Scrollbar(self.body, orient="vertical", command=self.canvas.yview, width=12)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<Configure>", self._canvas_configured, add="+")
        self.header.bind("<Configure>", self._header_configured, add="+")
        self.canvas.bind("<Enter>", self._bind_wheel, add="+")
        self.canvas.bind("<Leave>", self._canvas_left, add="+")
        self.canvas.bind("<Motion>", self._motion, add="+")
        self.canvas.bind("<Button-1>", self._clicked, add="+")

        self._wrap_refresh()
        self.refresh_from_model(force_structure=True)
        self.apply_theme()
        app.theme_var.trace_add("write", lambda *_args: app.after_idle(self.apply_theme))
        app._dashboard_gym_list = self

    def _wrap_refresh(self):
        original_refresh = self.app.refresh_table
        if getattr(original_refresh, "_dashboard_gym_list_wrapped", False):
            return

        def refresh_with_dashboard_rows(*args, **kwargs):
            result = original_refresh(*args, **kwargs)
            self.refresh_from_model()
            return result

        refresh_with_dashboard_rows._dashboard_gym_list_wrapped = True
        self.app.refresh_table = refresh_with_dashboard_rows

    def _header_configured(self, _event=None):
        self._schedule_layout()

    def _canvas_configured(self, event):
        # Height-only changes need no row work at all; the Canvas simply reveals
        # more/less of its existing scrollregion. Only horizontal changes require
        # column coordinate updates.
        width = max(1, int(event.width))
        if width != self._last_layout_width:
            self._schedule_layout()

    def _schedule_layout(self):
        if self._layout_after_id is not None:
            return
        try:
            self._layout_after_id = self.app.after_idle(self._layout)
        except tk.TclError:
            self._layout_after_id = None

    def _bind_wheel(self, _event=None):
        if self._wheel_bound:
            return
        self._wheel_bound = True
        self.canvas.bind_all("<MouseWheel>", self._mousewheel, add="+")

    def _unbind_wheel(self):
        if not self._wheel_bound:
            return
        self._wheel_bound = False
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    def _canvas_left(self, _event=None):
        self._unbind_wheel()
        if self.hovered_leader:
            old = self.rows.get(self.hovered_leader)
            self.hovered_leader = None
            if old is not None:
                old.is_hovered = False
                self._apply_row_style(old)

    def _mousewheel(self, event):
        try:
            units = int(-1 * (event.delta / 120))
            if units:
                self.canvas.yview_scroll(units, "units")
        except tk.TclError:
            pass
        return "break"

    def _leader_at(self, event):
        try:
            y = float(self.canvas.canvasy(event.y))
        except tk.TclError:
            return None
        index = int(y // max(1, self.row_height))
        if 0 <= index < len(self.order):
            return self.order[index]
        return None

    def _motion(self, event):
        leader = self._leader_at(event)
        if leader == self.hovered_leader:
            return
        old = self.rows.get(self.hovered_leader)
        if old is not None:
            old.is_hovered = False
            self._apply_row_style(old)
        self.hovered_leader = leader
        new = self.rows.get(leader)
        if new is not None:
            new.is_hovered = True
            self._apply_row_style(new)

    def _clicked(self, event):
        leader = self._leader_at(event)
        if leader:
            self.select(leader)
        return "break"

    def select(self, leader):
        if leader not in self.rows:
            return
        previous = self.rows.get(self.selected_leader)
        self.selected_leader = leader
        try:
            self.app.tree.selection_set(leader)
        except tk.TclError:
            pass
        if previous is not None and previous.leader != leader and previous.set_selected(False):
            self._apply_row_style(previous)
        current = self.rows.get(leader)
        if current is not None and current.set_selected(True):
            self._apply_row_style(current)

    def _restore_model_selection(self):
        if self.selected_leader and self.selected_leader in self.order:
            try:
                self.app.tree.selection_set(self.selected_leader)
            except tk.TclError:
                pass

    def _portrait_for(self, leader):
        presentation = getattr(self.app, "_presentation", None)
        if presentation is None:
            return None
        source = getattr(presentation, "_leader_images", {}).get(leader)
        if source is None:
            return None
        key = (leader, str(source), self.factor)
        if key in self._portrait_cache:
            return self._portrait_cache[key]
        try:
            image = source.zoom(DASHBOARD_PORTRAIT_NUMERATOR, DASHBOARD_PORTRAIT_NUMERATOR).subsample(
                DASHBOARD_PORTRAIT_DENOMINATOR, DASHBOARD_PORTRAIT_DENOMINATOR
            )
        except tk.TclError:
            image = source
        self._portrait_cache[key] = image
        if len(self._portrait_cache) > 180:
            self._portrait_cache = {key: image}
        return image

    def _row_payout(self, leader):
        _char_name, record = self.app.merged_record(leader)
        amount, actual = payout_for_record(leader, record)
        return format_dashboard_money(amount), actual

    def refresh_from_model(self, force_structure=False):
        try:
            visible = tuple(self.app.tree.get_children())
        except tk.TclError:
            return

        if force_structure or visible != tuple(self.order):
            self._rebuild_structure(visible)

        for leader in visible:
            row = self.rows.get(leader)
            if row is None:
                continue
            try:
                values = tuple(self.app.tree.item(leader, "values"))
                tags = tuple(self.app.tree.item(leader, "tags"))
            except tk.TclError:
                continue
            payout_text, payout_actual = self._row_payout(leader)
            changed = row.update(
                values,
                tags,
                self._portrait_for(leader),
                payout_text,
                payout_actual,
            )
            if changed:
                self._sync_row_content(row, changed)
            self._refresh_type_icon(row)
            if row.set_selected(leader == self.selected_leader):
                self._apply_row_style(row)

        self._restore_model_selection()

    def _rebuild_structure(self, visible):
        try:
            self.canvas.delete("all")
        except tk.TclError:
            return
        self.rows = {}
        self.order = list(visible)
        self.hovered_leader = None
        if self.selected_leader not in self.order:
            self.selected_leader = None

        for leader in self.order:
            row = GymRow(leader)
            self.rows[leader] = row
            self._create_row_items(row)
        self._last_layout_width = 0
        self._layout()

    def _create_row_items(self, row):
        c = self.canvas
        row.items = {
            "background": c.create_rectangle(0, 0, 1, 1, width=1),
            "portrait": c.create_image(0, 0, anchor="center"),
            "position": c.create_text(0, 0, text="—", anchor="center"),
            "type_bg": c.create_oval(0, 0, 1, 1, outline=""),
            "type_glyph": c.create_text(0, 0, text="", anchor="center"),
            "type_image": c.create_image(0, 0, anchor="center", state="hidden"),
            "leader": c.create_text(0, 0, text=row.leader, anchor="w"),
            "gym": c.create_text(0, 0, text="—", anchor="center"),
            "region": c.create_text(0, 0, text="—", anchor="center"),
            "rule": c.create_text(0, 0, text="—", anchor="center"),
            "cooldown": c.create_text(0, 0, text="—", anchor="center"),
            "last": c.create_text(0, 0, text="—", anchor="center"),
            "status_bg": c.create_polygon(0, 0, 1, 1, smooth=True, splinesteps=12, outline=""),
            "status": c.create_text(0, 0, text="UNKNOWN", anchor="center"),
            "payout": c.create_text(0, 0, text="—", anchor="e"),
        }
        self._configure_row_fonts(row)
        self._apply_row_style(row)

    def _configure_row_fonts(self, row):
        s = lambda value, minimum=7: max(minimum, int(round(value * self.factor)))
        try:
            for key in ("position", "leader", "gym", "region", "rule", "cooldown", "last"):
                self.canvas.itemconfigure(row.items[key], font=("Segoe UI", s(9)))
            self.canvas.itemconfigure(row.items["payout"], font=("Segoe UI Semibold", s(9)))
            self.canvas.itemconfigure(row.items["status"], font=("Segoe UI Semibold", s(8)))
            self.canvas.itemconfigure(row.items["type_glyph"], font=("Segoe UI Symbol", s(11, 8), "bold"))
        except tk.TclError:
            pass

    def _sync_row_content(self, row, changed):
        c = self.canvas
        try:
            for key in ("position", "leader", "gym", "region", "rule", "cooldown", "last"):
                if key in changed:
                    c.itemconfigure(row.items[key], text=row.data.get(key, "—"))
            if "status" in changed or "semantic" in changed:
                c.itemconfigure(row.items["status"], text=row.status_code)
            if "payout" in changed:
                c.itemconfigure(row.items["payout"], text=row.payout_text)
            if "portrait" in changed:
                c.itemconfigure(row.items["portrait"], image=row.portrait if row.portrait is not None else "")
            if "semantic" in changed:
                self._apply_row_style(row)
        except tk.TclError:
            pass

    def _refresh_type_icon(self, row):
        controller = getattr(self.app, "_type_icon_overrides", None)
        _group, icon_size, _gap, _text = full_leader_group_geometry(self.factor)
        custom = None
        if controller is not None:
            custom = controller.image_for_type(row.gym_type, icon_size, icon_size, fallback=False)
        if custom is row.type_image:
            return
        row.type_image = custom
        try:
            if custom is not None:
                self.canvas.itemconfigure(row.items["type_image"], image=custom, state="normal")
                self.canvas.itemconfigure(row.items["type_bg"], state="hidden")
                self.canvas.itemconfigure(row.items["type_glyph"], state="hidden")
            else:
                self.canvas.itemconfigure(row.items["type_image"], image="", state="hidden")
                self.canvas.itemconfigure(row.items["type_bg"], state="normal")
                self.canvas.itemconfigure(row.items["type_glyph"], state="normal")
        except tk.TclError:
            pass

    def _row_colours(self, row, theme):
        if row.is_selected:
            return theme["selected"], theme["accent"]
        if row.is_next:
            return theme["selection_bg"], theme["selection_border"]
        if row.is_hovered:
            return theme["panel"], theme["border"]
        return theme["card_bg"], theme["card_border"]

    def _apply_row_style(self, row):
        theme = self.app.theme()
        background, border = self._row_colours(row, theme)
        status_colour = {
            "READY": theme["ready"],
            "WAITING": theme["waiting"],
            "COOLDOWN": theme["cooldown"],
            "UNKNOWN": theme["unknown"],
        }[row.status_code]
        status_bg = {
            "READY": theme["ready_bg"],
            "WAITING": theme["waiting_bg"],
            "COOLDOWN": theme["cooldown_bg"],
            "UNKNOWN": theme["unknown_bg"],
        }[row.status_code]
        marker_colour, glyph = TYPE_MARKERS.get(row.gym_type, (theme["unknown"], ""))

        try:
            self.canvas.itemconfigure(row.items["background"], fill=background, outline=border)
            self.canvas.itemconfigure(row.items["type_bg"], fill=marker_colour)
            self.canvas.itemconfigure(row.items["type_glyph"], text=glyph, fill="#FFFFFF")
            self.canvas.itemconfigure(row.items["leader"], fill=theme["text"])
            self.canvas.itemconfigure(row.items["gym"], fill=theme["text"])
            self.canvas.itemconfigure(row.items["region"], fill=theme["muted"] if row.status_code != "UNKNOWN" else theme["unknown"])
            self.canvas.itemconfigure(row.items["rule"], fill=status_colour if row.status_code != "UNKNOWN" else theme["unknown"])
            self.canvas.itemconfigure(row.items["cooldown"], fill=status_colour if row.status_code != "UNKNOWN" else theme["unknown"])
            self.canvas.itemconfigure(row.items["last"], fill=theme["text"] if row.status_code != "UNKNOWN" else theme["unknown"])
            self.canvas.itemconfigure(row.items["position"], fill=theme["text"] if row.status_code != "UNKNOWN" else theme["unknown"])
            self.canvas.itemconfigure(row.items["status_bg"], fill=status_bg)
            self.canvas.itemconfigure(row.items["status"], fill=status_colour)
            self.canvas.itemconfigure(row.items["payout"], fill=theme["money"] if row.payout_actual else theme["muted"])
        except tk.TclError:
            pass

    def _layout_header(self, bounds):
        y = self.header_height / 2.0
        for index, item in enumerate(self._header_items):
            left, right = bounds[index]
            if index == 9:
                x, anchor = right - max(8, int(round(12 * self.factor))), "e"
            else:
                x, anchor = (left + right) / 2.0, "center"
            try:
                self.header.coords(item, x, y)
                self.header.itemconfigure(item, anchor=anchor)
            except tk.TclError:
                pass

    def _layout_row(self, row, index, bounds, width):
        y1 = index * self.row_height
        y2 = y1 + self.row_height
        cy = (y1 + y2) / 2.0
        pad = max(4, int(round(5 * self.factor)))
        group_width, icon_size, gap, _text_width = full_leader_group_geometry(self.factor)

        try:
            self.canvas.coords(row.items["background"], 1, y1 + 1, max(2, width - 1), y2 - 1)

            # Portrait / #
            self.canvas.coords(row.items["portrait"], sum(bounds[0]) / 2.0, cy)
            self.canvas.coords(row.items["position"], sum(bounds[1]) / 2.0, cy)

            # Type marker + Leader are one centred group inside the Leader column.
            l2, r2 = bounds[2]
            available = max(icon_size + gap + 1, (r2 - l2) - (2 * pad))
            group_width = min(group_width, available)
            start = (l2 + r2 - group_width) / 2.0
            icon_cx = start + icon_size / 2.0
            inset = max(1, int(round(icon_size * 0.08)))
            self.canvas.coords(
                row.items["type_bg"],
                icon_cx - icon_size / 2.0 + inset,
                cy - icon_size / 2.0 + inset,
                icon_cx + icon_size / 2.0 - inset,
                cy + icon_size / 2.0 - inset,
            )
            self.canvas.coords(row.items["type_glyph"], icon_cx, cy)
            self.canvas.coords(row.items["type_image"], icon_cx, cy)
            self.canvas.coords(row.items["leader"], start + icon_size + gap, cy)

            # Main table columns.
            self.canvas.coords(row.items["gym"], sum(bounds[3]) / 2.0, cy)
            self.canvas.coords(row.items["region"], sum(bounds[4]) / 2.0, cy)
            self.canvas.coords(row.items["rule"], sum(bounds[5]) / 2.0, cy)
            self.canvas.coords(row.items["cooldown"], sum(bounds[6]) / 2.0, cy)
            self.canvas.coords(row.items["last"], sum(bounds[7]) / 2.0, cy)

            # Status pill.
            l8, r8 = bounds[8]
            status_width = min(max(74, int(round(92 * self.factor))), max(40, (r8 - l8) - (2 * pad)))
            status_height = max(22, int(round(26 * self.factor)))
            sx1 = (l8 + r8 - status_width) / 2.0
            sx2 = sx1 + status_width
            sy1 = cy - status_height / 2.0
            sy2 = cy + status_height / 2.0
            self.canvas.coords(
                row.items["status_bg"],
                *_rounded_box_points(sx1, sy1, sx2, sy2, min(9, status_height * 0.28)),
            )
            self.canvas.coords(row.items["status"], (l8 + r8) / 2.0, cy)

            # Currency scans against a shared right rail.
            self.canvas.coords(row.items["payout"], bounds[9][1] - max(8, int(round(12 * self.factor))), cy)
        except tk.TclError:
            pass

    def _layout(self):
        self._layout_after_id = None
        try:
            width = max(1, int(self.canvas.winfo_width()))
        except tk.TclError:
            return
        self._last_layout_width = width
        bounds = dashboard_column_layout(width, self.factor)
        self._layout_header(bounds)
        for index, leader in enumerate(self.order):
            row = self.rows.get(leader)
            if row is not None:
                self._layout_row(row, index, bounds, width)
        try:
            total_height = max(1, len(self.order) * self.row_height)
            self.canvas.configure(scrollregion=(0, 0, width, total_height))
        except tk.TclError:
            pass

    def apply_scale(self, factor=1.0):
        try:
            self.factor = max(0.85, float(factor or 1.0))
        except (TypeError, ValueError):
            self.factor = 1.0
        self.row_height = max(48, int(round(ROW_HEIGHT_BASE * self.factor)))
        self.header_height = max(32, int(round(HEADER_HEIGHT_BASE * self.factor)))
        self._portrait_cache.clear()
        try:
            self.header.configure(height=self.header_height)
            self.canvas.configure(yscrollincrement=self.row_height)
            self.scrollbar.configure(width=max(10, int(round(12 * self.factor))))
            header_font = ("Segoe UI Semibold", max(8, int(round(9 * self.factor))))
            for item in self._header_items:
                self.header.itemconfigure(item, font=header_font)
        except tk.TclError:
            pass
        for leader, row in self.rows.items():
            row.portrait = self._portrait_for(leader)
            try:
                self.canvas.itemconfigure(row.items["portrait"], image=row.portrait if row.portrait is not None else "")
            except tk.TclError:
                pass
            self._configure_row_fonts(row)
            row.type_image = None
            self._refresh_type_icon(row)
        self._last_layout_width = 0
        self._layout()

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.container.configure(bg=theme["card_bg"], highlightbackground=theme["card_border"])
            self.header.configure(bg=theme["heading"])
            self.body.configure(bg=theme["card_bg"])
            self.canvas.configure(bg=theme["card_bg"])
            self.scrollbar.configure(
                bg=theme["heading"],
                troughcolor=theme["panel_dark"],
                activebackground=theme["selected"],
                highlightthickness=0,
                bd=0,
            )
            header_font = ("Segoe UI Semibold", max(8, int(round(9 * self.factor))))
            for item in self._header_items:
                self.header.itemconfigure(item, fill=theme["text"], font=header_font)
        except tk.TclError:
            pass
        for row in self.rows.values():
            self._apply_row_style(row)


def install_dashboard_gym_list(app):
    shell = getattr(app, "_dashboard_shell", None)
    if shell is None:
        return None
    app._dashboard_gym_list = DashboardGymList(app, shell)
    return app._dashboard_gym_list
