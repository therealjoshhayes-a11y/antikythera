#!/usr/bin/env python3
"""
parse_target_standards.py
--------------------------
Parses NCCER lesson-plan PDFs matching the naming convention:
    target_standards_YYYYMMDD[A-Z].pdf

Handles two NCCER PDF layouts automatically:
  - Format A/B  : "Lesson Plans for Module XXXXX" two-column layout
  - Format C    : Compact single-column "Welding Level Two" style

Outputs a single merged CSV to:
    target_standards_YYYYMMDD.csv

matching the schema expected by the alignment pipeline:
    standard_id, framework, program, module_id, module_title,
    objective_level, objective_code, standard_text, source_file

Usage:
    python parse_target_standards.py <input_dir> [output_dir]

    input_dir  : folder containing target_standards_*.pdf files
    output_dir : destination for output CSV (defaults to input_dir)

Example:
    python parse_target_standards.py /mnt/user-data/uploads /mnt/user-data/outputs
"""

import csv
import re
import sys
from pathlib import Path

import pdfplumber


# ---------------------------------------------------------------------------
# Module-number → program name mapping
# ---------------------------------------------------------------------------
def _program_from_module_id(module_id: str) -> tuple[str, str]:
    """Return (program_code, program_name) from a 5-digit NCCER module ID."""
    prefix = module_id[:3]
    mapping = {
        "001": ("CORE",  "NCCER Core"),
        "291": ("WLD1",  "NCCER Welding Level 1"),
        "292": ("WLD2",  "NCCER Welding Level 2"),
        "293": ("WLD3",  "NCCER Welding Level 3"),
        "294": ("WLD4",  "NCCER Welding Level 4"),
        "271": ("HVAC1", "NCCER HVAC Level 1"),
        "272": ("HVAC2", "NCCER HVAC Level 2"),
        "231": ("ELEC1", "NCCER Electrical Level 1"),
        "232": ("ELEC2", "NCCER Electrical Level 2"),
        "251": ("PIPE1", "NCCER Pipefitting Level 1"),
        "252": ("PIPE2", "NCCER Pipefitting Level 2"),
    }
    code, name = mapping.get(prefix, ("NCCER", "NCCER"))
    return code, name


# ---------------------------------------------------------------------------
# Text cleaning helpers
# ---------------------------------------------------------------------------
_HYPHEN_BREAK = re.compile(r"-\s*\n\s*(?=[a-z])")   # only collapse when next line starts lowercase
_MULTI_SPACE  = re.compile(r"[ \t]{2,}")
_NOISE_LINES  = re.compile(
    r"^(Before You Begin|Safety Considerations|Classroom Equipment|"
    r"Additional Resources|Equipment and Materials|Performance Tasks?|"
    r"Recommended Teaching Time|Copyright ©|Lesson Plans for|"
    r"Materials Checklist|Copies of|Instructors? (are|should|were)|"
    r"Using your access code|This module presents|"
    r"Welding Level (One|Two|Three|Four)\s*\|?\s*\d*$)",
    re.IGNORECASE,
)
# Lines that signal the end of the Objectives section entirely
_SECTION_STOP = re.compile(
    r"^(Before You Begin|Safety Considerations|Classroom Equipment|"
    r"Additional Resources|Recommended Teaching Time|Materials Checklist|"
    r"Performance Tasks?)",
    re.IGNORECASE,
)
# Numbered performance task lines: "1. text" or "1.text"
_PERF_TASK_LINE = re.compile(r"^\d+\.?\s")

def _clean(text: str) -> str:
    text = _HYPHEN_BREAK.sub("", text)
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Objective block parser (shared by both formats)
# ---------------------------------------------------------------------------
_LO_HEADER  = re.compile(r"^Learning Objective\s+(\d+)\s*$", re.IGNORECASE)
_SUB_LINE   = re.compile(r"^([a-z])\.\s+(.+)$")

