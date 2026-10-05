/*
 * Weerbericht card: Home Assistant's weather card look, with the weather types
 * of the KNMI app that Home Assistant has no picture for (showers with sun or
 * moon, thunder, snow and hail showers, and a moon for clear and partly cloudy
 * nights).
 *
 * The icon shapes and colours are taken from the Home Assistant frontend
 * (src/data/weather.ts, Apache License 2.0) and combined here.
 *
 * Generated from tools/weerbericht-card.template.js by tools/build_card.py. Do not edit.
 */

const P = {
  "sun": "m 14.39303,8.4033507 c 0,3.3114723 -2.684145,5.9956173 -5.9956169,5.9956173 -3.3114716,0 -5.9956168,-2.684145 -5.9956168,-5.9956173 0,-3.311471 2.6841452,-5.995617 5.9956168,-5.995617 3.3114719,0 5.9956169,2.684146 5.9956169,5.995617",
  "moon": "m 13.502891,11.382935 c -1.011285,1.859223 -2.976664,3.121381 -5.2405751,3.121381 -3.289929,0 -5.953329,-2.663833 -5.953329,-5.9537625 0,-2.263911 1.261724,-4.228856 3.120948,-5.240575 -0.452782,0.842738 -0.712753,1.806363 -0.712753,2.832381 0,3.289928 2.663833,5.9533275 5.9533291,5.9533275 1.026017,0 1.989641,-0.259969 2.83238,-0.712752",
  "smallSun": "m14.981 4.2112c0 1.9244-1.56 3.4844-3.484 3.4844-1.9244 0-3.4844-1.56-3.4844-3.4844s1.56-3.484 3.4844-3.484c1.924 0 3.484 1.5596 3.484 3.484",
  "cloudBack": "m3.8863 5.035c-0.54892 0.16898-1.04 0.46637-1.4372 0.8636-0.63077 0.63041-1.0206 1.4933-1.0206 2.455 0 1.9251 1.5589 3.4682 3.4837 3.4682h6.9688c1.9251 0 3.484-1.5981 3.484-3.5232 0-1.9251-1.5589-3.5232-3.484-3.5232h-1.0834c-0.25294-1.6916-1.6986-2.9083-3.4463-2.9083-1.7995 0-3.2805 1.4153-3.465 3.1679",
  "cloudFront": "m4.1996 7.6995c-0.33902 0.10407-0.64276 0.28787-0.88794 0.5334-0.39017 0.38982-0.63147 0.92322-0.63147 1.5176 0 1.1896 0.96414 2.1431 2.1537 2.1431h4.3071c1.1896 0 2.153-0.98742 2.153-2.1777 0-1.1896-0.96344-2.1777-2.153-2.1777h-0.66992c-0.15593-1.0449-1.0499-1.7974-2.1297-1.7974-1.112 0-2.0274 0.87524-2.1417 1.9586",
  "rain": [
    "m5.2852 14.734c-0.22401 0.24765-0.57115 0.2988-0.77505 0.11395-0.20391-0.1845-0.18732-0.53481 0.036689-0.78281 0.14817-0.16298 0.59126-0.32914 0.87559-0.42369 0.12453-0.04092 0.22684 0.05186 0.19791 0.17956-0.065617 0.2921-0.18732 0.74965-0.33514 0.91299",
    "m11.257 14.163c-0.22437 0.24765-0.57115 0.2988-0.77505 0.11395-0.2039-0.1845-0.18768-0.53481 0.03669-0.78281 0.14817-0.16298 0.59126-0.32914 0.8756-0.42369 0.12453-0.04092 0.22684 0.05186 0.19791 0.17956-0.06562 0.2921-0.18732 0.74965-0.33514 0.91299",
    "m8.432 15.878c-0.15452 0.17039-0.3937 0.20567-0.53446 0.07867-0.14041-0.12735-0.12876-0.36865 0.025753-0.53975 0.10195-0.11218 0.40711-0.22684 0.60325-0.29175 0.085725-0.02858 0.15628 0.03563 0.13652 0.12382-0.045508 0.20108-0.12912 0.51647-0.23107 0.629",
    "m7.9991 14.118c-0.19226 0.21237-0.49001 0.25612-0.66499 0.09737-0.17462-0.15804-0.16051-0.45861 0.03175-0.67098 0.12665-0.14005 0.50729-0.28293 0.75071-0.36336 0.10689-0.03563 0.19473 0.0441 0.17004 0.15346-0.056092 0.25082-0.16051 0.64347-0.28751 0.78352",
    "m10.648 16.448c-0.19226 0.21449-0.49001 0.25894-0.66499 0.09878-0.17498-0.16016-0.16087-0.4639 0.03175-0.67874 0.12665-0.14146 0.50694-0.2854 0.75071-0.36724 0.10689-0.03563 0.19473 0.0448 0.17004 0.15558-0.05645 0.25365-0.16051 0.65017-0.28751 0.79163",
    "m5.9383 16.658c-0.22437 0.25012-0.5715 0.30162-0.77505 0.11501-0.20391-0.18627-0.18768-0.54046 0.036689-0.79093 0.14817-0.1651 0.59126-0.33267 0.87559-0.42827 0.12418-0.04127 0.22648 0.05221 0.19791 0.18168-0.065617 0.29528-0.18732 0.75741-0.33514 0.92251"
  ],
  "windy": [
    "m 13.59616,15.30968 c 0,0 -0.09137,-0.0071 -0.250472,-0.0187 -0.158045,-0.01235 -0.381353,-0.02893 -0.64382,-0.05715 -0.262466,-0.02716 -0.564444,-0.06385 -0.877358,-0.124531 -0.156986,-0.03034 -0.315383,-0.06844 -0.473781,-0.111478 -0.157691,-0.04551 -0.313266,-0.09842 -0.463902,-0.161219 l -0.267406,-0.0949 c -0.09984,-0.02646 -0.205669,-0.04904 -0.305153,-0.06738 -0.193322,-0.02716 -0.3838218,-0.03316 -0.5640912,-0.02011 -0.3626556,0.02611 -0.6847417,0.119239 -0.94615,0.226483 -0.2617611,0.108656 -0.4642556,0.230364 -0.600075,0.324203 -0.1358195,0.09419 -0.2049639,0.160514 -0.2049639,0.160514 0,0 0.089958,-0.01623 0.24765,-0.04445 0.1559278,-0.02575 0.3764139,-0.06174 0.6367639,-0.08714 0.2596444,-0.02646 0.5591527,-0.0441 0.8678333,-0.02328 0.076905,0.0035 0.1538111,0.01658 0.2321278,0.02293 0.077611,0.01058 0.1534581,0.02893 0.2314221,0.04022 0.07267,0.01834 0.1397,0.03986 0.213078,0.05644 l 0.238125,0.08925 c 0.09207,0.03281 0.183444,0.07055 0.275872,0.09878 0.09243,0.0261 0.185208,0.05327 0.277636,0.07161 0.184856,0.0388 0.367947,0.06174 0.543983,0.0702 0.353131,0.01905 0.678745,-0.01341 0.951442,-0.06456 0.27305,-0.05292 0.494595,-0.123119 0.646642,-0.181681 0.152047,-0.05785 0.234597,-0.104069 0.234597,-0.104069",
    "m 4.7519154,13.905801 c 0,0 0.091369,-0.0032 0.2511778,-0.0092 0.1580444,-0.0064 0.3820583,-0.01446 0.6455833,-0.03281 0.2631722,-0.01729 0.5662083,-0.04269 0.8812389,-0.09137 0.1576916,-0.02434 0.3175,-0.05609 0.4776611,-0.09384 0.1591027,-0.03951 0.3167944,-0.08643 0.4699,-0.14358 l 0.2702277,-0.08467 c 0.1008945,-0.02222 0.2074334,-0.04127 0.3072695,-0.05574 0.1943805,-0.01976 0.3848805,-0.0187 0.5651499,0.0014 0.3608917,0.03951 0.67945,0.144639 0.936625,0.261761 0.2575278,0.118534 0.4554364,0.247297 0.5873754,0.346781 0.132291,0.09913 0.198966,0.168275 0.198966,0.168275 0,0 -0.08925,-0.01976 -0.245886,-0.05397 C 9.9423347,14.087088 9.7232597,14.042988 9.4639681,14.00736 9.2057347,13.97173 8.9072848,13.94245 8.5978986,13.95162 c -0.077258,7.06e-4 -0.1541638,0.01058 -0.2328333,0.01411 -0.077964,0.0078 -0.1545166,0.02328 -0.2331861,0.03175 -0.073025,0.01588 -0.1404055,0.03422 -0.2141361,0.04798 l -0.2420055,0.08008 c -0.093486,0.02963 -0.1859139,0.06421 -0.2794,0.0889 C 7.3028516,14.23666 7.2093653,14.2603 7.116232,14.27512 6.9303181,14.30722 6.7465209,14.3231 6.5697792,14.32486 6.2166487,14.33046 5.8924459,14.28605 5.6218654,14.224318 5.3505793,14.161565 5.1318571,14.082895 4.9822793,14.01869 4.8327015,13.95519 4.7519154,13.905801 4.7519154,13.905801"
  ],
  "snow": [
    "m 8.4319893,15.348341 c 0,0.257881 -0.209197,0.467079 -0.467078,0.467079 -0.258586,0 -0.46743,-0.209198 -0.46743,-0.467079 0,-0.258233 0.208844,-0.467431 0.46743,-0.467431 0.257881,0 0.467078,0.209198 0.467078,0.467431",
    "m 11.263878,14.358553 c 0,0.364067 -0.295275,0.659694 -0.659695,0.659694 -0.364419,0 -0.6596937,-0.295627 -0.6596937,-0.659694 0,-0.364419 0.2952747,-0.659694 0.6596937,-0.659694 0.36442,0 0.659695,0.295275 0.659695,0.659694",
    "m 5.3252173,13.69847 c 0,0.364419 -0.295275,0.660047 -0.659695,0.660047 -0.364067,0 -0.659694,-0.295628 -0.659694,-0.660047 0,-0.364067 0.295627,-0.659694 0.659694,-0.659694 0.36442,0 0.659695,0.295627 0.659695,0.659694"
  ],
  "bolt": "m 9.9252695,10.935875 -1.6483986,2.341014 1.1170184,0.05929 -1.2169864,2.02141 3.0450261,-2.616159 H 9.8864918 L 10.97937,11.294651 10.700323,10.79794 h -0.508706 l -0.2663475,0.137936"
};

