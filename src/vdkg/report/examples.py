"""Concrete examples of the learned representation for the report."""

import json
from pathlib import Path

import torch
from pykeen.triples import TriplesFactory

from vdkg.config import EMBEDDINGS
from vdkg.service.knowledge import KnowledgeBase

ENTITY_EXAMPLES = ("d07", "d22", "nightlife_per_km2:high", "pref:going_out", "line:U3")
LEVELS = ("low", "medium", "high")


def load(model: str):
    directory = EMBEDDINGS / "models" / model
    trained = torch.load(directory / "trained_model.pkl", weights_only=False, map_location="cpu")
    factory = TriplesFactory.from_path_binary(directory / "training_triples")
    return trained, factory


def _entity(trained, factory, label: str) -> torch.Tensor:
    index = torch.as_tensor([factory.entity_to_id[label]])
    with torch.no_grad():
        return trained.entity_representations[0](indices=index)[0]


def _relation(trained, factory, label: str) -> torch.Tensor:
    index = torch.as_tensor([factory.relation_to_id[label]])
    with torch.no_grad():
        return trained.relation_representations[0](indices=index)[0]


def entity_vectors(trained, factory, dims: int = 5) -> list[dict]:
    rows = []
    for label in ENTITY_EXAMPLES:
        vector = _entity(trained, factory, label)
        rows.append(
            {
                "entity": label,
                "first_dims": [round(float(v), 3) for v in vector[:dims]],
                "norm": round(float(vector.norm()), 3),
            }
        )
    return rows


def translation_check(trained, factory, district: str, feature: str) -> dict:
    """TransE intuition h + r ≈ t: distance of h + r to each candidate level."""
    head = _entity(trained, factory, district)
    relation = _relation(trained, factory, f"has_{feature}")
    distances = {
        level: round(
            float((head + relation - _entity(trained, factory, f"{feature}:{level}")).norm()), 3
        )
        for level in LEVELS
    }
    return {"district": district, "feature": feature, "distances": distances}


def suggested_facts(trained, factory, knowledge: KnowledgeBase, top: int = 8) -> list[dict]:
    """The most plausible underived `offers` edge per preference.

    Taking one candidate per preference counters the popularity bias of TransE towards
    targets that already have many incoming edges (e.g. `pref:family`).
    """
    relation = factory.relation_to_id["offers"]
    preferences = [label for label in factory.entity_to_id if label.startswith("pref:")]
    pref_ids = torch.as_tensor([factory.entity_to_id[p] for p in preferences])
    candidates = []
    for district in knowledge.districts:
        head = factory.entity_to_id[district]
        with torch.no_grad():
            scores = trained.score_t(torch.as_tensor([[head, relation]]))[0, pref_ids]
        for preference, score in zip(preferences, scores.tolist(), strict=True):
            name = preference.removeprefix("pref:")
            if name not in knowledge.offers.get(district, set()):
                hits = len(knowledge.evidence.get((district, name), []))
                candidates.append(
                    {
                        "district": district,
                        "name": knowledge.district_name(district),
                        "preference": name,
                        "score": round(score, 3),
                        "rule_signals_met": hits,
                    }
                )
    best: dict[str, dict] = {}
    for candidate in candidates:
        current = best.get(candidate["preference"])
        if current is None or candidate["score"] > current["score"]:
            best[candidate["preference"]] = candidate
    return sorted(best.values(), key=lambda c: -c["score"])[:top]


def completion_examples() -> dict:
    results = json.loads((EMBEDDINGS / "completion.json").read_text(encoding="utf-8"))
    examples = {}
    for result in results:
        predictions = result["predictions"]
        examples[result["model"]] = {
            "true_positive": next(p for p in predictions if p["correct"]),
            "false_positive": next(p for p in predictions if not p["correct"]),
        }
    return examples


def run(knowledge: KnowledgeBase, model: str = "TransE") -> dict:
    trained, factory = load(model)
    return {
        "model": model,
        "entity_vectors": entity_vectors(trained, factory),
        "translation_checks": [
            translation_check(trained, factory, "d07", "nightlife_per_km2"),
            translation_check(trained, factory, "d22", "nightlife_per_km2"),
            translation_check(trained, factory, "d13", "park_share"),
        ],
        "suggested_offers": suggested_facts(trained, factory, knowledge),
        "completion": completion_examples(),
    }


def write(examples: dict, path: Path) -> None:
    path.write_text(json.dumps(examples, indent=2, ensure_ascii=False), encoding="utf-8")
