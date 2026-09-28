# Implementation plan

Status: **decisions taken 2026-09-26** (see §11). Deadline 2026-09-30.

## 1. Goal in one paragraph
A Knowledge Graph over Vienna's 23 districts that integrates official open data (City of Vienna,
Wiener Linien) and OpenStreetMap. A **logic layer** (Nemo, Datalog with existential rules) derives
district traits, transit reachability (recursive) and **explained recommendations** from preferences a
user selects in a **web app**. An **embedding layer** (PyKEEN) learns district representations to find
**similar districts** and to **complete** missing facts. The web app is the service on top.

## 2. LO coverage (from the one-pager: focus LO1, LO2; basic LO4–LO12; not LO3)

| LO | Level | Where it is demonstrated | Evidence for the report |
|---|---|---|---|
| **LO1** KGE | focus | `embeddings/`: TransE (lecture model) + RotatE (lecture "glimpse beyond"), PyKEEN out of the box | 5 embedded entities/relations explained, link-prediction metrics (MRR, Hits@k), TP + FP prediction, similarity vs. feature baseline, seed stability |
| **LO2** Logic | focus | `reasoning/rules/*.rls` (Nemo) | ≥5 rules shown: aggregation, classification, **recursion** (transit reachability), **object creation** (`!Rec` recommendation nodes), stratified negation (hard constraints); discussion of Datalog± / wardedness |
| LO4 Data models | basic | Relational/Datalog facts as canonical store + triples for KGE; reified observations with year (temporal context) | Reflection: vs. RDF / property graph / plain feature table |
| LO5 Architecture | basic | Layered pipeline (§3), responsibility-driven split KG vs. app (lecture KG-08-06) | Architecture diagram + rationale |
| LO6 Scalable reasoning | basic | Offline materialisation vs. per-request reasoning; bounded recursion; transductive KGE limits | Timings, fact counts, scaling discussion (250 Zählbezirke, other cities) |
| LO7 KG creation | basic | Loaders + **schema-mapping rules** (Datalog, as in lecture KG-07-04) + record linkage (OSM vs. city sports facilities, district resolution from address/PLZ/coordinates) | 3 concrete node/edge construction examples |
| LO8 KG evolution | basic | Completion by logic (derived traits, reachability) and by KGE (predicted traits); re-materialisation on data updates | What gets added/changed, one completion experiment |
| LO9 Real-world app | basic | Newcomer district finder | Scenario section |
| LO10 Financial | basic | Income/unemployment context; relevance of location scoring for banks/insurers (mortgage risk, branch placement, real-estate valuation) | One paragraph |
| LO11 Services | basic | Web app (FastAPI + Leaflet): preference recommender, similar districts, district profile | Screenshots + service description |
| LO12 KG/ML/AI | basic | Logic → KGE (derived facts are training triples), KGE → service (similarity boost), comparison | Reflection section |

## 3. Architecture

```
            ┌──────────── offline pipeline (python -m vdkg <step>) ─────────────┐
 sources →  │ ingest → normalise → build KG facts → reason (materialise) → embed │ → artifacts
            └────────────────────────────────────────────────────────────────────┘
                                                                  │
 browser (HTML/JS + Leaflet) → FastAPI (JSON) → service layer → per-request reasoning (Nemo)
                                                          → embedding lookups (similarity)
```

**Responsibility split** (lecture: "responsibility of knowing/doing"):
- *In the KG (rules)*: everything data-dependent that needs non-trivial reasoning — aggregation,
  trait classification, reachability, matching preferences, explanations.
- *In application code*: data download/parsing, GTFS preprocessing, KGE training, HTTP API, UI.

### Package layout (src layout, one responsibility per module)
```
vienna-district-kg/
├── pyproject.toml              # package + deps; entry point `vdkg`
├── src/vdkg/
│   ├── config.py               # paths, constants (dataclass), no logic
│   ├── cli.py                  # `vdkg ingest|build|reason|embed|all`
│   ├── ingest/
│   │   ├── sources.py          # declarative registry of all datasets (url, loader, licence)
│   │   ├── http.py             # cached download
│   │   ├── ma23.py             # MA 23 statistics CSV parser (one parser for all series)
│   │   ├── wfs.py              # City of Vienna WFS point layers
│   │   ├── osm.py              # Overpass query + snapshot
│   │   ├── gtfs.py             # stop_times → station graph with travel minutes
│   │   └── geo.py              # district polygons, point-in-district, adjacency
│   ├── kg/
│   │   ├── schema.py           # predicates, entity id conventions
│   │   ├── build.py            # normalised tables → fact relations
│   │   ├── store.py            # read/write fact CSVs (the "KG store")
│   │   └── triples.py          # facts → (h, r, t) for PyKEEN
│   ├── reasoning/
│   │   ├── nemo.py             # thin wrapper around nmo (run program, parse results)
│   │   └── rules/              # 10_mapping, 20_aggregates, 30_traits, 40_transit, 50_recommend
│   ├── embeddings/
│   │   ├── train.py            # PyKEEN pipeline per model/seed
│   │   ├── similarity.py       # district similarity from embeddings
│   │   └── evaluate.py         # metrics, baseline comparison, completion experiment
│   ├── service/
│   │   ├── preferences.py      # preference catalogue (id, label, group) → request facts
│   │   ├── recommender.py      # run preference rules, rank, explain
│   │   └── districts.py        # profiles, similar districts
│   └── api/
│       ├── main.py             # FastAPI app factory, static file mount (`vdkg serve`)
│       ├── routes.py           # /api/preferences, /recommend, /similar, /districts/{id}, /stations, /stats
│       └── schemas.py          # pydantic request/response models
├── web/                        # static frontend, no build step
│   ├── index.html
│   ├── css/styles.css
│   └── js/                     # ES modules: api.js, map.js, preferences.js, results.js, views/*.js
├── data/  raw/ (gitignored) · snapshots/ (OSM, committed) · processed/ · kg/ (committed, small)
├── artifacts/                  # trained models, embeddings, reasoning outputs
├── tests/                      # parser + rule smoke tests
├── tools/setup_nemo.py
└── docs/
```
The empty folders created earlier (`construction/`, `logic/`, `ml/`, `service/`) get replaced by this layout.

