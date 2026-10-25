"""Bugs: `[bug]` entries in work/inbox.md, weighed by the process doc's severity words. `bugs` lists
them and names the change that last touched a path, `check` audits them, `status` puts them first,
and `bug-commit` records what /sdlc:bug wrote, from the main checkout only."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_bugs", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

INTENT = """\
---
id: {id}
slug: {slug}
tier: 1
impact: patch
stage: shipped
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
---

# {id} — {slug}
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _bug(entry_id: str, title: str, severity: str | None = "high", extra: str = "") -> str:
    line = f"Severity: {severity}\n" if severity else ""
    return f"## [{entry_id}] [bug] {title}\n\nWhat happens.\n\n{line}{extra}\n"


def _repo(tmp_path: Path, *entries: str) -> Path:
    root = tmp_path / "repo"
    (root / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "work" / "inbox.md").write_text("# Inbox\n\n" + "".join(entries), encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _inbox(root: Path, *entries: str) -> None:
    (root / "work" / "inbox.md").write_text("# Inbox\n\n" + "".join(entries), encoding="utf-8")


def _close(root: Path, name: str, path: str) -> None:
    """A change that edits `path`, landed on main and closed, as close leaves history."""
    number, slug = name.split("-", 1)
    folder = root / "work" / name
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(id=number, slug=slug), encoding="utf-8")
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(f"{name}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Ship {name}")
    _git(root, "rm", "-rq", f"work/{name}")
    _git(root, "commit", "-q", "-m", f"Close {name}")


def _process(root: Path, bullet: str) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "SDLC.md").write_text(
        f"# Process\n\n#### Nits\n\n- **severity:** `nope`\n\n#### Bugs here\n\n{bullet}\n",
        encoding="utf-8",
    )


# Severity.


