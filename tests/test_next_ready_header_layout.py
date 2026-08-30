import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.dashboard_next_ready import (
    COOLDOWN_COLUMN,
    DETAIL_COLUMN,
    HEADER_CARD_ORDER,
    NEXT_READY_COLUMN,
    READY_COLUMN,
    RUN_EARNINGS_COLUMN,
    WAITING_COLUMN,
)


class NextReadyHeaderLayoutTests(unittest.TestCase):
    def test_adopted_visible_order_matches_operational_priority(self):
        self.assertEqual(
            HEADER_CARD_ORDER,
            ("next_ready", "ready", "waiting", "cooldown", "earnings", "details"),
        )

    def test_visible_cards_map_left_to_right_with_cooldown_retained(self):
        self.assertEqual(
            (
                NEXT_READY_COLUMN,
                READY_COLUMN,
                WAITING_COLUMN,
                COOLDOWN_COLUMN,
                RUN_EARNINGS_COLUMN,
                DETAIL_COLUMN,
            ),
            (0, 1, 2, 3, 4, 5),
        )


if __name__ == "__main__":
    unittest.main()
