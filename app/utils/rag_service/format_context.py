"""

"""
from typing import List, Dict
import logging
logger = logging.getLogger(__name__)
# from utils.load_vocabulary import get_style_rules

def format_context(passages: List[str], vocabulary: Dict[str, str], abbreviations: Dict[str, str], language: str) -> str:
    """
    Build the "Style Reference" block injected at the top of every enriched prompt.
    Returns an empty string when there is nothing useful to inject.
    """
    parts: List[str] = []

    # style_rules = get_style_rules(language)
    # if style_rules:
    #     rules_block = "\n".join(f"- {r}" for r in style_rules)
    #     parts.append(f"## Style Rules\n{rules_block}")

    if vocabulary:
        term_lines = "\n".join(f"- {en} → {target}" for en, target in list(vocabulary.items())[:30])
        parts.append(f"## Key Terminology\n{term_lines}")

    if passages:
        passage_block = "\n\n".join(f"> {p}" for p in passages[:3])
        parts.append(f"## Reference Passages\n{passage_block}")

    if abbreviations:
        term_lines = "\n".join(f"- {en} → {target}" for en, target in list(abbreviations.items())[:30])
        parts.append(f"## Abbreviations\n{term_lines}")

    if not parts:
        return ""

    header = "=== Style Reference (use this to guide tone and terminology) ==="
    footer = "=== End of Style Reference ==="
    logger.info("DEBUG: format Context %s", f"{header}\n" + "\n\n".join(parts) + f"\n{footer}")
    return f"{header}\n" + "\n\n".join(parts) + f"\n{footer}"

