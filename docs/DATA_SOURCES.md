# Data sources (scouted 2026-09-26)

All City of Vienna data: licence **CC BY 4.0**, attribution "Datenquelle: Stadt Wien – data.wien.gv.at".
Wiener Linien data: **CC BY 4.0**, "Datenquelle: Wiener Linien – data.wien.gv.at".
Catalogue search API used: `https://www.data.gv.at/api/hub/search/search?q=...&filter=dataset`,
dataset metadata: `https://www.data.gv.at/api/hub/search/datasets/<id>`.

## A. MA 23 district statistics ("… seit 20xx – Bezirke Wien")
Uniform CSV: line 1 = title, line 2 = header `NUTS;DISTRICT_CODE;SUB_DISTRICT_CODE;REF_YEAR;REF_DATE;…`,
`;`-separated, German number format (`1.234,56`). DISTRICT_CODE `9xx00` = district xx, `90000` = Vienna total.

| Key | Dataset | Main indicators | Latest year | CSV |
|---|---|---|---|---|
| income_net | Durchschnittliches Nettoeinkommen seit 2002 | avg. annual net income per employee (total/m/f) | 2021 | https://www.wien.gv.at/gogv/l9ogdviebezbizecnincsex2002f |
| density | Bevölkerungsdichte seit 2002 | population, area km², inhabitants/km² | 2025 | https://www.wien.gv.at/gogv/l9ogdviebezbizpopden2002f |
| avg_age | Durchschnittsalter seit 2002 | average age | 2025 | https://www.wien.gv.at/gogv/l9ogdviebezbizpopage2002f |
| unemployed | Arbeitslose Personen seit 2002 | unemployed 15–64 per 1,000 inhabitants | 2023 | https://www.wien.gv.at/gogv/l9ogdviebezbizempsexuep2002f |
| education | Bildungsstand seit 2008 | % by highest education (incl. university) | 2023 | https://www.wien.gv.at/gogv/l9ogdviebezbizeduatt2008f |
| household_type | Bevölkerung nach Typ des Haushalts seit 2012 | single-person, couples, with kids, … | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezpopsexhhtyp2012f |
| traffic_area | Verkehrsflächen seit 2002 | road / pedestrian / cycle area per 1,000 inh. | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezbiztectra2002f |
| medical | Medizinische Versorgung seit 2002 | doctors, dentists, pharmacies per 1,000 inh. | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezbizmedsup2002f |
| tourism | Gästeübernachtungen seit 2002 | overnight stays per 1,000 inh. | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezbizecntou2002f |

Further MA 23 series available (not downloaded): nationality, birth country, household size,
family type, births/deaths, migration flows, commuters, dogs, cars by brand/kW, eligible voters,
population forecast 2023–2043.

## B. Other district tables (MA 18 / MA 20)
| Key | Dataset | Indicators | Year | CSV |
|---|---|---|---|---|
| car_density | PKW-Dichte der Bezirke Wien | cars per 1,000 inhabitants | 2024 | https://www.wien.gv.at/data/ogd/ma20/pkwdichte2024.csv |
| bike_infra | Radinfrastruktur nach Bezirken | cycle path length / area share | 2023 | https://go.gv.at/l9ogdverkehrsflaechenbezirke2023 |

## C. Point / polygon data (WFS, EPSG:4326, CSV) — aggregate per district
WFS base: `https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&outputFormat=csv&typeName=ogdwien:<TYPE>`

| Key | TYPE | Rows | District link |
|---|---|---|---|
| parks | PARKINFOOGD | 1054 | `BEZIRK` column (+ `FLAECHE` area, playground, water, dog zone) |
| schools | SCHULEOGD | 806 | `ADRESSE` prefix "11., …" |
| kindergartens | KINDERGARTENOGD | 1677 | `PLZ` (1170 → district 17) |
| universities | UNIVERSITAETOGD | 161 | `ADRESSE` prefix |
| markets | MAERKTEOGD | 23 | coordinates only → spatial join |
| green_public | OEFFGRUENFLOGD | 1936 | polygons → spatial join |
| district_borders | BEZIRKSGRENZEOGD | 23 | polygons → district adjacency graph (for recursion) |

