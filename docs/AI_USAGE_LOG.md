# AI usage log

For the Generative AI declaration on the portfolio cover page. Tool: Claude (Claude Code).
Record what the AI did, what the student decided/did, and the key prompts.

| Task | AI contribution | Student contribution |
|---|---|---|
| Reasoner choice | Proposed Nemo (fallback Clingo), installed and tested it | Approved choice |
| Dataset scouting | Searched data.gv.at catalogue API, downloaded samples, checked formats/years, documented in DATA_SOURCES.md | Provided starting links (wien.gv.at statistik, statistik.at), selects final features |
| Planning | Drafted PLAN.md (architecture, schema, LO mapping) | Chose UI stack (FastAPI + vanilla JS), scoring model, commute feature, language, layout; accepted defaults |
| Ingestion + KG + rules | Implemented loaders, KG build, Nemo rules, recommender; debugged Nemo issues | Defined preference categories (going out, sports, quiet/green, …); reviewed results |
| Embeddings, API, web app, tests | Implemented PyKEEN pipeline, evaluation, FastAPI, frontend, tests | Chose models to compare, UI stack/layout; reviews results and UI |
| Report evidence | Implemented verification, trace rendering, RDF export, examples, figures, screenshots, packaging | Chose which evidence to produce (approved the list) |
| Portfolio draft | Generated the first draft of the report (report.md), cover entries (cover.json) and the build script | Chose writing workflow, structure and LO self-assessment; revises the text, fills hours, AI percentages and declaration |
