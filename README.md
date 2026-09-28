# Vienna District KG

Knowledge Graph-based district similarity and lifestyle recommendation for Vienna.
Mini-project for *Knowledge Graphs* (TU Wien, 2026S) — Moritz Lindner.

A knowledge graph over Vienna's 23 districts built from open data (City of Vienna, Wiener Linien,
OpenStreetMap). A **logic layer** (Nemo, Datalog with existential rules) derives what districts
offer, public-transport reachability and explained recommendations; an **embedding layer**
(PyKEEN: TransE, RotatE) learns district similarity. A small web app serves both.

## Quick start

Requires Python ≥ 3.11 (developed with 3.12 on Windows). Commands are for Windows (`cmd`/PowerShell);
on macOS/Linux use `.venv/bin/...` instead of `.venv\Scripts\...`.

```bash
python -m venv .venv
.venv\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\pip install -e ".[ml,dev]"
python tools/setup_nemo.py
```

`tools/setup_nemo.py` downloads the Nemo rule engine (v0.10.1) for your platform into `tools/nemo/`
and verifies its checksum. It is not committed to git.

### Start the web app

```bash
.venv\Scripts\vdkg serve
```

Then open **http://127.0.0.1:8000** in a browser. Stop the server with `Ctrl+C`.

- Other port: `vdkg serve --port 8080`; reachable from other devices in the network: `vdkg serve --host 0.0.0.0`.
- Interactive API documentation (Swagger UI): **http://127.0.0.1:8000/docs**.
- The processed data, the ground KG, the reasoning results and the embeddings are committed, so the
  app works right after setup — no pipeline run needed.

Pages: **Recommend** (choose preferences, optional commute and "similar to a district I like"),
**Similar districts** (TransE / RotatE / feature baseline), **Districts** (profile with every fact,
its source and year), **About the KG** (statistics and model metrics).

## Pipeline

Each step reads the output of the previous one:

| Command | Does | Output | Time |
|---|---|---|---|
| `vdkg ingest` | download + parse all sources, district assignment, record-linkage candidates | `data/processed/`, `web/data/districts.geojson` | ~70 s |
| `vdkg build` | processed tables → ground facts for the rules | `data/kg/*.csv` | ~1 s |
| `vdkg reason` | Nemo materialisation (rules 10–40) | `artifacts/materialized/` | ~17 s |
| `vdkg embed` | PyKEEN training (TransE, RotatE × 5 seeds), evaluation, similarity facts | `artifacts/embeddings/`, `data/kg/triples.tsv` | ~6 min |
| `vdkg all` | the four steps above | | ~8 min |
| `vdkg report` | evidence for the report: verification, derivation traces, RDF export + SPARQL, embedding examples, figures | `artifacts/report/`, `data/kg/vienna_kg.trig` | ~20 s |
| `vdkg serve` | web app + API | | |

Restart `vdkg serve` after rerunning a step — the server caches the KG in memory.

Downloads are cached in `data/raw/` (not committed). The OpenStreetMap snapshot in
`data/snapshots/osm_pois.json` is committed so results are reproducible.

## Report evidence and submission

```bash
vdkg report                               # artifacts/report/: verification.json, traces.md, examples.json, rdf_export.json, figures/
python tools/screenshots.py               # needs a running `vdkg serve` and Chrome → artifacts/report/screenshots/
python tools/package_submission.py        # → dist/vienna-district-kg-submission.zip
python tools/build_portfolio.py           # → dist/portfolio/KG_Portfolio_Lindner-structured.{docx,pdf}
```

The portfolio is written in `docs/portfolio/report.md` (Markdown) with the cover-page entries in
`docs/portfolio/cover.json`. `build_portfolio.py` fills the course pro-forma, appends the report,
fills in the page references on the cover pages and exports the PDF through Microsoft Word
(`pip install -e ".[portfolio]"`, Windows with Word required). Highlighted fields on the cover pages
(hours, AI percentages, declaration) are placeholders to fill in `cover.json`.

