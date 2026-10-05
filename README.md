# Weerbericht for Home Assistant

A Home Assistant integration that shows the Dutch weather exactly as the official KNMI app shows it, for any location in the Netherlands, plus the national rain radar.

It reads the same backend the KNMI app uses (`api.app.knmi.cloud`, published as open source by KNMI). That gives you the KNMI meteorologists' forecast itself, not a third-party forecast built from KNMI data. No API key, no account.

Weerbericht is an independent project. It is not made by, endorsed by, or affiliated with KNMI. The weather data is produced by KNMI (Koninklijk Nederlands Meteorologisch Instituut).

## What you get

For each configured location:

- A `weather` entity with the current weather, an hourly forecast (about 60 hours) and a daily forecast (7 days with weather type, plus 8 more days from the 14-day outlook with temperature and precipitation only). Values match the KNMI app: temperature, precipitation amount and chance, wind speed and gusts in km/h, wind direction, UV index.
- Sensors: temperature now, maximum and minimum of today, precipitation today, hours of sunshine today, UV index, heat index (hittekracht), weather alert level, weather alert text, and a Dutch weather description ("Opklaringen", "Lichte bui, afgewisseld door zon", ...).
- A `camera` entity with the animated rain radar of the Netherlands (the loop published on knmi.nl, a new image every 5 minutes).
- A **Weerbericht card** for your dashboard. It looks like Home Assistant's own weather card, but shows every KNMI app weather type: showers, thunder, snow and hail with the sun or the moon behind the cloud, and a moon instead of a sun after sunset. It is installed together with the integration, no separate download.

The weather alert sensors follow the KNMI code colours: `none`, `yellow`, `orange`, `red`. The alert text sensor holds the KNMI warning text, or "Geen waarschuwingen" when there is none, so it can be shown on a dashboard tile directly.

## Installation

### HACS (custom repository)

1. In HACS, open the menu (three dots, top right) and choose **Custom repositories**.
2. Add `https://github.com/milamaja/ha-weerbericht` with category **Integration**.
3. Install **Weerbericht** and restart Home Assistant.

### Manual

1. Copy the folder `custom_components/weerbericht` into the `custom_components` folder of your Home Assistant configuration directory.
2. Restart Home Assistant.

## Configuration

Go to **Settings, Devices & services, Add integration** and search for **Weerbericht**. Fill in:

- **Name**: used for the device and the entity IDs, for example `Weerbericht`.
- **Latitude / Longitude**: default to your home location. The forecast is per grid cell of roughly 9 km, the same cells the app uses.
- **Warning region**: the province used for weather alerts.

You can add the integration more than once for several locations.

## Dashboard examples

Entity IDs depend on the name you gave the integration and on your Home Assistant language. The examples use the name `Weerbericht` with an English UI; check your own IDs on the device page.

### Weerbericht card

After installing, refresh your browser once. Then add the card from the card picker (search for "Weerbericht"), or in YAML:

```yaml
type: custom:weerbericht-card
entity: weather.weerbericht
forecast_type: daily      # or hourly
name: Thuis               # optional
forecast_slots: 5         # optional, otherwise as many as fit
```

It also supports `show_current: false`, `show_forecast: false`, `round_temperature: true` and a `tap_action` (`more-info`, `navigate`, `url` or `none`). With a Dutch Home Assistant the condition is shown in the KNMI wording ("Opklaringen", "Lichte bui, afgewisseld door zon").

Home Assistant's built-in weather card and the entity popup work too, but they have no pictures for showers with sun, and they draw partly cloudy with a sun even at night. The entity always reports the real KNMI condition; only the Weerbericht card and the entity icon show the moon behind a cloud.

### Weather alert tiles

```yaml
type: grid
columns: 1
cards:
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
- The radar image is fetched only when a dashboard asks for it, and cached for 5 minutes.

## Limitations

- Netherlands only, like the app.
- The app backend is a public but undocumented API without a stability promise. If KNMI changes it, this integration needs an update. The official KNMI Data Platform APIs do not offer the app's forecast.
- Current values (temperature, wind) are the app's nowcast for your cell, not a station measurement. For station observations use the KNMI Data Platform EDR API with a registered key.

## Attribution

Weather data and radar image: KNMI (Koninklijk Nederlands Meteorologisch Instituut), available under their open data terms. The card's icons are combined from the weather icons of the [Home Assistant frontend](https://github.com/home-assistant/frontend) (Apache License 2.0). KNMI is a name of the Dutch national weather service and is used here only to identify the data source.

## License

MIT, see [LICENSE](LICENSE).
