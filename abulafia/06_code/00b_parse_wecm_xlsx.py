"""
00b_parse_wecm_xlsx.py
Abulafia — Standards Alignment for Legacy Degree Programs
Part of the Antikythera project tree.

Parses the THECB Workforce Education Course Manual (WECM) xlsx
workbook into a structured CSV. Iterates all sheets, extracts
course rubric, number, title, SCH, description, and Student
Learning Outcomes per course.

Handles WECM workbooks with many sheets (the THECB WECM workbook
may contain thousands of sheets organized by discipline family).
Uses openpyxl read_only mode for memory efficiency.

Output: 02_processed/wecm_parsed_YYYYMMDD.csv

Run from the abulafia/ directory:
    python 06_code/00b_parse_wecm_xlsx.py

Requires:
    pip install openpyxl pandas

Copyright (c) 2026. All rights reserved.
Proprietary and confidential. See LICENSE.
"""

import re
import csv
import json
import logging
import hashlib
import openpyxl
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────

INPUT_PATH  = Path("01_input/source_data")
OUTPUT_PATH = Path("02_processed")
LOG_PATH    = Path("07_logs")

# Update this filename to match your actual download
WECM_XLSX_FILENAME = "wecm_corpus_20260218.xlsx"

TODAY = datetime.now().strftime("%Y%m%d")
OUTPUT_FILENAME = f"wecm_parsed_{TODAY}.csv"

# ── Logging ────────────────────────────────────────────────────────────────────

LOG_PATH.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH / f"00b_parse_wecm_{TODAY}.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)

# ── Column Name Candidates ─────────────────────────────────────────────────────
#
# WECM column names vary across editions. We try multiple candidate
# names and take the first match. Add variants here if your download
# uses different column headers — check the first sheet manually.

RUBRIC_CANDIDATES = [
    "Rubric", "rubric", "RUBRIC", "Course Rubric", "Prefix"
]
NUMBER_CANDIDATES = [
    "Course Number", "course_number", "CourseNumber", "Number", "Num"
]
TITLE_CANDIDATES = [
    "Course Title", "course_title", "Title", "TITLE", "CourseName"
]
DESC_CANDIDATES = [
    "Description", "description", "Course Description", "Desc", "DESCRIPTION"
]
SCH_CANDIDATES = [
    "SCH", "sch", "Semester Credit Hours", "Credit Hours", "Credits", "Hours"
]
SLO_CANDIDATES = [
    "Student Learning Outcomes", "SLO", "SLOs", "Learning Outcomes",
    "Outcomes", "student_learning_outcomes", "StudentLearningOutcomes"
]


