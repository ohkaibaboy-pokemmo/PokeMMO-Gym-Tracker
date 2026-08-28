import re
from datetime import datetime

from .constants import GYMS, LEADER_ALIASES


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
    return datetime.strptime(value, "%d/%m/%Y %H:%M:%S")


def gym_label(region: str, gym: str, leader: str) -> str:
    return f"{region} — {gym} — {leader}"
