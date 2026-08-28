import copy
import html
import json
import re
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .constants import APP_NAME, APP_VERSION, GYMS, REQUIRED_OTHER_TRAINERS


EXPORT_FORMAT = "PokeMMO Gym Tracker character export"
EXPORT_VERSION = 1
ALL_CHARACTERS = "All characters"


def _safe_filename(value):
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip())
    return text.strip("-._") or "Character"


def selected_character_names(state, selection):
    characters = state.get("characters", {})
    if selection == ALL_CHARACTERS:
        return sorted(characters)
    return [selection] if selection in characters else []


def _processed_event_player(event_id):
    try:
        return str(event_id).split("|", 2)[1]
    except (AttributeError, IndexError):
        return ""


def build_character_export(state, selection, exported_at=None):
    """Build a portable character-only backup payload.

    Global UI preferences, custom routes, log-folder paths and market/charm
    settings are deliberately excluded. Selecting All characters exports every
    tracked character; otherwise only the selected character is included.
    """
    names = selected_character_names(state, selection)
    characters = state.get("characters", {})
    selected = {name: copy.deepcopy(characters[name]) for name in names}
    name_set = set(names)

    processed_events = [
        event_id
        for event_id in state.get("processed_events", [])
        if _processed_event_player(event_id) in name_set
    ]

    when = exported_at or datetime.now()
    return {
        "format": EXPORT_FORMAT,
        "export_version": EXPORT_VERSION,
        "app_version": APP_VERSION,
        "exported_at": when.isoformat(timespec="seconds"),
        "scope": "all" if selection == ALL_CHARACTERS else "character",
        "selected_character": selection,
        "characters": selected,
        "processed_events": processed_events,
    }


def default_export_filename(selection, exported_at=None):
    when = exported_at or datetime.now()
    scope = "All-Characters" if selection == ALL_CHARACTERS else _safe_filename(selection)
    return f"PokeMMO-Gym-Tracker-{scope}-{when:%Y-%m-%d}.json"


def default_report_filename(selection, exported_at=None):
    when = exported_at or datetime.now()
    scope = "All-Characters" if selection == ALL_CHARACTERS else _safe_filename(selection)
    return f"PokeMMO-Gym-Tracker-{scope}-{when:%Y-%m-%d}.html"


def _money(value):
    try:
        return f"${int(value):,}"
    except (TypeError, ValueError):
        return "$0"


def _format_datetime(value):
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %b %Y · %H:%M:%S")
    except (TypeError, ValueError):
        return "—"


def _gym_report_row(record, now):
    if not record:
        return {
            "status": "UNKNOWN",
            "cooldown": "—",
            "rule": "—",
            "last": "—",
            "payout": "—",
        }

    other = min(REQUIRED_OTHER_TRAINERS, max(0, int(record.get("other_trainers", 0) or 0)))
    last = _format_datetime(record.get("defeated_at"))
    payout = _money(record.get("payout")) if record.get("payout") is not None else "—"

    if record.get("manual_ready"):
        return {
            "status": "READY",
            "cooldown": "Ready",
            "rule": f"{REQUIRED_OTHER_TRAINERS}/{REQUIRED_OTHER_TRAINERS}",
            "last": last,
            "payout": payout,
        }

    try:
        ready_at = datetime.fromisoformat(str(record.get("ready_at", "")))
    except (TypeError, ValueError):
        ready_at = now

    remaining = ready_at - now
    if remaining.total_seconds() > 0:
        seconds = max(0, int(remaining.total_seconds()))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        status = "COOLDOWN"
        cooldown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    elif other < REQUIRED_OTHER_TRAINERS:
        needed = REQUIRED_OTHER_TRAINERS - other
        status = "WAITING"
        cooldown = f"Need {needed} battle" + ("s" if needed != 1 else "")
    else:
        status = "READY"
        cooldown = "Ready"

    return {
        "status": status,
        "cooldown": cooldown,
        "rule": f"{other}/{REQUIRED_OTHER_TRAINERS}",
        "last": last,
        "payout": payout,
    }


