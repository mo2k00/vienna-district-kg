"""Offline reasoning: derive the static part of the KG once and store it."""

import json
import logging

from vdkg.config import KG_DIR, MATERIALIZED, RULES
from vdkg.reasoning.nemo import Nemo

log = logging.getLogger(__name__)

PROGRAMS = (
    "10_mapping.rls",
    "20_aggregates.rls",
    "30_traits.rls",
    "40_transit.rls",
    "90_export_materialized.rls",
)


def run() -> None:
    MATERIALIZED.mkdir(parents=True, exist_ok=True)
    result = Nemo().run([RULES / name for name in PROGRAMS], KG_DIR, MATERIALIZED)
    stats = {
        "derived_facts": result.derived_facts,
        "seconds": round(result.seconds, 2),
        "exported": {name: len(rows) for name, rows in sorted(result.relations.items())},
    }
    (MATERIALIZED / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    log.info("derived %d facts in %.1fs", result.derived_facts, result.seconds)
