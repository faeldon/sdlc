"""091: `sdlc.py gate`, the gate run by hand, and the record the board and status read.

The record is the factory's shape (`build/round-<N>.gate.md`), copied rather than imported: each
plugin is cached on its own. The copies are pinned to `factory.py` here.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
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
    return (_folder(root) / sdlc.factory_records.HAND_GATE).read_text(encoding="utf-8")


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
    assert not (_folder(repo) / sdlc.factory_records.HAND_GATE).exists()
    assert not (
        repo / ".sdlc" / "work" / "008-other-thing" / sdlc.factory_records.HAND_GATE
    ).exists()


def _masked(text: str) -> list[str]:
    return [
        "Build: *" if sdlc.factory_records.BUILD_RE.match(line)
        else "Seconds: *" if sdlc.factory_records.SECONDS_RE.match(line)
        else "Waited: *" if sdlc.factory_records.WAITED_RE.match(line)
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
    assert "    at <path-to-clone> under <home>\n" in ours and str(repo) not in ours


@pytest.mark.portable
def test_the_copies_are_the_factorys() -> None:
    """R3: the record's regexes and figures are `factory.py`'s."""
    for name in ("ATTEMPT_VERDICT_RE", "BUILD_RE", "SECONDS_RE"):
        assert getattr(sdlc.factory_records, name).pattern == getattr(factory, name).pattern, name
    for name in ("GATE_TAIL", "GATE_TIMEOUT"):
        assert getattr(sdlc, name) == getattr(factory, name), name
    for name in ("CLONE_MARK", "HOME_MARK", "TMP_MARK", "USER_MARK"):
        assert getattr(sdlc.factory_records, name) == getattr(factory, name), name


def test_the_placeholders_are_the_factorys(repo, monkeypatch) -> None:
    """R5: the main checkout, then the change's checkout, then home, then the temp directory and
    the login name inside a marked path, from inside a worktree; then the scan's shapes, and the
    terms in the main checkout's `.sdlc/terms.local` (nit 2026-11-18-72)."""
    monkeypatch.setenv("HOME", str(repo.parent))
    temp = repo.parent / "T"
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        monkeypatch.setenv(name, "drafter")
    tree = repo / ".claude" / "worktrees" / "009-elsewhere"
    _git(repo, "worktree", "add", "-q", "-b", "009-elsewhere", str(tree), "main")
    outside = repo.parent / "cache" / "venv"
    text = (
        f"{repo}/x and {tree}/y and {outside} and {tree.resolve().as_posix()}/z\n"
        f"{repo.resolve()}/w\n"
        f"{temp}/pytest-of-drafter/x, as drafter said, not /var{temp}/q or {temp}foo\n"
        "a fixture's work/"
        "046*, /Users/"
        "someone/x, /home/"
        "someone/x and ~/"
        "code/x\n"
        "built for Stale Widgets\n"
    )
    (repo / ".sdlc").mkdir(exist_ok=True)
    (repo / ".sdlc" / "terms.local").write_text("# kept out\n\\bstale widgets\\b\n")
    ours = sdlc.factory_records.placeholders(text, tree, sdlc._hand_main(tree))
    assert ours == factory._placeholders(text, tree)
    assert str(repo) not in ours and f"{sdlc.factory_records.HOME_MARK}/cache/venv" in ours
    assert "pytest-of-drafter" not in ours and "as drafter said" in ours
    assert "work/<046>*, /Users/<name>/x, /home/<name>/x and ~/<dir>/x" in ours
    assert "built for <term>\n" in ours and sdlc.factory_records.TERM_MARK == factory.TERM_MARK
    assert sdlc.factory_records.TERMS_FILE == factory.TERMS_FILE
    shapes = [shape for shape, _ in sdlc.factory_records.DEFUSE]
    assert shapes == [shape for shape, _ in factory.DEFUSE]


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
    raw = (_folder(repo) / sdlc.factory_records.HAND_GATE).read_bytes()
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
    """R7: None without a record; the last attempt's verdict, command and summary (187), current
    while the build is the one it judged and the checkout is on the change's branch."""
    folder = _folder(repo)
    assert sdlc.hand_gate(folder, repo, "main") is None
    _base_check(repo, 'test -z "$FAKE_GATE_FAIL"')
    monkeypatch.setenv("FAKE_GATE_FAIL", "1")
    _gate(repo, capsys)
    monkeypatch.delenv("FAKE_GATE_FAIL")
    _gate(repo, capsys)
    got = sdlc.hand_gate(folder, repo, "main")
    keys = ("verdict", "current", "exit", "attempts", "fails", "command", "summary")
    assert {k: got[k] for k in keys} == {
        "verdict": "PASS", "current": True, "exit": "0", "attempts": 2, "fails": 1,
        "command": 'test -z "$FAKE_GATE_FAIL"', "summary": None,
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
    _write(_folder(repo) / sdlc.factory_records.HAND_GATE, text)
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
    assert sdlc.closing._factory_files(repo, NAME) is None


# ---------------------------------------------------------------- the shared gate slots (113)
#
# A hand gate takes one of the factory's `gate_jobs` slots when `sdlc-factory` is enabled. Each
# test below holds a slot with one script's code and gates with the other's, so the lock files'
# names and the byte they lock are pinned by behaviour as well as by the copies.

SLOT_FILES = "sdlc-factory-gate-*.lock"
# A child that holds slot 0 through `factory.gate_slot()`, says so, holds it `argv[3]` seconds,
# stamps when it lets go into `argv[4]`, and exits.
HOLD_FACTORY = """\
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("factory_child", sys.argv[1])
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)
with factory.gate_slot(Path(sys.argv[2]), 1, "009-other") as (slot, waited):
    print(f"held {slot}", flush=True)
    time.sleep(float(sys.argv[3]))
    Path(sys.argv[4]).write_text(repr(time.time()), encoding="utf-8")
"""
# The same through `sdlc._hand_slot()`, holding slot 0 for 60 seconds.
HOLD_HAND = """\
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("sdlc_child", sys.argv[1])
sdlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdlc)
with sdlc._hand_slot(Path(sys.argv[2]), 1, "008-reopen-drafts", 60) as (slot, waited):
    print(f"held {slot}", flush=True)
    time.sleep(60)
"""
FACTORY_PY = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
SDLC_PY = ROOT / "scripts" / "sdlc.py"


@pytest.fixture(autouse=True)
def _no_factory(monkeypatch) -> None:
    """The developer's own settings never decide a result: the factory is off unless a test
    turns it on."""
    monkeypatch.setattr(sdlc, "factory_enabled", lambda home: (False, None))


def _factory_on(monkeypatch) -> None:
    monkeypatch.setattr(sdlc, "factory_enabled", lambda home: (True, "user"))


def _on_main(root: Path, factory_toml: str | None) -> None:
    """Commit `factory_toml` as the base branch's `.sdlc/factory.toml` (None: remove it)."""
    _git(root, "checkout", "-q", "main")
    path = root / ".sdlc" / "factory.toml"
    if factory_toml is None:
        _git(root, "rm", "-q", "--ignore-unmatch", ".sdlc/factory.toml")
    else:
        _write(path, factory_toml)
        _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "--allow-empty", "-m", "factory")
    _git(root, "checkout", "-q", NAME)


