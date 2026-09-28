"""Collect evidence for the portfolio report in artifacts/report/."""

import json
import logging

from vdkg.config import ARTIFACTS
from vdkg.kg import rdf
from vdkg.report import examples, figures, traces, verify
from vdkg.service.knowledge import KnowledgeBase

log = logging.getLogger(__name__)

REPORT = ARTIFACTS / "report"


def _write_json(name: str, content: dict) -> None:
    (REPORT / name).write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("wrote %s", name)


def run() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    knowledge = KnowledgeBase()

    _write_json("verification.json", verify.run(knowledge))
    _write_json("rdf_export.json", rdf.export(knowledge))
    _write_json("examples.json", examples.run(knowledge))

    rendered = traces.run(knowledge)
    text = "\n\n".join(f"## {fact}\n\n```\n{tree}\n```" for fact, tree in rendered.items())
    (REPORT / "traces.md").write_text(
        f"# Derivation traces (Nemo --trace)\n\n{text}\n", encoding="utf-8"
    )
    log.info("wrote traces.md")

    for name in figures.run(knowledge, REPORT / "figures"):
        log.info("wrote figures/%s", name)
