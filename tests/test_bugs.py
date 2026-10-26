"""Bugs: `[bug]` entries in work/inbox.md, weighed by the process doc's severity words. `bugs` lists
them and names the change that last touched a path, `check` audits them, `status` puts them first,
and `inbox-commit` records what /sdlc:bug or /sdlc:idea wrote, on main, from the main checkout or
for the entries a change's worktree names."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path

import pytest

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
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n" + "".join(entries), encoding="utf-8"
    )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _inbox(root: Path, *entries: str) -> None:
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n" + "".join(entries), encoding="utf-8"
    )


def _close(root: Path, name: str, path: str) -> None:
    """A change that edits `path`, landed on main and closed, as close leaves history."""
    number, slug = name.split("-", 1)
    folder = root / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(id=number, slug=slug), encoding="utf-8")
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(f"{name}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Ship {name}")
    _git(root, "rm", "-rq", f".sdlc/work/{name}")
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
        _bug("2026-10-02-1", "No severity", severity=None),
        _bug("2026-10-02-2", "Odd severity", severity="urgent"),
        _bug("2026-10-02-3", "Blamed on nothing", extra="Introduced by: 099-gone\n"),
    )
    found = [p["detail"] for p in sdlc.analyze(root)["problems"] if p["kind"] == "bugs"]
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


def test_a_line_from_a_changes_first_folderless_commit_is_blamed_on_it(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    start = _git(root, "rev-parse", "HEAD")
    (root / "src").mkdir()
    (root / "src" / "early.py").write_text("x\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a first commit, without the change's folder")
    folder = root / ".sdlc" / "work" / "001-keep-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(id="001", slug="keep-drafts"), "utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-keep-drafts")
    _git(root, "rm", "-rq", ".sdlc/work/001-keep-drafts")
    _git(root, "commit", "-q", "-m", "Close 001-keep-drafts", "-m", f"Sdlc-Base: {start}")
    assert sdlc.introducer(root, "main", "src/early.py") == "001-keep-drafts"


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
        ("idea", "idea", "A seed"),
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
    code = sdlc.cmd_inbox_commit(root, reasons=list(reasons))
    return code, json.loads(capsys.readouterr().out)


def test_inbox_commit_files_a_new_bug(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    _inbox(root, _bug("2026-10-01-1", "One"), _bug("2026-10-02-1", "Two"))
    code, out = _commit(root, capsys)
    assert code == 0, out
    assert _git(root, "log", "-1", "--format=%s") == "File 2026-10-02-1"
    assert _git(root, "status", "--short") == ""


def test_inbox_commit_updates_a_retagged_entry(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    _inbox(root, "## [2026-10-01-1] [seed] One\n\nIt's a request after all.\n\n")
    assert _commit(root, capsys)[0] == 0
    assert _git(root, "log", "-1", "--format=%s") == "Update 2026-10-01-1"


def test_inbox_commit_retires_with_a_reason_and_a_trailer(tmp_path: Path, capsys) -> None:
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


def test_inbox_commit_refuses_before_writing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    code, out = _commit(root, capsys)
    assert code == 1 and out["refusals"] == ["nothing to record: .sdlc/work/inbox.md is unchanged"]
    _inbox(root, _bug("2026-10-01-1", "One", severity="low"))
    (root / "README.md").write_text("stray\n", encoding="utf-8")
    code, out = _commit(root, capsys, "2026-10-01-1=wontfix", "2026-10-01-9=bogus")
    assert code == 1
    assert out["refusals"] == [
        "only .sdlc/work/inbox.md may be uncommitted; also changed: README.md",
        "--reason 2026-10-01-1: no entry by that id was removed",
        "--reason 2026-10-01-9: no entry by that id was removed",
    ]
    assert _git(root, "log", "--format=%s") == "init"


def _idea(entry_id: str, title: str, tag: str = "idea") -> str:
    return f"## [{entry_id}] [{tag}] {title}\n\nWhat it's for.\n\n"


def test_inbox_commit_retires_by_the_entry_s_kind(tmp_path: Path, capsys) -> None:
    """An idea retires as duplicate, superseded or declined, a bug by its own four, and a nit or
    an entry being built never here."""
    root = _repo(
        tmp_path,
        _bug("2026-10-01-1", "One"),
        _idea("2026-10-02-1", "Two"),
        _idea("2026-10-03-1", "Three", "nit"),
        _idea("2026-10-04-1", "Four", "building"),
    )
    _inbox(root, _bug("2026-10-01-1", "One"))
    code, out = _commit(
        root, capsys, "2026-10-02-1=wontfix", "2026-10-03-1=declined", "2026-10-04-1=declined"
    )
    assert code == 1 and out["refusals"] == [
        "--reason 2026-10-02-1=wontfix: an idea's reason is one of duplicate|superseded|declined",
        "2026-10-03-1 is a nit: ship retires nits, with the change that fixes one",
        "2026-10-04-1 is being built: its change removes it at ship, or /sdlc:drop says why not",
    ]
    _inbox(
        root,
        _bug("2026-10-01-1", "One"),
        _idea("2026-10-03-1", "Three", "nit"),
        _idea("2026-10-04-1", "Four", "building"),
    )
    code, out = _commit(root, capsys, "2026-10-02-1=superseded")
    assert code == 0, out
    body = _git(root, "log", "-1", "--format=%B")
    assert body.startswith("Retire 2026-10-02-1")
    assert "Reason 2026-10-02-1: superseded" in body and "Sdlc-Retired:" not in body
    _inbox(root, _idea("2026-10-03-1", "Three", "nit"), _idea("2026-10-04-1", "Four", "building"))
    code, out = _commit(root, capsys, "2026-10-01-1=superseded")
    assert code == 1 and out["refusals"] == [
        "--reason 2026-10-01-1=superseded: a bug's reason is one of "
        "duplicate|not-a-bug|wontfix|cant-reproduce"
    ]


def test_inbox_commit_never_retires_what_an_open_change_builds_or_fixes(
    tmp_path: Path, capsys
) -> None:
    """The `[building]` tag rides on the change's branch, so main's register still reads `[idea]`:
    an open change's `idea:` and `fixes:` lines are what say an entry is taken. Ids given from the
    main checkout are refused, since it records the whole register."""
    root = _repo(tmp_path, _idea("2026-10-01-1", "One"), _bug("2026-10-02-1", "Two"))
    folder = root / ".sdlc" / "work" / "001-keep-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(
        FIXING.format(fixes="2026-10-02-1").replace("idea:\n", "idea: 2026-10-01-1\n"),
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "open 001")
    _inbox(root)
    code, out = _commit(root, capsys, "2026-10-01-1=declined", "2026-10-02-1=wontfix")
    assert code == 1 and out["refusals"] == [
        "2026-10-01-1 is being built by 001-keep-drafts: its change removes it at ship, "
        "or /sdlc:drop says why not",
        "2026-10-02-1 is being built by 001-keep-drafts: its change removes it at ship, "
        "or /sdlc:drop says why not",
    ]
    code = sdlc.cmd_inbox_commit(root, ["2026-10-01-1"], ["2026-10-01-1=declined"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["refusals"][0] == (
        "from the main checkout it records the whole register: name no entries"
    )
    assert _git(root, "log", "-1", "--format=%s") == "open 001"


def test_bug_commit_is_gone(capsys, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "bug-commit"])
    with pytest.raises(SystemExit) as raised:
        sdlc.main()
    assert raised.value.code != 0


def _tree(root: Path, name: str = "001-x") -> Path:
    tree = root / ".claude" / "worktrees" / name
    _git(root, "worktree", "add", "-q", "-b", name, str(tree))
    return tree


def _tree_inbox(tree: Path, *entries: str) -> None:
    (tree / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n" + "".join(entries), encoding="utf-8"
    )


def _file(tree: Path, capsys, *ids: str, reasons: tuple[str, ...] = ()) -> tuple[int, dict]:
    code = sdlc.cmd_inbox_commit(tree, list(ids), list(reasons))
    return code, json.loads(capsys.readouterr().out)


def test_a_worktree_files_the_entries_it_names_on_main(tmp_path: Path, capsys) -> None:
    """A new idea from a change's worktree lands on main alone; the worktree's own edits stay, and
    the filed entry leaves its diff until it comes up to date."""
    root = _repo(tmp_path, _idea("2026-10-01-1", "One"), _bug("2026-10-02-1", "Two"))
    tree = _tree(root)
    _tree_inbox(
        tree,
        _idea("2026-10-01-1", "One", "building"),
        _bug("2026-10-02-1", "Two"),
        _idea("2026-10-05-1", "Five"),
    )
    code, out = _file(tree, capsys, "2026-10-05-1")
    assert code == 0, out
    assert _git(root, "log", "-1", "--format=%s") == "File 2026-10-05-1"
    assert _git(root, "show", "--name-only", "--format=", "HEAD") == ".sdlc/work/inbox.md"
    assert _git(root, "status", "--short") == ""
    on_main = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    filed = _idea("2026-10-05-1", "Five").rstrip("\n") + "\n"
    assert on_main.endswith(_bug("2026-10-02-1", "Two") + filed)
    in_tree = (tree / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert "[building] One" in in_tree and "Five" not in in_tree
    _tree_inbox(tree, _idea("2026-10-01-1", "One", "building"))
    code, out = _file(tree, capsys, "2026-10-02-1", reasons=("2026-10-02-1=not-a-bug",))
    assert code == 0, out
    assert _git(root, "log", "-1", "--format=%s") == "Retire 2026-10-02-1"
    assert "2026-10-02-1" not in (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert "[bug] Two" in (tree / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")


def test_a_worktree_updates_an_entry_in_place_on_main(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _idea("2026-10-01-1", "One"), _idea("2026-10-02-1", "Two"))
    tree = _tree(root)
    _tree_inbox(tree, _idea("2026-10-01-1", "One, sharper"), _idea("2026-10-02-1", "Two"))
    code, out = _file(tree, capsys, "2026-10-01-1")
    assert code == 0, out
    assert _git(root, "log", "-1", "--format=%s") == "Update 2026-10-01-1"
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == (
        "# Inbox\n\n" + _idea("2026-10-01-1", "One, sharper") + _idea("2026-10-02-1", "Two")
    )
    assert _git(tree, "status", "--short") == ""


def test_a_worktree_refuses_what_it_cant_file(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _idea("2026-10-01-1", "One"))
    tree = _tree(root)
    _tree_inbox(tree, _idea("2026-10-01-1", "One"), _idea("2026-10-05-1", "Five"))
    code, out = _file(tree, capsys)
    assert code == 1 and out["refusals"] == [
        "from a change's worktree, name the entries to file: inbox-commit <id>…"
    ]
    code, out = _file(tree, capsys, "2026-10-01-1")
    assert code == 1 and out["refusals"] == [
        "2026-10-01-1: this worktree's .sdlc/work/inbox.md doesn't change it"
    ]
    (root / "README.md").write_text("someone's draft\n", encoding="utf-8")
    code, out = _file(tree, capsys, "2026-10-05-1")
    assert code == 1 and out["refusals"] == [
        f"the main checkout ({root.resolve()}) has uncommitted changes: README.md"
    ]
    (root / "README.md").unlink()
    _git(root, "checkout", "-q", "-b", "elsewhere")
    code, out = _file(tree, capsys, "2026-10-05-1")
    assert code == 1 and out["refusals"] == [f"the main checkout ({root.resolve()}) isn't on main"]
    assert _git(root, "log", "--format=%s", "main") == "init"
    assert "Five" in (tree / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")


def test_inbox_commit_waits_for_the_lock_claim_takes(tmp_path: Path, capsys) -> None:
    """Two sessions filing at once: the second waits until the first lets go."""
    root = _repo(tmp_path, _idea("2026-10-01-1", "One"))
    tree = _tree(root)
    _tree_inbox(tree, _idea("2026-10-01-1", "One"), _idea("2026-10-05-1", "Five"))
    done = threading.Event()
    with sdlc._main_lock(root):
        worker = threading.Thread(
            target=lambda: (sdlc.cmd_inbox_commit(tree, ["2026-10-05-1"]), done.set())
        )
        worker.start()
        assert not done.wait(0.5)
    worker.join(10)
    assert done.is_set()
    assert _git(root, "log", "-1", "--format=%s") == "File 2026-10-05-1"


# The fix cycle: `fixes:` in the intent, ship removing the entry, close's trailer.

FIXING = """\
---
id: 001
slug: keep-drafts
tier: 1
impact: patch
stage: build
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
fixes: [{fixes}]
---