def checksum(path: Path) -> str:
    """MD5 checksum of input file for provenance logging."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_text(value) -> str:
    """Normalize a cell value to a clean string."""
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def find_column(headers: list[str], candidates: list[str]) -> str | None:
    """
    Return the first header string that matches any candidate name.
    Case-insensitive. Returns None if no match found.
    """
    headers_lower = {h.lower(): h for h in headers if h}
    for candidate in candidates:
        if candidate.lower() in headers_lower:
            return headers_lower[candidate.lower()]
    return None


def detect_sheet_structure(sheet) -> dict | None:
    """
    Inspect the first non-empty row of a sheet to detect column headers.

    Returns a dict mapping field names to detected column letters/indices,
    or None if the sheet does not appear to contain course data.
    """
    header_row = None
    header_values = []

    for row in sheet.iter_rows(max_row=10, values_only=True):
        if any(cell is not None for cell in row):
            header_row = row
            header_values = [clean_text(cell) for cell in row]
            break

    if not header_values:
        return None

    rubric_col  = find_column(header_values, RUBRIC_CANDIDATES)
    number_col  = find_column(header_values, NUMBER_CANDIDATES)
    title_col   = find_column(header_values, TITLE_CANDIDATES)
    desc_col    = find_column(header_values, DESC_CANDIDATES)
    sch_col     = find_column(header_values, SCH_CANDIDATES)
    slo_col     = find_column(header_values, SLO_CANDIDATES)

    # A sheet is considered a course sheet if it has at least
    # a title or rubric+number combination
    has_courses = (title_col is not None) or \
                  (rubric_col is not None and number_col is not None)

    if not has_courses:
        return None

    return {
        "headers":    header_values,
        "rubric":     rubric_col,
        "number":     number_col,
        "title":      title_col,
        "description": desc_col,
        "sch":        sch_col,
        "slo":        slo_col,
    }


def parse_sheet(sheet, sheet_name: str, col_map: dict) -> list[dict]:
    """
    Parse one worksheet into a list of course record dicts.

    Args:
        sheet:      openpyxl worksheet object.
        sheet_name: Name of the sheet (used as fallback rubric source).
        col_map:    Column mapping from detect_sheet_structure.

    Returns:
        List of course record dicts.
    """
    headers     = col_map["headers"]
    rubric_idx  = headers.index(col_map["rubric"])  if col_map["rubric"]  else None
    number_idx  = headers.index(col_map["number"])  if col_map["number"]  else None
    title_idx   = headers.index(col_map["title"])   if col_map["title"]   else None
    desc_idx    = headers.index(col_map["description"]) if col_map["description"] else None
    sch_idx     = headers.index(col_map["sch"])     if col_map["sch"]     else None
    slo_idx     = headers.index(col_map["slo"])     if col_map["slo"]     else None

    courses = []
    data_started = False

    for row in sheet.iter_rows(values_only=True):
        row_values = [clean_text(cell) for cell in row]

        # Skip header rows and empty rows
        if not any(row_values):
            continue
        if row_values == headers:
            data_started = True
            continue
        if not data_started:
            # Skip rows before we've confirmed the header
            if headers and any(v in row_values for v in headers if v):
                data_started = True
            continue

        # Extract fields with safe index access
        def get(idx):
            if idx is None or idx >= len(row_values):
                return ""
            return row_values[idx]

        rubric  = get(rubric_idx) or sheet_name
        number  = get(number_idx)
        title   = get(title_idx)
        desc    = get(desc_idx)
        sch     = get(sch_idx)
        slo_raw = get(slo_idx)

        # Skip rows that don't look like courses
        if not title and not number:
            continue

        course_id = f"{rubric} {number}".strip() if number else rubric

        # SLOs may be pipe-delimited, numbered, or newline-separated
        slos = parse_slo_field(slo_raw)
        slo_text = " ".join(slos)
        combined = clean_text(f"{title} {desc} {slo_text}")

        courses.append({
            "rubric":         clean_text(rubric),
            "course_number":  clean_text(number),
            "course_id":      clean_text(course_id),
            "course_title":   clean_text(title),
            "sch":            clean_text(sch),
            "description":    clean_text(desc),
            "slos":           " | ".join(slos),
            "slo_count":      len(slos),
            "combined_text":  combined,
            "source_sheet":   sheet_name,
        })

    return courses


def parse_slo_field(slo_raw: str) -> list[str]:
    """
    Parse SLO text from a single cell into a list of individual SLOs.

    Handles common WECM SLO formats:
      - Pipe-delimited:   "SLO one | SLO two | SLO three"
      - Numbered:         "1. SLO one 2. SLO two"
      - Newline:          "SLO one\nSLO two"
      - Single block:     "One long SLO text with no delimiter"

    Returns:
        List of individual SLO strings. Empty list if no content.
    """
    if not slo_raw:
        return []

    # Pipe-delimited
    if "|" in slo_raw:
        parts = [s.strip() for s in slo_raw.split("|") if s.strip()]
        if len(parts) > 1:
            return parts

    # Newline-delimited
    if "\n" in slo_raw:
        parts = [s.strip() for s in slo_raw.split("\n") if s.strip()]
        if len(parts) > 1:
            return parts

    # Numbered pattern: "1. text 2. text"
    numbered = re.split(r'\s*\d+\.\s+', slo_raw)
    numbered = [s.strip() for s in numbered if s.strip()]
    if len(numbered) > 1:
        return numbered

    # Single block — return as-is
    return [slo_raw.strip()]


def validate_output(df: pd.DataFrame) -> None:
    """Run basic quality checks on the parsed output."""
    log.info("Running validation checks ...")
    issues = []

    empty_titles = df["course_title"].isna() | (df["course_title"] == "")
    if empty_titles.any():
        issues.append(f"  {empty_titles.sum()} courses with empty title")

    empty_combined = df["combined_text"].isna() | (df["combined_text"] == "")
    if empty_combined.any():
        issues.append(f"  {empty_combined.sum()} courses with empty combined_text")

    no_slos = df["slo_count"] == 0
    if no_slos.any():
        issues.append(f"  {no_slos.sum()} courses with no SLOs parsed")

    dupe_ids = df[df.duplicated("course_id", keep=False)]
    if not dupe_ids.empty:
        issues.append(f"  {len(dupe_ids)} duplicate course_id values "
                      f"(may be valid if same course appears in multiple sheets)")

    if issues:
        log.warning("Validation issues found:")
        for issue in issues:
            log.warning(issue)
    else:
        log.info("All validation checks passed.")


def update_transformation_log(
    xlsx_path: Path,
    output_path: Path,
    record_count: int,
    sheet_count: int,
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
        "script":        "06_code/00b_parse_wecm_xlsx.py",
        "operation":     "parse_wecm_xlsx",
        "input_files":   [str(xlsx_path)],
        "output_files":  [str(output_path)],
        "sheets_processed": sheet_count,
        "records_in":    f"{sheet_count} sheets",
        "records_out":   record_count,
        "input_md5":     md5,
        "transformation_rules": [
            "Iterated all sheets using openpyxl read_only mode",
            "Auto-detected column headers per sheet using candidate name lists",
            "Parsed SLO field handling pipe, newline, and numbered formats",
            "Combined title + description + SLOs into combined_text field",
            "Normalized whitespace; removed control characters",
        ],
        "quality_flags": [],
        "analyst":       "",
    }

    log_data.setdefault("transformations", []).append(entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)

    log.info(f"Transformation log updated: {log_file}")


def main():
    xlsx_path   = INPUT_PATH / WECM_XLSX_FILENAME
    output_path = OUTPUT_PATH / OUTPUT_FILENAME

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    if not xlsx_path.exists():
        log.error(f"Input file not found: {xlsx_path}")
        log.error("Check WECM_XLSX_FILENAME in script header.")
        raise FileNotFoundError(xlsx_path)

    log.info("=" * 60)
    log.info("WECM xlsx Parser — Antikythera / Abulafia")
    log.info("=" * 60)

    md5 = checksum(xlsx_path)
    log.info(f"Input MD5: {md5}")
    log.info(f"Loading workbook in read_only mode (large file): {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    sheet_names = wb.sheetnames
    log.info(f"Sheets found: {len(sheet_names)}")

    all_courses   = []
    sheets_parsed = 0
    sheets_skipped = 0

    for i, name in enumerate(sheet_names):
        if i % 100 == 0:
            log.info(f"  Processing sheet {i}/{len(sheet_names)}: {name}")

        sheet = wb[name]
        col_map = detect_sheet_structure(sheet)

        if col_map is None:
            sheets_skipped += 1
            continue

        courses = parse_sheet(sheet, name, col_map)
        all_courses.extend(courses)
        sheets_parsed += 1

    wb.close()

    log.info(f"Sheets parsed:  {sheets_parsed}")
    log.info(f"Sheets skipped: {sheets_skipped} (no course data detected)")
    log.info(f"Courses extracted: {len(all_courses)}")

    if not all_courses:
        log.error("No courses extracted. Check column header candidates.")
        log.error("Open the xlsx manually and compare first-row headers "
                  "against RUBRIC_CANDIDATES, TITLE_CANDIDATES, etc.")
        raise ValueError("No courses parsed from xlsx.")

    df = pd.DataFrame(all_courses, columns=[
        "rubric", "course_number", "course_id", "course_title",
        "sch", "description", "slos", "slo_count", "combined_text",
        "source_sheet"
    ])

    # Drop exact duplicates (same course appearing in multiple sheets)
    before = len(df)
    df = df.drop_duplicates(subset=["course_id", "combined_text"])
    after = len(df)
    if before != after:
        log.info(f"Dropped {before - after} exact duplicates "
                 f"(same course_id + combined_text in multiple sheets)")

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

    update_transformation_log(xlsx_path, output_path, len(df),
                               sheets_parsed, md5)
    log.info("Done.")
    log.info("Next step: run 06_code/00c_build_corpus.py")


if __name__ == "__main__":
    main()
