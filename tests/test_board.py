"""The dashboard: `sdlc.py board`, its state, its three routes and the page (075).

The board reads every open change as `status` does, and a factory run's files with copies of
`factory.py`'s parsing, pinned here. It writes nothing, and serves only a change's own files.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_board_under_test", ROOT / "scripts" / "sdlc.py")
factory = _load("factory_board_pins", ROOT / "plugins" / "factory" / "scripts" / "factory.py")
board = sdlc._load_board()

INTENT = """\
---
id: {id}
slug: {slug}
tier: {tier}
stage: {stage}
created: 2026-11-17
updated: 2026-11-17
idea:
depends_on: {depends}
---

# {id} — {title}

## Problem

Written.

## Open questions

- {question}
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _change(root: Path, name: str, tier: int, stage: str, title: str, depends: str = "") -> Path:
    ident, slug = name.split("-", 1)
    folder = root / ".sdlc" / "work" / name
    _write(folder / "intent.md", INTENT.format(
        id=ident, slug=slug, tier=tier, stage=stage, title=title, depends=depends,
        question="Which drafts count?",
    ))  # fmt: skip
    return folder


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo on `main` with four open changes and a shipped one: a Tier 1 and a Tier 2 built by
    hand, a factory run ready to ship, and a factory run with a reply that isn't a review."""
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "README.md", "a repo\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")

    one = _change(root, "001-reopen-drafts", 1, "plan", "Reopen drafts")
    _write(one / "notes.md", "# Notes\n\n- [ ] say why a draft closes\n")

    two = _change(root, "002-draft-history", 2, "design", "Draft history", "[1]")
    _write(two / "spec.md", "# 002 — spec\n\n<Numbered requirements.>\n<Design.>\n<Contracts.>\n")
    _write(two / "checks.md", "# Checks\n\n## lists drafts\n\n```sh\ntrue\n```\n")

    three = _change(root, "003-draft-export", 2, "test", "Draft export")
    _write(three / "runs" / "builder.sessions", "s-1\n")
    _write(three / "build" / "round-1.md", "Built.\n")
    _write(three / "build" / "round-2.md", "Reworked.\n")
    _write(three / "reviews" / "round-1" / "code.md",
           "VERDICT: CHANGES\n- CHANGE: src/a.py:1: a\n- CHANGE: src/a.py:2: b\n")  # fmt: skip
    _write(three / "reviews" / "round-1" / "test.md", "VERDICT: PASS\n")
    _write(three / "reviews" / "round-1" / "verified.md",
           "- KEPT: code: src/a.py:1: a\n- DROPPED: code: src/a.py:2: b — not so\n")  # fmt: skip
    _write(three / "reviews" / "round-2" / "code.md", "VERDICT: PASS\n")
    _write(three / "decision.md", "DECISION: READY\n\nIt does what the spec says.\n")
    _write(three / "decisions.md", "# Decisions\n\n"
           "- [x] D1 (code round 1, default): CSV or JSON → decided: CSV\n"
           "- [ ] D2 (builder round 2, default): keep the old flag\n")  # fmt: skip

    four = _change(root, "004-draft-purge", 1, "build", "Draft purge")
    _write(four / "runs" / "builder.sessions", "s-2\n")
    _write(four / "reviews" / "round-1" / "code.md", "Looks fine to me.\n")
    _write(four / "decisions.md", "- [ ] D1 (code round 1, blocking): purge after 30 or 90 days?\n")

    _change(root, "005-old-thing", 1, "shipped", "Old thing")
    return root


def _cards(root: Path) -> dict[str, dict]:
    return {c["change"]: c for c in board.state(root)["changes"]}


@pytest.mark.portable
def test_every_open_change_is_on_the_board_with_its_next_step(repo) -> None:
    cards = _cards(repo)
    assert list(cards) == ["001-reopen-drafts", "002-draft-history", "003-draft-export",
                           "004-draft-purge"], "a shipped change is not open"  # fmt: skip
    one, two = cards["001-reopen-drafts"], cards["002-draft-history"]
    assert (one["tier"], one["stage"], one["mode"], one["column"]) == (1, "plan", "manual", "plan")
    assert one["next"] == "plan mode, then build it"
    assert one["title"] == "001 — Reopen drafts" and one["open_questions"] == 1
    assert one["undone"] == ["say why a draft closes"] and one["issue"] is None
    assert one["files"] == ["intent.md", "notes.md"] and one["problems"] == []
    assert (two["column"], two["next"]) == ("design", "plan mode, then build it")
    assert two["depends_on"] == ["001"] and two["unfilled"] == ["spec.md"] and two["checks"] == 1
    assert "rounds" not in two, "a change built by hand has no factory fields"
    assert "progress" not in one and "progress" not in two, "nor a step track"


@pytest.mark.portable
def test_a_factory_run_shows_its_rounds_decision_and_ledger(repo) -> None:
    three = _cards(repo)["003-draft-export"]
    assert (three["mode"], three["column"], three["decision"]) == ("factory", "ready", "READY")
    assert three["next"].startswith("/sdlc:ship")
    first, second = three["rounds"]
    assert first["reviews"] == {"code": {"verdict": "CHANGES", "changes": 2},
                                "test": {"verdict": "PASS", "changes": 0}}  # fmt: skip
    assert first["verified"] == {"kept": 1, "dropped": 1} and first["built"]
    assert second["reviews"] == {"code": {"verdict": "PASS", "changes": 0}}
    assert second["verified"] is None and three["built"] == [1, 2]
    assert three["pending"] == [] and [d["id"] for d in three["assumed"]] == ["D2"]
    assert three["cost"] is None, "no runs/costs.jsonl: no figure, never a guess"


@pytest.mark.portable
def test_a_superseded_default_is_not_assumed_on_the_board(repo) -> None:
    """105 R8: `decisions` ticks a superseded default, so the board's copy of the ledger pattern,
    unedited, shows only the default that replaced it as assumed."""
    _write(repo / ".sdlc" / "work" / "003-draft-export" / "decisions.md", "# Decisions\n\n"
           "- [x] D1 (code round 1, default): CSV or JSON → decided: CSV\n"
           "- [x] D2 (builder round 1, default): no badge on a card → superseded by D3\n"
           "- [ ] D3 (builder round 2, default): keep was ESCALATE on a card\n")  # fmt: skip
    three = _cards(repo)["003-draft-export"]
    assert [d["id"] for d in three["assumed"]] == ["D3"] and three["pending"] == []


@pytest.mark.portable
def test_a_blocking_decision_or_an_unreadable_reply_needs_the_person(repo) -> None:
    four = _cards(repo)["004-draft-purge"]
    assert four["column"] == "needs-you"
    assert [d["text"] for d in four["pending"]] == ["purge after 30 or 90 days?"]
    assert any("round-1/code.md" in p for p in four["problems"])
    assert four["next"] == (
        "decide D1 in the session running /sdlc-factory:build 004 (rerun it if that session "
        "ended), and fix what its problems name"
    ), "the problem, as its column (098), and the decision that still waits (110); 2026-11-18-27"


def _worktree(
    root: Path, name: str, tier: int, stage: str, commit=(), dirty=(), factory=False
) -> Path:
    """A change in a worktree of its own, as `new --worktree` makes one, its intent committed on
    its branch, then a commit holding `commit` and uncommitted `dirty` paths."""
    tree = root / ".claude" / "worktrees" / name
    _git(root, "worktree", "add", "-q", "-b", name, str(tree), "main")
    folder = _change(tree, name, tier, stage, name.split("-", 1)[1])
    if factory:
        _write(folder / "runs" / "builder.sessions", "s-9\n")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", f"wip {name[:3]}")
    for rel in commit:
        _write(tree / rel, "changed\n")
    if commit:
        _git(tree, "add", "-A")
        _git(tree, "commit", "-q", "-m", "build")
    for rel in dirty:
        _write(tree / rel, "edited\n")
    return folder


@pytest.mark.portable
def test_a_change_built_by_hand_moves_on_as_its_branch_and_review_do(repo) -> None:
    """Nothing moves `stage:` on a change built by hand between `plan` and `shipped` (080), so the
    board reads how far it has got from what it touched and whether ship's review has run."""
    _worktree(repo, "006-draft-tags", 1, "plan", commit=["src/tags.py"])
    _worktree(repo, "007-draft-notes", 1, "plan", commit=[".sdlc/work/inbox.md", ".sdlc/last-id"])
    _worktree(repo, "008-draft-sort", 1, "plan", dirty=["src/sort.py"])
    folder = _worktree(repo, "009-draft-share", 1, "plan", commit=["src/share.py"])
    _write(folder / "findings.md", "# Findings\n")
    _worktree(repo, "010-draft-sync", 2, "plan", commit=["src/sync.py"])
    _worktree(repo, "011-draft-lock", 1, "build", commit=["src/lock.py"], factory=True)
    cards = _cards(repo)
    seen = {n: (c["column"], c["seen"]) for n, c in cards.items() if n >= "006"}
    assert seen == {
        "006-draft-tags": ("build", "build"),
        "007-draft-notes": ("plan", None),  # only its folder, the register and the counter
        "008-draft-sort": ("build", "build"),  # uncommitted, in its own worktree
        "009-draft-share": ("test", "test"),
        "010-draft-sync": ("plan", None),  # a Tier 2 with no spec yet
        "011-draft-lock": ("build", None),  # the factory moves its own stage line
    }
    assert cards["006-draft-tags"]["next"] == "build it, then /sdlc:ship"
    assert cards["009-draft-share"]["next"] == "/sdlc:ship"
    assert cards["001-reopen-drafts"]["column"] == "plan", "no branch: nothing to read"
    assert cards["006-draft-tags"]["stage"] == "plan", (
        "the board reads its stage line, never writes it"
    )


def _main_check(root: Path, command: str) -> None:
    """`[commands] check` committed on `main`, the base branch, which the hand gate runs."""
    _write(root / ".sdlc" / "config.toml", f'[commands]\ncheck = "{command}"\n')
    _git(root, "add", ".sdlc/config.toml")
    _git(root, "commit", "-q", "-m", "gate")


def _hand_gate(tree: Path, ident: str) -> int:
    return sdlc.cmd_gate(tree, ident)


@pytest.mark.parametrize("stage", ["plan", "build"])
def test_a_green_gate_moves_a_hand_built_card_to_test_until_an_edit(repo, capsys, stage) -> None:
    """091 R8, R10: a current green record is `test`, `/sdlc:ship` next, before ship's review
    has run; an edit outside the change's folder makes it stale, and the card goes back."""
    _main_check(repo, "true")
    name = "012-draft-pins"
    folder = _worktree(repo, name, 1, stage, commit=["src/pins.py"])
    tree = sdlc.checkout_of(folder)
    card = _cards(repo)[name]
    assert (card["column"], card["gate"]) == ("build", None)
    assert _hand_gate(tree, "012") == 0
    capsys.readouterr()
    card = _cards(repo)[name]
    assert (card["column"], card["seen"], card["next"]) == ("test", "test", "/sdlc:ship")
    assert (card["gate"]["verdict"], card["gate"]["current"]) == ("PASS", True)
    assert card["stage"] == stage, "the board reads its stage line, never writes it"
    _write(tree / "src" / "pins.py", "edited again\n")
    card = _cards(repo)[name]
    assert (card["column"], card["gate"]["current"]) == ("build", False)
    assert card["next"] == "build it, then /sdlc:ship"


def test_a_red_gate_keeps_the_card_in_build_and_says_so(repo, capsys) -> None:
    """091 R9."""
    _main_check(repo, "exit 1")
    folder = _worktree(repo, "012-draft-pins", 1, "plan", commit=["src/pins.py"])
    assert _hand_gate(sdlc.checkout_of(folder), "012") == 1
    capsys.readouterr()
    card = _cards(repo)["012-draft-pins"]
    assert (card["column"], card["gate"]["verdict"], card["gate"]["current"]) == (
        "build", "FAIL", True,
    )  # fmt: skip
    assert card["next"] == "the gate is red: read build/gate.md, fix it, then sdlc.py gate 012"


@pytest.mark.portable
def test_a_factory_card_never_reads_a_hand_gate(repo) -> None:
    """091 R10: a factory run's gate is its own; a record in its folder moves nothing."""
    folder = _worktree(repo, "011-draft-lock", 1, "build", commit=["src/lock.py"], factory=True)
    _write(folder / "build" / "gate.md", "GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\n")
    card = _cards(repo)["011-draft-lock"]
    assert "gate" not in card and card["seen"] is None and card["column"] == "build"
    assert _cards(repo)["001-reopen-drafts"]["gate"] is None


