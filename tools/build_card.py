#!/usr/bin/env python3
"""Build custom_components/weerbericht/frontend/weerbericht-card.js.

Fills the template with the weather icon paths of the Home Assistant frontend
(src/data/weather.ts, Apache License 2.0), so the card draws the exact same
shapes as Home Assistant's own weather card.

    python tools/build_card.py [path/to/weather.ts]

Without an argument the file is downloaded from the frontend's dev branch.
"""
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "tools" / "weerbericht-card.template.js"
OUT = ROOT / "custom_components" / "weerbericht" / "frontend" / "weerbericht-card.js"
MANIFEST = ROOT / "custom_components" / "weerbericht" / "manifest.json"
SOURCE = "https://raw.githubusercontent.com/home-assistant/frontend/dev/src/data/weather.ts"


def main(argv):
    if len(argv) > 1:
        src = pathlib.Path(argv[1]).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(SOURCE, timeout=30) as r:
            src = r.read().decode("utf-8")
    body = src[src.index("const getWeatherStateSVG"):src.index("export const getWeatherStateIcon")]
    paths = re.findall(r'class="([a-z-]+)"\s*d="([^"]+)"', body)
    # Order in getWeatherStateSVG: sunny, clear-night, partly-cloudy moon, partly-cloudy
    # sun, cloud back, cloud front, 4 rain + 2 pouring drops, 2 wind lines, 3 snow, bolt.
    expected = ["sun", "moon", "moon", "sun", "cloud-back", "cloud-front"] + ["rain"] * 6 + \
        ["cloud-back"] * 2 + ["snow"] * 3 + ["sun"]
    got = [c for c, _ in paths]
    if got != expected:
        raise SystemExit(f"weather.ts layout changed, check the path order:\n{got}")
    d = [p for _, p in paths]
    data = {
        "sun": d[0],
        "moon": d[1],
        "smallSun": d[3],
        "cloudBack": d[4],
        "cloudFront": d[5],
        "rain": d[6:12],
        "windy": d[12:14],
        "snow": d[14:17],
        "bolt": d[17],
    }
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    js = TEMPLATE.read_text(encoding="utf-8")
    js = js.replace("__PATHS__", json.dumps(data, indent=2)).replace("__VERSION__", version)
    js = js.replace("Generated from tools/weerbericht-card.template.js by tools/build_card.py.",
                    "Generated from tools/weerbericht-card.template.js by tools/build_card.py. Do not edit.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(js, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(js)} bytes, version {version})")


if __name__ == "__main__":
    main(sys.argv)
