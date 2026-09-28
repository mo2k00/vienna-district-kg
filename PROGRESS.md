# Progress

## Plan (see docs/PLAN.md)
| Day | Work |
|---|---|
| 26 Sep | ingestion, KG, rules, recommender, embeddings, API, web app, tests (done) |
| 27 Sep | review with user, polish, figures for the report |
| 28 Sep | push to remote → PC switch; report drafting |
| 29 Sep | report, cover pages |
| 30 Sep | report + cover pages, ZIP, submit |

## Done
- 2026-09-26: requirements, LOs, dataset scouting (`docs/DATA_SOURCES.md`), plan (`docs/PLAN.md`).
- 2026-09-26: package skeleton (`src/vdkg`), venv, deps (pandas 3, shapely, fastapi, pykeen 1.11, torch cpu).
- 2026-09-26: `vdkg ingest` (MA 23, WFS, OSM snapshot, district geo, GTFS), `vdkg build` (ground KG),
  `vdkg reason` (Nemo materialisation), `service/recommender.py` (per-request rules) — all working.
- 2026-09-26: `vdkg embed` (TransE/RotatE, 5 seeds, completion experiment, similarity facts for rules),
  FastAPI + web app (Recommend, Similar, District, About), 26 tests passing, ruff clean, README.

- 2026-09-28: `vdkg report` (verification vs. Python, Nemo traces, RDF/TriG + SPARQL, embedding
  examples, figures), shareable result links, headless screenshots, `tools/package_submission.py`
  (7.3 MB ZIP), 27 tests.

## How to run
See `README.md` (setup, `vdkg ingest|build|reason|embed|serve`).

## Next
- [ ] User's change requests
- [ ] Commit + push (user provides remote)
- [ ] Report draft (docx from pro-forma) + cover pages; user reworks scenario/reflection/AI declaration
- [ ] Final: `vdkg report`, screenshots, `python tools/package_submission.py`, submit PDF + ZIP

## Decisions (2026-09-26, by user)
- Use all relevant datasets from `docs/DATA_SOURCES.md` (valid sources only).
- **No rent** (no official open data) → limitation in report.
- Recommendation = user picks preferences in a web app (importance 0–3), commute to any station.
- UI: FastAPI + vanilla JS/Leaflet + hand-written CSS, separate pages, English.
- Course example project reviewed: reuse its GTFS data only.
- Changed by implementation: levels are terciles by rank (not ±25 % of mean) — see PORTFOLIO_NOTES.

## Open questions
- Git remote: user will push to a remote branch before switching PCs (nothing committed yet).