def _common(root: Path) -> Path:
    return Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))


def _hold(script: str, *args: str) -> subprocess.Popen:
    child = subprocess.Popen(
        [sys.executable, "-c", script, *args], stdout=subprocess.PIPE, encoding="utf-8"
    )
    assert child.stdout.readline().strip() == "held 0"
    return child


def _stamp_check(root: Path, log: Path) -> None:
    """A check that writes when it started, as a float, to `log`."""
    py = Path(sys.executable).as_posix()
    stamp = f"import time, pathlib; pathlib.Path(r'{log.as_posix()}').write_text(repr(time.time()))"
    _base_check(root, f'"{py}" -c "{stamp}"')


@pytest.mark.parametrize("jobs", [1, 2])
def test_a_hand_gate_waits_for_a_factory_gates_slot(repo, capsys, monkeypatch, tmp_path, jobs):
    """R1, R3, R6: with one slot, held by a factory gate, the hand gate says it waits, runs only
    once the slot frees, and times the check alone; with two, it runs at once on the other."""
    _factory_on(monkeypatch)
    _on_main(repo, f"gate_jobs = {jobs}\n")
    started, released = tmp_path / "started", tmp_path / "released"
    _stamp_check(repo, started)
    capsys.readouterr()
    child = _hold(HOLD_FACTORY, str(FACTORY_PY), str(repo), "2.0", str(released))
    try:
        code = sdlc.cmd_gate(repo, "008")
        got = capsys.readouterr()
    finally:
        child.wait(timeout=30)
    out = json.loads(got.out)
    assert code == 0 and out["verdict"] == "PASS", got
    start, end = float(started.read_text()), float(released.read_text())
    waiting = f"{NAME}: waiting for a gate slot (1 of 1 in use), up to 30 minutes"
    if jobs == 1:
        assert start >= end, "the two gates overlapped"
        assert got.err.count(waiting) == 1, got.err
        assert out["waited"] >= 0.5 and out["seconds"] < out["waited"] and out["slot"] == 0, out
    else:
        assert start < end, "a free slot was left idle"
        assert "waiting" not in got.err and out["waited"] == 0.0 and out["slot"] == 1, out
    assert _masked(_record(repo))[2:4] == ["## Attempt 1", ""], "the record's shape is the same"


