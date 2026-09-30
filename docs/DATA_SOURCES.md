# Data sources

All data is open data. `vdkg ingest` downloads every source and caches it in `data/raw/` (file names
and manual download instructions are in the README). The OpenStreetMap snapshot is stored in
`data/snapshots/osm_pois.json` so that results are reproducible.

| Provider | Licence | Attribution |
|---|---|---|
| City of Vienna (data.wien.gv.at) | CC BY 4.0 | Datenquelle: Stadt Wien – data.wien.gv.at |
| Wiener Linien (data.wien.gv.at) | CC BY 4.0 | Datenquelle: Wiener Linien – data.wien.gv.at |
| OpenStreetMap | ODbL | © OpenStreetMap contributors |
| basemap.at (map tiles in the web app) | CC BY 4.0 | Basemap: basemap.at |

## 1. District statistics (City of Vienna, MA 23)

One CSV per series: `;`-separated, a title line above the header, German number format
(`1.234,56`), districts coded as `9xx00`. The loader uses the latest year in which all 23 districts
have a value.

| Series | Indicators used | Year | URL |
|---|---|---|---|
| Population density | population, area (km²), residents per km² | 2025 | https://www.wien.gv.at/gogv/l9ogdviebezbizpopden2002f |
| Average age | average age | 2025 | https://www.wien.gv.at/gogv/l9ogdviebezbizpopage2002f |
| Net income | average annual net income | 2021 | https://www.wien.gv.at/gogv/l9ogdviebezbizecnincsex2002f |
| Unemployment | unemployed per 1,000 residents | 2023 | https://www.wien.gv.at/gogv/l9ogdviebezbizempsexuep2002f |
| Education | share with tertiary education | 2023 | https://www.wien.gv.at/gogv/l9ogdviebezbizeduatt2008f |
| Households | people by household type (single, shared, married, cohabiting, single parent) | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezpopsexhhtyp2012f |
| Families | families by type (with and without children, single parents) | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezfamtyp2012f |
| Traffic areas | road area, pedestrian zones, length of cycle paths | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezbiztectra2002f |
| Medical care | general practitioners, specialists and pharmacies per 1,000 residents | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezbizmedsup2002f |
| Tourism | overnight stays per 1,000 residents | 2024 | https://www.wien.gv.at/gogv/l9ogdviebezbizecntou2002f |

## 2. Car density (City of Vienna)

Cars per 1,000 residents per district, 2024: https://www.wien.gv.at/data/ogd/ma20/pkwdichte2024.csv

## 3. Map layers (City of Vienna WFS)

Base URL (`<TYPE>` as in the table), returning CSV in WGS84:

`https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&srsName=EPSG:4326&outputFormat=csv&typeName=ogdwien:<TYPE>`

Every record is assigned to a district by its coordinates (point in polygon). The district stated in
the record itself (`BEZIRK` column, address prefix such as `11., …` or postcode) is kept to detect
conflicting records.

| Layer | TYPE | Records | Notes |
|---|---|---|---|
| Parks | `PARKINFOOGD` | 1,054 | park area from `FLAECHE` |
| Schools | `SCHULEOGD` | 806 | |
| Kindergartens | `KINDERGARTENOGD` | 1,676 | |
| Universities | `UNIVERSITAETOGD` | 161 | |
| Markets | `MAERKTEOGD` | 23 | |
| Museums | `MUSEUMOGD` | 137 | |
| Sport facilities | `SPORTSTAETTENOGD` | 1,542 | sport types from `SPORTSTAETTEN_ART` |
| Playgrounds | `SPIELPLATZPUNKTOGD` | 773 | ball courts from `SPIELPLATZ_DETAIL` |
| District boundaries | `BEZIRKSGRENZEOGD` | 23 | polygons (`outputFormat=json`): district assignment, adjacency, maps |

## 4. Public transport timetables (Wiener Linien GTFS)

http://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip

Only `stops.txt`, `stop_times.txt`, `trips.txt` and `routes.txt` are used. Platforms are merged into
stations, and for every line the mean in-vehicle time between consecutive stations is computed from
the timetable. Result: 1,757 stations, 195 lines and 7,545 line segments.

## 5. OpenStreetMap (Overpass API)

Snapshot of 2026-09-26, queried from https://overpass-api.de/api/interpreter with the query in
`src/vdkg/ingest/osm.py`. It covers bars, pubs, clubs, beer gardens, restaurants, cafés, public
baths, pitches, sports and fitness centres, outdoor fitness stations, water parks and public
swimming pools within Vienna.

| Category | Records |
|---|---|
| Restaurants | 3,018 |
| Cafés | 1,226 |
| Bars / pubs / nightclubs / beer gardens | 447 / 250 / 59 / 16 |
| Pitches | 2,687 |
| Sports centres | 317 |
| Fitness centres / fitness stations | 261 / 205 |
| Swimming venues | 68 |

OpenStreetMap pitches and the city's sport facilities describe partly the same places. Records of the
same sport within 40 m of each other are linked and merged into one venue by the rules: 3,715
records with 4,782 sport entries become 3,003 venues.

## Not included

Crime and rent figures per district are not published as official open data, so the KG contains
neither.
