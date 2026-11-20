"""The factory's eval and review: escapes from the register's history, reports and scores, and the
slice a review takes.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from factory_helpers import (
    LISTED,
    _change,
    _git,
    _run,
    factory,
    sdlc,
)

# ---------------------------------------------------------------- the eval: what escaped


REGISTER = """\
# Inbox

## [2026-10-20-1] [bug] Drafts list shows deleted ones

What happens.

Severity: high
Paths: `src/list.py`, src/views/
Introduced by: 001-start

## [2026-10-21-1] [idea] Not a bug

Paths: src/x.py

## [2026-10-22-1] [bug] Nobody knows where

Severity: low

```
## [2026-10-23-1] [bug] Fenced, not an entry
```
"""


def _history(tmp_path: Path) -> Path:
    """Main with two closed changes: 001-start (with its base recorded) and 002-fix (without),
    whose close says it fixed a bug 001 let in; then a register with open bugs."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    start = _git(root, "rev-parse", "HEAD")
    (root / "src").mkdir()
    (root / "src" / "drafts.py").write_text("v1\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-start")
    one = _git(root, "rev-parse", "HEAD")
    _git(
        root, "commit", "-q", "--allow-empty", "-m", "Close 001-start", "-m", f"Sdlc-Base: {start}"
    )
    (root / "src" / "drafts.py").write_text("v2\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 002-fix")
    fixes = [
        "Sdlc-Fixes: 2026-10-05-1 severity=high reported=2026-10-05 introduced_by=001-start "
        "paths=src/drafts.py",
        "Sdlc-Fixes: 2026-10-06-1 severity=low reported=2026-10-06 introduced_by=001-start",
        "Sdlc-Fixes: 2026-10-07-1 severity=low reported=2026-10-07 introduced_by=099-gone "
        "paths=src/x.py",
    ]
    _git(root, "commit", "-q", "--allow-empty", "-m", "Close 002-fix", "-m", "\n".join(fixes))
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "File bugs")
    root.joinpath(".one").write_text(one)
    return root


def test_escapes_lists_each_bug_with_the_diff_that_let_it_in(tmp_path, capsys) -> None:
    root = _history(tmp_path)
    one = root.joinpath(".one").read_text()
    root.joinpath(".one").unlink()
    code, out = _run(capsys, factory.cmd_escapes, root, 10)
    assert code == 0
    got = [(e["id"], e["change"], e["paths"], e["partial"]) for e in out["escapes"]]
    assert got == [
        ("2026-10-20-1", "001-start", ["src/list.py", "src/views/"], False),
        ("2026-10-06-1", "001-start", None, False),
        ("2026-10-05-1", "001-start", ["src/drafts.py"], False),
    ], "newest reported first; a pathless one listed, not dropped"
    first = out["escapes"][-1]
    assert first["commit"] == one and first["title"] is None, "a fixed bug's title left with it"
    assert first["base"] == _git(root, "rev-parse", "HEAD~5")
    assert out["escapes"][0]["title"] == "Drafts list shows deleted ones"
    assert (out["unattributed"], out["unknown_change"]) == (1, 1)
    assert _run(capsys, factory.cmd_escapes, root, 1)[1]["escapes"][0]["id"] == "2026-10-20-1"


def test_a_close_without_its_base_replays_the_last_commit_alone(tmp_path, capsys) -> None:
    root = _history(tmp_path)
    _git(root, "commit", "-q", "--allow-empty", "-m", "Ship 003-later")
    change = _git(root, "rev-parse", "HEAD")
    _git(root, "commit", "-q", "--allow-empty", "-m", "Close 003-later")
    register = root / ".sdlc" / "work" / "inbox.md"
    register.write_text(
        register.read_text()
        + "\n## [2026-10-30-1] [bug] Later\n\nSeverity: low\nIntroduced by: 003\n"
    )
    _, out = _run(capsys, factory.cmd_escapes, root, 10)
    [later] = [e for e in out["escapes"] if e["id"] == "2026-10-30-1"]
    assert (later["commit"], later["base"], later["partial"]) == (change, f"{change}^", True)


def test_the_register_is_read_as_sdlc_reads_it(tmp_path) -> None:
    (tmp_path / ".sdlc" / "work").mkdir(parents=True)
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(REGISTER)
    keys = ("id", "title", "reported", "severity", "paths", "introduced_by")
    ours = [{k: b[k] for k in keys} for b in factory.open_bugs(tmp_path)]
    theirs = [{k: b[k] for k in keys} for b in sdlc.bug_entries(tmp_path, ["high", "low"])[0]]
    assert ours == theirs


@pytest.mark.parametrize(
    "line",
    [
        "2026-10-05-1 severity=high reported=2026-10-05 introduced_by=001-start paths=a.py,b/",
        "2026-10-06-1 severity=low reported=unknown introduced_by=unknown",
        "2026-10-07-1 severity=med reported=2026-10-07 introduced_by=002-fix paths=unknown",
    ],
)
def test_fixes_lines_are_read_as_sdlc_reads_them(line: str) -> None:
    name, fields = factory._words(line)
    parsed = sdlc.metrics.parse_trailers(f"Sdlc-Fixes: {line}")["fixes"]
    assert {name: fields} == {k: {f: str(v) for f, v in d.items()} for k, d in parsed.items()}
    assert factory.bug_paths(fields.get("paths")) == sdlc.retro._bug_paths(fields.get("paths"))