@pytest.mark.portable
def test_the_gate_badge_is_built_as_text() -> None:
    """091 R10: the badge is a node of `h()`'s, only for a record that is current."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert '"gate green"' in page and '"gate red"' in page
    assert re.search(r"c\.gate && c\.gate\.current\s*\?\s*h\(", page)


@pytest.mark.portable
def test_a_shipped_change_waits_on_close_until_its_worktree_goes(served) -> None:
    root, url, _ = served
    _worktree(root, "012-draft-pins", 1, "shipped", commit=["src/pins.py"])
    card = _cards(root)["012-draft-pins"]
    assert (card["column"], card["next"]) == ("close", "/sdlc:close 012")
    assert "005-old-thing" not in _cards(root), "shipped with no worktree: closed already"
    query = urllib.parse.urlencode({"change": "012-draft-pins", "path": "intent.md"})
    assert _get(f"{url}/file?{query}")[0] == 200
    _git(
        root,
        "worktree",
        "remove",
        "--force",
        str(root / ".claude" / "worktrees" / "012-draft-pins"),
    )
    assert "012-draft-pins" not in _cards(root)
    assert _get(f"{url}/file?{query}")[0] == 404


@pytest.mark.portable
def test_the_cost_is_summed_as_the_factory_sums_it(repo) -> None:
    folder = repo / ".sdlc" / "work" / "003-draft-export"

    def row(session, role, model, ms, usd=None) -> dict:
        out = {"session": session, "role": role, "model": model, "duration_ms": ms}
        return out if usd is None else {**out, "cost_usd": usd}

    rows = [
        row("s-1", "builder", "opus", 60000, 0.5),
        row("s-1", "builder", "opus", 30000, 0.75),
        row("s-2", "code", "haiku", 1000, 0.1),
        row("s-3", "test", "haiku", 500),
    ]
    _write(folder / "runs" / "costs.jsonl", "".join(json.dumps(r) + "\n" for r in rows) + "{bad\n")
    mine, theirs = board.cost(folder), factory.run_cost(folder)
    for key in ("usd", "by_role", "by_model", "runs", "unknown"):
        assert mine[key] == theirs[key], key
    assert mine["usd"] == 0.85 and mine["duration_ms"] == 91500


# 078's round 1, as its run left it on 2026-11-17 (each long line cut at `…`): the reviewer asked
# for one change, and the verifier dropped it in other words than the reviewer's, so `verdicts`
# found the change answered no times and an answer to a change nobody asked for, and stopped.
STOP_CHANGE = (
    '.sdlc/REVIEW.md:50: The bullet says "The escapes from 047 and 050 are pinned by …" The commit'
    " history doesn't support that mapping. …"
)
STOP_DROPPED = (
    ".sdlc/REVIEW.md:50: the attribution of the two tests is wrong, so credit each to the change"
    " whose finding it pins."
)
STOP_PROBLEMS = [
    f"reviews/round-1/verified.md answers code: {STOP_CHANGE} 0 times, not once",
    f"reviews/round-1/verified.md answers code: {STOP_DROPPED}, which no review of round 1"
    " asks for",
]


def _stopped_run(root: Path, name: str = "013-draft-escapes", stage: str = "build") -> Path:
    """A factory run stopped as 078's was, after round 1's verification, with the record the
    supervisor's `verdicts --record` wrote from it:

        build/round-1.md            I added the two failure classes to `.sdlc/REVIEW.md`. …
                                    ## Evidence …
        reviews/round-1/code.md     VERDICT: CHANGES
                                    - CHANGE: .sdlc/REVIEW.md:50: The bullet says …
        reviews/round-1/verified.md - DROPPED: code: .sdlc/REVIEW.md:50: the attribution … — The
                                    attribution matches the history. …
    """
    folder = _change(root, name, 1, stage, "Review escape classes")
    _write(folder / "runs" / "builder.sessions", "s-3\n")
    _write(folder / "build" / "round-1.md", "I added the two failure classes to `.sdlc/REVIEW.md`."
           "\n\n## Evidence\n\n$ ./check.sh\n1848 passed\nexit: 0\n")  # fmt: skip
    _write(folder / "reviews" / "round-1" / "code.md",
           f"VERDICT: CHANGES\n\n- CHANGE: {STOP_CHANGE}\n\n## Notes\n\n- Fine.\n")  # fmt: skip
    _write(folder / "reviews" / "round-1" / "verified.md",
           f"- DROPPED: code: {STOP_DROPPED} — The attribution matches the history.\n")  # fmt: skip
    _write(folder / factory.STOPPED, factory.stop_text(name, "rerun", STOP_PROBLEMS))
    return folder


@pytest.mark.portable
def test_a_stopped_run_needs_the_person(repo) -> None:
    """R6: under Needs you, each problem as `verdicts` worded it, and the record's way on."""
    _stopped_run(repo)
    card = _cards(repo)["013-draft-escapes"]
    assert card["column"] == "needs-you"
    assert card["stopped"]["way"] == "rerun"
    assert card["stopped"]["problems"] == STOP_PROBLEMS
    assert card["next"] == factory.WAYS["rerun"].format(id="013")
    assert "the factory is building it" not in card["next"]
    assert card["problems"] == [], "a stop is not a file that won't read"


@pytest.mark.portable
def test_an_unreadable_stop_record_is_a_stop_as_in_status(repo) -> None:
    """R7, as 110 (2026-11-17-69) aligned it on `status`: a record that won't read is still a
    stop, whose way on is to read it, so the card and `/sdlc:status` say the same thing."""
    folder = _stopped_run(repo)
    _write(folder / factory.STOPPED, "stopped, somehow\n")
    card = _cards(repo)["013-draft-escapes"]
    assert card["stopped"] == sdlc.factory_stop(folder), "the reading status shows"
    assert card["stopped"]["next"] == "read runs/stopped.md"
    assert card["column"] == "needs-you" and card["problems"] == []
    assert card["needs"] == ["stopped: read runs/stopped.md"]
    assert card["next"] == "read runs/stopped.md"


@pytest.mark.portable
def test_the_stop_record_says_why_and_reads_as_before(tmp_path) -> None:
    """120 (2026-11-17-82): the record's body holds the longer sentence, for the drawer, and the
    fields `status` and the card read are the short `NEXT:` and the problems, as before."""
    for way in factory.WAYS:
        text = factory.stop_text("013-draft-escapes", way, ["it broke"])
        why = factory.WAYS_WHY[way].format(id="013")
        assert why in text.splitlines(), way
        for regex in (factory.STOPPED_RE, factory.NEXT_RE, factory.PROBLEM_RE):
            assert not regex.match(why), (way, regex.pattern)
        _write(tmp_path / factory.STOPPED, text)
        assert sdlc.factory_stop(tmp_path) == {
            "way": way, "next": factory.WAYS[way].format(id="013"), "problems": ["it broke"]
        }  # fmt: skip


@pytest.mark.portable
def test_a_long_next_step_wraps_inside_its_card() -> None:
    """120 (2026-11-17-81): a long unbroken token in `next:` breaks inside the card at any width,
    as the title, the needs line and the flags already do."""
    css, _ = _page_parts()
    rule = re.search(r"\.next code \{([^}]*)\}", css)
    assert rule and "overflow-wrap: anywhere" in rule.group(1), rule


@pytest.mark.portable
def test_a_stop_hides_the_step_track_as_it_always_has(repo) -> None:
    """120 (2026-11-17-83): `_progress()`'s stop test, parenthesised, reads as before: a stop
    `status` read hides the track at any stage, a record on disk only at `build`."""
    folder = _run_at(repo, "build")

    def track(stage: str, stopped: dict | None) -> dict | None:
        entry = {"stage": stage, "tier": 2, "built": [], "decision": None, "stopped": stopped}
        return board._progress(entry, folder, [], {}, board._since("2026-11-17T10:00:00Z") + 60)

    assert track("build", None) is not None
    assert track("build", {"way": "rerun"}) is None
    assert track("test", {"way": "rerun"}) is None
    _write(folder / factory.STOPPED, factory.stop_text(folder.name, "rerun", ["it broke"]))
    assert track("build", None) is None
    assert track("test", None) is not None, "a record left at another stage is no stop"


@pytest.mark.portable
def test_a_stop_record_counts_only_at_build(repo) -> None:
    """R8: a run shipped by hand keeps its record in history, and the board reads past it."""
    _stopped_run(repo, "013-draft-escapes", "design")
    folder = _stopped_run(repo, "014-draft-stale", "test")
    _write(folder / "decision.md", "DECISION: READY\n")
    cards = _cards(repo)
    assert cards["013-draft-escapes"]["column"] == "design"
    assert cards["013-draft-escapes"]["stopped"] is None
    assert (cards["014-draft-stale"]["column"], cards["014-draft-stale"]["stopped"]) == (
        "ready",
        None,
    )
    shipped = _worktree(repo, "015-draft-shipped", 1, "shipped", commit=["src/x.py"], factory=True)
    _write(shipped / factory.STOPPED, "not even readable\n")
    card = _cards(repo)["015-draft-shipped"]
    assert (card["column"], card["problems"]) == ("close", [])


@pytest.mark.portable
def test_a_resumed_run_goes_back_to_build(repo) -> None:
    """R9: a reading that finds the cause gone removes the record, and the card is a run again."""
    folder = _stopped_run(repo)
    (folder / factory.STOPPED).unlink()
    card = _cards(repo)["013-draft-escapes"]
    assert (card["column"], card["stopped"]) == ("build", None)
    assert card["next"] == "the factory is building it: wait for its decision"


@pytest.mark.portable
def test_the_factory_parsing_is_a_pinned_copy() -> None:
    names = ("VERDICT_RE", "DECISION_RE", "CHANGE_RE", "KEPT_RE", "DROPPED_RE", "LEDGER_RE")
    for name in names:
        assert getattr(board, name).pattern == getattr(factory, name).pattern, name
    assert board.VERIFIED == factory.VERIFIED and board.COSTS == factory.COSTS
    assert board.RECONSIDER == factory.RECONSIDER
    assert board.STOPPED == factory.STOPPED
    assert board.SETTLED == factory.SETTLED


@pytest.mark.portable
def test_the_boards_opening_is_a_pinned_copy() -> None:
    """140 R8: the board reads a round's verdicts and the decision as `factory.opening()` does,
    case for case over the shared table."""
    cases = json.loads((ROOT / "tests" / "fixtures" / "opening-cases.json").read_text("utf-8"))
    for case in cases:
        regex = {"verdict": factory.VERDICT_RE, "decision": factory.DECISION_RE}[case["kind"]]
        mine, theirs = board.opening(case["lines"], regex), factory.opening(case["lines"], regex)
        got = [mine[0], mine[1].group(1)] if mine else None
        assert got == ([theirs[0], theirs[1].group(1)] if theirs else None) == case["answer"], case


@pytest.mark.portable
def test_the_board_reads_a_verdict_and_a_decision_after_prose(tmp_path) -> None:
    """140 R8: a round's reply and a decision whose answer follows prose read on the board as
    `verdicts` reads them, never as a problem."""
    folder = tmp_path / "008-reopen-drafts"
    (folder / "reviews" / "round-1").mkdir(parents=True)
    (folder / "build").mkdir()
    (folder / "build" / "round-1.md").write_text("Built.\n", encoding="utf-8")
    (folder / "reviews" / "round-1" / "code.md").write_text(
        "Read it all.\n\nVERDICT: CHANGES\n- CHANGE: src/drafts.py:3: saves twice\n", "utf-8"
    )
    (folder / "reviews" / "round-1" / "test.md").write_text(
        "Hmm.\nVERDICT: PASS\nVERDICT: CHANGES\n", encoding="utf-8"
    )
    (folder / "decision.md").write_text("I read every round.\n\nDECISION: READY\n", "utf-8")
    problems: list[str] = []
    found = board._factory(folder, problems)
    assert found["rounds"][0]["reviews"]["code"] == {"verdict": "CHANGES", "changes": 1}
    assert found["decision"] == "READY"
    assert problems == ["reviews/round-1/test.md doesn't open with a VERDICT line"], problems
    assert board._reviewed(folder, 1) == 1


