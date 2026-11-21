"""CI on the base branch's tip, read through the tracker (`Tracker.ci()`, `base_ci()`): `status`
names a red one under Problems, ship's question says it, and the reading is cached in the git
common dir (`CI_CACHE`), so `status` reaches the network at most once in `CI_EVERY` per tip."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_base_ci", ROOT / "scripts" / "sdlc.py")
github = _load("sdlc_github_ci", ROOT / "scripts" / "trackers" / "github.py")


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, config: str = '[archive]\ntarget = "github"\n[git]\npush = []\n',
          tracking: bool = True, remote: str = "https://github.com/o/r.git") -> Path:  # fmt: skip
    """A repo on GitHub's tracker whose `origin/main` tracking ref is its tip, as after a push."""
    root = tmp_path / "repo"
    (root / ".sdlc").mkdir(parents=True)
    (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "remote", "add", "origin", remote)
    if tracking:
        _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def _runs(*runs: dict) -> None:
    """Seed the fake gh's workflow runs (the `gh` fixture's state file)."""
    path = Path(os.environ["FAKE_GH_STATE"])
    st = json.loads(path.read_text()) if path.exists() else {"issues": [], "calls": []}
    st["runs"] = list(runs)
    path.write_text(json.dumps(st))


def _run(sha: str, name: str = "check", status: str = "completed", conclusion: str = "success"):
    return {"databaseId": 1, "workflowName": name, "status": status, "conclusion": conclusion,
            "url": f"https://github.com/o/r/actions/runs/{name}", "headSha": sha}  # fmt: skip


def _run_calls(gh) -> list:
    return [c for c in gh()["calls"] if c[:2] == ["run", "list"]]


def _cfg(root: Path) -> dict:
    return sdlc.load_config(root)[0]


def _tip(root: Path) -> str:
    return _git(root, "rev-parse", "refs/remotes/origin/main")


# ---------------------------------------------------------------- the tracker (R1, R11)


@pytest.mark.portable
@pytest.mark.parametrize(
    "runs, state",
    [
        ([], "unknown"),
        ([{"status": "completed", "conclusion": "success"}], "green"),
        ([{"status": "completed", "conclusion": "cancelled"}], "green"),
        ([{"status": "completed", "conclusion": "neutral"}], "green"),
        ([{"status": "in_progress", "conclusion": ""}], "pending"),
        ([{"status": "completed", "conclusion": "success"},
          {"status": "queued", "conclusion": None}], "pending"),
        ([{"status": "completed", "conclusion": "failure"},
          {"status": "queued", "conclusion": None}], "red"),
        ([{"status": "completed", "conclusion": "timed_out"}], "red"),
        ([{"status": "completed", "conclusion": "startup_failure"}], "red"),
    ],
)  # fmt: skip
def test_ci_state_classifies_runs(runs, state) -> None:
    got, why = github.ci_state(runs)
    assert got == state
    assert (why is not None) == (state == "unknown"), "only unknown carries a why"


def test_github_ci_reads_each_state(tmp_path, gh, monkeypatch) -> None:
    """Driven through the fake gh: only a clear failure on the tip itself is red."""
    root = _repo(tmp_path)
    sha = _tip(root)
    t = sdlc.tracker(root, _cfg(root))
    cases = [
        ([_run(sha, "check", conclusion="failure"), _run(sha, "docs")], "red"),
        ([_run(sha), _run(sha, "docs", "in_progress", "")], "pending"),
        ([_run(sha), _run(sha, "docs", conclusion="cancelled")], "green"),
        ([], "unknown"),
        ([_run("0" * 40, conclusion="failure")], "unknown"),  # another commit's run is dropped
    ]
    for runs, state in cases:
        _runs(*runs)
        got = t.ci("main", sha, 10)
        assert got["state"] == state, (runs, got)
        assert set(got) == {"state", "runs", "why"}
        assert all(set(r) == {"name", "status", "conclusion", "url"} for r in got["runs"])
    call = _run_calls(gh)[0]
    assert call[:6] == ["run", "list", "--commit", sha, "--branch", "main"]
    assert call[6:] == ["--json", github.CI_FIELDS, "--limit", "50"]
    _runs(_run(sha, conclusion="failure"))
    monkeypatch.setenv("FAKE_GH_FAIL", "run")
    got = t.ci("main", sha, 10)
    assert got["state"] == "unknown" and "exited 1" in got["why"], "a failed gh is never red"


def test_bad_json_is_unknown(tmp_path, gh) -> None:
    root = _repo(tmp_path)
    path = Path(os.environ["FAKE_GH_STATE"])
    path.write_text(json.dumps({"issues": [], "calls": [], "runs": "not json"}))
    got = sdlc.tracker(root, _cfg(root)).ci("main", _tip(root), 10)
    assert got["state"] == "unknown" and got["why"]


