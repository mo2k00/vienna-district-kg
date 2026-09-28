import re

SPORTS = ("tennis", "football", "basketball", "volleyball", "fitness", "swimming")

_PATTERNS = {
    "tennis": re.compile(r"(?<!tisch)tennis"),
    "football": re.compile(r"fu(ß|ss)ball|rasenplatz|kunstrasen|polysportiv|soccer"),
    "basketball": re.compile(r"basketball|streetball|polysportiv"),
    "volleyball": re.compile(r"volleyball"),
    "fitness": re.compile(r"fitness|kraftkammer|calisthenics"),
    "swimming": re.compile(r"\b(sommer|hallen|frei|familien)?bad\b|schwimm|swimming"),
}


def sports_in(text: str | None) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    return [sport for sport, pattern in _PATTERNS.items() if pattern.search(lowered)]
