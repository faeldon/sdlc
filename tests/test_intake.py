"""Intake: GitHub issues filed into work/inbox.md as entries carrying `Issue: #N`, or attached to an
open change's `closes:` line, which close closes when the change lands. `check` audits both."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_intake", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

INTENT = """\
---
id: {id}
slug: {slug}
tier: 1
impact:
stage: build
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
closes: [{closes}]
---

# {id} — {slug}
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _entry(entry_id: str, title: str, tag: str = "idea", extra: str = "") -> str:
    return f"## [{entry_id}] [{tag}] {title}\n\nWhat it asks for.\n\n{extra}\n"


def _repo(tmp_path: Path, *entries: str) -> Path:
    root = tmp_path / "repo"
    (root / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "work" / "inbox.md").write_text("# Inbox\n\n" + "".join(entries), encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _change(root: Path, name: str, closes: str) -> Path:
    number, slug = name.split("-", 1)
    folder = root / "work" / name
    folder.mkdir(parents=True, exist_ok=True)
    text = INTENT.format(id=number, slug=slug, closes=closes)
    (folder / "intent.md").write_text(text, encoding="utf-8")
    return folder


def _problems(root: Path, kind: str) -> list[str]:
    return [p["detail"] for p in sdlc.analyze(root)["problems"] if p["kind"] == kind]


# R1. An entry carries its issues, the first the others' parent.


def test_an_entry_reads_its_issues_in_order(tmp_path: Path) -> None:
    root = _repo(tmp_path, _entry("2026-10-01-1", "Keep drafts", extra="Issue: #12, #15\n"))
    entry = sdlc.inbox_entries(root)[0]
    assert entry["fields"]["Issue"] == "#12, #15"
    assert sdlc.entry_issues(entry) == [12, 15]
    assert _problems(root, "issue") == []


def test_an_entry_with_no_issue_line_names_none(tmp_path: Path) -> None:
    root = _repo(tmp_path, _entry("2026-10-01-1", "Keep drafts"))
    assert sdlc.entry_issues(sdlc.inbox_entries(root)[0]) == []


def test_check_reports_an_issue_not_written_as_a_number(tmp_path: Path) -> None:
    root = _repo(tmp_path, _entry("2026-10-01-1", "Keep drafts", extra="Issue: 12\n"))
    assert _problems(root, "issue") == ["2026-10-01-1: Issue: names each issue as #N, got '12'"]


def test_check_reports_one_issue_on_two_entries(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        _entry("2026-10-01-1", "Keep drafts", extra="Issue: #12\n"),
        _entry("2026-10-01-2", "Reopen drafts", tag="bug", extra="Severity: low\nIssue: #12\n"),
    )
    assert _problems(root, "issue") == ["#12 is on 2 entries: 2026-10-01-1, 2026-10-01-2"]


# R6. A change's `closes:` line names the issues it closes, whatever their kind.


def test_closes_reads_issue_numbers_as_written(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _change(root, "030-keep-drafts", "12, 15")
    rec = sdlc.analyze(root)["open"][0]
    assert rec["closes"] == [12, 15]
    assert not [e for e in rec["errors"] if e.startswith("closes:")]


def test_closes_refuses_a_value_that_is_not_a_number_or_is_its_own(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _change(root, "030-keep-drafts", "12a, 30, x")
    rec = sdlc.analyze(root)["open"][0]
    assert [e for e in rec["errors"] if e.startswith("closes:")] == [
        "closes: '12a' isn't an issue number: write it bare, `12`",
        "closes: names this change's own issue",
        "closes: 'x' isn't an issue number: write it bare, `12`",
    ]
    assert rec["closes"] == []


def test_check_reports_two_open_changes_closing_one_issue(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _change(root, "030-keep-drafts", "12")
    _change(root, "031-reopen-drafts", "12, 14")
    assert _problems(root, "closes") == [
        "#12 is on the closes: line of 030-keep-drafts, 031-reopen-drafts"
    ]


def test_an_intent_without_closes_reads_as_before(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    folder = _change(root, "030-keep-drafts", "")
    text = (folder / "intent.md").read_text(encoding="utf-8").replace("closes: []\n", "")
    (folder / "intent.md").write_text(text, encoding="utf-8")
    rec = sdlc.analyze(root)["open"][0]
    assert rec["closes"] == [] and rec["errors"] == []
