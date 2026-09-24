#!/usr/bin/env python3
"""Derive the light-theme twin of every README SVG: assets/X.svg -> assets/light/X.svg.

The README serves each visual through <picture> with a prefers-color-scheme
source, so GitHub shows the dark or light version to match the viewer's theme.
Rather than hand-maintaining two copies of every card, the light one is
derived from the dark one by remapping the (small, closed) palette -- so a new
card, or tonight's regenerated age/stats cards, get a light version for free.

    python scripts/lightify.py            # every themed SVG
    python scripts/lightify.py a.svg ...  # just these (paths relative to repo root)
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# dark hex -> light hex. Accents stay rich and saturated, just deepened enough
# to hold contrast on white; neutrals invert.
PALETTE = {
    # surfaces & lines
    "#05060a": "#ffffff", "#0d0f18": "#f2f4fa", "#1a1d2e": "#e1e5ef",
    # text
    "#eef0f6": "#12131c", "#9aa0b8": "#555a70", "#9498ab": "#555a70", "#5c6078": "#8a8fa6",
    # brand accents
    "#00e5ff": "#0092d6", "#b14dff": "#8a24e8", "#ff2d95": "#e0107a", "#39ff88": "#0aa851",
    # tech chip dots that vanish on white
    "#ffd21e": "#c99a00", "#ff9900": "#d97a00",
}
PATTERN = re.compile("|".join(re.escape(k) for k in PALETTE), re.IGNORECASE)

# Neon glow reads as a smudge on a white background -- flatten it.
GLOW = re.compile(r'stdDeviation="[0-9.]+"')


def themed_files():
    files = ["assets/header.svg", "assets/age.svg", "assets/stats.svg", "assets/intel.svg"]
    files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "assets", "ui", "*.svg")))
    return [f for f in files if os.path.exists(os.path.join(ROOT, f))]


def lightify(rel):
    src = os.path.join(ROOT, rel)
    dst = os.path.join(ROOT, "assets", "light", os.path.relpath(src, os.path.join(ROOT, "assets")))
    with open(src) as f:
        s = f.read()
    s = PATTERN.sub(lambda m: PALETTE[m.group(0).lower()], s)
    s = GLOW.sub('stdDeviation="0"', s)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(s)
    print(f"  ✓ {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    for rel in sys.argv[1:] or themed_files():
        lightify(rel)