@pytest.mark.portable
def test_the_slot_copies_are_the_factorys() -> None:
    """R8: the lock files' name, the poll, where `gate_jobs` lives and its default."""
    assert sdlc.SLOT_NAME == factory.SLOT_NAME
    assert sdlc.SLOT_POLL == factory.SLOT_POLL
    assert sdlc.FACTORY_CONFIG == factory.CONFIG_FILE
    assert factory.DEFAULTS["gate_jobs"] == sdlc.GATE_JOBS_DEFAULT
    assert sdlc.SLOT_WAIT == sdlc.GATE_TIMEOUT


UI_TABLES = [
    None,
    "",
    "ui = 3\n",
    "[ui]\n",
    '[ui]\nserve = "s {port}"\nshoot = "t {url} {out}"\npaths = ["web/"]\n',
    '[ui]\nserve = "s"\nshoot = "  "\npaths = ["web/"]\n',
    '[ui]\nserve = "s"\nshoot = "t"\npaths = []\npages = ["/", "/a b/"]\n',
    '[ui]\nserve = "s"\nshoot = "t"\npaths = ["web/", 3]\nwidths = [[390, 844]]\n',
    '[ui]\nserve = "s"\nshoot = "t"\npaths = ["web/"]\nwidths = [[0, 1]]\npages = "/"\n',
    '[ui]\nserve = "s"\nshoot = "t"\npaths = ["web/"]\nwidths = [[1, true]]\nurl = "u"\n',
    "[ui\n",
]


@pytest.mark.portable
@pytest.mark.parametrize("text", UI_TABLES)
def test_the_ui_copies_are_the_factorys(repo, text) -> None:
    """143 R5: what ship's UI review reads of `[ui]` (complete, pages, widths, paths) is what
    the factory makes of the same base-branch table, and the page names its PNGs are under."""
    _on_main(repo, text)
    _write(repo / ".sdlc" / "factory.toml", '[ui]\nserve = "x"\nshoot = "y"\npaths = ["z/"]\n')
    ours = sdlc._ui_at(repo, "main")
    theirs = factory._ui(repo)[0]
    assert ours["complete"] == factory.ui_complete(theirs), text
    for key in ("pages", "widths", "paths", "serve", "shoot"):
        assert ours[key] == theirs[key], (text, key)
    assert set(sdlc.UI_DEFAULTS) <= set(factory.DEFAULTS["ui"])
    for page in ["/", "/drafts", "/a b/c", "", "?x=1", "../up"]:
        assert sdlc._ui_page_name(page) == factory._page_name(page), page


