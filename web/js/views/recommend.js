import { api } from "../api.js";
import { districtTitle, el, loading, notice } from "../dom.js";
import { DistrictMap } from "../map.js";

const WEIGHT_LABELS = ["Off", "Nice to have", "Important", "Very important"];
const STORAGE_KEY = "vdkg.recommend";
const VISIBLE_RESULTS = 8;

const state = restore() ?? {
  preferences: {},
  nearby: 10,
  commuteEnabled: false,
  commuteStation: null,
  commuteMinutes: 25,
  similarTo: "",
  similarWeight: 2,
  result: null,
  showAll: false,
};

function restore() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY));
    return saved ? { ...saved, result: null, showAll: false } : null;
  } catch {
    return null;
  }
}

function encodeSearch() {
  const query = new URLSearchParams();
  for (const [id, weight] of Object.entries(state.preferences)) if (weight > 0) query.set(id, weight);
  query.set("nearby", state.nearby);
  if (state.commuteEnabled && state.commuteStation) {
    query.set("station", state.commuteStation.id);
    query.set("station_name", state.commuteStation.name);
    query.set("commute", state.commuteMinutes);
  }
  if (state.similarTo) {
    query.set("similar", state.similarTo);
    query.set("similar_weight", state.similarWeight);
  }
  return query.toString();
}

function applySearch(encoded, meta) {
  const query = new URLSearchParams(encoded);
  const known = new Set(meta.preferences.map((p) => p.id));
  state.preferences = {};
  for (const [key, value] of query) {
    if (known.has(key)) state.preferences[key] = Math.min(3, Math.max(0, Number(value) || 0));
  }
  state.nearby = Number(query.get("nearby") ?? 10);
  state.commuteEnabled = query.has("station");
  state.commuteStation = query.has("station")
    ? { id: query.get("station"), name: query.get("station_name") ?? query.get("station") }
    : null;
  state.commuteMinutes = Number(query.get("commute") ?? 25);
  state.similarTo = query.get("similar") ?? "";
  state.similarWeight = Number(query.get("similar_weight") ?? 2);
}

function persist() {
  try {
    const { result, showAll, ...form } = state;
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(form));
  } catch {
    /* storage unavailable */
  }
}

