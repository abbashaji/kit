def caesar(text: str, shift: int) -> str:
    """Shift ASCII letters by `shift` (any int), preserving case.

    Non-letters are left unchanged. caesar(caesar(t, k), -k) == t.
    """
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        else:
            out.append(ch)
    return "".join(out)
