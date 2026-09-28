# Portfolio notes

Running collection of facts, examples and numbers for the final report. Tag each with its LO.

## Scenario (LO9, LO11)
- Newcomers (esp. students) choosing one of Vienna's 23 districts; user states preferences
  (importance 0–3) + optional daily commute (any station, max minutes) → ranked, explained districts.

## KG construction (LO5, LO7)
- Sources: 10 MA 23 district series + MA 20 car density (27 indicators, latest complete year each,
  2021–2025), 8 City of Vienna WFS point layers, OpenStreetMap snapshot 2026-09-26 (8,556 elements),
  Wiener Linien GTFS (1,757 stations in Vienna, 7,545 line segments), district polygons (56 adjacent pairs).
- Ingest run: ~60–70 s (GTFS stop_times 717 MB streamed in 2M-row chunks).
- Ground KG: 63,150 facts in 12 relations (`data/kg/*.csv`); observations are reified with year + source.
- District resolution by point-in-polygon for all POIs; stated district (address prefix / BEZIRK / PLZ)
  kept for validation.
- **Schema mapping as rules** (`10_mapping.rls`): source relations → KG predicates; venue taxonomy
  (`subClassOf`) with recursive transitive closure, e.g. bar ⊑ nightlife_venue ⊑ leisure_venue.
