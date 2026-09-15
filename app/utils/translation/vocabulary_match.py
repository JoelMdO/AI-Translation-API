import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from utils.load_vocabulary import get_vocabulary


@dataclass(frozen=True)
class VocabularyMatch:
    source: str
    target: str
    score: float
    match_type: Literal["exact", "semantic"]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold()

    # Treat common dash variants consistently.
    value = re.sub(r"[‐‑‒–—−]", "-", value)

    # Collapse repeated whitespace.
    return re.sub(r"\s+", " ", value).strip()


def term_pattern(term: str) -> re.Pattern[str]:
    normalized = normalize_text(term)

    # Allow a glossary hyphen or space to match either form.
    pieces = re.split(r"[\s-]+", normalized)
    expression = r"[\s-]+".join(re.escape(piece) for piece in pieces)

    # Avoid matching terms inside larger words.
    return re.compile(rf"(?<!\w){expression}(?!\w)", re.IGNORECASE)


def find_exact_matches(
    text: str,
    target_language: str,
    max_terms: int = 15,
) -> list[VocabularyMatch]:
    vocabulary = get_vocabulary(target_language)
    normalized_text = normalize_text(text)

    # Longer phrases are checked first.
    ordered_terms = sorted(
        vocabulary.items(),
        key=lambda item: len(normalize_text(item[0])),
        reverse=True,
    )

    matches: list[VocabularyMatch] = []
    occupied_spans: list[tuple[int, int]] = []

    for source, target in ordered_terms:
        match = term_pattern(source).search(normalized_text)

        if not match:
            continue

        span = match.span()

        # Prevent a shorter term from duplicating part of a longer phrase.
        overlaps = any(
            span[0] < occupied_end and span[1] > occupied_start
            for occupied_start, occupied_end in occupied_spans
        )

        if overlaps:
            continue

        matches.append(
            VocabularyMatch(
                source=source,
                target=target,
                score=1.0,
                match_type="exact",
            )
        )
        occupied_spans.append(span)

        if len(matches) >= max_terms:
            break

    return matches