# 001 — keep drafts
"""


def _fixing(root: Path, fixes: str) -> Path:
    folder = root / ".sdlc" / "work" / "001-keep-drafts"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "intent.md").write_text(FIXING.format(fixes=fixes), encoding="utf-8")
    return folder


def test_a_change_s_fixes_must_name_open_bugs_in_its_register(tmp_path: Path) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"), "## [2026-10-01-2] [seed] A seed\n\nx\n")
    _fixing(root, "2026-10-01-1, 2026-10-01-2, 2026-10-01-9")
    rec = sdlc.analyze(root)["open"][0]
    assert rec["fixes"] == ["2026-10-01-1", "2026-10-01-2", "2026-10-01-9"]
    errors = [e for e in rec["errors"] if e.startswith("fixes:")]
    assert errors == [
        "fixes: '2026-10-01-2' isn't a [bug] in .sdlc/work/inbox.md",
        "fixes: '2026-10-01-9' isn't a [bug] in .sdlc/work/inbox.md",
    ]


def test_a_bug_an_open_change_fixes_leaves_next_up_and_the_count(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "Being fixed"), _bug("2026-10-02-1", "Open"))
    _fixing(root, "2026-10-01-1")
    a = sdlc.analyze(root)
    items = sdlc.next_up(root, sdlc.load_config(root)[0], a["open"], date(2026, 10, 25))["items"]
    assert [i["title"] for i in items] == ["Open"]
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    sdlc.main()
    assert "■ Bugs: 1 open (high 1)" in capsys.readouterr().out


def test_ship_removes_each_bug_the_change_fixes_and_nothing_else(tmp_path: Path, capsys) -> None:
    entries = [
        _bug("2026-10-01-1", "One"),
        _bug("2026-10-01-2", "Two"),
        _bug("2026-10-01-3", "Three"),
    ]
    root = _repo(tmp_path, *entries)
    _fixing(root, "2026-10-01-1, 2026-10-01-3, 2026-10-01-9")
    assert sdlc.cmd_ship(root, "001") == 0
    out = capsys.readouterr().out
    assert "removed bug 2026-10-01-1" in out and "removed bug 2026-10-01-3" in out
    assert "no bug to remove: .sdlc/work/inbox.md has no entry 2026-10-01-9" in out
    inbox = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert inbox == "# Inbox\n\n" + entries[1].rstrip("\n") + "\n", "the last one trails no gap"


def test_close_s_trailer_describes_each_fix_from_the_branch(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        _bug("2026-10-01-1", "One", extra="Introduced by: 000-start\n"),
        _bug("2026-10-02-1", "Two", "low"),
    )
    _git(root, "checkout", "-q", "-b", "001-keep-drafts")
    _fixing(root, "2026-10-01-1, 2026-10-02-1, 2026-10-03-9")
    _inbox(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-keep-drafts")
    assert sdlc.fix_trailers(root, "001-keep-drafts") == [
        "Sdlc-Fixes: 2026-10-01-1 severity=high reported=2026-10-01 introduced_by=000-start",
        "Sdlc-Fixes: 2026-10-02-1 severity=low reported=2026-10-02 introduced_by=unknown",
        "Sdlc-Fixes: 2026-10-03-9 severity=unknown reported=unknown introduced_by=unknown",
    ]
    assert sdlc.fix_trailers(root, "no-such-branch") == []


def test_only_a_close_records_fixes_never_a_drop() -> None:
    import inspect

    assert "fix_trailers(" in inspect.getsource(sdlc.cmd_close)
    assert "fix_trailers(" not in inspect.getsource(sdlc._drop_record)


# What retro counts.


def test_retro_counts_bugs_reported_fixed_retired_open_and_escaped(
    tmp_path: Path, monkeypatch
) -> None:
    root = _repo(tmp_path)
    _close(root, "001-start", "src/drafts.py")
    # The fix: a change whose Close commit records it, ten days after the report.
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-10-11T12:00:00")
    folder = root / ".sdlc" / "work" / "002-fix-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(id="002", slug="fix-drafts"), encoding="utf-8")
    (root / "src" / "drafts.py").write_text("fixed\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Fix drafts")
    _git(root, "rm", "-rq", ".sdlc/work/002-fix-drafts")
    fixes = "Sdlc-Fixes: 2026-10-01-1 severity=high reported=2026-10-01 introduced_by=001-start"
    _git(root, "commit", "-q", "-m", "Close 002-fix-drafts", "-m", "x", "-m", fixes)
    # A retirement, on its own commit.
    _inbox(root, _bug("2026-10-02-1", "Twice", "low"))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "File 2026-10-02-1")
    _inbox(root, _bug("2026-10-03-1", "Still open", "med"))
    _git(root, "add", "-A")
    retired = "Sdlc-Retired: 2026-10-02-1 severity=low reported=2026-10-02 reason=duplicate"
    _git(root, "commit", "-q", "-m", "Retire 2026-10-02-1; File 2026-10-03-1", "-m", retired)
    out = sdlc.retro(root, sdlc.load_config(root)[0], date(2026, 10, 25))["bugs"]
    assert out["reported"] == {"high": 1, "med": 1, "low": 1}
    assert out["fixed"] == {"high": 1}
    assert out["retired"] == {"duplicate": 1}
    assert out["days_to_fix"] == {"median": 10, "max": 10}
    assert [(b["id"], b["severity"], b["age_days"]) for b in out["open"]] == [
        ("2026-10-03-1", "med", 22)
    ]
    assert out["escapes"] == [{"change": "001-start", "bugs": 1, "tier": 1}]
    assert out["unattributed"] == 1, "the open bug no one has attributed"


def test_retro_counts_no_bugs_as_nothing(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    out = sdlc.retro(root, sdlc.load_config(root)[0], date(2026, 10, 25))["bugs"]
    assert out == {
        "reported": {},
        "fixed": {},
        "retired": {},
        "triaged": {},
        "days_to_fix": {"median": None, "max": None},
        "open": [],
        "escapes": [],
        "unattributed": 0,
    }


def test_retro_counts_the_issues_triage_closed_by_verdict(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    triaged = ["12=resolved:019-status-next", "13=wontfix", "14=wontfix"]
    whys = ["13=Out of scope", "14=Out of scope"]
    assert sdlc.cmd_inbox_commit(root, triaged=triaged, whys=whys) == 0
    out = sdlc.retro(root, sdlc.load_config(root)[0], date(2026, 10, 25))["bugs"]
    assert out["triaged"] == {"resolved": 1, "wontfix": 2}


def test_retro_counts_escapes_only_from_its_window(tmp_path: Path) -> None:
    """A bug reported before the last retrospective was counted there, and isn't again."""
    root = _repo(tmp_path)
    _close(root, "001-start", "src/drafts.py")
    _inbox(
        root,
        _bug("2026-09-01-1", "Old", extra="Introduced by: 001-start\n"),
        _bug("2026-09-02-1", "Old and unattributed"),
        _bug("2026-10-10-1", "New", extra="Introduced by: 001-start\n"),
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Retrospective 2026-10-01")
    out = sdlc.retro(root, sdlc.load_config(root)[0], date(2026, 10, 25))["bugs"]
    assert out["escapes"] == [{"change": "001-start", "bugs": 1, "tier": 1}]
    assert out["unattributed"] == 0 and out["reported"] == {"high": 1}
    assert len(out["open"]) == 3, "every open bug is still listed by age"


def test_fixes_names_bugs_by_id_never_by_title(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _bug("2026-10-01-1", "One"))
    _fixing(root, '"One"')
    errors = sdlc.analyze(root)["open"][0]["errors"]
    assert "fixes: 'One' isn't an id: name each bug by its YYYY-MM-DD-n" in errors
    assert sdlc.cmd_ship(root, "001") == 0
    assert "no bug to remove" in capsys.readouterr().out
    assert "2026-10-01-1" in (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
