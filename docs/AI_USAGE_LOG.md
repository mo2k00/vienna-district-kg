# AI usage log

Supplement to the Generative AI declaration on the portfolio cover page.
Tool: Claude (Claude Code), used as a coding and writing assistant throughout the project.

I defined the project idea, scope and requirements, made the design decisions, and reviewed and
tested the results, requesting changes where needed. Claude was used to write parts of the code
and to draft texts, always based on my specifications and checked by me.

| Task | My part | Claude's part                                                                                       |
|---|---|-----------------------------------------------------------------------------------------------------|
| Idea and scope | Project idea and one-pager, feedback round with the lecturer, scope decisions (23 districts, focus on LO1/LO2, no rent data, user-chosen preferences instead of fixed lifestyle profiles) | –                                                                                                   |
| Reasoner | Decided on Nemo | Proposed Nemo (fallback Clingo), installed and tested it                                            |
| Data sources | Provided the starting sources (City of Vienna statistics, Statistik Austria), selected the datasets and features to use | Searched the open data catalogue, checked formats and years, documented the sources                 |
| Architecture and planning | Set the requirements: layered architecture, separate pages, UI stack (FastAPI, vanilla JS, Leaflet), importance scale, commute feature, language | Drafted the implementation plan and data schema                                                     |
| Ingestion, KG and rules | Defined the preference categories and what each should mean, reviewed the derived facts and fine-tuned the results | Assisted in implementing the loaders, KG build, Nemo rules and recommender to my specifications; debugging of Nemo issues |
| Embeddings, web app, tests | Chose the models to compare, tested the web app and requested changes to UI and behaviour | Assisted in implementing the PyKEEN pipeline and evaluation, the API, the frontend and the tests to my specifications |
| Report evidence | Decided which evidence the report needs | Assisted in implementing the verification, derivation traces, RDF export, examples and figures I asked for |
| Documentation and repository | Defined what the README must cover (data downloads, setup options), managed the repository and the final cleanup | Drafts of the README and documentation                                                              |
| Portfolio | Chose the structure and LO self-assessment, revised and completed the text, filled in hours, AI percentages and declaration | First draft of the report and cover entries                                                         |