def _current_run_events(character):
    earnings = character.get("earnings", {}) if isinstance(character, dict) else {}
    started = earnings.get("run_started_at")
    if not started:
        return []
    try:
        started_at = datetime.fromisoformat(str(started))
    except (TypeError, ValueError):
        return []

    result = []
    for event in earnings.get("events", []):
        try:
            event_at = datetime.fromisoformat(str(event.get("ts", "")))
        except (AttributeError, TypeError, ValueError):
            continue
        if event_at >= started_at:
            result.append(event)
    return result


def _character_report_data(name, character, now):
    gyms = character.get("gyms", {}) if isinstance(character, dict) else {}
    rows = []
    counts = {"READY": 0, "WAITING": 0, "COOLDOWN": 0, "UNKNOWN": 0}
    for region, gym, leader in GYMS:
        values = _gym_report_row(gyms.get(leader), now)
        counts[values["status"]] += 1
        rows.append({
            "region": region,
            "gym": gym,
            "leader": leader,
            **values,
        })

    events = _current_run_events(character)
    run_total = sum(int(event.get("amount", 0) or 0) for event in events)
    gym_total = sum(
        int(event.get("amount", 0) or 0)
        for event in events
        if event.get("is_gym")
    )
    other_total = run_total - gym_total

    return {
        "name": name,
        "rows": rows,
        "counts": counts,
        "run_started": _format_datetime(character.get("earnings", {}).get("run_started_at")),
        "run_total": run_total,
        "gym_total": gym_total,
        "other_total": other_total,
        "payout_events": len(events),
    }


def _e(value):
    return html.escape(str(value), quote=True)


