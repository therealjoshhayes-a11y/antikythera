"""
00a_parse_acgm_pdf.py
Abulafia — Standards Alignment for Legacy Degree Programs
Part of the Antikythera project tree.

Parses the THECB Academic Course Guide Manual (ACGM) PDF into a
structured CSV. Extracts course rubric, number, title, SCH,
description, and Student Learning Outcomes per course.

Output: 02_processed/acgm_parsed_YYYYMMDD.csv

Run from the abulafia/ directory:
    python 06_code/00a_parse_acgm_pdf.py

Requires:
    pip install pdfplumber pandas

Copyright (c) 2026. All rights reserved.
Proprietary and confidential. See LICENSE.
"""

import re
import csv
import json
import logging
import hashlib
import pdfplumber
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────

INPUT_PATH  = Path("01_input/source_data")
OUTPUT_PATH = Path("02_processed")
LOG_PATH    = Path("07_logs")

# Update this filename to match your actual download
ACGM_PDF_FILENAME = "acgm_corpus_20260218.pdf"

# Output filename (dated)
TODAY = datetime.now().strftime("%Y%m%d")
OUTPUT_FILENAME = f"acgm_parsed_{TODAY}.csv"

# ── Logging ────────────────────────────────────────────────────────────────────

LOG_PATH.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH / f"00a_parse_acgm_{TODAY}.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)

# ── ACGM Course Pattern ────────────────────────────────────────────────────────
#
# THECB ACGM course entries follow this general structure:
#
#   RUBR 1234  Course Title  (SCH-lecture-lab)
#   Description text spanning one or more lines.
#   Student Learning Outcomes:
#   1. First outcome text.
#   2. Second outcome text.
#
# The rubric is 2-5 uppercase letters. Course number is 4 digits.
# SCH notation appears as (3-3-0), (4-3-3), etc.

COURSE_HEADER = re.compile(
    r'^([A-Z]{2,5})\s+(\d{4})\s+(.+?)\s*(\(\d+-\d+-\d+\))?$'
)
SLO_LINE      = re.compile(r'^\s*(\d+)\.\s+(.+)$')
SLO_HEADER    = re.compile(
    r'student\s+learning\s+outcomes?',
    re.IGNORECASE
)
SCH_PATTERN   = re.compile(r'\((\d+)-\d+-\d+\)')


def checksum(path: Path) -> str:
    """MD5 checksum of input file for provenance logging."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_text(text: str) -> str:
    """Normalize whitespace and remove stray control characters."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def extract_sch(sch_str: str) -> str:
    """Extract semester credit hours from notation like (3-3-0)."""
    if not sch_str:
        return ""
    m = SCH_PATTERN.search(sch_str)
    return m.group(1) if m else ""


