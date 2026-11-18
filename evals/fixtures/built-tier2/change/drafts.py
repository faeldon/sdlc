"""Saved drafts, kept in memory."""

DRAFTS: dict[str, str] = {}


def save(title: str, text: str) -> None:
    DRAFTS[title] = text


def rename(old: str, new: str) -> bool:
    """Move a saved draft to a new title; False when `old` was never saved or `new` is taken."""
    if old not in DRAFTS or new in DRAFTS:
        return False
    DRAFTS[new] = DRAFTS.pop(old)
    return True


def titles() -> list[str]:
    return sorted(DRAFTS)