def _parse_objective_blocks(lines: list[str]) -> list[dict]:
    """
    Given cleaned lines from one column / one page, extract objective blocks.
    Returns list of dicts with keys: lo_num, parent_text, subs [(code, text), ...]
    """
    objectives     = []
    current_lo     = None
    current_text   = []
    current_subs   = []
    in_sub         = False
    sub_buf        = {}   # code -> accumulating text
    objs_started   = False  # True once we've seen the first LO header

    def _flush():
        nonlocal current_lo, current_text, current_subs, in_sub, sub_buf
        if current_lo is None:
            return
        # flush any pending sub
        if sub_buf:
            code, txt = list(sub_buf.items())[-1]
            current_subs.append((code, _clean(txt)))
            sub_buf = {}
        parent = _clean(" ".join(current_text))
        if parent:
            objectives.append({
                "lo_num":      current_lo,
                "parent_text": parent,
                "subs":        list(current_subs),
            })
        current_lo   = None
        current_text = []
        current_subs = []
        in_sub       = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Hard stop — only once we've entered the Objectives section
        if objs_started and _SECTION_STOP.match(line):
            break

        # Skip numbered performance task lines and other noise
        if _NOISE_LINES.match(line) or _PERF_TASK_LINE.match(line):
            continue

        # New "Learning Objective N"
        m = _LO_HEADER.match(line)
        if m:
            _flush()
            current_lo    = m.group(1)
            objs_started  = True
            in_sub        = False
            continue

        if current_lo is None:
            continue

        # Sub-objective line: "a. text" (also handles "a.text" from Level 2)
        sub_m = _SUB_LINE.match(line) or re.match(r"^([a-z])\.(.+)$", line)
        if sub_m:
            # flush previous sub if any
            if sub_buf:
                code, txt = list(sub_buf.items())[-1]
                current_subs.append((code, _clean(txt)))
                sub_buf = {}
            in_sub = True
            sub_buf[sub_m.group(1)] = sub_m.group(2).strip()
            continue

        # Continuation of sub-objective (indented continuation)
        if in_sub and sub_buf:
            code = list(sub_buf.keys())[-1]
            sub_buf[code] += " " + line
            continue

        # Continuation of parent objective text
        if not in_sub:
            current_text.append(line)

    _flush()
    return objectives


# ---------------------------------------------------------------------------
# Format A/B parser  (two-column "Lesson Plans" layout)
# ---------------------------------------------------------------------------
_MODULE_HEADER_AB = re.compile(
    r"Lesson Plans for Module\s+(\d{5})", re.IGNORECASE
)
_TITLE_NOISE = re.compile(
    r"(Build Your Future in ConstruCtion|Basic Safety|Introduction to|"
    r"Module \d{5})", re.IGNORECASE
)

def _extract_module_title_ab(raw_page_text: str, module_id: str) -> str:
    """Recover module title from the page header area."""
    # The title line usually follows "Lesson Plans for Module XXXXX"
    lines = raw_page_text.split("\n")
    for i, ln in enumerate(lines):
        if re.search(r"Lesson Plans for Module", ln, re.IGNORECASE):
            # Title is on the same line after "Module XXXXX" or the next line
            rest = re.sub(r"Lesson Plans for Module\s+\d{5}", "", ln).strip()
            if rest and not re.match(r"^\d", rest):
                return _clean(rest)
            # Try next non-empty line
            for j in range(i + 1, min(i + 4, len(lines))):
                candidate = lines[j].strip()
                # Strip ALL-CAPS artifact from PDF title rendering
                candidate_normal = candidate.title()
                if candidate and not re.match(r"^\d", candidate):
                    return _clean(candidate_normal)
    return f"Module {module_id}"