const CARD_VERSION = "1.0.0";

// KNMI app weather type -> [sky, precipitation, lightning, night]
//   sky: sun | moon | part | cloud | fog | windy
//   precipitation: rain1 (light) | rain2 | rain3 (heavy) | snow1 | snow2 | snow3 | sleet | hail | ""
const T = {
  1364: ["cloud", "sleet"], 1365: ["sun"], 1366: ["cloud", "rain3"], 1367: ["cloud", "snow3"],
  1368: ["cloud", "", 1], 1369: ["windy"], 1370: ["fog"], 1371: ["cloud", "rain3"],
  1372: ["sun"], 1373: ["moon"], 1374: ["cloud"], 1375: ["part"], 1376: ["part", "", 0, 1],
  1377: ["cloud", "rain1"], 1378: ["cloud", "rain2"], 1379: ["cloud", "rain3"],
  1380: ["part", "rain1"], 1381: ["part", "rain1", 0, 1],
  1382: ["part", "rain2"], 1383: ["part", "rain2", 0, 1],
  1384: ["part", "rain3"], 1385: ["part", "rain3", 0, 1],
  1386: ["cloud", "rain1"], 1387: ["part", "rain1"], 1388: ["part", "rain1", 0, 1],
  1389: ["cloud", "rain2", 1], 1390: ["cloud", "rain3", 1],
  1391: ["part", "rain2", 1], 1392: ["part", "rain2", 1, 1],
  1393: ["part", "rain3", 1], 1394: ["part", "rain3", 1, 1],
  1395: ["cloud", "hail", 1], 1396: ["part", "hail", 1], 1397: ["part", "hail", 1, 1],
  1398: ["cloud", "sleet", 1], 1399: ["part", "sleet", 1], 1400: ["part", "sleet", 1, 1],
  1401: ["cloud", "snow2", 1], 1402: ["part", "snow2", 1], 1403: ["part", "snow2", 1, 1],
  1404: ["cloud", "snow1"], 1405: ["part", "snow1"], 1406: ["part", "snow1", 0, 1],
  1407: ["cloud", "snow2"], 1408: ["part", "snow2"], 1409: ["part", "snow2", 0, 1],
  1410: ["cloud", "snow3"], 1411: ["part", "snow3"], 1412: ["part", "snow3", 0, 1],
  1413: ["cloud", "sleet"], 1414: ["part", "sleet"], 1415: ["part", "sleet", 0, 1],
  1416: ["cloud", "hail"], 1417: ["part", "hail"], 1418: ["part", "hail", 0, 1],
  1419: ["cloud", "sleet"], 1420: ["fog"], 1421: ["fog"], 1422: ["fog"],
  1423: ["windy"], 1424: ["windy"], 1425: ["windy"],
};

