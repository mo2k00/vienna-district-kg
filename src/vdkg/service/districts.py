from dataclasses import dataclass
from functools import cached_property

import pandas as pd

from vdkg.config import EMBEDDINGS
from vdkg.service.catalogue import FEATURE_LABELS, PREFERENCE_BY_ID
from vdkg.service.knowledge import KnowledgeBase

SIMILARITY_SOURCES = ("TransE", "RotatE", "features")

# Features that come straight from a statistics series keep that series' year and source.
_OBSERVED_FEATURES = {
    "population_density": "population_density",
    "avg_age": "avg_age",
    "net_income": "net_income",
    "unemployed_per_1000": "unemployed_per_1000",
    "pct_tertiary_education": "pct_tertiary_education",
    "cars_per_1000": "cars_per_1000",
    "gps_per_1000": "gps_per_1000",
    "specialists_per_1000": "specialists_per_1000",
    "pharmacies_per_1000": "pharmacies_per_1000",
    "overnight_stays_per_1000": "overnight_stays_per_1000",
}


@dataclass(frozen=True)
class FeatureFact:
    feature: str
    label: str
    value: float
    level: str
    rank: int
    year: int | None
    source: str | None


@dataclass(frozen=True)
class SimilarDistrict:
    district: str
    rank: int
    similarity: float
    shared_levels: tuple[str, ...]


class DistrictService:
    def __init__(self, knowledge: KnowledgeBase):
        self.knowledge = knowledge

    @cached_property
    def _similarities(self) -> dict[str, pd.DataFrame]:
        tables = {}
        for source in SIMILARITY_SOURCES:
            path = EMBEDDINGS / f"similarity_{source}.csv"
            if path.exists():
                tables[source] = pd.read_csv(path)
        return tables

    @property
    def similarity_sources(self) -> list[str]:
        return list(self._similarities)

    def features(self, district: str) -> list[FeatureFact]:
        observed = self.knowledge.observations[self.knowledge.observations["district"] == district]
        provenance = observed.set_index("indicator")[["year", "source"]].to_dict("index")
        facts = []
        for feature, value in sorted(self.knowledge.features[district].items()):
            origin = provenance.get(_OBSERVED_FEATURES.get(feature, ""), {})
            facts.append(
                FeatureFact(
                    feature=feature,
                    label=FEATURE_LABELS.get(feature, feature),
                    value=value,
                    level=self.knowledge.levels[(district, feature)],
                    rank=self.knowledge.ranks[(district, feature)],
                    year=origin.get("year"),
                    source=origin.get("source"),
                )
            )
        return facts

    def offers(self, district: str) -> list[dict]:
        return [
            {
                "preference": preference,
                "label": PREFERENCE_BY_ID[preference].label,
                "evidence": [
                    {"feature": f, "label": FEATURE_LABELS.get(f, f), "level": level}
                    for f, level in self.knowledge.evidence.get((district, preference), [])
                ],
            }
            for preference in sorted(self.knowledge.offers.get(district, set()))
        ]

    def travel_times(self, district: str) -> list[tuple[str, int]]:
        times = [
            (other, minutes)
            for (origin, other), minutes in self.knowledge.district_times.items()
            if origin == district and other != district
        ]
        return sorted(times, key=lambda item: item[1])

    def similar(self, district: str, source: str, k: int = 5) -> list[SimilarDistrict]:
        if source not in self._similarities:
            raise ValueError(f"Unknown similarity source: {source}")
        table = self._similarities[source]
        rows = table[(table["district"] == district) & (table["rank"] <= k)].sort_values("rank")
        return [
            SimilarDistrict(
                row.other, int(row.rank), float(row.similarity), self._shared(district, row.other)
            )
            for row in rows.itertuples(index=False)
        ]

    def _shared(self, a: str, b: str) -> tuple[str, ...]:
        levels = self.knowledge.levels
        return tuple(
            sorted(
                f"{feature}:{level}"
                for (district, feature), level in levels.items()
                if district == a and level != "medium" and levels.get((b, feature)) == level
            )
        )
