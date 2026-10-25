# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""This repo's evidence for `/sdlc:retro`: reported bugs per release window, as counts.

Named in `.sdlc/config.toml` under `retro.evidence`, so only `sdlc.py retro` in this repo runs it:
a host's cached copy of the plugin carries the file, but no host's config names it. Triage labels a
reported bug `bug`, plus an area (`area: setup`, `area: new`, `area: close`) for O1 or `lost-work`
for O2; a change's own tracking issue carries `sdlc` and is never counted. It asks GitHub for
labels, dates and state only, so no title, body or author can reach the output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

COUNTED = {
    "setup": "area: setup",
    "new": "area: new",
    "close": "area: close",
    "lost-work": "lost-work",
}


def _when(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def tag_times(root: Path) -> list[tuple[str, datetime]]:
    """Each `v*` tag and when it was made, oldest first."""
    out = subprocess.run(
        ["git", "for-each-ref", "refs/tags/v*", "--sort=creatordate",
         "--format=%(refname:short) %(creatordate:iso-strict)"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return [(name, _when(stamp)) for name, stamp in (row.split(" ", 1) for row in out.splitlines())]


def bug_issues(root: Path) -> list[dict]:
    """Every issue labelled `bug`, open or closed: labels, creation time and state, nothing else."""
    out = subprocess.run(
        ["gh", "issue", "list", "--state", "all", "--label", "bug", "--limit", "1000",
         "--json", "labels,createdAt,state"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return json.loads(out)


def count(issues: list[dict], tags: list[tuple[str, datetime]]) -> list[dict]:
    """One row per release window: each tag closes the window of issues created since the tag
    before it, and `unreleased` holds the rest. Issues carrying `sdlc` are changes, not reports."""
    rows = [
        {"window": name, "reported": 0, "open": 0, **dict.fromkeys(COUNTED, 0)} for name, _ in tags
    ]
    rows.append({"window": "unreleased", "reported": 0, "open": 0, **dict.fromkeys(COUNTED, 0)})
    for issue in issues:
        labels = {label["name"] for label in issue.get("labels", [])}
        if "sdlc" in labels:
            continue
        created = _when(issue["createdAt"])
        at = next((i for i, (_, made) in enumerate(tags) if created <= made), len(tags))
        row = rows[at]
        row["reported"] += 1
        row["open"] += issue.get("state") == "OPEN"
        for key, label in COUNTED.items():
            row[key] += label in labels
    return rows


def render(rows: list[dict]) -> str:
    head = "Reported bugs (issues labelled bug, not sdlc) by release window:"
    keys = ["reported", "open", *COUNTED]
    lines = [f"  {r['window']:<12} " + " ".join(f"{k}={r[k]}" for k in keys) for r in rows]
    return "\n".join([head, *lines])


def main() -> int:
    root = Path.cwd()
    try:
        rows = count(bug_issues(root), tag_times(root))
    except (subprocess.CalledProcessError, OSError, ValueError) as e:
        detail = getattr(e, "stderr", "") or str(e)
        print(f"evidence: {detail.strip()}", file=sys.stderr)
        return 1
    print(render(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
