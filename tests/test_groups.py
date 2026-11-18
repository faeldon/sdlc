"""`groups`: a batch of changes for `/sdlc:intent`, read against the register and the open
changes and put in creation order, before one question approves them all. It writes nothing; every
number still comes from `new`, and `depends_on` only from a change already created."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_groups", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

INBOX = """\
# Inbox

## [2026-11-01-1] [idea] Keep drafts

Why.
Issue: #12, #15

## [2026-11-01-2] [bug] Saving twice makes two drafts

What happens.

Severity: low

## [2026-11-01-3] [nit] A stray print

Theme: style
Paths: scripts/
Cost: S
Value: low
Raised by: 001-start (cost)

## [2026-11-01-4] [seed] Reopen a draft

Why.

## [2026-11-01-5] [building] Export drafts

Building in .sdlc/work/007-export-drafts/.
"""

INTENT = """\
---
id: {id}
slug: {slug}
tier: 1
stage: {stage}
created: 2026-11-01
updated: 2026-11-01
idea: {idea}
depends_on:
---

# {id} — {slug}
"""


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text(INBOX, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _open(root: Path, nid: str, slug: str, idea: str = "", stage: str = "build") -> None:
    d = root / ".sdlc" / "work" / f"{nid}-{slug}"
    d.mkdir()
    text = INTENT.format(id=nid, slug=slug, stage=stage, idea=idea)
    (d / "intent.md").write_text(text, encoding="utf-8")


def _groups(root: Path, capsys, *texts: str) -> tuple[int, dict]:
    code = sdlc.cmd_groups(root, list(texts))
    return code, json.loads(capsys.readouterr().out)


def test_a_group_reads_its_ids_slug_tier_and_after(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    code, out = _groups(
        root,
        capsys,
        "2026-11-01-1 2026-11-01-2 2026-11-01-3 as Keep-Drafts tier 1",
        "2026-11-01-4 as reopen tier 2 after keep-drafts",
    )
    assert code == 0 and out["refusals"] == []
    first, second = out["groups"]
    assert first["slug"] == "keep-drafts" and first["tier"] == 1 and first["after"] is None
    assert [(i["id"], i["kind"]) for i in first["ids"]] == [
        ("2026-11-01-1", "idea"),
        ("2026-11-01-2", "bug"),
        ("2026-11-01-3", "nit"),
    ]
    assert first["ids"][0]["issues"] == [12, 15]
    assert first["ids"][1]["title"] == "Saving twice makes two drafts"
    # An older `[seed]` tag is an idea.
    assert second["ids"][0]["kind"] == "idea" and second["after"] == "keep-drafts"
    assert second["created"] is None and second["depends_on"] is None


def test_every_refusal_names_its_group_and_the_batch_exits_1(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _open(root, "008", "taken", idea="2026-11-01-2")
    code, out = _groups(
        root,
        capsys,
        "2026-01-01-9 as unknown tier 1",
        "2026-11-01-1 as twice tier 1",
        "2026-11-01-1 as twice-again tier 1",
        "2026-11-01-2 as claimed tier 1",
        "2026-11-01-5 as building tier 1",
        "as no-ids tier 1",
        "2026-11-01-3 tier 1",
        "2026-11-01-4 as tier-zero tier 0",
        "2026-11-01-4 as dup tier 2 extra",
        "2026-11-01-4 as dup tier 2 after nowhere",
    )
    assert code == 1
    joined = "\n".join(out["refusals"])
    for expected in (
        "unknown: 2026-01-01-9 isn't in the register",
        "twice-again: 2026-11-01-1 is in twice too",
        "claimed: 2026-11-01-2 is taken by 008-taken",
        "building: 2026-11-01-5 is tagged [building]",
        "no-ids: names no register id",
        "group 7: has no `as <slug>`",
        "tier-zero: tier must be 1 or 2, not 0",
        "dup: can't read 'extra'",
        "dup: two groups take this slug",
        "dup: `after nowhere` names no group of this batch",
    ):
        assert expected in joined, expected


def test_order_follows_after_and_otherwise_the_given_order(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    # A chain written backwards: c after b after a.
    _, out = _groups(
        root,
        capsys,
        "2026-11-01-1 as c tier 1 after b",
        "2026-11-01-2 as b tier 1 after a",
        "2026-11-01-3 as a tier 1",
    )
    assert out["order"] == ["a", "b", "c"]
    # A fan-out: two after one, keeping their given order; a group with no `after` keeps its place.
    _, out = _groups(
        root,
        capsys,
        "2026-11-01-1 as x tier 2 after root",
        "2026-11-01-2 as free tier 1",
        "2026-11-01-3 as y tier 2 after root",
        "2026-11-01-4 as root tier 1",
    )
    assert out["order"] == ["free", "root", "x", "y"]


def test_a_cycle_is_refused_and_leaves_its_groups_unordered(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    code, out = _groups(
        root,
        capsys,
        "2026-11-01-1 as a tier 1 after b",
        "2026-11-01-2 as b tier 1 after a",
        "2026-11-01-3 as c tier 1",
    )
    assert code == 1
    assert out["order"] == ["c"]
    assert "a, b: their `after`s make a cycle" in out["refusals"]


def test_depends_on_is_the_number_new_gave_never_a_guess(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    batch = ("2026-11-01-1 as first tier 1", "2026-11-01-4 as second tier 2 after first")
    _, out = _groups(root, capsys, *batch)
    assert out["groups"][1]["depends_on"] is None
    # `new` made the first: read again, the second waits on that number.
    _open(root, "011", "first", idea="2026-11-01-1", stage="plan")
    code, out = _groups(root, capsys, *batch)
    assert code == 0
    assert out["groups"][0]["created"] == "011-first"
    assert out["groups"][1]["depends_on"] == "011"


def test_a_rerun_skips_what_it_created_without_refusing_its_ids(tmp_path: Path, capsys) -> None:
    """A batch that stopped partway is run again as it was: the change already made holds its
    group's slug and ids, which is `created`, not a claim by another change."""
    root = _repo(tmp_path)
    _open(root, "011", "first", idea="[2026-11-01-1, 2026-11-01-2]", stage="plan")
    code, out = _groups(
        root, capsys, "2026-11-01-1 2026-11-01-2 as first tier 1", "2026-11-01-4 as next tier 1"
    )
    assert code == 0, out["refusals"]
    assert [g["created"] for g in out["groups"]] == ["011-first", None]


