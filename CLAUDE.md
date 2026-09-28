# Vienna District KG — project context

TU Wien course "Knowledge Graphs" (192.194/192.116, 2026S), 6 ECTS, solo project by Moritz Lindner.
Title: *Knowledge Graph-based Vienna District Similarity and Lifestyle Recommendation*.
One-pager: `../OnePager/KG_One_Pager_Lindner_12036132.pdf`. Course slides: `../Slides/`.

**Always read `PROGRESS.md` first** — it holds the current state and next steps.

## Deadline
Extended track: portfolio due **2026-09-30** (check exact time in TUWEL).

## Goal
KG integrating district-level Vienna Open Data (23 districts) that answers:
- similarity: "which districts are like district X?" (KG embeddings, LO1)
- recommendation: "which district fits lifestyle/preferences Y?" (logic rules, LO2)

## Constraints / decisions
- Professor's feedback: **keep data ingestion lean** — spend time on the "AI parts" (logic + embeddings).
- LOs: focus LO1 (KGE) + LO2 (logic); basic LO4–LO12; LO3 (GNN) excluded.
- LO2 must show **full recursion** and **object creation (existential rules)** (course site wording).
- Reasoner: **Nemo** v0.10.1 (`tools/nemo/.../nmo.exe`, install via `python tools/setup_nemo.py`).
  Syntax: `head(?X) :- body(?X).`, existentials `!V` in head, aggregates `#sum/#count/#min/#max`.
- Embeddings: **PyKEEN**, used out of the box (no method changes).
- AI usage must be declared honestly on the portfolio cover page → keep `docs/AI_USAGE_LOG.md` updated.
- Record every portfolio-worthy fact/example/number in `docs/PORTFOLIO_NOTES.md` with its LO tag.

## Deliverable
1 PDF: pro-forma cover pages (`../Slides/10_*/06_KG - Portfolio - Pro-Forma-v3.docx`) + ~6-page report,
suggested structure `../Slides/10_*/07_KG - Portfolio - Example-Structure.pdf`
(Scenario / KG construction / ML representation / Logic representation / Reflection), LO tags like "(LO1)".
1 ZIP: code + data, folders "2 - construction", "3 - ML", "4 - logic", "5 - reflection" + readme.

## Layout
- `data/raw/` downloaded source files, `data/processed/` cleaned tables
- `construction/` data → KG (triples / Nemo facts)
- `logic/` Nemo rule files + runner
- `ml/` PyKEEN training + similarity
- `service/` similarity & recommendation queries
- `results/` outputs, figures
- `docs/` notes, AI usage log
