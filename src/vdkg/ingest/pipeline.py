import json
import logging
from datetime import date

import pandas as pd

from vdkg.config import PROCESSED, WEB
from vdkg.ingest.geo import DistrictMap
from vdkg.ingest.gtfs import ensure_gtfs, load_segments, load_stations
from vdkg.ingest.linkage import sport_venue_matches
from vdkg.ingest.ma23 import load_observations
from vdkg.ingest.osm import load_osm
from vdkg.ingest.wfs import load_point_layers

log = logging.getLogger(__name__)


def _write(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(PROCESSED / f"{name}.csv", index=False)
    log.info("wrote %s (%d rows)", name, len(frame))


def run() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    districts = DistrictMap.load()
    _write(districts.table(), "districts")
    _write(districts.adjacency(), "adjacency")
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    (WEB / "data" / "districts.geojson").write_text(
        json.dumps(districts.web_geojson()), encoding="utf-8"
    )

    observations = load_observations()
    _write(observations, "observations")

    city_pois, city_sports = load_point_layers()
    osm_pois, osm_sports, osm_date = load_osm()
    pois = pd.concat([city_pois, osm_pois], ignore_index=True)
    pois["district"] = districts.locate(pois["lon"].to_numpy(), pois["lat"].to_numpy())
    pois = pois[pois["district"] > 0]
    sports = pd.concat([city_sports, osm_sports], ignore_index=True)
    sports = sports[sports["key"].isin(pois["key"])].drop_duplicates()
    _write(pois, "pois")
    _write(sports, "poi_sports")
    _write(sport_venue_matches(pois, sports), "poi_matches")

    gtfs_dir = ensure_gtfs()
    stations = load_stations(gtfs_dir, districts)
    segments, lines = load_segments(gtfs_dir, stations)
    _write(stations, "stations")
    _write(segments, "segments")
    _write(lines, "station_lines")

    metadata = {
        "ingested": date.today().isoformat(),
        "osm_snapshot": osm_date,
        "indicator_years": observations.groupby("indicator")["year"].first().to_dict(),
    }
    (PROCESSED / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
