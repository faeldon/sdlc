"""This repo's retrospective evidence: reported bugs counted per release window, from fixture
issues shaped like `gh issue list --json labels,createdAt,state` and made-up tag times.
"""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sdlc_evidence_test", ROOT / ".sdlc" / "evidence.py")
evidence = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evidence)

TAGS = [
    ("v1.0.0", datetime(2026, 10, 1, 12, 0, tzinfo=UTC)),
    ("v1.1.0", datetime(2026, 10, 10, 12, 0, tzinfo=UTC)),
]


def _issue(created: str, *labels: str, state: str = "OPEN") -> dict:
    return {"createdAt": created, "state": state, "labels": [{"name": n} for n in labels]}


def _by_window(rows: list[dict]) -> dict[str, dict]:
    return {r["window"]: r for r in rows}


def test_change_issues_are_not_counted():
    rows = _by_window(evidence.count([_issue("2026-10-05T00:00:00Z", "bug", "sdlc")], TAGS))
    assert all(r["reported"] == 0 for r in rows.values())


def test_an_issue_falls_in_the_window_its_tag_closes():
    issues = [
        _issue("2026-09-30T00:00:00Z", "bug"),
        _issue("2026-10-01T12:00:00Z", "bug"),  # exactly at the tag: still that release's
        _issue("2026-10-01T12:00:01Z", "bug"),
        _issue("2026-10-11T00:00:00Z", "bug"),
    ]
    rows = _by_window(evidence.count(issues, TAGS))
    assert [rows[w]["reported"] for w in ("v1.0.0", "v1.1.0", "unreleased")] == [2, 1, 1]


def test_areas_lost_work_and_open_are_counted():
    issues = [
        _issue("2026-10-05T00:00:00Z", "bug", "area: setup"),
        _issue("2026-10-05T00:00:00Z", "bug", "area: close", state="CLOSED"),
        _issue("2026-10-05T00:00:00Z", "bug", "area: new", "lost-work"),
    ]
    row = _by_window(evidence.count(issues, TAGS))["v1.1.0"]
    assert row == {
        "window": "v1.1.0", "reported": 3, "open": 2,
        "setup": 1, "new": 1, "close": 1, "lost-work": 1,
    }  # fmt: skip


def test_no_tags_is_one_unreleased_window():
    rows = evidence.count([_issue("2026-10-05T00:00:00Z", "bug")], [])
    assert [(r["window"], r["reported"]) for r in rows] == [("unreleased", 1)]


def test_render_prints_counts_only():
    text = evidence.render(evidence.count([_issue("2026-10-05T00:00:00Z", "bug")], TAGS))
    assert text.splitlines()[2] == (
        "  v1.1.0       reported=1 open=1 setup=0 new=0 close=0 lost-work=0"
    )
    assert len(text.splitlines()) == 4


def test_a_failing_gh_is_an_exit_and_stderr_never_a_count(monkeypatch, capsys):
    def refuse(_root):
        raise evidence.subprocess.CalledProcessError(1, "gh", stderr="gh: not logged in\n")

    monkeypatch.setattr(evidence, "bug_issues", refuse)
    assert evidence.main() == 1
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == "evidence: gh: not logged in\n"
