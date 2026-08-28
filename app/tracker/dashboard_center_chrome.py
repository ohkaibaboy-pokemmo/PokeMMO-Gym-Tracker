import re
import tkinter as tk


_PROGRESS_RE = re.compile(
    r"Ready\s+(?P<ready>\d+)/(?P<total>\d+)\s+•\s+"
    r"Waiting\s+(?P<waiting>\d+)\s+•\s+"
    r"Cooldown\s+(?P<cooldown>\d+)\s+•\s+"
    r"Unknown\s+(?P<unknown>\d+)",
    re.IGNORECASE,
)


class DashboardCenterChrome:
    """Add route context above the Full-view Gym Route.

    v0.6 intentionally exposes no manual state-mutation controls. Cooldowns and
    five-rule progress are derived from PokeMMO log evidence, with replay available
    when live ingestion misses a historical record.
    """

    def __init__(self, app):
        self.app = app
        self.gym_list = getattr(app, "_dashboard_gym_list", None)
        self.shell = getattr(app, "_dashboard_shell", None)
        if self.gym_list is None or self.shell is None:
            raise RuntimeError("Dashboard gym list must exist before centre chrome")

        self.route_context_var = tk.StringVar(master=app, value="All gyms")
        self.next_context_var = tk.StringVar(master=app, value="")

        self._build_route_bar()
        self._hide_legacy_manual_strip()
        self._wrap_gym_list()

        app.theme_var.trace_add("write", lambda *_args: app.after_idle(self.apply_theme))
        self.refresh_context()
        self.apply_theme()
        app._dashboard_center_chrome = self

    def _build_route_bar(self):
        container = self.gym_list.container
        self.route_bar = tk.Frame(container, bd=0)
        self.route_bar.pack(fill="x", before=self.gym_list.header)

        self.route_left = tk.Frame(self.route_bar, bd=0)
        self.route_left.pack(side="left", fill="x", expand=True, padx=12, pady=(8, 7))
        self.route_title = tk.Label(
            self.route_left,
            text="GYM ROUTE",
            font=("Segoe UI Semibold", 8),
            anchor="w",
        )
        self.route_title.pack(side="left")
        self.route_context = tk.Label(
            self.route_left,
            textvariable=self.route_context_var,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.route_context.pack(side="left", padx=(10, 0))

        self.next_context = tk.Label(
            self.route_bar,
            textvariable=self.next_context_var,
            font=("Segoe UI Semibold", 8),
            anchor="e",
        )
        self.next_context.pack(side="right", padx=12, pady=(8, 7))

        self.route_divider = tk.Frame(container, height=1, bd=0)
        self.route_divider.pack(fill="x", before=self.gym_list.header)
        self.route_divider.pack_propagate(False)

    def _hide_legacy_manual_strip(self):
        # The old base UI still constructs a legacy manual strip before the v0.6
        # dashboard replaces that presentation. Keep it permanently hidden.
        legacy = getattr(self.shell, "manual_frame", None)
        if legacy is None:
            return
        try:
            legacy.pack_forget()
        except tk.TclError:
            pass

    def _wrap_gym_list(self):
        original_refresh = self.gym_list.refresh_from_model

        def refresh_with_context(*args, **kwargs):
            result = original_refresh(*args, **kwargs)
            self.refresh_context()
            return result

        self.gym_list.refresh_from_model = refresh_with_context

    def _progress(self):
        match = _PROGRESS_RE.search(str(self.app.progress_var.get() or ""))
        if not match:
            return {"ready": "0", "waiting": "0", "cooldown": "0", "unknown": "0", "total": "0"}
        return match.groupdict()

    def _next_leader(self):
        for leader in self.gym_list.order:
            row = self.gym_list.rows.get(leader)
            if row is not None and row.is_next:
                return leader
        return None

    def refresh_context(self):
        progress = self._progress()
        route_name = str(self.app.route_var.get() or "All gyms")
        visible = len(self.gym_list.order)
        if visible == int(progress.get("total", 0) or 0):
            count_text = f"{visible} gyms"
        else:
            count_text = f"{visible} visible"
        self.route_context_var.set(f"{route_name}  •  {count_text}")

        next_leader = self._next_leader()
        if next_leader:
            try:
                values = tuple(self.app.tree.item(next_leader, "values"))
                gym = values[2] if len(values) > 2 else ""
            except tk.TclError:
                gym = ""
            self.next_context_var.set(
                f"NEXT  {gym} — {next_leader}" if gym else f"NEXT  {next_leader}"
            )
        else:
            self.next_context_var.set("")

    def apply_scale(self, factor=1.0):
        factor = max(0.85, float(factor or 1.0))
        title_size = max(7, int(round(8 * factor)))
        context_size = max(7, int(round(8 * factor)))
        try:
            self.route_title.configure(font=("Segoe UI Semibold", title_size))
            self.route_context.configure(font=("Segoe UI", context_size))
            self.next_context.configure(font=("Segoe UI Semibold", context_size))
        except tk.TclError:
            pass

    def apply_theme(self):
        theme = self.app.theme()
        try:
            self.route_bar.configure(bg=theme["card_bg"])
            self.route_left.configure(bg=theme["card_bg"])
            self.route_title.configure(bg=theme["card_bg"], fg=theme["muted"])
            self.route_context.configure(bg=theme["card_bg"], fg=theme["text"])
            self.next_context.configure(
                bg=theme["card_bg"],
                fg=theme["selection_border"],
            )
            self.route_divider.configure(bg=theme["card_border"])
        except tk.TclError:
            pass


def install_dashboard_center_chrome(app):
    if getattr(app, "_dashboard_gym_list", None) is None:
        return None
    app._dashboard_center_chrome = DashboardCenterChrome(app)
    return app._dashboard_center_chrome
