"""v0.6 Compact visual hierarchy.

Keep the proven CompactWindow behaviour intact while making the route queue the
primary work surface. Compact status and run earnings are intentionally reduced
to a single route-header summary so the gym list owns virtually all available
vertical space.
"""

import tkinter as tk


def install_compact_priority(compact_window_cls):
    original_init = compact_window_cls.__init__
    if getattr(original_init, "_route_queue_priority", False):
        return compact_window_cls

    original_apply_dashboard_theme = compact_window_cls._apply_dashboard_theme

    def prioritised_theme(self):
        original_apply_dashboard_theme(self)
        try:
            theme = self.app.theme()
            if hasattr(self, "compact_status_summary"):
                self.compact_status_summary.configure(
                    bg=theme["card_bg"],
                    fg=theme["text"],
                )
            if hasattr(self, "compact_summary_separator"):
                self.compact_summary_separator.configure(
                    bg=theme["card_bg"],
                    fg=theme["muted"],
                )
            if hasattr(self, "compact_earnings_summary"):
                self.compact_earnings_summary.configure(
                    bg=theme["card_bg"],
                    fg=theme["money"],
                )
        except Exception:
            pass

    def prioritised_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        try:
            # CompactWindow builds Filter -> Status -> Route. The dedicated
            # status card is deliberately retired in v0.6 Compact: route queue
            # is the work surface, while glanceable status/earnings live in its
            # header instead.
            self.route_card.pack_forget()
            self.status_card.pack_forget()
            self.route_card.pack(fill="both", expand=True)

            self.compact_status_summary_var = tk.StringVar(master=self)
            theme = self.app.theme()

            self.compact_status_summary = tk.Label(
                self.route_header,
                textvariable=self.compact_status_summary_var,
                font=("Segoe UI Semibold", 8),
                anchor="e",
                bg=theme["card_bg"],
                fg=theme["text"],
            )
            self.compact_summary_separator = tk.Label(
                self.route_header,
                text=" · ",
                font=("Segoe UI Semibold", 8),
                anchor="center",
                bg=theme["card_bg"],
                fg=theme["muted"],
            )
            self.compact_earnings_summary = tk.Label(
                self.route_header,
                textvariable=self.run_money_var,
                font=("Segoe UI Semibold", 8),
                anchor="e",
                bg=theme["card_bg"],
                fg=theme["money"],
            )

            # route_name was already packed at the far right. The separator now
            # carries its own single-space padding, matching the separators inside
            # the status text so Ready / CD / earnings read as evenly spaced items.
            self.compact_earnings_summary.pack(
                side="right",
                padx=(0, self._scale(7)),
            )
            self.compact_summary_separator.pack(side="right", padx=0)
            self.compact_status_summary.pack(
                side="right",
                padx=(self._scale(4), 0),
            )

            def update_header_summary(*_args):
                try:
                    ready = int(self.ready_var.get() or 0)
                except (TypeError, ValueError):
                    ready = 0
                try:
                    waiting = int(self.waiting_var.get() or 0)
                except (TypeError, ValueError):
                    waiting = 0
                try:
                    cooldown = int(self.cooldown_var.get() or 0)
                except (TypeError, ValueError):
                    cooldown = 0

                parts = [f"{ready} Ready"]
                if waiting:
                    parts.append(f"{waiting} Wait")
                parts.append(f"{cooldown} CD")
                self.compact_status_summary_var.set(" · ".join(parts))

            for variable in (self.ready_var, self.waiting_var, self.cooldown_var):
                variable.trace_add("write", update_header_summary)
            update_header_summary()
            self._apply_dashboard_theme()
        except Exception:
            # Presentation must never stop the tracker from opening Compact.
            pass

    prioritised_init._route_queue_priority = True
    prioritised_theme._route_queue_priority_theme = True
    compact_window_cls.__init__ = prioritised_init
    compact_window_cls._apply_dashboard_theme = prioritised_theme
    return compact_window_cls
