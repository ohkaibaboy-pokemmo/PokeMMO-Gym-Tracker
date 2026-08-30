import json
import os
from pathlib import Path

from .constants import APP_VERSION, EXCLUDED_5_RULE_TRAINERS, VERIFIED_REMATCH_TRAINERS
from .core import canonical_leader
from .earnings import DEFAULT_EARNINGS_SETTINGS, ensure_earnings_state
from .trainers import learn_repeat_rematches, merge_verified_catalogue, recalculate_5_rule_counts


def state_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        path = Path(base) / "PokeMMOGymCooldownTracker"
    else:
        path = Path.home() / ".pokemmo_gym_cooldown_tracker"
    path.mkdir(parents=True, exist_ok=True)
    return path


STATE_FILE = state_dir() / "state.json"


def default_state():
    return {
        "version": APP_VERSION,
        "log_folder": "",
        "characters": {},
        "processed_events": [],
        # Legacy catalogue retained so existing state remains readable, but v0.6
        # no longer requires membership here before a trainer counts.
        "confirmed_normal_rematch_trainers": VERIFIED_REMATCH_TRAINERS[:],
        "learned_rematch_trainers": [],
        # New opt-out model: trainer wins qualify unless explicitly listed here.
        "excluded_5_rule_trainers": EXCLUDED_5_RULE_TRAINERS[:],
        "custom_routes": {},
        "route_selection": "All gyms",
        "region_filter": "All",
        "selected_character": "All characters",
        "display_filter": "Remaining",
        "hide_unknown": False,
        "compact_geometry": "560x450",
        "compact_mode": False,
        "theme": "Dark",
        "ui_scale": "1.0×",
        "window": {"geometry": "1100x650"},
        "earnings_settings": dict(DEFAULT_EARNINGS_SETTINGS),
    }


def _migrate_state(state):
    state.setdefault("characters", {})
    state.setdefault("processed_events", [])
    state.setdefault("confirmed_normal_rematch_trainers", [])
    state.setdefault("learned_rematch_trainers", [])
    state.setdefault("excluded_5_rule_trainers", EXCLUDED_5_RULE_TRAINERS[:])
    state.setdefault("custom_routes", {})
    state.setdefault("route_selection", "All gyms")
    state.setdefault("region_filter", "All")
    state.setdefault("selected_character", "All characters")
    state.setdefault("display_filter", "Remaining")
    state.setdefault("hide_unknown", False)
    state.setdefault("compact_geometry", "560x450")
    state.setdefault("theme", "Dark")
    state.setdefault("ui_scale", "1.0×")
    state.setdefault("window", {"geometry": "1100x650"})

    # Compact is intentionally a per-session choice: every fresh launch opens full view.
    state["compact_mode"] = False

    # Canonicalize historical gym keys and stored gym payout labels whenever a
    # PokeMMO log uses a shorter/alternate leader name. This repairs old state as
    # aliases are learned (for example "Wake" -> "Crasher Wake") rather than only
    # fixing newly detected battles.
    for char in state.get("characters", {}).values():
        gyms = char.setdefault("gyms", {})
        for leader in list(gyms):
            canonical = canonical_leader(leader)
            if canonical == leader:
                continue
            alias_record = gyms.pop(leader)
            canonical_record = gyms.get(canonical)
            if canonical_record is None:
                gyms[canonical] = alias_record
            elif str(alias_record.get("defeated_at") or "") > str(canonical_record.get("defeated_at") or ""):
                gyms[canonical] = alias_record

        for event in char.get("earnings", {}).get("events", []):
            if event.get("is_gym") and event.get("leader"):
                event["leader"] = canonical_leader(event["leader"])

    for name, route in list(state.get("custom_routes", {}).items()):
        state["custom_routes"][name] = [canonical_leader(leader) for leader in route]

    ensure_earnings_state(state)
    merge_verified_catalogue(state)
    learn_repeat_rematches(state)

    # Rebuild counters on every load from the already recorded victories. This is
    # especially important when upgrading from the old conservative allow-list:
    # previously detected ordinary trainer wins are credited retroactively unless
    # the opponent is now explicitly excluded.
    recalculate_5_rule_counts(state)
    state["version"] = APP_VERSION
    return state


def load_state(path: Path = STATE_FILE):
    state = default_state()
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state.update(loaded)
        except Exception:
            pass
    state = _migrate_state(state)
    save_state(state, path)
    return state


def save_state(state, path: Path = STATE_FILE):
    ensure_earnings_state(state)
    state["version"] = APP_VERSION
    state["processed_events"] = state.get("processed_events", [])[-2000:]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(path)