## C2. Leisure point data (WFS, same base URL) — added 2026-09-26
| Key | TYPE | Rows | District link | Notes |
|---|---|---|---|---|
| sport_facilities | SPORTSTAETTENOGD | 1543 | `ADRESSE` prefix | `SPORTSTAETTEN_ART`: pitches, halls, table tennis, skate, beach volleyball, pools… |
| playgrounds | SPIELPLATZPUNKTOGD | 773 | `BEZIRK` | `SPIELPLATZ_DETAIL`: Fußball 258, Basketball 184, Volleyball 68…; `TYP_DETAIL` Ballspielplatz/Käfig |
| museums | MUSEUMOGD | 137 | `BEZIRK` | culture |

## C3. OpenStreetMap (ODbL, "© OpenStreetMap contributors") via Overpass API
Query tested 2026-09-26 (area Wien admin_level 4), 8,292 elements:
restaurant 3019, pitch 2685 (tennis 600, soccer 499, table_tennis 265, basketball 255, beachvolleyball 164),
cafe 1226, bar 447, sports_centre 314, fitness_centre 261, pub 250, nightclub 59, biergarten 16.
Only source for nightlife (bars/pubs/clubs); much better tennis coverage than city data.
Coordinates → district via spatial join with BEZIRKSGRENZEOGD.

## D. Wiener Linien (public transport) — `https://www.wienerlinien.at/ogd_realtime/doku/ogd/`
| File | Content |
|---|---|
| wienerlinien-ogd-haltestellen.csv | 2,007 stations (DIVA, name, lon/lat) |
| wienerlinien-ogd-haltepunkte.csv | 5,124 stop points (StopID, DIVA, lon/lat) |
| wienerlinien-ogd-linien.csv | 205 lines (U-Bahn, tram, bus; MeansOfTransport) |
| wienerlinien-ogd-fahrwegverlaeufe.csv | 87k rows: stop sequence per line & direction |
→ stops per district (spatial join), U-Bahn lines per district, district-to-district transit links.

## D2. Wiener Linien GTFS (timetables) — already downloaded
In `../kgcourse-project-starting-template/src/assets/data/wienerlinien/` (feed valid 2025-12 → 2026-08):
stops.txt (4,331 stops incl. Baden → filter to Vienna), routes.txt, trips.txt (434k),
stop_times.txt (8.2M rows, 717 MB), shapes.txt. Source: data.gv.at dataset ab4a73b6-1c2d-42e1-b4d9-049e04889cf0.
→ travel times between stops/districts (weighted transit graph).

## E0. Rent — course-sanctioned approach (from the course's example project)
`../kgcourse-project-starting-template/helpers/`: manually copy willhaben search-result JSON
(`https://www.willhaben.at/webapi/iad/search/atz/seo/immobilien/mietwohnungen/wien?rows=30&page=N`)
"like a normal user" (template explicitly says: do NOT scrape) → `extractor.py` → PRICE, POSTCODE,
LIVING_AREA, coordinates. 4 sample pages from 2023-02 exist (120 listings, 20 postcodes).

## E. Gaps (no usable open source found)
- **Crime by district**: no open data. Only press figures (LPD Wien via e.g. oe24) and Statista (paywall).
- **Rent by district**: no official open data. Commercial benchmarks exist (mietdaten.at, metrox.io,
  ohne-makler.at) — not open data.
- **Kaufpreissammlung Liegenschaften** (property transactions): former link `go.gv.at/l9kaufpreissammlungliegenschaften` now 404 — discontinued.
- Statistik Austria (data.statistik.gv.at): mostly the same census data MA 23 republishes; not needed.
- Optional: OpenStreetMap (ODbL) via Overpass for bars/restaurants/cafés (nightlife) — not yet tested.
