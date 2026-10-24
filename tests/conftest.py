"""What every test shares."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def git_identity(monkeypatch) -> None:
    """`close` commits on main, so the git it runs needs an author, as a host's git has one."""
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "t")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "t@t")
