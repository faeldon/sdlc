"""091: `sdlc.py gate`, the gate run by hand, and the record the board and status read.

The record is the factory's shape (`build/round-<N>.gate.md`), copied rather than imported: each
plugin is cached on its own. The copies are pinned to `factory.py` here.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_hand_gate", ROOT / "scripts" / "sdlc.py")
factory = _load("factory_hand_gate", ROOT / "plugins" / "factory" / "scripts" / "factory.py")

NAME = "008-reopen-drafts"
INTENT = """\
---
id: 008
slug: reopen-drafts
tier: 1
stage: build
created: 2026-11-17
updated: 2026-11-17
idea:
---

# 008 — Reopen drafts

## Problem

Written.
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _base_check(root: Path, command: str | None) -> None:
    """Commit `[commands] check` on `main`, then go back to the change's branch."""
    here = _git(root, "branch", "--show-current")
    if here != "main":
        _git(root, "checkout", "-q", "main")
    text = '[git]\nbase = "main"\n'
    if command is not None:
        text += f"[commands]\ncheck = {json.dumps(command)}\n"
    _write(root / ".sdlc" / "config.toml", text)
    _git(root, "add", ".sdlc/config.toml")
    _git(root, "commit", "-q", "-m", "gate")
    if here != "main":
        _git(root, "checkout", "-q", here)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo on `main` holding a check, and a change built by hand on its own branch."""
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "README.md", "a repo\n")
    _write(root / "src" / "app.py", "x = 1\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _base_check(root, "echo base-ran")
    _git(root, "checkout", "-q", "-b", NAME)
    _write(root / ".sdlc" / "work" / NAME / "intent.md", INTENT)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "intent")
    _write(root / "src" / "app.py", "x = 2\n")
    return root


def _folder(root: Path) -> Path:
    return root / ".sdlc" / "work" / NAME


# ---------------------------------------------------------------- the build (R6)


@pytest.mark.portable
def test_the_build_hash_is_stable_and_survives_committing_the_work(repo) -> None:
    first = sdlc.hand_build(repo, "main")
    assert len(first) == 16 and int(first, 16) >= 0
    assert sdlc.hand_build(repo, "main") == first
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "built")
    assert sdlc.hand_build(repo, "main") == first, "ship's commit of the same work"


@pytest.mark.portable
def test_the_build_hash_moves_with_the_code_never_the_change_folder(repo) -> None:
    first = sdlc.hand_build(repo, "main")
    _write(_folder(repo) / "notes.md", "# Notes\n")
    _write(_folder(repo) / "build" / "gate.md", "GATE: PASS\n")
    _write(repo / ".sdlc" / "last-id", "8\n")
    assert sdlc.hand_build(repo, "main") == first, "the folder and the counter are no build"
    _write(repo / "src" / "new.py", "y = 1\n")
    second = sdlc.hand_build(repo, "main")
    assert second != first, "an untracked file is part of the build"
    (repo / "README.md").unlink()
    assert sdlc.hand_build(repo, "main") not in (first, second), "so is a deletion"


@pytest.mark.portable
def test_the_build_hash_moves_on_a_rebase_onto_a_moved_base(repo) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "built")
    first = sdlc.hand_build(repo, "main")
    _git(repo, "checkout", "-q", "main")
    _write(repo / "OTHER.md", "elsewhere\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "moved")
    _git(repo, "checkout", "-q", NAME)
    assert sdlc.hand_build(repo, "main") == first, "a base moving without a rebase: `behind`'s"
    _git(repo, "rebase", "-q", "main")
    assert sdlc.hand_build(repo, "main") != first


# ---------------------------------------------------------------- the command (R1–R5, R13, R14)


def _gate(root: Path, capsys, ident: str = "008") -> tuple[int, dict | None]:
    code = sdlc.cmd_gate(root, ident)
    out = capsys.readouterr().out
    return code, json.loads(out) if out.strip() else None


def _record(root: Path) -> str:
    return (_folder(root) / sdlc.HAND_GATE).read_text(encoding="utf-8")


def test_the_gate_runs_the_base_branchs_check_never_the_checkouts(repo, capsys) -> None:
    """R1: a change can't edit the gate it is judged by."""
    mine = '[git]\nbase = "main"\n[commands]\ncheck = "echo mine"\n'
    _write(repo / ".sdlc" / "config.toml", mine)
    code, out = _gate(repo, capsys)
    assert code == 0 and out["verdict"] == "PASS"
    record = _record(repo)
    assert "    base-ran\n" in record and "mine" not in record
    assert "Command: echo base-ran\n" in record