- `verification.json` checks reasoning results against independent Python implementations
  (Dijkstra for travel times, union-find for record linkage, ranks).
- `traces.md` contains derivation trees from `nmo --trace`.
- The submission ZIP contains the runnable repository (without `.venv`, Nemo binary and raw downloads)
  plus the folders `2 - construction`, `3 - ML`, `4 - logic`, `5 - reflection` with the evidence for
  each report section.
- Result pages are shareable: after a search the URL contains all preferences
  (e.g. `#/recommend/going_out=3&sport_tennis=2&nearby=10`); opening it re-runs the search.

## Data files: sources, names and locations

`vdkg ingest` downloads everything automatically and caches it under the names below. To download a
file **manually** (e.g. when a portal is slow or you want a specific version), save it under exactly
this name and location — the loader then uses the local file instead of downloading. Keep the files
as published: do not rename columns, change separators or re-encode them.

| Dataset | Download from | Save as |
|---|---|---|
| District statistics – density | https://www.wien.gv.at/gogv/l9ogdviebezbizpopden2002f | `data/raw/ma23_density.csv` |
| District statistics – age | https://www.wien.gv.at/gogv/l9ogdviebezbizpopage2002f | `data/raw/ma23_age.csv` |
| District statistics – income | https://www.wien.gv.at/gogv/l9ogdviebezbizecnincsex2002f | `data/raw/ma23_income.csv` |
| District statistics – unemployment | https://www.wien.gv.at/gogv/l9ogdviebezbizempsexuep2002f | `data/raw/ma23_unemployment.csv` |
| District statistics – education | https://www.wien.gv.at/gogv/l9ogdviebezbizeduatt2008f | `data/raw/ma23_education.csv` |
| District statistics – households | https://www.wien.gv.at/gogv/l9ogdviebezpopsexhhtyp2012f | `data/raw/ma23_households.csv` |
| District statistics – families | https://www.wien.gv.at/gogv/l9ogdviebezfamtyp2012f | `data/raw/ma23_families.csv` |
| District statistics – traffic_area | https://www.wien.gv.at/gogv/l9ogdviebezbiztectra2002f | `data/raw/ma23_traffic_area.csv` |
| District statistics – medical | https://www.wien.gv.at/gogv/l9ogdviebezbizmedsup2002f | `data/raw/ma23_medical.csv` |
| District statistics – tourism | https://www.wien.gv.at/gogv/l9ogdviebezbizecntou2002f | `data/raw/ma23_tourism.csv` |
| Cars per 1,000 residents (MA 20) | https://www.wien.gv.at/data/ogd/ma20/pkwdichte2024.csv | `data/raw/ma20_car_density.csv` |
| Map layer – parks (`PARKINFOOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:PARKINFOOGD&outputFormat=csv) | `data/raw/wfs_parks.csv` |
| Map layer – schools (`SCHULEOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:SCHULEOGD&outputFormat=csv) | `data/raw/wfs_schools.csv` |
| Map layer – kindergartens (`KINDERGARTENOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:KINDERGARTENOGD&outputFormat=csv) | `data/raw/wfs_kindergartens.csv` |
| Map layer – universities (`UNIVERSITAETOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:UNIVERSITAETOGD&outputFormat=csv) | `data/raw/wfs_universities.csv` |
| Map layer – markets (`MAERKTEOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:MAERKTEOGD&outputFormat=csv) | `data/raw/wfs_markets.csv` |
| Map layer – museums (`MUSEUMOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:MUSEUMOGD&outputFormat=csv) | `data/raw/wfs_museums.csv` |
| Map layer – sport_facilities (`SPORTSTAETTENOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:SPORTSTAETTENOGD&outputFormat=csv) | `data/raw/wfs_sport_facilities.csv` |
| Map layer – playgrounds (`SPIELPLATZPUNKTOGD`) | [WFS CSV](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:SPIELPLATZPUNKTOGD&outputFormat=csv) | `data/raw/wfs_playgrounds.csv` |
| District boundaries (`BEZIRKSGRENZEOGD`) | [WFS GeoJSON](https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&typeName=ogdwien:BEZIRKSGRENZEOGD&outputFormat=json) | `data/raw/district_borders.geojson` |
| Wiener Linien timetables (GTFS) | http://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip | unzip into `data/raw/gtfs/` (see below) |
| OpenStreetMap venues | Overpass API https://overpass-api.de/api/interpreter, query in `src/vdkg/ingest/osm.py` (`QUERY`) | `data/snapshots/osm_pois.json` |

Notes:

- **District statistics** (MA 23) are `;`-separated CSVs with a title line above the header; the
  loader picks the latest year in which all 23 districts have values.
- **Map layers** are the City of Vienna WFS; the links above return CSV (or GeoJSON for the
  boundaries) in WGS84 (`EPSG:4326`). The catalogue pages are listed in `docs/DATA_SOURCES.md`.
- **GTFS**: only `stops.txt`, `stop_times.txt`, `trips.txt` and `routes.txt` are needed. Either extract
  them into `data/raw/gtfs/` or point `VDKG_GTFS_DIR` to a folder that already contains them (e.g. the
  course template's `src/assets/data/wienerlinien`). `stop_times.txt` is ~700 MB unpacked.
- **OpenStreetMap**: POST the `QUERY` from `src/vdkg/ingest/osm.py` to the Overpass API
  (e.g. on https://overpass-turbo.eu, export as raw JSON) and save the response as
  `data/snapshots/osm_pois.json`. The snapshot date is read from a `snapshot_date` field if present,
  otherwise from the file's modification date. This file is committed so results stay reproducible.
- After adding or replacing any file, run `vdkg all` (or the steps from `vdkg ingest` on).

## Updating or exchanging data

| I want to … | Do this | Then run |
|---|---|---|
| refresh everything from the internet | delete `data/raw/` and `data/snapshots/osm_pois.json` | `vdkg all` |
| refresh only OpenStreetMap | delete `data/snapshots/osm_pois.json` | `vdkg all` |
| refresh one city dataset | delete its file in `data/raw/` (`ma23_<key>.csv`, `wfs_<key>.csv`, `ma20_car_density.csv`, `district_borders.geojson`) | `vdkg all` |
| use an already downloaded GTFS feed | set `VDKG_GTFS_DIR` to the folder with `stops.txt`, `stop_times.txt`, `trips.txt`, `routes.txt` (e.g. the course template's `src/assets/data/wienerlinien`) | `vdkg all` |
| get a fresh GTFS feed | delete `data/raw/gtfs/` and `data/raw/gtfs.zip` (and unset `VDKG_GTFS_DIR`) — downloaded automatically (large, stop_times.txt alone is ~700 MB unpacked) | `vdkg all` |
| add another MA 23 district statistics series | add a `StatisticsSeries` to `STATISTICS` in `src/vdkg/ingest/sources.py` (URL + column → indicator name); to use it as a feature add `directFeature("<indicator>").` in `20_aggregates.rls` and a label in `FEATURE_LABELS` (`service/catalogue.py`) | `vdkg all` |
| add another City of Vienna point layer | add a `PointLayer` to `POINT_LAYERS` in `sources.py`; map its category in the `subClassOf` / `countedClass` facts of `10_mapping.rls` / `20_aggregates.rls` | `vdkg all` |
| change what a preference means | edit its `signal(...)` / `required(...)` facts in `30_traits.rls` | `vdkg reason`, `vdkg embed` |
| add a new preference | add `signal`/`required` facts in `30_traits.rls` and a `Preference` in `service/catalogue.py` | `vdkg reason`, `vdkg embed` |
| change level thresholds (thirds) | the `level(...)` rules at the top of `30_traits.rls` | `vdkg reason`, `vdkg embed` |
| change transfer penalty / max travel time | `+ 4` and `<= 45` in `40_transit.rls` (keep the limit ≤ 45 — see below) | `vdkg reason`, `vdkg embed` |
| change scoring of recommendations | `contribution(...)` rules in `50_recommend.rls` / `55_similarity.rls` | restart `vdkg serve` |
| change embedding models / hyperparameters | `MODELS`, `SEEDS`, `TrainingConfig` in `src/vdkg/embeddings/train.py` | `vdkg embed` |

The web app only needs `data/processed/`, `artifacts/` and `web/`; everything else can be regenerated.

## Moving to another machine

1. Copy the repository (or `git clone` it), including `data/` and `artifacts/`.
2. Run the *Quick start* setup (venv, packages, `python tools/setup_nemo.py`).
3. `vdkg serve` — done. Only rerun the pipeline if data or rules change.

## Configuration

| Environment variable | Meaning |
|---|---|
| `VDKG_GTFS_DIR` | folder with an extracted GTFS feed (default `data/raw/gtfs`, downloaded if missing) |
| `VDKG_NEMO` | path to a Nemo executable (default: `tools/nemo/nemo_v0.10.1_*/nmo[.exe]`) |

## Tests and code quality

```bash
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check src tests
.venv\Scripts\ruff format src tests
```

The rule and service tests are skipped automatically if Nemo or the materialised KG are missing.

## Troubleshooting

- **"Nemo not found"** → run `python tools/setup_nemo.py` (or set `VDKG_NEMO`).
- **Port 8000 in use** → `vdkg serve --port 8080`.
- **Similar-districts page says no embeddings** → run `vdkg embed`.
- **`vdkg reason` uses a lot of memory / never finishes** → the transit recursion enumerates path
  costs; keep the travel-time limit at ≤ 45 minutes and segment times in whole minutes.
- **Map without background** → the basemap tiles come from basemap.at and need internet access.

## Layout

| Path | Content |
|---|---|
| `src/vdkg/ingest/` | loaders: MA 23 statistics, City of Vienna WFS layers, OSM (Overpass), GTFS, district geometry, record-linkage candidates |
| `src/vdkg/kg/` | ground relations (`schema.py`, `build.py`) and triples for embeddings |
| `src/vdkg/reasoning/rules/` | Nemo programs: `10_mapping`, `20_aggregates`, `30_traits`, `40_transit`, `50_recommend`, `55_similarity` |
| `src/vdkg/reasoning/` | Nemo wrapper and offline materialisation |
| `src/vdkg/embeddings/` | training, similarity, completion experiment |
| `src/vdkg/service/` | preference catalogue, KG access, recommender, district profiles |
| `src/vdkg/api/` | FastAPI routes (`/api/...`) and static hosting of `web/` |
| `src/vdkg/report/` | verification, traces, examples, figures for the report |
| `tools/` | Nemo setup, screenshots, submission packaging |
| `web/` | frontend: vanilla JS modules, Leaflet, hand-written CSS |
| `data/` | `raw/` downloads (not committed), `snapshots/` OSM, `processed/` tables, `kg/` ground facts |
| `artifacts/` | `materialized/` reasoning results, `embeddings/` models, metrics, similarities, `report/` evidence |
| `docs/` | plan, data sources, portfolio notes, AI usage log |
| `tests/` | parsers, a rule smoke test, recommender and API |

## Data sources

- Stadt Wien – data.wien.gv.at (CC BY 4.0): district statistics (MA 23, MA 20), WFS layers, district boundaries
- Wiener Linien – data.wien.gv.at (CC BY 4.0): GTFS timetables
- © OpenStreetMap contributors (ODbL): bars, restaurants, cafés, pitches, gyms, pools
- Basemap: basemap.at

See `docs/DATA_SOURCES.md` for all URLs.
