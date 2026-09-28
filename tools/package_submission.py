"""Build the submission ZIP: runnable repository + evidence folders following the report structure.

Usage: python tools/package_submission.py   →   dist/vienna-district-kg-submission.zip
Run `vdkg report` (and optionally `python tools/screenshots.py`) first.
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "dist" / "vienna-district-kg-submission.zip"
REPO = "repository"

EXCLUDED_PARTS = {
    ".venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    ".claude",
    ".idea",
}
EXCLUDED_PREFIXES = ("tools/nemo/", "data/raw/")

SECTIONS = {
    "2 - construction": {
        "readme": """# 2 – KG construction (LO5, LO7)

Code: `repository/src/vdkg/ingest/` (loaders, record-linkage candidates) and
`repository/src/vdkg/kg/` (ground relations, triples, RDF export).
Run: `vdkg ingest` then `vdkg build` (see `repository/README.md`).

- `DATA_SOURCES.md` — every dataset with its URL and licence.
- `metadata.json` — ingest date, OSM snapshot date, year of every indicator.
- Ground facts: `repository/data/kg/*.csv`; processed tables: `repository/data/processed/`.
- RDF version of the KG (ground + derived named graphs): `repository/data/kg/vienna_kg.trig`.
""",
        "files": {
            "docs/DATA_SOURCES.md": "DATA_SOURCES.md",
            "data/processed/metadata.json": "metadata.json",
        },
    },
    "3 - ML": {
        "readme": """# 3 – ML-based representation (LO1, LO6, LO8)

Code: `repository/src/vdkg/embeddings/` (PyKEEN training, similarity, completion experiment).
Run: `vdkg embed`.

- `report.json` — link prediction metrics (5 seeds), seed stability,
  comparison with the feature baseline.
- `completion.json` — completion experiment: hidden facts, predictions, scores.
- `examples.json` — embedding vectors, TransE translation check, suggested facts.
- `figures/` — PCA projection of district embeddings, similarity heatmaps.
""",
        "files": {
            "artifacts/embeddings/report.json": "report.json",
            "artifacts/embeddings/completion.json": "completion.json",
            "artifacts/report/examples.json": "examples.json",
            "artifacts/report/figures/embeddings_pca.png": "figures/embeddings_pca.png",
            "artifacts/report/figures/similarity_heatmaps.png": "figures/similarity_heatmaps.png",
        },
    },
    "4 - logic": {
        "readme": """# 4 – Logic-based representation (LO2, LO6, LO8)

Code: `repository/src/vdkg/reasoning/` — Nemo wrapper, materialisation, and the rule programs in
`rules/` (copied here). Run: `vdkg reason` (needs `python tools/setup_nemo.py`).

- `rules/` — 10_mapping, 20_aggregates, 30_traits, 40_transit (recursion), 50_recommend
  (existential rules), 55_similarity (embedding facts as soft preference).
- `traces.md` — derivation trees produced with `nmo --trace`.
- `verification.json` — reasoning results checked against independent Python implementations.
- `materialisation_stats.json` — derived facts and runtime.
""",
        "files": {
            "artifacts/report/traces.md": "traces.md",
            "artifacts/report/verification.json": "verification.json",
            "artifacts/materialized/stats.json": "materialisation_stats.json",
        },
        "globs": {"src/vdkg/reasoning/rules/*.rls": "rules"},
    },
    "5 - reflection": {
        "readme": """# 5 – Service and reflection (LO4, LO9–LO12)

Code: `repository/src/vdkg/service/`, `repository/src/vdkg/api/`, `repository/web/`.
Run: `vdkg serve` → http://127.0.0.1:8000.

- `screenshots/` — the web app (recommend, similar districts, district profile, about).
- `rdf_export.json` — RDF triple counts and a SPARQL query compared with the Datalog formulation.
- `figures/architecture.png` — architecture overview.
""",
        "files": {
            "artifacts/report/rdf_export.json": "rdf_export.json",
            "artifacts/report/figures/architecture.png": "figures/architecture.png",
        },
        "globs": {"artifacts/report/screenshots/*.png": "screenshots"},
    },
}

TOP_README = """# Vienna District KG — submission

Knowledge Graph-based district similarity and lifestyle recommendation (Moritz Lindner).

- `repository/` — the complete, runnable project (setup and usage: `repository/README.md`).
- `2 - construction/`, `3 - ML/`, `4 - logic/`, `5 - reflection/` — evidence for the report
  sections of the same name, each with a README pointing to the relevant code.

Quick start: see `repository/README.md` → *Quick start*, then `vdkg serve` and open
http://127.0.0.1:8000.
"""


def _included(relative: str) -> bool:
    parts = set(Path(relative).parts)
    return not (parts & EXCLUDED_PARTS) and not relative.startswith(EXCLUDED_PREFIXES)


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("README.md", TOP_README)
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT).as_posix()
            if path.is_file() and _included(relative):
                bundle.write(path, f"{REPO}/{relative}")
        for section, spec in SECTIONS.items():
            bundle.writestr(f"{section}/README.md", spec["readme"])
            for source, name in spec.get("files", {}).items():
                bundle.write(ROOT / source, f"{section}/{name}")
            for pattern, folder in spec.get("globs", {}).items():
                for path in sorted(ROOT.glob(pattern)):
                    bundle.write(path, f"{section}/{folder}/{path.name}")
    size = TARGET.stat().st_size / 1_000_000
    print(f"{TARGET} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