def build_html_report(state, selection, exported_at=None):
    """Return a standalone, browser-readable report for the selected scope."""
    when = exported_at or datetime.now()
    names = selected_character_names(state, selection)
    characters = state.get("characters", {})
    reports = [
        _character_report_data(name, characters.get(name, {}), when)
        for name in names
    ]

    nav = "".join(
        f'<a class="nav-pill" href="#char-{index}">{_e(report["name"])}</a>'
        for index, report in enumerate(reports, 1)
    )

    sections = []
    for index, report in enumerate(reports, 1):
        counts = report["counts"]
        cards = "".join(
            f'<div class="metric {key.lower()}"><span>{key}</span><strong>{counts[key]}</strong></div>'
            for key in ("READY", "WAITING", "COOLDOWN", "UNKNOWN")
        )
        cards += (
            '<div class="metric earnings"><span>RUN EARNINGS</span>'
            f'<strong>{_money(report["run_total"])}</strong></div>'
        )

        body_rows = []
        for position, row in enumerate(report["rows"], 1):
            status = row["status"].lower()
            body_rows.append(
                "<tr>"
                f"<td class=\"num\">{position:02d}</td>"
                f"<td>{_e(row['leader'])}</td>"
                f"<td>{_e(row['gym'])}</td>"
                f"<td>{_e(row['region'])}</td>"
                f"<td>{_e(row['rule'])}</td>"
                f"<td class=\"mono\">{_e(row['cooldown'])}</td>"
                f"<td>{_e(row['last'])}</td>"
                f"<td><span class=\"status {status}\">{_e(row['status'])}</span></td>"
                f"<td class=\"money\">{_e(row['payout'])}</td>"
                "</tr>"
            )

        sections.append(
            f'<section class="character" id="char-{index}">'
            '<div class="section-head">'
            f'<div><p class="eyebrow">CHARACTER</p><h2>{_e(report["name"])}</h2></div>'
            f'<div class="run-meta"><span>Run started</span><strong>{_e(report["run_started"])}</strong></div>'
            '</div>'
            f'<div class="metrics">{cards}</div>'
            '<div class="run-breakdown">'
            f'<span>Gym payouts <strong>{_money(report["gym_total"])}</strong></span>'
            f'<span>Other payouts <strong>{_money(report["other_total"])}</strong></span>'
            f'<span>Payout events <strong>{report["payout_events"]}</strong></span>'
            '</div>'
            '<div class="table-wrap"><table><thead><tr>'
            '<th>#</th><th>Leader</th><th>Gym</th><th>Region</th><th>5-rule</th>'
            '<th>Cooldown</th><th>Last Defeated</th><th>Status</th><th>Payout</th>'
            '</tr></thead><tbody>' + "".join(body_rows) + '</tbody></table></div>'
            '</section>'
        )

    title_scope = "All Characters" if selection == ALL_CHARACTERS else selection
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PokeMMO Gym Tracker · {_e(title_scope)}</title>
<style>
:root {{ color-scheme: dark; --bg:#10161b; --panel:#141c22; --panel2:#171f25; --border:#2b3943; --text:#eef2f4; --muted:#9ba7ae; --ready:#83c56a; --waiting:#e0b34e; --cooldown:#78a9d8; --unknown:#a986c7; --money:#e2c15d; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text); font:14px/1.45 "Segoe UI",Arial,sans-serif; }}
main {{ width:min(1500px,96vw); margin:0 auto; padding:28px 0 44px; }}
.hero {{ display:flex; gap:20px; justify-content:space-between; align-items:flex-end; margin-bottom:18px; }}
h1,h2,p {{ margin:0; }} h1 {{ font-size:24px; }} h2 {{ font-size:20px; }} .eyebrow {{ color:var(--muted); font-size:11px; font-weight:700; letter-spacing:.12em; }}
.exported {{ color:var(--muted); text-align:right; }} .nav {{ display:flex; flex-wrap:wrap; gap:8px; margin:0 0 18px; }} .nav-pill {{ color:var(--text); text-decoration:none; background:var(--panel2); border:1px solid var(--border); border-radius:999px; padding:6px 10px; }}
.character {{ background:var(--panel); border:1px solid var(--border); border-radius:9px; margin-bottom:22px; overflow:hidden; }}
.section-head {{ display:flex; justify-content:space-between; align-items:flex-end; padding:16px 18px 10px; }} .run-meta {{ color:var(--muted); text-align:right; }} .run-meta span,.run-meta strong {{ display:block; }} .run-meta strong {{ color:var(--text); }}
.metrics {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:8px; padding:0 18px 12px; }} .metric {{ background:var(--panel2); border:1px solid var(--border); border-radius:7px; padding:9px 11px; }} .metric span {{ display:block; color:var(--muted); font-size:10px; font-weight:700; letter-spacing:.08em; }} .metric strong {{ display:block; margin-top:2px; font-size:19px; }} .metric.ready strong {{ color:var(--ready); }} .metric.waiting strong {{ color:var(--waiting); }} .metric.cooldown strong {{ color:var(--cooldown); }} .metric.unknown strong {{ color:var(--unknown); }} .metric.earnings strong {{ color:var(--money); }}
.run-breakdown {{ display:flex; flex-wrap:wrap; gap:20px; padding:0 18px 12px; color:var(--muted); }} .run-breakdown strong {{ color:var(--text); margin-left:5px; }}
.table-wrap {{ overflow:auto; border-top:1px solid var(--border); }} table {{ width:100%; border-collapse:collapse; min-width:1050px; }} th {{ background:#202930; color:var(--muted); font-size:11px; letter-spacing:.05em; text-align:left; padding:9px 10px; position:sticky; top:0; }} td {{ padding:8px 10px; border-top:1px solid #202b33; white-space:nowrap; }} tbody tr:hover {{ background:#182229; }} .num {{ color:var(--muted); }} .mono {{ font-family:Consolas,"SFMono-Regular",monospace; }} .money {{ color:var(--money); font-weight:600; }}
.status {{ display:inline-block; min-width:78px; text-align:center; border-radius:999px; padding:3px 8px; font-size:11px; font-weight:700; }} .status.ready {{ color:var(--ready); background:#16231a; }} .status.waiting {{ color:var(--waiting); background:#241f14; }} .status.cooldown {{ color:var(--cooldown); background:#15202a; }} .status.unknown {{ color:var(--unknown); background:#201a27; }}
.footer {{ color:var(--muted); font-size:12px; text-align:center; margin-top:4px; }} @media (max-width:800px) {{ .metrics {{ grid-template-columns:repeat(2,1fr); }} .hero,.section-head {{ align-items:flex-start; flex-direction:column; }} .exported,.run-meta {{ text-align:left; }} }}
</style>
</head>
<body><main>
<div class="hero"><div><p class="eyebrow">POKEMMO GYM TRACKER</p><h1>{_e(title_scope)} Report</h1></div><div class="exported">Exported {_e(when.strftime('%d %b %Y · %H:%M:%S'))}<br>Tracker { _e(APP_VERSION) }</div></div>
<div class="nav">{nav}</div>
{''.join(sections)}
<p class="footer">Standalone report generated locally by PokeMMO Gym Tracker. No network access is required.</p>
</main></body></html>'''


class ExportChoiceDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.result = None
        self.title("Export")
        self.geometry("470x205")
        self.resizable(False, False)
        self.transient(app)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=18, pady=16)
        tk.Label(body, text="Choose export format", font=("Segoe UI Semibold", 14), anchor="w").pack(fill="x")
        tk.Label(
            body,
            text="The current Character selection controls which character data is included.",
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", pady=(2, 13))

        report = ttk.Button(body, text="Readable Report (.html)", command=lambda: self._choose("html"))
        report.pack(fill="x")
        tk.Label(
            body,
            text="Best for viewing or sharing · opens in any browser",
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", padx=8, pady=(2, 9))

        backup = ttk.Button(body, text="Tracker Backup (.json)", command=lambda: self._choose("json"))
        backup.pack(fill="x")
        tk.Label(
            body,
            text="Full-fidelity character data for backup/import use",
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", padx=8, pady=(2, 0))

        self.update_idletasks()
        try:
            x = app.winfo_rootx() + max(0, (app.winfo_width() - self.winfo_width()) // 2)
            y = app.winfo_rooty() + max(0, (app.winfo_height() - self.winfo_height()) // 2)
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass
        app.apply_theme()
        self.grab_set()
        report.focus_set()

    def _choose(self, value):
        self.result = value
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class CharacterExportController:
    def __init__(self, app):
        self.app = app
        self.button = None
        self._install_button()

    def _actions_host(self):
        shell = getattr(self.app, "_dashboard_shell", None)
        panel = getattr(shell, "control_panel", None)
        if panel is None:
            return None
        for child in panel.winfo_children():
            if not isinstance(child, tk.Frame):
                continue
            for widget in child.winfo_children():
                try:
                    if isinstance(widget, ttk.Button) and widget.cget("text") == "Manage Routes":
                        return child
                except tk.TclError:
                    pass
        return None

    def _install_button(self):
        host = self._actions_host()
        if host is None:
            return
        self.button = ttk.Button(host, text="Export…", command=self.export)
        self.button.pack(side="left", padx=(8, 0))

    def _choose_format(self):
        dialog = ExportChoiceDialog(self.app)
        self.app.wait_window(dialog)
        return dialog.result

    def export(self):
        selection = str(self.app.character_var.get() or ALL_CHARACTERS)
        names = selected_character_names(self.app.state_data, selection)
        if not names:
            messagebox.showinfo(
                APP_NAME,
                "There is no tracked character data to export for this selection.",
                parent=self.app,
            )
            return

        export_format = self._choose_format()
        if export_format not in {"html", "json"}:
            return

        is_report = export_format == "html"
        path = filedialog.asksaveasfilename(
            parent=self.app,
            title="Export readable character report" if is_report else "Export tracked character backup",
            defaultextension=".html" if is_report else ".json",
            initialfile=(
                default_report_filename(selection)
                if is_report
                else default_export_filename(selection)
            ),
            filetypes=(
                (("HTML report", "*.html"), ("All files", "*.*"))
                if is_report
                else (("JSON backup", "*.json"), ("All files", "*.*"))
            ),
        )
        if not path:
            return

        try:
            if is_report:
                contents = build_html_report(self.app.state_data, selection)
            else:
                payload = build_character_export(self.app.state_data, selection)
                contents = json.dumps(payload, indent=2, ensure_ascii=False)
            Path(path).write_text(contents, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror(
                APP_NAME,
                f"Could not export character data:\n{exc}",
                parent=self.app,
            )
            return

        label = "all tracked characters" if selection == ALL_CHARACTERS else selection
        kind = "report" if is_report else "backup"
        messagebox.showinfo(
            APP_NAME,
            f"Exported {label} {kind} to:\n{path}",
            parent=self.app,
        )


def install_character_export(app):
    app._character_export_controller = CharacterExportController(app)
    return app._character_export_controller
