import re

def extract_abbreviations(text: str) -> set[str]:
        """ Extract aviation-style abbreviations from text.
        Handles:
        - ATC, ICAO, FAA
        - V1, V2, FL350
        - Capt., Cmdr.
        Matches:
        - All caps words (2–6 chars): ATC, ICAO
        - Alphanumeric aviation terms: V1, FL350
        - Titles with period: Capt., Cmdr.
        """
        pattern = r"\b([A-Z]{2,6}|[A-Z]+\d+|[A-Z][a-z]{2,}\.)\b"

        matches = re.findall(pattern, text)

        # Normalize (NLTK expects lowercase abbrev types)
        abbrevs = {m.lower().rstrip('.') for m in matches}

        return abbrevs