def test_the_hand_gate_reads_gate_jobs_as_the_factory_does(repo) -> None:
    """R3: from the base branch, never the checkout, a value the factory refuses giving 1."""
    seen = []
    for text in [None, "gate_jobs = 3\n", "gate_jobs = 0\n", "gate_jobs = -1\n",
                 'gate_jobs = "2"\n', "gate_jobs = true\n", "gate_jobs = 2.5\n",
                 'mode = "auto"\n', "gate_jobs = [\n"]:  # fmt: skip
        (repo / ".sdlc" / "factory.toml").unlink(missing_ok=True)
        _on_main(repo, text)
        _write(repo / ".sdlc" / "factory.toml", "gate_jobs = 8\n")
        ours = sdlc._gate_jobs_at(repo, "main")
        assert ours == factory._gate_jobs(repo)[0], text
        seen.append(ours)
    assert seen == [1, 3, 1, 1, 1, 1, 1, 1, 1]


def test_a_hand_gate_gives_up_after_its_wait_and_records_nothing(
    repo, capsys, monkeypatch, tmp_path
) -> None:
    """R4: no slot within `SLOT_WAIT`: a refusal naming the limit, exit 1, the record as it was."""
    _factory_on(monkeypatch)
    _gate(repo, capsys)
    before = (_folder(repo) / sdlc.factory_records.HAND_GATE).read_bytes()
    monkeypatch.setattr(sdlc, "SLOT_WAIT", 0.5)
    child = _hold(HOLD_FACTORY, str(FACTORY_PY), str(repo), "60", str(tmp_path / "released"))
    try:
        code = sdlc.cmd_gate(repo, "008")
        got = capsys.readouterr()
    finally:
        child.kill()
        child.wait()
    assert code == 1
    assert json.loads(got.out)["refusals"] == [
        "no gate slot came free in 0.5 seconds (1 of 1 in use): nothing was judged, run it again"
    ]
    assert "up to 0.5 seconds" in got.err
    assert (_folder(repo) / sdlc.factory_records.HAND_GATE).read_bytes() == before
    assert sdlc._wait_text(sdlc.GATE_TIMEOUT) == "30 minutes"


def test_without_the_factory_the_hand_gate_takes_no_slot(repo, capsys, tmp_path) -> None:
    """R5: no wait, no waiting line, no lock file, even while slot 0 is held."""
    _on_main(repo, "gate_jobs = 2\n")
    child = _hold(HOLD_FACTORY, str(FACTORY_PY), str(repo), "60", str(tmp_path / "released"))
    try:
        files = sorted(_common(repo).glob(SLOT_FILES))
        code = sdlc.cmd_gate(repo, "008")
        got = capsys.readouterr()
        assert sorted(_common(repo).glob(SLOT_FILES)) == files
    finally:
        child.kill()
        child.wait()
    out = json.loads(got.out)
    assert code == 0 and "waiting" not in got.err
    assert (out["waited"], out["slot"]) == (0.0, None)


@pytest.mark.portable
def test_a_killed_hand_gate_frees_its_slot(repo) -> None:
    """R7: the slot is a lock on an open descriptor, freed however its gate ends."""
    import time

    child = _hold(HOLD_HAND, str(SDLC_PY), str(repo))
    lock = _common(repo) / "sdlc-factory-gate-0.lock"
    try:
        fd = os.open(lock, os.O_RDWR)
        try:
            assert not factory._try_lock(fd), "held while its gate runs"
        finally:
            os.close(fd)
    finally:
        child.kill()
        child.wait()
    start = time.monotonic()
    with factory.gate_slot(repo, 1, NAME) as (slot, _):
        assert slot == 0
    assert time.monotonic() - start < 2, "the slot outlived its gate"
    assert lock.is_file()


