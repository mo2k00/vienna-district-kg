import { api } from "./api.js";
import { el } from "./dom.js";

const SCALE = ["#eef6f4", "#c6e4de", "#8fcbbf", "#4fa596", "#1c7a6c", "#0a4f47"];
const NEUTRAL = "#e3e7e4";
const EXCLUDED = "#c9ceca";
const BASEMAP =
  "https://mapsneu.wien.gv.at/basemap/bmapgrau/normal/google3857/{z}/{y}/{x}.png";

export const districtId = (number) => `d${String(number).padStart(2, "0")}`;

export class DistrictMap {
  constructor(container, { onSelect, onHover } = {}) {
    this.map = L.map(container, { scrollWheelZoom: false, zoomSnap: 0.25 });
    L.tileLayer(BASEMAP, {
      maxZoom: 18,
      attribution: 'Basemap: <a href="https://basemap.at">basemap.at</a>',
    }).addTo(this.map);
    this.onSelect = onSelect;
    this.onHover = onHover;
    this.values = {};
    this.excluded = new Set();
    this.highlighted = new Set();
    this.selected = null;
    this.options = { min: 0, max: 1, format: (v) => v, title: "" };
    this.info = this.#infoControl();
    this.legend = this.#legendControl();
  }

  async load() {
    const shapes = await api.shapes();
    await new Promise(requestAnimationFrame);
    this.map.invalidateSize();
    this.layer = L.geoJSON(shapes, {
      style: (feature) => this.#style(feature),
      onEachFeature: (feature, layer) => this.#bind(feature, layer),
    }).addTo(this.map);
    this.#fit();
    this.resizeObserver = new ResizeObserver(() => {
      this.map.invalidateSize();
      this.#fit();
    });
    this.resizeObserver.observe(this.map.getContainer());
    return this;
  }

  #fit() {
    if (this.layer) this.map.fitBounds(this.layer.getBounds(), { padding: [6, 6] });
  }

  setValues(values, { min, max, format, title, excluded = [], reverse = false } = {}) {
    const numbers = Object.values(values);
    this.values = values;
    this.excluded = new Set(excluded);
    this.options = {
      min: min ?? Math.min(...numbers),
      max: max ?? Math.max(...numbers),
      format: format ?? ((v) => v),
      title: title ?? "",
      reverse,
    };
    this.#restyle();
    this.#renderLegend();
  }

  select(id) {
    this.selected = id;
    this.#restyle();
  }

  highlight(ids) {
    this.highlighted = new Set(ids);
    this.#restyle();
  }

  destroy() {
    this.resizeObserver?.disconnect();
    this.map.remove();
  }

  #colour(id) {
    if (this.excluded.has(id)) return EXCLUDED;
    const value = this.values[id];
    if (value === undefined) return NEUTRAL;
    const { min, max, reverse } = this.options;
    let t = max === min ? 1 : (value - min) / (max - min);
    if (reverse) t = 1 - t;
    return SCALE[Math.min(SCALE.length - 1, Math.max(0, Math.round(t * (SCALE.length - 1))))];
  }

  #style(feature) {
    const id = districtId(feature.properties.district);
    const selected = id === this.selected;
    const highlighted = this.highlighted.has(id);
    return {
      fillColor: this.#colour(id),
      fillOpacity: this.excluded.has(id) ? 0.55 : 0.78,
      color: selected ? "#b7682a" : highlighted ? "#1c2521" : "#ffffff",
      weight: selected ? 3.5 : highlighted ? 2.5 : 1.2,
      dashArray: this.excluded.has(id) ? "4 3" : null,
    };
  }

  #restyle() {
    this.layer?.setStyle((feature) => this.#style(feature));
    if (this.selected) {
      this.layer?.eachLayer((layer) => {
        if (districtId(layer.feature.properties.district) === this.selected) layer.bringToFront();
      });
    }
  }

  #bind(feature, layer) {
    const id = districtId(feature.properties.district);
    layer.bindTooltip(String(feature.properties.district), {
      permanent: true,
      direction: "center",
      className: "district-label",
    });
    layer.on({
      click: () => this.onSelect?.(id),
      mouseover: () => {
        layer.setStyle({ weight: 3, color: "#1c2521" });
        this.#showInfo(feature, id);
        this.onHover?.(id);
      },
      mouseout: () => {
        layer.setStyle(this.#style(feature));
        this.#showInfo(null);
        this.onHover?.(null);
      },
    });
  }

  #infoControl() {
    const control = L.control({ position: "topright" });
    control.onAdd = () => (this.infoNode = el("div", { class: "legend" }, "Hover a district"));
    control.addTo(this.map);
    return control;
  }

  #showInfo(feature, id) {
    if (!this.infoNode) return;
    if (!feature) {
      this.infoNode.textContent = "Hover a district";
      return;
    }
    const value = this.values[id];
    const detail = this.excluded.has(id)
      ? "excluded"
      : value === undefined
        ? ""
        : `${this.options.title}: ${this.options.format(value)}`;
    this.infoNode.replaceChildren(
      el("strong", {}, `${feature.properties.district}. ${feature.properties.name}`),
      detail ? el("div", {}, detail) : "",
    );
  }

  #legendControl() {
    const control = L.control({ position: "bottomleft" });
    control.onAdd = () => (this.legendNode = el("div", { class: "legend", hidden: true }));
    control.addTo(this.map);
    return control;
  }

  #renderLegend() {
    const { min, max, format, title, reverse } = this.options;
    const colours = reverse ? [...SCALE].reverse() : SCALE;
    this.legendNode.hidden = false;
    this.legendNode.replaceChildren(
      el("div", {}, title),
      el("div", { class: "legend__scale" }, colours.map((c) => el("span", { style: `background:${c}` }))),
      el("div", { class: "legend__labels" }, el("span", {}, format(min)), el("span", {}, format(max))),
    );
  }
}