def test_a_hanging_gh_is_unknown(tmp_path, gh, monkeypatch) -> None:
    root = _repo(tmp_path)
    _runs(_run(_tip(root), conclusion="failure"))
    monkeypatch.setenv("FAKE_GH_SLEEP", "5")
    got = sdlc.tracker(root, _cfg(root)).ci("main", _tip(root), 0.5)
    assert got["state"] == "unknown" and "timed out" in got["why"]


def test_core_reads_failures_by_the_trackers_words() -> None:
    """`CI_FAILED` in core names a red run as the GitHub tracker's `CI_RED` does: two copies, one
    meaning, since core never imports a tracker."""
    assert set(sdlc.CI_FAILED) == set(github.CI_RED)


# ---------------------------------------------------------------- core's reading (R2, R3, R6)


@pytest.mark.parametrize(
    "config, tracking, remote, why",
    [
        ('[archive]\ntarget = "none"\n', True, "https://github.com/o/r.git", "archive.target"),
        ('[archive]\ntarget = "github"\n[git]\npush = []\n', False,
         "https://github.com/o/r.git", "tracking ref"),
        ('[archive]\ntarget = "github"\n[git]\npush = []\n', True,
         "https://example.com/o/r.git", "github.com"),
        ('[archive]\ntarget = "command"\ncommand = "true"\n', True,
         "https://github.com/o/r.git", "reads no CI"),
    ],
)  # fmt: skip
def test_base_ci_never_calls_the_tracker_without_a_source(
    tmp_path, gh, config, tracking, remote, why
) -> None:
    root = _repo(tmp_path, config, tracking, remote)
    _runs(_run(_git(root, "rev-parse", "HEAD"), conclusion="failure"))
    got = sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    assert got["state"] == "unknown" and why in got["why"], got
    assert _run_calls(gh) == [], "nothing is called"
    assert not (root / ".git" / sdlc.CI_CACHE).exists(), "nothing read, nothing cached"


def test_base_ci_without_a_base_branch_is_unknown(tmp_path, gh) -> None:
    root = _repo(tmp_path)
    cfg = _cfg(root)
    cfg["git"]["base"] = None
    got = sdlc.base_ci(root, cfg, sdlc.CI_EVERY)
    assert got["state"] == "unknown" and "git.base" in got["why"]
    assert _run_calls(gh) == []


def test_base_ci_reuses_the_cache_for_the_same_tip(tmp_path, gh) -> None:
    root = _repo(tmp_path)
    sha = _tip(root)
    _runs(_run(sha, "check", conclusion="failure"), _run(sha, "docs"))
    first = sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    assert (first["state"], first["branch"], first["sha"]) == ("red", "main", sha)
    assert first["failed"] == ["check"]
    assert first["url"] == "https://github.com/o/r/actions/runs/check"
    assert set(first) == {"state", "branch", "sha", "runs", "failed", "url", "why"}
    cache = root / ".git" / sdlc.CI_CACHE
    saved = json.loads(cache.read_text(encoding="utf-8"))
    assert (saved["branch"], saved["sha"], saved["reading"]["state"]) == ("main", sha, "red")
    assert sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY) == first
    assert len(_run_calls(gh)) == 1, "a second read inside max_age calls nothing"
    _git(root, "commit", "-q", "--allow-empty", "-m", "fix")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    _runs(_run(_tip(root)))
    moved = sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    assert (moved["state"], moved["sha"]) == ("green", _tip(root))
    assert len(_run_calls(gh)) == 2, "a moved tip is read again"


@pytest.mark.parametrize("age", [timedelta(seconds=sdlc.CI_EVERY + 1), timedelta(hours=-1)])
def test_an_old_or_future_cache_is_read_again(tmp_path, gh, age) -> None:
    root = _repo(tmp_path)
    _runs(_run(_tip(root)))
    sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    cache = root / ".git" / sdlc.CI_CACHE
    saved = json.loads(cache.read_text(encoding="utf-8"))
    saved["checked"] = (datetime.now(UTC) - age).isoformat()
    cache.write_text(json.dumps(saved), encoding="utf-8")
    sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    assert len(_run_calls(gh)) == 2
    cache.write_text("{not json", encoding="utf-8")
    assert sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)["state"] == "green"
    assert len(_run_calls(gh)) == 3, "a cache that won't read is read again"


def test_a_raising_tracker_reads_as_unknown(tmp_path, gh, monkeypatch, capsys) -> None:
    root = _repo(tmp_path)

    def boom(self, branch, sha, timeout):
        raise RuntimeError("the tracker broke")

    mod = sdlc._tracker_module("github")
    monkeypatch.setattr(mod.Tracker, "ci", boom)
    got = sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    assert got["state"] == "unknown" and "RuntimeError: the tracker broke" in got["why"]
    assert not (root / ".git" / sdlc.CI_CACHE).exists(), "nothing is cached for it"
    assert sdlc.cli_status(root, root, argparse.Namespace(all=False)) == 0
    assert "Traceback" not in capsys.readouterr().err


