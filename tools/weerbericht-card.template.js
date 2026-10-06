/*
 * Weerbericht card: Home Assistant's weather card look, with the weather types
 * of the KNMI app that Home Assistant has no picture for (showers with sun or
 * moon, thunder, snow and hail showers, and a moon for clear and partly cloudy
 * nights).
 *
 * The icon shapes and colours are taken from the Home Assistant frontend
 * (src/data/weather.ts, Apache License 2.0) and combined here.
 *
 * Generated from tools/weerbericht-card.template.js by tools/build_card.py.
 */

const P = __PATHS__;

const CARD_VERSION = "__VERSION__";

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

// Glow along the edges of the dashboard while a KNMI weather warning is active
// (card option alert_glow). It is drawn BEHIND the cards: the glow element lives
// inside the dashboard's view container with z-index -1, and the container is
// made its own stacking context, so it only shows in the gaps and along the
// edges (placed after Home Assistant's own background layer). It stays below the top bar and right of the side menu.
const GLOW_CLASS = "weerbericht-alert-glow";
const GLOW_LEVELS = ["yellow", "orange", "red"];
const GLOW_RGB = { yellow: "255, 214, 0", orange: "255, 140, 0", red: "235, 35, 35" };
const glowOwners = new Map();
let glowEl = null;
let glowTimer = null;

function dashboardParts(card) {
  let node = card;
  for (let i = 0; node && i < 40; i++) {
    if (node.tagName === "HUI-ROOT" && node.shadowRoot) {
      const view = node.shadowRoot.getElementById("view");
      return view ? { view, header: node.shadowRoot.querySelector(".header") } : null;
    }
    node = node.parentNode || (node.getRootNode && node.getRootNode().host) || null;
  }
  return null;
}

function removeGlow() {
  if (glowEl) {
    glowEl.remove();
    glowEl = null;
  }
  if (glowTimer) {
    clearInterval(glowTimer);
    glowTimer = null;
  }
}

function positionGlow() {
  if (!glowEl || !glowEl._parts) return;
  const { view, header } = glowEl._parts;
  if (!view.isConnected) {
    removeGlow();
    return;
  }
  const v = view.getBoundingClientRect();
  const h = header ? header.getBoundingClientRect() : null;
  const top = h && h.height > 0 ? Math.max(0, h.bottom) : Math.max(0, v.top);
  const left = Math.max(0, v.left);
  const right = Math.min(window.innerWidth, v.right);
  Object.assign(glowEl.style, {
    left: left + "px",
    top: top + "px",
    width: Math.max(0, right - left) + "px",
    height: Math.max(0, window.innerHeight - top) + "px",
  });
}

function updateGlow() {
  let best = null;
  let anchor = null;
  for (const [card, level] of glowOwners) {
    if (level && (!best || GLOW_LEVELS.indexOf(level) > GLOW_LEVELS.indexOf(best))) {
      best = level;
      anchor = card;
    }
  }
  const parts = best ? dashboardParts(anchor) : null;
  if (!parts) {
    removeGlow();
    return;
  }
  if (!glowEl || glowEl._parts.view !== parts.view) {
    removeGlow();
    parts.view.style.isolation = "isolate";
    glowEl = document.createElement("div");
    glowEl.className = GLOW_CLASS;
    glowEl.setAttribute("aria-hidden", "true");
    Object.assign(glowEl.style, { position: "fixed", zIndex: "-1", pointerEvents: "none" });
    glowEl._parts = parts;
    // Home Assistant paints the dashboard background as its own z-index -1
    // layer (hui-view-background). Same layer, later in the page = on top, so
    // the glow goes right after it: above the background, below the cards.
    const background = parts.view.querySelector(":scope > hui-view-background");
    if (background) background.after(glowEl);
    else parts.view.prepend(glowEl);
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      glowEl.animate([{ opacity: 0.4 }, { opacity: 0.85 }, { opacity: 0.4 }], {
        duration: 3000, iterations: Infinity, easing: "ease-in-out",
      });
    }
    glowTimer = setInterval(positionGlow, 500);
  }
  const rgb = GLOW_RGB[best];
  glowEl.style.boxShadow = `inset 0 0 32px 8px rgba(${rgb}, 0.6), inset 0 0 6px 2px rgba(${rgb}, 0.75)`;
  glowEl.dataset.level = best;
  positionGlow();
}

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
    // Once attached, the dashboard can be found: place the glow now and once
    // more after Home Assistant has finished laying out the view.
    if (this._hass && this._config) {
      requestAnimationFrame(() => this._render());
      setTimeout(() => this._render(), 1000);
    }
  }

  disconnectedCallback() {
    if (this._ro) this._ro.disconnect();
    this._unsubscribe();
    if (glowOwners.delete(this)) updateGlow();
  }

  _updateGlow(stateObj) {
    const cfg = this._config || {};
    if (!cfg.alert_glow) {
      if (glowOwners.delete(this)) updateGlow();
      return;
    }
    let level = cfg.alert_glow_test;
    if (!level && cfg.alert_entity) level = this._hass.states[cfg.alert_entity]?.state;
    if (!level) level = stateObj?.attributes?.alert_level;
    level = String(level || "").toLowerCase();
    const next = GLOW_LEVELS.includes(level) ? level : null;
    glowOwners.set(this, next);
    // Always re-evaluate: when the card is first drawn it may not be attached
    // to the dashboard yet, so the glow has to be (re)placed on a later pass.
    updateGlow();
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
    this._updateGlow(stateObj);
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