**Code conventions**: type hints, small functions, dataclasses for records, no business logic in the UI,
docstrings only where behaviour is not obvious, no narrating comments, `ruff` for formatting.

## 4. Data (see `DATA_SOURCES.md`)
Granularity: **23 districts** (Zählbezirke would be 250 — mentioned as scaling direction only).
Latest available year per indicator; the year is kept on every observation.

| Group | Indicators | Normalisation |
|---|---|---|
| Population | population, density, avg. age, household types, education (% academic) | as published |
| Economy (context) | net income, unemployment | as published |
| Going out | bars + pubs + nightclubs (OSM) | per km² (walkability) |
| Food & cafés | restaurants + cafés (OSM) | per km² |
| Sports | tennis, football, basketball, volleyball, fitness, swimming (OSM pitches + city sport facilities + ball playgrounds, de-duplicated) | per 10,000 residents |
| Green & quiet | park area share, public green space, road area, density | share of district area / per resident |
| Family | kindergartens, schools, playgrounds, family households | per 1,000 residents |
| Students | universities, single households, avg. age | count / share |
| Culture | museums | count |
| Mobility | U-Bahn lines, travel time to centre, cycle paths, cars per 1,000 | as computed |
| Health | doctors, pharmacies per 1,000 | as published |
| Structure | district adjacency (polygons), station graph (GTFS) | — |

Rent and crime: not available as official open data → limitation.

## 5. KG schema (Nemo predicates)
Extensional (ground facts, CSV):
- `district(D, Name, Number)`, `area(D, Km2)`, `population(D, N)`
- `observation(D, Indicator, Value, Year, Source)` — reified, keeps temporal context + provenance
- `poi(P, Category, D, Source)`, `sportType(P, Sport)`
- `station(S, Name, D)`, `servedBy(S, Line)`, `line(L, Mode)`, `segment(S1, S2, Minutes)`
- `adjacent(D1, D2)`

