"""Figures for the report."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402

from vdkg.config import EMBEDDINGS  # noqa: E402
from vdkg.service.knowledge import KnowledgeBase  # noqa: E402

PRIMARY = "#0f6e63"
SOFT = "#d8ede9"
LOGIC = "#f6e7da"
ACCENT = "#b7682a"
LEVEL_COLOURS = {"low": "#b7682a", "medium": "#8a948f", "high": "#0f6e63"}


def architecture(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.3)
    ax.axis("off")
    w, h = 1.75, 1.2
    boxes = [
        (0.2, 2.8, "Open data\nCity of Vienna\nWiener Linien · OSM", SOFT),
        (2.25, 2.8, "Ingest (Python)\nparsing · district lookup\nlinkage candidates", SOFT),
        (4.3, 2.8, "Ground facts D\n~38k facts\n12 relations", SOFT),
        (7.15, 2.8, "Materialised KG r(D)\n1.9M derived facts\nlevels · offers · times", SOFT),
        (10.05, 2.8, "Service\nper-request rules\n(existential)\nFastAPI + web app", SOFT),
        (5.72, 0.55, "Rules K (Nemo)\nmapping · aggregation\nlevels · transit recursion", LOGIC),
        (8.6, 0.55, "Embeddings l(D)\nTransE · RotatE\nsimilarity · completion", SOFT),
    ]
    for x, y, label, colour in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.04",
                linewidth=1.2,
                edgecolor=PRIMARY,
                facecolor=colour,
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8.2)

    def arrow(start, end, text="", colour=PRIMARY, offset=(0.0, 0.12)):
        ax.add_patch(
            FancyArrowPatch(
                start, end, arrowstyle="-|>", mutation_scale=12, color=colour, linewidth=1.3
            )
        )
        if text:
            ax.text(
                (start[0] + end[0]) / 2 + offset[0],
                (start[1] + end[1]) / 2 + offset[1],
                text,
                ha="center",
                fontsize=7.6,
                color=colour,
            )

    y = 2.8 + h / 2
    arrow((1.95, y), (2.25, y))
    arrow((4.0, y), (4.3, y))
    arrow((6.05, y), (7.15, y), "reasoning", ACCENT)
    arrow((6.6, 1.75), (6.6, y - 0.06), colour=ACCENT)
    arrow((8.9, y), (10.05, y), "queries")
    arrow((8.3, 2.8), (9.1, 1.75), "training triples", offset=(-0.75, -0.05))
    arrow((10.35, 1.4), (10.85, 2.8), "similarRank facts", offset=(0.75, -0.2))
    ax.text(
        0.2,
        0.25,
        "KG = (D, K; g, l, r): ground facts D, rules K, reasoning r, learning l",
        fontsize=7.8,
        color="#5d6b64",
    )
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def _vectors(model: str, districts: list[str]) -> np.ndarray:
    frame = pd.read_csv(EMBEDDINGS / f"entities_{model}.csv", index_col="entity")
    return frame.loc[districts].to_numpy()


def embedding_projection(knowledge: KnowledgeBase, path: Path) -> None:
    districts = sorted(knowledge.districts)
    colour_feature = "population_density"
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for ax, model in zip(axes, ("TransE", "RotatE"), strict=True):
        points = PCA(n_components=2, random_state=0).fit_transform(_vectors(model, districts))
        for (x, y), district in zip(points, districts, strict=True):
            level = knowledge.levels[(district, colour_feature)]
            ax.scatter(x, y, s=140, color=LEVEL_COLOURS[level], alpha=0.85, edgecolor="white")
            ax.text(
                x,
                y,
                str(knowledge.districts[district].number),
                ha="center",
                va="center",
                fontsize=7.5,
                color="white",
                fontweight="bold",
            )
        ax.set_title(f"{model}: district embeddings (PCA)", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=c, markersize=8, label=f"density {lvl}")
        for lvl, c in LEVEL_COLOURS.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def similarity_heatmaps(knowledge: KnowledgeBase, path: Path) -> None:
    districts = sorted(knowledge.districts)
    labels = [str(knowledge.districts[d].number) for d in districts]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
    sources = (("TransE", "TransE embedding"), ("features", "Feature baseline"))
    for ax, (source, title) in zip(axes, sources, strict=True):
        table = pd.read_csv(EMBEDDINGS / f"similarity_{source}.csv")
        matrix = table.pivot(index="district", columns="other", values="similarity")
        matrix = matrix.reindex(index=districts, columns=districts).fillna(1.0)
        image = ax.imshow(matrix.to_numpy(), cmap="BuGn", vmin=-0.2, vmax=1)
        ax.set_xticks(range(len(labels)), labels, fontsize=6.5)
        ax.set_yticks(range(len(labels)), labels, fontsize=6.5)
        ax.set_title(f"{title}: cosine similarity", fontsize=10)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def run(knowledge: KnowledgeBase, directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    architecture(directory / "architecture.png")
    embedding_projection(knowledge, directory / "embeddings_pca.png")
    similarity_heatmaps(knowledge, directory / "similarity_heatmaps.png")
    return ["architecture.png", "embeddings_pca.png", "similarity_heatmaps.png"]