@pytest.mark.portable
def test_a_change_s_issue_link_is_built_from_the_remote_only_when_github_numbers_it(
    repo, monkeypatch
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:someone/drafts.git")
    cfg = sdlc.load_config(repo)[0]
    assert board._issue_base(repo, cfg) is None, "local numbering has no issue to link"
    monkeypatch.setattr(sdlc, "ids_mode", lambda home, cfg: "github")
    assert board._issue_base(repo, cfg) == "https://github.com/someone/drafts/issues/"
    assert (
        _cards(repo)["002-draft-history"]["issue"] == "https://github.com/someone/drafts/issues/2"
    )


def test_status_never_loads_the_board() -> None:
    """R1: only `board`'s dispatch loads `board.py`, so no other command pays for it."""
    source = (ROOT / "scripts" / "sdlc.py").read_text(encoding="utf-8")
    calls = re.findall(r"(?<!def )_load_board\(\)", source)
    assert len(calls) == 1 and "return _load_board().cmd_board(root, args.port)" in source
    assert "board" not in vars(sdlc), "nothing binds it at import, as retro is bound"


# ---------------------------------------------------------------- the server


@pytest.fixture
def served(repo):
    # Port 0 binds at once, so no other worker can take the port between choosing and binding it.
    server = board.serve(repo, 0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield repo, f"http://127.0.0.1:{port}", port
    server.shutdown()
    server.server_close()


def _get(url: str, method: str = "GET", headers: dict | None = None) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


@pytest.mark.portable
def test_the_board_answers_three_gets_and_nothing_else(served) -> None:
    root, url, _ = served
    code, body, headers = _get(url + "/")
    assert code == 200 and b"<title>Change board</title>" in body
    assert headers["Content-Type"].startswith("text/html")
    code, body, _ = _get(url + "/state.json")
    st = json.loads(body)
    assert code == 200 and st["board"] == "sdlc" and len(st["changes"]) == 4
    code, body, _ = _get(url + "/file?change=001-reopen-drafts&path=notes.md")
    assert code == 200 and b"say why a draft closes" in body
    for method in ("POST", "PUT", "DELETE", "PATCH"):
        assert _get(url + "/state.json", method)[0] == 405, method
    assert _get(url + "/anything")[0] == 404
    assert _get(url + "/state.json", headers={"Host": "evil.example:80"})[0] == 404, "rebinding"
    for host in ("127.0.0.1:0", "localhost:0", "127.0.0.1"):
        assert _get(url + "/state.json", headers={"Host": host})[0] == 404, host
    port = int(url.rsplit(":", 1)[1])
    assert _get(url + "/state.json", headers={"Host": f"localhost:{port}"})[0] == 200


@pytest.mark.portable
def test_file_never_leaves_an_open_change_s_folder(served) -> None:
    root, url, _ = served
    (root / "secret.txt").write_text("nope\n", encoding="utf-8")
    folder = root / ".sdlc" / "work" / "001-reopen-drafts"
    for change, path in [
        ("001-reopen-drafts", "../../../secret.txt"),
        ("001-reopen-drafts", str(root / "secret.txt")),
        ("001-reopen-drafts", "missing.md"),
        ("009-no-such-change", "intent.md"),
        ("005-old-thing", "intent.md"),
        ("001-reopen-drafts", ""),
    ]:
        query = urllib.parse.urlencode({"change": change, "path": path})
        assert _get(f"{url}/file?{query}")[0] == 404, (change, path)
    try:
        (folder / "link.txt").symlink_to(root / "secret.txt")
    except OSError:
        return  # no symlinks without privileges on Windows: the rest has been checked
    assert _get(f"{url}/file?change=001-reopen-drafts&path=link.txt")[0] == 404


@pytest.mark.portable
def test_the_board_writes_nothing(served) -> None:
    root, url, _ = served
    _closed(root, "019-draft-closed", 2)
    _run_at(root, "review", 1)
    _git(root, "add", "-A")
    before = _git(root, "status", "--porcelain", "--ignored")
    for path in ("/", "/state.json", "/file?change=003-draft-export&path=decision.md"):
        _get(url + path)
    assert json.loads(_get(url + "/state.json")[1])["changes"][-1]["progress"]["step"] == "review"
    _get(url + "/state.json", "POST")
    assert _git(root, "status", "--porcelain", "--ignored") == before


@pytest.mark.portable
def test_a_second_board_reports_the_first_and_anything_else_is_refused(
    served, capsys, tmp_path
) -> None:
    root, url, port = served
    assert board.cmd_board(root, port) == 0
    assert json.loads(capsys.readouterr().out) == {"url": f"{url}/", "serving": "already"}
    other = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
    threading.Thread(target=other.serve_forever, daemon=True).start()
    try:
        taken = other.server_address[1]
        assert board.cmd_board(root, taken) == 1
        assert f"port {taken}" in json.loads(capsys.readouterr().out)["refusals"][0]
    finally:
        other.shutdown()
        other.server_close()


# ---------------------------------------------------------------- the page


@pytest.mark.portable
def test_the_page_is_self_contained_and_never_parses_data_as_html() -> None:
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", page), "nothing external"
    assert "<link" not in page and "@import" not in page
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
        assert sink not in page, sink
    assert "textContent" in page
    for column in ("plan", "design", "build", "test", "ready", "needs-you"):
        assert f'key: "{column}"' in page, column


@pytest.mark.portable
def test_no_column_key_is_a_class_the_page_styles_on_its_own() -> None:
    # A card carries its column's key as a class (`card close`), so a rule for that class
    # anywhere but on a `.col` or a `.card` restyles every card in the column.
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    keys = set(re.findall(r'\{ key: "([^"]+)"', page))
    assert {"ready", "close", "needs-you"} <= keys
    css = re.search(r"<style>(.*?)</style>", page, re.S).group(1)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    clashes = []
    for block in re.findall(r"([^{}]+)\{", css):
        for selector in block.split(","):
            if selector.strip().startswith("@"):
                continue
            for compound in re.split(r"[\s>+~]+", selector.strip()):
                classes = set(re.findall(r"\.([A-Za-z_][\w-]*)", compound))
                if classes & keys and not classes & {"col", "card"}:
                    clashes.append(selector.strip())
    assert not clashes, clashes


# ---------------------------------------------------------------- progress (088)

FULL = ["code", "security", "test", "behaviour"]


def _run_at(
    root: Path,
    step: str | None,
    rnd: int | None = 1,
    name: str = "016-draft-tags",
    tier: int = 2,
    since: str = "2026-11-17T10:00:00Z",
    after: str | None = None,
) -> Path:
    """A factory run at `stage: build` whose supervisor's last reading named `step`, the record
    written by `factory.py`'s own writer; `None` leaves no record."""
    folder = _change(root, name, tier, "build", "Draft tags")
    _write(folder / "runs" / "builder.sessions", "s-1\n")
    if step is not None:
        out = {"next": step, "round": rnd, "limit": 3, "reviewers": FULL}
        _write(folder / factory.STEP, factory.step_text(out, since, after))
    return folder


def _states(card: dict) -> list[str]:
    return [s["state"] for s in card["progress"]["steps"]]


TRACKS = {
    "build": ["current", "todo", "todo", "todo", "todo", "todo"],
    "gate": ["done", "current", "todo", "todo", "todo", "todo"],
    "fix": ["done", "current", "todo", "todo", "todo", "todo"],
    "review": ["done", "done", "current", "todo", "todo", "todo"],
    "verify": ["done", "done", "done", "current", "todo", "todo"],
    "rework": ["done", "done", "done", "done", "current", "todo"],
    "approve": ["done", "done", "done", "done", "done", "current"],
    "decide": ["done", "done", "paused", "todo", "todo", "todo"],
    "done": ["done"] * 6,
}


@pytest.mark.portable
@pytest.mark.parametrize("step", list(TRACKS))
def test_a_factory_card_shows_its_step_track(repo, step) -> None:
    """R4: the record's step is current, those before it done, those after it to do."""
    _run_at(repo, step, None if step in ("decide", "done") else 1, after="review")
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert [s["name"] for s in progress["steps"]] == list(board.TRACK)
    assert [s["state"] for s in progress["steps"]] == TRACKS[step]
    assert progress["step"] == step and progress["limit"] == 3
    labels = {s["name"]: s["label"] for s in progress["steps"]}
    assert (labels["gate"] == "fixing") == (step == "fix")
    if step in ("decide", "done"):
        assert progress["elapsed"] is None and progress["fraction"] is None, "no bar"
    else:
        assert progress["elapsed"] >= 0 and progress["round"] == 1


@pytest.mark.portable
@pytest.mark.parametrize("step", ["upgrade", "spec"])
def test_an_upgrade_pauses_the_step_track(repo, step) -> None:
    """112 R13: an upgrade and its spec pause the track where the run was, as a decide does, from
    the board's pinned copy of the paused steps."""
    assert board.PAUSES == factory.PAUSES
    _run_at(repo, step, 2, after="review")
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert progress is not None, "the track is kept, not dropped"
    assert [s["state"] for s in progress["steps"]] == TRACKS["decide"]
    assert progress["paused"] is True and progress["elapsed"] is None


@pytest.mark.portable
def test_an_early_stop_shows_on_the_card(repo) -> None:
    """2026-11-18-33: a run that stopped early (its record's `- STUCK:` and `- UNTESTABLE:` lines)
    says so on its `approve` step and names each reason, rather than reading as a plain approve;
    a run with none reads as before."""
    stuck, line = "code: src/a.py:1: rename a", "R4: judged by eye, no test can show it"
    folder = _run_at(repo, "approve", rnd=2)
    card = _cards(repo)["016-draft-tags"]
    assert card["progress"]["early"] is None
    assert card["progress"]["steps"][-1]["label"] == "approve"
    out = {"next": "approve", "round": 2, "limit": 3, "reviewers": FULL, "stuck": [stuck],
           "untestable": [line]}  # fmt: skip
    _write(folder / factory.STEP, factory.step_text(out, "2026-11-17T10:00:00Z"))
    card = _cards(repo)["016-draft-tags"]
    progress = card["progress"]
    assert progress["early"] == {"stuck": [stuck], "untestable": [line]}
    assert _states(card) == TRACKS["approve"] and progress["step"] == "approve"
    assert progress["steps"][-1]["label"] == "approve (stuck, untestable)"
    out["untestable"] = []
    _write(folder / factory.STEP, factory.step_text(out, "2026-11-17T10:00:00Z"))
    assert _cards(repo)["016-draft-tags"]["progress"]["steps"][-1]["label"] == "approve (stuck)"
    assert card["column"] == "build" and card["needs"] == [], "the approver is still to decide"
    script = _page_parts()[1]
    row = re.search(r"function progressRow\(p\) \{(.*?)\n\}", script, re.S).group(1)
    assert re.search(r"p\.early.*stuck.*\"flag\".*stopped early", row, re.S), row
    assert re.search(r"p\.early.*untestable.*\"flag\".*stopped early", row, re.S), row


@pytest.mark.portable
def test_a_decision_or_a_stop_overrides_the_record(repo) -> None:
    """R4: a valid decision is every step done, at the stage it belongs to (098); a stop shown
    has no track at all."""
    folder = _run_at(repo, "review")
    _write(folder / "decision.md", "DECISION: ESCALATE\n\nAsk them.\n")
    intent = folder / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8").replace("stage: build", "stage: test"),
                      encoding="utf-8", newline="\n")  # fmt: skip
    assert _states(_cards(repo)["016-draft-tags"]) == ["done"] * 6
    stopped = _run_at(repo, "stop", None, name="017-draft-stop")
    _write(stopped / factory.STOPPED, factory.stop_text("017-draft-stop", "rerun", ["it broke"]))
    assert _cards(repo)["017-draft-stop"]["progress"] is None
    assert _cards(repo)["003-draft-export"]["progress"]["steps"][-1]["state"] == "done", "READY"


@pytest.mark.portable
def test_reviews_count_up_as_they_land(repo) -> None:
    """R5: `n` is counted on every request from the round's folder; `m` is the record's."""
    folder = _run_at(repo, "review", 2)
    review = _cards(repo)["016-draft-tags"]["progress"]["steps"][2]
    assert review["label"] == "reviews 0/4"
    _write(folder / "reviews" / "round-2" / "code.md", "VERDICT: PASS\n")
    _write(folder / "reviews" / "round-2" / "verified.md", "- KEPT: code: a\n")
    _write(folder / "reviews" / "round-1" / "test.md", "VERDICT: PASS\n")
    assert _cards(repo)["016-draft-tags"]["progress"]["steps"][2]["label"] == "reviews 1/4"
    _write(folder / "reviews" / "round-2" / "test.md", "VERDICT: CHANGES\n- CHANGE: a\n")
    assert _cards(repo)["016-draft-tags"]["progress"]["steps"][2]["label"] == "reviews 2/4"


@pytest.mark.portable
def test_a_first_build_runs_from_its_builder_session(repo) -> None:
    """R6: no record and no builder report: the build is current since `builder.sessions`."""
    folder = _run_at(repo, None)
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert _states({"progress": progress}) == TRACKS["build"] and progress["round"] == 1
    _write(folder / "build" / "round-1.md", "Built.\n")
    assert _cards(repo)["016-draft-tags"]["progress"] is None, "built, but no record: no track"


@pytest.mark.portable
def test_a_run_without_a_record_has_no_track(repo) -> None:
    """R6: a Tier 2 whose spec is still being drafted, or a run from before the record."""
    folder = _change(repo, "018-draft-spec", 2, "plan", "Draft spec")
    _write(folder / "runs" / "spec-writer.sessions", "s-1\n")
    cards = _cards(repo)
    assert cards["018-draft-spec"]["progress"] is None
    assert cards["001-reopen-drafts"].get("progress", "absent") == "absent", "by hand: no key"


@pytest.mark.portable
def test_a_garbled_step_record_is_a_problem(repo) -> None:
    folder = _run_at(repo, "review")
    _write(folder / factory.STEP, "running, probably\n")
    card = _cards(repo)["016-draft-tags"]
    assert card["progress"] is None
    assert any("runs/step.md" in p for p in card["problems"]), card["problems"]


@pytest.mark.portable
def test_the_step_record_is_a_pinned_copy(tmp_path) -> None:
    """R7: the board's copies are `factory.py`'s, and its writer reads back through the board."""
    for name in ("STEP_RE", "ROUND_RE", "LIMIT_RE", "REVIEWERS_RE", "SINCE_RE", "AFTER_RE",
                 "SECONDS_RE", "STUCK_RE", "UNTESTABLE_RE"):  # fmt: skip
        assert getattr(board, name).pattern == getattr(factory, name).pattern, name
    assert board.STEP == factory.STEP and board.REVIEWER_ROLES == factory.REVIEWERS
    gate = (ROOT / "plugins" / "factory" / "scripts" / "factory.py").read_text(encoding="utf-8")
    assert "Seconds: {seconds}" in gate and board.SECONDS_RE.match("Seconds: 12.5")
    for out in (
        {"next": "review", "round": 2, "limit": 3, "reviewers": [*FULL, "ui"]},
        {"next": "decide", "round": None, "limit": 2, "reviewers": ["code"]},
        {
            "next": "approve",
            "round": 2,
            "limit": 3,
            "reviewers": FULL,
            "stuck": ["code: a"],
            "untestable": ["R4: by eye"],
        },
    ):
        text = factory.step_text(out, "2026-11-17T10:00:00Z", "rework")
        assert board.read_step(text) == factory.read_step(text)
        assert board.read_step(text)["reviewers"] == out["reviewers"]
    assert board.read_step(text)["stuck"] == ["code: a"], "the early stop's reason reads back"


def _row(role: str, seconds: float | None) -> tuple[str, dict]:
    return role, ({} if seconds is None else {"duration_ms": int(seconds * 1000)})


# One closed factory run, in the order its sessions ended: a build, two review rounds with a
# verification and a rework between them, the approver, then the landing's own review.
RUN = [
    _row("spec-writer", 300), _row("builder", 100), _row("code", 30), _row("test", 50),
    _row("verifier", 20), _row("builder", 40), _row("code", 10), _row("builder", None),
    _row("test", 12), _row("approver", 15), _row("code", 999), _row("builder", 999),
]  # fmt: skip


def _closed(root: Path, name: str, tier: int, rows=RUN, gates=(5.0, 6.0), land_gates=()) -> None:
    """A factory change closed on `main`: its folder committed with the rows `factory.py`'s own
    `record_cost()` writes and its gate files, then removed by a `Close` commit."""
    folder = _change(root, name, tier, "shipped", name.split("-", 1)[1])
    for i, (role, figures) in enumerate(rows):
        factory.record_cost(folder, f"s-{i}", role, "opus", figures)
    for file, seconds in (("round-1", gates), ("land-1", land_gates)):
        if not seconds:
            continue
        attempts = "".join(f"## Attempt {k}\n\nVerdict: PASS\nSeconds: {s}\n\n"
                           for k, s in enumerate(seconds, 1))  # fmt: skip
        _write(folder / "build" / f"{file}.gate.md", f"GATE: PASS\n\n{attempts}")
    _git(root, "add", "-A", str(folder))
    _git(root, "commit", "-q", "-m", f"Ship {name}")
    _git(root, "rm", "-rq", str(folder))
    _git(root, "commit", "-q", "-m", f"Close {name}")


@pytest.mark.portable
def test_typical_times_come_from_closed_factory_runs(repo) -> None:
    """R9: each step's samples, split by role and order, at the change's tier."""
    _closed(repo, "020-draft-a", 2)
    rows = [_row("builder", 200), _row("code", 70), _row("approver", 25)]
    _closed(repo, "021-draft-b", 2, rows, gates=(9.0,))
    _closed(repo, "022-draft-c", 2, rows, gates=())
    _closed(repo, "023-draft-d", 1, rows)
    _change(repo, "024-draft-manual", 2, "shipped", "Manual")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Close 024-draft-manual")
    samples = board.history_samples(repo, "main")
    assert samples[("build", 2)] == {"020-draft-a": [100], "021-draft-b": [200],
                                      "022-draft-c": [200]}  # fmt: skip
    assert samples[("review", 2)]["020-draft-a"] == [50, 12], "the slowest of each round"
    assert samples[("verify", 2)] == {"020-draft-a": [20]}
    assert samples[("rework", 2)] == {"020-draft-a": [40]}, "a row with no duration is skipped"
    assert samples[("approve", 2)]["020-draft-a"] == [15], "the landing's rows are not the run's"
    assert samples[("gate", 2)] == {"020-draft-a": [5.0, 6.0], "021-draft-b": [9.0]}
    assert set(samples[("build", 1)]) == {"023-draft-d"}
    table = board.typical_times(repo, "main")
    assert table["build/2"] == {"seconds": 200, "samples": 3}
    assert table["review/2"] == {"seconds": 60, "samples": 3}, "the median of every sample"
    assert "verify/2" not in table and "build/1" not in table, "fewer than 3 changes: no figure"


@pytest.mark.portable
def test_the_estimate_is_capped_and_absent_without_history(repo) -> None:
    """R8: the bar never passes 95%, and a tier with 2 sampled changes has no typical time."""
    rows = [_row("builder", 60), _row("code", 60), _row("approver", 60)]
    for name in ("030-draft-a", "031-draft-b"):
        _closed(repo, name, 2, rows)
    _run_at(repo, "build", since="2000-01-01T00:00:00Z")
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert progress["elapsed"] > 0
    assert (progress["typical"], progress["fraction"], progress["samples"]) == (None, None, None)
    _closed(repo, "032-draft-c", 2, rows)
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert (progress["typical"], progress["fraction"], progress["samples"]) == (60, 0.95, 3)
    fresh = board._progress(
        {"stage": "build", "tier": 2, "built": [1], "decision": None, "stopped": None},
        repo / ".sdlc" / "work" / "016-draft-tags",
        [],
        {"build/2": {"seconds": 600, "samples": 3}},
        board._since("2000-01-01T00:00:00Z") + 60,
    )
    assert (fresh["elapsed"], fresh["fraction"]) == (60, 0.1)


@pytest.mark.portable
def test_history_is_read_once_per_base_branch_tip(repo, monkeypatch) -> None:
    """R10: one `rev-parse` a request; the walk again only once the tip moves."""
    rows = [_row("builder", 60)]
    for name in ("040-draft-a", "041-draft-b", "042-draft-c"):
        _closed(repo, name, 2, rows)
    walks = []
    real = sdlc._git

    def counting(root, *args):
        if "log" in args and any("costs.jsonl" in a for a in args):
            walks.append(args)
        return real(root, *args)

    monkeypatch.setattr(sdlc, "_git", counting)
    board.state(repo)
    board.state(repo)
    assert len(walks) == 1, walks
    _closed(repo, "043-draft-d", 2, [_row("builder", 600)])
    board.state(repo)
    assert len(walks) == 2
    assert board.typical_times(repo, "main")["build/2"]["samples"] == 4


PLAN = """\
# 050 — plan

## Files to change

- `src/tags.py`: the tags.
- `docs/tags.md` (new): what they are.
- src/other.py: untouched yet, its width read from
  `progress.fraction` on a wrapped line, which names nothing.
- tests/: a test each.
- `<Path + one line on what happens to it.>`
- The docs, as their own lines.

## Work order

- `src/not-a-file-to-change.py`
"""


@pytest.mark.portable
def test_the_plan_hint_counts_named_files_the_branch_touched(repo) -> None:
    """R11: the named paths of `## Files to change` the branch or its worktree has touched."""
    commit = ["src/tags.py", "tests/test_tags.py"]
    folder = _worktree(
        repo, "050-draft-tags", 2, "build", factory=True, commit=commit, dirty=["docs/tags.md"]
    )
    _write(folder / "plan.md", PLAN)
    assert board._plan_named(PLAN) == ["src/tags.py", "docs/tags.md", "src/other.py", "tests/"]
    assert _cards(repo)["050-draft-tags"]["progress"]["plan"] == {"named": 4, "touched": 3}
    _write(folder / "plan.md", "# plan\n\n## Files to change\n\n<Path.>\n<More.>\n")
    assert _cards(repo)["050-draft-tags"]["progress"]["plan"] is None, "an unfilled plan"
    one = _worktree(repo, "051-draft-pins", 1, "build", factory=True, commit=["src/tags.py"])
    _write(one / "plan.md", PLAN)
    assert _cards(repo)["051-draft-pins"]["progress"]["plan"] is None, "a Tier 1 change"
    _write(folder / "plan.md", "# plan\n\n## Files to change\n\nThe usual ones.\n")
    assert _cards(repo)["050-draft-tags"]["progress"]["plan"] is None, "no path named"


@pytest.mark.portable
def test_the_bar_is_drawn_from_the_capped_fraction() -> None:
    """R13: the only width the page sets from data is `progress.fraction`'s, labelled an estimate,
    and the track's chips use no column key as a class."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    widths = re.findall(r"width:\s*\$\{([^}]*)\}", script)
    assert widths and all(re.fullmatch(r"Math\.round\(p\.fraction \* 100\)", w) for w in widths)
    assert "style" not in re.sub(r'style: `width: \$\{Math\.round\(p\.fraction \* 100\)\}%`', "",
                                 script), "no other style is set"  # fmt: skip
    assert "estimate" in script and "typical" in script and "files touched" in script
    assert "function progressRow(" in script and "progressRow(c.progress)" in script


@pytest.mark.portable
def test_a_step_s_state_is_in_its_text_and_the_bar_is_hidden_from_assistive_tech() -> None:
    """Round 1's ux changes: a step's state is said in its text, not by colour alone, and the bar,
    inside the card's button where a role would be dropped, is hidden; its figures are text."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    words = re.search(r"const STEP_WORDS = \{(.*?)\};", script, re.S)
    assert words, "each state has its own words"
    for state in ("done", "current", "paused", "stopped"):
        assert re.search(rf'\b{state}: "[^"]+"', words.group(1)), state
    assert "progressbar" not in script
    assert re.search(r'class: "bar", "aria-hidden": "true"', script)


def _page_parts() -> tuple[str, str]:
    """The served page's stylesheet, comments dropped, and its script."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", page, re.S).group(1)
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S), script


@pytest.mark.portable
def test_needs_you_comes_first_at_phone_width_and_nowhere_else() -> None:
    """099 (2026-11-17-24): below 760px the columns stack, and the one waiting on the person
    leads them in the DOM, so Tab and a screen reader meet it first, as the eye does; the desktop
    grid keeps stage order, and no CSS `order` sets a look the DOM doesn't follow."""
    css, script = _page_parts()
    assert re.search(r"@media \(max-width: 760px\) \{\s*main\.board \{[^}]*1fr", css)
    assert 'window.matchMedia("(max-width: 760px)")' in script, "the same width as the CSS"
    order = re.search(r"function columnOrder\(\) \{(.*?)\n\}", script, re.S)
    assert order, "one place says the order"
    body = order.group(1)
    assert re.search(r"NARROW\.matches\s*\?\s*\[", body), "reordered only when narrow"
    assert re.search(r":\s*COLUMNS;", body), "stage order otherwise"
    assert body.index('=== "needs-you"') < body.index('!== "needs-you"'), "Needs you first"
    assert "columnOrder().map(" in script and "COLUMNS.map(" not in script
    assert re.search(r"JSON\.stringify\(\[NARROW\.matches, st\.changes\], shownAs\)", script), (
        "a width change is a change to render"
    )
    assert re.search(r'NARROW\.addEventListener\("change", [^\n]*render\(', script)
    assert not re.search(r"(?<![\w-])order:", css), "the DOM is the order"


@pytest.mark.portable
def test_the_open_drawer_keeps_tab_inside_it() -> None:
    """099 (2026-11-17-25): the drawer is aria-modal, so Tab and Shift-Tab cycle its focusable
    nodes, focus outside it is pulled back in, and Escape still closes it and returns focus."""
    _, script = _page_parts()
    trap = re.search(r"function trapTab\(e\) \{(.*?)\n\}", script, re.S)
    assert trap, "the trap's handler"
    body = trap.group(1)
    assert "querySelectorAll(FOCUSABLE)" in body and "e.preventDefault()" in body
    assert "e.shiftKey" in body and ".contains(document.activeElement)" in body
    handler = r'document\.addEventListener\("keydown", \(e\) => \{(.*?)\n\}\);'
    keys = re.search(handler, script, re.S)
    assert keys and "if (!open) return;" in keys.group(1)
    assert 'e.key === "Escape"' in keys.group(1) and 'e.key === "Tab"' in keys.group(1)
    assert "trapTab(e)" in keys.group(1)
    assert "back.focus()" in script, "focus returns to the card that opened it"
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert re.search(r'<div class="doc" tabindex="0"[^>]*aria-label="[^"]+"', page), (
        "the scrolling pane is a stop of the trap's, not a way out"
    )


@pytest.mark.portable
def test_the_verifier_chip_says_whose_count_it_is_in_its_text() -> None:
    """099 (2026-11-17-26): the count names the verifier in the text every user gets, not only in
    a tooltip."""
    _, script = _page_parts()
    chip = re.search(r"if \(r\.verified\) \{(.*?)\n  \}", script, re.S)
    assert chip
    assert re.search(r"`verifier: kept \$\{r\.verified\.kept\} · dropped", chip.group(1))


def _escalated(root: Path, name: str, stage: str, commit=()) -> Path:
    """A factory change in a worktree of its own, as a run leaves one the approver escalated: a
    round built and reviewed, `decision.md` saying ESCALATE, and `stage:` at whatever the person's
    answer moved it to."""
    folder = _worktree(root, name, 2, stage, commit=commit, factory=True)
    _write(folder / "build" / "round-1.md", "Built.\n\n## Evidence\n\n$ ./check.sh\nexit: 0\n")
    _write(folder / "reviews" / "round-1" / "code.md", "VERDICT: PASS\n")
    _write(folder / "decision.md", "DECISION: ESCALATE\n\nThe spec leaves the retention open.\n")
    return folder


@pytest.mark.portable
def test_each_factory_signal_counts_only_at_its_stage(repo) -> None:
    """086: the stage is the only mark of the person's answer, so an escalation, a stop or a
    pending decision the person has moved past leaves Needs you for the column that answer leads
    to."""
    _escalated(repo, "020-esc-shipped", "shipped", commit=["src/a.py"])
    _escalated(repo, "021-esc-dropped", "dropped")
    _escalated(repo, "022-esc-by-hand", "test", commit=["src/b.py"])
    _escalated(repo, "023-esc-back", "build")
    stopped = _worktree(repo, "024-stop-shipped", 1, "shipped", commit=["src/c.py"], factory=True)
    _write(stopped / factory.STOPPED, factory.stop_text("024", "rerun", STOP_PROBLEMS))
    pending = _worktree(repo, "025-pend-shipped", 1, "shipped", commit=["src/d.py"], factory=True)
    _write(pending / "decisions.md", "- [ ] D1 (code round 1, blocking): purge after 30 days?\n")
    at_test = _worktree(repo, "027-pend-test", 1, "test", commit=["src/f.py"], factory=True)
    _write(at_test / "decisions.md", "- [ ] D1 (code round 1, blocking): purge after 30 days?\n")
    answered = _escalated(repo, "028-esc-answered", "test", commit=["src/g.py"])
    _write(answered / "decisions.md", TICKED)
    cards = _cards(repo)
    got = {n: (c["column"], c["next"]) for n, c in cards.items() if n >= "020"}
    assert got == {
        "020-esc-shipped": ("close", "/sdlc:close 020"),
        "021-esc-dropped": ("close", "/sdlc:close 021"),
        "022-esc-by-hand": ("needs-you", "/sdlc:ship, or /sdlc-factory:land with the others ready"),
        "028-esc-answered": ("ready", "/sdlc:ship, or /sdlc-factory:land with the others ready"),
        "023-esc-back": ("build", "the factory is building it: wait for its decision"),
        "024-stop-shipped": ("close", "/sdlc:close 024"),
        "025-pend-shipped": ("close", "/sdlc:close 025"),
        "027-pend-test": ("test", "/sdlc:ship"),
    }
    assert all(cards[n]["problems"] == [] for n in got), "every file read"
    assert cards["022-esc-by-hand"]["needs"] == ["read the escalation"], "107 R9: no ledger"
    assert all(cards[n]["needs"] == [] for n in got if cards[n]["column"] != "needs-you")


@pytest.mark.portable
def test_a_file_that_wont_read_needs_the_person_at_any_stage(repo) -> None:
    """086: a stage never hides a problem."""
    folder = _escalated(repo, "026-bad-shipped", "shipped", commit=["src/e.py"])
    _write(folder / "decision.md", "Ship it, I think.\n")
    card = _cards(repo)["026-bad-shipped"]
    assert card["column"] == "needs-you"
    assert any("decision.md" in p for p in card["problems"]), card["problems"]
    assert card["needs"] == [f"fix: {p}" for p in card["problems"]], "107 R8"


@pytest.mark.portable
def test_a_restarted_factory_card_is_in_build_with_its_old_decision_as_a_file(served) -> None:
    """095 R11: a change the factory took back has no decision of its own run yet; its old one is
    a file in its folder, never the card's decision."""
    root, url, _ = served
    folder = _change(root, "016-draft-restart", 2, "build", "Draft restart")
    _write(folder / "runs" / "builder.sessions", "s-1\ns-2\n")
    _write(folder / "build" / "round-1.md", "Built.\n")
    _write(folder / "reviews" / "round-1" / "code.md", "VERDICT: PASS\n")
    _write(folder / "decision-1.md", "DECISION: ESCALATE\n\nD1 is still assumed.\n")
    _write(folder / "build" / "round-2.restart.md", "RESTART: decision-1.md\n")
    card = _cards(root)["016-draft-restart"]
    assert (card["column"], card["decision"], card["problems"]) == ("build", None, [])
    assert card["built"] == [1], "the restart record is no builder report"
    assert {"decision-1.md", "build/round-2.restart.md"} <= set(card["files"])
    code, body, _ = _get(f"{url}/file?change=016-draft-restart&path=decision-1.md")
    assert code == 200 and body.startswith(b"DECISION: ESCALATE")


# ---------------------------------------------------------------- the board as it is (098)


@pytest.mark.portable
def test_a_card_with_a_problem_never_names_close(repo) -> None:
    """2026-11-17-23: a card with a file that won't read is under Needs you at any stage, and its
    next step is the problem, never `/sdlc:close`, `/sdlc:ship` or the stage's own step."""
    named = {"026-bad-shipped": "shipped", "028-bad-dropped": "dropped",
             "030-bad-build": "build", "031-bad-test": "test", "032-bad-plan": "plan"}  # fmt: skip
    for name, stage in named.items():
        folder = _escalated(repo, name, stage, commit=[f"src/{name}.py"])
        _write(folder / "decision.md", "Ship it, I think.\n")
    cards = _cards(repo)
    for name in named:
        card = cards[name]
        assert card["column"] == "needs-you" and card["problems"], card
        assert "/sdlc:close" not in card["next"], card["next"]
        assert card["next"] == "fix what its problems name"


# `next_action()`'s precedence, highest first: each state's fields, and the step it names when
# it is the highest a card holds. A card in two states names the higher one's step, whatever
# else it holds, but for the pairs in `BOTH`; two states that set `stage` to different values
# can't overlap.
PRECEDENCE = [
    ("rebasing", {"rebasing": True},
     "a rebase is stopped in its worktree: resolve its conflicts, then "
     "sdlc.py resolve 016 --continue, or sdlc.py resolve 016 --abort, which keeps the "
     "resolved work under refs/sdlc/end/016-draft-tags"),
    ("stage missing", {"stage": None, "problems": ["intent.md couldn't be read: conflict"]},
     "fix intent.md's frontmatter"),
    ("problems", {"problems": ["findings.md couldn't be read: conflict"]},
     "fix what its problems name"),
    ("landing stopped", {"progress": {"kind": "land", "stopped": True, "after": "gate"}},
     "the landing stopped at gate: fix what it names, then /sdlc-factory:land 016, or "
     "/sdlc:ship 016 by hand"),
    ("landing", {"progress": {"kind": "land", "stopped": False, "step": "review"}},
     "the factory is landing it, at review: wait for it, or /sdlc-factory:land 016 if its "
     "session ended"),
    ("closed", {"stage": "shipped"}, "/sdlc:close 016"),
    ("stopped", {"stopped": {"next": "read runs/step.md, then rerun the build"}},
     "read runs/step.md, then rerun the build"),
    ("decision pending", {"stage": "build", "pending": ["D1"], "needs": ["decide D1"]},
     "decide D1 in the session running /sdlc-factory:build 016 (rerun it if that session ended)"),
    ("escalation pending",
     {"stage": "test", "decision": "ESCALATE", "needs": ["decide D2", "confirm 1 default"]},
     "/sdlc-factory:decide 016 for D2 and 1 default, then /sdlc:ship, or /sdlc-factory:land with "
     "the others ready"),
    ("defaults to confirm",
     {"stage": "test", "decision": "ESCALATE", "needs": ["confirm 2 defaults"]},
     "/sdlc-factory:decide 016 for 2 defaults, then /sdlc:ship, or /sdlc-factory:land with the "
     "others ready"),
    ("approver decided", {"stage": "test", "decision": "READY"},
     "/sdlc:ship, or /sdlc-factory:land with the others ready"),
    ("factory building", {"stage": "build", "mode": "factory", "built": [1]},
     "the factory is building it: wait for its decision"),
    ("red gate", {"gate": {"current": True, "verdict": "FAIL"}},
     "the gate is red: read build/gate.md, fix it, then sdlc.py gate 016"),
    ("its stage's step", {}, "plan mode, then build it"),
]  # fmt: skip

# The pairs whose step names both states (2026-11-17-57): a decision still waits while a file
# won't read, so the card says so, the decision first, as its `needs you:` line holds it.
BOTH = {
    ("problems", "decision pending"):
        "decide D1 in the session running /sdlc-factory:build 016 (rerun it if that session "
        "ended), and fix what its problems name",
    ("problems", "escalation pending"): "decide D2, and fix what its problems name",
    # 133: a landing stopped on a change already shipped is closed by hand, not shipped again.
    ("landing stopped", "closed"):
        "the landing stopped at gate: fix what it names, then /sdlc-factory:land 016, or "
        "/sdlc:close 016 by hand",
    ("escalation pending", "defaults to confirm"):
        "/sdlc-factory:decide 016 for 2 defaults, then /sdlc:ship, or /sdlc-factory:land with the "
        "others ready",
}  # fmt: skip


def _in_states(*states: dict) -> dict | None:
    """A card holding every state in `states`, or None when two set different stages."""
    entry = {"id": "016", "change": "016-draft-tags", "tier": 1, "stage": "plan",
             "mode": "manual", "problems": [], "needs": []}  # fmt: skip
    stages = {fields["stage"] for fields in states if "stage" in fields}
    if len(stages) > 1:
        return None
    for fields in states:
        for key, value in fields.items():
            entry[key] = entry[key] + value if key == "problems" else value
    return entry


@pytest.mark.portable
@pytest.mark.parametrize(
    "high, low",
    [(PRECEDENCE[i], PRECEDENCE[j]) for i in range(len(PRECEDENCE))
     for j in range(i, len(PRECEDENCE))],
    ids=lambda s: s[0],
)  # fmt: skip
def test_a_card_in_two_states_names_the_higher_ones_step(high, low) -> None:
    """Rounds 1 and 2 of 098 each found one more pair of states `next_action()` put in the
    wrong order: every pair that can overlap is pinned here, by the full text of its step."""
    entry = _in_states(high[1], low[1])
    if entry is None:
        pytest.skip(f"{high[0]} and {low[0]} set different stages")
    if high is not low and "progress" in high[1] and "progress" in low[1]:
        pytest.skip(f"{high[0]} and {low[0]} are two readings of one record")
    assert board.next_action(entry) == BOTH.get((high[0], low[0]), high[2])


@pytest.mark.portable
def test_a_card_with_a_problem_and_a_decision_names_both(repo) -> None:
    """2026-11-17-57: a `build` card with a reply that won't read and a blocking decision says
    the decision waits too, never only the problem."""
    four = _cards(repo)["004-draft-purge"]
    assert four["problems"] and four["needs"][-1] == "decide D1", four["needs"]
    assert four["next"] == (
        "decide D1 in the session running /sdlc-factory:build 004 (rerun it if that session "
        "ended), and fix what its problems name"
    )


@pytest.mark.portable
def test_an_escalation_names_the_decision_it_still_needs_first(repo) -> None:
    """2026-11-17-70: the next step follows the `needs you:` line, so an escalation that still
    needs `decide D2` names it before ship or land; one with nothing to decide names ship."""
    folder = _escalated(repo, "033-esc-open", "test", commit=["src/h.py"])
    _write(folder / "decisions.md", "# Decisions\n\n"
           "- [x] D1 (code round 1, default): page at 50 → decided: 50\n"
           "- [ ] D2 (builder round 1, blocking): keep drafts 30 days?\n")  # fmt: skip
    card = _cards(repo)["033-esc-open"]
    assert card["needs"] == ["decide D2"] and card["column"] == "needs-you"
    assert card["next"] == (
        "/sdlc-factory:decide 033 for D2, then /sdlc:ship, or /sdlc-factory:land with the others "
        "ready"
    )
    _write(folder / "decisions.md", TICKED)
    card = _cards(repo)["033-esc-open"]
    assert card["needs"] == [] and card["next"].startswith("/sdlc:ship")


@pytest.mark.portable
def test_a_decision_counts_on_the_track_only_at_its_stage(repo) -> None:
    """Nit 2026-11-17-22: a change put back to `build` with its `decision.md` still there shows
    the step its record names, not every step done; at `test` the decision is the run's end."""
    folder = _run_at(repo, "review")
    _write(folder / "decision.md", "DECISION: ESCALATE\n\nAsk them.\n")
    assert _states(_cards(repo)["016-draft-tags"]) == TRACKS["review"]
    intent = folder / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8").replace("stage: build", "stage: test"),
                      encoding="utf-8", newline="\n")  # fmt: skip
    assert _states(_cards(repo)["016-draft-tags"]) == ["done"] * 6


