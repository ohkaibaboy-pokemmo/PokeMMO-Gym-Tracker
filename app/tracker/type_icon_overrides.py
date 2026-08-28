import math
import re
import tkinter as tk
from pathlib import Path

from .dashboard_gym_list import TYPE_MARKERS
from .user_assets import custom_asset_directory


TYPE_ICON_DIRNAME = "type_icons"


def type_icon_filename(gym_type):
    """Return the stable local-override filename for a gym specialty."""
    slug = re.sub(r"[^a-z0-9]+", "_", str(gym_type or "").lower()).strip("_")
    return f"{slug}.png" if slug else ""


def type_icon_path(directory, gym_type):
    filename = type_icon_filename(gym_type)
    return Path(directory) / filename if filename else None


def type_icon_directory():
    return custom_asset_directory(TYPE_ICON_DIRNAME)


class TypeIconOverrideController:
    """Own local PNG overrides shared by Full and Compact type markers.

    User-facing overrides live beside the portable app under
    ``custom/type_icons`` rather than inside LocalAppData. The Full Gym Route is
    rendered directly on one Canvas rather than through a tree of per-row Tk
    widgets. Both Full and Compact therefore request images from this controller
    explicitly. Missing/invalid PNGs still fall back to the project-owned marker
    drawn by the consuming view.
    """

    def __init__(self, app):
        self.app = app
        self.directory = type_icon_directory()
        self._image_cache = {}
        self._fallback_cache = {}
        self._bad_cache = set()

    def _cache_key(self, gym_type, path, width, height):
        try:
            stat = path.stat()
            modified = stat.st_mtime_ns
            size = stat.st_size
        except OSError:
            return None
        return str(gym_type), str(path), modified, size, int(width), int(height)

    def _load_for_size(self, gym_type, width, height):
        path = type_icon_path(self.directory, gym_type)
        if path is None or not path.is_file():
            return None

        width = max(1, int(width))
        height = max(1, int(height))
        key = self._cache_key(gym_type, path, width, height)
        if key is None:
            return None
        if key in self._image_cache:
            return self._image_cache[key]
        if key in self._bad_cache:
            return None

        try:
            image = tk.PhotoImage(master=self.app, file=str(path))
            target = max(1, min(width, height) - 2)
            factor = max(
                1,
                math.ceil(image.width() / target),
                math.ceil(image.height() / target),
            )
            if factor > 1:
                image = image.subsample(factor, factor)
        except (tk.TclError, OSError, ValueError):
            self._bad_cache.add(key)
            return None

        stale = [cached for cached in self._image_cache if cached[0] == str(gym_type) and cached != key]
        for cached in stale:
            self._image_cache.pop(cached, None)
            self._bad_cache.discard(cached)
        self._image_cache[key] = image
        return image

    def _compact_fallback(self, gym_type, width, height):
        marker = TYPE_MARKERS.get(gym_type)
        if marker is None:
            return None
        colour, _glyph = marker
        width = max(8, int(width))
        height = max(8, int(height))
        key = (str(gym_type), width, height, colour)
        if key in self._fallback_cache:
            return self._fallback_cache[key]

        image = tk.PhotoImage(master=self.app, width=width, height=height)
        cx = (width - 1) / 2.0
        cy = (height - 1) / 2.0
        radius = max(2.0, min(width, height) / 2.0 - 1.0)
        r2 = radius * radius
        inner = max(1.0, radius * 0.28)
        inner2 = inner * inner
        for y in range(height):
            for x in range(width):
                distance = (x - cx) ** 2 + (y - cy) ** 2
                if distance <= r2:
                    pixel = "#FFFFFF" if distance <= inner2 else colour
                    image.put(pixel, (x, y))

        self._fallback_cache[key] = image
        return image

    def image_for_type(self, gym_type, width, height, fallback=True):
        """Return an image for one gym specialty at the requested size.

        ``fallback=False`` is used by the Full Canvas renderer so it can preserve
        the richer project-owned glyph marker when no local PNG exists. Compact
        uses ``fallback=True`` because Treeview cells require a raster image.
        """
        if not gym_type:
            return None
        custom = self._load_for_size(gym_type, width, height)
        if custom is not None:
            return custom
        if fallback:
            return self._compact_fallback(gym_type, width, height)
        return None


def install_type_icon_overrides(app):
    existing = getattr(app, "_type_icon_overrides", None)
    if existing is not None:
        return existing

    controller = TypeIconOverrideController(app)
    app._type_icon_overrides = controller
    return controller