def _no_trunk(root: Path) -> None:
    _write(root / ".sdlc" / "config.toml", '[git]\nbase = "gone"\n')


def _no_check(root: Path) -> None:
    _base_check(root, None)


def _bad_config(root: Path) -> None:
    _git(root, "checkout", "-q", "main")
    _write(root / ".sdlc" / "config.toml", "[commands\n")
    _git(root, "commit", "-q", "-am", "broken")
    _git(root, "checkout", "-q", NAME)


def _ambiguous(root: Path) -> None:
    _write(root / ".sdlc" / "work" / "008-other-thing" / "intent.md", INTENT)


def _factory_run(root: Path) -> None:
    _write(_folder(root) / "runs" / "builder.sessions", "s-1\n")


def _other_branch(root: Path) -> None:
    _git(root, "checkout", "-q", "-b", "elsewhere")


@pytest.mark.parametrize(
    ("setup", "ident"),
    [
        (_no_trunk, "008"),
        (_no_check, "008"),
        (_bad_config, "008"),
        (lambda root: None, "099"),
        (_ambiguous, "008"),
        (_factory_run, "008"),
        (_other_branch, "008"),
    ],
    ids=["no-base-branch", "no-check", "bad-config", "no-change", "ambiguous", "factory", "branch"],
)
def test_gate_refuses_and_writes_nothing(repo, capsys, setup, ident) -> None:
    """R2: each refusal exits 1 before anything runs or is written."""
    setup(repo)
    code, _ = _gate(repo, capsys, ident)
    assert code == 1
    assert not (_folder(repo) / sdlc.HAND_GATE).exists()
    assert not (repo / ".sdlc" / "work" / "008-other-thing" / sdlc.HAND_GATE).exists()


def _masked(text: str) -> list[str]:
    return [
        "Build: *" if sdlc.BUILD_RE.match(line)
        else "Seconds: *" if sdlc.SECONDS_RE.match(line)
        else line
        for line in text.splitlines()
    ]  # fmt: skip