// Home Assistant conditions, used when an entity has no KNMI weather type.
const BY_CONDITION = {
  sunny: ["sun"], "clear-night": ["moon"], partlycloudy: ["part"], cloudy: ["cloud"],
  fog: ["fog"], rainy: ["cloud", "rain2"], pouring: ["cloud", "rain3"],
  snowy: ["cloud", "snow3"], "snowy-rainy": ["cloud", "sleet"], hail: ["cloud", "hail"],
  lightning: ["cloud", "", 1], "lightning-rainy": ["cloud", "rain2", 1],
  windy: ["windy"], "windy-variant": ["windy"], exceptional: ["cloud"],
};

const path = (cls, d, extra = "") => `<path class="${cls}" d="${d}"${extra}/>`;
// The crescent of clear-night, mirrored and scaled into the spot of the partly-cloudy sun.
const SMALL_MOON = `<g transform="translate(17.2 -2.2) scale(-0.72 0.72) rotate(20 8 8)">${path("moon", P.moon)}</g>`;
const FOG_LINES =
  '<rect class="cloud-back" x="2.2" y="12.6" width="12.4" height="0.9" rx="0.45"/>' +
  '<rect class="cloud-back" x="3.6" y="14.4" width="9.6" height="0.9" rx="0.45"/>';

