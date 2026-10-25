"""The register of change requests, `work/inbox.md`: its entries, the shim that still reads a repo's
`work/ideas.md`, and the host template kept under the old name."""

from __future__ import annotations

import importlib.util
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
    (tmp_path / "work").mkdir(exist_ok=True)
    (tmp_path / "work" / name).write_text(text, encoding="utf-8")
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
    assert sdlc.register_path(root / "work") == root / "work" / "ideas.md"
    assert [e["title"] for e in sdlc.inbox_entries(root)] == [
        "Reopen drafts",
        "Close leaves the worktree",
    ]


def test_with_both_registers_the_inbox_is_read_and_check_says_so(tmp_path: Path) -> None:
    root = _work(tmp_path, "inbox.md", "# Inbox\n\n## [2026-10-03-1] [seed] Only here\n\nx\n")
    _work(tmp_path, "ideas.md")
    assert [e["title"] for e in sdlc.inbox_entries(root)] == ["Only here"]
    problems = sdlc.analyze(root)["problems"]
    assert [p["dir"] for p in problems if p["kind"] == "register"] == ["work/ideas.md"]


def test_no_register_is_no_entries(tmp_path: Path) -> None:
    assert sdlc.inbox_entries(tmp_path) == []
    assert sdlc.register_path(tmp_path / "work") == tmp_path / "work" / "inbox.md"


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
