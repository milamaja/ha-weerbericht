"""Constants for the Weerbericht integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_CONDITION_WINDY_VARIANT,
)

DOMAIN = "weerbericht"
ATTRIBUTION = "Bron: KNMI"

CONF_REGION = "region"

BASE_URL = "https://api.app.knmi.cloud"
REQUEST_TIMEOUT = 20
USER_AGENT = "ha-weerbericht/1.0.0 (+https://github.com/milamaja/ha-weerbericht)"
UPDATE_INTERVAL = timedelta(minutes=20)

# National precipitation radar loop as published on knmi.nl (no key needed),
# a new image every 5 minutes.
RADAR_URL = "https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/neerslagradar/WWWRADAR_loop.gif"
RADAR_INTERVAL = 300

# Forecast grid "A" of the KNMI app: a 35 x 30 grid of roughly 9 km cells
# covering the Netherlands, numbered from the north-west corner, column-major.
GRID_SW_LAT = 50.7
GRID_SW_LON = 3.2
GRID_NE_LAT = 53.6
GRID_NE_LON = 7.4
GRID_STEPS_LAT = 35
GRID_STEPS_LON = 30
GRID_PREFIX = "A"

# Weather alert regions (the KNMI warning regions), id -> name.
ALERT_REGIONS = {
    "1": "Drenthe",
    "2": "Flevoland",
    "3": "Friesland",
    "4": "Gelderland",
    "5": "Groningen",
    "6": "IJsselmeergebied",
    "7": "Limburg",
    "8": "Noord-Brabant",
    "9": "Noord-Holland",
    "10": "Overijssel",
    "11": "Utrecht",
    "12": "Waddeneilanden",
    "13": "IJsselmeer",
    "14": "Zeeland",
    "15": "Zuid-Holland",
}

ALERT_LEVELS = ["none", "yellow", "orange", "red"]
NO_ALERT_TEXT = "Geen waarschuwingen"

# KNMI app weatherType codes -> Home Assistant conditions. Codes come in
# day/night pairs (for example 1372 "zonnig" and 1373 "onbewolkt" at night).
_CONDITION_CODES = {
    ATTR_CONDITION_SUNNY: [1372, 1365],
    ATTR_CONDITION_CLEAR_NIGHT: [1373],
    ATTR_CONDITION_PARTLYCLOUDY: [1375, 1376],
    ATTR_CONDITION_CLOUDY: [1374],
    ATTR_CONDITION_RAINY: [1377, 1378, 1380, 1381, 1382, 1383, 1386, 1387, 1388],
    ATTR_CONDITION_POURING: [1379, 1384, 1385, 1366, 1371],
    ATTR_CONDITION_LIGHTNING: [1368, 1448],
    ATTR_CONDITION_LIGHTNING_RAINY: [1389, 1390, 1391, 1392, 1393, 1394, 1395, 1396, 1397],
    ATTR_CONDITION_SNOWY: [
        1401, 1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1367,
    ],
    ATTR_CONDITION_SNOWY_RAINY: [1398, 1399, 1400, 1413, 1414, 1415, 1419, 1364],
    ATTR_CONDITION_HAIL: [1416, 1417, 1418],
    ATTR_CONDITION_FOG: [1420, 1421, 1422, 1370],
    ATTR_CONDITION_WINDY: [1423, 1424, 1425],
    ATTR_CONDITION_WINDY_VARIANT: [1369],
}
CONDITION_MAP = {code: cond for cond, codes in _CONDITION_CODES.items() for code in codes}

# The night variant of each day/night pair (the KNMI app shows a moon for these).
NIGHT_CODES = {
    1373, 1376, 1381, 1383, 1385, 1388, 1392, 1394, 1397, 1400, 1403, 1406, 1409,
    1412, 1415, 1418,
}

# Icons for the entity (tiles, pickers, history) after sunset. Home Assistant
# has only one night condition (clear-night), so the other night looks are
# provided through the entity icon.
NIGHT_ICONS = {
    "sunny": "mdi:weather-night",
    "clear-night": "mdi:weather-night",
    "partlycloudy": "mdi:weather-night-partly-cloudy",
}

# Dutch description per code, as the KNMI app names its icons.
WEATHER_TYPE_TEXT = {
    1372: "Zonnig",
    1373: "Onbewolkt",
    1374: "Zwaar bewolkt",
    1375: "Opklaringen",
    1376: "Opklaringen",
    1377: "Lichte regen",
    1378: "Matige regen",
    1379: "Zware regen",
    1380: "Lichte bui, afgewisseld door zon",
    1381: "Lichte bui, afgewisseld door zon",
    1382: "Matige bui, afgewisseld door zon",
    1383: "Matige bui, afgewisseld door zon",
    1384: "Zware bui, afgewisseld door zon",
    1385: "Zware bui, afgewisseld door zon",
    1386: "Motregen",
    1387: "Motregen, afgewisseld door opklaringen",
    1388: "Motregen, afgewisseld door opklaringen",
    1389: "Onweer met matige regen",
    1390: "Onweer met zware regen",
    1391: "Onweer met matige regen, afgewisseld door zon",
    1392: "Onweer met matige regen, afgewisseld door zon",
    1393: "Onweer met zware regen, afgewisseld door zon",
    1394: "Onweer met zware regen, afgewisseld door zon",
    1395: "Onweer met hagel",
    1396: "Onweer met hagel, afgewisseld door zon",
    1397: "Onweer met hagel, afgewisseld door zon",
    1398: "Winterse buien met onweer",
    1399: "Winterse buien met onweer, afgewisseld door zon",
    1400: "Winterse buien met onweer, afgewisseld door zon",
    1401: "Sneeuwbui met onweer",
    1402: "Sneeuwbui met onweer, afgewisseld door zon",
    1403: "Sneeuwbui met onweer, afgewisseld door zon",
    1404: "Lichte sneeuwbui",
    1405: "Lichte sneeuwbui, afgewisseld door zon",
    1406: "Lichte sneeuwbui, afgewisseld door zon",
    1407: "Matige sneeuwbui",
    1408: "Matige sneeuwbui, afgewisseld door zon",
    1409: "Matige sneeuwbui, afgewisseld door zon",
    1410: "Zware sneeuwbui",
    1411: "Zware sneeuwbui, afgewisseld door zon",
    1412: "Zware sneeuwbui, afgewisseld door zon",
    1413: "Natte sneeuwbui",
    1414: "Natte sneeuwbui, afgewisseld door zon",
    1415: "Natte sneeuwbui, afgewisseld door zon",
    1416: "Hagelbui",
    1417: "Hagelbui, afgewisseld door zon",
    1418: "Hagelbui, afgewisseld door zon",
    1419: "Gladheid door ijzel",
    1420: "Mist",
    1421: "Mist",
    1422: "Mist",
    1423: "Windstoten",
    1424: "Harde wind",
    1425: "Harde wind",
}
