"""Verify the generated ICO frames were embedded into the Windows EXE."""

from pathlib import Path
import struct
import sys

import pefile


ROOT = Path(__file__).resolve().parents[1]
ICO = ROOT / ".build-assets" / "gym-tracker.ico"
DIST = ROOT / "dist"
EXE_CANDIDATES = (
    DIST / "PokeMMO Gym Tracker.exe",
    DIST / "PokeMMO Gym Tracker" / "PokeMMO Gym Tracker.exe",
)


def built_exe_path():
    for path in EXE_CANDIDATES:
        if path.exists():
            return path
    return EXE_CANDIDATES[0]


def ico_payloads(path):
    data = path.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0 or kind != 1 or count < 1:
        raise RuntimeError("Generated icon is not a valid ICO")
    payloads = []
    for index in range(count):
        entry = struct.unpack_from("<BBBBHHII", data, 6 + index * 16)
        width, height, _colours, _reserved, _planes, _bits, size, offset = entry
        logical_width = 256 if width == 0 else width
        logical_height = 256 if height == 0 else height
        payloads.append(((logical_width, logical_height), data[offset:offset + size]))
    return payloads


def exe_icon_resources(path):
    pe = pefile.PE(str(path))
    resources = []
    try:
        root = pe.DIRECTORY_ENTRY_RESOURCE
    except AttributeError as exc:
        raise RuntimeError("EXE has no Windows resource directory") from exc

    rt_icon = pefile.RESOURCE_TYPE["RT_ICON"]
    for resource_type in root.entries:
        if resource_type.id != rt_icon:
            continue
        for resource_id in resource_type.directory.entries:
            for language in resource_id.directory.entries:
                rva = language.data.struct.OffsetToData
                size = language.data.struct.Size
                resources.append(pe.get_data(rva, size))
    return resources


def main():
    exe = built_exe_path()
    if not ICO.exists() or not exe.exists():
        raise RuntimeError("ICO or EXE missing; run this after the Windows build")

    expected = ico_payloads(ICO)
    embedded = exe_icon_resources(exe)
    if not embedded:
        raise RuntimeError("No RT_ICON resources found in built EXE")

    matched = [size for size, payload in expected if payload in embedded]
    required = {(16, 16), (24, 24), (32, 32)}
    if not required.issubset(set(matched)):
        raise RuntimeError(
            f"Built EXE does not contain required native icon frames. Matched: {matched}"
        )

    print(f"Verified EXE icon frames: {matched} ({exe.relative_to(ROOT)})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Icon verification failed: {exc}", file=sys.stderr)
        raise
