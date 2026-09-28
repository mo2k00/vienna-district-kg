import { api } from "../api.js";
import { districtTitle, el, levelBadge, loading, notice } from "../dom.js";
import { DistrictMap } from "../map.js";

const SOURCES = {
  TransE: "TransE embedding — relations as translations (h + r ≈ t), as in the lecture.",
  RotatE: "RotatE embedding — relations as rotations in complex space.",
  features: "Baseline without the graph: cosine similarity of the raw district statistics.",
};

let selected = "d07";
let source = "TransE";

export async function render(root, { meta, navigate, params }) {
  if (params && meta.districts.some((d) => d.id === params)) selected = params;
  const available = meta.similarity_sources;
  if (!available.includes(source)) source = available[0];
  const byId = Object.fromEntries(meta.districts.map((d) => [d.id, d]));

  if (!available.length) {
    root.append(notice("No embeddings trained yet. Run `vdkg embed` first.", "error"));
    return () => {};
  }

  const listNode = el("div");
  const mapNode = el("div", { class: "map" });
  const sourceNote = el("p", { class: "small muted" }, SOURCES[source]);
  const select = el(
    "select",
    { onChange: (e) => update(e.target.value, source), "aria-label": "District" },
    meta.districts.map((d) => el("option", { value: d.id, selected: d.id === selected }, districtTitle(d))),
  );
  const sourceButtons = el(
    "div",
    { class: "segmented", role: "group" },
    available.map((s) =>
      el("button", { type: "button", "aria-pressed": String(s === source), onClick: () => update(selected, s) }, s === "features" ? "Baseline" : s),
    ),
  );

  root.append(
    el(
      "section",
      { class: "page-intro" },
      el("h1", {}, "Similar districts"),
      el(
        "p",
        {},
        "Knowledge graph embeddings place every district in a vector space learned from the graph — its levels, what it offers, its neighbours and transit links. Districts close in that space are similar.",
      ),
    ),
    el(
      "div",
      { class: "split" },
      el(
        "aside",
        { class: "card card--sticky" },
        el("div", { class: "field" }, el("label", {}, "District"), select),
        el("div", { class: "field" }, el("label", {}, "Similarity from"), sourceButtons, sourceNote),
        el("p", { class: "small muted", style: "margin-top:1rem" }, "Click any district on the map to compare it instead."),
      ),
      el("section", { class: "stack" }, el("div", { class: "card" }, mapNode), el("div", { class: "card" }, listNode)),
    ),
  );

  const map = await new DistrictMap(mapNode, { onSelect: (id) => update(id, source) }).load();
  await update(selected, source);

  async function update(id, from) {
    selected = id;
    source = from;
    select.value = id;
    sourceNote.textContent = SOURCES[source];
    for (const button of sourceButtons.children) {
      button.setAttribute("aria-pressed", String(button.textContent === (source === "features" ? "Baseline" : source)));
    }
    history.replaceState(null, "", `#/similar/${id}`);
    listNode.replaceChildren(loading());
    try {
      const all = await api.similar(id, source, 22);
      const values = Object.fromEntries(all.map((s) => [s.district, s.similarity]));
      map.setValues(values, { format: (v) => v.toFixed(2), title: `Similarity to ${byId[id].name}` });
      map.select(id);
      listNode.replaceChildren(
        el("h2", {}, `Most similar to ${byId[id].name}`),
        el("div", { class: "result-list" }, all.slice(0, 5).map((s) => similarCard(s, meta, navigate))),
      );
    } catch (error) {
      listNode.replaceChildren(notice(error.message, "error"));
    }
  }

  return () => map.destroy();
}

function similarCard(item, meta, navigate) {
  const shared = item.shared_levels.slice(0, 8).map((entry) => entry.split(":"));
  return el(
    "article",
    { class: "result", tabindex: "0", onClick: () => navigate(`district/${item.district}`) },
    el("div", { class: "result__rank" }, item.rank),
    el(
      "div",
      {},
      el("div", { class: "result__title" }, item.name),
      shared.length
        ? el(
            "div",
            { class: "chips" },
            shared.map(([feature, level]) =>
              el("span", { class: "chip", title: "Same level in both districts" }, `${meta.feature_labels[feature] ?? feature}: `, levelBadge(level)),
            ),
          )
        : el("div", { class: "result__meta" }, "No extreme levels in common"),
    ),
    el("div", { class: "result__score" }, el("strong", {}, item.similarity.toFixed(2))),
  );
}
