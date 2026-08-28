import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.engine import TrackerEngine, format_detector_money
from tracker.logs import ChatLiveTailer
from tracker.state import default_state


class DetectorLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.state = default_state()
        self.events = []
        self.engine = TrackerEngine(
            self.state,
            on_event=lambda ts, text, level="info": self.events.append((ts, text, level)),
            save_callback=lambda _state: None,
        )

    def feed(self, *lines):
        for line in lines:
            self.engine.process_line(line + "\n")

    def test_replay_emits_lifecycle_and_reconstructs_gym_timeline(self):
        lines = [
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:06:38] [Battle] TestCharacter sent out Typhlosion!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!",
        ]
        self.feed(*lines)
        payout_count = len(self.state["characters"]["TestCharacter"]["earnings"]["events"])
        processed_count = len(self.state["processed_events"])

        self.events.clear()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "chat_test.log"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.engine.replay_file(path)

        texts = [text for _ts, text, _level in self.events]
        self.assertTrue(texts[0].startswith("Replay started: chat_test.log"))
        self.assertTrue(any(text.startswith("Battle detected: Leader Brock") for text in texts))
        self.assertTrue(any(text.startswith("GYM WIN:") for text in texts))
        self.assertTrue(any(text.startswith("PAYOUT: Brock") and "$8,632" in text for text in texts))
        self.assertFalse(any("¥" in text for text in texts))
        self.assertTrue(texts[-1].startswith("Replay complete: chat_test.log"))
        self.assertEqual(len(self.state["processed_events"]), processed_count)
        self.assertEqual(
            len(self.state["characters"]["TestCharacter"]["earnings"]["events"]),
            payout_count,
        )

    def test_detector_money_formatter_uses_dollar_symbol(self):
        self.assertEqual(format_detector_money(9048), "$9,048")
        self.assertEqual(format_detector_money("8632"), "$8,632")

    def test_unmatched_payout_emits_warning(self):
        self.feed("[23/08/2026 15:08:50] [Battle] TestCharacter got $8632 for winning!")
        self.assertTrue(
            any(
                level == "warn"
                and text.startswith("Unmatched payout: TestCharacter")
                and "$8,632" in text
                and "¥" not in text
                for _ts, text, level in self.events
            )
        )

    def test_unresolved_victory_warns_when_next_battle_starts(self):
        self.feed(
            "[23/08/2026 15:06:31] [Battle] You are challenged by Leader Brock!",
            "[23/08/2026 15:08:44] [Battle] Player defeated Leader Brock!",
            "[23/08/2026 15:09:00] [Battle] You are challenged by Leader Misty!",
        )
        self.assertTrue(
            any(
                level == "warn" and text.startswith("Unresolved victory: Leader Brock")
                for _ts, text, level in self.events
            )
        )

    def test_live_tailer_switch_emits_filename_only_info_event(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            path = folder / "chat_25-08-2026.log"
            path.write_text("", encoding="utf-8")
            tailer = ChatLiveTailer(folder, self.engine)
            try:
                tailer.switch_to(path)
            finally:
                tailer.close()

        self.assertTrue(
            any(
                level == "info" and text == "Now watching log: chat_25-08-2026.log"
                for _ts, text, level in self.events
            )
        )
        self.assertFalse(any(temp in text for _ts, text, _level in self.events))

    def test_paused_live_tailer_does_not_process_new_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            path = folder / "chat_25-08-2026.log"
            path.write_text("", encoding="utf-8")
            tailer = ChatLiveTailer(folder, self.engine)
            try:
                tailer.switch_to(path)
                self.events.clear()
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(
                        "[25/08/2026 17:00:00] [Battle] You are challenged by Leader Brock!\n"
                    )

                tailer.paused = True
                tailer.poll()
                self.assertEqual(self.events, [])

                tailer.paused = False
                tailer.poll()
                self.assertTrue(
                    any(text == "Battle detected: Leader Brock" for _ts, text, _level in self.events)
                )
            finally:
                tailer.close()


if __name__ == "__main__":
    unittest.main()
