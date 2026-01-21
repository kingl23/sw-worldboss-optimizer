from __future__ import annotations


def _clean_name(value: str | None) -> str:
    return str(value).strip() if value is not None else ""


def normalize_deck_slots(values: list[str | None], max_slots: int = 3) -> list[str]:
    cleaned = [_clean_name(value) for value in values]
    cleaned = cleaned[:max_slots]
    while len(cleaned) < max_slots:
        cleaned.append("")
    return cleaned


def format_deck_slots(
    values: list[str | None],
    placeholder: str = "-",
    max_slots: int = 3,
) -> list[str]:
    slots = normalize_deck_slots(values, max_slots=max_slots)
    return [slot if slot else placeholder for slot in slots]


def format_deck_label(
    values: list[str | None],
    placeholder: str = "-",
    max_slots: int = 3,
    separator: str = " / ",
) -> str:
    return separator.join(format_deck_slots(values, placeholder=placeholder, max_slots=max_slots))


def make_deck_key(leader: str | None, second: str | None, third: str | None) -> str:
    leader = _clean_name(leader)
    if not leader:
        return ""
    rest = sorted([_clean_name(value) for value in [second, third] if _clean_name(value)])
    slots = normalize_deck_slots([leader] + rest, max_slots=3)
    return "|".join(slots)


def split_deck_key(deck_key: str, max_slots: int = 3) -> list[str]:
    parts = deck_key.split("|") if deck_key else []
    return normalize_deck_slots(parts, max_slots=max_slots)
