"""Saved drafts, kept in memory."""

DRAFTS: dict[str, str] = {}


def save(title: str, text: str) -> None:
    DRAFTS[title] = text


def titles() -> list[str]:
    return sorted(DRAFTS)
