import re

_WORD = re.compile(r"[a-z0-9']+")


def word_count(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for w in _WORD.findall(text.lower()):
        counts[w] = counts.get(w, 0) + 1
    return counts
