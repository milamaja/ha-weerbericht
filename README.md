# Weerbericht for Home Assistant

A Home Assistant integration that shows the Dutch weather exactly as the official KNMI app shows it, for any location in the Netherlands, plus the national rain radar.

It reads the same backend the KNMI app uses (`api.app.knmi.cloud`, published as open source by KNMI). That gives you the KNMI meteorologists' forecast itself, not a third-party forecast built from KNMI data. No API key, no account.

Weerbericht is an independent project. It is not made by, endorsed by, or affiliated with KNMI. The weather data is produced by KNMI (Koninklijk Nederlands Meteorologisch Instituut).

## What you get

For each configured location:

- A `weather` entity with the current weather, an hourly forecast (about 60 hours) and a daily forecast (7 days with weather type, plus 8 more days from the 14-day outlook with temperature and precipitation only). Values match the KNMI app: temperature, precipitation amount and chance, wind speed and gusts in km/h, wind direction, UV index.
- Sensors: temperature now, maximum and minimum of today, precipitation today, hours of sunshine today, UV index, heat index (hittekracht), weather alert level, weather alert text, and a Dutch weather description ("Opklaringen", "Lichte bui, afgewisseld door zon", ...).
- Expected rain for the next 2 hours on your location, from the KNMI app's rain graph (radar nowcast in 5-minute steps): an **Expected rain** sensor with the total in mm and the 5-minute series in its `forecast` attribute (plus `rain_start`, `rain_end` and `max_intensity`), and a **Rain intensity** sensor with the current intensity in mm/h. Both update every 5 minutes.
- A `camera` entity with the animated rain radar of the Netherlands (the loop published on knmi.nl, a new image every 5 minutes), with a small house on your location so you can see where the rain is heading.
- A **Weerbericht card** for your dashboard. It looks like Home Assistant's own weather card, but shows every KNMI app weather type: showers, thunder, snow and hail with the sun or the moon behind the cloud, and a moon instead of a sun after sunset. It is installed together with the integration, no separate download. Tapping it opens a detail popup with more information than Home Assistant's own weather dialog.
- Its own integration icon (Home Assistant 2026.3 and newer).

The weather alert sensors follow the KNMI code colours: `none`, `yellow`, `orange`, `red`. The alert text sensor holds the warning text, or "Geen waarschuwingen" ("No warnings" in English) when there is none, so it can be shown on a dashboard tile directly.

## Installation

### HACS (custom repository)

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=milamaja&repository=ha-weerbericht&category=integration)

