"""Generate the Windows .ico used by PyInstaller from native emblem frames."""

from io import BytesIO
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from tracker.icon_spec import WINDOWS_ICON_SIZES, icon_spans


def render(size):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for x1, y1, x2, y2, colour in icon_spans(size):
        draw.rectangle((x1, y1, x2 - 1, y2 - 1), fill=colour)
    return image


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def write_ico(output, sizes):
    """Write an ICO containing separately rendered PNG frames at every size."""
    frames = [(size, png_bytes(render(size))) for size in sizes]
    header_size = 6 + 16 * len(frames)
    offset = header_size

    with output.open("wb") as handle:
        handle.write(struct.pack("<HHH", 0, 1, len(frames)))
        for size, data in frames:
            width = 0 if size == 256 else size
            height = 0 if size == 256 else size
            handle.write(
                struct.pack(
                    "<BBBBHHII",
                    width,
                    height,
                    0,
                    0,
                    1,
                    32,
                    len(data),
                    offset,
                )
            )
            offset += len(data)
        for _size, data in frames:
            handle.write(data)


def main():
    output_dir = ROOT / ".build-assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "gym-tracker.ico"

    # Each frame is rendered independently. This prevents the 16/24/32px art
    # from being blurred by an automatic 256px downscale and preserves the gaps.
    write_ico(output, WINDOWS_ICON_SIZES)

    # Fail the build early if Pillow cannot see every native frame we intended.
    with Image.open(output) as icon:
        embedded = set(icon.ico.sizes())
    expected = {(size, size) for size in WINDOWS_ICON_SIZES}
    if embedded != expected:
        raise RuntimeError(f"ICO frame mismatch: expected {expected}, got {embedded}")

    print(f"{output} ({', '.join(str(size) for size in WINDOWS_ICON_SIZES)}px native frames)")


if __name__ == "__main__":
    main()
