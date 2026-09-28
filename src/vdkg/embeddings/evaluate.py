from dataclasses import asdict, dataclass

import pandas as pd
import torch

from vdkg.embeddings.train import TrainingConfig, factory, link_prediction_metrics, train

LEVELS = ("low", "medium", "high")


@dataclass(frozen=True)
class CompletionPrediction:
    district: str
    feature: str
    true_level: str
    predicted_level: str
    scores: dict[str, float]

    @property
    def correct(self) -> bool:
        return self.true_level == self.predicted_level


def completion_experiment(
    triples: pd.DataFrame, config: TrainingConfig, seed: int = 0, holdout: float = 0.2
) -> dict:
    """Hide a share of the feature-level facts, train without them and predict them back."""
    attributes = triples[triples["relation"].str.startswith("has_")]
    hidden = attributes.sample(frac=holdout, random_state=seed)
    training = factory(triples.drop(hidden.index))
    hidden = hidden[hidden["tail"].isin(training.entity_to_id)]
    result = train(config, training, factory(hidden, reference=training), seed)

    predictions = [_predict(result, row) for row in hidden.itertuples(index=False)]
    majority = _majority_levels(triples.drop(hidden.index))
    return {
        "model": config.model,
        "seed": seed,
        "hidden_facts": len(predictions),
        "accuracy": sum(p.correct for p in predictions) / len(predictions),
        "majority_baseline": sum(majority[p.feature] == p.true_level for p in predictions)
        / len(predictions),
        "off_by_two": sum({p.true_level, p.predicted_level} == {"low", "high"} for p in predictions)
        / len(predictions),
        "link_prediction": link_prediction_metrics(result),
        "predictions": [asdict(p) | {"correct": p.correct} for p in predictions],
    }


def _predict(result, row) -> CompletionPrediction:
    feature = row.relation.removeprefix("has_")
    entity_to_id = result.training.entity_to_id
    head = entity_to_id[row.head]
    relation = result.training.relation_to_id[row.relation]
    with torch.no_grad():
        scores = result.model.score_t(torch.as_tensor([[head, relation]]))[0]
    candidates = {
        level: float(scores[entity_to_id[f"{feature}:{level}"]])
        for level in LEVELS
        if f"{feature}:{level}" in entity_to_id
    }
    predicted = max(candidates, key=candidates.get)
    return CompletionPrediction(row.head, feature, row.tail.split(":")[-1], predicted, candidates)


def _majority_levels(triples: pd.DataFrame) -> dict[str, str]:
    attributes = triples[triples["relation"].str.startswith("has_")]
    levels = attributes.assign(
        feature=attributes["relation"].str.removeprefix("has_"),
        level=attributes["tail"].str.split(":").str[-1],
    )
    return levels.groupby("feature")["level"].agg(lambda s: s.value_counts().idxmax()).to_dict()
