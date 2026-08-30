import re
from datetime import datetime, timedelta
from pathlib import Path

from .constants import COOLDOWN_HOURS, REQUIRED_OTHER_TRAINERS
from .core import canonical_leader, gym_for_leader, norm, opponent_is_leader, parse_ts
from .earnings import record_payout
from .state import save_state
from .trainers import normal_trainer_counts

COLOR_TAG_RE = re.compile(r"\[#(?:[0-9A-Fa-f]{6})?\]")
# Timestamp formatting is locale-dependent in PokeMMO logs. Capture the complete
# leading timestamp field here and let core.parse_ts validate the supported forms.
LINE_RE = re.compile(r"^\[([^\]]+)\]\s+\[([^\]]+)\]\s?(.*)$")
CHALLENGE_RE = re.compile(r"^You are challenged by (.+)!$")
SEND_OUT_RE = re.compile(r"^(.+?) sent out (.+)!$")
VICTORY_RE = re.compile(r"^Player defeated (.+)!$")
PAYOUT_RE = re.compile(r"^(.+?) got \$([0-9,]+) for winning!$")
FIVE_BATTLE_BLOCK_TEXT = "You must battle other trainers before you may rematch this trainer."
PAYOUT_MATCH_WINDOW_SECONDS = 120


def strip_tags(value: str) -> str:
    return COLOR_TAG_RE.sub("", value).strip()


def format_detector_money(value) -> str:
    """Format detected PokeMMO prize money for the v0.6 presentation layer."""
    try:
        return f"${int(value):,}"
    except (TypeError, ValueError):
        return "$0"