- **Record linkage** (LO7): blocking by sport + matching within 40 m (Python, `linkage.py`) → 2,868
  candidate pairs; rules compute venues as transitive closure and pick a representative (#min id):
  4,782 sport records → **3,003 venues** (tennis 1,040 → 441: OSM maps single courts, city lists clubs).
- Reasoner: Nemo v0.10.1 (TU Dresden), Datalog with existential rules, stratified negation,
  aggregates; close to Vadalog syntax.

## Logic-based representation (LO2, LO6, LO8)
Rule files: 10_mapping, 20_aggregates, 30_traits, 40_transit, 50_recommend.
Example candidates for the "5 examples":
1. Taxonomy recursion: `isA(?P, ?Super) :- isA(?P, ?Class), subClassOfT(?Class, ?Super).`
2. Record linkage closure + representative (`sameVenue`, `representative(#min)`).
3. **Transit recursion** (bounded, line-aware, transfer penalty 4 min, ≤ 45 min):
   `ride(H, Next, Line, T) :- ride(H, S, Prev, T1), segment(S, Next, Line, T2, _), Line != Prev, T = T1+T2+4, T <= 45.`
4. Rank-based levels via aggregation (`below(#count)`), preference definitions as data
   (`signal`, `required`) → `offers(D, P)` with evidence.
5. **Object creation**: `recommendation(!Rec, ?R, ?D) :- candidate(?R, ?D).` + scores, explanations.
6. Stratified negation: commute constraint `excluded(R, D) :- hasCommute(R), district(D), ~commuteFeasible(R, D).`
7. Cleaning: `locationConflict(P, Stated, Actual)` → 31 of 6,144 records (0.5 %) contradict their coordinates.
- Two-stage reasoning: offline materialisation 1.89M derived facts in ~17 s; per request ~0.12 s / ~400 facts.
- Checks: ranks 713/713 identical to Python; earlier (non-line) travel times 39,820/39,820 identical to Dijkstra.
- Levels are **terciles by rank** (top 8 = high, bottom 8 = low) instead of ±25 % of the mean: distributions
  are very skewed (Innere Stadt: 161,680 overnight stays per 1,000 residents) so mean-based thresholds
  would mark almost no district "high"; ranks give balanced classes (also good for KGE).
- Travel times: mean of GTFS segment times (minute resolution makes the median collapse to 0) rounded to
  minutes; examples: Donaustadt→centre 17 min, Favoriten 18, Floridsdorf 21, Liesing 27.
- **Practical reasoner limitations found** (LO6 discussion):
  - Nemo 0.10.1 accepts one program file → wrapper concatenates the modular rule files.
  - `#min` over imported strings is not a consistent order → numeric ids for linkage.
  - A predicate defined by two column-permuted copy rules was mis-joined → symmetric input facts instead.
  - Line-aware transit at 1-second resolution exploded (> 3.8 GB, killed); at 1-minute resolution
    1.8M facts / 17 s. Path-based recursion without min-aggregation inside recursion enumerates all
    distinct path costs — shortest-path semantics would need aggregation in recursion (Vadalog supports
    monotonic aggregation, Nemo does not).
  - Non-linear transitive closure replaced by linear recursion (also the efficient fragment, cf. Vadalog).

## ML-based representation (LO1, LO6, LO8)
- Triples built from the **materialised** KG (logic output feeds ML): 1,104 triples, 35 relations,
  ~137 entities — `has_<feature>` → `<feature>:<low|medium|high>` (713), `adjacent_to` (112),
  `offers` → `pref:*` (124), `within_10_min_of` (116, from transit recursion), `served_by` → `line:U*` (39).
- PyKEEN 1.11 out of the box: TransE, RotatE; dim 64, 300 epochs, Adam lr 0.01, 10 negatives/positive,
  sLCWA; split 80/10/10 (seed 42), filtered evaluation; 5 seeds each; ~30 s per run on CPU.
- Link prediction (mean ± std over 5 seeds):
  - TransE: MRR 0.371 ± 0.024, Hits@1 0.169, Hits@3 0.469, Hits@10 0.785
  - RotatE: MRR 0.345 ± 0.022, Hits@1 0.161, Hits@3 0.416, Hits@10 0.780
- Seed stability of district similarity (Spearman between seeds): TransE 0.83, RotatE 0.91.
- vs. feature baseline (cosine of standardised raw features): Spearman TransE 0.55, RotatE 0.57;
  top-3 overlap TransE 0.28, RotatE 0.41 → embeddings capture the feature profile partially and add
  graph structure (adjacency, transit reachability).
- Similar districts (TransE): Neubau → Josefstadt, Rudolfsheim-Fünfhaus, Innere Stadt;
  Donaustadt → Leopoldstadt, Floridsdorf, Simmering; Hietzing → Liesing, Meidling, Penzing.
- **Completion experiment (LO8)**: hide 20 % of level facts (143), train without them, predict the
  level among {low, medium, high}: TransE 41 %, RotatE 48 % accuracy; random 33 %, majority 21 %
  (terciles are balanced, so the majority class is not informative); low↔high confusions 15 %.
  - TP: Josefstadt (d08) pct_tertiary_education → high (true high).
  - FP: Hernals (d17) overnight_stays_per_1000 → high (true medium); Margareten (d05) food_per_km2 → low (true high).
- Serving model chosen by MRR: TransE. Artefacts: `artifacts/embeddings/report.json`, `completion.json`.
- **Hybrid (LO12)**: learned similarity is published as facts `similarRank(D, Other, Rank)` and used by
  the rule `55_similarity.rls` as a soft preference ("similar to a district I like").

## Service (LO11)
- FastAPI JSON API (`/api/meta`, `/api/recommend`, `/api/districts/{id}`, `/similar`, `/stations`) +
  static web app (vanilla JS, Leaflet, basemap.at): Recommend, Similar districts, District profile, About.
- Per request: preferences (0–3), nearby limit, commute station + max minutes, optional liked district
  → Nemo run (~120 ms, ~300–450 facts) → ranked districts with explanations and evidence.
- Scoring: in district 2W, nearby W·(2 − T/limit) (decays with travel time), normalised to %.

## Evidence produced by `vdkg report` (2026-09-28)
- **Verification** (`artifacts/report/verification.json`): line-aware travel times 36,639/36,639 equal to a
  Dijkstra over (station, line) states with the same 4-min transfer rule; ranks 713/713; sport venues
  3,003 = union-find over the candidate matches.
- **Derivation traces** (`traces.md`, `nmo --trace`):
  - `offers(d07, going_out)` ← signalHits ← evidence ← level high ← rank 20 ← below(#count) ←
    feature 41.6 bars/km² ← 67 nightlife venues / 1.61 km².
  - `offers(d02, green_quiet)`: 2 of 3 signals (park share 18.4 % → rank 22 → high, …).
  - Recursion: `ride(Kagraner Platz → Karlsplatz, U1, 15)` unfolds stop by stop along the U1
    (Kagran 2, Alte Donau 4, … Praterstern 9, … Stephansplatz 13, Karlsplatz 15).
  - Observation: for aggregates Nemo reports *a* witness, not necessarily the minimal one
    (`busiest` shows Kalmusweg with 4 departures) → traced `ride` instead of `travelTime`.
- **Embedding examples** (`examples.json`, TransE seed 0): unit-norm 64-d vectors;
  h + r ≈ t: Neubau + has_nightlife → distances low 1.745 / medium 1.624 / **high 1.487** (true high);
  Donaustadt → **low 1.429** / medium 1.62 / high 1.783 (true low).
- **Suggested facts** (underived `offers` edges ranked by TransE): raw ranking dominated by
  `pref:family` (popularity bias: 10 districts offer it) → best candidate per preference:
  Landstraße → going_out (plausible, medium nightlife level), Josefstadt → green_quiet (implausible:
  dense inner district) → embedding suggestions need validation by rules (LO12).
- **PCA figure**: dense inner districts (1, 4–9, 15) and low-density outer districts (13, 14, 21–23)
  separate in both TransE and RotatE, learned from graph facts only.
- **RDF export** (LO4): TriG with named graphs `graph/ground` (102,979 triples) and `graph/derived`
  (6,602 triples; levels, offers, journeys). SPARQL "districts offering going out within 10 min of the
  centre" → Innere Stadt (0), Neubau (4). Same query in Datalog is one rule over `offers` and
  `districtTime`; SPARQL cannot express the recursive travel-time derivation itself without property
  paths over a precomputed graph (no path costs) → reasoning stays in Nemo, RDF for exchange.
- Figures: `artifacts/report/figures/{architecture,embeddings_pca,similarity_heatmaps}.png`;
  screenshots `artifacts/report/screenshots/*.png`.

## Reflection (LO4, LO11, LO12)
- Transit model ignores waiting times at the first stop and walking between stations; transfer = 4 min flat.

## Financial angle (LO10)

## Limitations
- No rent / crime data (no official open data at district level).
- OSM completeness varies; snapshot date 2026-09-26.