@pytest.mark.portable
def test_board_on_port_0_prints_the_port_it_bound(repo, capsys, monkeypatch) -> None:
    """The board half of 2026-11-17-19: the URL names the port the OS picked, never `:0`."""

    def stop(self, *args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(board._Server, "serve_forever", stop)
    assert board.cmd_board(repo, 0) == 0
    url = json.loads(capsys.readouterr().out)["url"]
    port = int(url.rstrip("/").rsplit(":", 1)[1])
    assert port > 0 and url == f"http://127.0.0.1:{port}/"


def test_a_change_being_rebased_keeps_its_card(repo) -> None:
    """2026-11-17-30: while a rebase stops in a change's worktree its HEAD is detached; the card
    stays, marked rebasing, its branch read from the rebase's own record, and reading it changes
    nothing in git."""
    name = "029-draft-rebase"
    folder = _worktree(repo, name, 1, "plan", commit=["src/rebase.py"])
    tree = sdlc.checkout_of(folder)
    _write(repo / "src" / "rebase.py", "main's own\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main moves")
    stopped = subprocess.run(["git", "-C", str(tree), "rebase", "main"], capture_output=True,
                             encoding="utf-8")  # fmt: skip
    assert stopped.returncode != 0 and _git(tree, "branch", "--show-current") == ""
    before = (_git(tree, "status", "--porcelain"), _git(tree, "rev-parse", "HEAD"))
    card = _cards(repo)[name]
    assert card["rebasing"] is True and card["problems"] == [], card
    assert card["next"] == (
        "a rebase is stopped in its worktree: resolve its conflicts, then "
        "sdlc.py resolve 029 --continue, or sdlc.py resolve 029 --abort, which keeps the "
        "resolved work under refs/sdlc/end/029-draft-rebase"
    ), "never ship or build mid-rebase; 2026-11-17-58: what --abort keeps, and where"
    assert _cards(repo)["001-reopen-drafts"]["rebasing"] is False
    assert name in [p.name for p in sdlc.change_dirs(repo)], "status finds it too"
    assert (_git(tree, "status", "--porcelain"), _git(tree, "rev-parse", "HEAD")) == before
    assert _git(tree, "branch", "--show-current") == "", "the rebase is still under way"
    _git(tree, "rebase", "--abort")
    assert _cards(repo)[name]["rebasing"] is False


def test_a_shipped_change_whose_landing_rebase_is_stopped_keeps_its_card(repo) -> None:
    """2026-11-18-32: a landing's rebase stopped on a conflict detaches the worktree's HEAD, so
    `ready_to_close()` no longer lists the shipped change; its card stays, rebasing, on the
    landing track at its rebase, and its files are still served."""
    folder = _landing_at(repo, "resolve")
    tree = sdlc.checkout_of(folder)
    _write(repo / "src" / "land.py", "main's own\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main moves")
    stopped = subprocess.run(["git", "-C", str(tree), "rebase", "main"], capture_output=True,
                             encoding="utf-8")  # fmt: skip
    assert stopped.returncode != 0 and _git(tree, "branch", "--show-current") == ""
    assert not sdlc.ready_to_close(repo), "the detached worktree is no longer listed"
    card = _cards(repo)["030-draft-land"]
    assert card["rebasing"] is True and card["stage"] == "shipped" and card["problems"] == []
    assert card["progress"]["kind"] == "land" and _states(card) == LANDS["resolve"]
    assert board.file_at(repo, "030-draft-land", "intent.md") is not None
    _git(tree, "rebase", "--abort")
    assert _cards(repo)["030-draft-land"]["rebasing"] is False


@pytest.mark.portable
def test_the_rebasing_badge_is_built_as_text() -> None:
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert re.search(
        r'c\.rebasing\s*\?\s*h\("span", \{ class: "badge rebasing" \}, "rebasing"\)', page
    )


def _touch_later(path: Path, text: str) -> None:
    """Write `path` and move its mtime on, so a filesystem with coarse times still sees a change."""
    before = path.stat().st_mtime_ns
    path.write_text(text, encoding="utf-8", newline="\n")
    later = max(before, path.stat().st_mtime_ns) + 2_000_000_000
    os.utime(path, ns=(later, later))


@pytest.mark.portable
def test_the_running_board_serves_board_py_as_it_is_on_disk(repo, tmp_path) -> None:
    """2026-11-17-47: a change to `board.py` reaches a board already running, with no restart;
    a `board.py` that won't load keeps the code it had, and the state says so."""
    scripts = tmp_path / "plugin" / "scripts"
    scripts.mkdir(parents=True)
    for name in ("board.py", "board.html"):
        (scripts / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    source = scripts / "board.py"
    original = source.read_text(encoding="utf-8")
    copy = board._load(source)
    server = copy.serve(repo, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/state.json"
    try:
        st = json.loads(_get(url)[1])
        assert "patched" not in st and "reload_error" not in st
        patch = (
            "\n_unpatched = state\n\n\n"
            "def state(root):\n    return _unpatched(root) | {'patched': True}\n"
        )
        _touch_later(source, original + patch)
        st = json.loads(_get(url)[1])
        assert st["patched"] is True and len(st["changes"]) == 4, "the edit is served"
        _touch_later(source, original[: len(original) // 2])
        code, body, _ = _get(url)
        st = json.loads(body)
        assert code == 200 and st["patched"] is True, "half a file: the old code serves on"
        assert "board.py" in st["reload_error"]
        assert "restart" not in st["reload_error"], "the next edit that loads is served"
        _touch_later(source, original)
        st = json.loads(_get(url)[1])
        assert "patched" not in st and "reload_error" not in st
        assert _get(url.replace("/state.json", "/"))[0] == 200
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.portable
def test_a_board_that_wont_reload_says_so_on_the_page() -> None:
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert re.search(r"st\.reload_error\s*\?", page)


FIXTURE = ROOT / "tests" / "fixtures" / "board"


@pytest.mark.portable
def test_the_board_fixture_stops_as_the_factory_writes() -> None:
    """120 (decision-1): the shots are rendered from the fixture, so each stop record in it is
    exactly what `stop_text()` writes now for its way and problems, never an older wording."""
    records = sorted((FIXTURE / "changes").glob(f"*/{factory.STOPPED}"))
    assert records, "the fixture holds a stopped run"
    for record in records:
        folder = record.parent.parent
        stop = sdlc.factory_stop(folder)
        assert stop, record
        want = factory.stop_text(folder.name, stop["way"], stop["problems"])
        assert record.read_text(encoding="utf-8") == want, folder.name


@pytest.mark.portable
def test_the_board_fixture_lands_as_the_factory_writes() -> None:
    """133: each landing record in the fixture is what `land_step_text()` writes for its fields."""
    records = sorted((FIXTURE / "changes").glob(f"*/{factory.LAND_STEP}"))
    assert records, "the fixture holds a landing"
    for record in records:
        text = record.read_text(encoding="utf-8")
        rec = factory.read_land_step(text)
        assert rec, record
        want = factory.land_step_text(rec, rec["since"] or "", rec["after"], rec["problems"])
        assert text == want, record


@pytest.mark.skipif(
    not all(shutil.which(tool) for tool in ("sh", "git", "uv")), reason="needs sh, git and uv"
)
def test_the_board_fixture_shows_every_card_state(tmp_path: Path, monkeypatch) -> None:
    """106 R13: the data the UI review's server shows holds a card in every column and each state
    a card can show, built by the fixture's own script, so a screenshot shows them all."""
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    repo = tmp_path / "repo"
    done = subprocess.run(
        ["sh", str(FIXTURE / "build.sh"), str(FIXTURE / "changes"), str(repo)],
        capture_output=True, encoding="utf-8", errors="replace",
    )  # fmt: skip
    assert done.returncode == 0, done.stdout + done.stderr
    cards = {c["change"]: c for c in board.state(repo)["changes"]}
    assert set(cards) == {p.name for p in (FIXTURE / "changes").iterdir() if p.is_dir()}
    columns = {c["column"] for c in cards.values()}
    assert columns == {"plan", "design", "build", "test", "ready", "close", "needs-you"}, columns
    factory_cards = [c for c in cards.values() if c["mode"] == "factory"]
    assert any(c.get("progress") and c["progress"]["steps"] for c in factory_cards), "a step track"
    assert any(c.get("stopped") for c in factory_cards), "a stopped run"
    landing = [c for c in factory_cards if (c.get("progress") or {}).get("kind") == "land"]
    assert any(c["column"] == "close" for c in landing), "a landing under way, tracked"
    assert any(c.get("pending") and c["column"] == "needs-you" for c in factory_cards)
    assert any(
        c["stage"] == "test" and c["decision"] == "ESCALATE" and c["column"] == "needs-you"
        for c in factory_cards
    ), "an escalated change at test"
    assert any(
        c["stage"] in ("shipped", "dropped") and c["decision"] == "ESCALATE" for c in factory_cards
    ), "a card that was ESCALATE"
    gates = {c["gate"]["verdict"] for c in cards.values() if (c.get("gate") or {}).get("current")}
    assert gates == {"PASS", "FAIL"}, "a green and a red gate badge"
    assert any(c["problems"] for c in cards.values()), "a file that won't read"
    assert _git(repo, "status", "--porcelain") == "", "the main checkout is left clean"


# ---------------------------------------------------------------- what each card needs (107)

TICKED = (
    "# Decisions\n\n"
    "- [x] D1 (code round 1, blocking): keep drafts 30 days? → decided: 30\n"
    "- [x] D2 (builder round 1, default): page at 50 → decided: 50\n"
    "- [x] R1 (person, restart): try the other store\n"
)


@pytest.mark.portable
def test_an_answered_escalation_is_ready_to_ship(repo) -> None:
    """R5: every ledger line ticked and no Reconsider section: Ready to ship, marked answered."""
    folder = _escalated(repo, "040-esc-done", "test", commit=["src/done.py"])
    _write(folder / "decisions.md", TICKED)
    card = _cards(repo)["040-esc-done"]
    assert (card["column"], card["needs"], card["answered"]) == ("ready", [], True)
    assert card["problems"] == [] and card["ledger_lines"] == 2, "R1 is no ledger line"
    _write(
        folder / "decisions.md",
        TICKED + "- [ ] D3 (approver, blocking): which store?\n"
        "- [ ] D4 (builder round 1, default): CSV\n- [ ] D5 (code round 1, default): UTC\n",
    )
    card = _cards(repo)["040-esc-done"]
    assert card["column"] == "needs-you" and card["answered"] is False
    assert card["needs"] == ["decide D3", "confirm 2 defaults"]
    _write(folder / "decisions.md", TICKED)
    _write(
        folder / "decision.md",
        "DECISION: ESCALATE\n\nOut of rounds.\n\n"
        "## Reconsider the approach\n\nThe store is wrong.\n",
    )
    card = _cards(repo)["040-esc-done"]
    assert (card["column"], card["needs"]) == ("needs-you", ["reconsider the approach"])
    assert card["answered"] is False


WEIGHED = (
    "# Decisions\n\n"
    "- [x] D1 (code round 1, default): log the draft id? → settled by the approver: spec R4\n"
    "- [ ] D2 (builder round 1, default): page at 50\n"
    "  - OPTION: 50 — one screen; a second page past it\n"
    "  - WHY: the list view shows 50\n"
)


@pytest.mark.portable
def test_a_ledger_with_alternatives_is_not_garbled(repo) -> None:
    """137 R2 on the board: the indented OPTION and WHY lines are no open box."""
    folder = _escalated(repo, "044-esc-weighed", "test", commit=["src/weighed.py"])
    _write(folder / "decisions.md", WEIGHED)
    card = _cards(repo)["044-esc-weighed"]
    assert card["problems"] == [] and card["needs"] == ["confirm 1 default"], card


@pytest.mark.portable
def test_an_escalation_with_only_settled_defaults_is_not_answered(repo) -> None:
    """137 R10 on the board: a settled line is no ledger line, so the escalation still needs
    reading."""
    folder = _escalated(repo, "045-esc-settled", "test", commit=["src/settled.py"])
    _write(folder / "decisions.md", WEIGHED.split("- [ ] D2")[0])
    card = _cards(repo)["045-esc-settled"]
    assert (card["ledger_lines"], card["answered"]) == (0, False), card
    assert card["needs"] == ["read the escalation"], card


@pytest.mark.portable
def test_a_malformed_open_line_keeps_the_escalation(repo) -> None:
    """R6: an open box the ledger can't read is a problem, never an answer."""
    folder = _escalated(repo, "041-esc-garbled", "test", commit=["src/garbled.py"])
    _write(folder / "decisions.md", TICKED + "- [ ] D3 which store, blocking?\n")
    card = _cards(repo)["041-esc-garbled"]
    line = "decisions.md: an open line that doesn't read as a decision"
    assert card["problems"] == [line] and card["column"] == "needs-you"
    assert card["needs"] == [f"fix: {line}"] and card["answered"] is False


@pytest.mark.portable
def test_a_written_spec_at_plan_needs_the_person(repo) -> None:
    """R7 on the board: a written spec whose stage never moved; a scaffold stays in Plan."""
    folder = _change(repo, "042-spec-written", 2, "plan", "Spec written")
    _write(folder / "spec.md", "# 042 — spec\n\n## Requirements\n\n1. It lists drafts.\n")
    scaffold = _change(repo, "043-spec-scaffold", 2, "plan", "Spec scaffold")
    _write(scaffold / "spec.md", "# 043 — spec\n\n<Numbered requirements.>\n<Design.>\n")
    cards = _cards(repo)
    assert (cards["042-spec-written"]["column"], cards["042-spec-written"]["needs"]) == (
        "needs-you",
        ["approve its spec"],
    )
    assert (cards["043-spec-scaffold"]["column"], cards["043-spec-scaffold"]["needs"]) == (
        "plan",
        [],
    )
    assert cards["003-draft-export"]["needs"] == [] and cards["003-draft-export"]["column"] == (
        "ready"
    ), "a READY with an unticked default is not the person's"


def _status(root: Path, monkeypatch, capsys) -> tuple[str, dict]:
    """`sdlc.py status` run in `root`: what it printed, and the records it printed from."""
    seen = {}
    real = sdlc.print_status

    def keep(a: dict) -> None:
        seen["a"] = a
        real(a)

    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "status"])
    monkeypatch.setattr(sdlc, "print_status", keep)
    capsys.readouterr()
    assert sdlc.main() == 0
    return capsys.readouterr().out, seen["a"]


def _needs_folders(root: Path) -> None:
    done = _escalated(root, "040-esc-done", "test", commit=["src/done.py"])
    _write(done / "decisions.md", TICKED)
    open_ = _escalated(root, "041-esc-open", "test", commit=["src/open.py"])
    _write(
        open_ / "decisions.md",
        TICKED + "- [ ] D3 (approver, blocking): which store?\n"
        "- [ ] D4 (builder round 1, default): CSV\n- [ ] D5 (code round 1, default): UTC\n",
    )
    _stopped_run(root)


@pytest.mark.portable
def test_status_ends_with_what_needs_me(repo, monkeypatch, capsys) -> None:
    """R11: the last section, one line per change with needs, as the board reads them."""
    _needs_folders(repo)
    out, a = _status(repo, monkeypatch, capsys)
    heads = [line for line in out.splitlines() if line.startswith("■ ")]
    assert heads[-1] == "■ What needs me" and heads[-2].startswith("■ Problems"), heads
    tail = out.split("■ What needs me\n", 1)[1].splitlines()
    assert tail == [
        "    004  decide D1",
        "    013  stopped: fix its cause and rerun",
        "    041  decide D3, confirm 2 defaults  /sdlc-factory:decide 041",
    ], tail
    assert "  · stopped, touched" in out and "→ " in out, "the stop's own lines stay"
    cards = _cards(repo)
    for rec in a["open"]:
        card = cards[f"{rec['id']}-{rec['slug']}"]
        # A problem only the board reads (a reply with no VERDICT) is the board's alone.
        assert rec["needs"] == [n for n in card["needs"] if not n.startswith("fix: ")], rec["id"]
        assert rec["answered"] == card["answered"], rec["id"]
    assert {r["id"]: r["answered"] for r in a["open"]}["040"] is True


@pytest.mark.portable
def test_status_says_nothing_needs_me_when_nothing_does(tmp_path, monkeypatch, capsys) -> None:
    root = tmp_path / "quiet"
    root.mkdir()
    _write(root / "README.md", "a repo\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _change(root, "001-reopen-drafts", 1, "plan", "Reopen drafts")
    out, _ = _status(root, monkeypatch, capsys)
    assert out.rstrip().endswith("■ What needs me\n    nothing"), out[-200:]


@pytest.mark.portable
def test_status_records_only_gain_keys(repo, monkeypatch, capsys) -> None:
    """R12: each open record gains `needs` and `answered`, and every other key stays as it was."""
    _needs_folders(repo)
    before = {r["dir"]: set(r) for r in sdlc.analyze(repo)["open"]}
    _, a = _status(repo, monkeypatch, capsys)
    dispatch = {"behind", "touched_ago", "quiet", "stopped", "gate"}
    for rec in a["open"]:
        assert set(rec) == before[rec["dir"]] | dispatch | {"needs", "answered"}, rec["dir"]
        assert isinstance(rec["needs"], list) and isinstance(rec["answered"], bool)


@pytest.mark.portable
def test_status_reads_a_malformed_open_line_as_a_problem(repo, monkeypatch, capsys) -> None:
    """R6 in status: the escalation stays the person's."""
    folder = _escalated(repo, "041-esc-garbled", "test", commit=["src/garbled.py"])
    _write(folder / "decisions.md", TICKED + "- [ ] D3 which store, blocking?\n")
    out, a = _status(repo, monkeypatch, capsys)
    rec = next(r for r in a["open"] if r["id"] == "041")
    line = "decisions.md: an open line that doesn't read as a decision"
    assert rec["needs"] == [f"fix: {line}"] and rec["answered"] is False
    assert f"    041  fix: {line}" in out


@pytest.mark.portable
def test_a_needs_card_names_what_it_needs() -> None:
    """R10: a line above `next:` names the needs, and an answered escalation is badged, as text."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    _, script = _page_parts()
    body = re.search(r"function card\(c\) \{(.*?)\n\}", script, re.S).group(1)
    line = 'h("div", { class: "needs" }, `needs you: ${c.needs.join(" · ")}`)'
    assert line in body, "built with h(), its text a string"
    assert body.index(line) < body.index('h("div", { class: "next" }'), "above next:"
    badge = 'c.answered ? h("span", { class: "badge answered" }, "escalated: answered")'
    assert badge in body
    assert '"the approver escalated it to you"' in body and "waits on you: ${d.text}" in body
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML"):
        assert sink not in page, sink
    assert '{ key: "needs-you", label: "Needs you", who: "what each card says it needs" }' in script


@pytest.mark.portable
def test_the_render_key_holds_what_is_shown() -> None:
    """R13 (2026-11-17-50): a poll rebuilds the board only when what a person sees changes, so
    the key holds seconds as the page renders them, never raw."""
    _, script = _page_parts()
    keys = re.findall(r"JSON\.stringify\(([^)]*\]?[^)]*)\)", script)
    assert keys == ["[NARROW.matches, st.changes], shownAs"], keys
    shown = re.search(r"function shownAs\(k, v\) \{(.*?)\n\}", script, re.S)
    assert shown, "the replacer"
    body = shown.group(1)
    assert re.search(r'k === "touched_ago"\) return ago\(v\)', body)
    assert re.search(r'k === "elapsed"\)[^\n]*dur\(v\)', body)
    assert re.search(r'k === "fraction"\)[^\n]*Math\.round\(v \* 100\)', body)
    assert "Math.round(p.fraction * 100)" in script, "the same percent the bar draws"


@pytest.mark.portable
def test_a_rebuild_puts_focus_back() -> None:
    """R14: the card that held focus gets it back after a rebuild, unless the drawer is open."""
    _, script = _page_parts()
    render = re.search(r"function render\(st\) \{(.*?)\n\}", script, re.S).group(1)
    held = render.index("document.activeElement")
    swap = render.index('$("board").replaceChildren(')
    back = re.search(r'querySelector\(`\[data-change="\$\{CSS\.escape\(held\)\}"\]`\)', render)
    assert held < swap < back.start(), "read before, restored after"
    assert re.search(r"if \(held && !open\)", render), "an open drawer keeps its focus"
    # `open` there is the drawer's: a local of that name in render() is read before it is set,
    # and throws whenever a card holds focus (107 round 1).
    assert not re.search(r"\b(const|let|var)\s+open\b", render), "render() shadows `open`"
    assert re.search(r"^let open = null;$", script, re.M), "the drawer's, at module level"
    assert ".focus()" in render[swap:]


@pytest.mark.portable
def test_aria_live_sits_on_the_status_line_alone() -> None:
    """R15: a screen reader hears the board connect, drop, or its Needs you count change, never
    the whole board each poll, nor the time."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    live = re.findall(r"<[^>]*aria-live[^>]*>", page)
    assert live == ['<span class="status" id="status" aria-live="polite">'], live
    assert '<main class="board" id="board">' in page
    assert re.search(r'<span class="status" id="polled"></span>', page)
    _, script = _page_parts()
    assert "toLocaleTimeString()" in script
    for line in script.splitlines():
        if "toLocaleTimeString()" in line:
            assert '$("polled")' in line and '$("status")' not in line, line
    say = re.search(r"function say\(text, down\) \{(.*?)\n\}", script, re.S)
    assert say and '$("status").textContent !== text' in say.group(1), "set only when it changes"
    assert re.search(r"`live · \$\{need\} need", script)


@pytest.mark.portable
def test_a_column_subtitle_sits_under_its_heading() -> None:
    """2026-11-17-52: the column head is two rows, CSS alone, at every width: the heading and its
    count on the first, the `who` subtitle on a row of its own under the heading, so a wrapped
    subtitle never sits indented beside a one-line title."""
    css, script = _page_parts()

    def rule(selector: str) -> re.Match:
        return re.search(rf"(?m)^{re.escape(selector)} \{{([^}}]*)\}}", css)

    head = rule(".col-head").group(1)
    assert re.search(r"display:\s*grid", head) and "flex" not in head, head
    assert re.search(r"grid-template-columns:\s*1fr auto", head), head
    who = rule(".col-head .who").group(1)
    assert re.search(r"grid-column:\s*1 / -1", who) and re.search(r"grid-row:\s*2", who), who
    count = rule(".col-head .count").group(1)
    assert re.search(r"grid-row:\s*1", count) and "margin-left" not in count, count
    assert 'h("h2", {}, col.label), h("span", { class: "who" }, col.who)' in script, "DOM order"


@pytest.mark.portable
def test_an_empty_column_says_so() -> None:
    """2026-11-17-56: an empty column says in words that nothing waits there, never a bare dash."""
    _, script = _page_parts()
    assert 'h("div", { class: "empty" }, "nothing waiting here")' in script
    assert 'class: "empty" }, "—"' not in script


# ---------------------------------------------------------------- the drawer's markdown (124)

# A stand-in DOM, just what `h()` and the markdown section call, whose tree reads back as JSON.
_FAKE_DOM = r"""
class Node {}
class Text extends Node {
  constructor(t) { super(); this.text = String(t); }
  toJSON() { return this.text; }
}
class El extends Node {
  constructor(tag) { super(); this.tag = tag; this.attrs = {}; this.kids = []; }
  get tagName() { return this.tag.toUpperCase(); }
  get childNodes() { return this.kids; }
  set className(v) { this.attrs.class = v; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  append(...ns) { for (const n of ns) this.kids.push(n instanceof Node ? n : new Text(n)); }
  set textContent(v) { this.kids = [new Text(v)]; }
  toJSON() { return { tag: this.tag, attrs: this.attrs, kids: this.kids }; }
}
const document = { createElement: (t) => new El(t), createTextNode: (t) => new Text(t) };
"""


def _render_markdown(text: str, base: str, files: list[str]) -> list:
    """`renderMarkdown()` as the page has it, run under node over a stand-in DOM."""
    _, script = _page_parts()
    helper = re.search(r"^function h\(tag, attrs, \.\.\.children\) \{.*?^\}$", script, re.S | re.M)
    section = re.search(r"^// ---- markdown\b.*?^// ---- end markdown$", script, re.S | re.M)
    assert helper and section, "h() and the page's markdown section"
    program = "\n".join(
        [
            '"use strict";',
            _FAKE_DOM,
            helper.group(0),
            section.group(0),
            "const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));",
            "process.stdout.write(JSON.stringify(renderMarkdown(input.text, input.ctx)));",
        ]
    )
    out = subprocess.run(
        ["node", "-e", program],
        input=json.dumps({"text": text, "ctx": {"base": base, "files": files}}),
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(out.stdout)


def _nodes(tree, tag: str | None = None) -> list[dict]:
    found = []
    for n in tree if isinstance(tree, list) else [tree]:
        if isinstance(n, dict):
            if tag is None or n["tag"] == tag:
                found.append(n)
            found += _nodes(n["kids"], tag)
    return found


def _text(tree) -> str:
    if isinstance(tree, str):
        return tree
    if isinstance(tree, list):
        return "".join(_text(n) for n in tree)
    return _text(tree["kids"])


needs_node = pytest.mark.skipif(
    not shutil.which("node"), reason="needs node to run the page's script"
)

MARKDOWN = """\
---
id: 005
stage: build
---

# 005 — Share drafts

A draft is **shared** by *link*, with `share()` and __bold__ and _em_ but snake_case_name.
Its second line ~~was~~ joins the paragraph.

## Outcome

- one
- two, wrapped
  onto a second line
  - nested
- [x] done
- [ ] not yet

1. first
2. second

> quoted **text**

```python
print("<b>not bold</b>")
```

| Role | Verdict |
| --- | --- |
| code | PASS |

See [the spec](../../spec.md), [the site](https://example.com/a), [nothing](missing.md).

<!-- a comment the template left -->

---
"""


@needs_node
def test_the_drawer_renders_markdown_as_nodes() -> None:
    """124: a `.md` file in the drawer reads as a document, every construct its own node."""
    tree = _render_markdown(
        MARKDOWN, "reviews/round-1/code.md", ["spec.md", "reviews/round-1/code.md"]
    )
    front = _nodes(tree, "pre")[0]
    assert front["attrs"]["class"] == "md-front" and _text(front) == "id: 005\nstage: build"
    heads = [(n["tag"], _text(n)) for n in _nodes(tree) if re.fullmatch(r"h[4-6]", n["tag"])]
    assert heads == [("h4", "005 — Share drafts"), ("h5", "Outcome")]
    para = _nodes(tree, "p")[0]
    assert _text(para).endswith("snake_case_name. Its second line was joins the paragraph.")
    assert [_text(n) for n in _nodes(para, "strong")] == ["shared", "bold"]
    assert [_text(n) for n in _nodes(para, "em")] == ["link", "em"]
    assert [_text(n) for n in _nodes(para, "code")] == ["share()"]
    assert [_text(n) for n in _nodes(para, "del")] == ["was"]
    ul = _nodes(tree, "ul")[0]
    items = [n for n in ul["kids"] if isinstance(n, dict)]
    assert len(items) == 4
    assert _text(items[1]).startswith("two, wrapped onto a second line")
    assert [_text(n) for n in _nodes(items[1]["kids"], "li")] == ["nested"]
    boxes = _nodes(ul, "input")
    assert [b["attrs"].get("checked") for b in boxes] == ["", None]
    assert all(b["attrs"]["type"] == "checkbox" and "disabled" in b["attrs"] for b in boxes)
    # A task's box sits in a label holding its text, so a screen reader names it.
    labels = _nodes(ul, "label")
    assert [_text(n) for n in labels] == ["done", "not yet"]
    assert all(_nodes(n, "input") for n in labels)
    assert [_text(n) for n in _nodes(_nodes(tree, "ol")[0], "li")] == ["first", "second"]
    quote = _nodes(tree, "blockquote")[0]
    assert _text(quote) == "quoted text" and _nodes(quote, "strong")
    code = next(n for n in _nodes(tree, "pre") if n["attrs"].get("class") == "md-code")
    assert _text(code) == 'print("<b>not bold</b>")' and _nodes(code, "code")
    table = next(n for n in _nodes(tree, "div") if n["attrs"].get("class") == "md-table")
    for box, name in ((code, "code"), (table, "table")):
        # A box that scrolls sideways is a named tab stop, so a keyboard can scroll it.
        assert box["attrs"]["tabindex"] == "0" and box["attrs"]["role"] == "region", box["attrs"]
        assert box["attrs"]["aria-label"] == name
    assert [_text(n) for n in _nodes(tree, "th")] == ["Role", "Verdict"]
    assert [_text(n) for n in _nodes(tree, "td")] == ["code", "PASS"]
    links = {_text(a): a["attrs"] for a in _nodes(tree, "a")}
    assert links["the spec"]["data-path"] == "spec.md", "a file of the change opens in the drawer"
    assert links["the site"] == {
        "href": "https://example.com/a",
        "target": "_blank",
        "rel": "noopener noreferrer",
    }
    assert "nothing" not in links and "nothing" in _text(tree), "a file it lacks is text"
    assert "a comment the template left" not in _text(tree)
    assert _nodes(tree, "hr")


@pytest.mark.portable
def test_a_rendered_heading_never_outranks_the_drawer_title() -> None:
    """124: a file's `# ` heading is never larger than the drawer's title."""
    style, _ = _page_parts()

    def px(selector: str) -> float:
        rule = re.search(re.escape(selector) + r"\s*\{[^}]*?font-size:\s*([\d.]+)px", style)
        assert rule, selector
        return float(rule.group(1))

    title = px(".d-head h3")
    sizes = [px(f".md .md-h{n}") for n in (1, 2, 3)]
    assert all(size <= title for size in sizes), (title, sizes)
    assert sizes == sorted(sizes, reverse=True), "each level no larger than the one above it"


@needs_node
def test_markdown_holding_markup_shows_it_as_text() -> None:
    """124: nothing in a change's file is parsed as HTML, and no link runs or leaves the change
    but to the web."""
    hostile = (
        "<script>alert(1)</script>\n\n"
        "<img src=x onerror=alert(2)>\n\n"
        "[run](javascript:alert(3)) [data](data:text/html,x) [up](../../../etc/passwd) "
        "[abs](/etc/passwd) [**bold** `code`](JavaScript:alert(4))\n"
    )
    tree = _render_markdown(hostile, "intent.md", ["intent.md"])
    tags = {n["tag"] for n in _nodes(tree)}
    assert tags <= {"p", "strong", "code", "span"}, tags
    assert "<script>alert(1)</script>" in _text(tree)
    assert "<img src=x onerror=alert(2)>" in _text(tree)
    assert not _nodes(tree, "a"), "every one of those links is refused"
    for n in _nodes(tree):
        assert not any(k.startswith("on") or k in ("href", "src", "style") for k in n["attrs"]), n
    assert "run" in _text(tree) and "bold" in _text(tree)


@pytest.mark.portable
def test_only_a_markdown_file_is_rendered() -> None:
    """124: `.md` shows rendered, unless the person asks for its raw text; every other file shows
    in the `pre` as before; code and tables scroll inside themselves at any width."""
    css, script = _page_parts()
    paint = re.search(r"function paint\(\) \{(.*?)\n\}", script, re.S)
    assert paint, "paint() draws the file the drawer holds"
    body = paint.group(1)
    assert re.search(r"/\\\.md\$/i\.test\(", body), "a path ending .md, and nothing else"
    assert "renderMarkdown(" in body and 'h("pre", {}, ' in body
    assert '$("d-doc").replaceChildren(' in body
    show = re.search(r"async function show\(change, path\) \{(.*?)\n\}", script, re.S).group(1)
    assert "paint()" in show and "renderMarkdown" not in show
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    drawer = re.search(r'<aside class="drawer".*?</aside>', page, re.S).group(0)
    assert re.search(r'<button[^>]*id="d-raw"[^>]*aria-pressed="false"', drawer), "the raw toggle"
    assert '<div id="d-doc"></div>' in drawer

    def rule(selector: str) -> str:
        return re.search(rf"(?m)^{re.escape(selector)} \{{([^}}]*)\}}", css).group(1)

    assert "overflow-x: auto" in rule(".md pre.md-code") and "white-space: pre" in rule(
        ".md pre.md-code"
    )
    assert "overflow-x: auto" in rule(".md .md-table")


@pytest.mark.portable
def test_the_focus_trap_skips_a_hidden_node() -> None:
    """124 R1: the Raw toggle is hidden for any file but `.md`, and a hidden node can't take
    focus, so the trap's cycle leaves out every node a `[hidden]` holds."""
    _, script = _page_parts()
    trap = re.search(r"function trapTab\(e\) \{(.*?)\n\}", script, re.S).group(1)
    assert re.search(
        r'querySelectorAll\(FOCUSABLE\)\]\.filter\(\(n\) => !n\.closest\("\[hidden\]"\)\)', trap
    )
    css, _ = _page_parts()
    assert re.search(
        r"(?m)^\.md \.md-table:focus-visible, \.md pre\.md-code:focus-visible \{[^}]*outline", css
    )


# ---------------------------------------------------------------- the landing's track (133)


def _landing_at(
    root: Path,
    step: str,
    stage: str = "shipped",
    rnd: int | None = 1,
    moves: int = 1,
    since: str = "2000-01-01T00:00:00Z",
    after: str | None = None,
    problems: tuple[str, ...] = (),
    name: str = "030-draft-land",
) -> Path:
    """A factory change the approver passed, landing: its record written by `factory.py`'s own
    writer, at `stage` (`test` before its commit, `shipped` after)."""
    folder = _worktree(root, name, 1, stage, commit=["src/land.py"], factory=True)
    _write(folder / "build" / "round-1.md", "Built.\n")
    _write(folder / "reviews" / "round-1" / "code.md", "VERDICT: PASS\n")
    _write(folder / "decision.md", "DECISION: READY\n\nIt does what it says.\n")
    out = {"step": step, "round": rnd, "moves": moves, "limit": 3}
    _write(folder / factory.LAND_STEP, factory.land_step_text(out, since, after, list(problems)))
    return folder


LANDS = {
    "checks": ["current", "todo", "todo", "todo", "todo", "todo"],
    "cases": ["current", "todo", "todo", "todo", "todo", "todo"],
    "ship": ["current", "todo", "todo", "todo", "todo", "todo"],
    "rebase": ["done", "current", "todo", "todo", "todo", "todo"],
    "resolve": ["done", "current", "todo", "todo", "todo", "todo"],
    "fix": ["done", "current", "todo", "todo", "todo", "todo"],
    "gate": ["done", "done", "current", "todo", "todo", "todo"],
    "review": ["done", "done", "done", "current", "todo", "todo"],
    "mend": ["done", "done", "done", "current", "todo", "todo"],
    "verify": ["done", "done", "done", "done", "current", "todo"],
    "close": ["done", "done", "done", "done", "done", "current"],
    # 139: a train's steps. `stack` sits at the rebase; `eject` is a stop, at the gate when the
    # record names no step it stopped after.
    "stack": ["done", "current", "todo", "todo", "todo", "todo"],
    "eject": ["done", "done", "stopped", "todo", "todo", "todo"],
}
LABELS = {"resolve": ("rebase", "resolving"), "fix": ("rebase", "fixing"),
          "mend": ("review", "mending"), "stack": ("rebase", "stacking"),
          "checks": ("ship", "checks"), "cases": ("ship", "cases")}  # fmt: skip
STOPS = ("eject",)


@pytest.mark.portable
@pytest.mark.parametrize("step", list(LANDS))
def test_a_landing_card_shows_its_landing_track(repo, step) -> None:
    """133: a change landing shows the landing's track, its step current, with its round and the
    moves followed out of the bound, where it sits: Ready to close once committed."""
    assert set(LANDS) == set(factory.LAND_STEPS), "every step the factory records"
    _landing_at(repo, step)
    card = _cards(repo)["030-draft-land"]
    progress = card["progress"]
    assert progress["kind"] == "land" and progress["step"] == step
    assert [s["name"] for s in progress["steps"]] == list(board.LAND_TRACK)
    assert [s["state"] for s in progress["steps"]] == LANDS[step]
    assert (progress["round"], progress["moves"], progress["limit"]) == (1, 1, 3)
    if step in STOPS:
        assert progress["stopped"] is True and progress["elapsed"] is None
    else:
        assert progress["elapsed"] > 0 and progress["problems"] == []
    labels = {s["name"]: s["label"] for s in progress["steps"]}
    if step in LABELS:
        assert labels[LABELS[step][0]] == LABELS[step][1]
    # 141: a stopped landing (a train's ejection too) needs the person; else it waits on close.
    assert card["column"] == ("needs-you" if step in STOPS else "close"), step
    assert progress["plan"] is None


@pytest.mark.portable
def test_a_landing_from_ready_to_ship_is_tracked_there(repo) -> None:
    """133: a landing at its first step, before its commit, shows in Ready to ship."""
    _landing_at(repo, "ship", stage="test", rnd=None, moves=0)
    card = _cards(repo)["030-draft-land"]
    assert card["column"] == "ready" and card["progress"]["kind"] == "land"
    assert card["progress"]["round"] is None and LANDS["ship"] == [
        s["state"] for s in card["progress"]["steps"]
    ]


@pytest.mark.portable
def test_a_stopped_landing_shows_why_on_its_card(repo) -> None:
    """133: a stop is not `done`: the step it stopped after is marked stopped, its problems with
    it, and no time runs."""
    why = "the gate failed on the change as rebased (exit 1), in build/land-1.gate.md"
    _landing_at(repo, "stop", after="gate", problems=(why,))
    progress = _cards(repo)["030-draft-land"]["progress"]
    assert [s["state"] for s in progress["steps"]] == [
        "done", "done", "stopped", "todo", "todo", "todo",
    ]  # fmt: skip
    assert progress["problems"] == [why] and progress["elapsed"] is None
    assert progress["stopped"] is True


@pytest.mark.portable
def test_a_landing_record_counts_only_at_a_landing_stage(repo) -> None:
    """133: at `build` the build's record is the track; with no landing record, a decision at
    `test` is every step of the build done, as before; a garbled one is a problem."""
    folder = _run_at(repo, "review")
    out = {"step": "close", "round": 1, "moves": 0, "limit": 3}
    _write(folder / factory.LAND_STEP, factory.land_step_text(out, "2026-11-18T10:00:00Z"))
    assert _cards(repo)["016-draft-tags"]["progress"]["kind"] == "build"
    assert _states(_cards(repo)["016-draft-tags"]) == TRACKS["review"]
    assert _states(_cards(repo)["003-draft-export"]) == ["done"] * 6
    landing = _landing_at(repo, "gate")
    _write(landing / factory.LAND_STEP, "landing, probably\n")
    card = _cards(repo)["030-draft-land"]
    assert card["progress"] is None
    assert any(factory.LAND_STEP.as_posix() in p for p in card["problems"]), card["problems"]


@pytest.mark.portable
def test_the_landing_step_record_is_a_pinned_copy() -> None:
    """133: the board's copies are `factory.py`'s, and its writer reads back through the board."""
    for name in ("MOVES_RE", "PROBLEM_RE", "TRAIN_RE"):
        assert getattr(board, name).pattern == getattr(factory, name).pattern, name
    assert board.LAND_STEP == factory.LAND_STEP
    assert set(board.LAND_AT) == set(factory.LAND_STEPS)
    for out, after, problems in (
        ({"step": "review", "round": 2, "moves": 1, "limit": 3}, None, []),
        ({"step": "stop", "round": None, "moves": 0, "limit": 2}, "ship", ["it broke"]),
        ({"step": "stack", "round": 1, "moves": 0, "limit": 3, "train": {"k": 2, "n": 3}}, None,
         []),
        ({"step": "eject", "round": 1, "moves": 0, "limit": 3, "train": {"k": 2, "n": 3}}, "gate",
         ["ejected from the train: the gate failed"]),
    ):  # fmt: skip
        text = factory.land_step_text(out, "2026-11-18T10:00:00Z", after, problems)
        assert board.read_land_step(text) == factory.read_land_step(text)
        assert board.read_land_step(text)["train"] == out.get("train")


@pytest.mark.portable
def test_a_train_member_shows_its_place_and_an_ejection(repo) -> None:
    """139 R18: a change in a train shows `k of n in a train`, `stack` at the rebase position as
    stacking, and `eject` as a stop at the step it stopped after, with its reason."""
    folder = _landing_at(repo, "stack")
    out = {"step": "stack", "round": 1, "moves": 0, "limit": 3, "train": {"k": 2, "n": 3}}
    _write(folder / factory.LAND_STEP, factory.land_step_text(out, "2000-01-01T00:00:00Z"))
    progress = _cards(repo)["030-draft-land"]["progress"]
    assert progress["train"] == "2 of 3" and progress["stopped"] is False
    assert [s["state"] for s in progress["steps"]] == LANDS["stack"]
    assert {s["name"]: s["label"] for s in progress["steps"]}["rebase"] == "stacking"
    why = "ejected from the train: the gate failed on the stack up to 030-draft-land (exit 1)"
    out = {"step": "eject", "round": 1, "moves": 0, "limit": 3, "train": {"k": 2, "n": 3}}
    _write(folder / factory.LAND_STEP,
           factory.land_step_text(out, "2000-01-01T00:00:00Z", "gate", [why]))  # fmt: skip
    card = _cards(repo)["030-draft-land"]
    progress = card["progress"]
    assert progress["stopped"] is True and progress["after"] == "gate"
    assert [s["state"] for s in progress["steps"]] == ["done", "done", "stopped", "todo", "todo",
                                                      "todo"]  # fmt: skip
    assert progress["problems"] == [why] and progress["train"] == "2 of 3"
    assert "the landing stopped at gate" in card["next"], card["next"]
    # `status` reads the eject as the board does, so the two never disagree on it.
    stop = sdlc.factory_land_stop(folder)
    assert stop == card["land_stop"] == {"after": "gate", "problems": [why]}, "as status reads it"
    assert (
        "landing stopped at gate"
        in sdlc.needs_of({"stage": "test", "decision": None, "land_stop": stop})
        and card["column"] == "needs-you"
    ), card
    html = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert "in a train" in html and "p.train" in html, "the page shows the place"
    _landing_at(repo, "gate", name="031-draft-plain")
    assert _cards(repo)["031-draft-plain"]["progress"]["train"] is None


@pytest.mark.portable
def test_landing_typical_times_come_from_closed_factory_runs(repo) -> None:
    """133: the rows after the approver are the landing's: its reviews and verifications, and its
    gate from `build/land-<n>.gate.md`; a landing step is timed against them."""
    rows = [*RUN[:-2], _row("behaviour", 90), _row("verifier", 30), _row("code", 70)]
    for name in ("060-draft-a", "061-draft-b", "062-draft-c"):
        _closed(repo, name, 1, rows, land_gates=(40.0,))
    samples = board.history_samples(repo, "main")
    assert samples[("land-review", 1)]["060-draft-a"] == [90, 70]
    assert samples[("land-verify", 1)]["060-draft-a"] == [30]
    assert samples[("land-gate", 1)]["060-draft-a"] == [40.0]
    assert samples[("approve", 1)]["060-draft-a"] == [15]
    table = board.typical_times(repo, "main")
    assert table["land-gate/1"] == {"seconds": 40, "samples": 3}
    _landing_at(repo, "gate", since="2000-01-01T00:00:00Z")
    progress = _cards(repo)["030-draft-land"]["progress"]
    assert (progress["typical"], progress["fraction"], progress["samples"]) == (40, 0.95, 3)


@pytest.mark.portable
def test_rounds_are_labelled_b_and_landings_l() -> None:
    """2026-11-18-38: the page labels build rounds `B1`, `B2` (never `R`, a requirement's or the
    ledger's letter) and landing rounds `L1`: display labels only, no file is named otherwise."""
    script = _page_parts()[1]
    rounds = re.search(r"function roundRow\(r\) \{(.*?)\n\}", script, re.S).group(1)
    assert "`B${r.round}`" in rounds and "R${" not in rounds
    row = re.search(r"function progressRow\(p\) \{(.*?)\n\}", script, re.S).group(1)
    assert "`B${p.round}" in row and "L${p.round}" in row and "R${" not in row
    assert "R${" not in script, "no round label reads R anywhere on the page"


@pytest.mark.portable
def test_the_page_labels_a_landing_track_and_says_why_it_stopped() -> None:
    """133: a landing's row names itself and its round, the moves it followed out of its bound,
    and each problem of a stop as a flag, in text."""
    script = _page_parts()[1]
    row = re.search(r"function progressRow\(p\) \{(.*?)\n\}", script, re.S).group(1)
    assert 'p.kind === "land"' in row and "`landing${" in row
    assert "base moved ${p.moves} of" in row
    assert re.search(r'for \(const why of p\.problems \|\| \[\]\).*"flag".*landing stopped', row)


@pytest.mark.portable
def test_a_landing_card_names_the_landing_not_close(repo) -> None:
    """133 round 1: a landing under way, before or after its commit, names the landing as its next
    step, never the hand-run close or ship; a stopped one names the way on, close by hand for a
    change already shipped, and no landing record leaves close as it was."""
    folder = _landing_at(repo, "review")
    card = _cards(repo)["030-draft-land"]
    assert card["next"] == (
        "the factory is landing it, at review: wait for it, or /sdlc-factory:land 030 if its "
        "session ended"
    )
    why = "its commit failed: the landing's output gives git's words; rerun it once fixed"
    out = {"step": "stop", "round": 1, "moves": 0, "limit": 3}
    _write(folder / factory.LAND_STEP, factory.land_step_text(out, "", "ship", [why]))
    card = _cards(repo)["030-draft-land"]
    assert card["progress"]["after"] == "ship" and card["progress"]["problems"] == [why]
    assert card["next"] == (
        "the landing stopped at ship: fix what it names, then /sdlc-factory:land 030, or "
        "/sdlc:close 030 by hand"
    ), "a shipped change is closed by hand, never shipped again"
    (folder / factory.LAND_STEP).unlink()
    assert _cards(repo)["030-draft-land"]["next"] == "/sdlc:close 030"


@pytest.mark.portable
def test_a_stopped_landing_is_in_needs_you(repo) -> None:
    """2026-11-18-17: a landing that stopped moves its card to Needs you, before its commit and
    after, its `needs you:` line naming the step it stopped after, and its next step the way on
    (2026-11-18-19: `/sdlc:close` by hand on a shipped card, `/sdlc:ship` before). The page needs
    no look of its own for it: the column's is the stop's."""
    why = "sdlc.py close failed: run /sdlc:close 030 by hand to see why"
    folder = _landing_at(repo, "stop", after="close", problems=(why,))
    card = _cards(repo)["030-draft-land"]
    assert (card["column"], card["needs"]) == ("needs-you", ["landing stopped at close"]), card
    assert card["land_stop"] == {"after": "close", "problems": [why]}
    assert card["next"] == (
        "the landing stopped at close: fix what it names, then /sdlc-factory:land 030, or "
        "/sdlc:close 030 by hand"
    )
    assert sdlc.factory_land_stop(folder) == card["land_stop"], "as status reads it"
    _landing_at(repo, "stop", stage="test", after="ship", problems=("it broke",),
                name="031-draft-early")  # fmt: skip
    card = _cards(repo)["031-draft-early"]
    assert (card["column"], card["needs"]) == ("needs-you", ["landing stopped at ship"]), card
    assert card["next"].endswith("/sdlc-factory:land 031, or /sdlc:ship 031 by hand")
    running = _cards(repo)
    _landing_at(repo, "review", name="032-draft-running")
    card = _cards(repo)["032-draft-running"]
    assert (card["column"], card["needs"], card["land_stop"]) == ("close", [], None)
    assert running, "a landing under way keeps its column"
    css, script = _page_parts()
    assert "landing-stopped" not in css and "landing-stopped" not in script
    assert re.search(r'key: "close", label: "Ready to close", who: "[^"]*landing', script)


@pytest.mark.portable
def test_the_landing_stop_is_read_as_status_reads_it(repo) -> None:
    """141: `sdlc.py`'s reading of a stop in `runs/land-step.md` is a pinned copy of the factory's,
    None for a landing under way or no record, and never raises on one that won't read."""
    assert sdlc.FACTORY_LAND_STEP == factory.LAND_STEP
    assert sdlc.FACTORY_AFTER_RE.pattern == factory.AFTER_RE.pattern
    assert sdlc.FACTORY_LAND_STOPS == board.LAND_STOPS, "a stop to the board is one to status"
    folder = _landing_at(repo, "stop", after="gate", problems=("the gate failed", "exit 1"))
    assert sdlc.factory_land_stop(folder) == {"after": "gate", "problems": ["the gate failed",
                                                                            "exit 1"]}  # fmt: skip
    out = {"step": "verify", "round": 1, "moves": 0, "limit": 3}
    _write(folder / factory.LAND_STEP, factory.land_step_text(out, "2026-11-18T10:00:00Z"))
    assert sdlc.factory_land_stop(folder) is None
    _write(folder / factory.LAND_STEP, "landing, probably\n")
    assert sdlc.factory_land_stop(folder) is None
    (folder / factory.LAND_STEP).unlink()
    assert sdlc.factory_land_stop(folder) is None


@pytest.mark.portable
def test_status_lists_a_stopped_landing_under_what_needs_me(repo, monkeypatch, capsys) -> None:
    """141: `status` reads the landing's stop as the board does: a shipped change whose landing
    stopped is marked on its Ready to close line and listed under `■ What needs me`, as is one
    stopped before its commit; a landing under way is neither."""
    why = "sdlc.py close failed: run /sdlc:close 030 by hand to see why"
    _landing_at(repo, "stop", after="close", problems=(why,))
    _landing_at(repo, "stop", stage="test", after="ship", problems=("it broke",),
                name="031-draft-early")  # fmt: skip
    _landing_at(repo, "review", name="032-draft-running")
    out, a = _status(repo, monkeypatch, capsys)
    tail = out.split("■ What needs me\n", 1)[1].splitlines()
    assert tail == [
        "    004  decide D1",
        "    031  landing stopped at ship",
        "    030  landing stopped at close",
    ], tail
    ready = out.split("■ Ready to close: ", 1)[1].split("\n■", 1)[0]
    assert (
        "030  draft-land                   → /sdlc:close 030  (landing stopped at close)" in ready
    )
    assert "032  draft-running                → /sdlc:close 032\n" in ready
    cards = _cards(repo)
    for rec in a["open"]:
        card = cards[f"{rec['id']}-{rec['slug']}"]
        assert rec["needs"] == [n for n in card["needs"] if not n.startswith("fix: ")], rec["id"]


# ---------------------------------------------------------------- the drawer's file (138)

# The drawer's ids, each a stand-in node, and a `fetch` whose responses the test releases in the
# order it names: `steps` is a list of ("show", path) and ("answer", path) moves.
_DRAWER_RUN = r"""
El.prototype.replaceChildren = function (...ns) { this.kids = []; this.append(...ns); };
Object.defineProperty(El.prototype, "children", {
  get() { return this.kids.filter((k) => k instanceof El); },
});
const ids = {};
const $ = (id) => (ids[id] ??= new El("div"));
const waiting = {};
globalThis.fetch = (url) => new Promise((resolve) => {
  const path = new URLSearchParams(url.split("?")[1]).get("path");
  waiting[path] = () => resolve({ ok: true, status: 200, text: async () => input.files[path] });
});
const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
const tick = () => new Promise((r) => setTimeout(r, 0));
(async () => {
  for (const [move, path] of input.steps) {
    if (move === "show") show("005-share", path);
    else waiting[path]();
    await tick();
  }
  process.stdout.write(JSON.stringify({ doc, pane: $("d-doc"), raw: $("d-raw").hidden }));
})();
"""


def _drawer(files: dict[str, str], steps: list[tuple[str, str]]) -> dict:
    """The page's `show()` and `paint()`, run under node over the stand-in DOM."""
    _, script = _page_parts()
    helper = re.search(r"^function h\(tag, attrs, \.\.\.children\) \{.*?^\}$", script, re.S | re.M)
    section = re.search(r"^// ---- markdown\b.*?^// ---- end markdown$", script, re.S | re.M)
    drawer = re.search(r"^let open = null;$.*?^async function show\(.*?^\}$", script, re.S | re.M)
    assert helper and section and drawer, "h(), the markdown section, paint() and show()"
    program = "\n".join(
        ['"use strict";', _FAKE_DOM, helper.group(0), section.group(0), drawer.group(0)]
        + [_DRAWER_RUN]
    )
    out = subprocess.run(
        ["node", "-e", program],
        input=json.dumps({"files": files, "steps": steps}),
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(out.stdout)


@needs_node
def test_a_stale_response_never_paints_over_the_newer_file() -> None:
    """2026-11-18-9: two files clicked quickly, the older answering last, show the newer."""
    files = {"intent.md": "# Intent\n\nthe older file\n", "notes.md": "the newer file\n"}
    steps = [("show", "intent.md"), ("show", "notes.md"), ("answer", "notes.md")]
    run = _drawer(files, steps + [("answer", "intent.md")])
    assert run["doc"]["path"] == "notes.md"
    assert _text(run["pane"]) == "the newer file"
    in_order = _drawer(files, [("show", "intent.md"), ("answer", "intent.md")])
    assert in_order["doc"]["path"] == "intent.md" and "the older file" in _text(in_order["pane"])


@needs_node
def test_an_empty_file_says_so() -> None:
    """2026-11-18-8: an empty file draws a note, never a blank pane, and no Raw toggle; one
    holding only whitespace is as empty."""
    cases = [
        ("intent.md", ""),
        ("build/round-1.files", ""),
        ("notes.md", "\n"),
        ("a.md", " \n\t\n"),
    ]
    for path, text in cases:
        run = _drawer({path: text}, [("show", path), ("answer", path)])
        assert run["doc"] == {"path": path, "text": text}
        assert _text(run["pane"]) == "This file is empty.", path
        assert _nodes(run["pane"], "pre"), "in the pane's plain style, as an empty folder's note"
        assert run["raw"] is True, "nothing raw to show"
