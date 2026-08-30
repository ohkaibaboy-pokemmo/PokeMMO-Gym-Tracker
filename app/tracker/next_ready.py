"""Pure helpers for the Full dashboard's NEXT READY summary card."""

from datetime import datetime

from .constants import REQUIRED_OTHER_TRAINERS
from .core import canonical_leader

ALL_CHARACTERS = "All characters"


def _parse_iso(value):
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _trainer_count(record):
    try:
        return int(record.get("other_trainers", 0))
    except (TypeError, ValueError, AttributeError):
        return 0


def next_ready_gym(state, selected_character=ALL_CHARACTERS, now=None):
    """Return the next predictably rerunnable gym for the selected scope.

    A gym is predictable only after the 5-other-trainer requirement has reached
    5/5. Its ready time is then the stored 18-hour ``ready_at`` timestamp. Gyms
    whose timer already expired are returned as READY NOW. Legacy ``manual_ready``
    state is honoured so this summary never contradicts the existing row status.

    ``All characters`` searches every character. A concrete character name scopes
    the calculation to that character only. Route/region/display filters are
    intentionally ignored: this card answers the global operational question,
    "what can I rerun next?"
    """
    now = now or datetime.now()
    characters = (state or {}).get("characters", {})
    if not isinstance(characters, dict):
        return None

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
            if not isinstance(record, dict):
                continue

            ready_at = _parse_iso(record.get("ready_at"))
            if record.get("manual_ready"):
                # Keep legacy/manual-ready state aligned with the table: it is
                # already ready irrespective of old counter/timestamp contents.
                candidate_time = ready_at or now
                candidates.append((candidate_time, character, canonical_leader(leader), True))
                continue

            if _trainer_count(record) < REQUIRED_OTHER_TRAINERS or ready_at is None:
                continue

            candidates.append((ready_at, character, canonical_leader(leader), ready_at <= now))

    if not candidates:
        return None

    # If anything is already rerunnable, surface the one whose ready timestamp is
    # oldest first. Otherwise surface the nearest future ready timestamp.
    ready_now = [candidate for candidate in candidates if candidate[3]]
    pool = ready_now or candidates
    ready_at, character, leader, is_ready_now = min(pool, key=lambda item: item[0])
    return {
        "character": character,
        "leader": leader,
        "ready_at": ready_at,
        "ready_now": bool(is_ready_now),
    }


def format_next_ready_time(result):
    """Return a compact local date/time label for the summary card."""
    if not result:
        return "—"
    if result.get("ready_now"):
        return "READY NOW"
    ready_at = result.get("ready_at")
    if not isinstance(ready_at, datetime):
        return "—"
    return f"{ready_at.day} {ready_at.strftime('%b')} · {ready_at.strftime('%H:%M')}"


def format_next_ready_detail(result, selected_character=ALL_CHARACTERS, max_chars=24):
    """Return the leader, plus character when the card is showing all accounts."""
    if not result:
        return "Complete 5-rule first"
    leader = str(result.get("leader") or "Unknown")
    if selected_character == ALL_CHARACTERS:
        detail = f"{leader} · {result.get('character') or 'Unknown'}"
    else:
        detail = leader
    max_chars = max(8, int(max_chars or 24))
    if len(detail) > max_chars:
        return detail[: max_chars - 1].rstrip() + "…"
    return detail