def test_the_tracker_is_given_ci_timeout(tmp_path, gh, monkeypatch) -> None:
    root = _repo(tmp_path)
    seen = []
    mod = sdlc._tracker_module("github")
    monkeypatch.setattr(
        mod.Tracker, "ci", lambda self, b, s, t: seen.append(t) or {"state": "green", "runs": []}
    )
    sdlc.base_ci(root, _cfg(root), sdlc.CI_EVERY)
    assert seen == [sdlc.CI_TIMEOUT]


# ---------------------------------------------------------------- status (R4, R5)


def _status(root: Path, capsys) -> str:
    assert sdlc.cli_status(root, root, argparse.Namespace(all=False)) == 0
    return capsys.readouterr().out


def test_status_names_a_red_base(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    sha = _tip(root)
    _runs(_run(sha, "check", conclusion="failure"), _run(sha, "lint", conclusion="timed_out"))
    out = _status(root, capsys)
    line = (
        f"⚠  origin/main: CI is red at {sha[:7]} (check, lint): "
        "https://github.com/o/r/actions/runs/check"
    )
    assert line in out, out
    assert "■ Problems: 1" in out


@pytest.mark.parametrize(
    "runs", [[{"conclusion": "success"}], [{"status": "in_progress", "conclusion": ""}], []]
)
def test_status_is_silent_on_green_pending_and_unknown(tmp_path, gh, capsys, runs) -> None:
    root = _repo(tmp_path)
    _runs(*[_run(_tip(root), **r) for r in runs])
    out = _status(root, capsys)
    assert "CI is" not in out and "Problems: 0" in out, out


def test_vet_strict_never_sees_ci(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _runs(_run(_tip(root), conclusion="failure"))
    assert sdlc.cli_vet(root, root, argparse.Namespace(strict=True)) == 0
    assert "CI is" not in capsys.readouterr().out
    assert _run_calls(gh) == [], "vet reads no CI at all"


def test_status_with_a_fresh_cache_calls_nothing(tmp_path, gh, capsys) -> None:
    root = _repo(tmp_path)
    _runs(_run(_tip(root), conclusion="failure"))
    cache = root / ".git" / sdlc.CI_CACHE
    reading = {"state": "green", "runs": [], "why": None}
    checked = (datetime.now(UTC) - timedelta(seconds=sdlc.CI_EVERY - 30)).isoformat()
    cache.write_text(
        json.dumps({"branch": "main", "sha": _tip(root), "checked": checked, "reading": reading}),
        encoding="utf-8",
    )
    assert "CI is" not in _status(root, capsys)
    assert _run_calls(gh) == []


# ---------------------------------------------------------------- ship's question (R8)

SHIPPED = ".sdlc/work/001-x/ stamped shipped"


def _ask(**kw):
    args = {"folder": ".sdlc/work/001-x", "closes": [], "target": "none", "context": False,
            "nits": False, "closing": [], "split": [],
            "register": ".sdlc/work/inbox.md"}  # fmt: skip
    return sdlc.ship_question(**(args | kw))


def _reading(state: str) -> dict:
    red = state == "red"
    return {"state": state, "branch": "main", "sha": "abcdef1234567890", "runs": [],
            "failed": ["check"] if red else [], "url": "https://ci/1" if red else None,
            "why": None if state != "unknown" else "no CI"}  # fmt: skip


def test_ship_question_names_a_red_base() -> None:
    question, why = _ask(ci=_reading("red"), sensitive=["check.sh"])
    assert why is None
    assert question == (
        "Commit this, touching sensitive path check.sh, on a base whose CI is red at abcdef1 "
        f"(https://ci/1), and {SHIPPED}? (yes / edit the message)"
    )
    for state in ("green", "pending", "unknown"):
        question, _ = _ask(ci=_reading(state))
        assert "CI is red" not in question, state
    assert "CI is red" not in _ask()[0]


def test_ship_question_command_reads_ci_itself(tmp_path, gh, capsys) -> None:
    """`preflight --question` reads the base's CI itself, so the skill can't leave it out."""
    root = _repo(tmp_path)
    sha = _tip(root)
    _runs(_run(sha, conclusion="failure"))
    _git(root, "checkout", "-q", "-b", "001-x")
    folder = root / ".sdlc" / "work" / "001-x"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        "---\nid: 001\nslug: x\ntier: 1\nimpact:\nstage: build\ncreated: 2026-11-21\n"
        "updated: 2026-11-21\nidea:\ndepends_on:\n---\n\n# 001 — X\n",
        encoding="utf-8",
    )
    assert sdlc.cmd_ship_question(root, "001", False, False, [], []) == 0
    out = capsys.readouterr().out
    assert f"on a base whose CI is red at {sha[:7]} " in out, out
