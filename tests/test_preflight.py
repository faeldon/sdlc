"""`preflight`, everything ship's Step 0 looks up about a change in one read-only call, and its
`--question`, ship's WAIT question with each clause decided by code, not the skill's prose."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_preflight", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

NITS = """\
# Inbox

> The note.

## [2026-10-04-1] [nit] A registry that isn't UTF-8 crashes status

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: med
Raised by: 003-test-lifetimes (correctness)

## [2026-10-20-1] [nit] An idiom

Theme: style
Paths: docs/
Cost: M
Value: low
Raised by: 009-drift-message (cost)
"""

INTENT = """\
---
id: 001
slug: reopen-drafts
tier: 2
impact:
stage: build
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
closes: [12, 15]
---

# 001 — Reopen drafts
"""

CHECKS = """\
# Acceptance checks

> The note.

## The list reopens a draft

```sh
true
```
"""

FULL = (
    "Commit this, with the context update shown, the nits shown recorded in .sdlc/work/inbox.md, "
    "closing #N and #M when it lands and splitting #K off as a seed, and "
    ".sdlc/work/NNN-<slug>/ stamped shipped, then update its issue? "
    "(yes / fix a finding first / edit the message)"
)


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


@pytest.fixture
def change(tmp_path: Path) -> tuple[Path, Path]:
    """A repo on a change's branch: notes with an undone item, a nit its diff touches, two issues
    on `closes:`, an acceptance check and a context doc above a changed path."""
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text(NITS, encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "AGENTS.md").write_text("the scripts\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", "001-reopen-drafts")
    folder = root / ".sdlc" / "work" / "001-reopen-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    (folder / "notes.md").write_text("# Notes\n\n- [ ] the empty list\n", encoding="utf-8")
    (folder / "checks.md").write_text(CHECKS, encoding="utf-8")
    (root / "scripts" / "sdlc.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "work")
    return root, folder


def _json(capsys, run) -> tuple[int, dict]:
    code = run()
    return code, json.loads(capsys.readouterr().out)


def test_preflight_parts_equal_the_single_commands(change, capsys) -> None:
    root, _ = change
    code, out = _json(capsys, lambda: sdlc.cmd_preflight(root, "001"))
    assert code == 0, out["problems"]
    assert (out["change"], out["tier"], out["stage"]) == ("001-reopen-drafts", 2, "build")
    assert out["folder"] == ".sdlc/work/001-reopen-drafts"
    singles = {
        "undone": lambda: sdlc.cmd_undone(root, "001"),
        "nits": lambda: sdlc.cmd_nits(root, None, "001"),
        "closes": lambda: sdlc.cmd_closes(root, "001"),
        "checks": lambda: sdlc.cmd_checks(root, "001"),
        "context": lambda: sdlc.cmd_context(root),
    }
    for part, run in singles.items():
        assert out[part] == _json(capsys, run)[1], part
    # The fixture puts something in every part, so equal is never equally empty.
    assert [i["text"] for i in out["undone"]["items"]] == ["the empty list"]
    assert [n["id"] for n in out["nits"]["nits"]] == ["2026-10-04-1"]
    assert [c["number"] for c in out["closes"]["closes"]] == [12, 15]
    assert [c["name"] for c in out["checks"]["checks"]] == ["The list reopens a draft"]
    assert "scripts/AGENTS.md" in [d["path"] for d in out["context"]["docs"]]


def test_preflight_writes_nothing(change, capsys) -> None:
    root, folder = change
    before = (_git(root, "status", "--porcelain"), sorted(p.name for p in folder.iterdir()))
    sdlc.cmd_preflight(root, "001")
    capsys.readouterr()
    after = (_git(root, "status", "--porcelain"), sorted(p.name for p in folder.iterdir()))
    assert before == after


def test_preflight_exits_1_on_a_part_s_problems_and_prints_every_part(change, capsys) -> None:
    root, folder = change
    (folder / "checks.md").write_text("# Acceptance checks\n\n```sh\ntrue\n```\n")
    code, out = _json(capsys, lambda: sdlc.cmd_preflight(root, "001"))
    assert code == 1
    assert out["problems"] and all(p.startswith("checks: ") for p in out["problems"])
    assert {"undone", "nits", "closes", "checks", "context"} <= out.keys()


def test_preflight_refuses_an_unknown_id(change, capsys) -> None:
    root, _ = change
    assert sdlc.cmd_preflight(root, "009") == 1
    assert capsys.readouterr().out == ""


def _ask(**kw) -> tuple[str | None, str | None]:
    args = {"folder": ".sdlc/work/001-reopen-drafts", "closes": [], "target": "github",
            "context": False, "nits": False, "closing": [], "split": [],
            "register": ".sdlc/work/inbox.md"}  # fmt: skip
    return sdlc.ship_question(**(args | kw))


def test_question_with_every_clause_matches_ship_s_example() -> None:
    """The skill's example sentence, every clause in, is what the script renders: N, M and K
    stand in for the numbers, and the folder for the change's."""
    question, why = _ask(folder=".sdlc/work/NNN-<slug>", closes=[1, 2, 3], context=True,
                         nits=True, closing=[1, 2], split=[3])  # fmt: skip
    assert why is None
    assert question == FULL.replace("#N", "#1").replace("#M", "#2").replace("#K", "#3")
    skill = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    assert FULL in " ".join(skill.split()), "the skill shows the same sentence"


