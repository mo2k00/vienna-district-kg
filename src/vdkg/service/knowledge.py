"""Read access to the materialised KG for the service layer."""

import json
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import pandas as pd

from vdkg.config import EMBEDDINGS, MATERIALIZED, PROCESSED
from vdkg.kg.schema import district_number
from vdkg.reasoning.nemo import read_export


@dataclass(frozen=True)
class District:
    id: str
    number: int
    name: str


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    district: str


class KnowledgeBase:
    def __init__(self, materialized: Path = MATERIALIZED, processed: Path = PROCESSED):
        self.materialized = materialized
        self.processed = processed

    def _relation(self, name: str) -> list[tuple]:
        return read_export(self.materialized / f"{name}.csv")

    @cached_property
    def districts(self) -> dict[str, District]:
        rows = sorted(self._relation("districtName"))
        return {d: District(d, district_number(d), name) for d, name in rows}

    @cached_property
    def features(self) -> dict[str, dict[str, float]]:
        table: dict[str, dict[str, float]] = defaultdict(dict)
        for district, feature, value in self._relation("feature"):
            table[district][feature] = value
        return dict(table)

    @cached_property
    def levels(self) -> dict[tuple[str, str], str]:
        return {(d, f): level for d, f, level in self._relation("level")}

    @cached_property
    def ranks(self) -> dict[tuple[str, str], int]:
        return {(d, f): rank for d, f, rank in self._relation("rank")}

    @cached_property
    def offers(self) -> dict[str, set[str]]:
        table: dict[str, set[str]] = defaultdict(set)
        for district, preference in self._relation("offers"):
            table[district].add(preference)
        return dict(table)

    @cached_property
    def evidence(self) -> dict[tuple[str, str], list[tuple[str, str]]]:
        table: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
        for district, preference, feature, level in self._relation("evidence"):
            table[(district, preference)].append((feature, level))
        return dict(table)

    @cached_property
    def district_times(self) -> dict[tuple[str, str], int]:
        return {(a, b): t for a, b, t in self._relation("districtTime")}

    @cached_property
    def travel_times(self) -> dict[tuple[str, str], int]:
        """Minutes from each district's hub to every station reachable within the bound."""
        return {(d, s): t for d, s, t in self._relation("travelTime")}

    @cached_property
    def neighbours(self) -> dict[str, list[str]]:
        table: dict[str, list[str]] = defaultdict(list)
        for a, b in self._relation("adjacent"):
            table[a].append(b)
        return {d: sorted(n) for d, n in table.items()}

    @cached_property
    def stations(self) -> dict[str, Station]:
        frame = pd.read_csv(self.processed / "stations.csv")
        return {
            row.station: Station(row.station, row.name, f"d{row.district:02d}")
            for row in frame.itertuples(index=False)
        }

    @cached_property
    def hubs(self) -> dict[str, Station]:
        return {d: self.stations[s] for d, s in self._relation("hub")}

    @cached_property
    def subway_lines(self) -> dict[str, list[str]]:
        table: dict[str, list[str]] = defaultdict(list)
        for district, line in self._relation("subwayLine"):
            table[district].append(line)
        return {d: sorted(lines) for d, lines in table.items()}

    @cached_property
    def observations(self) -> pd.DataFrame:
        frame = pd.read_csv(self.processed / "observations.csv")
        return frame.assign(district=frame["district"].map(lambda n: f"d{n:02d}"))

    @cached_property
    def venue_counts(self) -> dict[str, dict[str, int]]:
        table: dict[str, dict[str, int]] = defaultdict(dict)
        for district, category, count in self._relation("venues"):
            table[district][category] = count
        for district, sport, count in self._relation("sportVenues"):
            table[district][f"sport:{sport}"] = count
        return dict(table)

    @cached_property
    def stats(self) -> dict:
        stats = json.loads((self.materialized / "stats.json").read_text(encoding="utf-8"))
        metadata = json.loads((self.processed / "metadata.json").read_text(encoding="utf-8"))
        return {**stats, "metadata": metadata}

    @property
    def embedding_report(self) -> dict | None:
        path = EMBEDDINGS / "report.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def district_name(self, district: str) -> str:
        return self.districts[district].name
