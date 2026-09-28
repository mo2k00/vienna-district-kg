import { el, formatNumber } from "../dom.js";

export async function render(root, { meta }) {
  const stats = meta.stats;
  const embeddings = meta.embeddings;
  root.append(
    el(
      "section",
      { class: "page-intro" },
      el("h1", {}, "About the knowledge graph"),
      el(
        "p",
        {},
        "A knowledge graph over Vienna's 23 districts built from open data. A rule layer derives what districts offer and how they are connected; an embedding layer learns how similar they are. This page shows how it is put together.",
      ),
    ),
    el(
      "div",
      { class: "stack" },
      el("div", { class: "card" }, el("h2", {}, "Pipeline"), pipeline()),
      el(
        "div",
        { class: "grid-2" },
        el("div", { class: "card" }, el("h2", {}, "Logic layer (Nemo)"), reasoningStats(stats)),
        el("div", { class: "card" }, el("h2", {}, "Embedding layer (PyKEEN)"), embeddingStats(embeddings)),
      ),
      el("div", { class: "card" }, el("h2", {}, "Data sources"), sources(meta)),
      el("div", { class: "card" }, el("h2", {}, "Limitations"), limitations()),
    ),
  );
  return () => {};
}

function pipeline() {
  const steps = [
    "Open data (City of Vienna, Wiener Linien, OSM)",
    "Ingest & record linkage",
    "Ground facts",
    "Rules: mapping, aggregation, levels, transit recursion",
    "Materialised KG",
    "Embeddings (TransE, RotatE)",
    "Per-request rules: preferences → recommendation objects",
    "Web app",
  ];
  return el(
    "div",
    { class: "pipeline" },
    steps.flatMap((step, i) => [
      el("span", { class: "pipeline__step" }, step),
      i < steps.length - 1 ? el("span", { class: "pipeline__arrow" }, "→") : "",
    ]),
  );
}

function reasoningStats(stats) {
  const exported = stats.exported ?? {};
  return el(
    "div",
    {},
    el(
      "div",
      { class: "facts" },
      fact(formatNumber(stats.derived_facts), "facts derived offline"),
      fact(`${stats.seconds} s`, "materialisation time"),
      fact(formatNumber(exported.feature ?? 0), "district features"),
      fact(formatNumber(exported.offers ?? 0), "“district offers …” facts"),
      fact(formatNumber(exported.sportVenue ?? 0), "sport venues after linkage"),
      fact(formatNumber(exported.locationConflict ?? 0), "records with conflicting district"),
    ),
    el(
      "p",
      { class: "small muted", style: "margin-top:0.75rem" },
      "Rules include a recursive venue taxonomy, record linkage by transitive closure, rank-based levels, line-aware transit reachability (recursive, 4 min per transfer, ≤ 45 min) and — per request — existential rules that create one recommendation object per district.",
    ),
  );
}

function embeddingStats(report) {
  if (!report) return el("p", { class: "muted" }, "Embeddings have not been trained yet.");
  const rows = Object.entries(report.models).map(([model, data]) => {
    const lp = data.link_prediction;
    const completion = report.completion?.[model];
    return el(
      "tr",
      {},
      el("td", {}, model, model === report.serving_model ? el("span", { class: "muted small" }, " (served)") : ""),
      el("td", { class: "num" }, `${lp.mrr.mean.toFixed(3)} ± ${lp.mrr.std.toFixed(3)}`),
      el("td", { class: "num" }, lp.hits_at_10.mean.toFixed(3)),
      el("td", { class: "num" }, data.vs_feature_baseline.spearman.toFixed(2)),
      el("td", { class: "num" }, completion ? `${Math.round(completion.accuracy * 100)} %` : "–"),
    );
  });
  return el(
    "div",
    {},
    el(
      "table",
      {},
      el("thead", {}, el("tr", {}, el("th", {}, "Model"), el("th", {}, "MRR"), el("th", {}, "Hits@10"), el("th", {}, "ρ vs. baseline"), el("th", {}, "Completion acc."))),
      el("tbody", {}, rows),
    ),
    el(
      "p",
      { class: "small muted", style: "margin-top:0.75rem" },
      `${report.triples} training triples, 5 seeds per model. Completion: hide 20 % of the level facts and predict them back (majority baseline ${Math.round(
        (Object.values(report.completion ?? {})[0]?.majority_baseline ?? 0) * 100,
      )} %).`,
    ),
  );
}

function sources(meta) {
  const years = meta.stats.metadata?.indicator_years ?? {};
  const range = Object.values(years);
  return el(
    "div",
    {},
    el(
      "ul",
      {},
      el("li", {}, "District statistics (MA 23 / MA 20), latest complete year ", range.length ? `${Math.min(...range)}–${Math.max(...range)}` : ""),
      el("li", {}, "Parks, schools, kindergartens, universities, markets, museums, sport facilities and playgrounds (City of Vienna WFS)"),
      el("li", {}, "Timetables (Wiener Linien GTFS) — stations, lines, travel times"),
      el("li", {}, `Bars, restaurants, cafés, pitches, gyms and pools (OpenStreetMap, snapshot ${meta.stats.metadata?.osm_snapshot ?? ""})`),
      el("li", {}, "District boundaries (City of Vienna)"),
    ),
    el("p", { class: "small muted" }, meta.attributions.join(" · ")),
  );
}

function limitations() {
  return el(
    "ul",
    {},
    el("li", {}, "No rent or crime data — not available as official open data per district."),
    el("li", {}, "Travel times are in-vehicle times between each district's busiest station and a destination; waiting and walking are not modelled."),
    el("li", {}, "Levels are relative (top / middle / bottom third of Vienna's districts), not absolute thresholds."),
    el("li", {}, "OpenStreetMap coverage varies between districts."),
  );
}

function fact(value, label) {
  return el("div", { class: "fact" }, el("div", { class: "fact__value" }, value), el("div", { class: "fact__label" }, label));
}