SHIPPED = ".sdlc/work/001-reopen-drafts/ stamped shipped"


@pytest.mark.parametrize(
    "kw, expected",
    [
        ({}, f"Commit this, with {SHIPPED}, then update its issue?"),
        ({"target": "none"}, f"Commit this, with {SHIPPED}? (yes"),
        ({"context": True}, f"Commit this, with the context update shown, and {SHIPPED}, then"),
        ({"nits": True}, "Commit this, the nits shown recorded in .sdlc/work/inbox.md, and .sdlc"),
        ({"closes": [4], "closing": [4]}, "Commit this, closing #4 when it lands, and .sdlc"),
        ({"closes": [4, 5], "closing": [5, 4]}, "closing #4 and #5 when it lands, and"),
        ({"closes": [4, 5, 6], "closing": [4, 5, 6]}, "closing #4, #5 and #6 when it lands, and"),
        ({"closes": [4], "split": [4]}, "Commit this, splitting #4 off as a seed, and"),
        ({"closes": [4, 5], "split": [4, 5]}, "splitting #4 and #5 off as seeds, and"),
        (
            {"closes": [4, 5], "closing": [4], "split": [5]},
            "closing #4 when it lands and splitting #5 off as a seed, and",
        ),
    ],
)
def test_question_clause(kw, expected) -> None:
    question, why = _ask(**kw)
    assert why is None and question.startswith("Commit this") and expected in question
    if "context" not in kw:
        assert "context update" not in question
    if "nits" not in kw:
        assert "nits shown" not in question
    if not kw.get("closing"):
        assert "closing" not in question
    if not kw.get("split"):
        assert "splitting" not in question
    assert question.endswith("? (yes / fix a finding first / edit the message)")


@pytest.mark.parametrize(
    "kw, why",
    [
        ({"closes": [4], "closing": [4, 9]}, "#9 not on the change's closes: line"),
        ({"closes": [4], "closing": [4], "split": [4]}, "#4 given to both"),
        ({"closes": [4, 5], "closing": [4]}, "#5 on closes: but given to neither"),
    ],
    ids=["not-on-closes", "given-to-both", "left-out"],
)
def test_question_refuses_issues_that_don_t_partition_closes(kw, why) -> None:
    question, said = _ask(**kw)
    assert question is None and why in said


def test_question_through_the_command(change, capsys) -> None:
    root, _ = change
    assert sdlc.cmd_ship_question(root, "001", True, False, [12], [15]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed == (
        "Commit this, with the context update shown, closing #12 when it lands and splitting "
        "#15 off as a seed, and .sdlc/work/001-reopen-drafts/ stamped shipped? "
        "(yes / fix a finding first / edit the message)"
    ), "no tracker configured, so no issue update"
    assert sdlc.cmd_ship_question(root, "001", False, False, [12], []) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "#15 on closes: but given to neither" in captured.err


def test_preflight_and_nits_are_allowed_without_a_prompt() -> None:
    assert {"preflight", "nits"} <= set(sdlc.READ_ONLY)
