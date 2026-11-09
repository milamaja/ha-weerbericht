"""Draw the rain radar loops: the KNMI app's radar images on a light or a dark map.

The KNMI app gets its radar as one PNG per 5 minutes: only the rain, on a
transparent background, in a few fixed colours (light blue for light rain up
to red for the heaviest), in the Dutch RD grid (EPSG:28992). Every frame is
cut to the Netherlands and laid on a map made by tools/build_radar_map.py from
Natural Earth. The light style keeps the KNMI colours on a map in the colours
of knmi.nl; the dark style shows the rain from white (light) to dark blue
(heavy) on a dark map. Each frame shows its time, and a small house can mark
the configured location.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# The "detail" radar images of the KNMI app: size and area (RD metres).
FRAME_SIZE = (1007, 1208)
FRAME_BBOX = (-100000.0, 150000.0, 400000.0, 750000.0)  # x min, y min, x max, y max
# The part shown: the Netherlands with some 25 km around it, in frame pixels.
CROP = (180, 222, 806, 926)  # left, top, right, bottom

# KNMI colours from light to heavy rain (the order in which they border each
# other in the images).
KNMI_RAIN = [
    (152, 216, 250),
    (29, 169, 244),
    (49, 183, 254),
    (7, 129, 242),
    (2, 104, 198),
    (255, 212, 109),
    (254, 172, 49),
    (220, 81, 69),
]

FRAME_MS = 300
LAST_FRAME_MS = 3000


@dataclass(frozen=True)
class RadarStyle:
    """How a radar loop looks: its map, rain colours, text and house."""

    map_file: str
    rain: tuple[tuple[int, int, int], ...]  # the colour for each KNMI_RAIN colour
    heaviest: tuple[int, int, int]  # any other colour: beyond the known scale
    text: tuple[int, int, int]  # the time
    text_halo: tuple[int, int, int] | None  # a thin outline around it, or none
    label: tuple[int, int, int]
    house_rim: float  # width of a light rim around the house, 0 for none


LIGHT = RadarStyle(
    map_file="radar_map_light.png",
    rain=tuple(KNMI_RAIN),
    heaviest=(150, 60, 170),
    text=(20, 22, 24),
    text_halo=None,
    label=(40, 60, 40),
    house_rim=0,
)
DARK = RadarStyle(
    map_file="radar_map_dark.png",
    rain=(
        (238, 242, 250),
        (196, 214, 245),
        (154, 184, 238),
        (112, 152, 230),
        (78, 121, 220),
        (52, 94, 206),
        (36, 71, 186),
        (26, 52, 160),
    ),
    heaviest=(18, 38, 128),
    text=(232, 234, 238),
    text_halo=(0, 0, 0),
    label=(120, 124, 130),
    house_rim=1,
)
STYLES = {"light": LIGHT, "dark": DARK}

# The house of the knmi.nl loop, around the location: roof peak, eaves, walls,
# and the door. These images are about 1.5 times as large as that loop, so the
# house is too, to look the same size on a dashboard.
_HOUSE = [(0, -7), (7, 0), (5, 0), (5, 6), (-5, 6), (-5, 0), (-7, 0)]
_HOUSE_DOOR = (-1.5, 1.5, 1.5, 6)
_HOUSE_SCALE = 1.5
_HOUSE_FILL = (255, 255, 255)
_HOUSE_LINE = (24, 24, 24)
_HOUSE_RIM_COLOUR = (214, 216, 220)

# --- Dutch RD grid (EPSG:28992) ------------------------------------------------
# Oblique stereographic projection on the Bessel 1841 ellipsoid, reached from
# WGS84 through the 7-parameter datum shift of Amersfoort (reversed).
_WGS84 = (6378137.0, 1 / 298.257223563)
_BESSEL = (6377397.155, 1 / 299.1528128)
_SHIFT = (565.417, 50.3319, 465.552)  # metres
_ROTATION = tuple(math.radians(s / 3600) for s in (-0.398957, 0.343988, -1.8774))
_SCALE_PPM = 4.0725
_LAT0, _LON0 = math.radians(52.156160556), math.radians(5.387638889)
_K0, _FALSE_E, _FALSE_N = 0.9999079, 155000.0, 463000.0


def _e2(ellipsoid: tuple[float, float]) -> float:
    f = ellipsoid[1]
    return 2 * f - f * f


def _projection_constants() -> tuple[float, float, float, float, float]:
    a, e2 = _BESSEL[0], _e2(_BESSEL)
    e = math.sqrt(e2)
    sin0 = math.sin(_LAT0)
    rho0 = a * (1 - e2) / (1 - e2 * sin0**2) ** 1.5
    nu0 = a / math.sqrt(1 - e2 * sin0**2)
    radius = math.sqrt(rho0 * nu0)
    n = math.sqrt(1 + e2 * math.cos(_LAT0) ** 4 / (1 - e2))
    s1 = (1 + sin0) / (1 - sin0)
    s2 = (1 - e * sin0) / (1 + e * sin0)
    w1 = (s1 * s2**e) ** n
    sin_chi00 = (w1 - 1) / (w1 + 1)
    c = (n + sin0) * (1 - sin_chi00) / ((n - sin0) * (1 + sin_chi00))
    w2 = c * w1
    chi0 = math.asin((w2 - 1) / (w2 + 1))
    return radius, n, c, chi0, e


_R, _N, _C, _CHI0, _E = _projection_constants()


def _wgs84_to_bessel(latitude: float, longitude: float) -> tuple[float, float]:
    """Latitude and longitude (radians) on the Bessel ellipsoid of the RD grid."""
    a, e2 = _WGS84[0], _e2(_WGS84)
    lat, lon = math.radians(latitude), math.radians(longitude)
    nu = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    x = nu * math.cos(lat) * math.cos(lon) - _SHIFT[0]
    y = nu * math.cos(lat) * math.sin(lon) - _SHIFT[1]
    z = nu * (1 - e2) * math.sin(lat) - _SHIFT[2]
    rx, ry, rz = _ROTATION
    s = 1 - _SCALE_PPM * 1e-6
    x, y, z = s * (x + rz * y - ry * z), s * (-rz * x + y + rx * z), s * (ry * x - rx * y + z)
    a, e2 = _BESSEL[0], _e2(_BESSEL)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(5):
        nu = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        lat = math.atan2(z + e2 * nu * math.sin(lat), p)
    return lat, math.atan2(y, x)


def rd_from_wgs84(latitude: float, longitude: float) -> tuple[float, float]:
    """RD coordinates (x, y in metres) of a WGS84 position."""
    lat, lon = _wgs84_to_bessel(latitude, longitude)
    sin_lat = math.sin(lat)
    w = _C * ((1 + sin_lat) / (1 - sin_lat) * ((1 - _E * sin_lat) / (1 + _E * sin_lat)) ** _E) ** _N
    chi = math.asin((w - 1) / (w + 1))
    dlon = _N * (lon - _LON0)
    b = 1 + math.sin(chi) * math.sin(_CHI0) + math.cos(chi) * math.cos(_CHI0) * math.cos(dlon)
    x = _FALSE_E + 2 * _R * _K0 * math.cos(chi) * math.sin(dlon) / b
    y = _FALSE_N + 2 * _R * _K0 * (
        math.sin(chi) * math.cos(_CHI0) - math.cos(chi) * math.sin(_CHI0) * math.cos(dlon)
    ) / b
    return x, y


def map_pixel(x: float, y: float) -> tuple[float, float]:
    """Pixel on the radar image (after the crop) of RD coordinates."""
    xmin, ymin, xmax, ymax = FRAME_BBOX
    column = (x - xmin) / (xmax - xmin) * FRAME_SIZE[0]
    row = (ymax - y) / (ymax - ymin) * FRAME_SIZE[1]
    return column - CROP[0], row - CROP[1]


def radar_pixel(latitude: float, longitude: float) -> tuple[int, int]:
    """Pixel on the radar image of a WGS84 position."""
    column, row = map_pixel(*rd_from_wgs84(latitude, longitude))
    return math.floor(column), math.floor(row)


# --- Drawing --------------------------------------------------------------------
def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow without FreeType: the small bitmap font
        return ImageFont.load_default()


def _house(rim_width: float) -> Image.Image:
    """The house marker with smooth edges, centred in a transparent square."""
    supersample = 4
    k = _HOUSE_SCALE * supersample
    size = round(18 * _HOUSE_SCALE) * supersample  # 18: the house plus its outline
    centre = size / 2
    outline = [(centre + dx * k, centre + dy * k) for dx, dy in _HOUSE]
    sprite = Image.new("RGBA", (size, size), _HOUSE_RIM_COLOUR + (0,))
    if rim_width:
        # A light rim around the dark outline, which would vanish on a dark map.
        shape = Image.new("L", (size, size), 0)
        ImageDraw.Draw(shape).polygon(outline, fill=255)
        sprite.putalpha(shape.filter(ImageFilter.MaxFilter(2 * round(rim_width * k) + 1)))
    draw = ImageDraw.Draw(sprite)
    draw.polygon(outline, fill=_HOUSE_FILL + (255,), outline=_HOUSE_LINE + (255,), width=round(2 * k))
    left, top, right, bottom = _HOUSE_DOOR
    draw.rectangle(
        [centre + left * k, centre + top * k, centre + right * k, centre + bottom * k],
        fill=_HOUSE_LINE + (255,),
    )
    return sprite.resize((size // supersample, size // supersample), Image.Resampling.LANCZOS)


def _shared_palette(style: RadarStyle, map_colours: list[int]) -> Image.Image:
    """A palette image with the map's colours, the rain scale and the drawing colours.

    The text and the house are drawn smooth, so a few steps between the text
    colour and its shadow, and between the house's colours, are added for their edges.
    """
    colours = [tuple(map_colours[i:i + 3]) for i in range(0, len(map_colours) - 2, 3)]
    colours += list(style.rain) + [style.heaviest, _HOUSE_FILL, _HOUSE_LINE, style.label]
    # The text's edges blend into its outline, or into the map.
    edge = style.text_halo or tuple(map_colours[:3]) or style.text
    colours.append(edge)
    for start, end in ((edge, style.text), (_HOUSE_LINE, _HOUSE_FILL)):
        for step in range(8):
            colours.append(tuple(round(a + (b - a) * step / 8) for a, b in zip(start, end)))
    colours.append(style.text)
    unique = list(dict.fromkeys(colours))[:256]
    unique += [unique[-1]] * (256 - len(unique))
    palette = Image.new("P", (1, 1))
    palette.putpalette([value for colour in unique for value in colour])
    return palette


def _rain_layer(png: bytes, style: RadarStyle) -> tuple[Image.Image, Image.Image] | None:
    """The rain of one KNMI frame in the style's colours, with its mask; None if unusable."""
    shown = dict(zip(KNMI_RAIN, style.rain))
    frame = Image.open(io.BytesIO(png))
    if frame.size != FRAME_SIZE or frame.mode != "P":
        return None
    frame = frame.crop(CROP)
    palette = frame.getpalette() or []
    transparency = frame.info.get("transparency")
    dry = set()
    if isinstance(transparency, int):
        dry.add(transparency)
    elif isinstance(transparency, bytes):
        dry.update(i for i, alpha in enumerate(transparency) if alpha == 0)
    colours, mask_table = [], []
    for index in range(256):
        knmi = tuple(palette[3 * index:3 * index + 3])
        colours.extend(shown.get(knmi, style.heaviest))
        mask_table.append(0 if index in dry or len(knmi) < 3 else 255)
    mask = frame.point(mask_table, "L")
    rain = frame.copy()
    rain.putpalette(colours)
    return rain.convert("RGB"), mask


