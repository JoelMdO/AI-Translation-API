"""
Vocabulary loader — loads vocabulary.json once at import time.

Exposes:
  get_vocabulary(language) -> dict   bilingual term map for the given language
  get_style_rules(language) -> list  style rule strings for the given language
"""
import json
import os
from typing import Dict, List, Any

_cache: Dict[str, Any] = {}

def _load() -> None:
    if _cache:
        return
    vocab_path = os.path.join(os.path.dirname(__file__), "..", "data", "vocabulary.json")
    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["style_rules"] = data.get("style_rules", {})
        _cache["vocabulary"] = data.get("vocabulary", {})
        print("✅ vocabulary.json loaded")
    except Exception as e:
        print(f"⚠️  Could not load vocabulary.json: {e}")
        _cache["style_rules"] = {}
        _cache["vocabulary"] = {}
    abbrev_path = os.path.join(os.path.dirname(__file__), "..", "data", "abbreviation.json")
    try:
        with open(abbrev_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert list of objects to dict: {abbreviation: spanish}
        _cache["abbreviation"] = {
            item["abbreviation"]: item["spanish"]
            for item in data
            if "abbreviation" in item and "spanish" in item
        }
        print("✅ abbreviation.json loaded")
    except Exception as e:
        print(f"⚠️  Could not load abbreviation.json: {e}")
        _cache["abbreviation"] = {}

def get_vocabulary(language: str) -> Dict[str, str]:
    """Return the EN→target or ES→target term map for the given language."""
    _load()
    lang = language.lower()[:2]
    return _cache.get("vocabulary", {}).get(lang, {})


def get_style_rules(language: str) -> List[str]:
    """Return per-language style rule strings."""
    _load()
    lang = language.lower()[:2]
    return _cache.get("style_rules", {}).get(lang, [])

def get_abbreviations() -> Dict[str, str]:
    """Return the abbreviation → Spanish term map."""
    _load()
    return _cache.get("abbreviation", {})

def get_summary_rules(language: str) -> List[str]:
    """Return per-language summary rule strings."""
    _load()
    lang = language.lower()[:2]
    return _cache.get("summary_rules", {}).get(lang, [])