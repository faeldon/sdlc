"""CI's own supply chain (221): every action a workflow runs is pinned to a commit, never to a tag
or branch, which its owner can move to other code that would then run with this repo's token."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)(.*)$")
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")
VERSION = re.compile(r"^\s+#\s*v\d+(\.\d+)*\s*$")


def workflow_files(folder: Path) -> list[Path]:
    """Every workflow GitHub runs from `folder`: it reads both `.yml` and `.yaml`."""
    return sorted(p for p in folder.iterdir() if p.suffix in (".yml", ".yaml"))


def unpinned(text: str) -> list[str]:
    """Each `uses:` line in a workflow's `text` that names no full commit SHA, or no trailing
    `# v<version>` comment saying which release that commit is. A local action (`./...`) runs
    the repo's own code, so it is never one."""
    found = []
    for line in text.splitlines():
        match = USES.match(line)
        if not match or match.group(1).startswith("./"):
            continue
        if not PINNED.match(match.group(1)) or not VERSION.match(match.group(2)):
            found.append(line.strip())
    return found


def test_the_check_refuses_a_tag_or_branch_pin() -> None:
    sha = "11d5960a326750d5838078e36cf38b85af677262"
    text = (
        "steps:\n"
        "  - uses: actions/checkout@v4\n"
        "  - uses: actions/checkout@main\n"
        "  - uses: actions/checkout@11d5960\n"
        f"  - uses: actions/checkout@{sha}\n"
        f"  - uses: actions/checkout@{sha} # v4.4.0\n"
        "  - uses: ./.github/actions/local\n"
    )
    assert unpinned(text) == [
        "- uses: actions/checkout@v4",
        "- uses: actions/checkout@main",
        "- uses: actions/checkout@11d5960",
        f"- uses: actions/checkout@{sha}",
    ]


def test_a_yaml_workflow_is_read_as_well(tmp_path: Path) -> None:
    for name in ("a.yml", "b.yaml", "notes.md"):
        (tmp_path / name).write_text("", encoding="utf-8", newline="\n")
    assert [p.name for p in workflow_files(tmp_path)] == ["a.yml", "b.yaml"]


def test_every_action_is_pinned_to_a_commit() -> None:
    workflows = workflow_files(WORKFLOWS)
    assert workflows
    found = {p.name: unpinned(p.read_text(encoding="utf-8")) for p in workflows}
    assert all(not lines for lines in found.values()), found