The button opens this repository in HACS (it uses [My Home Assistant](https://www.home-assistant.io/integrations/my/), which is on by default). Or add it by hand:

1. In HACS, open the menu (three dots, top right) and choose **Custom repositories**.
2. Add `https://github.com/milamaja/ha-weerbericht` with category **Integration**.
3. Install **Weerbericht** and restart Home Assistant.

### Manual

1. Copy the folder `custom_components/weerbericht` into the `custom_components` folder of your Home Assistant configuration directory.
2. Restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up Weerbericht.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=weerbericht)

Or go to **Settings, Devices & services, Add integration** and search for **Weerbericht**. Fill in:

- **Name**: used for the device and the entity IDs, for example `Weerbericht`.
- **Latitude / Longitude**: default to your home location. The forecast is per grid cell of roughly 9 km, the same cells the app uses.
- **Warning region**: the province used for weather alerts.

You can add the integration more than once for several locations.

### Settings

Under **Settings, Devices & services, Weerbericht, Configure** you choose the language of the warning texts, and whether the rain radar shows the location as a small house (on by default).

### Warning language

The warning texts come in two languages:

- **Dutch** (default): the KNMI's own texts, straight from the KNMI app, for example "Code geel voor dichte mist vanaf 01:00 tot 10:00".
- **English**: the same warnings from [MeteoAlarm](https://meteoalarm.org), the European warning service the KNMI also publishes to, for example "Code yellow: moderate fog warning from 01:00 until 10:00". They are only fetched while a warning is out.

The warning level (and the glow on the card) always comes from the KNMI.

## Dashboard examples

Entity IDs depend on the name you gave the integration and on your Home Assistant language. The examples use the name `Weerbericht` with an English UI; check your own IDs on the device page.

### Weerbericht card

After installing, refresh your browser once. Then add the card from the card picker (search for "Weerbericht"). All options can be set in the visual editor, labelled in Dutch or English following your Home Assistant language. Or in YAML:

```yaml
type: custom:weerbericht-card
entity: weather.weerbericht
forecast_type: daily      # or hourly
name: Thuis               # optional
forecast_slots: 5         # optional, otherwise as many as fit
```

It also supports `show_current: false`, `show_forecast: false`, `round_temperature: true` and a `tap_action` (`more-info`, `navigate`, `url` or `none`).

Below the forecast the card can show the **rain graph** for the next 2 hours on your location, like the KNMI app: a bar per 5 minutes, with lines for light, moderate and heavy rain (the KNMI app's levels: up to 1, 8 and 15 mm/h, each level equally high), a line with the value at this moment, and a summary such as "Rain from 14:25 · 0.6 mm".

- `show_rain: auto` (default) shows it only while rain is on its way, `always` keeps it there (also "Dry for the next 2 hours"), `never` leaves it out.
- `rain_height: 136` sets its height in pixels (default 96).
- The card finds the Expected rain sensor of the same location by itself; `rain_entity` points it at another one.

The graph is also available as a card of its own, for example next to the radar:

```yaml
type: custom:weerbericht-rain-card
title: Neerslag            # optional
show_levels: true          # light / moderate / heavy lines
show_summary: true
```

Point at the graph (or tap it on a touch screen) to see the value at that moment.

Without a `tap_action`, tapping the card opens the **Weerbericht popup**: the current weather with the KNMI icon and description, a warning bar in the KNMI colour, wind with direction and Beaufort, gusts, rain today (amount and chance), hours of sunshine, UV index, sunrise and sunset, the rain graph for the next 2 hours, and tabs with the hourly forecast and up to 15 days with temperature bars and rain. The chart button in the popup opens Home Assistant's own dialog for history graphs. With a Dutch Home Assistant the condition is shown in the KNMI wording ("Opklaringen", "Lichte bui, afgewisseld door zon").

#### Weather alert glow

Add `alert_glow: true` to the card and the dashboard gets a soft, slowly pulsing glow along its edges while a KNMI weather warning is out: yellow, orange or red, following the KNMI code. No glow when there is no warning.

```yaml
type: custom:weerbericht-card
entity: weather.weerbericht
alert_glow: true
```

- The glow sits behind the cards, below the top bar and right of the side menu, so buttons stay fully visible and every tap goes through.
- It follows the warnings for the next 24 hours, like the KNMI app, and appears, changes colour or disappears by itself on an open dashboard (handy for a wall tablet).
- It only shows while a dashboard with such a card is open.
- `alert_entity: sensor.your_alert_sensor` takes the level from another entity, and `alert_glow_test: yellow` (or `orange`, `red`) shows the glow for trying it out. Remove the test option afterwards.

You can tune the look:

| Option | Default | Meaning |
|---|---|---|
| `alert_glow_size` | `32` | How far the glow reaches into the dashboard, in pixels (4 to 200) |
| `alert_glow_strength` | `60` | How strong the colour is, in percent (5 to 100) |
| `alert_glow_pulse` | `3` | Seconds per pulse (up to 30). `0` or `false` gives a steady glow |

```yaml
type: custom:weerbericht-card
entity: weather.weerbericht
alert_glow: true
alert_glow_size: 48
alert_glow_strength: 40
alert_glow_pulse: 5
```

When several cards with a glow are on screen, the settings of the card with the highest warning level are used. The pulse is a slow fade, so it also runs on devices set to reduce motion; set `alert_glow_pulse: 0` for a steady glow.

Home Assistant's built-in weather card and the entity popup work too, but they have no pictures for showers with sun, and they draw partly cloudy with a sun even at night. The entity always reports the real KNMI condition; only the Weerbericht card and the entity icon show the moon behind a cloud.

### Weather alert tiles

One tile per alert level, each shown only for its own level. This uses Home Assistant's built-in card visibility option, no plugin needed. In a sections dashboard you can also set it on the **Visibility** tab of each card. That tab is missing for cards nested inside a grid or stack, so add these tiles as separate cards.

```yaml
- type: tile
  entity: sensor.weerbericht_weather_alert_text
  name: No warnings
  icon: mdi:check-circle-outline
  color: green
  hide_state: true
  visibility:
    - condition: state
      entity: sensor.weerbericht_weather_alert
      state: none
- type: tile
  entity: sensor.weerbericht_weather_alert_text
  name: Weather warning
  icon: mdi:alert-outline
  color: yellow
  visibility:
    - condition: state
      entity: sensor.weerbericht_weather_alert
      state: yellow
- type: tile
  entity: sensor.weerbericht_weather_alert_text
  name: Dangerous weather
  icon: mdi:alert-outline
  color: deep-orange
  visibility:
    - condition: state
      entity: sensor.weerbericht_weather_alert
      state: orange
- type: tile
  entity: sensor.weerbericht_weather_alert_text
  name: Red alert
  icon: mdi:alert-outline
  color: red
  visibility:
    - condition: state
      entity: sensor.weerbericht_weather_alert
      state: red
```

The tile state shows the KNMI warning text. The `hide_state` on the green tile hides "Geen waarschuwingen".

### Rain radar

```yaml
type: picture-entity
entity: camera.weerbericht_rain_radar
camera_image: camera.weerbericht_rain_radar
camera_view: auto
fit_mode: contain
show_state: false
show_name: false
```

## How it works

- The integration polls the app backend every 20 minutes: one summary request and one detail request per forecast day.
- Your coordinates are converted to the app's forecast grid cell (grid "A", 35 by 30 cells over the Netherlands). The cell is shown as the `grid_cell` attribute of the weather entity.
- KNMI weather type codes are mapped to Home Assistant conditions. Night variants map to `clear-night` and `partlycloudy`.
- The rain graph is polled every 5 minutes (two small requests), only while one of the rain sensors is enabled.
- The radar image is fetched only when a dashboard asks for it, and cached for 5 minutes. The house is drawn on each frame of the loop inside Home Assistant; your location never leaves your system.

## Limitations

- Netherlands only, like the app.
- The app backend is a public but undocumented API without a stability promise. If KNMI changes it, this integration needs an update. The official KNMI Data Platform APIs do not offer the app's forecast.
- Current values (temperature, wind) are the app's nowcast for your cell, not a station measurement. For station observations use the KNMI Data Platform EDR API with a registered key.

## Attribution

Weather data and radar image: KNMI (Koninklijk Nederlands Meteorologisch Instituut), available under their open data terms. The card's icons and the integration icon are made from the weather icons of the [Home Assistant frontend](https://github.com/home-assistant/frontend) (Apache License 2.0). KNMI is a name of the Dutch national weather service and is used here only to identify the data source.

## License

MIT, see [LICENSE](LICENSE).
