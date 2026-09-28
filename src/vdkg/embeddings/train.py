from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from pykeen.pipeline import PipelineResult, pipeline
from pykeen.triples import TriplesFactory


@dataclass(frozen=True)
class TrainingConfig:
    model: str
    embedding_dim: int = 64
    epochs: int = 300
    batch_size: int = 128
    learning_rate: float = 0.01
    negatives_per_positive: int = 10


MODELS = (TrainingConfig("TransE"), TrainingConfig("RotatE"))
SEEDS = (0, 1, 2, 3, 4)


def factory(triples: pd.DataFrame, reference: TriplesFactory | None = None) -> TriplesFactory:
    labeled = triples[["head", "relation", "tail"]].to_numpy(dtype=str)
    if reference is None:
        return TriplesFactory.from_labeled_triples(labeled)
    return TriplesFactory.from_labeled_triples(
        labeled, entity_to_id=reference.entity_to_id, relation_to_id=reference.relation_to_id
    )


def train(
    config: TrainingConfig,
    training: TriplesFactory,
    testing: TriplesFactory,
    seed: int,
    validation: TriplesFactory | None = None,
) -> PipelineResult:
    filters = [training.mapped_triples] + ([validation.mapped_triples] if validation else [])
    return pipeline(
        training=training,
        testing=testing,
        validation=validation,
        model=config.model,
        model_kwargs={"embedding_dim": config.embedding_dim},
        optimizer="Adam",
        optimizer_kwargs={"lr": config.learning_rate},
        negative_sampler_kwargs={"num_negs_per_pos": config.negatives_per_positive},
        training_kwargs={"num_epochs": config.epochs, "batch_size": config.batch_size},
        evaluation_kwargs={"additional_filter_triples": filters},
        random_seed=seed,
        device="cpu",
        use_tqdm=False,
    )


def entity_vectors(result: PipelineResult, labels: list[str]) -> np.ndarray:
    """Real-valued entity vectors; complex ones (RotatE) are split into real and imaginary parts."""
    ids = torch.as_tensor([result.training.entity_to_id[label] for label in labels])
    with torch.no_grad():
        vectors = result.model.entity_representations[0](indices=ids)
    if vectors.is_complex():
        vectors = torch.cat([vectors.real, vectors.imag], dim=-1)
    return vectors.cpu().numpy()


def link_prediction_metrics(result: PipelineResult) -> dict[str, float]:
    metrics = result.metric_results
    return {
        "mrr": float(metrics.get_metric("both.realistic.inverse_harmonic_mean_rank")),
        "hits_at_1": float(metrics.get_metric("both.realistic.hits_at_1")),
        "hits_at_3": float(metrics.get_metric("both.realistic.hits_at_3")),
        "hits_at_10": float(metrics.get_metric("both.realistic.hits_at_10")),
    }
