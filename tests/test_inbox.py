"""The register of change requests, `work/inbox.md`: its entries, the shim that still reads a repo's
`work/ideas.md`, the host template kept under the old name, entry ids and how a reference names
an entry."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_inbox", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

ENTRIES = (
    "# Inbox\n\n"
    '## [2026-10-01] [seed] Reopen drafts\n\nWhy.\n\nAfter: "Keep drafts"\n\n'
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
        (None, "seed", "Reopen drafts"),
        ("2026-10-02-1", "bug", "Close leaves the worktree"),
    ]
    assert got[0]["after"] == ["Keep drafts"]
    assert got[1]["fields"] == {
        "Severity": "high",
        "Paths": "scripts/sdlc.py",
        "Introduced by": "019-status-next-work",
    }


def test_ideas_md_still_reads(tmp_path: Path) -> None:
    """The shim: a repo that hasn't moved to the inbox is read from its old register."""
    root = _work(tmp_path, "ideas.md")
    assert sdlc.register_path(root / ".sdlc" / "work") == root / ".sdlc" / "work" / "ideas.md"
    assert [e["title"] for e in sdlc.inbox_entries(root)] == [
        "Reopen drafts",
        "Close leaves the worktree",
    ]


def test_with_both_registers_the_inbox_is_read_and_check_says_so(tmp_path: Path) -> None:
    root = _work(tmp_path, "inbox.md", "# Inbox\n\n## [2026-10-03-1] [seed] Only here\n\nx\n")
    _work(tmp_path, "ideas.md")
    assert [e["title"] for e in sdlc.inbox_entries(root)] == ["Only here"]
    problems = sdlc.analyze(root)["problems"]
    assert [p["dir"] for p in problems if p["kind"] == "register"] == [".sdlc/work/ideas.md"]


def test_no_register_is_no_entries(tmp_path: Path) -> None:
    assert sdlc.inbox_entries(tmp_path) == []
    assert (
        sdlc.register_path(tmp_path / ".sdlc" / "work") == tmp_path / ".sdlc" / "work" / "inbox.md"
    )


def test_a_fenced_example_is_never_an_entry(tmp_path: Path) -> None:
    text = "# Inbox\n\n```\n## [2026-10-01-1] [seed] An example\n```\n"
    assert sdlc.inbox_entries(_work(tmp_path, "inbox.md", text)) == []


