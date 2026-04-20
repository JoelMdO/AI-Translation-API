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
  {"abbreviation": "A/A", "english": "air air", "spanish": "aire a aire", "id": "entry_0"},
  ...
]

Normalized for embedding generation (Aya + Chroma) with English to Spanish translation.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List

try:
    import pymupdf
except ImportError:
    sys.exit("pymupdf is required.  Install it with:  pip install pymupdf")


NOISE_PATTERNS = [
    re.compile(r'^[A-Z]$'),
    re.compile(r'^\d+$'),
    re.compile(r'^VOCABULARIO.*', re.IGNORECASE),
    re.compile(r'^INGLÉS.*', re.IGNORECASE),
    re.compile(r'^ESPAÑOL.*', re.IGNORECASE),
    re.compile(r'^AERONÁUTICO.*', re.IGNORECASE),
    re.compile(r'^ABREVIATURAS.*', re.IGNORECASE),
]


def normalize_text(text: str) -> str:
    """Normalize text for embedding generation."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def clean_abbreviation(text: str) -> str:
    """Clean abbreviation, preserving slashes and special chars."""
    return text.strip()


def is_noise(line: str) -> bool:
    """Return True for lines that are not vocabulary content."""
    line = line.strip()
    if not line:
        return True
    for pattern in NOISE_PATTERNS:
        if pattern.match(line):
            return True
    return False


def extract_from_table(page) -> List[List[str]]:
    """Try to extract vocabulary from PDF tables."""
    tables = page.find_tables()
    if tables and tables[0].rows:
        rows = []
        for table in tables:
            for row in table.extract():
                if len(row) >= 3:
                    rows.append([normalize_text(c) if i > 0 else c for i, c in enumerate(row[:3])])
        return rows
    return []


def extract_entries(pdf_path: str, use_tables: bool = True) -> List[Dict[str, str]]:
    """
    Extract vocabulary entries from the PDF using PyMuPDF.
    
    Attempts table extraction first, then falls back to line-based extraction.
    Applies normalization for embedding generation.
    """
    doc = pymupdf.open(pdf_path)
    
    entries: List[Dict[str, str]] = []
    
    for page_num, page in enumerate(doc):
        if use_tables:
            table_rows = extract_from_table(page)
            if table_rows:
                i = 0
                while i + 2 < len(table_rows):
                    row = table_rows[i]
                    if len(row) >= 3:
                        entry = {
                            "abbreviation": clean_abbreviation(row[0]),
                            "english": row[1],
                            "spanish": row[2],
                        }
                        if entry["abbreviation"] and entry["english"] and entry["spanish"]:
                            entries.append(entry)
                    i += 3
                continue
        
        lines: List[str] = []
        for raw in page.get_text().splitlines():
            s = raw.strip()
            if s and not is_noise(s):
                lines.append(s)
        
        i = 0
        while i + 2 < len(lines):
            entry = {
                "abbreviation": clean_abbreviation(lines[i]),
                "english": normalize_text(lines[i + 1]),
                "spanish": normalize_text(lines[i + 2]),
            }
            if entry["abbreviation"] and entry["english"] and entry["spanish"]:
                entries.append(entry)
            i += 3
    
    doc.close()
    return entries


def prepare_for_embedding(entry: Dict[str, str], index: int) -> Dict[str, str]:
    """Prepare entry with embedding-ready text and unique ID."""
    return {
        "id": f"entry_{index}",
        "abbreviation": entry["abbreviation"],
        "english": entry["english"],
        "spanish": entry["spanish"],
        "english_text": f"Translate to Spanish: {entry['english']}",
        "spanish_text": entry["spanish"],
        "combined_text": f"{entry['english']} | {entry['spanish']}",
    }


def convert(pdf_path: str, output_path: str | None = None, use_tables: bool = True) -> List[Dict[str, str]]:
    """
    Convert PDF to normalized JSON entries.
    
    Args:
        pdf_path: Path to input PDF file
        output_path: Optional path for JSON output
        use_tables: Attempt table extraction first (default True)
    """
    path = Path(pdf_path)
    if not path.exists():
        sys.exit(f"File not found: {pdf_path}")

    print(f"Extracting from: {path.name}", file=sys.stderr)

    entries = extract_entries(pdf_path, use_tables=use_tables)

    if not entries:
        print("No entries found. Trying fallback extraction...", file=sys.stderr)
        entries = extract_entries(pdf_path, use_tables=False)

    print(f"Entries found: {len(entries)}", file=sys.stderr)

    embedding_ready = [prepare_for_embedding(entry, i) for i, entry in enumerate(entries)]

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(embedding_ready, f, ensure_ascii=False, indent=2)
        print(f"Wrote to: {output_path}", file=sys.stderr)
    else:
        print(json.dumps(embedding_ready, ensure_ascii=False, indent=2))

    return embedding_ready


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {Path(__file__).name} <input.pdf> [output.json]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert(pdf_file, out_file)
