"""196 (bug 2026-11-20-17): a read that prints Markdown keeps its `## ` lines as its output, so
it owes no `exit:`; the section still ends at a heading outside any command's output, and a read
that printed nothing still owes its exit."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "factory_evidence_headings", ROOT / "plugins" / "factory" / "scripts" / "factory.py"
)
factory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(factory)

# 189's report: a read whose output opens with a heading and holds another, then more commands.
REPORT = """\
Built.

## Evidence

$ uv run --quiet --script scripts/sdlc.py retro --report > /tmp/rep.md
exit: 0

$ sed -n '/^## Insights/,/^## Speed/p' /tmp/rep.md
## Insights

Not answered: this report was written without the retrospective's insights.

## Speed

$ git status --porcelain
exit: 0
"""


@pytest.mark.portable
def test_a_read_printing_headings_owes_no_exit() -> None:
    assert factory.read_evidence(REPORT, "r") == []


@pytest.mark.portable
def test_the_commands_after_a_read_printing_headings_are_still_checked() -> None:
    text = REPORT.replace("$ git status --porcelain\nexit: 0\n", "$ ./check.sh\n1 passed\n")
    assert factory.read_evidence(text, "r") == ["r: `./check.sh` has no `exit:` line"]


@pytest.mark.portable
def test_a_heading_after_an_exit_ends_the_section() -> None:
    text = "## Evidence\n\n$ ./check.sh\nexit: 0\n\n## Notes\n\n$ ./later.sh\n"
    assert factory.read_evidence(text, "r") == []


@pytest.mark.portable
def test_a_silent_read_before_the_next_section_still_owes_its_exit() -> None:
    text = "## Evidence\n\n$ cmp a b\n\n## Notes\n\nFine.\n"
    assert factory.read_evidence(text, "r") == ["r: `cmp a b` has no `exit:` line"]
