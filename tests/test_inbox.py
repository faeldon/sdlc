"""The register of change requests, `.sdlc/work/inbox.md`: its entries, their ids, and how a
reference names an entry."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_inbox", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

ENTRIES = (
    "# Inbox\n\n"
    '## [2026-10-01-1] [seed] Reopen drafts\n\nWhy.\n\nAfter: "Keep drafts"\n\n'
    "## [2026-10-02-1] [bug] Close leaves the worktree\n\nWhat happens.\n\n"
    "Severity: high\nPaths: scripts/sdlc.py\nIntroduced by: 019-status-next-work\n"
)


def _work(tmp_path: Path, name: str, text: str = ENTRIES) -> Path:
    (tmp_path / ".sdlc" / "work").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sdlc" / "work" / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_the_inbox_reads_as_its_entries(tmp_path: Path) -> None:
    got = sdlc.inbox_entries(_work(tmp_path, "inbox.md"))
    assert [(e["id"], e["status"], e["title"]) for e in got] == [
        ("2026-10-01-1", "seed", "Reopen drafts"),
        ("2026-10-02-1", "bug", "Close leaves the worktree"),
    ]
    assert got[0]["after"] == ["Keep drafts"]
    assert got[1]["fields"] == {
        "Severity": "high",
        "Paths": "scripts/sdlc.py",
        "Introduced by": "019-status-next-work",
    }


def test_the_old_register_is_never_read(tmp_path: Path, capsys) -> None:
    """`ideas.md`, the register's name before 1.2.0, holds no entries, and the writers' register
    is `inbox.md` beside it."""
    root = _work(tmp_path, "ideas.md")
    assert sdlc.inbox_entries(root) == []
    sdlc.cmd_config(root)
    assert json.loads(capsys.readouterr().out)["work"]["register"] == str(
        root / ".sdlc" / "work" / "inbox.md"
    )


def test_a_heading_without_an_id_is_not_an_entry(tmp_path: Path) -> None:
    text = "# Inbox\n\n## [2026-10-03] [seed] From before ids\n\nx\n"
    assert sdlc.inbox_entries(_work(tmp_path, "inbox.md", text)) == []


def test_no_register_is_no_entries(tmp_path: Path) -> None:
    assert sdlc.inbox_entries(tmp_path) == []
    assert (
        sdlc.register_path(tmp_path / ".sdlc" / "work") == tmp_path / ".sdlc" / "work" / "inbox.md"
    )


def test_a_fenced_example_is_never_an_entry(tmp_path: Path) -> None:
    text = "# Inbox\n\n```\n## [2026-10-01-1] [seed] An example\n```\n"
    assert sdlc.inbox_entries(_work(tmp_path, "inbox.md", text)) == []


def test_a_hosts_template_under_the_old_name_is_not_the_inbox_template(tmp_path: Path) -> None:
    templates = tmp_path / ".sdlc" / "templates"
    templates.mkdir(parents=True)
    (templates / "ideas.md").write_text("# Inbox\n", encoding="utf-8")
    assert sdlc.template_path(tmp_path, "inbox.md")[1] == "plugin"
    (templates / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
    assert sdlc.template_path(tmp_path, "inbox.md") == (templates / "inbox.md", "host")


# Ids and references.


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, inbox: str = "# Inbox\n") -> Path:
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text(inbox, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _entry(entry_id: str, title: str, tag: str = "idea", after: str = "") -> str:
    line = f"\nAfter: {after}\n" if after else ""
    return f"## [{entry_id}] [{tag}] {title}\n\nWhy.\n{line}\n"


def _inbox(root: Path, *entries: str) -> None:
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n" + "".join(entries), encoding="utf-8"
    )


def test_a_line_names_entries_by_quoted_title_or_bare_id() -> None:
    assert sdlc.refs_in('"Keep drafts", 2026-10-01-2, 006') == ["Keep drafts", "2026-10-01-2"]
    assert sdlc.refs_in("2026-10-01") == [], "a bare date is no id"


def test_a_reference_matches_by_id_or_by_title() -> None:
    entry = {"id": "2026-10-01-2", "title": "Keep drafts"}
    assert sdlc.ref_matches("2026-10-01-2", entry)
    assert sdlc.ref_matches("Keep drafts", entry)
    assert sdlc.ref_matches("[2026-10-01] [seed] Keep drafts", entry), "an older heading"
    assert not sdlc.ref_matches("2026-10-01-3", entry)
    assert not sdlc.ref_matches("2026-10-01-2", {"id": None, "title": "2026-10-01-2"})
    assert sdlc.same_ref("2026-10-01-2", "2026-10-01-2")
    assert not sdlc.same_ref("2026-10-01-2", "Keep drafts")


def test_an_idea_line_is_read_as_text() -> None:
    assert sdlc.intent_idea("---\nid: 001\nidea: 2026-10-01-2\n---\n") == "2026-10-01-2"
    assert sdlc.intent_idea("---\nid: 001\nidea: 2026-10-01\n---\n") == "2026-10-01", "not a date"
    assert sdlc.intent_idea("---\nid: 001\n---\n") == ""


def test_a_groups_line_takes_ids_before_change_numbers() -> None:
    doc = '## Milestones\n\n### M1. Drafts\n\nGroups: 006, 2026-10-01-2, "Keep drafts"\n'
    m1 = sdlc.direction_items(doc)["items"][0]
    assert m1["groups"] == {"changes": ["006"], "seeds": ["2026-10-01-2", "Keep drafts"]}


def test_after_by_id_reads_as_the_entry_it_names(tmp_path: Path) -> None:
    text = "# Inbox\n\n" + _entry("2026-10-01-1", "Keep drafts")
    text += _entry("2026-10-02-1", "Share drafts", after="2026-10-01-1, 2026-09-01-9")
    share = sdlc.inbox_entries(_work(tmp_path, "inbox.md", text))[1]
    assert share["after"] == ["Keep drafts", "2026-09-01-9"], "an id naming nothing stays"


def test_the_next_id_counts_every_checkout_and_history(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _inbox(root, _entry("2026-10-25-1", "In main"), _entry("2026-10-25-4", "Gone"))
    _git(root, "commit", "-qam", "add")
    _inbox(root, _entry("2026-10-25-1", "In main"))
    _git(root, "commit", "-qam", "ship")
    assert sdlc.next_entry_ids(root, "2026-10-25") == ["2026-10-25-5"], "a deleted id is spent"
    tree = root / ".claude" / "worktrees" / "001-x"
    _git(root, "worktree", "add", "-q", "-b", "001-x", str(tree))
    _inbox(tree, _entry("2026-10-25-7", "Uncommitted in a change's worktree"))
    assert sdlc.next_entry_ids(root, "2026-10-25", 2) == ["2026-10-25-8", "2026-10-25-9"]
    assert sdlc.next_entry_ids(root, "2026-10-26") == ["2026-10-26-1"]


def test_check_reports_an_id_used_twice(tmp_path: Path) -> None:
    text = "# Inbox\n\n" + _entry("2026-10-01-1", "One") + _entry("2026-10-01-1", "Two")
    problems = sdlc.analyze(_work(tmp_path, "inbox.md", text))["problems"]
    assert [p["detail"] for p in problems if p["kind"] == "entry id"] == [
        "2026-10-01-1 is used 2 times"
    ]


def test_ship_finds_the_seed_by_id_or_by_title(tmp_path: Path) -> None:
    text = "# Inbox\n\n" + _entry("2026-10-01-1", "Keep drafts") + _entry("2026-10-01-2", "Other")
    register = _work(tmp_path, "inbox.md", text) / ".sdlc" / "work" / "inbox.md"
    assert sdlc._seed_lines(register, "2026-10-01-2") == [6]
    assert sdlc._seed_lines(register, "Keep drafts") == [2]


def _next(root: Path, open_changes: list[dict] | None = None) -> dict:
    return sdlc.next_up(root, sdlc.load_config(root)[0], open_changes or [], date(2026, 10, 25))


def test_next_up_waits_on_an_id_and_names_each_command_by_id(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _inbox(
        root,
        _entry("2026-10-01-1", "Keep drafts"),
        _entry("2026-10-02-1", "Share drafts", after="2026-10-01-1"),
    )
    assert [(i["title"], i["command"]) for i in _next(root)["items"]] == [
        ("Keep drafts", "/sdlc:intent 2026-10-01-1"),
    ], "Share drafts waits while Keep drafts is open"


def test_next_up_leaves_out_the_seed_an_open_change_names_by_id(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _inbox(root, _entry("2026-10-01-1", "Keep drafts"))
    assert _next(root, [{"id": "001", "slug": "x", "idea": "2026-10-01-1"}])["items"] == []


def test_a_milestone_puts_forward_its_seed_named_by_id(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _inbox(root, _entry("2026-10-01-1", "Keep drafts"), _entry("2026-10-01-2", "Other"))
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(
        "## Milestones\n\n### M1. Drafts kept\n\nGroups: 2026-10-01-2\n", encoding="utf-8"
    )
    items = _next(root)["items"]
    assert [(i["rule"], i["title"]) for i in items][0] == ("milestone", "Other")


def test_migrate_inbox_is_no_longer_a_command(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["sdlc.py", "migrate-inbox"])
    with pytest.raises(SystemExit) as exit_:
        sdlc.main()
    assert exit_.value.code == 2