def test_new_claims_a_number_while_a_hand_gate_waits(repo, tmp_path) -> None:
    """R9: a waiting hand gate holds neither `_main_lock` nor `sdlc.lock`."""
    import threading

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "built")
    home = tmp_path / "home"
    _write(home / ".claude" / "settings.json", '{"enabledPlugins": {"sdlc-factory@x": true}}\n')
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | {"HOME": str(home)}
    child = _hold(HOLD_FACTORY, str(FACTORY_PY), str(repo), "60", str(tmp_path / "released"))
    gate = subprocess.Popen(
        [sys.executable, str(SDLC_PY), "gate", "008"], cwd=repo, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        line = gate.stderr.readline()
        assert "waiting for a gate slot" in line, line
        took = threading.Event()

        def claim() -> None:
            with sdlc.closing._main_lock(repo):
                took.set()

        threading.Thread(target=claim, daemon=True).start()
        assert took.wait(2), "a waiting hand gate blocked `new`"
    finally:
        child.kill()
        child.wait()
        out, err = gate.communicate(timeout=30)
    assert gate.returncode == 0 and json.loads(out)["slot"] == 0, (out, err)


# ---------------------------------------------------------------- a factory run at test (145 R7)


def _factory_at(root: Path, stage: str) -> None:
    folder = _folder(root)
    _write(folder / "runs" / "builder.sessions", "s-1\n")
    intent = folder / "intent.md"
    intent.write_text(INTENT.replace("stage: build", f"stage: {stage}"), encoding="utf-8")


def test_the_hand_gate_gates_a_factory_run_at_test_alone(repo, capsys) -> None:
    """145 R7: at `test` a factory run is gated by hand into `build/gate.md`; at `build` or
    `design` it is refused, naming `factory.py gate`."""
    for stage in ("build", "design"):
        _factory_at(repo, stage)
        code = sdlc.cmd_gate(repo, "008")
        out = json.loads(capsys.readouterr().out)
        assert code == 1 and "factory.py gate" in out["refusals"][0], out
        assert not (_folder(repo) / sdlc.factory_records.HAND_GATE).exists()
    _factory_at(repo, "test")
    code, out = _gate(repo, capsys)
    assert code == 0 and out["verdict"] == "PASS", out
    assert _record(repo).startswith("GATE: PASS\n")


def test_a_hand_gate_on_a_factory_run_is_counted_in_no_factory_figure(repo, capsys) -> None:
    """145 R7: `gate_fail` counts the factory's round gates alone, never `build/gate.md`."""
    _base_check(repo, "exit 1")
    _factory_at(repo, "test")
    _gate(repo, capsys)
    folder = _folder(repo)
    _write(folder / "decision.md", "DECISION: ESCALATE\n\n- ESCALATED: gate: red\n")
    attempts = "## Attempt 1\n\nVerdict: FAIL\n\n## Attempt 2\n\nVerdict: PASS\n"
    _write(folder / "build" / "round-1.gate.md", f"GATE: PASS\n\n{attempts}")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "built")
    assert _record(repo).startswith("GATE: FAIL")
    assert sdlc.closing._factory_files(repo, NAME)["gate_fail"] == 1