function precipitation(kind) {
  switch (kind) {
    case "rain1": return path("rain", P.rain[3]) + path("rain", P.rain[1]);
    case "rain2": return P.rain.slice(0, 4).map((d) => path("rain", d)).join("");
    case "rain3": return P.rain.map((d) => path("rain", d)).join("");
    case "snow1": return path("snow", P.snow[0]) + path("snow", P.snow[1]);
    case "snow2":
    case "snow3": return P.snow.map((d) => path("snow", d)).join("");
    case "sleet": return path("snow", P.snow[2]) + path("snow", P.snow[1]) + path("rain", P.rain[2]) + path("rain", P.rain[3]);
    case "hail": return P.snow.map((d) => path("hail", d)).join("");
    default: return "";
  }
}

function iconSVG(spec, night) {
  const [sky, precip = "", bolt = 0, isNight = 0] = spec;
  const dark = night || isNight;
  let out = "";
  if (sky === "sun") out += dark ? path("moon", P.moon) : path("sun", P.sun);
  else if (sky === "moon") out += path("moon", P.moon);
  else if (sky === "part") out += dark ? SMALL_MOON : path("sun", P.smallSun);
  if (sky !== "sun" && sky !== "moon") {
    out += path("cloud-back", P.cloudBack) + path("cloud-front", P.cloudFront);
  }
  if (sky === "windy") out += path("cloud-back", P.windy[0]) + path("cloud-back", P.windy[1]);
  if (sky === "fog") out += FOG_LINES;
  out += precipitation(precip);
  if (bolt) out += path("sun", P.bolt);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 17 17">${out}</svg>`;
}

