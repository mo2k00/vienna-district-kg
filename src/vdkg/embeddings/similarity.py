import numpy as np
import pandas as pd


def cosine_matrix(vectors: np.ndarray) -> np.ndarray:
    normalised = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    return normalised @ normalised.T


def feature_baseline(features: dict[str, dict[str, float]], districts: list[str]) -> np.ndarray:
    """Cosine similarity of standardised raw feature vectors — the non-graph baseline."""
    table = pd.DataFrame(features).T.loc[districts]
    standardised = (table - table.mean()) / table.std(ddof=0).replace(0, 1)
    return cosine_matrix(standardised.to_numpy())


def ranked_pairs(matrix: np.ndarray, districts: list[str]) -> pd.DataFrame:
    rows = []
    for i, district in enumerate(districts):
        order = [j for j in np.argsort(-matrix[i]) if j != i]
        rows.extend(
            (district, districts[j], rank, float(matrix[i, j]))
            for rank, j in enumerate(order, start=1)
        )
    return pd.DataFrame(rows, columns=["district", "other", "rank", "similarity"])


def upper_triangle(matrix: np.ndarray) -> np.ndarray:
    return matrix[np.triu_indices_from(matrix, k=1)]


def _top_k(row: np.ndarray, own: int, k: int) -> set[int]:
    return set([j for j in np.argsort(-row) if j != own][:k])


def top_k_overlap(a: np.ndarray, b: np.ndarray, k: int = 3) -> float:
    """Mean share of each district's k most similar districts that both matrices agree on."""
    return float(np.mean([len(_top_k(a[i], i, k) & _top_k(b[i], i, k)) / k for i in range(len(a))]))