class TrackerEngine:
    def __init__(self, state, on_event=None, on_change=None, save_callback=None):
        self.state = state
        self.on_event = on_event or (lambda *args: None)
        self.on_change = on_change or (lambda: None)
        self.save_callback = save_callback or save_state
        self.active = None
        self.pending_victory = None
        self.last_victory = None
        # Explicit log replay should reconstruct the Detector activity stream even
        # when the underlying win/payout is already present in persistent state.
        # State remains de-duplicated; only presentation events are re-emitted.
        self.replaying = False

    def emit(self, ts, text, level="info"):
        self.on_event(ts, text, level)

    @staticmethod
    def event_id(ts, player, opponent):
        return f"{ts.isoformat()}|{player}|{opponent}"

    def get_char(self, player):
        chars = self.state.setdefault("characters", {})
        char = chars.setdefault(player, {"gyms": {}})
        char.setdefault("gyms", {})
        return char

    def apply_other_trainer_win(self, ts, player, opponent, exclude_leader=None):
        """Apply one qualifying trainer victory to every active gym requirement."""
        char = self.get_char(player)
        updated = 0
        for leader, record in char.get("gyms", {}).items():
            if exclude_leader and canonical_leader(leader) == canonical_leader(exclude_leader):
                continue
            defeated = record.get("defeated_at")
            if not defeated:
                continue
            try:
                defeated_at = datetime.fromisoformat(defeated)
            except Exception:
                continue
            if ts <= defeated_at:
                continue
            current = int(record.get("other_trainers", 0))
            if current < REQUIRED_OTHER_TRAINERS:
                record["other_trainers"] = current + 1
                record.setdefault("qualifying_events", []).append({"ts": ts.isoformat(), "opponent": opponent})
                updated += 1
        return updated

    def _emit_gym_win(self, ts, player, leader):
        leader = canonical_leader(leader)
        mapped = gym_for_leader(leader)
        label = f"{mapped[0]} / {mapped[1]}" if mapped else leader
        self.emit(ts, f"GYM WIN: {label} — {player}; 18h cooldown started", "success")

    def _emit_replayed_victory(self, ts, player, opponent):
        """Reconstruct Detector history without mutating already-recorded state."""
        is_leader, leader = opponent_is_leader(opponent)
        if is_leader:
            self._emit_gym_win(ts, player, leader)
        elif normal_trainer_counts(self.state, opponent):
            self.emit(ts, f"Trainer win: {opponent} — previously recorded", "success")
        else:
            self.emit(ts, f"Trainer win: {opponent} — explicitly excluded from the 5-rule", "warn")

    def _warn_pending_victory(self, ts=None, reason="could not identify the player"):
        pending = self.pending_victory
        if not pending:
            return False
        event_ts = ts or pending.get("ts") or datetime.now()
        opponent = pending.get("opponent") or "unknown opponent"
        self.emit(event_ts, f"Unresolved victory: {opponent} — {reason}.", "warn")
        self.pending_victory = None
        return True

    def record_victory(self, ts, player, opponent):
        event_id = self.event_id(ts, player, opponent)
        processed = self.state.setdefault("processed_events", [])
        if event_id in processed:
            if self.replaying:
                self._emit_replayed_victory(ts, player, opponent)
            return False
        processed.append(event_id)

        is_leader, leader = opponent_is_leader(opponent)
        if is_leader:
            self.apply_other_trainer_win(ts, player, opponent, exclude_leader=leader)
            leader = canonical_leader(leader)
            char = self.get_char(player)
            char["gyms"][leader] = {
                "defeated_at": ts.isoformat(),
                "ready_at": (ts + timedelta(hours=COOLDOWN_HOURS)).isoformat(),
                "other_trainers": 0,
                "qualifying_events": [],
                "manual_ready": False,
            }
            self._emit_gym_win(ts, player, leader)
        elif normal_trainer_counts(self.state, opponent):
            updated = self.apply_other_trainer_win(ts, player, opponent)
            if updated:
                self.emit(
                    ts,
                    f"Trainer win: {opponent} — counted toward {updated} active gym requirement"
                    + ("s" if updated != 1 else ""),
                    "success",
                )
            else:
                self.emit(ts, f"Trainer win: {opponent} — eligible for the 5-rule", "success")
        else:
            self.emit(ts, f"Trainer win: {opponent} — explicitly excluded from the 5-rule", "warn")

        self.save_callback(self.state)
        self.on_change()
        return True

    def remember_victory(self, ts, player, opponent):
        self.last_victory = {"ts": ts, "player": player, "opponent": opponent}

    def payout_context(self, ts, player):
        context = self.last_victory
        if not context or norm(context.get("player")) != norm(player):
            return None
        age = (ts - context["ts"]).total_seconds()
        if age < 0 or age > PAYOUT_MATCH_WINDOW_SECONDS:
            return None
        return context

    def _emit_payout(self, ts, player, opponent, amount, is_gym=None):
        detected_is_gym, detected_leader = opponent_is_leader(opponent)
        if is_gym is None:
            is_gym = detected_is_gym
        if is_gym:
            leader = detected_leader if detected_is_gym else canonical_leader(opponent)
            label = canonical_leader(leader)
        else:
            label = opponent
        self.emit(ts, f"PAYOUT: {label} — {player}; {format_detector_money(amount)}", "info")

    def record_linked_payout(self, ts, player, opponent, amount):
        event = record_payout(self.state, ts, player, opponent, amount)
        if event is None:
            if self.replaying:
                self._emit_payout(ts, player, opponent, amount)
            return False
        self._emit_payout(ts, player, opponent, amount, bool(event.get("is_gym")))
        self.save_callback(self.state)
        self.on_change()
        return True

    def process_line(self, raw_line):
        raw_line = raw_line.rstrip("\r\n")
        match = LINE_RE.match(raw_line)
        if not match:
            return
        ts_text, channel, message = match.groups()
        if channel not in {"Battle", "System Messages"}:
            return
        try:
            ts = parse_ts(ts_text)
        except Exception:
            return
        message = strip_tags(message)

        if channel == "System Messages":
            if FIVE_BATTLE_BLOCK_TEXT in message:
                self.emit(ts, "PokeMMO says the 5-other-trainer requirement is not yet met.", "warn")
            return

        challenge = CHALLENGE_RE.match(message)
        if challenge:
            if self.pending_victory:
                self._warn_pending_victory(ts, "no player/payout context arrived before the next battle")
            opponent = challenge.group(1).strip()
            self.active = {"opponent": opponent, "started": ts, "player": None}
            self.pending_victory = None
            self.emit(ts, f"Battle detected: {opponent}", "info")
            return

        send_out = SEND_OUT_RE.match(message)
        if send_out and self.active:
            who = send_out.group(1).strip()
            if norm(who) != norm(self.active["opponent"]) and not who.startswith(("Leader ", "Leaders ")):
                self.active["player"] = who
            return

        victory = VICTORY_RE.match(message)
        if victory:
            opponent = victory.group(1).strip()
            player = self.active.get("player") if self.active else None
            if player:
                self.remember_victory(ts, player, opponent)
                self.record_victory(ts, player, opponent)
                self.active = None
                self.pending_victory = None
            else:
                self.pending_victory = {"ts": ts, "opponent": opponent}
            return

        payout = PAYOUT_RE.match(message)
        if payout:
            player = payout.group(1).strip()
            amount = int(payout.group(2).replace(",", ""))

            if self.pending_victory:
                pending = self.pending_victory
                self.remember_victory(pending["ts"], player, pending["opponent"])
                self.record_victory(pending["ts"], player, pending["opponent"])
                self.pending_victory = None
                self.active = None

            context = self.payout_context(ts, player)
            if context:
                self.record_linked_payout(ts, player, context["opponent"], amount)
            else:
                self.emit(
                    ts,
                    f"Unmatched payout: {player} received {format_detector_money(amount)} — no recent victory context.",
                    "warn",
                )
            return

    def replay_iter(self, path: Path):
        """Incrementally replay one log while preserving the normal replay semantics.

        The synchronous ``replay_file`` method consumes this iterator immediately.
        The dashboard can instead advance it in small Tk ``after`` batches, which
        keeps the Windows message loop responsive during large historical replays.
        One value is yielded after each input line has been processed.
        """
        path = Path(path)
        self.active = None
        self.pending_victory = None
        self.last_victory = None
        previous_replaying = self.replaying
        self.replaying = True
        self.emit(datetime.now(), f"Replay started: {path.name}", "info")
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    self.process_line(line)
                    yield None
            if self.pending_victory:
                self._warn_pending_victory(reason="replay ended before player/payout context was available")
        except Exception as exc:
            self.emit(datetime.now(), f"Replay failed: {path.name} — {exc.__class__.__name__}", "warn")
            raise
        else:
            self.emit(datetime.now(), f"Replay complete: {path.name}", "info")
        finally:
            self.replaying = previous_replaying

    def replay_file(self, path: Path):
        for _unused in self.replay_iter(path):
            pass
