# Antikythera

**Semantic curriculum alignment for higher education and industry credentials**

Antikythera is an applied research-and-development project for identifying plausible relationships among college courses, student learning outcomes, industry certifications, and professional standards. It uses computational ranking to help qualified academic reviewers focus their attention; it does **not** automate credit decisions.

> **Project status — active work in progress.** Completed analytical work products exist, including a March 2026 comparison of six Google credential groupings with the Texas Workforce Education Course Manual (WECM). This public repository also contains authored parsers, source provenance, technical documentation, and an evolving Abulafia alignment architecture. Some matching, preprocessing, and export modules remain intentionally incomplete. Do not treat the whole repository as an install-and-run application.

## Start here

| Resource | What it shows | Status |
| --- | --- | --- |
| [Google × WECM case study](case_studies/google_wecm_2026.md) | March 2026 completed run, **35,113** candidate comparisons, example Google IT Support mappings, and recorded outputs | Analytical work completed; mappings exploratory |
| [Abulafia overview](abulafia/readme.md) | Standards-alignment workflow for existing degree programs, available parsers, documentation, and implementation limits | Research/development |
| [MinK technical documentation](abulafia/05_documentation/Abulafia_MinK_Technical_Documentation_v3.2.docx.pdf) | Human subject-matter-expert (SME) review design, acceptance protocol, and intended audit trail | Protocol documented |
| [Research white paper](abulafia/05_documentation/Curriculum_Alignment_White_Paper.docx) | Supporting research and rationale for academic alignment work | Research document |
| [Source and parser code](abulafia/06_code/) | ACGM/WECM and target-standard extraction, data preparation, matching interfaces, export interfaces | Mixed implementation maturity |

### Demonstrated Google credential analysis

A run completed on **March 11, 2026**, compared **37 course units** across **six Google credential groupings** with **949 WECM course records**, producing **35,113 pairwise comparisons**. The analysis used `all-mpnet-base-v2` sentence embeddings and complementary TF-IDF and Jaccard checks. It included exploratory instructional-content placement for the Google IT Support Professional Certificate.

The work was presented at a **statewide TACTE conference in March 2026**. The full output CSVs and run manifest are retained separately and are **not included in this public repository**. See the [case study](case_studies/google_wecm_2026.md) for the run identity, illustrative findings, limitations, and artifact inventory.

**That completed analysis is not the same as a finished public end-to-end software package, and the candidate matches are not approved credit equivalencies.**

## Abulafia: standards alignment for existing programs

Abulafia explores how existing Texas college course outcomes may align with external technical, occupational, and professional standards, using a documented review process rather than a fixed cosine-similarity cutoff. Frameworks represented in the research scope include **USCG, NCCER, BCSP, NAPTA, SACA, and DOT**; listing a framework does not imply an institutionally approved crosswalk.

The repository contains dated Texas ACGM/WECM source materials, NCCER standard inputs, provenance notes, several substantive parser and corpus-building scripts, and detailed design documentation. The current `02_matching_pipeline.py`, `01_preprocessing.py`, and `03_export_results.py` files contain declared functions with `NotImplementedError` placeholders. They define the intended interfaces; they do not establish that this public code can reproduce the completed March Google analysis.

## Human review: MinK

**MinK (Minimum K)** is the documented SME-review protocol for future or continuing alignment work. An operator specifies a queue depth `K` per comparison method and an `acceptance_target`. The proposed process presents ranked course/standard candidates to a **three-person reviewer panel**, records **Accept / Not Accept** judgments, and ends when its acceptance condition is met.

MinK describes how academic judgment should govern the output; it is **not** evidence that the March Google demonstration was reviewed or approved by a three-person faculty panel.

## What this project does—and does not—claim

- **Does:** produce or specify auditable candidate rankings; preserve the distinction among semantic similarity, instructional content placement, academic equivalence, and institutional approval.
- **Does:** document actual research outputs alongside partial public implementations and proprietary methods.
- **Does not:** issue credits, approve curricula, make accreditation or financial-aid determinations, or claim that similarity scores are acceptance thresholds.
- **Does not:** represent the entire public code tree as production ready or fully reproducible without separately retained artifacts and unpublished implementation details.

## License and contact

The repository is publicly viewable but **proprietary and not open-source licensed**. See [License](License) for permissions and restrictions.

For demonstrations, academic collaboration, or permissions: **Joshua Hayes — joshua.hayes.info@gmail.com**.
