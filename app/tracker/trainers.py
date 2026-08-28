from collections import defaultdict
from datetime import datetime

from .constants import EXCLUDED_5_RULE_TRAINERS, REQUIRED_OTHER_TRAINERS, VERIFIED_REMATCH_TRAINERS
from .core import canonical_leader, norm, opponent_is_leader


def excluded_5_rule_trainers(state):
    """Return normalized trainer names explicitly excluded from the 5-rule.

    v0.6 uses an opt-out model: every detected non-gym trainer victory qualifies
    unless that opponent has been explicitly excluded. This matches the tracker
    behaviour adopted during live testing and avoids silently under-counting
    ordinary trainers that are not present in a hard-coded catalogue.
    """
    configured = state.setdefault("excluded_5_rule_trainers", EXCLUDED_5_RULE_TRAINERS[:])
    return {norm(name) for name in configured}


def normal_trainer_counts(state, opponent):
    return norm(opponent) not in excluded_5_rule_trainers(state)


def merge_verified_catalogue(state):
    """Preserve the old verified catalogue for state/backwards compatibility.

    The catalogue is no longer an allow-list for the 5-rule. Trainer wins now
    qualify by default; only `excluded_5_rule_trainers` can opt an opponent out.
    """
    confirmed = state.setdefault("confirmed_normal_rematch_trainers", [])
    existing = {norm(name) for name in confirmed}
    for trainer in VERIFIED_REMATCH_TRAINERS:
        key = norm(trainer)
        if key not in existing:
            confirmed.append(trainer)
            existing.add(key)


def learn_repeat_rematches(state):
    """Retain historical repeat-evidence metadata for backwards compatibility.

    This data is no longer required before a trainer can count toward the 5-rule,
    but keeping it avoids destroying information already stored by older builds.
    """
    seen = defaultdict(lambda: defaultdict(list))
    for event_id in state.get("processed_events", []):
        try:
            ts_text, player, opponent = event_id.split("|", 2)
            ts = datetime.fromisoformat(ts_text)
        except Exception:
            continue
        is_leader, _ = opponent_is_leader(opponent)
        if not is_leader:
            seen[player][opponent].append(ts)

    learned = set(state.get("learned_rematch_trainers", []))
    for opponents in seen.values():
        for opponent, times in opponents.items():
            times.sort()
            if len(times) < 2:
                continue
            first = times[0]
            if any((later - first).total_seconds() >= 3600 for later in times[1:]):
                learned.add(opponent)

    state["learned_rematch_trainers"] = sorted(learned, key=str.lower)
    confirmed = state.setdefault("confirmed_normal_rematch_trainers", [])
    existing = {norm(name) for name in confirmed}
    added = []
    for trainer in state["learned_rematch_trainers"]:
        key = norm(trainer)
        if key not in existing:
            confirmed.append(trainer)
            existing.add(key)
            added.append(trainer)
    return added


def _is_legacy_manual_leader_event(ts, opponent):
    """Identify pre-fix v0.6 manual Gym corrections in processed_events.

    PokeMMO chat-log timestamps are second precision. Older Manual Correction code
    called ``record_victory(datetime.now(), ...)`` directly, producing leader event
    ids with non-zero microseconds. Those synthetic events must not be reused as
    evidence for other gyms' five-battle requirements during state reconstruction.
    """
    is_leader, _ = opponent_is_leader(opponent)
    return bool(is_leader and getattr(ts, "microsecond", 0))


def recalculate_5_rule_counts(state):
    """Rebuild gym counters from recorded victories using opt-out semantics."""
    excluded = excluded_5_rule_trainers(state)
    events_by_player = {}
    for event_id in state.get("processed_events", []):
        try:
            ts_text, player, opponent = event_id.split("|", 2)
            ts = datetime.fromisoformat(ts_text)
        except Exception:
            continue
        if _is_legacy_manual_leader_event(ts, opponent):
            continue
        events_by_player.setdefault(player, []).append((ts, opponent))

    for player, char in state.get("characters", {}).items():
        events = sorted(events_by_player.get(player, []), key=lambda item: item[0])
        for leader, record in char.get("gyms", {}).items():
            if record.get("manual_ready"):
                record["other_trainers"] = REQUIRED_OTHER_TRAINERS
                continue
            try:
                defeated_at = datetime.fromisoformat(record.get("defeated_at", ""))
            except Exception:
                continue

            qualifying = []
            for ts, opponent in events:
                if ts <= defeated_at:
                    continue
                is_leader, other_leader = opponent_is_leader(opponent)
                if is_leader:
                    # A different Gym Leader is an "other trainer". The same
                    # leader cannot satisfy their own post-defeat requirement.
                    qualifies = canonical_leader(other_leader) != canonical_leader(leader)
                else:
                    qualifies = norm(opponent) not in excluded
                if not qualifies:
                    continue
                qualifying.append({"ts": ts.isoformat(), "opponent": opponent})
                if len(qualifying) >= REQUIRED_OTHER_TRAINERS:
                    break

            record["other_trainers"] = len(qualifying)
            record["qualifying_events"] = qualifying