Intensional (rules) → derived:
- `poiCount(D, Cat, N)` (#count), `cityAvg(Cat, X)` (#sum / #count), `density(D, Cat, X)` (arithmetic)
- `level(D, Feature, high|medium|low)` relative to the Vienna average (e.g. high ≥ 1.25 × avg)
- `hub(D, S)` = station with most lines in D (#count, #max)
- `reach(H, S, T)` recursive, bounded (T ≤ 30 min) from each hub; `travelTime(D1, D2, #min(T))`
- `offers(D, Pref)` in district; `offersNearby(D, Pref, E, T)` via reachability
- per request: `recommendation(!Rec, Req, D)` (**existential**), `contribution(Rec, Pref, V)`,
  `score(Rec, #sum(V, Pref))`, `because(Rec, Pref, How, Via)`
- hard constraints with stratified negation: `excluded(Req, D)`, `candidate(Req, D) :- …, ~excluded(Req, D)`

All of this was smoke-tested in Nemo 0.10.1 (recursion + arithmetic bound, #min/#sum, negation, `!` nulls).

## 6. Logic layer (LO2) — rule files
| File | Content | Shows |
|---|---|---|
| `10_mapping.rls` | raw relations → KG predicates (schema mapping as rules) | LO7 |
| `20_aggregates.rls` | counts, densities, city averages | numeric reasoning |
| `30_traits.rls` | feature levels, `offers(D, Pref)` definitions | classification |
| `40_transit.rls` | hubs, bounded recursive reachability, district travel times | **recursion** |
| `50_recommend.rls` | request facts → candidates, recommendation objects, scores, explanations | **object creation**, negation |

Two-stage execution: files 10–40 are **materialised offline** once (static KG); file 50 runs **per
request** over the materialised facts + the request's preference facts (fast; LO6 discussion,
view-maintenance angle for LO8).

**Scoring**: `score = Σ w_p · s(D, p) / Σ w_p`, with s = 1 if offered in the district,
s = 0.5 if offered in a district reachable within the user's "nearby" minutes, else 0.

## 7. Embedding layer (LO1)
Training triples (≈ 800, ≈ 100 entities), built from the **materialised** KG (so logic feeds ML):
`adjacentTo`, `hasLevel_<feature> → <feature>_<level>`, `offers → <pref>`, `reachableWithin15 → D`,
`hasLine → U1..U6`.
- Models: **TransE** and **RotatE**, PyKEEN defaults, 5 seeds each (small KG → report variance).
- Split 80/10/10; metrics MRR, Hits@1/3/10.
- **Similarity**: cosine similarity of district embeddings, averaged over seeds; compared (Spearman)
  with a plain feature-vector baseline → reflection on what the KG structure adds.
- **Completion experiment (LO8)**: hide all `hasLevel_goingOut` triples of 3 districts, predict them,
  report one true positive and one false positive.
- In the app: "districts similar to X" page, optional "boost districts similar to one I like".

## 8. Web app (LO11) — FastAPI + HTML/Leaflet
```
┌ Sidebar ──────────────────────┐ ┌ Main ─────────────────────────────────────┐
│ What matters to you?          │ │  Map of Vienna, districts coloured by     │
│ Going out        ○ ○ ● ○      │ │  match score (0–100 %)                    │
│ Food & cafés     ○ ● ○ ○      │ │                                           │
│ Sports ▸ tennis ☑ football ☐ │ │  Top matches                              │
│ Green & quiet    ○ ○ ○ ●      │ │  1  Neubau · 87 %                         │
│ …                             │ │     ✓ Going out — in the district         │
│ Count places nearby: [10 min] │ │     ✓ Culture — 5 min away (Innere Stadt) │
│ Daily commute to [station ▾]  │ │     ✗ Green & quiet                       │
│   within [25 min]             │ │  2  …                                     │
└───────────────────────────────┘ └───────────────────────────────────────────┘
Separate views with a top navigation bar (hash routing in one `index.html`, e.g. `#/recommend`):
Recommend (above) · Similar districts · District profile (also opened by clicking a district) · About the KG
```
- Importance per preference: 0 (ignore) … 3 (very important).
- Backend: FastAPI + pydantic; serves the JSON API and the static `web/` folder (one process, `vdkg serve`).
- Frontend: plain HTML + one hand-written stylesheet (CSS variables) + ES-module JavaScript,
  Leaflet for the map (district GeoJSON choropleth), no framework, no build step.
- Commute: searchable station picker (all Wiener Linien stations) + max minutes; uses the recursive
  transit facts.
- District profile: all facts with source + year, derived traits, neighbours, travel times (explainability).
- About: KG statistics (entities, facts, derived facts, reasoning time), data attributions (CC BY / ODbL).

## 9. Timeline
| When | Work | Output |
|---|---|---|
| Sat 26 (rest) | package skeleton, loaders (MA 23, WFS, OSM, geo), GTFS preprocessing | `data/processed/*` |
| Sun 27 | KG facts, rule files 10–50, recommender service, tests | materialised KG, working CLI recommendation |
| Mon 28 | PyKEEN training/eval, similarity, completion experiment; **push to remote → PC switch** | `artifacts/`, metrics |
| Tue 29 | FastAPI + web frontend, figures, README, portfolio notes complete | running app, screenshots |
| Wed 30 | report + cover pages, ZIP, submit | PDF + ZIP |

## 10. Risks
| Risk | Mitigation |
|---|---|
| GTFS stop_times is 717 MB | stream with `usecols`, cache the small station graph; done once |
| Tiny KG → unstable embeddings | multiple seeds, report variance, baseline comparison; lecture FAQ: bad results are fine if analysed |
| Transit model ignores transfer/wait times | stated limitation; in-vehicle minutes only |
| OSM completeness varies | snapshot date recorded; limitation |
| PyKEEN/torch install on second PC | pinned `requirements.txt`, CPU wheels |
| Time | UI kept thin (no framework, no build); API can start Mon 28 evening; report notes collected continuously |

## 11. Decisions
Taken by user (2026-09-26): **FastAPI + vanilla JS/Leaflet + hand-written CSS**, **separate pages**
with top navigation, importance **0–3** per preference, **commute constraint to any station**,
**English** (report + UI). Defaults below accepted for the prototype (adjustable later: thresholds live in rules, catalogue in config).
Defaults below apply unless the user objects:
1. Preference catalogue as in §4 (going out, food & cafés, 6 sports, green & quiet, family, students, culture, well connected, car-free, health).
2. Traits relative to the Vienna average (high ≥ 1.25 × avg, low ≤ 0.75 × avg).
3. "Nearby" default 10 minutes, slider 0–30.
4. KGE models TransE + RotatE, 5 seeds.
5. RDF/Turtle export only if time permits (LO4 is covered by reflection either way).
6. Minimal tests (parsers, one rule smoke test).
7. ZIP = repository + README mapping report sections to folders.