def _parse_ab_page(page) -> list[dict]:
    """
    Split one page at the horizontal midpoint, extract objectives from
    both columns independently, return list of (module_id, title, objectives).
    Returns [] if no module header found on this page.
    """
    raw_full = page.extract_text() or ""

    # Only process pages that contain at least one "Learning Objective"
    if "Learning Objective" not in raw_full:
        return []

    width    = page.width
    mid      = width / 2

    left_txt  = _HYPHEN_BREAK.sub("", page.crop((0,    0, mid,   page.height)).extract_text() or "")
    right_txt = _HYPHEN_BREAK.sub("", page.crop((mid,  0, width, page.height)).extract_text() or "")

    # Detect module id from full text
    m = _MODULE_HEADER_AB.search(raw_full)
    if not m:
        return []
    module_id = m.group(1)
    title     = _extract_module_title_ab(raw_full, module_id)

    left_objs  = _parse_objective_blocks(left_txt.split("\n"))
    right_objs = _parse_objective_blocks(right_txt.split("\n"))

    results = []
    for obj in left_objs + right_objs:
        results.append({
            "module_id":    module_id,
            "module_title": title,
            "lo_num":       obj["lo_num"],
            "parent_text":  obj["parent_text"],
            "subs":         obj["subs"],
        })
    return results


# ---------------------------------------------------------------------------
# Format C parser  (single-column compact "Welding Level Two" layout)
# Processes the ENTIRE PDF as a stream to handle cross-page objective splits.
# ---------------------------------------------------------------------------
_MODULE_ID_C = re.compile(r"^(\d{5})\s*$")
_PREAMBLE_C  = re.compile(
    r"Successful completion of this module prepares trainees to:?",
    re.IGNORECASE,
)
_PAGE_BREAK_NOISE = re.compile(
    r"^(Welding Level (One|Two|Three|Four)\s*\|?\s*\d*|Copyright ©)",
    re.IGNORECASE,
)

def _parse_c_pdf(pdf_path: Path) -> list[dict]:
    """
    Parse an entire Format-C PDF as one continuous text stream.
    Yields (module_id, module_title, objectives_list) for each module.
    """
    # Collect all page lines into a single stream
    all_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text() or ""
            raw = _HYPHEN_BREAK.sub("", raw)
            for ln in raw.split("\n"):
                all_lines.append(ln)

    results = []
    current_module_id    = None
    current_module_title = None
    pending_objectives   = []   # accumulate raw LO blocks before next module

    i = 0
    while i < len(all_lines):
        ln = all_lines[i].strip()

        # Detect module boundary (standalone 5-digit number)
        m = _MODULE_ID_C.match(ln)
        if m:
            # Flush previous module
            if current_module_id and pending_objectives:
                for obj in _parse_objective_blocks(pending_objectives):
                    results.append({
                        "module_id":    current_module_id,
                        "module_title": current_module_title,
                        "lo_num":       obj["lo_num"],
                        "parent_text":  obj["parent_text"],
                        "subs":         obj["subs"],
                    })
            current_module_id = m.group(1)
            pending_objectives = []
            # Title is next non-trivial line
            current_module_title = f"Module {current_module_id}"
            for j in range(i + 1, min(i + 6, len(all_lines))):
                candidate = all_lines[j].strip()
                if candidate and not re.match(
                    r"^(Welding|Overview|Learning Objective|Copyright|Performance|\d)",
                    candidate, re.IGNORECASE
                ):
                    current_module_title = _clean(candidate)
                    break
            i += 1
            continue

        # Skip page-break noise
        if _PAGE_BREAK_NOISE.match(ln):
            i += 1
            continue

        # Skip preamble
        if _PREAMBLE_C.match(ln):
            i += 1
            continue

        # Accumulate into current module's objective stream
        if current_module_id:
            pending_objectives.append(ln)

        i += 1

    # Flush last module
    if current_module_id and pending_objectives:
        for obj in _parse_objective_blocks(pending_objectives):
            results.append({
                "module_id":    current_module_id,
                "module_title": current_module_title,
                "lo_num":       obj["lo_num"],
                "parent_text":  obj["parent_text"],
                "subs":         obj["subs"],
            })

    return results


