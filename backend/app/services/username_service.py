import re
import unicodedata


USERNAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_username(value: str | None) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", str(value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    username = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return username[:30].rstrip("-")


def validate_username(value: str | None) -> str:
    username = normalize_username(value)
    if len(username) < 3:
        raise ValueError("Username must contain at least 3 letters or numbers")
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username can only contain letters, numbers, and hyphens")
    return username


def make_unique_username(base_value: str | None, used_usernames: set[str]) -> str:
    base = normalize_username(base_value) or "rebloom-user"
    base = base[:30].rstrip("-")
    candidate = base
    suffix = 2

    while candidate in used_usernames:
        suffix_text = f"-{suffix}"
        candidate = f"{base[:30 - len(suffix_text)].rstrip('-')}{suffix_text}"
        suffix += 1

    used_usernames.add(candidate)
    return candidate
