"""Identifiers and source relations of the ground (extensional) part of the KG."""

from dataclasses import dataclass


def district_id(number: int) -> str:
    return f"d{int(number):02d}"


def district_number(identifier: str) -> int:
    return int(identifier.lstrip("d"))


@dataclass(frozen=True)
class Relation:
    name: str
    columns: tuple[str, ...]


DISTRICT = Relation("district", ("district", "name", "number"))
OBSERVATION = Relation("observation", ("district", "indicator", "value", "year", "source"))
ADJACENT = Relation("adjacent", ("district_a", "district_b"))
POI = Relation("poi", ("key", "category", "district", "source"))
POI_ID = Relation("poi_id", ("key", "id"))
POI_AREA = Relation("poi_area", ("key", "area_m2"))
POI_SPORT = Relation("poi_sport", ("id", "sport", "district"))
POI_MATCH = Relation("poi_match", ("id_a", "id_b", "sport"))
POI_DECLARED = Relation("poi_declared", ("key", "district"))
STATION = Relation("station", ("station", "name", "district"))
SEGMENT = Relation("segment", ("from_station", "to_station", "line", "minutes", "trips"))
STATION_LINE = Relation("station_line", ("station", "line", "mode"))

GROUND_RELATIONS = (
    DISTRICT,
    OBSERVATION,
    ADJACENT,
    POI,
    POI_ID,
    POI_AREA,
    POI_SPORT,
    POI_MATCH,
    POI_DECLARED,
    STATION,
    SEGMENT,
    STATION_LINE,
)
