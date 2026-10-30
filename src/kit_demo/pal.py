def is_palindrome(s: str) -> bool:
    t = [c.lower() for c in s if c.isalnum()]
    return t == t[::-1]
