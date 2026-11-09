#!/usr/bin/env python3
"""Build the maps under the rain radar: radar_map_light.png and radar_map_dark.png.

The maps have exactly the size, area and projection (the Dutch RD grid) of the
part of the KNMI radar images the integration shows, so the rain lands on the
right spot. Land, sea, lakes, rivers, country and province borders come from
Natural Earth (public domain, 1:10 million). The light map has the colours of
the knmi.nl radar, with the Netherlands lighter than the countries around it.

Needs Pillow. Downloads the Natural Earth files (about 65 MB) into a cache folder.

    python3 tools/build_radar_map.py [cache_dir]
"""
import importlib.util
import json
import pathlib
import sys
import urllib.request

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "custom_components" / "weerbericht"
SOURCE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson"
CACHE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/natural-earth")
SUPERSAMPLE = 4  # drawn this many times larger, then scaled down for smooth edges
AREA = (1.5, 49.5, 9.0, 55.0)  # lon min, lat min, lon max, lat max: features outside are skipped

MAPS = {
    "radar_map_light.png": {
        "sea": (53, 146, 186),
        "land": (113, 165, 76),
        "home": (143, 183, 109),  # the Netherlands
        "river": (66, 150, 175),
        "province": (108, 156, 90),
        "country": (78, 126, 68),
    },
    "radar_map_dark.png": {
        "sea": (16, 18, 21),
        "land": (38, 40, 44),
        "home": (38, 40, 44),
        "river": (44, 55, 68),
        "province": (60, 64, 70),
        "country": (100, 105, 113),
    },
}

# radar_image.py holds the projection and the crop; load it without Home Assistant.
spec = importlib.util.spec_from_file_location("radar_image", PACKAGE / "radar_image.py")
radar_image = importlib.util.module_from_spec(spec)
sys.modules["radar_image"] = radar_image  # the dataclass in it looks itself up
spec.loader.exec_module(radar_image)


def layer(name: str) -> list[dict]:
    path = CACHE / f"{name}.geojson"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SOURCE.format(name), timeout=300) as resp:
            path.write_bytes(resp.read())
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def rings(geometry: dict) -> list[list[list[float]]]:
    """Every ring or line of a geometry, as lists of [lon, lat]."""
    kind, coords = geometry["type"], geometry["coordinates"]
    if kind == "Polygon":
        return coords
    if kind == "MultiPolygon":
        return [ring for polygon in coords for ring in polygon]
    if kind == "LineString":
        return [coords]
    if kind == "MultiLineString":
        return coords
    return []


def in_area(ring: list[list[float]]) -> bool:
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return not (max(lons) < AREA[0] or min(lons) > AREA[2] or max(lats) < AREA[1] or min(lats) > AREA[3])


def pixels(ring: list[list[float]]) -> list[tuple[float, float]]:
    out = []
    for lon, lat in ring:
        column, row = radar_image.map_pixel(*radar_image.rd_from_wgs84(lat, lon))
        out.append((column * SUPERSAMPLE, row * SUPERSAMPLE))
    return out


def polygons(
    image: Image.Image,
    names: list[str],
    fill: tuple[int, int, int],
    holes: bool = True,
    country: str | None = None,
) -> None:
    """Fill the polygons of the layers. A hole (an island in a lake, a lake on
    land) keeps what is under it; with holes=False the holes are filled too."""
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    for name in names:
        for feature in layer(name):
            geometry = feature["geometry"]
            if geometry is None or (country and feature["properties"].get("ADM0_A3") != country):
                continue
            polys = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            for polygon in polys:
                if not in_area(polygon[0]):
                    continue
                draw.polygon(pixels(polygon[0]), fill=255)
                for inner in polygon[1:] if holes else []:
                    draw.polygon(pixels(inner), fill=0)
    image.paste(fill, mask=mask)


def lines(draw: ImageDraw.ImageDraw, names: list[str], colour: tuple[int, int, int], width: float) -> None:
    for name in names:
        for feature in layer(name):
            if feature["geometry"] is None:
                continue
            for ring in rings(feature["geometry"]):
                if in_area(ring):
                    draw.line(pixels(ring), fill=colour, width=round(width * SUPERSAMPLE), joint="curve")


def main() -> None:
    left, top, right, bottom = radar_image.CROP
    size = (right - left, bottom - top)
    for filename, c in MAPS.items():
        image = Image.new("RGB", (size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE), c["sea"])
        draw = ImageDraw.Draw(image)
        polygons(image, ["ne_10m_land", "ne_10m_minor_islands"], c["land"])
        if c["home"] != c["land"]:
            # Without its holes; the lakes are drawn over it next.
            polygons(image, ["ne_10m_admin_0_countries"], c["home"], holes=False, country="NLD")
        polygons(image, ["ne_10m_lakes", "ne_10m_lakes_europe"], c["sea"])
        lines(draw, ["ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe"], c["river"], 1.2)
        lines(draw, ["ne_10m_admin_1_states_provinces_lines"], c["province"], 0.8)
        lines(draw, ["ne_10m_admin_0_boundary_lines_land"], c["country"], 1.3)
        image = image.resize(size, Image.Resampling.LANCZOS)
        image = image.quantize(colors=64, dither=Image.Dither.NONE)
        out = PACKAGE / filename
        image.save(out, optimize=True)
        print(f"{out} {size[0]}x{size[1]} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