export async function render(root, { meta, navigate, params }) {
  const districtsById = Object.fromEntries(meta.districts.map((d) => [d.id, d]));
  const shared = Boolean(params);
  if (shared) applySearch(params, meta);
  const resultsNode = el("div");
  const mapNode = el("div", { class: "map" });
  let map;

  const form = buildForm(meta, () => search());
  root.append(
    el(
      "section",
      { class: "page-intro" },
      el("h1", {}, "Find your district"),
      el(
        "p",
        {},
        "Tell the knowledge graph what matters to you. Rules over Vienna's open data decide what each district offers — also what is reachable nearby by public transport — and every result explains why it ranks where it does.",
      ),
    ),
    el(
      "div",
      { class: "split" },
      el("aside", { class: "card card--sticky" }, form),
      el("section", { class: "stack" }, el("div", { class: "card" }, mapNode), el("div", { class: "card" }, resultsNode)),
    ),
  );

  map = await new DistrictMap(mapNode, {
    onSelect: (id) => focusResult(id),
    onHover: (id) => markResult(id),
  }).load();

  if (shared) {
    await search();
  } else {
    renderResults();
    if (state.result) paintMap();
  }

  async function search() {
    const body = requestBody();
    resultsNode.replaceChildren(loading("Reasoning over the knowledge graph…"));
    try {
      state.result = await api.recommend(body);
      state.showAll = false;
      persist();
      history.replaceState(null, "", `#/recommend/${encodeSearch()}`);
      renderResults();
      paintMap();
    } catch (error) {
      resultsNode.replaceChildren(notice(error.message, "error"));
    }
  }

  function requestBody() {
    return {
      preferences: Object.fromEntries(Object.entries(state.preferences).filter(([, w]) => w > 0)),
      nearby_minutes: state.nearby,
      commute_station: state.commuteEnabled && state.commuteStation ? state.commuteStation.id : null,
      commute_minutes: state.commuteEnabled && state.commuteStation ? state.commuteMinutes : null,
      similar_to: state.similarTo || null,
      similar_weight: state.similarWeight,
    };
  }

  function paintMap() {
    const values = Object.fromEntries(state.result.recommendations.map((r) => [r.district, r.score]));
    map.setValues(values, {
      min: 0,
      max: 100,
      format: (v) => `${Math.round(v)} %`,
      title: "Match",
      excluded: state.result.excluded,
    });
  }

  function renderResults() {
    const result = state.result;
    if (!result) {
      resultsNode.replaceChildren(
        el(
          "div",
          { class: "empty" },
          el("p", {}, "Choose how important each topic is to you and press ", el("strong", {}, "Find districts"), "."),
          el("p", { class: "small" }, "Tip: add your daily commute to rule out districts that are too far away."),
        ),
      );
      return;
    }
    const excluded = result.excluded.map((id) => districtsById[id].name);
    const items = state.showAll ? result.recommendations : result.recommendations.slice(0, VISIBLE_RESULTS);
    resultsNode.replaceChildren(
      el(
        "div",
        { class: "results-header" },
        el("h2", {}, `${result.recommendations.length} districts ranked`),
        el(
          "span",
          { class: "small muted" },
          `Reasoned in ${result.reasoning_ms} ms · ${result.derived_facts} facts derived · `,
          el("a", { href: location.href, onClick: copyLink }, "copy link"),
        ),
      ),
      excluded.length
        ? notice(`Excluded by your commute (${state.commuteMinutes} min to ${state.commuteStation?.name}): ${excluded.join(", ")}`)
        : "",
      el("div", { class: "result-list" }, items.map((r, index) => resultCard(r, index + 1))),
      result.recommendations.length > VISIBLE_RESULTS && !state.showAll
        ? el(
            "div",
            { class: "actions" },
            el(
              "button",
              { class: "button button--ghost", type: "button", onClick: () => { state.showAll = true; renderResults(); } },
              `Show all ${result.recommendations.length}`,
            ),
          )
        : "",
    );
  }

  function resultCard(r, rank) {
    const meta = [];
    if (r.commute_minutes !== null && state.commuteStation) {
      meta.push(`${r.commute_minutes} min to ${state.commuteStation.name}`);
    }
    if (r.similarity_rank !== null && state.similarTo) {
      meta.push(`#${r.similarity_rank} most similar to ${districtsById[state.similarTo].name}`);
    }
    return el(
      "article",
      {
        class: "result",
        dataset: { district: r.district },
        tabindex: "0",
        onClick: () => navigate(`district/${r.district}`),
        onKeydown: (event) => event.key === "Enter" && navigate(`district/${r.district}`),
        onMouseenter: () => map.highlight([r.district]),
        onMouseleave: () => map.highlight([]),
      },
      el("div", { class: "result__rank" }, rank),
      el(
        "div",
        {},
        el("div", { class: "result__title" }, districtTitle(r)),
        meta.length ? el("div", { class: "result__meta" }, meta.join(" · ")) : "",
        el("div", { class: "chips" }, r.matches.map(matchChip)),
      ),
      el(
        "div",
        { class: "result__score" },
        el("strong", {}, `${Math.round(r.score)} %`),
        el("div", { class: "bar" }, el("span", { style: `width:${r.score}%` })),
      ),
    );
  }

  function focusResult(id) {
    const card = resultsNode.querySelector(`[data-district="${id}"]`);
    if (!card && state.result) {
      state.showAll = true;
      renderResults();
    }
    const target = resultsNode.querySelector(`[data-district="${id}"]`);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      target.focus({ preventScroll: true });
    } else {
      navigate(`district/${id}`);
    }
  }

  function markResult(id) {
    for (const card of resultsNode.querySelectorAll(".result")) {
      card.style.borderColor = card.dataset.district === id ? "var(--primary)" : "";
    }
  }

  return () => map?.destroy();
}

async function copyLink(event) {
  event.preventDefault();
  try {
    await navigator.clipboard.writeText(location.href);
    event.target.textContent = "link copied";
  } catch {
    event.target.textContent = "copy from the address bar";
  }
}

function matchChip(match) {
  const evidence = match.evidence.map((e) => `${e.label}: ${e.level}`).join("\n");
  if (match.status === "in_district") {
    return el("span", { class: "chip chip--in", title: evidence }, "✓ ", match.label);
  }
  if (match.status === "nearby") {
    return el(
      "span",
      { class: "chip chip--nearby", title: `Reachable in ${match.minutes} min: ${match.via_name}\n${evidence}` },
      "↗ ",
      `${match.label} · ${match.minutes} min (${match.via_name})`,
    );
  }
  return el("span", { class: "chip chip--missing", title: "Not offered in or near this district" }, match.label);
}

