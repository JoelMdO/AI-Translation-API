"""
pdf_to_json.py — Convert an aviation vocabulary PDF to a list of entries.

Usage:
    python pdf_to_json.py <input.pdf> [output.json]

If output.json is omitted the result is printed to stdout.

Dependencies:
    pip install pymupdf

The PDF is structured as repeating triplets of lines:
    <ABBREVIATION>
    <English term>
    <Spanish term>

Noise lines (page numbers, single-letter section headers, title) are filtered
before grouping so that every 3 consecutive lines form one entry.

Output format:
[
  {"abbreviation": "A/A", "english": "Air/air", "spanish": "Aire a aire"},
  ...
]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

try:
    import pymupdf  # type: ignore[import]
except ImportError:
    sys.exit("pymupdf is required.  Install it with:  pip install pymupdf")


# Noise-line patterns to skip during extraction
_SECTION_HEADER_RE = re.compile(r'^[A-Z]$')
_PAGE_NUMBER_RE = re.compile(r'^\d+$')
_TITLE_WORDS = ('VOCABULARIO', 'INGLÉS', 'ESPAÑOL', 'AERONÁUTICO')


def _is_noise(line: str) -> bool:
    """Return True for lines that are not vocabulary content."""
    if _SECTION_HEADER_RE.match(line):
        return True
    if _PAGE_NUMBER_RE.match(line):
        return True
    upper = line.upper()
    return any(word in upper for word in _TITLE_WORDS)


# ── Extraction ─────────────────────────────────────────────────────────────────

def extract_entries(pdf_path: str) -> List[Dict[str, str]]:
    """
    Extract vocabulary entries from the PDF using PyMuPDF.

    The PDF is structured as repeating triplets of text lines per entry:
        <ABBREVIATION>   e.g. "A/A"
        <English term>   e.g. "Air/air"
        <Spanish term>   e.g. "Aire a aire"

    Noise lines (page numbers, single-letter section headers, title) are
    filtered out before grouping.
    """
    doc = pymupdf.open(pdf_path) # type: ignore[attr-defined]

    lines: List[str] = []
    for page in doc: # type: ignore[attr-defined]
        for raw in page.get_text().splitlines(): # type: ignore[attr-defined]
            s = raw.strip() # type: ignore[attr-defined]
            if s and not _is_noise(s): # type: ignore[attr-defined]
                lines.append(s) # type: ignore[attr-defined]

    entries: List[Dict[str, str]] = []
    i = 0
    while i + 2 < len(lines):
        entries.append({
            "abbreviation": lines[i],
            "english": lines[i + 1],
            "spanish": lines[i + 2],
        })
        i += 3

    return entries


# ── Main ───────────────────────────────────────────────────────────────────────

def convert(pdf_path: str, output_path: str | None = None) -> List[Dict[str, str]]:
    path = Path(pdf_path)
    if not path.exists():
        sys.exit(f"File not found: {pdf_path}")

    print(f"Extracting from: {path.name}", file=sys.stderr)

    entries = extract_entries(pdf_path)

    if not entries:
        print("⚠️  No entries found. The PDF may be scanned/image-based.", file=sys.stderr)

    print(f"Entries found : {len(entries)}", file=sys.stderr)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"✅ Written to: {output_path}", file=sys.stderr)
    else:
        print(json.dumps(entries, ensure_ascii=False, indent=2))

    return entries


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {Path(__file__).name} <input.pdf> [output.json]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert(pdf_file, out_file)