def test_a_hosts_template_under_the_old_name_is_the_inbox_template(tmp_path: Path) -> None:
    templates = tmp_path / ".sdlc" / "templates"
    templates.mkdir(parents=True)
    (templates / "ideas.md").write_text("# Inbox\n", encoding="utf-8")
    assert sdlc.template_path(tmp_path, "inbox.md") == (templates / "ideas.md", "host")
    (templates / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
    assert sdlc.template_path(tmp_path, "inbox.md") == (templates / "inbox.md", "host")


def test_drift_names_a_template_kept_under_the_old_name(tmp_path: Path) -> None:
    templates = tmp_path / ".sdlc" / "templates"
    templates.mkdir(parents=True)
    (templates / "ideas.md").write_text("# Inbox\n", encoding="utf-8")
    rows = [r for r in sdlc.drift(tmp_path)["report"] if r["what"] == "template"]
    assert [(r["where"], r["class"]) for r in rows] == [(".sdlc/templates/ideas.md", "renamed")]


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
        "## [2026-10-03] [seed] From before ids\n\nx\n\n",
    )
    assert [(i["title"], i["command"]) for i in _next(root)["items"]] == [
        ("Keep drafts", "/sdlc:intent 2026-10-01-1"),
        ("From before ids", "/sdlc:intent From before ids"),
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


# Moving a repo over: `migrate-inbox`.

OLD_IDEAS = """\
# Ideas

> The note.

## [2026-10-01] [seed] Keep drafts

Why.

## [2026-10-01] [building] Share drafts

Building in work/001-share-drafts/.

After: "Keep drafts"

## [2026-10-03] [bug] Drafts lose their title

What happens.
"""

OLD_NITS = """\
# Nits

> The note.

## 003-1 [tests] A test that can't fail
- **raised:** 2026-10-01 by 003-test-lifetimes (correctness)
- **paths:** tests/test_x.py
- **cost:** S  **value:** low

The half that runs patched proves nothing.

## 009-1 [style] An idiom
- **raised:** 2026-10-04 by 009-drift-message (cost)
- **paths:** tests/test_defaults.py, docs/
- **cost:** M  **value:** low
"""

OPEN_INTENT = """\
---
id: 001
slug: share-drafts
tier: 1
impact:
stage: build
created: 2026-10-02
updated: 2026-10-02
idea: Share drafts
depends_on:
---

# 001 — Share drafts
"""

DIRECTION = '## Milestones\n\n### M1. Drafts\n\nGroups: 001, "Keep drafts", "Long gone"\n'


def _old_layout(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".sdlc" / "work" / "001-share-drafts").mkdir(parents=True)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "work" / "ideas.md").write_text(OLD_IDEAS, encoding="utf-8")
    (root / ".sdlc" / "work" / "nits.md").write_text(OLD_NITS, encoding="utf-8")
    (root / ".sdlc" / "work" / "001-share-drafts" / "intent.md").write_text(
        OPEN_INTENT, encoding="utf-8"
    )
    (root / ".sdlc" / "DIRECTION.md").write_text(DIRECTION, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _migrate(root: Path, capsys) -> tuple[int, dict]:
    code = sdlc.cmd_migrate_inbox(root)
    return code, json.loads(capsys.readouterr().out)


def test_migrate_moves_the_registers_into_one_inbox_with_ids(tmp_path: Path, capsys) -> None:
    root = _old_layout(tmp_path)
    code, out = _migrate(root, capsys)
    assert code == 0, out
    work = root / ".sdlc" / "work"
    assert not (work / "ideas.md").exists() and not (work / "nits.md").exists()
    assert ".sdlc/work/ideas.md -> .sdlc/work/inbox.md" in _git(root, "status", "--short"), (
        "a git mv"
    )
    inbox = (work / "inbox.md").read_text(encoding="utf-8")
    assert inbox.startswith("# Ideas\n\n> The note.\n\n## [2026-10-01-1] [idea] Keep drafts\n")
    assert "## [2026-10-01-2] [building] Share drafts" in inbox
    assert "After: 2026-10-01-1\n" in inbox
    assert "## [2026-10-03-1] [bug] Drafts lose their title" in inbox
    assert inbox.endswith(
        "## [2026-10-01-3] [nit] A test that can't fail\n\n"
        "The half that runs patched proves nothing.\n\n"
        "Theme: tests\nPaths: tests/test_x.py\nCost: S\nValue: low\n"
        "Raised by: 003-test-lifetimes (correctness)\n\n"
        "## [2026-10-04-1] [nit] An idiom\n\n"
        "Theme: style\nPaths: tests/test_defaults.py, docs/\nCost: M\nValue: low\n"
        "Raised by: 009-drift-message (cost)\n"
    )
    nits, problems = sdlc.nit_entries(root)
    assert problems == [] and [n["by"] for n in nits] == ["003-test-lifetimes", "009-drift-message"]
    groups = (root / ".sdlc" / "DIRECTION.md").read_text(encoding="utf-8")
    assert 'Groups: 001, 2026-10-01-1, "Long gone"' in groups, "a shipped title stays a title"
    intent = (work / "001-share-drafts" / "intent.md").read_text(encoding="utf-8")
    assert "\nidea: 2026-10-01-2\n" in intent
    assert [r["to"] for r in out["references"]] == ["2026-10-01-1", "2026-10-01-1", "2026-10-01-2"]
    assert sdlc.inbox_migration(root) == []


def test_migrate_retags_seed_entries_as_ideas(tmp_path: Path, capsys) -> None:
    """Only a live `[seed]` heading becomes `[idea]`; everything else is left byte for byte, and
    readiness nudges until it's done."""
    root = _repo(
        tmp_path,
        "# Inbox\n\n> Example: `## [2026-10-01-9] [seed] Not an entry`\n\n"
        "```\n## [2026-10-01-8] [seed] A fenced example\n```\n\n"
        + _entry("2026-10-01-1", "Keep drafts", "seed", after="2026-10-01-2")
        + _entry("2026-10-01-2", "Share drafts", "Seed")
        + _entry("2026-10-01-3", "Drafts lose their title", "bug")
        + _entry("2026-10-01-4", "Reopen drafts", "building")
        + _entry("2026-10-01-5", "Already an idea"),
    )
    before = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert sdlc.inbox_migration(root) == ["retag 2 [seed] entries as [idea]"]
    sdlc.cmd_readiness(root)
    item = next(i for i in json.loads(capsys.readouterr().out)["items"] if i["name"] == "inbox")
    assert item["status"] == "warn" and "retag 2 [seed] entries as [idea]" in item["detail"]

    code, out = _migrate(root, capsys)
    assert code == 0, out
    assert out["retagged"] == [
        {"id": "2026-10-01-1", "title": "Keep drafts"},
        {"id": "2026-10-01-2", "title": "Share drafts"},
    ]
    after = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert after == before.replace("[2026-10-01-1] [seed]", "[2026-10-01-1] [idea]").replace(
        "[2026-10-01-2] [Seed]", "[2026-10-01-2] [idea]"
    )
    sdlc.cmd_readiness(root)
    item = next(i for i in json.loads(capsys.readouterr().out)["items"] if i["name"] == "inbox")
    assert item["status"] == "ok"
    _git(root, "commit", "-qam", "retagged")
    assert _migrate(root, capsys)[1]["done"] == ["nothing to migrate"]


def test_a_second_migration_has_nothing_to_do(tmp_path: Path, capsys) -> None:
    root = _old_layout(tmp_path)
    assert _migrate(root, capsys)[0] == 0
    before = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    code, out = _migrate(root, capsys)
    assert code == 0 and out["done"] == ["nothing to migrate"]
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == before


def test_migrate_refuses_uncommitted_edits_before_writing(tmp_path: Path, capsys) -> None:
    root = _old_layout(tmp_path)
    (root / ".sdlc" / "DIRECTION.md").write_text(DIRECTION + "\nmore\n", encoding="utf-8")
    code, out = _migrate(root, capsys)
    assert code == 1 and out["refusals"] == ["commit or put back these first: .sdlc/DIRECTION.md"]
    assert (root / ".sdlc" / "work" / "ideas.md").read_text(encoding="utf-8") == OLD_IDEAS


def test_migrate_refuses_both_registers(tmp_path: Path, capsys) -> None:
    root = _old_layout(tmp_path)
    (root / ".sdlc" / "work" / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "both")
    code, out = _migrate(root, capsys)
    assert code == 1 and any(
        "both .sdlc/work/ideas.md and .sdlc/work/inbox.md" in r for r in out["refusals"]
    )


def test_readiness_says_a_repo_has_registers_to_move(tmp_path: Path, capsys) -> None:
    root = _old_layout(tmp_path)
    sdlc.cmd_readiness(root)
    item = next(i for i in json.loads(capsys.readouterr().out)["items"] if i["name"] == "inbox")
    assert item["status"] == "warn" and "migrate-inbox" in item["detail"]


def test_config_names_the_register_a_skill_writes_to(tmp_path: Path, capsys) -> None:
    """Under the shim the writers append to `work/ideas.md`: a second file beside it would hide
    every entry the first holds."""
    root = _old_layout(tmp_path)
    sdlc.cmd_config(root)
    assert json.loads(capsys.readouterr().out)["work"]["register"] == str(
        root / ".sdlc" / "work" / "ideas.md"
    )
    assert _migrate(root, capsys)[0] == 0
    sdlc.cmd_config(root)
    assert json.loads(capsys.readouterr().out)["work"]["register"] == str(
        root / ".sdlc" / "work" / "inbox.md"
    )


def test_migrate_refuses_a_register_it_cant_read_before_moving_it(tmp_path: Path, capsys) -> None:
    root = _old_layout(tmp_path)
    (root / ".sdlc" / "work" / "ideas.md").write_bytes(
        b"# Ideas\n\n## [2026-10-01] [seed] Caf\xe9\n"
    )
    _git(root, "commit", "-qam", "not utf-8")
    code, out = _migrate(root, capsys)
    assert code == 1 and any(
        r.startswith(".sdlc/work/ideas.md can't be read") for r in out["refusals"]
    )
    assert (root / ".sdlc" / "work" / "ideas.md").is_file() and not (
        root / ".sdlc" / "work" / "inbox.md"
    ).exists()
    assert _git(root, "status", "--short") == ""


def test_migrate_and_readiness_name_a_change_open_elsewhere(tmp_path: Path, capsys) -> None:
    """Its `idea:` can't be rewritten from here, so its seed would read `vanished`, not
    `shipped`, against a rewritten `Groups:` line: best migrated with no change open."""
    root = _old_layout(tmp_path)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "ignore worktrees")
    tree = root / ".claude" / "worktrees" / "002-other"
    _git(root, "worktree", "add", "-q", "-b", "002-other", str(tree))
    (tree / ".sdlc" / "work" / "002-other").mkdir(parents=True)
    (tree / ".sdlc" / "work" / "002-other" / "intent.md").write_text(
        OPEN_INTENT.replace("id: 001", "id: 002").replace("slug: share-drafts", "slug: other"),
        encoding="utf-8",
    )
    sdlc.cmd_readiness(root)
    item = next(i for i in json.loads(capsys.readouterr().out)["items"] if i["name"] == "inbox")
    assert "best with no change open" in item["detail"] and "002-other" in item["detail"]
    code, out = _migrate(root, capsys)
    assert code == 0 and out["elsewhere"] == ["002-other"]
