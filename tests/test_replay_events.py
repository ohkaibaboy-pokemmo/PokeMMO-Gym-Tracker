import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.engine import TrackerEngine
from tracker.state import default_state


class ReplayPresentationEventTests(unittest.TestCase):
    LINES = (
        "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
        "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
        "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
        "[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!",
    )

    def setUp(self):
        self.state = default_state()
        self.events = []
        self.engine = TrackerEngine(
            self.state,
            on_event=lambda ts, text, level="info": self.events.append((ts, text, level)),
            save_callback=lambda _state: None,
        )

    def test_replay_re_emits_existing_win_and_payout_without_duplicating_state(self):
        for line in self.LINES:
            self.engine.process_line(line + "\n")

        processed_before = list(self.state["processed_events"])
        payouts_before = list(
            self.state["characters"]["TestCharacter"]["earnings"]["events"]
        )
        self.events.clear()

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chat_test.log"
            path.write_text("\n".join(self.LINES) + "\n", encoding="utf-8")
            self.engine.replay_file(path)

        texts = [text for _ts, text, _level in self.events]
        self.assertTrue(any(text.startswith("Battle detected: Leader Brock") for text in texts))
        self.assertTrue(any(text.startswith("GYM WIN: Kanto / Pewter") for text in texts))
        self.assertTrue(any(text.startswith("PAYOUT: Brock") for text in texts))

        self.assertEqual(self.state["processed_events"], processed_before)
        self.assertEqual(
            self.state["characters"]["TestCharacter"]["earnings"]["events"],
            payouts_before,
        )

    def test_replay_iterator_can_be_advanced_incrementally(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chat_incremental.log"
            path.write_text("\n".join(self.LINES) + "\n", encoding="utf-8")
            iterator = self.engine.replay_iter(path)

            # Nothing runs until the UI advances the generator.
            self.assertFalse(self.engine.replaying)
            self.assertEqual(self.events, [])

            next(iterator)
            self.assertTrue(self.engine.replaying)
            texts = [text for _ts, text, _level in self.events]
            self.assertTrue(texts[0].startswith("Replay started: chat_incremental.log"))
            self.assertTrue(any(text.startswith("Battle detected: Leader Brock") for text in texts))
            self.assertFalse(any(text.startswith("Replay complete:") for text in texts))

            # The iterator is deliberately consumable in arbitrary-sized batches.
            # Existing synchronous replay tests separately cover the full BATTLE /
            # GYM / PAY presentation semantics; this test only guards yielding and
            # lifecycle restoration for the responsive Tk controller.
            for _unused in iterator:
                pass

        self.assertFalse(self.engine.replaying)
        texts = [text for _ts, text, _level in self.events]
        self.assertTrue(texts[-1].startswith("Replay complete: chat_incremental.log"))


if __name__ == "__main__":
    unittest.main()
