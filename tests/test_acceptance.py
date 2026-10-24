"""A change's acceptance checks: `## ` sections of its checks.md, each one `sh` block. `checks`
lists them and runs nothing; `accept` runs them from the change's checkout root, and is never
allowed without a prompt, since an agent may have written them.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_accept", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

INTENT = """\
---
id: 001
slug: reopen-drafts
tier: 1
impact:
stage: build
created: 2026-10-01
updated: 2026-10-02
idea:
depends_on:
---

# 001 — Reopen drafts

## Problem

Real prose.

## Outcome

Real prose.
"""
NAME = "001-reopen-drafts"


def _check(name: str, command: str, why: str = "Only a revert could fail it.") -> str:
    return f"## {name}\n\n{why}\n\n```sh\n{command}\n```\n"


def _checks(*sections: str) -> str:
    return "# Checks\n\n> The change's checks.\n\n" + "\n".join(sections)


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    folder = root / "work" / NAME
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _write(repo: Path, text: str) -> None:
    (repo / "work" / NAME / "checks.md").write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "checks")


def _read(repo: Path) -> dict:
    return sdlc.acceptance(repo / "work" / NAME)


def _cmd(capsys, fn, repo: Path) -> tuple[int, dict]:
    code = fn(repo, "001")
    return code, json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------- R1: the template


def test_config_lists_the_checks_template(repo: Path, capsys) -> None:
    sdlc.cmd_config(repo)
    out = json.loads(capsys.readouterr().out)
    assert out["templates"]["checks.md"]["source"] == "plugin"


def test_the_template_itself_is_unfilled(repo: Path) -> None:
    _write(repo, (ROOT / "templates" / "checks.md").read_text(encoding="utf-8"))
    found = _read(repo)
    assert found["checks"] == []
    assert found["problems"] == ["checks.md is still the template: fill it or delete it"]


# ---------------------------------------------------------------- R2: reading it


def test_no_checks_file_is_no_checks(repo: Path) -> None:
    assert _read(repo) == {"path": "checks.md", "exists": False, "checks": [], "problems": []}


def test_a_good_file_lists_each_check_in_order(repo: Path) -> None:
    text = _checks(
        _check("The flag reads", "grep -q flag README.md"),
        "## The page shows it\n\nWhat it printed:\n\n```text\nok\n```\n\n"
        "```sh\ntest -f README.md\n```\n",
    )
    _write(repo, text)
    found = _read(repo)
    assert found["problems"] == []
    assert found["checks"] == [
        {"name": "The flag reads", "command": "grep -q flag README.md"},
        {"name": "The page shows it", "command": "test -f README.md"},
    ], "a non-sh fence is prose, not a second command"


@pytest.mark.parametrize(
    ("text", "why"),
    [
        (_checks("## No command\n\nJust prose.\n"), "## No command: holds 0 `sh` blocks, not one"),
        (
            _checks("## Two\n\n```sh\ntrue\n```\n\n```sh\ntrue\n```\n"),
            "## Two: holds 2 `sh` blocks, not one",
        ),
        (
            _checks(_check("Same", "true"), _check("Same", "true")),
            "## Same: its name is used twice",
        ),
        ("# Checks\n\n```sh\ntrue\n```\n\n" + _check("Later", "true"), "above the first `## `"),
        (_checks("## Open\n\n```sh\ntrue\n"), "a fenced block is never closed"),
    ],
    ids=["no-sh", "two-sh", "duplicate", "above", "unclosed"],
)
def test_checks_problem(repo: Path, text: str, why: str) -> None:
    _write(repo, text)
    problems = _read(repo)["problems"]
    assert any(why in p for p in problems), problems


def test_an_unreadable_file_is_a_problem(repo: Path) -> None:
    (repo / "work" / NAME / "checks.md").write_bytes(b"## Bad\n\n\xff\xfe\n")
    assert any("can't be read" in p for p in _read(repo)["problems"])


def test_check_strict_reports_them(repo: Path, monkeypatch, capsys) -> None:
    _write(repo, _checks("## No command\n\nJust prose.\n"))
    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "check", "--strict"])
    assert sdlc.main() == 1
    kinds = [p["kind"] for p in sdlc.analyze(repo)["problems"]]
    assert kinds == ["checks"]


# ---------------------------------------------------------------- R3: listing


def test_checks_lists_and_runs_nothing(repo: Path, capsys) -> None:
    _write(repo, _checks(_check("Makes a file", "touch made.txt")))
    code, out = _cmd(capsys, sdlc.cmd_checks, repo)
    assert code == 0
    assert out["change"] == NAME and out["checks"][0]["command"] == "touch made.txt"
    assert not (repo / "made.txt").exists()


def test_checks_is_allowed_and_accept_never_is() -> None:
    allowed = " ".join(sdlc.ALLOW_RULES)
    assert "sdlc.py checks *" in allowed
    assert "sdlc.py accept" not in allowed
    assert "accept" not in sdlc.READ_ONLY


# ---------------------------------------------------------------- R4: running


def test_accept_passes_and_fails_by_exit_code(repo: Path, capsys) -> None:
    _write(repo, _checks(_check("Holds", "true"), _check("Broke", "echo nope; exit 3")))
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 1 and out["passed"] is False
    by = {c["name"]: c for c in out["checks"]}
    assert by["Holds"]["passed"] and by["Holds"]["exit"] == 0
    assert not by["Broke"]["passed"] and by["Broke"]["exit"] == 3
    assert "nope" in by["Broke"]["output"]


def test_accept_times_out(repo: Path, capsys, monkeypatch) -> None:
    monkeypatch.setattr(sdlc, "CHECK_TIMEOUT", 1)
    _write(repo, _checks(_check("Hangs", "sleep 5")))
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 1
    assert out["checks"][0]["exit"] is None and "timed out" in out["checks"][0]["output"]


def test_accept_fails_a_check_that_dirties_the_tree(repo: Path, capsys) -> None:
    _write(repo, _checks(_check("Leaves a file", "touch stray.txt")))
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 1
    check = out["checks"][0]
    assert check["exit"] == 0 and not check["passed"]
    assert check["left"] == ["?? stray.txt"]


def test_accept_leaves_work_already_uncommitted_alone(repo: Path, capsys) -> None:
    _write(repo, _checks(_check("Reads", "grep -q edited README.md")))
    (repo / "README.md").write_text("edited\n", encoding="utf-8")
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 0, "the change's own uncommitted work isn't the check's doing"
    assert out["checks"][0]["left"] == []


def test_accept_runs_from_the_checkout_root(repo: Path, capsys, monkeypatch) -> None:
    _write(repo, _checks(_check("Where", "pwd")))
    monkeypatch.chdir(repo / "work")
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 0
    assert Path(out["checks"][0]["output"].strip()).resolve() == repo.resolve()


def test_accept_with_no_file_passes(repo: Path, capsys) -> None:
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 0 and out == {"change": NAME, "checks": [], "passed": True, "problems": []}


def test_accept_refuses_a_bad_file(repo: Path, capsys) -> None:
    _write(repo, _checks("## No command\n\nJust prose.\n"))
    code, out = _cmd(capsys, sdlc.cmd_accept, repo)
    assert code == 1 and out["passed"] is False and out["problems"]
