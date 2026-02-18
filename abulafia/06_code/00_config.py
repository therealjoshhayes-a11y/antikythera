"""
00_config.py
Abulafia — Standards Alignment for Legacy Degree Programs
Part of the Antikythera project tree.

Configuration file for a single alignment project run.
All operator-set parameters are defined here. No other file
should contain hardcoded paths or session parameters.

Copyright (c) 2026. All rights reserved.
Proprietary and confidential. See LICENSE.
"""

# ── Project Identity ───────────────────────────────────────────────────────────

PROJECT_ID = "YYYYMMDD_ClientName_Framework"
ANALYST = ""
FRAMEWORK = ""          # e.g. "USCG", "NCCER", "BCSP"
CLIENT = ""

# ── MinK Session Parameters ────────────────────────────────────────────────────
# K: number of top-ranked pairs per measure loaded into the SME presentation
#    queue. The same K applies to SBERT, TF-IDF, and Jaccard. Max queue = 3K.
# acceptance_target: session terminates when this many ACCEPT decisions have
#    been recorded by the panel, across all measures.

K = 30
ACCEPTANCE_TARGET = 3

# ── File Paths ─────────────────────────────────────────────────────────────────

PATHS = {
    "acgm_wecm_corpus":     "_shared_data/texas_corpus/acgm_wecm_consolidated.csv",
    "client_catalog":       "01_input/source_data/client_catalog.csv",
    "degree_plans":         "01_input/source_data/target_degree_plans.csv",
    "target_standards":     "01_input/source_data/target_standards.csv",
    "courses_in_scope":     "02_processed/courses_in_scope.csv",
    "slos_cleaned":         "02_processed/slos_cleaned.csv",
    "standards_cleaned":    "02_processed/standards_cleaned.csv",
    "embeddings_dir":       "03_interim/embeddings/",
    "stage1_output":        "03_interim/stage1_sbert_ranked.csv",
    "stage2_output":        "03_interim/stage2_tfidf_ranked.csv",
    "stage3_output":        "03_interim/stage3_jaccard_ranked.csv",
    "sme_queue":            "04_output/sme_presentation_queue.csv",
    "admin_report":         "04_output/administrative_report.xlsx",
    "transformation_log":   "00_data_prep/transformation_log.json",
    "project_manifest":     "project_manifest.json",
}

# ── Model Configuration ────────────────────────────────────────────────────────

SBERT_MODEL = "all-mpnet-base-v2"
RANDOM_SEED = 42            # for torch.manual_seed; do not change between runs

# ── TF-IDF Configuration ───────────────────────────────────────────────────────
# Stop word removal and lemmatization are applied in preprocessing (01_preprocessing.py)
# before the vectorizer sees the text. stop_words is set to None here accordingly.

TFIDF_CONFIG = {
    "ngram_range":  (1, 3),
    "max_features": 5000,
    "min_df":       2,
    "stop_words":   None,   # handled upstream in preprocessing pipeline
}