function iconFor(code, condition, night) {
  const spec = T[code] || BY_CONDITION[condition] || ["cloud"];
  return iconSVG(spec, night);
}

const STYLE = `
  :host { display: block; height: 100%; }
  ha-card { cursor: pointer; height: 100%; display: flex; flex-direction: column;
    justify-content: center; box-sizing: border-box; padding: 16px 0; }
  .content { display: flex; flex-wrap: nowrap; justify-content: space-between;
    align-items: center; padding: 0 16px; }
  .content + .forecast { padding-top: 16px; }
  .icon-image { display: flex; align-items: center; min-width: 64px; margin-inline-end: 16px; }
  .icon-image > svg { flex: 0 0 64px; height: 64px; width: 64px; }
  .info { display: flex; justify-content: space-between; flex-grow: 1; overflow: hidden; }
  .name-state { overflow: hidden; padding-inline-end: 12px; width: 100%; }
  .state, .temp-attribute .temp { font-size: var(--ha-font-size-3xl, 28px);
    line-height: var(--ha-line-height-condensed, 1.2); }
  .name, .attribute { font-size: var(--ha-font-size-m, 14px);
    line-height: var(--ha-line-height-condensed, 1.2); }
  .name, .state { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .temp-attribute { text-align: end; }
  .temp-attribute .temp { position: relative; margin-right: 24px; direction: ltr; white-space: nowrap; }
  .temp-attribute .temp span { position: absolute; font-size: var(--ha-font-size-2xl, 24px); top: 1px; }
  .attribute { white-space: nowrap; direction: ltr; }
  .attribute, .templow, .name { color: var(--secondary-text-color); }
  .forecast { display: flex; justify-content: space-around; padding: 0 16px; overflow: hidden; }
  .forecast-item { display: flex; flex-direction: column; align-items: center; text-align: center;
    min-width: 48px; padding: 0 8px; flex: 0 0 auto; gap: var(--ha-space-1, 4px); }
  .forecast-item-label, .forecast .temp { line-height: 1; white-space: nowrap; }
  .forecast-item-label { color: var(--secondary-text-color); font-size: var(--ha-font-size-s, 12px); }
  .forecast .temp { font-size: var(--ha-font-size-l, 16px); }
  .forecast-image-icon { padding-top: 6px; padding-bottom: 6px; display: flex; justify-content: center; }
  .forecast-image-icon > svg { width: 40px; height: 40px; }
  .rain { fill: var(--weather-icon-rain-color, #30b3ff); }
  .sun { fill: var(--weather-icon-sun-color, #fdd93c); }
  .moon { fill: var(--weather-icon-moon-color, #fcf497); }
  .cloud-back { fill: var(--weather-icon-cloud-back-color, #d4d4d4); }
  .cloud-front { fill: var(--weather-icon-cloud-front-color, #f9f9f9); }
  .snow { fill: var(--weather-icon-snow-color, #f9f9f9); }
  .hail { fill: var(--weather-icon-hail-color, #d4e8f5); }
  .unavailable { height: 100px; display: flex; justify-content: center; align-items: center;
    font-size: var(--ha-font-size-l, 16px); }
`;

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

class WeerberichtCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._forecast = null;
    this._unsub = null;
    this._width = 0;
  }

  static getStubConfig(hass) {
    const entity =
      Object.keys(hass.states).find((e) => e.startsWith("weather.") &&
        hass.states[e].attributes.attribution === "Bron: KNMI") ||
      Object.keys(hass.states).find((e) => e.startsWith("weather.")) || "";
    return { entity, forecast_type: "daily" };
  }

  _fail(where, err) {
    const msg = `${where}: ${err && err.message ? err.message : err}`;
    console.error("weerbericht-card", msg, err);
    if (this._hass && !this._reported) {
      this._reported = true;
      this._hass.callWS({
        type: "system_log/write",
        logger: "custom_components.weerbericht.card",
        level: "error",
        message: `weerbericht-card ${CARD_VERSION} ${navigator.userAgent}: ${msg}
${(err && err.stack) || ""}`,
      }).catch(() => {});
    }
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="unavailable" style="padding:16px;text-align:center">Weerbericht card error: ${esc(msg)}</div></ha-card>`;
  }

  setConfig(config) {
    if (!config || !config.entity || !String(config.entity).startsWith("weather.")) {
      throw new Error("Set 'entity' to a weather entity");
    }
    const changed = !this._config || this._config.entity !== config.entity ||
      this._config.forecast_type !== config.forecast_type;
    this._config = { forecast_type: "daily", show_forecast: true, show_current: true, ...config };
    try {
      if (changed) {
        this._forecast = null;
        this._unsubscribe();
        if (this._hass) this._subscribe();
      }
      this._render();
    } catch (err) {
      this._fail("setConfig", err);
    }
  }

  set hass(hass) {
    this._hass = hass;
    try {
      if (!this._unsub) this._subscribe();
      this._render();
    } catch (err) {
      this._fail("render", err);
    }
  }

  connectedCallback() {
    if (!this._ro) {
      this._ro = new ResizeObserver((entries) => {
        const w = Math.round(entries[0].contentRect.width);
        if (w !== this._width) { this._width = w; this._render(); }
      });
    }
    this._ro.observe(this);
    if (this._hass && !this._unsub) this._subscribe();
  }

  disconnectedCallback() {
    if (this._ro) this._ro.disconnect();
    this._unsubscribe();
  }

  _subscribe() {
    if (!this._hass || !this._config || this._unsub || this._config.show_forecast === false) return;
    this._unsub = this._hass.connection
      .subscribeMessage((event) => {
        this._forecast = event.forecast || [];
        try { this._render(); } catch (err) { this._fail("forecast", err); }
      }, {
        type: "weather/subscribe_forecast",
        entity_id: this._config.entity,
        forecast_type: this._config.forecast_type,
      })
      .catch((err) => { this._unsub = null; this._forecastError = err?.message || String(err); this._render(); });
  }

  _unsubscribe() {
    if (this._unsub) {
      Promise.resolve(this._unsub).then((fn) => typeof fn === "function" && fn()).catch(() => {});
      this._unsub = null;
    }
  }

  getCardSize() { return this._config?.show_forecast === false ? 2 : 4; }

  getGridOptions() {
    const rows = 1 + (this._config?.show_current !== false ? 1 : 0) +
      (this._config?.show_forecast !== false ? (this._config?.forecast_type === "daily" ? 2 : 1) : 0);
    return { columns: 12, rows, min_columns: 5, min_rows: rows - 1 };
  }

  _stateText(stateObj) {
    const a = stateObj.attributes;
    const cond = a.raw_condition || stateObj.state;
    const lang = this._hass.locale?.language || this._hass.language || "en";
    if (lang.startsWith("nl") && a.weather_text) return a.weather_text;
    const key = `component.weather.entity_component._.state.${cond}`;
    return this._hass.localize(key) || this._hass.formatEntityState?.(stateObj) || cond;
  }

  _fmt(n, digits) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return "";
    return Number(n).toLocaleString(this._hass.locale?.language || undefined, {
      maximumFractionDigits: digits,
    });
  }

  _label(item) {
    const d = new Date(item.datetime);
    const lang = this._hass.locale?.language || undefined;
    const tz = this._hass.locale?.time_zone === "server" ? this._hass.config.time_zone : undefined;
    if (this._config.forecast_type === "hourly") {
      return d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit", timeZone: tz });
    }
    return d.toLocaleDateString(lang, { weekday: "short", timeZone: tz });
  }

  _tap() {
    const action = this._config.tap_action || { action: "more-info" };
    switch (action.action) {
      case "none":
        return;
      case "navigate":
        if (action.navigation_path) {
          history.pushState(null, "", action.navigation_path);
          window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
        }
        return;
      case "url":
        if (action.url_path) window.open(action.url_path, "_blank", "noopener");
        return;
      default: {
        const ev = new Event("hass-more-info", { bubbles: true, composed: true });
        ev.detail = { entityId: action.entity || this._config.entity };
        this.dispatchEvent(ev);
      }
    }
  }

  _render() {
    if (!this._config || !this._hass) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj || stateObj.state === "unavailable") {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="unavailable">${
        esc(this._hass.localize("ui.card.weather.attributes.unavailable") || "Unavailable")}</div></ha-card>`;
      return;
    }
    const a = stateObj.attributes;
    const digits = this._config.round_temperature ? 0 : undefined;
    const unit = a.temperature_unit || this._hass.config.unit_system?.temperature || "°C";
    const name = this._config.name ?? a.friendly_name ?? this._config.entity;
    const night = a.night === true;
    const forecast = this._forecast || [];
    const daily = this._config.forecast_type !== "hourly";
    let high = a.today_high, low = a.today_low;
    if (high === undefined && daily && forecast[0]) { high = forecast[0].temperature; low = forecast[0].templow; }

    let current = "";
    if (this._config.show_current !== false) {
      current = `
        <div class="content">
          <div class="icon-image">${iconFor(a.weather_type, a.raw_condition || stateObj.state, night)}</div>
          <div class="info">
            <div class="name-state">
              <div class="state">${esc(this._stateText(stateObj))}</div>
              <div class="name" title="${esc(name)}">${esc(name)}</div>
            </div>
            <div class="temp-attribute">
              <div class="temp">${a.temperature != null ? `${this._fmt(a.temperature, digits)}&nbsp;<span>${esc(unit)}</span>` : "&nbsp;"}</div>
              <div class="attribute">${high != null ? `${this._fmt(high, digits)} ${esc(unit)}` : ""}${
                low != null ? ` / ${this._fmt(low, digits)} ${esc(unit)}` : ""}</div>
            </div>
          </div>
        </div>`;
    }

    let fc = "";
    if (this._config.show_forecast !== false && forecast.length) {
      const fit = this._width ? Math.max(1, Math.floor((this._width - 32) / 64)) : 5;
      const slots = Math.min(this._config.forecast_slots || fit, fit, forecast.length);
      const items = forecast.slice(0, slots).map((item) => {
        const itemNight = item.is_daytime === false;
        return `
          <div class="forecast-item">
            <div class="forecast-item-label">${esc(this._label(item))}</div>
            <div class="forecast-image-icon">${iconFor(item.weather_type, item.condition, itemNight)}</div>
            <div class="temp">${item.temperature != null ? `${this._fmt(item.temperature, digits)}°` : "-"}</div>
            <div class="templow">${item.templow != null ? `${this._fmt(item.templow, digits)}°` : daily ? "-" : ""}</div>
          </div>`;
      }).join("");
      fc = `<div class="forecast">${items}</div>`;
    }

    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card>${current}${fc}</ha-card>`;
    this.shadowRoot.querySelector("ha-card").addEventListener("click", () => this._tap());
  }
}

// Home Assistant installs a scoped custom element registry polyfill (needed in
// Firefox) while the page loads. A definition made before that is invisible to
// the polyfilled registry, so register again on whatever registry is current
// until Home Assistant can see the card. Each attempt uses a fresh subclass,
// because a registry refuses a constructor it has seen before.
const TAG = "weerbericht-card";
function register() {
  const registry = window.customElements;
  if (registry.get(TAG)) return;
  try {
    registry.define(TAG, class extends WeerberichtCard {});
  } catch (err) {
    console.warn("weerbericht-card: define failed", err);
  }
}
register();
window.addEventListener("load", register);
for (const ms of [250, 1000, 2500, 5000, 10000, 30000]) setTimeout(register, ms);

if (!window.__weerberichtCardAnnounced) {
  window.__weerberichtCardAnnounced = true;
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: TAG,
    name: "Weerbericht",
    description: "Weather card with the KNMI app weather types, including night and shower icons.",
    preview: true,
    documentationURL: "https://github.com/milamaja/ha-weerbericht",
  });
  console.info(`%c WEERBERICHT-CARD %c ${CARD_VERSION} `, "color:#fff;background:#30b3ff", "");
}
