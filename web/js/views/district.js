import { api } from "../api.js";
import { districtTitle, el, formatFeature, formatNumber, levelBadge, loading, notice, ordinal } from "../dom.js";
import { DistrictMap } from "../map.js";

const KEY_FEATURES = ["population_density", "minutes_to_centre", "park_share", "avg_age", "net_income"];

export async function render(root, { meta, navigate, params }) {
  const id = meta.districts.some((d) => d.id === params) ? params : "d01";
  const content = el("div", {}, loading());
  root.append(content);

  let district, similar;
  try {
    [district, similar] = await Promise.all([
      api.district(id),
      meta.similarity_sources.length ? api.similar(id, meta.similarity_sources[0], 5) : Promise.resolve([]),
    ]);
  } catch (error) {
    content.replaceChildren(notice(error.message, "error"));
    return () => {};
  }

  const features = Object.fromEntries(district.features.map((f) => [f.feature, f]));
  const mapNode = el("div", { class: "map map--small" });
  const picker = el(
    "select",
    { onChange: (e) => navigate(`district/${e.target.value}`), "aria-label": "Choose a district" },
    meta.districts.map((d) => el("option", { value: d.id, selected: d.id === id }, districtTitle(d))),
  );

  content.replaceChildren(
    el(
      "section",
      { class: "page-intro" },
      el("h3", {}, `${ordinal(district.number)} district`),
      el("h1", {}, district.name),
      el("div", { style: "max-width:320px" }, picker),
    ),
    el(
      "div",
      { class: "stack" },
      el(
        "div",
        { class: "facts" },
        fact(`${district.hub.name}`, "Main station (hub)"),
        fact(district.subway_lines.length ? district.subway_lines.join(" · ") : "none", "U-Bahn lines"),
        ...KEY_FEATURES.filter((f) => features[f]).map((f) =>
          fact(formatFeature(f, features[f].value), meta.feature_labels[f]),
        ),
      ),
      el(
        "div",
        { class: "grid-2" },
        el(
          "div",
          { class: "stack" },
          el("div", { class: "card" }, el("h2", {}, "What it offers"), offersList(district)),
          el("div", { class: "card" }, el("h2", {}, "Similar districts"), ...similarSection(similar, id)),
        ),
        el(
          "div",
          { class: "stack" },
          el("div", { class: "card" }, el("h2", {}, "Travel time by public transport"), mapNode, travelTimes(district, navigate)),
        ),
      ),
      el("div", { class: "card" }, el("h2", {}, "All facts"), featureTable(district, meta)),
      el("div", { class: "card" }, el("h2", {}, "Venues in the knowledge graph"), venues(district)),
    ),
  );

  const map = await new DistrictMap(mapNode, { onSelect: (other) => navigate(`district/${other}`) }).load();
  const times = Object.fromEntries(district.travel_times.map((t) => [t.district, t.minutes]));
  times[id] = 0;
  map.setValues(times, { min: 0, max: 45, format: (v) => `${v} min`, title: `Minutes from ${district.hub.name}`, reverse: true });
  map.select(id);
  map.highlight(district.neighbours.map((n) => n.id));

  return () => map.destroy();
}

function fact(value, label) {
  return el("div", { class: "fact" }, el("div", { class: "fact__value" }, value), el("div", { class: "fact__label" }, label));
}

function offersList(district) {
  if (!district.offers.length) return el("p", { class: "muted" }, "No preference is clearly offered here.");
  return el(
    "div",
    { class: "chips" },
    district.offers.map((o) =>
      el(
        "span",
        { class: "chip chip--in", title: o.evidence.map((e) => `${e.label}: ${e.level}`).join("\n") },
        "✓ ",
        o.label,
      ),
    ),
    el("p", { class: "small muted", style: "width:100%;margin-top:0.5rem" }, "Hover a label to see the evidence the rules used."),
  );
}

function similarList(similar) {
  if (!similar.length) return el("p", { class: "muted" }, "No embeddings available.");
  return el(
    "ol",
    {},
    similar.map((s) =>
      el(
        "li",
        {},
        el("a", { href: `#/district/${s.district}` }, s.name),
        el("span", { class: "muted small" }, ` · similarity ${s.similarity.toFixed(2)}`),
      ),
    ),
  );
}

function similarSection(similar, id) {
  return [similarList(similar), el("a", { href: `#/similar/${id}` }, "Compare embedding models →")];
}

function travelTimes(district, navigate) {
  const max = 45;
  return el(
    "div",
    { class: "times", style: "margin-top:0.75rem" },
    district.travel_times.slice(0, 10).map((t) =>
      el(
        "div",
        { class: "time-row" },
        el("a", { href: `#/district/${t.district}` }, t.name),
        el("div", { class: "bar" }, el("span", { style: `width:${(t.minutes / max) * 100}%` })),
        el("span", { class: "small" }, `${t.minutes} min`),
      ),
    ),
  );
}

function featureTable(district, meta) {
  return el(
    "div",
    { style: "overflow-x:auto" },
    el(
      "table",
      {},
      el("thead", {}, el("tr", {}, el("th", {}, "Feature"), el("th", {}, "Value"), el("th", {}, "Level"), el("th", {}, "Rank of 23"), el("th", {}, "Source"))),
      el(
        "tbody",
        {},
        district.features
          .slice()
          .sort((a, b) => a.label.localeCompare(b.label))
          .map((f) =>
            el(
              "tr",
              {},
              el("td", {}, f.label),
              el("td", { class: "num" }, formatFeature(f.feature, f.value)),
              el("td", {}, levelBadge(f.level)),
              el("td", {}, el("span", { class: "rank-dots", title: `${f.rank + 1} of 23 (ascending)` }, el("span", { style: `left:${(f.rank / 22) * 100}%` }))),
              el("td", { class: "small muted" }, f.source ? `${f.source} (${f.year})` : "derived by rules"),
            ),
          ),
      ),
    ),
  );
}

function venues(district) {
  const labels = {
    nightlife_venue: "Bars, pubs & clubs",
    food_venue: "Restaurants, cafés & markets",
    culture_venue: "Museums",
    childcare: "Kindergartens",
    school: "Schools",
    university: "University sites",
    playground: "Playgrounds",
    park: "Parks",
  };
  const entries = Object.entries(district.venues).map(([key, count]) => [
    key.startsWith("sport:") ? `${key.slice(6)[0].toUpperCase()}${key.slice(7)} venues` : labels[key] ?? key,
    count,
  ]);
  return el("div", { class: "chips" }, entries.map(([label, count]) => el("span", { class: "chip" }, `${label}: ${formatNumber(count)}`)));
}
