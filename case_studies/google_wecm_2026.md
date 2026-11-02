# Google credential × Texas WECM alignment study (March 2026)

**Status: completed analytical run; exploratory curriculum-alignment findings, not approved equivalencies.**

This case study records work presented at the statewide Texas Association for Career and Technical Education (TACTE) conference in March 2026. It is a research and curriculum-design demonstration, not an approved academic program, a credit-award decision, or a production deployment.

## Reproducible run identity

| Field | Recorded value |
| --- | --- |
| Run ID | `20260311_193536` |
| Completed | March 11, 2026 |
| Source curriculum | Texas Workforce Education Course Manual (WECM) |
| WECM rows in comparison corpus | 949 |
| Google credential groupings | 6 |
| Google course units evaluated | 37 |
| Candidate course comparisons | **35,113** (37 × 949) |
| Primary semantic model | `all-mpnet-base-v2` |
| Embedding size | 768 dimensions |
| Additional comparison measures | TF-IDF cosine and Jaccard |

The six groupings were Google IT Support Professional, Data Analytics, Digital Marketing, IT Automation with Python, Project Management, and AI Essentials.

**Source caution:** Some per-credential comparison subtotals printed in the original conference deck were based on 943 rather than 949 WECM rows and therefore do not sum to the stated total. The underlying permutation output and run provenance identify **35,113** candidate comparisons, using 949 WECM rows for each of 37 Google course units. This page uses that corrected total, without repeating the inconsistent slide subtotals.

## What the analysis did

1. Ingested Google credential course descriptions/outcomes and Texas WECM course material.
2. Computed semantic similarities with Sentence-BERT to rank candidate instructional relationships. TF-IDF cosine and Jaccard provided distinct lexical checks; agreement among measures was evidence to inspect, not a replacement for evaluation.
3. Examined plausible placements of Google instructional content within existing college courses, including an exploratory Google IT Support Technician alignment.
4. Produced comparison tables and provenance artifacts for subsequent academic review.

### Illustrative IT Support findings

The 114-hour Google IT Support example considered five Google courses and exploratory placements in existing Texas college courses:

| Google course | Hours | Exploratory course container | SBERT score |
| --- | ---: | --- | ---: |
| Technical Support Fundamentals | 19 | ITNW 1354 — Implementing & Supporting Servers | 0.497 |
| Bits & Bytes of Computer Networking | 22 | ITCC 1314 — CCNA 1: Introduction to Networks | 0.626 |
| Operating Systems — Power User | 27 | ITNW 1354 — Implementing & Supporting Servers | 0.448 |
| System Administration & IT Infrastructure | 24 | ITNW 1336 — Cloud Deployment & Infrastructure Management | 0.608 |
| IT Security: Defense against Dark Arts | 22 | ITSY 1342 — Information Technology Security | 0.542 |

These are **ranked curriculum-design candidates**. The numbers are not probabilities, transferable credit hours, coverage percentages, or authorizations to grant equivalency. The presentation also explored reducing the number of course containers while considering instructional-hour capacity.

## Recorded work products

The March 11 run generated the following products (retained outside this public GitHub repository):

- **Product 1:** CE container analysis;
- **Product 2:** LSCO course-alignment analysis;
- **Product 3:** Full permutation CSV with 35,113 comparison rows;
- **Product 4:** Industry-credential embedding output;
- Embedding arrays and a run manifest containing source file checksums, model version, environment, and corpus statistics.

The conference deck provides the public-facing explanation of the Google IT Support example. Detailed run tables and some input data are not included in this repository; their absence should not be read as indicating that the analysis was never run.

## Academic and implementation boundaries

- A strong semantic match is a **candidate for review**, not an academic equivalency.
- The March analysis and its analyst-selected examples are not evidence of completed faculty-panel validation.
- The **MinK** panel-review protocol documented in this repository is a governance design for later validation workflows; do not infer that a three-person MinK panel approved the March Google findings.
- Course and program changes, prior-learning credit, occupational awards, financial-aid eligibility, and accreditation questions require separate institutional and regulatory review.
- This study is distinct from the later Abulafia code tree. The public Abulafia matching and export modules contain unfinished interfaces and are not an end-to-end reproduction of the March run.

For the broader methodology, review the [Antikythera overview](../README.md) and [Abulafia documentation](../abulafia/README.md).

**Availability and permissions:** See the repository [License](../License). For an academic demonstration, collaboration, or access to additional artifacts, contact Joshua Hayes at **joshua.hayes.info@gmail.com**.
