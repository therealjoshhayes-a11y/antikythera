"""
00c_build_corpus.py
Abulafia — Standards Alignment for Legacy Degree Programs
Part of the Antikythera project tree.

Consolidates parsed ACGM and WECM CSVs into a single corpus file
used for TF-IDF IDF training across all Antikythera projects.

Output: ../../_shared_data/texas_corpus/acgm_wecm_consolidated.csv

This file lives at the Antikythera repository root level in
_shared_data/texas_corpus/ because it is shared infrastructure
used by all Antikythera projects, not specific to Abulafia.

Run from the abulafia/ directory:
    python 06_code/00c_build_corpus.py

Requires:
    pip install pandas

Copyright (c) 2026. All rights reserved.
Proprietary and confidential. See LICENSE.
"""

import csv
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime
from glob import glob

# ── Configuration ──────────────────────────────────────────────────────────────

PROCESSED_PATH  = Path("02_processed")
SHARED_DATA_PATH = Path("../_shared_data/texas_corpus")
LOG_PATH        = Path("07_logs")

TODAY = datetime.now().strftime("%Y%m%d")
OUTPUT_FILENAME = "acgm_wecm_consolidated.csv"

# ── Logging ────────────────────────────────────────────────────────────────────

LOG_PATH.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH / f"00c_build_corpus_{TODAY}.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


def find_latest(prefix: str) -> Path | None:
    """
    Find the most recently dated parsed file matching a prefix pattern.
    Looks for files like acgm_parsed_YYYYMMDD.csv in 02_processed/.
    """
    pattern = str(PROCESSED_PATH / f"{prefix}_parsed_*.csv")
    matches = sorted(glob(pattern), reverse=True)
    if not matches:
        return None
    return Path(matches[0])


def checksum(path: Path) -> str:
    """MD5 checksum for provenance."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_consolidated(df: pd.DataFrame) -> None:
    """Run quality checks on the consolidated corpus."""
    log.info("Running validation checks ...")
    issues = []

    empty_combined = (
        df["combined_text"].isna() | (df["combined_text"].str.strip() == "")
    )
    if empty_combined.any():
        issues.append(f"  {empty_combined.sum()} rows with empty combined_text")

    empty_ids = df["course_id"].isna() | (df["course_id"].str.strip() == "")
    if empty_ids.any():
        issues.append(f"  {empty_ids.sum()} rows with empty course_id")

    short_text = df["combined_text"].str.len() < 20
    if short_text.any():
        issues.append(f"  {short_text.sum()} rows with very short combined_text (<20 chars)")

    if issues:
        log.warning("Validation issues found:")
        for issue in issues:
            log.warning(issue)
    else:
        log.info("All validation checks passed.")


def update_transformation_log(
    acgm_path: Path,
    wecm_path: Path,
    output_path: Path,
    acgm_count: int,
    wecm_count: int,
    total_count: int,
    output_md5: str,
) -> None:
    """Append consolidation record to transformation log."""
    log_file = Path("00_data_prep/transformation_log.json")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(log_file) as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"transformations": []}

    entry = {
        "step_number":   len(log_data.get("transformations", [])) + 1,
        "timestamp":     datetime.utcnow().isoformat() + "Z",
        "script":        "06_code/00c_build_corpus.py",
        "operation":     "consolidate_acgm_wecm",
        "input_files":   [str(acgm_path), str(wecm_path)],
        "output_files":  [str(output_path)],
        "records_in":    {"acgm": acgm_count, "wecm": wecm_count},
        "records_out":   total_count,
        "output_md5":    output_md5,
        "transformation_rules": [
            "Concatenated ACGM and WECM parsed CSVs",
            "Retained shared columns: rubric, course_number, course_id, "
            "course_title, sch, description, slos, slo_count, combined_text",
            "Added source column: acgm or wecm",
            "Dropped exact duplicate course_id + combined_text pairs",
            "Wrote to _shared_data/texas_corpus/ for shared use across "
            "Antikythera projects",
        ],
        "quality_flags": [],
        "analyst":       "",
    }

    log_data.setdefault("transformations", []).append(entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)

    log.info(f"Transformation log updated: {log_file}")


def main():
    log.info("=" * 60)
    log.info("Corpus Builder — Antikythera / Abulafia")
    log.info("=" * 60)

    # Find latest parsed files
    acgm_path = find_latest("acgm")
    wecm_path = find_latest("wecm")

    if not acgm_path:
        log.error("No ACGM parsed file found in 02_processed/")
        log.error("Run 06_code/00a_parse_acgm_pdf.py first.")
        raise FileNotFoundError("acgm_parsed_*.csv not found in 02_processed/")

    if not wecm_path:
        log.error("No WECM parsed file found in 02_processed/")
        log.error("Run 06_code/00b_parse_wecm_xlsx.py first.")
        raise FileNotFoundError("wecm_parsed_*.csv not found in 02_processed/")

    log.info(f"ACGM input: {acgm_path}")
    log.info(f"WECM input: {wecm_path}")

    # Shared output path
    SHARED_DATA_PATH.mkdir(parents=True, exist_ok=True)
    output_path = SHARED_DATA_PATH / OUTPUT_FILENAME

    # Load both
    acgm_df = pd.read_csv(acgm_path, dtype=str).fillna("")
    wecm_df = pd.read_csv(wecm_path, dtype=str).fillna("")

    acgm_df["source"] = "acgm"
    wecm_df["source"] = "wecm"

    acgm_count = len(acgm_df)
    wecm_count = len(wecm_df)

    log.info(f"ACGM rows: {acgm_count}")
    log.info(f"WECM rows: {wecm_count}")

    # Standardize to shared column set
    shared_cols = [
        "rubric", "course_number", "course_id", "course_title",
        "sch", "description", "slos", "slo_count", "combined_text", "source"
    ]

    def align_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """Add missing columns as empty strings; drop extras."""
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df[cols]

    acgm_df = align_columns(acgm_df, shared_cols)
    wecm_df = align_columns(wecm_df, shared_cols)

    combined = pd.concat([acgm_df, wecm_df], ignore_index=True)

    # Drop exact duplicates on course_id + combined_text
    before = len(combined)
    combined = combined.drop_duplicates(
        subset=["course_id", "combined_text"], keep="first"
    )
    after = len(combined)
    if before != after:
        log.info(f"Dropped {before - after} exact duplicates")

    validate_consolidated(combined)

    combined.to_csv(output_path, index=False, encoding="utf-8",
                    quoting=csv.QUOTE_ALL)

    output_md5 = checksum(output_path)
    log.info(f"Output written: {output_path}")
    log.info(f"Total rows: {len(combined)}")
    log.info(f"Output MD5: {output_md5}")

    # Source breakdown
    source_counts = combined["source"].value_counts().to_dict()
    log.info(f"Source breakdown: {source_counts}")

    update_transformation_log(
        acgm_path, wecm_path, output_path,
        acgm_count, wecm_count, len(combined), output_md5
    )

    log.info("Done.")
    log.info("Corpus ready at: _shared_data/texas_corpus/acgm_wecm_consolidated.csv")
    log.info("Next step: run 06_code/02_matching_pipeline.py")


if __name__ == "__main__":
    main()
