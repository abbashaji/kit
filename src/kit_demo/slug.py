import re


def slugify(text: str) -> str:
    """Lowercase, collapse runs of non-alphanumerics into one '-', trim '-' at both ends."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
