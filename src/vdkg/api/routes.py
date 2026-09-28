from dataclasses import asdict
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from vdkg.api import schemas
from vdkg.ingest.sources import CITY_OF_VIENNA, OPENSTREETMAP, WIENER_LINIEN
from vdkg.service.catalogue import FEATURE_LABELS, PREFERENCE_BY_ID, PREFERENCES
from vdkg.service.districts import DistrictService
from vdkg.service.knowledge import KnowledgeBase
from vdkg.service.recommender import MAX_MINUTES, RecommendationRequest, Recommender

router = APIRouter(prefix="/api")


class Services:
    def __init__(self):
        self.knowledge = KnowledgeBase()
        self.recommender = Recommender(self.knowledge)
        self.districts = DistrictService(self.knowledge)


@lru_cache(maxsize=1)
def services() -> Services:
    return Services()


ServicesDep = Annotated[Services, Depends(services)]


def _summary(kb: KnowledgeBase, district: str) -> schemas.DistrictSummary:
    info = kb.districts[district]
    return schemas.DistrictSummary(
        id=info.id,
        number=info.number,
        name=info.name,
        offers=sorted(kb.offers.get(district, set())),
    )


def _require_district(kb: KnowledgeBase, district: str) -> None:
    if district not in kb.districts:
        raise HTTPException(status_code=404, detail="Unknown district")


@router.get("/meta", response_model=schemas.MetaOut)
def meta(s: ServicesDep):
    kb = s.knowledge
    return schemas.MetaOut(
        preferences=[schemas.PreferenceOut(**asdict(p)) for p in PREFERENCES],
        feature_labels=FEATURE_LABELS,
        districts=[_summary(kb, d) for d in kb.districts],
        similarity_sources=s.districts.similarity_sources,
        max_minutes=MAX_MINUTES,
        stats=kb.stats,
        embeddings=kb.embedding_report,
        attributions=[CITY_OF_VIENNA, WIENER_LINIEN, OPENSTREETMAP],
    )


@router.get("/stations", response_model=list[schemas.StationOut])
def stations(
    s: ServicesDep,
    q: str = Query("", max_length=60),
    limit: int = Query(12, le=50),
):
    needle = q.strip().lower()
    reachable = {station for (_, station) in s.knowledge.travel_times}
    matches = [
        st
        for st in s.knowledge.stations.values()
        if st.id in reachable and needle in st.name.lower()
    ]
    matches.sort(key=lambda st: (not st.name.lower().startswith(needle), st.name))
    return [schemas.StationOut(**asdict(st)) for st in matches[:limit]]


@router.post("/recommend", response_model=schemas.RecommendOut)
def recommend(body: schemas.RecommendIn, s: ServicesDep):
    kb = s.knowledge
    request = RecommendationRequest(**body.model_dump())
    try:
        result = s.recommender.recommend(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    def match(m):
        return schemas.MatchOut(
            preference=m.preference,
            label=PREFERENCE_BY_ID[m.preference].label,
            weight=m.weight,
            status=m.status,
            via=m.via,
            via_name=kb.district_name(m.via) if m.via else None,
            minutes=m.minutes,
            evidence=[
                schemas.EvidenceOut(
                    feature=e.feature, label=FEATURE_LABELS.get(e.feature, e.feature), level=e.level
                )
                for e in m.evidence
            ],
        )

    return schemas.RecommendOut(
        recommendations=[
            schemas.RecommendationOut(
                node=r.node,
                district=r.district,
                name=kb.district_name(r.district),
                number=kb.districts[r.district].number,
                score=r.score,
                commute_minutes=r.commute_minutes,
                similarity_rank=r.similarity_rank,
                matches=[match(m) for m in r.matches],
            )
            for r in result.recommendations
        ],
        excluded=result.excluded,
        derived_facts=result.derived_facts,
        reasoning_ms=round(result.seconds * 1000),
    )


@router.get("/districts/{district}", response_model=schemas.DistrictOut)
def district(district: str, s: ServicesDep):
    kb = s.knowledge
    _require_district(kb, district)
    info = kb.districts[district]
    hub = kb.hubs[district]
    return schemas.DistrictOut(
        id=info.id,
        number=info.number,
        name=info.name,
        hub=schemas.StationOut(**asdict(hub)),
        subway_lines=kb.subway_lines.get(district, []),
        neighbours=[_summary(kb, n) for n in kb.neighbours.get(district, [])],
        offers=s.districts.offers(district),
        features=[schemas.FeatureOut(**asdict(f)) for f in s.districts.features(district)],
        venues=kb.venue_counts.get(district, {}),
        travel_times=[
            schemas.TravelTimeOut(district=d, name=kb.district_name(d), minutes=m)
            for d, m in s.districts.travel_times(district)
        ],
    )


@router.get("/districts/{district}/similar", response_model=list[schemas.SimilarOut])
def similar(
    district: str,
    s: ServicesDep,
    source: str = Query("TransE"),
    k: int = Query(5, ge=1, le=22),
):
    kb = s.knowledge
    _require_district(kb, district)
    try:
        rows = s.districts.similar(district, source, k)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return [
        schemas.SimilarOut(
            district=r.district,
            name=kb.district_name(r.district),
            rank=r.rank,
            similarity=round(r.similarity, 4),
            shared_levels=list(r.shared_levels),
        )
        for r in rows
    ]
