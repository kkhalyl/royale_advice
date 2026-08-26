"""Deterministic (no-LLM) tagging of raw Reddit content by card/archetype/
king-level. This is the cheap pre-filter that runs before the expensive
LLM summarization step - only content that matches at least one tag gets
summarized, keeping LLM usage bounded.
"""

import re
from typing import List, Optional, Tuple

ARCHETYPE_KEYWORDS = {
    "cycle": ["cycle"],
    "beatdown": ["beatdown"],
    "control": ["control deck", "control"],
    "siege": ["siege"],
}

_KING_LEVEL_PATTERNS = [
    re.compile(r"king level (\d{1,2})", re.IGNORECASE),
    re.compile(r"\bkt\s?(\d{1,2})\b", re.IGNORECASE),
    re.compile(r"level (\d{1,2}) king tower", re.IGNORECASE),
]


def find_mentioned_cards(text: str, known_card_names: List[str]) -> List[str]:
    """Substring-match known card names (case-insensitive) in text.
    Returns names in their original casing from known_card_names."""
    lowered = text.lower()
    return [name for name in known_card_names if name.lower() in lowered]


def find_mentioned_archetype(text: str) -> Optional[str]:
    """Return the first archetype whose keyword(s) appear in text, or None."""
    lowered = text.lower()
    for archetype, keywords in ARCHETYPE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return archetype
    return None


def find_king_level_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract an explicit king-level mention as a (min, max) range - both
    values are the same single level found, or (None, None) if no explicit
    level is mentioned (the tip then applies generally, not level-scoped)."""
    for pattern in _KING_LEVEL_PATTERNS:
        match = pattern.search(text)
        if match:
            level = int(match.group(1))
            return level, level
    return None, None


def is_taggable(text: str, known_card_names: List[str]) -> bool:
    """True if this content matched at least one card/archetype/level tag."""
    if find_mentioned_cards(text, known_card_names):
        return True
    if find_mentioned_archetype(text):
        return True
    level_min, _ = find_king_level_range(text)
    return level_min is not None
