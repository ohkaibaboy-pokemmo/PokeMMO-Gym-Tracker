import re
from datetime import datetime

from .constants import GYMS, LEADER_ALIASES


TIMESTAMP_FORMATS = (
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%y %I:%M:%S %p",
    "%m/%d/%Y %I:%M:%S %p",
)


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9&]+", "", value.lower())


def canonical_leader(name: str) -> str:
    key = norm(name)
    if key in LEADER_ALIASES:
        return LEADER_ALIASES[key]
    for _, _, leader in GYMS:
        if norm(leader) == key:
            return leader
    return name.strip()


def gym_for_leader(leader: str):
    canonical = canonical_leader(leader)
    for region, gym, name in GYMS:
        if name == canonical:
            return region, gym, name
    return None


def opponent_is_leader(opponent: str):
    value = opponent.strip()
    if value.startswith("Leader "):
        return True, canonical_leader(value[len("Leader "):])
    if value.startswith("Leaders "):
        return True, canonical_leader(value[len("Leaders "):])
    return False, ""


def parse_ts(value: str) -> datetime:
    """Parse timestamp formats emitted by PokeMMO on supported Windows locales.

    Existing UK/live validation uses day-first 24-hour timestamps with a four-digit
    year. External US Windows validation exposed month-first 12-hour timestamps
    with AM/PM and a two-digit year. Keep the accepted UK grammar while accepting
    the observed US variants as the same canonical datetime input.
    """
    value = str(value).strip()
    last_error = None
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError as exc:
            last_error = exc
    raise last_error or ValueError(f"Unsupported timestamp: {value}")


def gym_label(region: str, gym: str, leader: str) -> str:
    return f"{region} — {gym} — {leader}"