def parse_acgm_pdf(pdf_path: Path) -> list[dict]:
    """
    Extract all course records from the ACGM PDF.

    Each course record is a dict with keys:
        rubric, course_number, course_id, course_title,
        sch, description, slos, slo_count, combined_text

    combined_text = course_title + ' ' + description + ' ' + all SLOs.
    This is the field used for TF-IDF IDF training and semantic matching.

    Returns:
        List of course record dicts.
    """
    courses = []
    current = None
    in_slos = False
    description_lines = []
    slo_lines = []

    def finalize_course(course, desc_lines, slo_list):
        """Package accumulated lines into a completed course record."""
        if not course:
            return None
        desc = clean_text(" ".join(desc_lines))
        slos = [clean_text(s) for s in slo_list if s.strip()]
        slo_text = " ".join(slos)
        combined = clean_text(
            f"{course['course_title']} {desc} {slo_text}"
        )
        return {
            **course,
            "description":   desc,
            "slos":          " | ".join(slos),
            "slo_count":     len(slos),
            "combined_text": combined,
        }

    log.info(f"Opening PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        log.info(f"PDF has {total_pages} pages")

        for page_num, page in enumerate(pdf.pages, start=1):
            if page_num % 50 == 0:
                log.info(f"  Processing page {page_num}/{total_pages} ...")

            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Check for a new course header
                m = COURSE_HEADER.match(line_stripped)
                if m:
                    # Save previous course
                    if current:
                        record = finalize_course(
                            current, description_lines, slo_lines
                        )
                        if record:
                            courses.append(record)

                    rubric  = m.group(1)
                    number  = m.group(2)
                    title   = clean_text(m.group(3))
                    sch_raw = m.group(4) or ""

                    current = {
                        "rubric":         rubric,
                        "course_number":  number,
                        "course_id":      f"{rubric} {number}",
                        "course_title":   title,
                        "sch":            extract_sch(sch_raw),
                    }
                    description_lines = []
                    slo_lines         = []
                    in_slos           = False
                    continue

                # Check for SLO section header
                if SLO_HEADER.search(line_stripped):
                    in_slos = True
                    continue

                if current:
                    if in_slos:
                        # Try to match a numbered SLO
                        slo_match = SLO_LINE.match(line_stripped)
                        if slo_match:
                            slo_lines.append(slo_match.group(2))
                        elif slo_lines:
                            # Continuation of the last SLO
                            slo_lines[-1] += " " + line_stripped
                    else:
                        description_lines.append(line_stripped)

        # Finalize the last course
        if current:
            record = finalize_course(
                current, description_lines, slo_lines
            )
            if record:
                courses.append(record)

    return courses


def validate_output(df: pd.DataFrame) -> None:
    """Run basic quality checks on the parsed output."""
    log.info("Running validation checks ...")
    issues = []

    empty_titles = df["course_title"].isna() | (df["course_title"] == "")
    if empty_titles.any():
        issues.append(f"  {empty_titles.sum()} courses with empty title")

    empty_desc = df["description"].isna() | (df["description"] == "")
    if empty_desc.any():
        issues.append(f"  {empty_desc.sum()} courses with empty description")

    no_slos = df["slo_count"] == 0
    if no_slos.any():
        issues.append(f"  {no_slos.sum()} courses with no SLOs parsed")

    dupe_ids = df[df.duplicated("course_id", keep=False)]
    if not dupe_ids.empty:
        issues.append(f"  {len(dupe_ids)} duplicate course_id entries")

    if issues:
        log.warning("Validation issues found:")
        for issue in issues:
            log.warning(issue)
        log.warning("Review 07_logs/ for details. These may reflect "
                    "PDF formatting irregularities requiring manual review.")
    else:
        log.info("All validation checks passed.")


def update_transformation_log(
    pdf_path: Path,
    output_path: Path,
    record_count: int,
    md5: str,
) -> None:
    """Append a transformation record to 00_data_prep/transformation_log.json."""
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
        "script":        "06_code/00a_parse_acgm_pdf.py",
        "operation":     "parse_acgm_pdf",
        "input_files":   [str(pdf_path)],
        "output_files":  [str(output_path)],
        "records_in":    "n/a (PDF pages)",
        "records_out":   record_count,
        "input_md5":     md5,
        "transformation_rules": [
            "Extracted rubric, course_number, title, SCH, description, SLOs per course",
            "Combined title + description + SLOs into combined_text field",
            "Normalized whitespace; removed control characters",
            "SLOs joined with pipe delimiter in slos column",
        ],
        "quality_flags": [],
        "analyst":       "",
    }

    log_data.setdefault("transformations", []).append(entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)

    log.info(f"Transformation log updated: {log_file}")


def main():
    pdf_path    = INPUT_PATH / ACGM_PDF_FILENAME
    output_path = OUTPUT_PATH / OUTPUT_FILENAME

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        log.error(f"Input file not found: {pdf_path}")
        log.error("Check ACGM_PDF_FILENAME in script header.")
        raise FileNotFoundError(pdf_path)

    log.info("=" * 60)
    log.info("ACGM PDF Parser — Antikythera / Abulafia")
    log.info("=" * 60)

    md5 = checksum(pdf_path)
    log.info(f"Input MD5: {md5}")

    courses = parse_acgm_pdf(pdf_path)
    log.info(f"Courses extracted: {len(courses)}")

    if not courses:
        log.error("No courses extracted. Check PDF format and COURSE_HEADER pattern.")
        raise ValueError("No courses parsed from PDF.")

    df = pd.DataFrame(courses, columns=[
        "rubric", "course_number", "course_id", "course_title",
        "sch", "description", "slos", "slo_count", "combined_text"
    ])

    validate_output(df)

    df.to_csv(output_path, index=False, encoding="utf-8",
              quoting=csv.QUOTE_ALL)
    log.info(f"Output written: {output_path}")
    log.info(f"Rows: {len(df)} | Columns: {list(df.columns)}")

    # Sample output for sanity check
    log.info("Sample record (first course):")
    log.info(f"  course_id:     {df.iloc[0]['course_id']}")
    log.info(f"  course_title:  {df.iloc[0]['course_title']}")
    log.info(f"  slo_count:     {df.iloc[0]['slo_count']}")
    log.info(f"  combined_text: {df.iloc[0]['combined_text'][:120]}...")

    update_transformation_log(pdf_path, output_path, len(df), md5)

    log.info("Done.")
    log.info(f"Next step: run 06_code/00b_parse_wecm_xlsx.py")


if __name__ == "__main__":
    main()
