#!/usr/bin/env python3
"""Build custom_components/weerbericht/places.json: every Dutch place (woonplaats).

Each place with its BAG code (the "wp" code the KNMI uses for local warnings),
its name and its centre point. The integration picks the place whose centre is
nearest to the location, like the KNMI app's own place list; no lookup at run time.

Source: the BAG (Kadaster, open data) through the PDOK Locatieserver.

    python3 tools/build_places.py
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "custom_components" / "weerbericht" / "places.json"
URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
ROWS = 100


def page(start: int) -> dict:
    query = urllib.parse.urlencode({
        "q": "*:*", "fq": "type:woonplaats", "rows": ROWS, "start": start, "sort": "woonplaatscode asc",
        "fl": "woonplaatscode,woonplaatsnaam,centroide_ll",
    })
    with urllib.request.urlopen(f"{URL}?{query}", timeout=60) as resp:
        return json.load(resp)["response"]


def main() -> None:
    places, start, total = [], 0, None
    while total is None or start < total:
        response = page(start)
        total = response["numFound"]
        for doc in response["docs"]:
            point = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", doc.get("centroide_ll") or "")
            code = str(doc.get("woonplaatscode") or "")
            if point and code.isdigit():
                lon, lat = float(point.group(1)), float(point.group(2))
                places.append([f"wp{int(code):04d}", doc["woonplaatsnaam"], round(lat, 4), round(lon, 4)])
        start += ROWS
        time.sleep(0.2)
    places.sort(key=lambda p: int(p[0][2:]))
    data = {
        "source": "BAG woonplaatsen (Kadaster, open data) via the PDOK Locatieserver",
        "built": time.strftime("%Y-%m-%d"),
        "fields": ["code", "name", "lat", "lon"],
        "places": places,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(places)} of {total} places -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
