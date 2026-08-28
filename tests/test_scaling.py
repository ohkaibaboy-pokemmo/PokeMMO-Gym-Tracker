import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from tracker.dashboard_scaling import (
    combobox_popdown_listbox_path,
    configure_combobox_popup_font,
)
from tracker.scaling import (
    DEFAULT_UI_SCALE,
    UI_SCALE_FACTORS,
    create_font,
    normalise_scale,
    scaled,
)


class UIScalingTests(unittest.TestCase):
    def test_supported_scale_options(self):
        self.assertEqual(
            tuple(UI_SCALE_FACTORS.keys()),
            ("0.85×", "1.0×", "1.25×", "1.5×", "1.75×", "2.0×"),
        )
        self.assertEqual(UI_SCALE_FACTORS["1.25×"], 1.25)

    def test_scale_normalisation(self):
        self.assertEqual(normalise_scale("1.5×"), "1.5×")
        self.assertEqual(normalise_scale("1.24"), "1.25×")
        self.assertEqual(normalise_scale("not-a-scale"), DEFAULT_UI_SCALE)

    def test_pixel_scaling(self):
        self.assertEqual(scaled(40, 1.5), 60)
        self.assertEqual(scaled(46, 1.25), 58)
        self.assertEqual(scaled(2, 0.85), 2)

    def test_font_constructor_uses_root_not_master(self):
        fake_root = object()
        with patch("tracker.scaling.tkfont.Font") as font_ctor:
            create_font(fake_root, family="Segoe UI", size=14)
        font_ctor.assert_called_once_with(root=fake_root, family="Segoe UI", size=14)

    def test_combobox_popdown_listbox_path_matches_ttk_layout(self):
        self.assertEqual(
            combobox_popdown_listbox_path(".combo.popdown"),
            ".combo.popdown.f.l",
        )

    def test_combobox_popup_uses_same_font_as_visible_field(self):
        widget = Mock()
        widget.__str__ = Mock(return_value=".filters.region")
        widget.cget.return_value = "font42"
        widget.tk.call.side_effect = [".filters.region.popdown", ""]

        self.assertTrue(configure_combobox_popup_font(widget))
        self.assertEqual(
            widget.tk.call.call_args_list,
            [
                unittest.mock.call(
                    "ttk::combobox::PopdownWindow",
                    ".filters.region",
                ),
                unittest.mock.call(
                    ".filters.region.popdown.f.l",
                    "configure",
                    "-font",
                    "font42",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
