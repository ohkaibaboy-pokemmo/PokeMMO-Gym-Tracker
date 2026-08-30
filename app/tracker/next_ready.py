"""Pure helpers for the Full dashboard's NEXT READY summary card."""

from datetime import datetime

from .core import canonical_leader

ALL_CHARACTERS = "All characters"


def _parse_iso(value):
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def next_ready_gym(state, selected_character=ALL_CHARACTERS, now=None):
    """Return the gym whose active cooldown ends next for the selected scope.

    NEXT READY is intentionally a cooldown-timing card. While any gym is still on
    cooldown, it shows the earliest future ``ready_at`` timestamp regardless of
    five-rule progress. Only when no active cooldown remains does the card report
    READY.

    ``All characters`` searches every character. A concrete character name scopes
    the calculation to that character only. Route/region/display filters are
    intentionally ignored so the card always reflects the real next cooldown end
    for the selected account scope.
    """
    now = now or datetime.now()
    characters = (state or {}).get("characters", {})
    if not isinstance(characters, dict):
        return {"ready_now": True, "leader": None, "character": None, "ready_at": None}

    if selected_character == ALL_CHARACTERS:
        names = list(characters.keys())
    else:
        names = [selected_character] if selected_character in characters else []

    candidates = []
    for character in names:
        char = characters.get(character) or {}
        gyms = char.get("gyms", {}) if isinstance(char, dict) else {}
        if not isinstance(gyms, dict):
            continue
        for leader, record in gyms.items():
            if not isinstance(record, dict) or record.get("manual_ready"):
                continue

            ready_at = _parse_iso(record.get("ready_at"))
            if ready_at is None or ready_at <= now:
                continue

            candidates.append((ready_at, character, canonical_leader(leader)))

    if not candidates:
        return {"ready_now": True, "leader": None, "character": None, "ready_at": None}

    ready_at, character, leader = min(candidates, key=lambda item: item[0])
    return {
        "character": character,
        "leader": leader,
        "ready_at": ready_at,
        "ready_now": False,
    }


def format_next_ready_time(result):
    """Return the next cooldown-end date/time, or READY when none are active."""
    if not result or result.get("ready_now"):
        return "READY"
    ready_at = result.get("ready_at")
    if not isinstance(ready_at, datetime):
        return "READY"
    return f"{ready_at.day} {ready_at.strftime('%b')} · {ready_at.strftime('%H:%M')}"


def format_next_ready_detail(result, selected_character=ALL_CHARACTERS, max_chars=24):
    """Return the leader for the next cooldown, plus character in all-account view."""
    if not result or result.get("ready_now"):
        return "No active cooldowns"
    leader = str(result.get("leader") or "Unknown")
    if selected_character == ALL_CHARACTERS:
        detail = f"{leader} · {result.get('character') or 'Unknown'}"
    else:
        detail = leader
    max_chars = max(8, int(max_chars or 24))
    if len(detail) > max_chars:
        return detail[: max_chars - 1].rstrip() + "…"
    return detail