@pytest.mark.parametrize(
    "evidence, paths",
    [
        ("src/drafts.py:3", ["src/drafts.py"]),
        ("src/list/view.py:9", ["src/list/"]),
        ("src/list:1", ["src/list/view.py"]),
        ("src/drafts_old.py:3", ["src/drafts.py"]),
        ("src/drafts.py:3", None),
    ],
)
def test_on_paths_is_sdlc_s_own(evidence: str, paths: list[str] | None) -> None:
    assert factory.on_paths(evidence, paths) is sdlc.retro._on_paths(evidence, paths)


# ---------------------------------------------------------------- reports and scores


def test_a_report_folder_ignores_itself(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the change so far")
    _, first = _run(capsys, factory.cmd_report_dir, root, "eval")
    _, second = _run(capsys, factory.cmd_report_dir, root, "eval")
    assert first["run"].endswith("-1") and second["run"].endswith("-2")
    (root / second["run"] / "note.md").write_text("x\n")
    assert _git(root, "status", "--porcelain") == "", "nothing a report writes dirties a checkout"


def _scored(root: Path, capsys, run: str, escapes: list[dict], replies: dict) -> dict:
    (root / run / "escapes.json").write_text(json.dumps({"escapes": escapes}))
    for (bug, role), text in replies.items():
        (root / run / bug).mkdir(exist_ok=True)
        (root / run / bug / f"{role}.md").write_text(text)
    return _run(capsys, factory.cmd_score, root, run)[1]


def test_a_reviewer_caught_a_bug_when_a_change_sits_on_its_paths(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    run = _run(capsys, factory.cmd_report_dir, root, "eval")[1]["run"]
    escapes = [
        {"id": "b1", "change": "001-start", "paths": ["src/drafts.py"]},
        {"id": "b2", "change": "001-start", "paths": None},
    ]
    replies = {
        ("b1", "code"): "VERDICT: CHANGES\n- CHANGE: src/drafts.py:3: saves twice\n",
        ("b1", "test"): "VERDICT: CHANGES\n- CHANGE: tests/test_x.py: add a test\n",
        ("b2", "code"): "VERDICT: CHANGES\n- CHANGE: src/drafts.py:3: saves twice\n",
    }
    out = _scored(root, capsys, run, escapes, replies)
    assert out["reviewers"]["code"] == {"caught": 1, "scored": 1, "previous": None}
    assert out["reviewers"]["test"] == {"caught": 0, "scored": 1, "previous": None}
    [b1, b2] = out["bugs"]
    assert b1["results"]["code"] == {"result": "caught", "lines": ["src/drafts.py:3: saves twice"]}
    assert b2["results"]["code"]["result"] == "unknown", "no paths: never scored as missed"
    report = (root / f"{run}.md").read_text()
    assert "- code: 1 of 1 caught" in report and "- test: 0 of 1 caught" in report


def test_each_eval_is_compared_with_the_last(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    escapes = [{"id": "b1", "change": "001-start", "paths": ["src/drafts.py"]}]
    first = _run(capsys, factory.cmd_report_dir, root, "eval")[1]["run"]
    _scored(root, capsys, first, escapes, {("b1", "code"): "VERDICT: PASS\n"})
    second = _run(capsys, factory.cmd_report_dir, root, "eval")[1]["run"]
    caught = {("b1", "code"): "VERDICT: CHANGES\n- CHANGE: src/drafts.py:1: x\n"}
    out = _scored(root, capsys, second, escapes, caught)
    assert out["reviewers"]["code"]["previous"] == {"caught": 0, "scored": 1}
    assert "- code: 1 of 1 caught (was 0 of 1)" in (root / f"{second}.md").read_text()


# ---------------------------------------------------------------- the review: old code


def _slice(root: Path, capsys, *paths: str, limit: int = 10) -> dict:
    return _run(capsys, factory.cmd_slice, root, list(paths), limit)[1]


def test_a_review_takes_the_sensitive_paths_first(tmp_path, capsys) -> None:
    root = _change(tmp_path, config=LISTED)
    (root / "src" / "secret").mkdir(parents=True)
    (root / "src" / "secret" / "key.py").write_text("k\n")
    (root / "src" / "other.py").write_text("o\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "more code")
    _git(root, "branch", "-q", "-f", "main", "HEAD")
    out = _slice(root, capsys)
    assert out["paths"] == ["src/secret/key.py"] and "sensitive" in out["why"]
    assert _slice(root, capsys, "src/other.py")["paths"] == ["src/other.py"], "named wins"


def test_without_sensitive_paths_the_least_recently_changed_come_first(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the change so far")
    (root / "newer.py").write_text("n\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "newer", "--date", "2030-01-01T00:00:00")
    out = _slice(root, capsys, limit=1)
    assert out["paths"] == ["README.md"] and "least recently changed" in out["why"]


def test_a_review_leaves_out_what_an_open_change_touches(tmp_path, capsys) -> None:
    root = _change(tmp_path, branch="main-work")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the work")
    _git(root, "branch", "-q", "-f", "main", "HEAD")
    tree = tmp_path / "wt"
    _git(root, "worktree", "add", "-q", "-b", "009-open", str(tree), "main")
    (tree / "README.md").write_text("an open change edits this\n")
    out = _slice(root, capsys, "README.md", "other.md")
    assert out["paths"] == ["other.md"] and out["left_out"] == ["README.md"]
