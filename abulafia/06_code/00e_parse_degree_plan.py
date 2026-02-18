#!/usr/bin/env python3
"""
00e_parse_degree_plan.py
------------------------
Parses LSCO Modern Campus Catalog degree plan PDFs (browser Print-to-PDF format)
into target_degree_plans_YYYYMMDD.csv.

These PDFs are image-based (Microsoft: Print To PDF) and require OCR.

Output schema:
    institution, program, degree_type, semester, sequence,
    course_prefix, course_number, course_id, course_name,
    credit_hours, requirement_type, choice_group, source_file

requirement_type values:
    required      - must take this course
    choose_one    - pick one from a labeled group
    gen_ed        - general education / core requirement (no course ID)
    elective      - approved elective slot

Usage:
    python 00e_parse_degree_plan.py <input_dir> [output_dir]

Example:
    python 00e_parse_degree_plan.py /mnt/user-data/uploads /mnt/user-data/outputs
"""

import csv
import re
import sys
from pathlib import Path

try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.run(["pip", "install", "pdf2image", "pytesseract",
                    "--break-system-packages", "-q"], check=True)
    from pdf2image import convert_from_path
    import pytesseract


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# Course line: "WLDG 1323 - Welding Safety, Tools, and Equipment  3"
_COURSE_LINE = re.compile(
    r"^([A-Z]{2,6})\s+(\d{4})\s*[-–]\s*(.+?)\s+(\d)\s*$"
)
# Credit line adjacent to course: "Credits:" then next line has course
_CREDITS_PREFIX = re.compile(r"^Credits:?\s*$", re.IGNORECASE)
# Semester header
_SEMESTER = re.compile(
    r"^(First|Second|Third|Fourth|Fifth|Sixth)\s+Semester\s*$",
    re.IGNORECASE,
)
# "Choose One:" marker
_CHOOSE_ONE = re.compile(r"^Choose One:?\s*$", re.IGNORECASE)
# "OR" separator inside a choice group
_OR_LINE = re.compile(r"^\s*OR\s*$", re.IGNORECASE)
# Semester hours summary line — signals end of semester block
_SEM_HOURS = re.compile(r"^Semester Hours:", re.IGNORECASE)
# Program header line to extract metadata
_PROGRAM_LINE = re.compile(
    r"^(.+?),\s*(AAS|AS|AFA|Certificate|Level \d+)\s*$",
    re.IGNORECASE,
)
# Gen-ed placeholder lines (no real course ID)
_GEN_ED = re.compile(
    r"^(Lang Phil Cult Core|Soc Beh Sci Core|Creative Arts Core"
    r"|American History Core|Government Core|Component Area Option"
    r"|Approved Elective)\b",
    re.IGNORECASE,
)
# Lines to skip entirely
_SKIP = re.compile(
    r"^(Course Name|Catalog:|Student|Advisor|Campus|Minor|Degree Planner"
    r"|https?://|Registrar|General Elective|2/1|Page \d|\d+/\d+|$)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def parse_degree_plan_pdf(pdf_path: Path) -> list[dict]:
    pages = convert_from_path(str(pdf_path), dpi=200)
    raw_text = []
    for page in pages:
        raw_text.extend(pytesseract.image_to_string(page).split("\n"))

    rows          = []
    institution   = "Lamar State College Orange"
    program       = "Unknown Program"
    degree_type   = "AAS"
    current_sem   = None
    sem_seq       = 0        # 1-based semester counter
    in_choose_one = False
    or_expected   = False    # True right after "OR" line
    first_in_group = False   # True for the very first course after "Choose One:"
    choice_group  = 0        # increments each time we see "Choose One"
    seq           = 0        # row sequence within semester
    source        = pdf_path.name

    # First pass: find program name
    for line in raw_text:
        m = _PROGRAM_LINE.match(line.strip())
        if m and not any(skip in line for skip in
                         ["Course", "Catalog", "Student", "Campus"]):
            program     = m.group(1).strip()
            degree_type = m.group(2).strip().upper()
            break

    # Second pass: extract courses
    i = 0
    while i < len(raw_text):
        line = raw_text[i].strip()

        # Skip empty and noise
        if not line or _SKIP.match(line):
            i += 1
            continue

        # Semester header
        m = _SEMESTER.match(line)
        if m:
            sem_name    = m.group(1).capitalize()
            sem_seq     += 1
            current_sem = sem_name
            in_choose_one  = False
            or_expected    = False
            first_in_group = False
            seq = 0
            i += 1
            continue

        # End of semester block
        if _SEM_HOURS.match(line):
            in_choose_one  = False
            or_expected    = False
            first_in_group = False
            i += 1
            continue

        # Choose One marker
        if _CHOOSE_ONE.match(line):
            in_choose_one  = True
            or_expected    = False
            first_in_group = True   # next course is first in group
            choice_group  += 1
            i += 1
            continue

        # OR separator — next course stays in current group
        if _OR_LINE.match(line):
            or_expected    = True
            first_in_group = False
            i += 1
            continue

        # Credits: prefix line — skip, the course follows
        if _CREDITS_PREFIX.match(line):
            i += 1
            continue

        # Gen-ed / elective placeholder (no course ID)
        if _GEN_ED.match(line):
            if current_sem:
                seq += 1
                req_type = "elective" if "Elective" in line else "gen_ed"
                rows.append({
                    "institution":    institution,
                    "program":        program,
                    "degree_type":    degree_type,
                    "semester":       current_sem,
                    "sequence":       seq,
                    "course_prefix":  "",
                    "course_number":  "",
                    "course_id":      "",
                    "course_name":    line.strip(),
                    "credit_hours":   3,
                    "requirement_type": req_type,
                    "choice_group":   choice_group if in_choose_one else "",
                    "source_file":    source,
                })
            i += 1
            continue

        # Course line: PREFIX NNNN - Name  Credits
        m = _COURSE_LINE.match(line)
        if m and current_sem:
            prefix, number, name, credits = (
                m.group(1), m.group(2), m.group(3).strip(), int(m.group(4))
            )
            # Determine if this course belongs to a choose_one group:
            # - first course right after "Choose One:", OR
            # - course after explicit "OR" separator
            in_group = in_choose_one and (first_in_group or or_expected)
            if in_choose_one and not in_group:
                in_choose_one = False  # group ended implicitly
            req_type       = "choose_one" if in_group else "required"
            or_expected    = False
            first_in_group = False
            seq += 1
            rows.append({
                "institution":    institution,
                "program":        program,
                "degree_type":    degree_type,
                "semester":       current_sem,
                "sequence":       seq,
                "course_prefix":  prefix,
                "course_number":  number,
                "course_id":      f"{prefix} {number}",
                "course_name":    name,
                "credit_hours":   credits,
                "requirement_type": req_type,
                "choice_group":   choice_group if req_type == "choose_one" else "",
                "source_file":    source,
            })
            i += 1
            continue

        # Course line missing credit count at end (OCR dropout)
        m2 = re.match(r"^([A-Z]{2,6})\s+(\d{4})\s*[-–]\s*(.+)$", line)
        if m2 and current_sem:
            prefix, number, name = m2.group(1), m2.group(2), m2.group(3).strip()
            credits = 3
            for j in range(i + 1, min(i + 4, len(raw_text))):
                peek = raw_text[j].strip()
                if re.match(r"^\d$", peek):
                    credits = int(peek)
                    break
                if peek and not _CREDITS_PREFIX.match(peek):
                    break
            in_group = in_choose_one and (first_in_group or or_expected)
            if in_choose_one and not in_group:
                in_choose_one = False
            req_type       = "choose_one" if in_group else "required"
            or_expected    = False
            first_in_group = False
            seq += 1
            rows.append({
                "institution":    institution,
                "program":        program,
                "degree_type":    degree_type,
                "semester":       current_sem,
                "sequence":       seq,
                "course_prefix":  prefix,
                "course_number":  number,
                "course_id":      f"{prefix} {number}",
                "course_name":    name,
                "credit_hours":   credits,
                "requirement_type": req_type,
                "choice_group":   choice_group if req_type == "choose_one" else "",
                "source_file":    source,
            })
            i += 1
            continue

        i += 1

    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "institution", "program", "degree_type", "semester", "sequence",
    "course_prefix", "course_number", "course_id", "course_name",
    "credit_hours", "requirement_type", "choice_group", "source_file",
]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_dir  = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_dir

    pdfs = sorted(input_dir.glob("target_degree_plans_*.pdf"))
    if not pdfs:
        print(f"No target_degree_plans_*.pdf files found in {input_dir}")
        sys.exit(1)

    stem      = pdfs[0].stem
    datestamp = re.search(r"_(\d{8})", stem).group(1)
    out_path  = output_dir / f"target_degree_plans_{datestamp}.csv"

    all_rows = []
    for pdf_path in pdfs:
        rows = parse_degree_plan_pdf(pdf_path)
        all_rows.extend(rows)
        print(f"  {pdf_path.name}  →  {len(rows)} rows")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows → {out_path}")

    # Summary
    from collections import Counter
    by_type = Counter(r["requirement_type"] for r in all_rows)
    by_sem  = Counter(r["semester"] for r in all_rows)
    prefixes = sorted(set(r["course_prefix"] for r in all_rows if r["course_prefix"]))
    print(f"\nBy requirement type: {dict(by_type)}")
    print(f"By semester:         {dict(by_sem)}")
    print(f"Course prefixes:     {prefixes}")
    print(f"Total course IDs:    {len([r for r in all_rows if r['course_id']])}")


if __name__ == "__main__":
    main()
