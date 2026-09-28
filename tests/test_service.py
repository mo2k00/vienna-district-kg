import pytest

from vdkg.config import MATERIALIZED

pytestmark = pytest.mark.skipif(
    not (MATERIALIZED / "offers.csv").exists(), reason="run `vdkg reason` first"
)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from vdkg.api.main import app

    return TestClient(app)


@pytest.fixture(scope="module")
def recommender():
    from vdkg.service.knowledge import KnowledgeBase
    from vdkg.service.recommender import Recommender

    return Recommender(KnowledgeBase())


def test_every_district_gets_a_recommendation_node(recommender):
    from vdkg.service.recommender import RecommendationRequest

    result = recommender.recommend(RecommendationRequest({"going_out": 3}))
    assert len(result.recommendations) == 23
    assert len({r.node for r in result.recommendations}) == 23
    assert result.recommendations[0].score >= result.recommendations[-1].score


def test_commute_constraint_excludes_far_districts(recommender):
    from vdkg.service.recommender import RecommendationRequest

    karlsplatz = next(s for s in recommender.knowledge.stations.values() if s.name == "Karlsplatz")
    result = recommender.recommend(
        RecommendationRequest({"green_quiet": 2}, commute_station=karlsplatz.id, commute_minutes=10)
    )
    assert result.excluded
    assert all(r.commute_minutes <= 10 for r in result.recommendations)
    assert not {r.district for r in result.recommendations} & set(result.excluded)


def test_invalid_requests_are_rejected(recommender):
    from vdkg.service.recommender import RecommendationRequest

    with pytest.raises(ValueError):
        recommender.recommend(RecommendationRequest({}))
    with pytest.raises(ValueError):
        recommender.recommend(RecommendationRequest({"unknown": 1}))


def test_api_endpoints(client):
    assert client.get("/api/meta").status_code == 200
    response = client.post(
        "/api/recommend", json={"preferences": {"family": 2}, "nearby_minutes": 5}
    )
    assert response.status_code == 200
    assert response.json()["recommendations"][0]["matches"][0]["preference"] == "family"
    assert client.post("/api/recommend", json={"preferences": {}}).status_code == 422
    assert client.get("/api/districts/d99").status_code == 404
    assert client.get("/api/districts/d07").json()["name"] == "Neubau"


def test_reasoning_matches_reference_implementations():
    from vdkg.report.verify import run
    from vdkg.service.knowledge import KnowledgeBase

    result = run(KnowledgeBase())
    assert result["travel_times"]["mismatches"] == 0
    assert result["ranks"]["mismatches"] == 0
    assert result["sport_venues"]["mismatches"] == 0
