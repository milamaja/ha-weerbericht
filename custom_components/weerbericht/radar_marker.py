"""Draw a small house on the rain radar loop at the configured location.

The knmi.nl radar loop (425 x 445 pixels) uses the KNMI radar projection:
polar stereographic, true at 60 degrees north, central meridian 0 degrees.
The scale and offsets below were fitted on coastline points (Wadden islands,
Afsluitdijk) and checked on cities across the country; the error is about
one or two pixels (one or two kilometres).
"""
from __future__ import annotations

import io
import math

from PIL import Image, ImageDraw

RADAR_SIZE = (425, 445)
_EARTH_RADIUS_KM = 6371.0
_SCALE = 1.14739  # pixels per kilometre
_OFFSET_X = -173.524
_OFFSET_Y = -4431.464

# House outline around the location, in pixels: roof peak, eaves, walls.
_HOUSE = [(0, -7), (7, 0), (5, 0), (5, 6), (-5, 6), (-5, 0), (-7, 0)]
_FILL = (255, 255, 255)
_LINE = (33, 33, 33)


def radar_pixel(latitude: float, longitude: float) -> tuple[int, int]:
    """Pixel of a coordinate on the radar image."""
    r = (
        _EARTH_RADIUS_KM
        * (1 + math.sin(math.radians(60)))
        * math.tan(math.radians(45 - latitude / 2))
    )
    t = math.radians(longitude)
    return (
        round(_SCALE * r * math.sin(t) + _OFFSET_X),
        round(_SCALE * r * math.cos(t) + _OFFSET_Y),
    )


def mark_location(gif: bytes, latitude: float, longitude: float) -> bytes:
    """Return the radar loop with a house drawn on every frame.

    Returns the image unchanged when it does not have the known size (the
    projection would not fit) or the location falls outside it.
    """
    src = Image.open(io.BytesIO(gif))
    if src.size != RADAR_SIZE:
        return gif
    x, y = radar_pixel(latitude, longitude)
    if not (8 <= x < RADAR_SIZE[0] - 8 and 8 <= y < RADAR_SIZE[1] - 8):
        return gif

    house = [(x + dx, y + dy) for dx, dy in _HOUSE]
    frames: list[Image.Image] = []
    durations: list[int] = []
    for index in range(getattr(src, "n_frames", 1)):
        src.seek(index)
        frame = src.convert("RGB")
        draw = ImageDraw.Draw(frame)
        draw.polygon(house, fill=_FILL, outline=_LINE, width=2)
        draw.rectangle([x - 1, y + 2, x + 1, y + 5], fill=_LINE)  # door
        frames.append(frame)
        durations.append(src.info.get("duration", 300))

    out = io.BytesIO()
    frames[0].save(
        out,
        "GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=src.info.get("loop", 0),
    )
    return out.getvalue()