def test_a_rerun_drafts_a_change_whose_intent_was_never_written(tmp_path: Path, capsys) -> None:
    """A run stopped between `new` and the intent leaves the scaffold: `created`, not `drafted`,
    so the rerun writes that change's intent instead of skipping it."""
    root = _repo(tmp_path)
    _open(root, "011", "first", stage="plan")
    intent = root / ".sdlc" / "work" / "011-first" / "intent.md"
    intent.write_text(
        intent.read_text() + "\n<What's wrong.>\n\n<What's true.>\n", encoding="utf-8"
    )
    _, out = _groups(root, capsys, "2026-11-01-1 as first tier 1")
    assert out["groups"][0]["created"] == "011-first"
    assert out["groups"][0]["drafted"] is False
    _open(root, "012", "second", idea="2026-11-01-4", stage="plan")
    _, out = _groups(root, capsys, "2026-11-01-4 as second tier 1")
    assert out["groups"][0]["drafted"] is True


def test_a_slug_a_shipped_or_dropped_folder_holds_is_refused(tmp_path: Path, capsys) -> None:
    """`new` refuses a slug any folder on disk holds: one shipped and waiting for close is not a
    change this batch made, and never `created` or a `depends_on`."""
    root = _repo(tmp_path)
    _open(root, "009", "done", stage="shipped")
    _open(root, "010", "gone", stage="dropped")
    code, out = _groups(
        root,
        capsys,
        "2026-11-01-1 as done tier 1",
        "2026-11-01-2 as gone tier 1",
        "2026-11-01-4 as next tier 1 after done",
    )
    assert code == 1
    assert "done: taken by 009-done (shipped)" in out["refusals"]
    assert "gone: taken by 010-gone (dropped)" in out["refusals"]
    assert [g["created"] for g in out["groups"]] == [None, None, None]
    assert out["groups"][2]["depends_on"] is None


def test_a_malformed_issue_line_is_refused_not_dropped(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    inbox = root / ".sdlc" / "work" / "inbox.md"
    inbox.write_text(inbox.read_text().replace("Issue: #12, #15", "Issue: 12"), encoding="utf-8")
    code, out = _groups(root, capsys, "2026-11-01-1 as first tier 1")
    assert code == 1
    assert "first: 2026-11-01-1's Issue: line isn't #N, …" in out["refusals"]


def test_a_shipped_change_claims_its_seed_until_it_closes(tmp_path: Path, capsys) -> None:
    """134 R10: the seed stays in the register until close retires it, so a shipped change still
    holds it, and no batch takes it meanwhile."""
    root = _repo(tmp_path)
    _open(root, "009", "done", idea="2026-11-01-4", stage="shipped")
    code, out = _groups(root, capsys, "2026-11-01-4 as again tier 1")
    assert code == 1 and out["refusals"] == ["again: 2026-11-01-4 is taken by 009-done"]


def test_groups_writes_nothing_and_needs_no_prompt(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _groups(root, capsys, "2026-11-01-1 as first tier 1")
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True
    )
    assert status.stdout == ""
    assert "groups" in sdlc.READ_ONLY


def test_an_untagged_seed_an_open_change_names_is_taken(tmp_path: Path, capsys) -> None:
    """100 R5: nothing tags a seed now; the open change's `idea:` alone holds it, and `groups`
    names that change."""
    root = _repo(tmp_path)
    _open(root, "008", "keep", idea="2026-11-01-1")
    code, out = _groups(root, capsys, "2026-11-01-1 as again tier 1")
    assert code == 1 and out["refusals"] == ["again: 2026-11-01-1 is taken by 008-keep"]