def test_the_record_is_the_factorys_shape_line_for_line(repo, capsys, monkeypatch) -> None:
    """R3, R5: `factory.py gate` and `sdlc.py gate` on the same build and the same check write the
    same record, a red attempt then a green one, the machine's paths written as placeholders."""
    monkeypatch.setenv("HOME", str(repo.parent))
    _base_check(repo, 'echo "at $PWD under $HOME"; echo base-ran; test -z "$FAKE_GATE_FAIL"')
    _write(_folder(repo) / "build" / "round-1.md", "Built slice 1.\n")
    monkeypatch.setenv("FAKE_GATE_FAIL", "1")
    assert factory.cmd_gate(repo, "008") == 1
    assert sdlc.cmd_gate(repo, "008") == 1
    monkeypatch.delenv("FAKE_GATE_FAIL")
    assert factory.cmd_gate(repo, "008") == 0
    assert sdlc.cmd_gate(repo, "008") == 0
    capsys.readouterr()
    theirs = (_folder(repo) / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    ours = _record(repo)
    assert _masked(ours) == _masked(theirs)
    assert ours.startswith("GATE: PASS\n") and ours.count("## Attempt ") == 2
    assert "    at <path-to-clone> under ~\n" in ours and str(repo) not in ours


@pytest.mark.portable
def test_the_copies_are_the_factorys() -> None:
    """R3: the record's regexes and figures are `factory.py`'s."""
    for name in ("ATTEMPT_VERDICT_RE", "BUILD_RE", "SECONDS_RE"):
        assert getattr(sdlc, name).pattern == getattr(factory, name).pattern, name
    for name in ("GATE_TAIL", "GATE_TIMEOUT", "CLONE_MARK", "HOME_MARK"):
        assert getattr(sdlc, name) == getattr(factory, name), name


def test_the_placeholders_are_the_factorys(repo, monkeypatch) -> None:
    """R5: the main checkout, then the change's checkout, then home, from inside a worktree."""
    monkeypatch.setenv("HOME", str(repo.parent))
    tree = repo / ".claude" / "worktrees" / "009-elsewhere"
    _git(repo, "worktree", "add", "-q", "-b", "009-elsewhere", str(tree), "main")
    outside = repo.parent / "cache" / "venv"
    text = (
        f"{repo}/x and {tree}/y and {outside} and {tree.resolve().as_posix()}/z\n"
        f"{repo.resolve()}/w\n"
    )
    ours = sdlc._hand_placeholders(text, tree)
    assert ours == factory._placeholders(text, tree)
    assert str(repo) not in ours and f"{sdlc.HOME_MARK}/cache/venv" in ours


@pytest.mark.parametrize(
    ("command", "verdict", "exit_", "tree"),
    [
        ("true", "PASS", "0", "unchanged"),
        ("echo no; exit 3", "FAIL", "3", "unchanged"),
        ("exec sleep 5", "FAIL", "timeout", "unchanged"),
        ("printf more >> src/app.py", "FAIL", "0", "changed: src/app.py"),
    ],
    ids=["pass", "fail", "timeout", "tree"],
)
def test_each_outcome_is_recorded(repo, capsys, monkeypatch, command, verdict, exit_, tree):
    """R4: PASS only on exit 0, in time, with the tree as it was; the summary says which."""
    _base_check(repo, command)
    monkeypatch.setattr(sdlc, "GATE_TIMEOUT", 0.5)
    code, out = _gate(repo, capsys)
    assert code == (0 if verdict == "PASS" else 1)
    assert (out["verdict"], out["exit"], out["tree"], out["attempt"]) == (verdict, exit_, tree, 1)
    assert out["change"] == NAME and out["to"] == f".sdlc/work/{NAME}/build/gate.md"
    assert isinstance(out["seconds"], float)
    record = _record(repo)
    assert record.startswith(f"GATE: {verdict}\n")
    assert f"\nExit: {exit_}\n" in record and f"\nTree: {tree}\n" in record


def test_a_check_that_cannot_start_is_recorded(repo, capsys, monkeypatch) -> None:
    """R4: `didn't run`, its reason as the output."""

    def no_shell(command: str) -> list[str]:
        raise OSError("no sh on PATH")

    monkeypatch.setattr(sdlc, "_sh", no_shell)
    code, out = _gate(repo, capsys)
    assert code == 1 and (out["verdict"], out["exit"]) == ("FAIL", "didn't run")
    assert "    didn't run: no sh on PATH\n" in _record(repo)


@pytest.mark.portable
def test_the_record_is_written_with_unix_newlines(repo, capsys) -> None:
    """R14."""
    _gate(repo, capsys)
    _gate(repo, capsys)
    raw = (_folder(repo) / sdlc.HAND_GATE).read_bytes()
    assert b"\r" not in raw and raw.decode("utf-8").count("## Attempt ") == 2


@pytest.mark.portable
def test_gate_is_never_pre_approved() -> None:
    """R13: it runs a command and writes, so the harness asks first; it runs the change's own
    script, as every command ship's worktree runs that writes."""
    assert "gate" in sdlc.OWN_SCRIPT_CMDS
    assert "gate" not in sdlc.READ_ONLY
    run = "uv run --quiet --script /x/scripts/sdlc.py gate 008"
    assert not any(
        re.fullmatch(re.escape(r).replace(r"\*", ".*"), f"Bash({run})") for r in sdlc.ALLOW_RULES
    )
    skills = [*ROOT.glob("skills/*/*.md"), *ROOT.glob("plugins/*/skills/*/*.md")]
    for path in skills:
        assert "sdlc.py gate" not in path.read_text(encoding="utf-8"), path


# ---------------------------------------------------------------- the reader (R7)


def test_hand_gate_reads_none_current_and_stale(repo, capsys, monkeypatch) -> None:
    """R7: None without a record; the last attempt's verdict, current while the build is the one
    it judged and the checkout is on the change's branch."""
    folder = _folder(repo)
    assert sdlc.hand_gate(folder, repo, "main") is None
    _base_check(repo, 'test -z "$FAKE_GATE_FAIL"')
    monkeypatch.setenv("FAKE_GATE_FAIL", "1")
    _gate(repo, capsys)
    monkeypatch.delenv("FAKE_GATE_FAIL")
    _gate(repo, capsys)
    got = sdlc.hand_gate(folder, repo, "main")
    assert {k: got[k] for k in ("verdict", "current", "exit", "attempts", "fails")} == {
        "verdict": "PASS", "current": True, "exit": "0", "attempts": 2, "fails": 1,
    }  # fmt: skip
    assert isinstance(got["seconds"], float) and got["path"] == f".sdlc/work/{NAME}/build/gate.md"
    assert "problems" not in got
    _write(folder / "notes.md", "# Notes\n")
    assert sdlc.hand_gate(folder, repo, "main")["current"], "the folder is no build"
    _write(repo / "src" / "app.py", "x = 3\n")
    assert sdlc.hand_gate(folder, repo, "main")["current"] is False
    _write(repo / "src" / "app.py", "x = 2\n")
    assert sdlc.hand_gate(folder, repo, "main")["current"]
    _git(repo, "checkout", "-q", "-b", "elsewhere")
    assert sdlc.hand_gate(folder, repo, "main")["current"] is False, "another branch"
    assert sdlc.hand_gate(folder, repo, None)["current"] is False, "no base branch"


@pytest.mark.parametrize(
    "text", ["GATE: PASS\n", "GATE: PASS\n\n## Attempt 1\n\nCommand: true\n", "\x00garbled"]
)
def test_a_malformed_record_is_a_problem_never_current(repo, text) -> None:
    """R7: never raises."""
    _write(_folder(repo) / sdlc.HAND_GATE, text)
    got = sdlc.hand_gate(_folder(repo), repo, "main")
    assert got["current"] is False and got["problems"], got
    assert "build/gate.md" in got["problems"][0]


# ---------------------------------------------------------------- status (R11)


def _status_line(root: Path, capsys, monkeypatch) -> str:
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    capsys.readouterr()
    sdlc.main()
    lines = capsys.readouterr().out.splitlines()
    return next(line for line in lines if line.strip().startswith("008  T1"))


def test_status_marks_a_current_gate_only(repo, capsys, monkeypatch) -> None:
    """R11: green or red while the record judged the build as it stands; nothing when stale."""
    assert "gate" not in _status_line(repo, capsys, monkeypatch)
    _base_check(repo, 'test -z "$FAKE_GATE_FAIL"')
    _gate(repo, capsys)
    assert "  · gate green" in _status_line(repo, capsys, monkeypatch)
    _write(repo / "src" / "app.py", "x = 4\n")
    assert "gate" not in _status_line(repo, capsys, monkeypatch), "stale: says nothing"
    monkeypatch.setenv("FAKE_GATE_FAIL", "1")
    _gate(repo, capsys)
    assert "  · gate red" in _status_line(repo, capsys, monkeypatch)


# ---------------------------------------------------------------- close's measure (R12)


def test_a_hand_gate_is_no_factory_file(repo, capsys) -> None:
    """R12: no `decision.md`, and `build/gate.md` isn't a round's gate file: close counts
    nothing of the factory's for a change built by hand, a red attempt included."""
    _base_check(repo, "exit 1")
    _gate(repo, capsys)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "built, gate red")
    assert _git(repo, "show", f"{NAME}:.sdlc/work/{NAME}/build/gate.md").startswith("GATE: FAIL")
    assert sdlc._factory_files(repo, NAME) is None
