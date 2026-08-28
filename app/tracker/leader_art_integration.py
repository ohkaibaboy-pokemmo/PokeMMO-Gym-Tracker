from tkinter import ttk

from .constants import GYMS
from .leader_art import PixelPortraitRenderer
from .user_assets import custom_asset_directory


_SCALE_RATIOS = {
    0.85: (6, 7),
    1.0: (1, 1),
    1.25: (5, 4),
    1.5: (3, 2),
    1.75: (7, 4),
    2.0: (2, 1),
}


class LeaderArtController:
    """Installs original leader portraits over the presentation fallback art.

    Local user-provided PNG overrides remain highest priority and live beside the
    portable app under ``custom/leader_sprites``. The built-in portraits are
    generated entirely in Tk at runtime and contain no copied Pokémon/PokeMMO
    sprite pixels.

    FullViewPresentation owns the app's theme-change callback and historically
    rebuilt its older generic fallback badges there. Rebind that presentation
    image-builder hook to this controller so every later theme rebuild uses the
    adopted original portraits instead of racing the fallback theme pass.
    """

    def __init__(self, app):
        self.app = app
        self.presentation = app._presentation
        # presentation._after_theme_change() always calls _build_leader_images().
        # Delegate that hook permanently to the adopted portrait renderer. This is
        # deterministic and avoids the previous after_idle/after(1) race where a
        # Light-theme fallback rebuild could win and replace all leader portraits.
        self.presentation._build_leader_images = self.rebuild
        self.rebuild()

    def _factor(self):
        getter = getattr(self.app, "ui_scale_factor", None)
        if callable(getter):
            try:
                return float(getter())
            except Exception:
                pass
        return 1.0

    def _scale_image(self, image):
        factor = self._factor()
        nearest = min(_SCALE_RATIOS, key=lambda value: abs(value - factor))
        numerator, denominator = _SCALE_RATIOS[nearest]
        if numerator == denominator:
            return image
        try:
            return image.zoom(numerator, numerator).subsample(denominator, denominator)
        except Exception:
            return image

    def rebuild(self):
        renderer = PixelPortraitRenderer(self.app, self.app.theme())
        custom_dir = custom_asset_directory("leader_sprites")

        images = {}
        for _region, _gym, leader in GYMS:
            custom_path = custom_dir / self.presentation._sprite_filename(leader)
            custom = self.presentation._load_custom_sprite(custom_path)
            image = custom if custom is not None else renderer.render(leader)
            images[leader] = self._scale_image(image)

        self.presentation._leader_images = images
        factor = self._factor()
        rowheight = max(30, int(round(40 * factor)))
        image_column = max(38, int(round(46 * factor)))
        style = ttk.Style(self.app)
        style.configure("Treeview", rowheight=rowheight)
        self.app.tree.column("#0", width=image_column, minwidth=image_column, stretch=False, anchor="center")
        self.presentation._decorate_rows()


def install_leader_art(app):
    app._leader_art_controller = LeaderArtController(app)
    return app._leader_art_controller
