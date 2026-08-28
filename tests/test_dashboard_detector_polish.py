import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.dashboard_detector_polish import (
    DETECTOR_PIXEL_SCROLL_INCREMENT,
    detector_bottom_offset,
    detector_scroll_step,
    replay_started_filename,
    without_completed_replay_sessions,
)


class DashboardDetectorReplayPolishTests(unittest.TestCase):
    def event(self, text):
        return {"text": text}

    def test_replay_started_filename_extracts_only_lifecycle_start(self):
        self.assertEqual(replay_started_filename("Replay started: chat_26-08-2026.log"), "chat_26-08-2026.log")
        self.assertIsNone(replay_started_filename("Replay complete: chat_26-08-2026.log"))
        self.assertIsNone(replay_started_filename("Battle detected: Leader Erika"))

    def test_completed_replay_session_is_replaced_without_touching_live_events(self):
        events = [
            self.event("Live before"),
            self.event("Replay started: chat_test.log"),
            self.event("Battle detected: Leader Erika"),
            self.event("GYM WIN: Kanto / Celadon — Test; 18h cooldown started"),
            self.event("Replay complete: chat_test.log"),
            self.event("Live after"),
        ]
        cleaned = without_completed_replay_sessions(events, "chat_test.log")
        self.assertEqual([event["text"] for event in cleaned], ["Live before", "Live after"])

    def test_failed_replay_session_is_replaced(self):
        events = [
            self.event("Replay started: chat_test.log"),
            self.event("Battle detected: Leader Erika"),
            self.event("Replay failed: chat_test.log — OSError"),
        ]
        self.assertEqual(without_completed_replay_sessions(events, "chat_test.log"), [])

    def test_incomplete_replay_session_is_retained(self):
        events = [
            self.event("Replay started: chat_test.log"),
            self.event("Battle detected: Leader Erika"),
            self.event("Live later"),
        ]
        cleaned = without_completed_replay_sessions(events, "chat_test.log")
        self.assertEqual(cleaned, events)

    def test_only_matching_filename_session_is_removed(self):
        events = [
            self.event("Replay started: first.log"),
            self.event("Battle detected: Leader Erika"),
            self.event("Replay complete: first.log"),
            self.event("Replay started: second.log"),
            self.event("Battle detected: Leader Bugsy"),
            self.event("Replay complete: second.log"),
        ]
        cleaned = without_completed_replay_sessions(events, "first.log")
        self.assertEqual(
            [event["text"] for event in cleaned],
            [
                "Replay started: second.log",
                "Battle detected: Leader Bugsy",
                "Replay complete: second.log",
            ],
        )

    def test_short_history_bottom_offset_removes_blank_space_below_newest_event(self):
        # Three 1.0x rows occupy 90px; in a 124px Detector viewport they should
        # start 34px lower so the newest event still lands against the bottom.
        self.assertEqual(detector_bottom_offset(3, 124, 1.0), 34)
        self.assertEqual(detector_bottom_offset(4, 124, 1.0), 3)
        self.assertEqual(detector_bottom_offset(5, 124, 1.0), 0)
        self.assertEqual(detector_bottom_offset(0, 124, 1.0), 0)

    def test_detector_scroll_is_pixel_addressable_but_wheel_moves_one_visual_row(self):
        # A 1px Canvas increment avoids scale-dependent rounding/overshoot at the
        # bottom edge. Wheel movement still advances exactly one rendered row+gap.
        self.assertEqual(DETECTOR_PIXEL_SCROLL_INCREMENT, 1)
        self.assertEqual(detector_scroll_step(1.0), 31)
        self.assertEqual(detector_scroll_step(1.5), 46)
        self.assertEqual(detector_scroll_step(2.0), 62)


if __name__ == "__main__":
    unittest.main()
