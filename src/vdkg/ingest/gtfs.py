import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from vdkg.config import GTFS_DIR, RAW
from vdkg.ingest.geo import DistrictMap
from vdkg.ingest.http import USER_AGENT
from vdkg.ingest.sources import GTFS_URL

REQUIRED_FILES = ("stops.txt", "stop_times.txt", "trips.txt", "routes.txt")
CHUNK_ROWS = 2_000_000
MIN_SEGMENT_SECONDS = 30
ROUTE_TYPES = {"0": "tram", "1": "subway", "2": "rail", "3": "bus", "7": "funicular"}


def ensure_gtfs(directory: Path = GTFS_DIR) -> Path:
    if all((directory / name).exists() for name in REQUIRED_FILES):
        return directory
    archive = RAW / "gtfs.zip"
    with requests.get(GTFS_URL, headers={"User-Agent": USER_AGENT}, stream=True, timeout=600) as r:
        r.raise_for_status()
        with archive.open("wb") as target:
            for block in r.iter_content(chunk_size=1 << 20):
                target.write(block)
    with zipfile.ZipFile(archive) as bundle:
        for name in REQUIRED_FILES:
            bundle.extract(name, directory)
    return directory


def station_of(stop_ids: pd.Series) -> pd.Series:
    """Platform ids `at:49:1664:0:4` collapse to their station `at:49:1664`."""
    return stop_ids.str.split(":").str[:3].str.join(":")


def _seconds(times: pd.Series) -> np.ndarray:
    parts = times.str.split(":", expand=True).astype(int)
    return (parts[0] * 3600 + parts[1] * 60 + parts[2]).to_numpy()


def load_stations(directory: Path, districts: DistrictMap) -> pd.DataFrame:
    stops = pd.read_csv(directory / "stops.txt", dtype=str)
    stops["station"] = station_of(stops["stop_id"])
    stops[["stop_lat", "stop_lon"]] = stops[["stop_lat", "stop_lon"]].astype(float)
    stations = stops.groupby("station").agg(
        name=("stop_name", "first"), lat=("stop_lat", "mean"), lon=("stop_lon", "mean")
    )
    stations["district"] = districts.locate(stations["lon"].to_numpy(), stations["lat"].to_numpy())
    return stations[stations["district"] > 0].reset_index()


def _trip_routes(directory: Path) -> pd.DataFrame:
    trips = pd.read_csv(directory / "trips.txt", dtype=str, usecols=["trip_id", "route_id"])
    routes = pd.read_csv(
        directory / "routes.txt", dtype=str, usecols=["route_id", "route_short_name", "route_type"]
    )
    routes["mode"] = routes["route_type"].map(ROUTE_TYPES).fillna("other")
    return trips.merge(routes, on="route_id")[["trip_id", "route_short_name", "mode"]]


def load_segments(directory: Path, stations: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Mean in-vehicle seconds between consecutive stations per line, plus the lines per station.

    GTFS times have minute resolution, so single segments are often 0 or 60 seconds; the mean over
    all trips is a better estimate than the median.
    """
    trip_routes = _trip_routes(directory).set_index("trip_id")
    known = set(stations["station"])
    segments, served, carry = [], [], None
    reader = pd.read_csv(
        directory / "stop_times.txt",
        dtype=str,
        usecols=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
        chunksize=CHUNK_ROWS,
    )
    for chunk in reader:
        if carry is not None:
            chunk = pd.concat([carry, chunk], ignore_index=True)
        last_trip = chunk["trip_id"].iloc[-1]
        carry = chunk[chunk["trip_id"] == last_trip]
        chunk = chunk[chunk["trip_id"] != last_trip]
        segments.append(_chunk_segments(chunk, known, trip_routes))
        served.append(_chunk_served(chunk, known, trip_routes))
    segments.append(_chunk_segments(carry, known, trip_routes))
    served.append(_chunk_served(carry, known, trip_routes))

    all_segments = pd.concat(segments, ignore_index=True)
    keys = ["from_station", "to_station", "line"]
    summary = all_segments.groupby(keys)["seconds"].agg(["mean", "size"])
    summary["seconds"] = np.maximum(MIN_SEGMENT_SECONDS, summary["mean"].round()).astype(int)
    summary = summary.rename(columns={"size": "trips"})[["seconds", "trips"]].reset_index()
    lines = pd.concat(served, ignore_index=True).drop_duplicates()
    return summary, lines.sort_values(["station", "line"]).reset_index(drop=True)


def _chunk_segments(
    chunk: pd.DataFrame, known: set[str], trip_routes: pd.DataFrame
) -> pd.DataFrame:
    chunk = chunk.assign(
        station=station_of(chunk["stop_id"]), seq=chunk["stop_sequence"].astype(int)
    ).sort_values(["trip_id", "seq"])
    following = chunk.shift(-1)
    same_trip = chunk["trip_id"] == following["trip_id"]
    frame = pd.DataFrame(
        {
            "from_station": chunk["station"][same_trip],
            "to_station": following["station"][same_trip],
            "seconds": _seconds(following["arrival_time"][same_trip])
            - _seconds(chunk["departure_time"][same_trip]),
            "line": chunk["trip_id"][same_trip].map(trip_routes["route_short_name"]),
        }
    )
    keep = (
        frame["from_station"].isin(known)
        & frame["to_station"].isin(known)
        & (frame["from_station"] != frame["to_station"])
        & (frame["seconds"] >= 0)
    )
    return frame[keep]


def _chunk_served(chunk: pd.DataFrame, known: set[str], trip_routes: pd.DataFrame) -> pd.DataFrame:
    pairs = pd.DataFrame(
        {"station": station_of(chunk["stop_id"]), "trip_id": chunk["trip_id"]}
    ).drop_duplicates()
    pairs = pairs[pairs["station"].isin(known)].join(trip_routes, on="trip_id", how="inner")
    return pairs.rename(columns={"route_short_name": "line"})[["station", "line", "mode"]]