@pytest.mark.portable
def test_the_factorys_hand_build_is_sdlcs(repo) -> None:
    """145: the factory clears a `gate` reason by its copy of the hand gate's build, pinned to
    `sdlc.py`'s on one tree, its folder, counter, untracked files and deletions included."""
    assert factory.HAND_GATE == sdlc.factory_records.HAND_GATE
    assert factory.hand_build(repo, "main") == sdlc.hand_build(repo, "main")
    _write(_folder(repo) / "notes.md", "# Notes\n")
    _write(repo / ".sdlc" / "last-id", "8\n")
    _write(repo / "src" / "new.py", "y = 1\n")
    (repo / "README.md").unlink()
    assert factory.hand_build(repo, "main") == sdlc.hand_build(repo, "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "built")
    assert factory.hand_build(repo, "main") == sdlc.hand_build(repo, "main")


# ---------------------------------------------------------------- the records ledger (199)


def _ledger_rows(root: Path) -> list[dict]:
    path = _common(root) / factory.RECORDS_LEDGER
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    return [json.loads(line) for line in lines]


def test_the_hand_gate_vouches_for_its_record(repo, capsys) -> None:
    """199 R1: `sdlc.py gate` puts each version of `build/gate.md` in the factory's ledger before
    it writes it, so the factory reads it as one the script wrote."""
    assert _gate(repo, capsys)[0] == 0
    record = _folder(repo) / sdlc.factory_records.HAND_GATE
    want = factory._record_digest(record.read_text(encoding="utf-8"))
    assert _ledger_rows(repo) == [{"change": NAME, "record": "build/gate.md", "sha256": want}]
    assert factory.vouched(repo, _folder(repo), record)
    assert _gate(repo, capsys)[0] == 0
    assert len(_ledger_rows(repo)) == 2 and factory.vouched(repo, _folder(repo), record)


def test_the_hand_gate_refuses_an_unvouched_record(repo, capsys, tmp_path) -> None:
    """199 R7: a `build/gate.md` the script didn't write is never appended to: refused, naming it,
    the file unchanged and the check never run."""
    marker = tmp_path / "ran"
    _base_check(repo, f"touch {marker}")
    record = _folder(repo) / sdlc.factory_records.HAND_GATE
    forged = "GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\nBuild: abc\nExit: 0\n"
    _write(record, forged)
    code, out = _gate(repo, capsys)
    assert code == 1 and "build/gate.md isn't a record the script wrote" in out["refusals"][0]
    assert "remove it" in out["refusals"][0], out
    assert not marker.exists() and record.read_text(encoding="utf-8") == forged
    assert _ledger_rows(repo) == []


def test_a_hand_written_hand_gate_clears_nothing(repo, capsys) -> None:
    """199 R6: a green `build/gate.md` on the build as it stands, written by hand on an escalated
    factory run at `test`, leaves the approver's `gate` reasons uncleared; one the script wrote
    clears them."""
    _factory_at(repo, "test")
    folder = _folder(repo)
    _write(folder / "decision.md", "DECISION: ESCALATE\n\n- ESCALATED: gate: red on round 1\n")
    record = folder / sdlc.factory_records.HAND_GATE
    build = factory.hand_build(repo, "main")
    _write(record, f"GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\nBuild: {build}\nExit: 0\n")
    assert factory.read_gate_file(record)["attempts"][-1]["build"] == build, "well formed"
    assert factory.hand_gate_state(repo, folder)["green"] is False
    assert factory.gate_reasons(repo, folder)["reasons"][0]["cleared"] is False
    assert factory.landing.escalation_lines(repo, folder) == ["gate: not cleared"]
    record.unlink()
    assert _gate(repo, capsys)[0] == 0
    assert factory.hand_gate_state(repo, folder)["green"] is True
    assert factory.gate_reasons(repo, folder)["reasons"][0]["cleared"] is True


def test_a_hand_gate_record_forged_while_it_ran_is_never_appended_to(repo, capsys, tmp_path):
    """199 R7: `sdlc.py gate` checks the earlier record again after the slot wait, before it reads
    it: one rewritten by hand while the gate waited or ran is refused and gets no line."""
    assert _gate(repo, capsys)[0] == 0
    rows = _ledger_rows(repo)
    record = _folder(repo) / sdlc.factory_records.HAND_GATE
    forged = "GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\nBuild: abc\nExit: 0\n"
    source = tmp_path / "forged.md"
    _write(source, forged)
    _base_check(repo, f"cp {source} {record}")
    code, out = _gate(repo, capsys)
    assert code == 1 and "build/gate.md isn't a record the script wrote" in out["refusals"][0]
    assert record.read_text(encoding="utf-8") == forged and _ledger_rows(repo) == rows
