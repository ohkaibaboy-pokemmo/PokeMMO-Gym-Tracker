from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from .core import canonical_leader, opponent_is_leader


# Local base rematch payouts used for route projections. These are deliberately
# embedded in the application: the tracker makes no runtime web/API requests.
GYM_BASE_PAYOUTS = {
    # Kanto
    "Brock": 8632,
    "Misty": 8736,
    "Lt. Surge": 8840,
    "Erika": 8944,
    "Koga": 9048,
    "Sabrina": 9152,
    "Blaine": 9256,
    # Johto
    "Falkner": 8632,
    "Bugsy": 8736,
    "Whitney": 8840,
    "Morty": 8944,
    "Chuck": 9048,
    "Jasmine": 9152,
    "Pryce": 9256,
    "Clair": 9360,
    # Hoenn
    "Roxanne": 8632,
    "Brawly": 8736,
    "Wattson": 8840,
    "Flannery": 8944,
    "Norman": 9048,
    "Winona": 9152,
    "Tate & Liza": 9256,
    "Juan": 9360,
    # Sinnoh
    "Roark": 8632,
    "Gardenia": 8736,
    "Fantina": 8840,
    "Maylene": 8944,
    "Crasher Wake": 9048,
    "Byron": 9152,
    "Candice": 9256,
    "Volkner": 9360,
    # Unova
    "Cilan": 8632,
    "Chili": 8632,
    "Cress": 8632,
    "Lenora": 8736,
    "Burgh": 8840,
    "Elesa": 8944,
    "Clay": 9048,
    "Skyla": 9152,
    "Brycen": 9256,
    "Iris": 9360,
}

CHARM_OPTIONS = (
    ("No charm", Decimal("1.0"), None),
    ("Amulet Coin", Decimal("1.5"), "amulet_price"),
    ("Riches Charm 75%", Decimal("1.75"), "riches_75_price"),
    ("Riches Charm 100%", Decimal("2.0"), "riches_100_price"),
)

DEFAULT_EARNINGS_SETTINGS = {
    "amulet_price": 0,
    "riches_75_price": 0,
    "riches_100_price": 0,
    "donator": False,
}


def format_yen(value):
    try:
        amount = int(value)
    except (TypeError, ValueError):
        amount = 0
    sign = "-" if amount < 0 else ""
    return f"{sign}¥{abs(amount):,}"


def parse_yen_input(value):
    text = str(value or "").replace("¥", "").replace("$", "").replace(",", "").strip()
    if not text:
        return 0
    try:
        return max(0, int(text))
    except ValueError:
        return 0


def _round_yen(value):
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def route_base_total(leaders):
    return sum(GYM_BASE_PAYOUTS.get(canonical_leader(leader), 0) for leader in (leaders or []))


def projection_rows(base_total, settings):
    """Return CharmCalc-style route projections using only local inputs.

    Donator applies a 5% multiplier to the selected base total, then the charm
    multiplier is applied and the manually entered charm cost is subtracted.
    """
    base = Decimal(int(base_total or 0))
    donator_multiplier = Decimal("1.05") if settings.get("donator") else Decimal("1.0")
    donor_base = base * donator_multiplier
    rows = []
    for name, multiplier, price_key in CHARM_OPTIONS:
        gross_decimal = donor_base * multiplier
        gross = _round_yen(gross_decimal)
        price = parse_yen_input(settings.get(price_key, 0)) if price_key else 0
        net = _round_yen(gross_decimal - Decimal(price))
        rows.append({
            "name": name,
            "gross": gross,
            "price": price,
            "net": net,
        })
    return rows


def ensure_earnings_state(state):
    settings = state.setdefault("earnings_settings", {})
    for key, value in DEFAULT_EARNINGS_SETTINGS.items():
        settings.setdefault(key, value)
    for char in state.setdefault("characters", {}).values():
        ensure_character_earnings(char)
    return state


def ensure_character_earnings(char):
    earnings = char.setdefault("earnings", {})
    earnings.setdefault("run_started_at", None)
    earnings.setdefault("events", [])
    return earnings


def payout_event_id(ts, player, opponent, amount):
    return f"{ts.isoformat()}|{player}|{opponent}|{int(amount)}"


def record_payout(state, ts, player, opponent, amount):
    """Store one payout linked to a confirmed victory.

    Returns the newly added event, or None when the exact payout was already
    present (for example after replaying the same chat log).
    """
    chars = state.setdefault("characters", {})
    char = chars.setdefault(player, {"gyms": {}})
    char.setdefault("gyms", {})
    earnings = ensure_character_earnings(char)

    amount = int(amount)
    event_id = payout_event_id(ts, player, opponent, amount)
    if any(event.get("id") == event_id for event in earnings.get("events", [])):
        return None

    is_gym, leader = opponent_is_leader(opponent)
    leader = canonical_leader(leader) if is_gym else None
    event = {
        "id": event_id,
        "ts": ts.isoformat(),
        "opponent": opponent,
        "amount": amount,
        "is_gym": bool(is_gym),
        "leader": leader,
    }
    earnings.setdefault("events", []).append(event)
    earnings["events"] = earnings["events"][-3000:]
    if not earnings.get("run_started_at"):
        earnings["run_started_at"] = ts.isoformat()

    if is_gym and leader:
        record = char.get("gyms", {}).get(leader)
        if record is not None:
            record["payout"] = amount
            record["payout_at"] = ts.isoformat()

    return event


def reset_run(char, started_at=None):
    earnings = ensure_character_earnings(char)
    started_at = started_at or datetime.now()
    earnings["run_started_at"] = started_at.isoformat()
    return earnings["run_started_at"]


def current_run_events(char):
    earnings = ensure_character_earnings(char)
    started = earnings.get("run_started_at")
    if not started:
        return []
    try:
        started_at = datetime.fromisoformat(started)
    except (TypeError, ValueError):
        return []

    result = []
    for event in earnings.get("events", []):
        try:
            event_ts = datetime.fromisoformat(event.get("ts", ""))
        except (TypeError, ValueError):
            continue
        if event_ts >= started_at:
            result.append(event)
    return result


def summarize_run(char, route_leaders):
    route = [canonical_leader(leader) for leader in (route_leaders or [])]
    route_set = set(route)
    events = current_run_events(char)

    total = sum(int(event.get("amount", 0)) for event in events)
    route_gym_events = [
        event for event in events
        if event.get("is_gym") and canonical_leader(event.get("leader")) in route_set
    ]
    route_gym_total = sum(int(event.get("amount", 0)) for event in route_gym_events)
    completed = {
        canonical_leader(event.get("leader"))
        for event in route_gym_events
        if event.get("leader")
    }
    other_total = total - route_gym_total
    remaining_leaders = [leader for leader in route if leader not in completed]

    return {
        "total": total,
        "route_gym_total": route_gym_total,
        "other_total": other_total,
        "gym_count": len(completed),
        "route_count": len(route),
        "completed_leaders": completed,
        "remaining_base": route_base_total(remaining_leaders),
        "events": events,
    }
