"""

"""
from .format_context import format_context
from utils.load_vocabulary import get_abbreviations, get_vocabulary
from .query import query

async def build_context_block(text: str, language: str) -> str:
    """
    Convenience wrapper used by the services.
    Queries ChromaDB, loads vocabulary, formats and returns the context block.
    An empty string is returned when RAG is unavailable.
    """
    lang = language
    passages = await query(text, lang)
    vocabulary = get_vocabulary(lang)
    abbreviations = get_abbreviations()
    return format_context(passages, vocabulary, abbreviations, lang)