def build_loop(
    frames: list[tuple[datetime, bytes]],
    location: tuple[float, float] | None,
    style: RadarStyle = DARK,
    credit: str = "Data source: KNMI",
) -> bytes | None:
    """The animated GIF of the frames (local times, PNG bytes), oldest first.

    The credit (where the data comes from) goes in the bottom right corner.

    Frames that are not a KNMI radar image of the known size are left out;
    None when none is left.
    """
    map_file = Path(__file__).parent / style.map_file
    with Image.open(map_file) as stored:
        base = stored.convert("RGB")
        map_colours = stored.getpalette() if stored.mode == "P" else []
    if base.size != (CROP[2] - CROP[0], CROP[3] - CROP[1]):
        raise ValueError(f"{map_file.name} has size {base.size}, expected the crop size")
    palette = _shared_palette(style, map_colours or [])
    house, house_at = None, (0, 0)
    if location is not None:
        x, y = radar_pixel(*location)
        house = _house(style.house_rim)
        half = house.width // 2
        if half <= x < base.width - half and half <= y < base.height - half:
            house_at = (x - half, y - half)
        else:
            house = None
    font = _font(20)
    small = _font(14)
    images: list[Image.Image] = []
    for moment, png in frames:
        layer = _rain_layer(png, style)
        if layer is None:
            continue
        image = base.copy()
        image.paste(*layer)
        if house is not None:
            image.paste(house, house_at, house)
        draw = ImageDraw.Draw(image)
        label = moment.strftime("%H:%M")
        # The time; on the dark map with a thin outline, so it stays clear of
        # the rain in white.
        if style.text_halo:
            draw.text((12, 10), label, font=font, fill=style.text, stroke_width=1, stroke_fill=style.text_halo)
        else:
            draw.text((12, 10), label, font=font, fill=style.text)
        draw.text((image.width - 8, image.height - 7), credit, font=small, fill=style.label, anchor="rs")
        # One palette for all frames: the map stays the same from frame to
        # frame, so the GIF only stores what changed (mostly the rain).
        images.append(image.quantize(palette=palette, dither=Image.Dither.NONE))
    if not images:
        return None
    out = io.BytesIO()
    images[0].save(
        out,
        "GIF",
        save_all=True,
        append_images=images[1:],
        duration=[FRAME_MS] * (len(images) - 1) + [LAST_FRAME_MS],
        loop=0,
        optimize=False,
    )
    return out.getvalue()