function buildForm(meta, onSubmit) {
  const groups = Map.groupBy(meta.preferences, (p) => p.group);
  const formNode = el("form", {
    onSubmit: (event) => {
      event.preventDefault();
      onSubmit();
    },
  });

  const preferenceNodes = [...groups].map(([group, preferences]) =>
    el(
      "div",
      { class: "pref-group" },
      el("h3", {}, group),
      preferences.map((p) =>
        el(
          "div",
          { class: "pref-row" },
          el("div", {}, el("div", { class: "pref-row__label" }, p.label), el("div", { class: "pref-row__desc" }, p.description)),
          segmented(
            [0, 1, 2, 3],
            state.preferences[p.id] ?? 0,
            (w) => {
              state.preferences[p.id] = w;
              persist();
            },
            (w) => (w === 0 ? "–" : String(w)),
            (w) => `${p.label}: ${WEIGHT_LABELS[w]}`,
          ),
        ),
      ),
    ),
  );

  const nearbyOutput = el("output", {}, minutesLabel(state.nearby));
  const nearbyField = el(
    "div",
    { class: "field" },
    el("label", { for: "nearby" }, "Also count places reachable within"),
    el(
      "div",
      { class: "range-row" },
      el("input", {
        id: "nearby",
        type: "range",
        min: "0",
        max: "30",
        step: "1",
        value: String(state.nearby),
        onInput: (event) => {
          state.nearby = Number(event.target.value);
          nearbyOutput.textContent = minutesLabel(state.nearby);
          persist();
        },
      }),
      nearbyOutput,
    ),
    el("div", { class: "hint" }, "by public transport from the district's main station (0 = only inside the district)"),
  );

  const commuteDetails = el("div", { hidden: !state.commuteEnabled }, commuteFields());
  const commuteField = el(
    "div",
    { class: "field" },
    el(
      "label",
      { class: "switch" },
      el("input", {
        type: "checkbox",
        checked: state.commuteEnabled,
        onChange: (event) => {
          state.commuteEnabled = event.target.checked;
          commuteDetails.hidden = !state.commuteEnabled;
          persist();
        },
      }),
      "I commute daily (university, work, …)",
    ),
    commuteDetails,
  );

  const similarWeight = el(
    "div",
    { class: "range-row", hidden: !state.similarTo },
    el("span", { class: "small muted" }, "Importance"),
    segmented([1, 2, 3], state.similarWeight, (w) => {
      state.similarWeight = w;
      persist();
    }, String, (w) => WEIGHT_LABELS[w]),
  );
  const similarField = el(
    "div",
    { class: "field" },
    el("label", { for: "similar" }, "Similar to a district I like"),
    el(
      "select",
      {
        id: "similar",
        onChange: (event) => {
          state.similarTo = event.target.value;
          similarWeight.hidden = !state.similarTo;
          persist();
        },
      },
      el("option", { value: "" }, "— none —"),
      meta.districts.map((d) =>
        el("option", { value: d.id, selected: d.id === state.similarTo }, districtTitle(d)),
      ),
    ),
    similarWeight,
    el("div", { class: "hint" }, "Uses the learned knowledge graph embeddings."),
  );

  formNode.append(
    el("h2", {}, "What matters to you?"),
    el("p", { class: "small muted" }, "– = off · 1 = nice to have · 3 = very important"),
    ...preferenceNodes,
    nearbyField,
    commuteField,
    similarField,
    el(
      "div",
      { class: "actions" },
      el("button", { class: "button", type: "submit" }, "Find districts"),
      el(
        "button",
        {
          class: "button button--ghost",
          type: "button",
          onClick: () => {
            state.preferences = {};
            state.similarTo = "";
            state.commuteEnabled = false;
            persist();
            location.reload();
          },
        },
        "Reset",
      ),
    ),
  );
  return formNode;
}

function commuteFields() {
  const minutesOutput = el("output", {}, minutesLabel(state.commuteMinutes));
  return [
    stationPicker(),
    el(
      "div",
      { class: "range-row" },
      el("span", { class: "small muted" }, "at most"),
      el("input", {
        type: "range",
        min: "5",
        max: "45",
        step: "5",
        value: String(state.commuteMinutes),
        "aria-label": "Maximum commute in minutes",
        onInput: (event) => {
          state.commuteMinutes = Number(event.target.value);
          minutesOutput.textContent = minutesLabel(state.commuteMinutes);
          persist();
        },
      }),
      minutesOutput,
    ),
  ];
}

function stationPicker() {
  const list = el("ul", { class: "autocomplete__list", role: "listbox", hidden: true });
  let timer;
  const input = el("input", {
    type: "search",
    placeholder: "Station, e.g. Karlsplatz",
    value: state.commuteStation?.name ?? "",
    "aria-label": "Commute destination station",
    autocomplete: "off",
    onInput: (event) => {
      clearTimeout(timer);
      const query = event.target.value.trim();
      state.commuteStation = null;
      if (query.length < 2) {
        list.hidden = true;
        return;
      }
      timer = setTimeout(async () => {
        const stations = await api.stations(query);
        list.replaceChildren(
          ...stations.map((station) =>
            el(
              "li",
              {
                role: "option",
                onMousedown: (e) => {
                  e.preventDefault();
                  state.commuteStation = station;
                  input.value = station.name;
                  list.hidden = true;
                  persist();
                },
              },
              station.name,
            ),
          ),
        );
        list.hidden = stations.length === 0;
      }, 180);
    },
    onBlur: () => setTimeout(() => (list.hidden = true), 150),
  });
  return el("div", { class: "autocomplete" }, input, list);
}

function segmented(values, current, onChange, label, describe) {
  const node = el("div", { class: "segmented", role: "group" });
  const buttons = values.map((value) =>
    el(
      "button",
      {
        type: "button",
        "aria-pressed": String(value === current),
        dataset: value === 0 ? { off: "" } : undefined,
        title: describe(value),
        "aria-label": describe(value),
        onClick: () => {
          for (const b of buttons) b.setAttribute("aria-pressed", String(b === buttons[values.indexOf(value)]));
          onChange(value);
        },
      },
      label(value),
    ),
  );
  node.append(...buttons);
  return node;
}

function minutesLabel(minutes) {
  return minutes === 0 ? "only here" : `${minutes} min`;
}
