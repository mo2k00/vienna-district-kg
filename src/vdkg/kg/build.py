"""Turn the processed source tables into the ground relations the rules import."""

import logging

import pandas as pd

from vdkg.config import PROCESSED
from vdkg.kg import schema
from vdkg.kg.store import write_relation

log = logging.getLogger(__name__)


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED / f"{name}.csv")


def _symmetric(frame: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Store both directions; Nemo 0.10.1 mis-joins column-permuted copy rules."""
    swapped = frame.rename(columns={a: b, b: a})
    return pd.concat([frame, swapped], ignore_index=True)


def _with_district_ids(frame: pd.DataFrame, *columns: str) -> pd.DataFrame:
    return frame.assign(**{c: frame[c].map(schema.district_id) for c in columns})


def ground_relations() -> dict[schema.Relation, pd.DataFrame]:
    districts = _read("districts").rename(columns={"district": "number"})
    districts["district"] = districts["number"].map(schema.district_id)

    pois = _with_district_ids(_read("pois"), "district")
    pois["id"] = range(1, len(pois) + 1)
    poi_ids = pois.set_index("key")["id"]
    sports = _read("poi_sports").merge(pois[["key", "id", "district"]], on="key")
    matches = _read("poi_matches").assign(
        id_a=lambda m: m["key_a"].map(poi_ids), id_b=lambda m: m["key_b"].map(poi_ids)
    )
    declared = pois.dropna(subset=["declared_district"])
    declared = declared.assign(
        district=declared["declared_district"].astype(int).map(schema.district_id)
    )

    return {
        schema.DISTRICT: districts,
        schema.OBSERVATION: _with_district_ids(_read("observations"), "district"),
        schema.ADJACENT: _symmetric(
            _with_district_ids(_read("adjacency"), "district_a", "district_b"),
            "district_a",
            "district_b",
        ),
        schema.POI: pois,
        schema.POI_ID: pois,
        schema.POI_AREA: pois.dropna(subset=["area_m2"]),
        schema.POI_SPORT: sports,
        schema.POI_MATCH: _symmetric(matches, "id_a", "id_b"),
        schema.POI_DECLARED: declared,
        schema.STATION: _with_district_ids(_read("stations"), "district"),
        schema.SEGMENT: _read("segments").assign(
            minutes=lambda f: (f["seconds"] / 60).round().clip(lower=1).astype(int)
        ),
        schema.STATION_LINE: _read("station_lines"),
    }


def run() -> None:
    for relation, frame in ground_relations().items():
        write_relation(relation, frame)
        log.info("%s: %d facts", relation.name, len(frame))
