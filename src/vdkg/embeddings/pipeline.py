"""Train embedding models, evaluate them and publish district similarities."""

import csv
import json
import logging

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from vdkg.config import EMBEDDINGS, KG_DIR, MATERIALIZED
from vdkg.embeddings.evaluate import completion_experiment
from vdkg.embeddings.similarity import (
    cosine_matrix,
    feature_baseline,
    ranked_pairs,
    top_k_overlap,
    upper_triangle,
)
from vdkg.embeddings.train import (
    MODELS,
    SEEDS,
    entity_vectors,
    factory,
    link_prediction_metrics,
    train,
)
from vdkg.kg.triples import build_triples
from vdkg.service.knowledge import KnowledgeBase

log = logging.getLogger(__name__)

SPLIT = (0.8, 0.1, 0.1)
SPLIT_SEED = 42


def _summary(values: list[float]) -> dict[str, float]:
    return {"mean": round(float(np.mean(values)), 4), "std": round(float(np.std(values)), 4)}


def run() -> None:
    EMBEDDINGS.mkdir(parents=True, exist_ok=True)
    knowledge = KnowledgeBase()
    districts = sorted(knowledge.districts)
    triples = build_triples(knowledge)
    triples.to_csv(KG_DIR / "triples.tsv", sep="\t", index=False)
    log.info("%d triples, %d relations", len(triples), triples["relation"].nunique())

    training, validation, testing = factory(triples).split(list(SPLIT), random_state=SPLIT_SEED)
    baseline = feature_baseline(knowledge.features, districts)
    report: dict = {"triples": len(triples), "split": SPLIT, "models": {}}
    similarities: dict[str, np.ndarray] = {}

    for config in MODELS:
        runs, matrices = [], []
        for seed in SEEDS:
            result = train(config, training, testing, seed, validation)
            runs.append(link_prediction_metrics(result))
            matrices.append(cosine_matrix(entity_vectors(result, districts)))
            if seed == SEEDS[0]:
                _save_vectors(result, config.model, districts)
                result.save_to_directory(EMBEDDINGS / "models" / config.model)
            log.info("%s seed %d: %s", config.model, seed, runs[-1])

        mean_similarity = np.mean(matrices, axis=0)
        similarities[config.model] = mean_similarity
        pairwise = [upper_triangle(m) for m in matrices]
        report["models"][config.model] = {
            "config": config.__dict__,
            "link_prediction": {k: _summary([r[k] for r in runs]) for k in runs[0]},
            "seed_stability_spearman": _summary(
                [spearmanr(pairwise[0], p).statistic for p in pairwise[1:]]
            ),
            "vs_feature_baseline": {
                "spearman": round(
                    float(
                        spearmanr(
                            upper_triangle(mean_similarity), upper_triangle(baseline)
                        ).statistic
                    ),
                    4,
                ),
                "top3_overlap": round(top_k_overlap(mean_similarity, baseline, 3), 4),
            },
        }

    best = max(
        report["models"], key=lambda m: report["models"][m]["link_prediction"]["mrr"]["mean"]
    )
    report["serving_model"] = best
    for model, matrix in similarities.items():
        ranked_pairs(matrix, districts).to_csv(EMBEDDINGS / f"similarity_{model}.csv", index=False)
    ranked_pairs(baseline, districts).to_csv(EMBEDDINGS / "similarity_features.csv", index=False)
    _publish_similarity_facts(similarities[best], districts)

    completion = [completion_experiment(triples, config) for config in MODELS]
    (EMBEDDINGS / "completion.json").write_text(json.dumps(completion, indent=2), encoding="utf-8")
    report["completion"] = {
        c["model"]: {
            k: c[k] for k in ("hidden_facts", "accuracy", "majority_baseline", "off_by_two")
        }
        for c in completion
    }
    (EMBEDDINGS / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info("serving model: %s", best)


def _save_vectors(result, model: str, districts: list[str]) -> None:
    labels = sorted(result.training.entity_to_id)
    vectors = entity_vectors(result, labels)
    frame = pd.DataFrame(vectors, index=labels)
    frame.index.name = "entity"
    frame.to_csv(EMBEDDINGS / f"entities_{model}.csv")


def _publish_similarity_facts(matrix: np.ndarray, districts: list[str]) -> None:
    """Make the learned similarity available to the rules as `similarRank(D, Other, Rank)` facts.

    Values are written as quoted string literals, the same form Nemo uses for its own exports.
    """
    pairs = ranked_pairs(matrix, districts)[["district", "other", "rank"]]
    quoted = pairs.assign(district='"' + pairs["district"] + '"', other='"' + pairs["other"] + '"')
    quoted.to_csv(
        MATERIALIZED / "similarRank.csv", index=False, header=False, quoting=csv.QUOTE_MINIMAL
    )
