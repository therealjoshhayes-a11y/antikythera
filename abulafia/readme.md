# Abulafia — standards alignment for existing degree programs

Abulafia is the Antikythera workstream for examining possible relationships between Student Learning Outcomes (SLOs) in existing Texas community-college coursework and external professional, technical, and industry standards.

**Status: applied research / partial public implementation.** The directory includes original input materials and provenance notes, authored parsing and corpus-preparation code, and substantial technical documentation. The later semantic matching, preprocessing, MinK queue-generation, and export modules include declared interfaces that are **not yet implemented in this public code tree**. This is not advertised as an end-to-end runnable package.

## Where to look

| Path | Contents |
| --- | --- |
| [`01_input/source_data/`](01_input/source_data/) | Dated ACGM, WECM, degree-plan, and NCCER standards materials |
| [`01_input/provenance/`](01_input/provenance/) | Retrieval metadata and source notes |
| [`06_code/`](06_code/) | Parsers for ACGM, WECM, technical standards, and degree plans; corpus-building code; matching and report interfaces |
| [`05_documentation/`](05_documentation/) | MinK technical documentation and research white paper |
| [`project_manifest.json`](project_manifest.json) | Reserved project manifest; currently an empty placeholder |

Some processed, interim, output, and log folders are intentionally empty in the public repository. Their presence documents the intended project layout; it does **not** imply the files have been published.

## Review model

The proposed alignment workflow ranks candidates using distinct semantic and lexical signals. MinK specifies a human subject-matter-expert review process: the panel determines **Accept** or **Not Accept**, with traceable votes and session metadata. The software is not empowered to award academic credit or approve curricular equivalence.

The published MinK protocol is a **documented design**, not proof that a particular credential crosswalk has passed institutional or faculty review.

## Relationship to completed Google demonstration

The **March 2026 Google × WECM study was completed as a separate analytical run**, with its artifacts retained outside the repository. Abulafia code should not be mistaken for that study's full executable implementation. See the [Google/WECM case study](../case_studies/google_wecm_2026.md).

Return to the [main Antikythera overview](../README.md).

## Rights and inquiries

This repository is proprietary; see [License](../License). Collaboration and documentation inquiries: **joshua.hayes.info@gmail.com**.
