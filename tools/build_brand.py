#!/usr/bin/env python3
"""Build the integration's brand icons (custom_components/weerbericht/brand/).

The icon is Home Assistant's own "partly cloudy" weather drawing (sun behind a
cloud) from the frontend's src/data/weather.ts (Apache License 2.0), the same
picture HA's weather card shows. Two colour sets:

    icon.png / icon@2x.png            light theme: slightly darker cloud greys,
                                      so the cloud stays visible on white
    dark_icon.png / dark_icon@2x.png  dark theme: HA's own weather colours

    python tools/build_brand.py [path/to/weather.ts]

Needs Pillow and svg.path (pip install pillow svg.path).
"""
import json
import pathlib
import re
import sys
import urllib.request

from PIL import Image, ImageDraw
from svg.path import parse_path

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "custom_components" / "weerbericht" / "brand"
SOURCE = "https://raw.githubusercontent.com/home-assistant/frontend/dev/src/data/weather.ts"

COLOURS = {
    "light": {"sun": "#fdd93c", "cloud-back": "#a9b0b8", "cloud-front": "#d9dde2"},
    "dark": {"sun": "#fdd93c", "cloud-back": "#d4d4d4", "cloud-front": "#f9f9f9"},
}
SUPERSAMPLE = 4
SAMPLES_PER_SEGMENT = 40


def load_paths(src: str) -> dict[str, str]:
    body = src[src.index("const getWeatherStateSVG"):src.index("export const getWeatherStateIcon")]
    paths = re.findall(r'class="([a-z-]+)"\s*d="([^"]+)"', body)
    d = [p for _, p in paths]
    # order: sunny, clear-night, partly-cloudy moon, partly-cloudy sun, cloud back, cloud front, ...
    return {"sun": d[3], "cloud-back": d[4], "cloud-front": d[5]}


def polygons(d: str):
    """Flatten an SVG path into closed polygons (one per subpath)."""
    path = parse_path(d)
    polys, current = [], []
    for seg in path:
        name = type(seg).__name__
        if name == "Move":
            if len(current) > 2:
                polys.append(current)
            current = [seg.end]
            continue
        n = 1 if name in ("Line", "Close") else SAMPLES_PER_SEGMENT
        for i in range(1, n + 1):
            current.append(seg.point(i / n))
    if len(current) > 2:
        polys.append(current)
    return polys


def bbox(all_polys):
    xs = [p.real for poly in all_polys for p in poly]
    ys = [p.imag for poly in all_polys for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def render(paths: dict[str, str], colours: dict[str, str], size: int) -> Image.Image:
    shapes = {k: polygons(v) for k, v in paths.items()}
    x0, y0, x1, y1 = bbox([p for polys in shapes.values() for p in polys])
    big = size * SUPERSAMPLE
    margin = big * 0.06
    scale = (big - 2 * margin) / max(x1 - x0, y1 - y0)
    ox = (big - (x1 - x0) * scale) / 2 - x0 * scale
    oy = (big - (y1 - y0) * scale) / 2 - y0 * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for key in ("sun", "cloud-back", "cloud-front"):  # painting order of HA's SVG
        for poly in shapes[key]:
            draw.polygon([(p.real * scale + ox, p.imag * scale + oy) for p in poly], fill=colours[key])
    return img.resize((size, size), Image.LANCZOS)


def main(argv):
    if len(argv) > 1:
        src = pathlib.Path(argv[1]).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(SOURCE, timeout=30) as r:
            src = r.read().decode("utf-8")
    paths = load_paths(src)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme, prefix in (("light", ""), ("dark", "dark_")):
        for size, suffix in ((256, ""), (512, "@2x")):
            name = f"{prefix}icon{suffix}.png"
            render(paths, COLOURS[theme], size).save(OUT / name, optimize=True)
            print("wrote", (OUT / name).relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv)
