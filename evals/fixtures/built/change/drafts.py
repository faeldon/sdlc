"""Saved drafts, kept in memory."""

DRAFTS: dict[str, str] = {}


def save(title: str, text: str) -> None:
    DRAFTS[title] = text


def reopen(title: str) -> str | None:
    return DRAFTS.get(title)


def titles() -> list[str]:
    return sorted(DRAFTS)