# ---------------------------------------------------------------------------
# Format detector
# ---------------------------------------------------------------------------
def _detect_format(pdf_path: Path) -> str:
    """Return 'AB' or 'C' based on first-page content."""
    with pdfplumber.open(pdf_path) as pdf:
        first = pdf.pages[0].extract_text() or ""
    if "Lesson Plans for Module" in first:
        return "AB"
    return "C"


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------
def parse_pdf(pdf_path: Path) -> list[dict]:
    """
    Parse one PDF, return list of row dicts ready for CSV output.
    """
    fmt       = _detect_format(pdf_path)
    source    = pdf_path.name
    rows      = []
    seen_mods = {}  # module_id -> title (de-dup across pages)

    if fmt == "C":
        entries = _parse_c_pdf(pdf_path)
    else:
        entries = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                entries.extend(_parse_ab_page(page))

    for e in entries:
        mid    = e["module_id"]
        title  = seen_mods.get(mid, e["module_title"])
        seen_mods[mid] = title

        prog_code, prog_name = _program_from_module_id(mid)

        lo_code  = f"LO{e['lo_num']}"
        std_id   = f"NCCER-{prog_code}-{mid}-{lo_code}"

        # Parent / module-level row
        rows.append({
            "standard_id":     std_id,
            "framework":       "NCCER",
            "program":         prog_name,
            "module_id":       mid,
            "module_title":    title,
            "objective_level": "module",
            "objective_code":  lo_code,
            "standard_text":   e["parent_text"],
            "source_file":     source,
        })

        # Sub-objective rows
        for sub_code, sub_text in e["subs"]:
            full_sub_code = f"{lo_code}{sub_code}"
            sub_std_id    = f"NCCER-{prog_code}-{mid}-{full_sub_code}"
            rows.append({
                "standard_id":     sub_std_id,
                "framework":       "NCCER",
                "program":         prog_name,
                "module_id":       mid,
                "module_title":    title,
                "objective_level": "sub",
                "objective_code":  full_sub_code,
                "standard_text":   sub_text,
                "source_file":     source,
            })

    return rows


# ---------------------------------------------------------------------------
# De-duplication (same standard_id may appear on multiple pages)
# ---------------------------------------------------------------------------
def _dedup(rows: list[dict]) -> list[dict]:
    seen = {}
    for r in rows:
        key = r["standard_id"]
        if key not in seen:
            seen[key] = r
    return list(seen.values())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "standard_id", "framework", "program", "module_id", "module_title",
    "objective_level", "objective_code", "standard_text", "source_file",
]

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_dir  = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_dir

    # Find all matching PDFs, sort for deterministic order
    pdfs = sorted(input_dir.glob("target_standards_*.pdf"))
    if not pdfs:
        print(f"No target_standards_*.pdf files found in {input_dir}")
        sys.exit(1)

    # Derive datestamp from first filename (e.g. target_standards_20260218A.pdf → 20260218)
    stem      = pdfs[0].stem                          # "target_standards_20260218A"
    datestamp = re.search(r"_(\d{8})", stem).group(1) # "20260218"
    out_path  = output_dir / f"target_standards_{datestamp}.csv"

    all_rows = []
    for pdf_path in pdfs:
        fmt = _detect_format(pdf_path)
        rows = parse_pdf(pdf_path)
        all_rows.extend(rows)
        print(f"  {pdf_path.name}  [{fmt}]  →  {len(rows)} rows")

    all_rows = _dedup(all_rows)
    # Sort for deterministic output: program → module_id → objective_code
    all_rows.sort(key=lambda r: (r["program"], r["module_id"], r["objective_code"]))

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows → {out_path}")

    # Summary
    from collections import Counter
    by_prog  = Counter(r["program"]          for r in all_rows)
    by_level = Counter(r["objective_level"]  for r in all_rows)
    by_mod   = len(set(r["module_id"]        for r in all_rows))
    print("\nRows by program:")
    for k, v in sorted(by_prog.items()):
        print(f"  {k:<40} {v}")
    print(f"\nRows by objective level:  {dict(by_level)}")
    print(f"Unique modules parsed:    {by_mod}")


if __name__ == "__main__":
    main()
