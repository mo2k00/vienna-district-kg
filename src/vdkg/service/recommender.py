from dataclasses import dataclass, field
from typing import Literal

from vdkg.config import MATERIALIZED, RULES
from vdkg.reasoning.nemo import Nemo
from vdkg.service.catalogue import PREFERENCE_BY_ID
from vdkg.service.knowledge import KnowledgeBase

MAX_WEIGHT = 3
MAX_MINUTES = 45
REQUEST_ID = "request"

MatchStatus = Literal["in_district", "nearby", "missing"]


@dataclass(frozen=True)
class RecommendationRequest:
    preferences: dict[str, int]
    nearby_minutes: int = 10
    commute_station: str | None = None
    commute_minutes: int | None = None
    similar_to: str | None = None
    similar_weight: int = 2

    def validate(self, knowledge: KnowledgeBase) -> None:
        active = {p: w for p, w in self.preferences.items() if w > 0}
        if not active and not self.similar_to:
            raise ValueError("Select at least one preference or a district you like.")
        unknown = set(active) - set(PREFERENCE_BY_ID)
        if unknown:
            raise ValueError(f"Unknown preferences: {sorted(unknown)}")
        if any(w > MAX_WEIGHT for w in active.values()):
            raise ValueError(f"Weights must be between 0 and {MAX_WEIGHT}.")
        if not 0 <= self.nearby_minutes <= MAX_MINUTES:
            raise ValueError(f"Nearby minutes must be between 0 and {MAX_MINUTES}.")
        if self.commute_station is not None:
            if self.commute_station not in knowledge.stations:
                raise ValueError("Unknown station.")
            if not self.commute_minutes or not 1 <= self.commute_minutes <= MAX_MINUTES:
                raise ValueError(f"Commute minutes must be between 1 and {MAX_MINUTES}.")
        if self.similar_to is not None:
            if self.similar_to not in knowledge.districts:
                raise ValueError("Unknown district.")
            if not 1 <= self.similar_weight <= MAX_WEIGHT:
                raise ValueError(f"Similarity weight must be between 1 and {MAX_WEIGHT}.")

    def as_facts(self) -> str:
        lines = [
            f'request("{REQUEST_ID}").',
            f'nearbyLimit("{REQUEST_ID}", {self.nearby_minutes}).',
        ]
        lines += [
            f'prefers("{REQUEST_ID}", "{preference}", {weight}).'
            for preference, weight in self.preferences.items()
            if weight > 0
        ]
        if self.commute_station:
            lines.append(
                f'commute("{REQUEST_ID}", "{self.commute_station}", {self.commute_minutes}).'
            )
        if self.similar_to:
            lines.append(f'likes("{REQUEST_ID}", "{self.similar_to}", {self.similar_weight}).')
        return "\n".join(lines)

    @property
    def programs(self) -> list[str]:
        return ["50_recommend.rls"] + (["55_similarity.rls"] if self.similar_to else [])


@dataclass(frozen=True)
class Evidence:
    feature: str
    level: str


@dataclass(frozen=True)
class PreferenceMatch:
    preference: str
    weight: int
    status: MatchStatus
    via: str | None = None
    minutes: int | None = None
    evidence: tuple[Evidence, ...] = ()


@dataclass
class DistrictRecommendation:
    node: str
    district: str
    score: float
    matches: list[PreferenceMatch]
    commute_minutes: int | None = None
    similarity_rank: int | None = None


@dataclass
class RecommendationResult:
    recommendations: list[DistrictRecommendation]
    excluded: list[str] = field(default_factory=list)
    derived_facts: int = 0
    seconds: float = 0.0


class Recommender:
    def __init__(self, knowledge: KnowledgeBase, nemo: Nemo | None = None):
        self.knowledge = knowledge
        self.nemo = nemo or Nemo()

    def recommend(self, request: RecommendationRequest) -> RecommendationResult:
        request.validate(self.knowledge)
        result = self.nemo.run(
            [RULES / name for name in request.programs], MATERIALIZED, facts=request.as_facts()
        )

        nodes = {node: district for node, _, district in result["recommendation"]}
        scores = dict(result["score"])
        max_score = dict(result["maxScore"]).get(REQUEST_ID, 1)
        satisfied_in = {(node, p) for node, p in result["satisfiedIn"]}
        nearby = {(node, p): (via, t) for node, p, via, t in result["satisfiedNearby"]}
        commute = dict(result["commuteTime"])
        similarity = dict(result["similarToLiked"])

        recommendations = [
            DistrictRecommendation(
                node=node,
                district=district,
                score=round(100 * scores.get(node, 0) / max_score, 1),
                matches=self._matches(node, district, request, satisfied_in, nearby),
                commute_minutes=commute.get(node),
                similarity_rank=similarity.get(node),
            )
            for node, district in nodes.items()
        ]
        recommendations.sort(
            key=lambda r: (
                -r.score,
                r.commute_minutes or 0,
                self.knowledge.districts[r.district].number,
            )
        )
        return RecommendationResult(
            recommendations=recommendations,
            excluded=sorted(d for _, d in result["excluded"]),
            derived_facts=result.derived_facts,
            seconds=result.seconds,
        )

    def _matches(self, node, district, request, satisfied_in, nearby) -> list[PreferenceMatch]:
        matches = []
        for preference, weight in sorted(request.preferences.items(), key=lambda kv: -kv[1]):
            if weight <= 0:
                continue
            if (node, preference) in satisfied_in:
                status, via, minutes, where = "in_district", None, None, district
            elif (node, preference) in nearby:
                via, minutes = nearby[(node, preference)]
                status, where = "nearby", via
            else:
                status, via, minutes, where = "missing", None, None, district
            evidence = tuple(
                Evidence(f, level)
                for f, level in self.knowledge.evidence.get((where, preference), [])
            )
            matches.append(PreferenceMatch(preference, weight, status, via, minutes, evidence))
        return matches
