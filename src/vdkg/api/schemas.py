from typing import Literal

from pydantic import BaseModel, Field


class PreferenceOut(BaseModel):
    id: str
    label: str
    group: str
    description: str


class StationOut(BaseModel):
    id: str
    name: str
    district: str


class DistrictSummary(BaseModel):
    id: str
    number: int
    name: str
    offers: list[str]


class MetaOut(BaseModel):
    preferences: list[PreferenceOut]
    feature_labels: dict[str, str]
    districts: list[DistrictSummary]
    similarity_sources: list[str]
    max_minutes: int
    stats: dict
    embeddings: dict | None = None
    attributions: list[str]


class RecommendIn(BaseModel):
    preferences: dict[str, int] = Field(default_factory=dict)
    nearby_minutes: int = Field(10, ge=0, le=45)
    commute_station: str | None = None
    commute_minutes: int | None = Field(None, ge=1, le=45)
    similar_to: str | None = None
    similar_weight: int = Field(2, ge=1, le=3)


class EvidenceOut(BaseModel):
    feature: str
    label: str
    level: str


class MatchOut(BaseModel):
    preference: str
    label: str
    weight: int
    status: Literal["in_district", "nearby", "missing"]
    via: str | None
    via_name: str | None
    minutes: int | None
    evidence: list[EvidenceOut]


class RecommendationOut(BaseModel):
    node: str
    district: str
    name: str
    number: int
    score: float
    commute_minutes: int | None
    similarity_rank: int | None
    matches: list[MatchOut]


class RecommendOut(BaseModel):
    recommendations: list[RecommendationOut]
    excluded: list[str]
    derived_facts: int
    reasoning_ms: int


class FeatureOut(BaseModel):
    feature: str
    label: str
    value: float
    level: str
    rank: int
    year: int | None
    source: str | None


class OfferOut(BaseModel):
    preference: str
    label: str
    evidence: list[EvidenceOut]


class TravelTimeOut(BaseModel):
    district: str
    name: str
    minutes: int


class SimilarOut(BaseModel):
    district: str
    name: str
    rank: int
    similarity: float
    shared_levels: list[str]


class DistrictOut(BaseModel):
    id: str
    number: int
    name: str
    hub: StationOut
    subway_lines: list[str]
    neighbours: list[DistrictSummary]
    offers: list[OfferOut]
    features: list[FeatureOut]
    venues: dict[str, int]
    travel_times: list[TravelTimeOut]
