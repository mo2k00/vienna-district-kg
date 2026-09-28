import re

import pandas as pd

from vdkg.ingest.http import fetch
from vdkg.ingest.numbers import parse_number
from vdkg.ingest.sources import POINT_LAYERS, PointLayer
from vdkg.ingest.sports import sports_in

POI_COLUMNS = ["key", "category", "name", "lon", "lat", "declared_district", "area_m2", "source"]

_ADDRESS_DISTRICT = re.compile(r"^\s*(\d{1,2})\.,")
_SPORT_TEXT_COLUMNS = ("SPORTSTAETTEN_ART", "SPIELPLATZ_DETAIL")


def _coordinates(shape_column: pd.Series) -> pd.DataFrame:
    parts = shape_column.str.extract(r"POINT \(([-\d.]+) ([-\d.]+)\)")
    return parts.astype(float).rename(columns={0: "lon", 1: "lat"})


def _declared_district(frame: pd.DataFrame) -> pd.Series:
    if "BEZIRK" in frame:
        return pd.to_numeric(frame["BEZIRK"], errors="coerce")
    if "ADRESSE" in frame:
        return pd.to_numeric(frame["ADRESSE"].str.extract(_ADDRESS_DISTRICT)[0], errors="coerce")
    if "PLZ" in frame:
        return pd.to_numeric(frame["PLZ"].str[1:3], errors="coerce")
    return pd.Series(float("nan"), index=frame.index)


def _name(frame: pd.DataFrame) -> pd.Series:
    for column in ("ANL_NAME", "NAME", "BEZEICHNUNG", "SPORTSTAETTEN_ART"):
        if column in frame:
            return frame[column].fillna("")
    return pd.Series("", index=frame.index)


def load_layer(layer: PointLayer) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(fetch(layer.url, f"wfs_{layer.key}.csv"), dtype=str)
    coords = _coordinates(frame["SHAPE"])
    pois = pd.DataFrame(
        {
            "key": "wfs:" + frame["FID"],
            "category": layer.category,
            "name": _name(frame),
            "lon": coords["lon"],
            "lat": coords["lat"],
            "declared_district": _declared_district(frame),
            "area_m2": frame["FLAECHE"].map(parse_number) if "FLAECHE" in frame else float("nan"),
            "source": layer.key,
        }
    )[POI_COLUMNS]

    sport_column = next((c for c in _SPORT_TEXT_COLUMNS if c in frame), None)
    sports = pd.DataFrame(columns=["key", "sport"])
    if sport_column:
        sports = (
            pd.DataFrame({"key": pois["key"], "sport": frame[sport_column].map(sports_in)})
            .explode("sport")
            .dropna()
        )
    return pois, sports


def load_point_layers() -> tuple[pd.DataFrame, pd.DataFrame]:
    loaded = [load_layer(layer) for layer in POINT_LAYERS]
    pois = pd.concat([p for p, _ in loaded], ignore_index=True)
    sports = pd.concat([s for _, s in loaded], ignore_index=True)
    return pois, sports