def test_severity_words_come_from_the_process_doc(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _process(root, "- **severity:** `critical`, it's down ·\n  `minor`, it's ugly")
    assert sdlc.severities(root, sdlc.load_config(root)[0]) == ["critical", "minor"]


def test_without_the_bullet_the_default_doc_s_words_hold(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _process(root, "Nothing about severity here.")
    assert sdlc.severities(root, sdlc.load_config(root)[0]) == ["high", "med", "low"]


# Reading and checking.


def test_bugs_read_with_their_lines(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        _bug("2026-10-02-1", "Close leaves the worktree", extra="Paths: scripts/a.py, docs/\n"),
        "## [2026-10-02-2] [seed] Not a bug\n\nWhy.\n\n",
    )
    bugs, problems = sdlc.bug_entries(root)
    assert problems == []
    assert [(b["id"], b["severity"], b["reported"]) for b in bugs] == [
        ("2026-10-02-1", "high", "2026-10-02")
    ]
    assert bugs[0]["paths"] == ["scripts/a.py", "docs/"] and bugs[0]["text"] == "What happens."


def test_check_reports_each_malformed_bug(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        "## [2026-10-02] [bug] Before ids\n\nx\n\nSeverity: high\n\n",
        _bug("2026-10-02-1", "No severity", severity=None),
        _bug("2026-10-02-2", "Odd severity", severity="urgent"),
        _bug("2026-10-02-3", "Blamed on nothing", extra="Introduced by: 099-gone\n"),
    )
    found = [p["detail"] for p in sdlc.analyze(root)["problems"] if p["kind"] == "bugs"]
    assert any(d.startswith("'Before ids' has no id") for d in found)
    assert "2026-10-02-1 has no `Severity:` line" in found
    assert "2026-10-02-2: Severity must be one of high|med|low, got 'urgent'" in found
    assert "2026-10-02-3: Introduced by '099-gone' names no change" in found


def test_an_introducing_change_that_closed_is_no_problem(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-keep-drafts", "src/drafts.py")
    _inbox(root, _bug("2026-10-02-1", "Drafts", extra="Introduced by: 001-keep-drafts\n"))
    assert not [p for p in sdlc.analyze(root)["problems"] if p["kind"] == "bugs"]


def test_bugs_lists_by_path_and_names_the_change_that_last_touched_one(
    tmp_path: Path, capsys
) -> None:
    root = _repo(tmp_path)
    _close(root, "001-keep-drafts", "src/drafts.py")
    _close(root, "002-share-drafts", "src/share.py")
    (root / "src" / "loose.py").write_text("x\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a commit outside any change")
    _inbox(
        root,
        _bug("2026-10-02-1", "Drafts", extra="Paths: src/drafts.py\n"),
        _bug("2026-10-02-2", "Sharing", extra="Paths: src/share.py\n"),
    )
    code = sdlc.cmd_bugs(root, ["src/drafts.py"], ["src/drafts.py", "src/loose.py", "nowhere"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and [b["id"] for b in out["bugs"]] == ["2026-10-02-1"]
    assert out["introduced"] == [
        {"path": "src/drafts.py", "change": "001-keep-drafts"},
        {"path": "src/loose.py", "change": None},
        {"path": "nowhere", "change": None},
    ]


# What comes next.


def _next(root: Path) -> list[dict]:
    return sdlc.next_up(root, sdlc.load_config(root)[0], [], date(2026, 10, 25))["items"]


def test_next_up_puts_bugs_first_most_severe_then_oldest(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        "## [2026-10-01-1] [seed] A seed\n\nWhy.\n\n",
        _bug("2026-10-01-2", "Old and low", severity="low"),
        _bug("2026-10-03-1", "New and high", severity="high"),
        _bug("2026-10-02-1", "Older and high", severity="high"),
    )
    assert [(i["rule"], i["label"], i["title"]) for i in _next(root)] == [
        ("bug", "bug high", "Older and high"),
        ("bug", "bug high", "New and high"),
        ("bug", "bug low", "Old and low"),
        ("seed", "seed", "A seed"),
    ]


def test_status_counts_the_open_bugs(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(
        tmp_path,
        _bug("2026-10-01-1", "One", severity="low"),
        _bug("2026-10-02-1", "Two", severity="high"),
    )
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    sdlc.main()
    out = capsys.readouterr().out
    assert "■ Bugs: 2 open (high 1, low 1), oldest" in out


# Recording what /sdlc:bug wrote.


def _commit(root: Path, capsys, *reasons: str) -> tuple[int, dict]:
    code = sdlc.cmd_bug_commit(root, list(reasons))
    return code, json.loads(capsys.readouterr().out)


def test_bug_commit_files_a_new_bug(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    _inbox(root, _bug("2026-10-01-1", "One"), _bug("2026-10-02-1", "Two"))
    code, out = _commit(root, capsys)
    assert code == 0, out
    assert _git(root, "log", "-1", "--format=%s") == "File 2026-10-02-1"
    assert _git(root, "status", "--short") == ""


def test_bug_commit_updates_a_retagged_entry(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    _inbox(root, "## [2026-10-01-1] [seed] One\n\nIt's a request after all.\n\n")
    assert _commit(root, capsys)[0] == 0
    assert _git(root, "log", "-1", "--format=%s") == "Update 2026-10-01-1"


def test_bug_commit_retires_with_a_reason_and_a_trailer(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"), _bug("2026-10-02-1", "Two", "low"))
    _inbox(root, _bug("2026-10-01-1", "One"))
    code, out = _commit(root, capsys)
    assert code == 1 and out["refusals"] == [
        "2026-10-02-1 is removed with no reason: give --reason 2026-10-02-1=<word>"
    ]
    code, out = _commit(root, capsys, "2026-10-02-1=duplicate")
    assert code == 0, out
    body = _git(root, "log", "-1", "--format=%B")
    assert body.startswith("Retire 2026-10-02-1")
    assert "Sdlc-Retired: 2026-10-02-1 severity=low reported=2026-10-02 reason=duplicate" in body


def test_bug_commit_refuses_before_writing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    code, out = _commit(root, capsys)
    assert code == 1 and out["refusals"] == ["nothing to record: work/inbox.md is unchanged"]
    _inbox(root, _bug("2026-10-01-1", "One", severity="low"))
    (root / "README.md").write_text("stray\n", encoding="utf-8")
    code, out = _commit(root, capsys, "2026-10-01-1=wontfix", "2026-10-01-9=bogus")
    assert code == 1
    assert out["refusals"] == [
        "only work/inbox.md may be uncommitted; also changed: README.md",
        "--reason 2026-10-01-9=bogus: the reason is one of "
        "duplicate|not-a-bug|wontfix|cant-reproduce",
        "--reason 2026-10-01-1: no entry by that id was removed",
        "--reason 2026-10-01-9: no entry by that id was removed",
    ]
    assert _git(root, "log", "--format=%s") == "init"


def test_bug_commit_refuses_a_change_s_worktree(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    tree = root / ".claude" / "worktrees" / "001-x"
    _git(root, "worktree", "add", "-q", "-b", "001-x", str(tree))
    (tree / "work" / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
    code, out = _commit(tree, capsys)
    assert code == 1 and any("run it from the main checkout" in r for r in out["refusals"])
