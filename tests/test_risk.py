"""`[review]`'s sensitive and irreversible paths: what a change's diff touches of them, the `risk`
part of `preflight`, and the clauses ship's question carries for a deep diff."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_risk", ROOT / "scripts" / "sdlc.py")
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
updated: 2026-10-01
idea:
depends_on:
---

# 001 — Reopen drafts
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, config: str = "") -> Path:
    """A repo on a change's branch whose diff adds a CI workflow, edits a migration and renames
    a script into `release/`."""
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    (root / "migrations").mkdir()
    (root / "migrations" / "001.sql").write_text("create\n", encoding="utf-8")
    (root / "tools").mkdir()
    (root / "tools" / "cut.sh").write_text("echo cut\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", "001-reopen-drafts")
    folder = root / ".sdlc" / "work" / "001-reopen-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
    (root / "migrations" / "001.sql").write_text("create table\n", encoding="utf-8")
    (root / "release").mkdir()
    _git(root, "mv", "tools/cut.sh", "release/cut.sh")
    return root


SENSITIVE = """\
[review]
sensitive = [".github/", "tools/*.sh"]
irreversible = ["migrations/*.sql"]
"""


def test_review_lists_default_empty_and_take_a_host_s_values(tmp_path: Path) -> None:
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert cfg["review"] == {"sensitive": [], "irreversible": []} and warnings == []
    (tmp_path / ".sdlc").mkdir()
    (tmp_path / ".sdlc" / "config.toml").write_text(SENSITIVE, encoding="utf-8")
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert cfg["review"]["sensitive"] == [".github/", "tools/*.sh"] and warnings == []


def test_a_review_list_that_isn_t_one_is_warned_not_raised(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir()
    (tmp_path / ".sdlc" / "config.toml").write_text(
        '[review]\nsensitive = ".github/"\n', encoding="utf-8"
    )
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert cfg["review"]["sensitive"] == []
    assert warnings == ["review.sensitive must be a list of paths"]


@pytest.mark.parametrize(
    "path, pattern, hit",
    [
        (".github/workflows/ci.yml", ".github/", True),
        (".githubx/ci.yml", ".github/", False),
        ("scripts/release/cut.sh", "scripts/*.sh", True),
        ("scripts/cut.py", "scripts/*.sh", False),
        ("check.sh", "check.sh", True),
        ("docs/check.sh", "check.sh", False),
    ],
)
def test_a_trailing_slash_is_a_prefix_and_anything_else_a_glob(path, pattern, hit) -> None:
    assert (sdlc.risk_paths([path], [pattern]) == [path]) is hit


def test_no_lists_means_nothing_is_risky(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    risk = sdlc._risk_report(root, root / ".sdlc" / "work" / "001-reopen-drafts")
    assert risk == {"sensitive": [], "irreversible": [], "deep": False}


def test_the_risk_part_names_what_the_diff_touches(tmp_path: Path) -> None:
    """A rename counts by both its paths: moving a sensitive script away is still touching it."""
    root = _repo(tmp_path, SENSITIVE)
    risk = sdlc._risk_report(root, root / ".sdlc" / "work" / "001-reopen-drafts")
    assert sorted(risk["sensitive"]) == [".github/workflows/ci.yml", "tools/cut.sh"]
    assert risk["irreversible"] == ["migrations/001.sql"] and risk["deep"] is True


def test_preflight_carries_the_risk_part(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, SENSITIVE)
    sdlc.cmd_preflight(root, "001")
    out = json.loads(capsys.readouterr().out)
    assert out["risk"]["deep"] is True and out["risk"]["irreversible"] == ["migrations/001.sql"]


def _ask(**kw) -> str:
    args = {"folder": ".sdlc/work/001-reopen-drafts", "closes": [], "target": "none",
            "context": False, "nits": False, "closing": [], "split": [],
            "register": ".sdlc/work/inbox.md"}  # fmt: skip
    question, why = sdlc.ship_question(**(args | kw))
    assert why is None
    return question


def test_the_question_names_sensitive_paths_five_then_how_many_more() -> None:
    assert "touching sensitive path a.yml, and" in _ask(sensitive=["a.yml"])
    assert "touching sensitive paths a and b, and" in _ask(sensitive=["a", "b"])
    many = _ask(sensitive=[f"p{i}" for i in range(7)])
    assert "touching sensitive paths p0, p1, p2, p3, p4 and 2 more, and" in many
    assert "sensitive" not in _ask()


def test_the_question_says_a_skipped_fresh_review_and_a_recovery() -> None:
    assert "without the fresh review (no Agent tool here)" in _ask(
        fresh_skipped="no Agent tool here"
    )
    assert "with how to recover it shown" in _ask(irreversible=True)
    plain = _ask()
    assert "fresh review" not in plain and "recover" not in plain


def test_the_command_reads_the_diff_itself(tmp_path: Path, capsys) -> None:
    """The skill can't leave a sensitive path out: the script finds them."""
    root = _repo(tmp_path, SENSITIVE)
    assert sdlc.cmd_ship_question(root, "001", False, False, [], []) == 0
    printed = capsys.readouterr().out
    assert "touching sensitive paths" in printed and ".github/workflows/ci.yml" in printed
    assert "with how to recover it shown" in printed


def test_ship_never_changes_the_tier_from_risk() -> None:
    ship = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    assert "Risk never changes the tier" in ship
