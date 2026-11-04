"""The host's own command as a tracker: for one the plugin can't know about.

`archive.command` archives a landed change's folder and prints where it put it. It numbers
nothing and has no live view: the change is mirrored once, at close.

Loaded by path from `sdlc.py` (`tracker()`), only when `archive.target = "command"`.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path


def _sh(command: str) -> list[str]:
    """A copy of `sdlc.py`'s `_sh()`, since a tracker never imports it, pinned to it by a test:
    `archive.command` through `sh -c`, `/bin/sh` or on Windows Git for Windows' `sh`, never
    `cmd.exe`. Raises OSError when Windows has none."""
    if os.name != "nt":
        return ["/bin/sh", "-c", command]
    found = shutil.which("sh")
    if found is None:
        raise OSError("no sh on PATH: install Git for Windows, whose sh runs a host's commands")
    return [found, "-c", command]


class Tracker:
    numbers = False

    def __init__(self, home: Path, cfg: dict) -> None:
        self.home = home
        self.cfg = cfg

    def unavailable(self) -> str | None:
        return (
            None if self.cfg["archive"]["command"] else "archive.target is command, but no command"
        )

    def readiness(self) -> list[tuple[str, str, str]]:
        return []

    def lookup(self, field: str) -> tuple[list[str] | None, str | None]:
        return None, "the host's command has no lookups"

    def sync(self, change: dict) -> dict:
        return {"nothing": "the host's command archives at close only"}

    def archive(self, change: dict) -> tuple[str | None, str | None]:
        """(where, None) when the host's command exits 0 and prints where it put the change."""
        command = self.cfg["archive"]["command"].format(
            dir=shlex.quote(str(change["folder"])),
            id=change["id"],
            slug=change["slug"],
            sha=change["sha"],
        )
        try:
            ran = subprocess.run(
                _sh(command), cwd=self.home, capture_output=True, encoding="utf-8", errors="replace"
            )
        except OSError as e:
            return None, f"archive.command didn't run: {e}"
        lines = [ln.strip() for ln in ran.stdout.splitlines() if ln.strip()]
        if ran.returncode != 0 or not lines:
            why = ran.stderr.strip() or "it printed nowhere"
            return None, f"archive.command exited {ran.returncode}: {why}"
        return lines[-1], None


def make(home: Path, cfg: dict) -> Tracker:
    return Tracker(home, cfg)
