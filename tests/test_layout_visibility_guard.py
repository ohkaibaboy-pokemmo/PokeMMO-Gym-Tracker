import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.layout_visibility_guard import (
    install_layout_visibility_guard,
    layout_manager_matches,
)


class FakeWidget:
    def __init__(self, manager, exists=True):
        self.manager = manager
        self.exists = exists

    def winfo_exists(self):
        return self.exists

    def winfo_manager(self):
        return self.manager


class LayoutVisibilityGuardTests(unittest.TestCase):
    def test_manager_match_requires_widget_to_be_actively_managed(self):
        self.assertTrue(layout_manager_matches(FakeWidget("pack"), "pack"))
        self.assertFalse(layout_manager_matches(FakeWidget(""), "pack"))
        self.assertFalse(layout_manager_matches(FakeWidget("grid"), "pack"))
        self.assertFalse(layout_manager_matches(FakeWidget("pack", exists=False), "pack"))

    def test_hidden_entries_are_withheld_from_scaling_then_restored(self):
        visible = FakeWidget("grid")
        hidden = FakeWidget("")
        seen_during_apply = []

        scaling = SimpleNamespace()
        scaling._base_layout = {
            "visible": (visible, "grid", {"padx": (7,)}),
            "hidden": (hidden, "grid", {"padx": (7,)}),
        }

        def original_apply():
            seen_during_apply.append(tuple(sorted(scaling._base_layout)))

        scaling._apply_full_layout_padding = original_apply
        app = SimpleNamespace(_scaling_controller=scaling)

        install_layout_visibility_guard(app)
        scaling._apply_full_layout_padding()

        self.assertEqual(seen_during_apply, [("visible",)])
        self.assertEqual(tuple(sorted(scaling._base_layout)), ("hidden", "visible"))

        # If a previously hidden widget is deliberately managed again later, it
        # participates in scaling on the next pass rather than being discarded.
        hidden.manager = "grid"
        scaling._apply_full_layout_padding()
        self.assertEqual(seen_during_apply[-1], ("hidden", "visible"))


if __name__ == "__main__":
    unittest.main()
