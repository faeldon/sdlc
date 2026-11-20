"""139: the landing train. A batch is stacked, in `land-check`'s order, each change on the one
before; gated once at the tip; a red tip bisected and the change at fault ejected; conflicts
resolved once by one landing agent; the changes closed in order, each by `sdlc.py close`'s
fast-forward, so the base branch's first-parent line reads as a one-at-a-time landing. And close
holds `_main_lock()` from its merge to its `Close` commit.

Each test builds a bare scratch repo and makes its changes with `sdlc.py new`, as a host does.
Nothing here runs an agent: a review or a resolution is written as the agent would reply.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from train_driver import DRIVER_STEPS, asked, drive_train, fake_claude, verdict, verified
from uv_run import uv_script

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_for_train", ROOT / "scripts" / "sdlc.py")
factory = _load("factory_train", ROOT / "plugins" / "factory" / "scripts" / "factory.py")

INBOX = ".sdlc/work/inbox.md"
REGISTER = "# Inbox\n\n> The register.\n\n## [2026-10-01-1] [idea] Keep drafts\n\nThe first.\n"


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _run(capsys, fn, *args, **kwargs) -> tuple[int, dict]:
    capsys.readouterr()
    code = fn(*args, **kwargs)
    return code, json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------- close's lock (R12–R15)


def _plain_repo(tmp_path: Path) -> Path:
    """A repo with a register, its changes made by `sdlc.py new` in process: no `uv`."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / INBOX).write_text(REGISTER, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _shipped(root: Path, slug: str, counter: bool = True) -> tuple[Path, Path]:
    """A change opened in its worktree, built and shipped, its commit made by hand as
    `/sdlc:ship` makes it. Without `counter`, `.sdlc/last-id` is left out of its commit, so two
    such branches rebase onto each other with nothing to conflict on."""
    assert sdlc.cmd_new(root, slug, 1, None, worktree=True) == 0
    branch = next(b for _, b in sdlc.worktrees(root) if b.endswith(f"-{slug}"))
    tree = root / ".claude" / "worktrees" / branch
    folder = tree / ".sdlc" / "work" / branch
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("impact:\n", "impact: none\n", 1), "utf-8"
    )
    if not counter:
        (tree / ".sdlc" / "last-id").unlink()
    (tree / f"{branch}.txt").write_text("the change\n", encoding="utf-8")
    assert sdlc.cmd_ship(tree, branch.split("-")[0]) == 0
    _git(tree, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", f"ship {branch}")
    return tree, folder


@pytest.mark.portable
def test_the_lock_is_reentrant_in_a_thread_and_exclusive_across_threads(tmp_path) -> None:
    """R14: a thread holding `_main_lock()` takes it again without deadlock, since only its
    outermost hold takes the OS lock; another thread still waits for it."""
    root = _plain_repo(tmp_path)
    done = threading.Event()

    def other() -> None:
        with sdlc.closing._main_lock(root):
            done.set()

    with sdlc.closing._main_lock(root):
        with sdlc.closing._main_lock(root):
            worker = threading.Thread(target=other)
            worker.start()
            assert not done.wait(0.5), "another thread got the lock while this one held it twice"
        assert not done.wait(0.3), "the inner exit let go of the lock"
    worker.join(10)
    assert done.is_set(), "the outer exit let go"


@pytest.mark.portable
def test_close_holds_the_lock_from_its_merge_to_its_close(tmp_path, capsys, monkeypatch) -> None:
    """R13: with close paused after its merge, a session filing an idea under the lock waits, so
    no `File` commit can land between the change's commit and its `Close`."""
    root = _plain_repo(tmp_path)
    tree, folder = _shipped(root, "reopen")
    paused, go = threading.Event(), threading.Event()
    real = sdlc.closing.measure_change

    def pausing(main, branch, cfg):
        paused.set()  # just after the merge, before the Close commit
        assert go.wait(10)
        return real(main, branch, cfg)

    monkeypatch.setattr(sdlc.closing, "measure_change", pausing)
    results: dict = {}

    def closing() -> None:
        results["close"] = sdlc.closing.cmd_close(root, "001")

    filed = threading.Event()

    def filing() -> None:
        with sdlc.closing._main_lock(root):
            (root / INBOX).write_text(
                REGISTER + "\n## [2026-10-03-1] [idea] Late\n\nFiled meanwhile.\n", "utf-8"
            )
            results["file"] = sdlc.cmd_inbox_commit(root)
        filed.set()

    closer = threading.Thread(target=closing)
    closer.start()
    assert paused.wait(10), "close never reached its measure step"
    assert _git(root, "log", "-1", "--format=%s", "main") == f"ship {folder.name}", "merged"
    filer = threading.Thread(target=filing)
    filer.start()
    assert not filed.wait(0.5), "the idea was filed while close held the lock"
    go.set()
    closer.join(30)
    filer.join(30)
    assert results == {"close": 0, "file": 0}, capsys.readouterr().out
    subjects = _git(root, "log", "--first-parent", "--format=%s", "main").splitlines()
    assert subjects == ["File 2026-10-03-1", f"Close {folder.name}", f"ship {folder.name}", "init"]


def test_close_refuses_a_branch_carrying_another_change(tmp_path, capsys) -> None:
    """R12: a branch whose commits touch another change's folder, as a crashed train leaves one,
    is refused before anything is written: its fast-forward would land the other change with no
    `Close`."""
    root = _plain_repo(tmp_path)
    a_tree, a = _shipped(root, "first", counter=False)
    b_tree, b = _shipped(root, "second", counter=False)
    _git(b_tree, "-c", "user.name=t", "-c", "user.email=t@t", "rebase", "-q", a.name)
    assert _git(b_tree, "rev-parse", "HEAD^") == _git(a_tree, "rev-parse", "HEAD"), "stacked"
    before = _git(root, "rev-parse", "main")
    code, out = _run(capsys, sdlc.closing.cmd_close, root, "002")
    assert code == 1, out
    assert any(a.name in r and "another change" in r for r in out["refusals"]), out["refusals"]
    assert out["done"] == [] and _git(root, "rev-parse", "main") == before
    assert b_tree.exists() and a_tree.exists()


def _close_env() -> dict[str, str]:
    """The environment a close is run in from a test: without this session's virtualenv, so `uv`
    builds the script's own, and without the flags a handed-off close reads."""
    dropped = (
        "VIRTUAL_ENV",
        sdlc.closing.HANDOFF_ENV,
        sdlc.OWN_SCRIPT_ENV,
        sdlc.closing.LOCK_HELD_ENV,
    )
    return {k: v for k, v in os.environ.items() if k not in dropped}


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")
def test_a_close_that_hands_off_runs_under_the_parents_hold(tmp_path) -> None:
    """R14: in the plugin's own repo a change editing `scripts/` is closed by main's script, which
    holds `_main_lock()` from its merge and hands the rest to the merged code; the child is told
    the parent holds the lock and takes none, so the close finishes. Were the variable not passed,
    the child would wait on the parent's lock for good, and this test's timeout would fail it."""
    root = tmp_path / "plugin"
    for name in (".claude-plugin", "scripts", "templates", "defaults", "guide"):
        shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
    (root / ".gitignore").write_text(".claude/worktrees/\n__pycache__/\n", encoding="utf-8")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text('[archive]\ntarget = "none"\n', encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the plugin")
    script = root / "scripts" / "sdlc.py"

    def by(cwd: Path, *args: str) -> subprocess.CompletedProcess:
        # Idea 2026-11-19-75: a copy at a new path resolves its dependencies, so with no network
        # it runs from uv's cache, or the test skips naming the network, as the adoption tests do.
        return uv_script(script, cwd, args, _close_env(), timeout=600)

    made = by(root, "new", "lock-probe", "--worktree")
    assert made.returncode == 0, made.stderr
    tree = next((root / ".claude" / "worktrees").glob("*-lock-probe"))
    intent = tree / ".sdlc" / "work" / tree.name / "intent.md"
    intent.write_text(intent.read_text("utf-8").replace("impact:\n", "impact: none\n", 1), "utf-8")
    with (tree / "scripts" / "sdlc.py").open("a", encoding="utf-8") as f:
        f.write("\n# a change to the script, so close hands itself to the merged code\n")
    shipped = by(tree, "ship", "001")
    assert shipped.returncode == 0, shipped.stderr
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", f"ship {tree.name}")
    start = time.monotonic()
    closed = by(root, "close", "001")
    assert closed.returncode == 0, closed.stdout + closed.stderr
    out = json.loads(closed.stdout)
    assert out["ran"] == "merged code" and "remove folder" in out["done"], out
    assert time.monotonic() - start < 600
    subjects = _git(root, "log", "--first-parent", "--format=%s", "main").splitlines()
    assert subjects[:2] == [f"Close {tree.name}", f"ship {tree.name}"], subjects
    assert not tree.exists()


@pytest.mark.portable
def test_the_handoff_passes_the_hold_and_the_child_takes_no_lock(tmp_path, monkeypatch) -> None:
    """R14: `_handoff()` names the lock file in `LOCK_HELD_ENV` only while this process holds the
    lock; a close told so pops the variable before any other process starts, and runs to its end
    while another thread holds the OS lock, since it takes none of its own."""
    root = _plain_repo(tmp_path)
    lock = str(sdlc.closing._lock_path(root))
    seen: list[dict | None] = []
    real = subprocess.run

    def fake_run(argv, **kwargs):
        if argv[0] == "git":
            return real(argv, **kwargs)  # the lock path's own read
        seen.append(kwargs.get("env"))
        return subprocess.CompletedProcess(
            argv, 0, stdout='{"done": [], "refusals": []}', stderr=""
        )

    monkeypatch.setattr(sdlc.subprocess, "run", fake_run)
    report = {"change": "001", "refusals": [], "done": []}
    sdlc.closing._handoff(root, ["001"], "merged", dict(report))
    assert sdlc.closing.LOCK_HELD_ENV not in seen[-1], "not held: nothing to pass"
    with sdlc.closing._main_lock(root):
        sdlc.closing._handoff(root, ["001"], "merged", dict(report))
    assert (
        seen[-1][sdlc.closing.LOCK_HELD_ENV] == lock
        and seen[-1][sdlc.closing.HANDOFF_ENV] == "merged"
    )
    monkeypatch.undo()

    # The child's side: told the parent holds it, it runs while that hold stands.
    _, folder = _shipped(root, "reopen")
    carried: list[bool] = []

    def watching(argv, **kwargs):
        env = kwargs.get("env") or os.environ
        carried.append(sdlc.closing.LOCK_HELD_ENV in env)
        return real(argv, **kwargs)

    monkeypatch.setattr(sdlc.subprocess, "run", watching)
    held, done = threading.Event(), threading.Event()
    result: dict = {}

    def holding() -> None:
        with sdlc.closing._main_lock(root):
            held.set()
            assert done.wait(60), "the close never finished under the parent's hold"

    def closing() -> None:
        result["code"] = sdlc.closing.cmd_close(root, "001")
        done.set()

    holder = threading.Thread(target=holding)
    holder.start()
    assert held.wait(10)
    monkeypatch.setenv(sdlc.closing.LOCK_HELD_ENV, lock)  # as the parent sets it for its child
    closer = threading.Thread(target=closing)
    closer.start()
    closer.join(60)
    assert done.is_set(), "the close deadlocked on the lock its parent holds"
    holder.join(10)
    assert result["code"] == 0
    assert sdlc.closing.LOCK_HELD_ENV not in os.environ, "popped at the close's entry"
    assert carried and not any(carried), "no subprocess of the close saw the variable"
    assert _git(root, "log", "-1", "--format=%s", "main") == f"Close {folder.name}"


# ---------------------------------------------------------------- the train's repo


needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _repo(tmp_path: Path, check: str | None = None) -> Path:
    """A scratch host on `main`; with `check`, its base branch names that `[commands] check`."""
    root = tmp_path / "host"
    root.mkdir()
    (root / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / INBOX).write_text(REGISTER, encoding="utf-8")
    if check is not None:
        (root / ".sdlc" / "config.toml").write_text(
            f"[commands]\ncheck = {json.dumps(check)}\n", encoding="utf-8"
        )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _ready(
    root: Path, slug: str, edit: dict[str, str], tier: int = 1, gone: tuple[str, ...] = ()
) -> Path:
    """A change made by `sdlc.py new`, built (each path in `edit` written, each in `gone`
    deleted), at `stage: test` with the approver's READY and a minor impact, one build round every
    reviewer passed, as a factory run leaves one. Returns its worktree."""
    code, _, said = factory._sdlc(["new", slug, "--tier", str(tier), "--worktree"], root)
    assert code == 0, said
    tree = next(p for p in (root / ".claude" / "worktrees").iterdir() if p.name.endswith(slug))
    folder = tree / ".sdlc" / "work" / tree.name
    intent = folder / "intent.md"
    text = intent.read_text(encoding="utf-8").replace("stage: plan", "stage: test")
    intent.write_text(text.replace("stage: design", "stage: test"), encoding="utf-8")
    if tier == 2:
        (folder / "spec.md").write_text(
            f"# {tree.name} — spec\n\n## Requirements\n\n1. R1. It does what {slug} says.\n",
            encoding="utf-8",
        )
        (folder / "plan.md").write_text("# plan\n\n## Files to change\n\n- README.md\n", "utf-8")
    (folder / "decision.md").write_text(
        "DECISION: READY\n\nIt does what it says.\n\n- IMPACT: minor — a test change\n",
        encoding="utf-8",
    )
    for path, content in edit.items():
        (tree / path).parent.mkdir(parents=True, exist_ok=True)
        (tree / path).write_text(content, encoding="utf-8")
    for path in gone:
        (tree / path).unlink()
    (folder / "build").mkdir()
    (folder / "build" / "round-1.md").write_text("Built.\n", encoding="utf-8")
    hashes = factory._tree_hashes(tree, "main")
    factory.snapshot_path(folder, 1).write_text(
        "".join(f"{digest}  {p}\n" for p, digest in hashes.items()), encoding="utf-8"
    )
    (folder / "reviews" / "round-1").mkdir(parents=True)
    for role in factory.DEFAULTS["reviewers"]:
        (folder / "reviews" / "round-1" / f"{role}.md").write_text(verdict(factory, role), "utf-8")
    return tree


def _folder(tree: Path) -> Path:
    return tree / ".sdlc" / "work" / tree.name


def _move(root: Path, n: int) -> None:
    """The base branch moves on, touching nothing a change does."""
    (root / f"elsewhere-{n}.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", f"elsewhere-{n}.txt")
    _git(root, "commit", "-q", "-m", f"main moves on, {n}")


# ---------------------------------------------------------------- land stops at its commit (R2)


@needs_uv
def test_land_commits_and_leaves_the_rebase_to_the_train(tmp_path, capsys) -> None:
    """R2: `land --by` ships and commits, then stops with `committed`: the branch's parent is
    still its old base though the base branch moved, and a rerun says the same."""
    root = _repo(tmp_path)
    tree = _ready(root, "lone", {"lone.txt": "lone\n"})
    base = _git(root, "rev-parse", "main")
    _move(root, 1)
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "committed", None), out
    assert "Sdlc-Landed: by=auto" in _git(tree, "log", "-1", "--format=%B")
    assert _git(tree, "rev-parse", "HEAD^") == base, "not rebased: the train stacks it"
    assert _git(tree, "status", "--porcelain") == ""
    assert not list((_folder(tree) / "reviews").glob("land-*")), "no landing round opened"
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.landing.cmd_land, tree, "001", "auto")
    assert (code, out["state"]) == (0, "committed"), out
    assert _git(tree, "rev-parse", "HEAD") == head, "a rerun commits nothing again"


# ---------------------------------------------------------------- the question (R16)


def _entry(name: str, **parts) -> dict:
    base = {"change": name, "checks": [], "cases": {}, "undone": [], "assumed": [], "recover": []}
    return {**base, **parts}


@pytest.mark.portable
def test_the_question_says_the_batch_is_stacked_and_gated_once() -> None:
    """R16: the one question says what a train does: stacked in this order, gated once at the
    tip, a red tip bisected and the change at fault left out, conflicts resolved by one landing
    agent and reviewed again, up to date as often as the base moves, closed in order."""
    plain = factory.landing.land_question([_entry("001-a"), _entry("002-b")], "main", 4)
    assert plain == (
        "Land 2 changes in this order, 001-a, 002-b, each shipped with its approver's impact, "
        "committed, stacked in this order on main, gated once at the tip (a red tip bisected, "
        "the change at fault left out with why and the rest landed; a conflict resolved by one "
        "landing agent and reviewed again), brought up to date as often as main moves while "
        "landing, up to 4 times, and closed in order, pushed as git.push says? "
        "(yes / yes, with a fix / leave one out / no)"
    )
    assert "its builder" not in plain, "one landing agent, never each change's own builder"
    one = factory.landing.land_question(
        [_entry("001-a", checks=[{"name": "x", "command": "true"}])], "t"
    )
    assert one.startswith("Land 1 change in this order, 001-a, each shipped with its approver's "
                          "impact, its acceptance checks run as shown, and again as stacked, "
                          "committed, stacked in this "
                          "order on t, gated once at the tip")  # fmt: skip


# ---------------------------------------------------------------- driving a train as the skill does


def _begin(root: Path, capsys, by: str = "auto", *idents: str) -> dict:
    """Begin a train over `idents`, or over every ready change."""
    names = list(idents) or [r["change"] for r in factory.ready(root)]
    code, out = _run(capsys, factory.landing.cmd_train, root, begin=names, by=by)
    assert code == 0 and out["state"] == "begun", out
    return out


def _keeping(name: str):
    """Stand-ins for a landing round in which change `name`'s behaviour check asks for a change
    and the arbiter keeps it; every other reply passes."""

    def review(folder: Path, n: int, role: str) -> None:
        asks = folder.name == name and role == "behaviour"
        text = verdict(factory, role, "CHANGES", ("bb.txt:1: say more",)) if asks else None
        text = text or verdict(factory, role)
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(text, encoding="utf-8")

    def arbitrate(folder: Path, found: dict) -> None:
        verified(factory, folder, found["round"], kept=asked(found))

    return review, arbitrate


def _three(tmp_path: Path, check: str | None = None) -> tuple[Path, list[Path]]:
    """A host with three ready changes, each editing a file of its own."""
    root = _repo(tmp_path, check)
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb", "cc")]
    return root, trees


def _first_parent(root: Path) -> list[str]:
    return _git(root, "log", "--first-parent", "--format=%s", "main").splitlines()


def _state_file(root: Path) -> Path:
    common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / factory.landing.TRAIN_STATE


# ---------------------------------------------------------- stacking and closing (R1, R9, R11, R19)


@needs_uv
def test_a_train_stacks_each_change_on_the_one_before(tmp_path, capsys) -> None:
    """R1: change 1 goes onto the base branch's tip and change k onto stacked commit k−1, each
    rebased in its own worktree; `<trunk>..<k>` holds exactly changes 1..k's commits."""
    root, trees = _three(tmp_path)
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "close")
    assert readings[-1].get("change") == trees[0].name, readings
    heads = [_git(t, "rev-parse", "HEAD") for t in trees]
    base = _git(root, "rev-parse", "main")
    assert _git(trees[0], "rev-parse", "HEAD^") == base
    for k in (1, 2):
        assert _git(trees[k], "rev-parse", "HEAD^") == heads[k - 1], f"{k + 1} on {k}"
        own = _git(trees[k], "rev-list", f"main..{trees[k].name}").splitlines()
        assert own == list(reversed(heads[: k + 1])), "exactly changes 1..k, one commit each"
        dirty = _git(trees[k], "status", "--porcelain").splitlines()
        assert all(f".sdlc/work/{trees[k].name}/" in d for d in dirty), (
            "only the folder's records are uncommitted, for the close to amend in; nothing stashed"
        )
    stacked = readings[-1]["changes"]
    assert [stacked[t.name]["stacked"] for t in trees] == heads
    assert all(stacked[t.name]["pre"] != stacked[t.name]["stacked"] for t in trees[1:])
    assert stacked[trees[0].name]["pre"] == heads[0], "the first change didn't move"
    assert "merge" not in " ".join(_git(root, "reflog", "--format=%gs").splitlines()[:5])


@needs_uv
def test_a_train_of_three_lands_as_three_closes(tmp_path, capsys) -> None:
    """R9: the base branch's first-parent line reads A, Close A, B, Close B, C, Close C, and
    `closed_changes()` reads three records in that order, each `sha` its `Close`'s parent, each
    intent shipped with its metrics from its `Close` commit."""
    root, trees = _three(tmp_path)
    names = [t.name for t in trees]
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys)
    assert readings[-1]["next"] == "done", readings[-1]
    subjects = _first_parent(root)
    closes = [s for s in subjects if s.startswith("Close ")]
    assert closes == [f"Close {n}" for n in reversed(names)], subjects
    for name in reversed(names):
        at = subjects.index(f"Close {name}")
        parent = _git(root, "rev-parse", f"main~{at + 1}")
        shown = _git(root, "show", f"{parent}:.sdlc/work/{name}/intent.md")
        assert "stage: shipped" in shown, name
        assert "Sdlc-Landed: by=auto" in _git(root, "log", "-1", "--format=%B", parent)
    records = sdlc.closed_changes(root, None, "main")
    assert [r["name"] for r in records] == names
    for r in records:
        assert r["sha"] == _git(root, "rev-parse", "--short", f"{r['close_sha']}^"), r
        assert r["metrics"] and "coverage" in r["metrics"], r["metrics"]
    assert not any(t.exists() for t in trees), "every worktree removed by close"
    assert not _state_file(root).exists(), "the train is over"
    assert _run(capsys, factory.landing.cmd_train, root)[1]["under_way"] is False


@needs_uv
def test_a_rerun_resumes_the_train_and_a_second_refuses(tmp_path, capsys) -> None:
    """R19: the train's state lives in the git common dir, never in a tree; a second `--begin`
    refuses while one is under way, and a later reading carries on where it was."""
    root, trees = _three(tmp_path)
    begun = _begin(root, capsys)
    assert begun["order"] == [t.name for t in trees]
    assert _state_file(root).is_file() and ".git" in _state_file(root).parts, "the common dir"
    assert _git(root, "status", "--porcelain") == "", "the main checkout is untouched"
    drive_train(factory, root, capsys, until=lambda o: o["next"] == "stack")
    code, again = _run(capsys, factory.landing.cmd_train, root, begin=["1", "2"], by="person")
    assert code == 1 and "under way" in again["refusals"][0], again
    # A new session: the reading resumes from the state alone.
    readings = drive_train(factory, root, capsys)
    assert readings[-1]["next"] == "done" and readings[-1]["landed"] == [t.name for t in trees]
    assert len([s for s in _first_parent(root) if s.startswith("Close ")]) == 3


@needs_uv
def test_a_stopped_train_puts_every_unlanded_change_back(tmp_path, capsys) -> None:
    """R11: on a stop, every change not landed goes back to its pre-train commit: its parent is
    its old base again, its tree outside its own folder is its pre-train commit's, a `stop`
    record is in its commit, and no branch holds another change's commit."""
    root, trees = _three(tmp_path)
    base = _git(root, "rev-parse", "main")
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o["next"] == "close")
    pre = {n: c["pre"] for n, c in readings[-1]["changes"].items()}
    code, out = _run(capsys, factory.landing.cmd_train, root, stop=True)
    assert code == 0 and out["state"] == "stopped", out
    assert [p["change"] for p in out["put_back"]] == [t.name for t in trees]
    undone = {p["change"]: p["undo"] for p in out["put_back"]}
    assert undone[trees[0].name] is None, "the first change never moved: nothing to undo"
    assert not _state_file(root).exists()
    for tree in trees:
        head = _git(tree, "rev-parse", "HEAD")
        assert _git(tree, "rev-parse", "HEAD^") == base, tree.name
        assert _git(tree, "status", "--porcelain") == "", tree.name
        assert subprocess.run(
            ["git", "-C", str(tree), "diff", "--quiet", pre[tree.name], head, "--", ".",
             ":(exclude).sdlc/work"], capture_output=True,
        ).returncode == 0, f"{tree.name}: outside its folder, its pre-train tree"  # fmt: skip
        assert _git(tree, "rev-list", "--count", f"main..{tree.name}") == "1"
        if tree is not trees[0]:
            step = factory.read_land_step(
                _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/{factory.LAND_STEP.as_posix()}")
            )
            assert step["step"] == "stop" and step["problems"], step
    for tree in trees[1:]:
        assert undone[tree.name].startswith("git reset --keep "), undone


# -------------------------------------------------- the gate, once; a red tip bisected (R5–R8, R17)


def _gate_attempts(root: Path, rev: str, name: str) -> list[dict]:
    """Every gate attempt in change `name`'s `build/land-*.gate.md` files as commit `rev` holds
    them, oldest file first."""
    rel = f".sdlc/work/{name}/build"
    listed = _git(root, "ls-tree", "--name-only", rev, "--", rel + "/") or ""
    found: list[dict] = []
    for path in sorted(p for p in listed.splitlines() if p.endswith(".gate.md") and "land-" in p):
        text = _git(root, "show", f"{rev}:{path}")
        attempts: list[dict] = []
        for line in text.splitlines():
            if line.startswith("## Attempt "):
                attempts.append({"file": path})
            elif attempts and line.startswith("Verdict: "):
                attempts[-1]["verdict"] = line[len("Verdict: ") :]
            elif attempts and line.startswith("Build: "):
                attempts[-1]["build"] = line[len("Build: ") :]
        found += attempts
    return found


def _closes(root: Path) -> dict[str, str]:
    """Each landed change's own commit, by name, from its `Close` on the first-parent line."""
    log = _git(root, "log", "--first-parent", "--format=%H %s", "main").splitlines()
    return {
        line.split(" ", 1)[1][len("Close ") :]: _git(root, "rev-parse", f"{line.split()[0]}^")
        for line in log if line.split(" ", 1)[1].startswith("Close ")
    }  # fmt: skip


@needs_uv
def test_a_green_train_of_three_gates_once(tmp_path, capsys) -> None:
    """R5: a train of three with no red gate, no fix and no move runs the base branch's check
    once, at the tip, in change 3's worktree, before any reviewer reads any change."""
    root, trees = _three(tmp_path, check="true")
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys)
    assert readings[-1]["next"] == "done" and len(readings[-1]["landed"]) == 3, readings[-1]
    steps = [(r["next"], r.get("change")) for r in readings]
    gates = [c for step, c in steps if step == "gate"]
    assert gates == [trees[2].name], "one gate, at the tip, in change 3's worktree"
    assert steps.index(("gate", trees[2].name)) < min(
        i for i, (step, _) in enumerate(steps) if step == "review"
    ), "before any reviewer"
    own = _closes(root)
    attempts = [a for name, sha in own.items() for a in _gate_attempts(root, sha, name)]
    assert len(attempts) == 1 and attempts[0]["verdict"] == "PASS", attempts
    assert attempts[0]["file"] == f".sdlc/work/{trees[2].name}/build/land-1.gate.md"


@needs_uv
def test_each_landed_change_records_its_place_in_the_train(tmp_path, capsys) -> None:
    """R17: each landed change's commit holds `runs/land-train.md` with its place, what it stacked
    on, and the tip's gate: its verdict, commit and the change folder whose gate file holds it."""
    root, trees = _three(tmp_path, check="true")
    _begin(root, capsys)
    assert drive_train(factory, root, capsys)[-1]["next"] == "done"
    own = _closes(root)
    names = [t.name for t in trees]
    tip_commit = None
    for k, name in enumerate(names, 1):
        text = _git(root, "show", f"{own[name]}:.sdlc/work/{name}/runs/land-train.md")
        lines = text.splitlines()
        assert f"TRAIN: {k} of 3" in lines, text
        assert f"STACKED ON: {names[k - 2] if k > 1 else 'main'}" in lines, text
        tip = next(ln for ln in lines if ln.startswith("TIP GATE: "))
        words = tip.split()
        assert words[2] == "PASS" and words[4] == f"{names[2]}/build/land-1.gate.md", tip
        tip_commit = tip_commit or words[3]
        assert words[3] == tip_commit, "one tip gate, named by every change"
    gated = _gate_attempts(root, own[names[2]], names[2])[0]["build"]
    assert tip_commit.startswith(gated) or gated.startswith(tip_commit), (tip_commit, gated)


@needs_uv
def test_a_red_tip_ejects_the_change_at_fault(tmp_path, capsys) -> None:
    """R6, R7: a check that fails while change 2's file exists: the tip is red, the prefixes are
    bisected (at most 1 + ⌈log₂ 3⌉ gates before the re-stack), change 2 is ejected back to its
    pre-train commit with its reason and the gate file that shows why, 1 and 3 land, nothing of
    2 reaches the base branch, and the re-stacked tip is gated again."""
    root, trees = _three(tmp_path, check="test ! -f bb.txt")
    base = _git(root, "rev-parse", "main")
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys)
    last = readings[-1]
    assert last["next"] == "done", last
    assert last["landed"] == [trees[0].name, trees[2].name]
    assert [e["change"] for e in last["ejected"]] == [trees[1].name]
    reason = last["ejected"][0]["reason"]
    assert "the gate failed" in reason and f"{trees[1].name}/build/land-1.gate.md" in reason
    steps = [(r["next"], r.get("change")) for r in readings]
    ejected_at = steps.index(("eject", trees[1].name))
    before = [c for step, c in steps[:ejected_at] if step == "gate"]
    assert len(before) <= 3 and before[0] == trees[2].name, before
    assert steps[ejected_at + 1 :].count(("gate", trees[2].name)) == 1, "the new tip, gated again"
    # R7: nothing of 2 on the base branch; its branch back as it was, with its reason.
    touched = _git(root, "log", "--format=", "--name-only", "main").splitlines()
    assert not any(p.startswith(f".sdlc/work/{trees[1].name}/") or p == "bb.txt" for p in touched)
    pre = readings[-1]["changes"][trees[1].name]["pre"]
    tree = trees[1]
    assert tree.exists() and _git(tree, "rev-parse", "HEAD^") == base, "its parent is its old base"
    assert subprocess.run(
        ["git", "-C", str(tree), "diff", "--quiet", pre, "HEAD", "--", ".", ":(exclude).sdlc/work"],
        capture_output=True,
    ).returncode == 0, "its tree outside its folder is its pre-train commit's"  # fmt: skip
    assert _git(tree, "status", "--porcelain") == "", "the record is in its commit"
    rel = f".sdlc/work/{tree.name}"
    step = factory.read_land_step(_git(tree, "show", f"HEAD:{rel}/{factory.LAND_STEP.as_posix()}"))
    assert step["step"] == "eject" and step["problems"] == [f"ejected from the train: {reason}"]
    assert "GATE: 2 FAIL" in _git(tree, "show", f"HEAD:{rel}/runs/land-train.md")
    did = readings[ejected_at]["did"]
    assert did["state"] == "ejected" and did["undo"].startswith("git reset --keep "), did
    assert _git(tree, "show", f"HEAD:{rel}/build/land-1.gate.md").startswith("GATE: FAIL")
    own = _closes(root)
    tips = _gate_attempts(root, own[trees[2].name], trees[2].name)
    assert [a["verdict"] for a in tips] == ["FAIL", "PASS"], tips


@needs_uv
def test_a_kept_landing_change_ejects_only_its_change(tmp_path, capsys) -> None:
    """R8: a landing review that keeps a change in change 2 ejects change 2 alone; 1 and 3 land."""
    root, trees = _three(tmp_path, check="true")
    base = _git(root, "rev-parse", "main")
    _begin(root, capsys)

    review, arbitrate = _keeping(trees[1].name)

    readings = drive_train(factory, root, capsys, review=review, arbitrate=arbitrate)
    last = readings[-1]
    assert last["next"] == "done", last
    assert last["landed"] == [trees[0].name, trees[2].name]
    assert [e["change"] for e in last["ejected"]] == [trees[1].name]
    assert "kept 1 change" in last["ejected"][0]["reason"], last["ejected"]
    assert trees[1].exists() and _git(trees[1], "rev-parse", "HEAD^") == base, "its old base"
    assert len([s for s in _first_parent(root) if s.startswith("Close ")]) == 2


@needs_uv
def test_a_change_landed_again_by_hand_on_the_base_is_reviewed_afresh(tmp_path, capsys) -> None:
    """A change ejected by its landing review, fixed and brought up to date with the base by hand,
    then landed again: already in place, its stack moves nothing, and the new landing opens a
    round of its own, never judged by the ejected round's kept change."""
    root, trees = _three(tmp_path, check="true")
    _begin(root, capsys)

    review, arbitrate = _keeping(trees[1].name)

    first = drive_train(factory, root, capsys, review=review, arbitrate=arbitrate)[-1]
    assert [e["change"] for e in first["ejected"]] == [trees[1].name], first
    folder = _folder(trees[1])
    ejected_round = factory.land_round(folder)
    code, out, said = factory._sdlc(["resolve", trees[1].name], trees[1])
    assert code == 0 and out["state"] == "clean", said
    _begin(root, capsys, "person", trees[1].name)
    readings = drive_train(factory, root, capsys)
    last = readings[-1]
    assert last["next"] == "done" and last["landed"] == [trees[1].name], last
    assert not last["ejected"], last["ejected"]
    rounds = {r["verdict"]["round"] for r in readings if r.get("next") == "review"}
    assert rounds == {ejected_round + 1}, "reviewed in a round of its own"


@needs_uv
def test_failing_acceptance_checks_as_stacked_eject_only_that_change(tmp_path, capsys) -> None:
    """R8: change 2's acceptance check passes on its own but fails once stacked on change 1
    (whose file it forbids): the check runs again on its stacked commit, and 2 alone is ejected,
    with the check's record named; 1 and 3 land."""
    root, trees = _three(tmp_path, check="true")
    (_folder(trees[1]) / "checks.md").write_text(
        "# Checks\n\n> Acceptance checks.\n\n## No aa.txt\n\n```sh\ntest ! -f aa.txt\n```\n",
        encoding="utf-8",
    )
    _begin(root, capsys, "person")
    readings = drive_train(factory, root, capsys)
    last = readings[-1]
    assert last["next"] == "done", last
    assert last["landed"] == [trees[0].name, trees[2].name]
    assert [e["change"] for e in last["ejected"]] == [trees[1].name]
    assert "acceptance checks failed" in last["ejected"][0]["reason"], last["ejected"]
    assert "build/land-accept.md" in last["ejected"][0]["reason"]
    steps = [(r["next"], r.get("change")) for r in readings]
    commit = next(r for r in readings if r["next"] == "commit" and r["change"] == trees[1].name)
    assert commit["before"] == ["accept"], "passed before the train, on its own base"
    assert ("accept", trees[1].name) in steps, "run again on the stacked commit"
    assert ("eject", trees[1].name) in steps
    record = _git(trees[1], "show", f"HEAD:.sdlc/work/{trees[1].name}/build/land-accept.md")
    assert record.startswith("ACCEPT: FAIL") and record.count("## Attempt") == 2, record
    assert len([s for s in _first_parent(root) if s.startswith("Close ")]) == 2


@needs_uv
def test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change(tmp_path, capsys):
    """R8: change 2's behaviour check gives verdict lines that disagree, none of them first (a
    verdict after a preamble alone is read, as `opening()` says); mended once, it does so again,
    which is a stop for the round and so 2's ejection alone; 1 and 3 land."""
    root, trees = _three(tmp_path, check="true")
    _begin(root, capsys)
    unreadable = "I ran it first.\n\nVERDICT: CHANGES\n- CHANGE: x\n" + verdict(
        factory, "behaviour"
    )

    def review(folder: Path, n: int, role: str) -> None:
        text = unreadable if folder.name == trees[1].name else verdict(factory, role)
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(text, encoding="utf-8")

    def mend(folder: Path, n: int, role: str) -> None:
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(unreadable, encoding="utf-8")

    readings = drive_train(factory, root, capsys, review=review, mend=mend)
    last = readings[-1]
    assert last["next"] == "done", last
    assert last["landed"] == [trees[0].name, trees[2].name]
    assert [e["change"] for e in last["ejected"]] == [trees[1].name]
    assert (
        "holds no VERDICT: PASS or VERDICT: CHANGES the script reads"
        in last["ejected"][0]["reason"]
    ), last["ejected"]
    steps = [(r["next"], r.get("change")) for r in readings]
    assert steps.count(("mend", trees[1].name)) == 1, "mended once, then a stop"
    assert ("eject", trees[1].name) in steps
    mended = _git(trees[1], "show", f"HEAD:.sdlc/work/{trees[1].name}/{factory.MENDED.as_posix()}")
    assert mended.split("\n")[0] == "behaviour land-1"
    assert len([s for s in _first_parent(root) if s.startswith("Close ")]) == 2


def _conflicting(
    tmp_path: Path, check: str | None = "true", tier2: bool = False, extra: dict | None = None
) -> tuple[Path, list[Path]]:
    """Two ready changes that edit README's first line: stacking the second conflicts. `extra` is
    more the second writes, which merges without a conflict."""
    root = _repo(tmp_path, check)
    first = _ready(root, "first", {"README.md": "first's one\ntwo\nthree\n"})
    second = _ready(root, "second", {"README.md": "second's one\ntwo\nthree\n", **(extra or {})},
                    tier=2 if tier2 else 1)  # fmt: skip
    return root, [first, second]


def _resolving(tree: Path, files: list[str]) -> None:
    assert files == ["README.md"], files
    (tree / "README.md").write_text("first's one, and second's\ntwo\nthree\n", encoding="utf-8")


@needs_uv
def test_a_train_resolution_is_reviewed_before_it_closes(tmp_path, capsys) -> None:
    """R4: a stack conflict resolved in change 2 is reviewed by every reviewer at its depth after
    the tip's gate passes; `land --close` refuses it while that review is missing."""
    root, trees = _conflicting(tmp_path)
    _begin(root, capsys)
    readings = drive_train(
        factory, root, capsys, resolve=_resolving, until=lambda o: o.get("next") == "review"
    )
    last = readings[-1]
    assert last["change"] == trees[1].name and set(last["verdict"]["missing"]) == set(
        factory.DEFAULTS["reviewers"]
    ), last
    steps = [(r["next"], r.get("change")) for r in readings]
    assert ("resolve", trees[1].name) in steps and ("gate", trees[1].name) in steps
    assert steps.index(("gate", trees[1].name)) < steps.index(("review", trees[1].name))
    code, out = _run(capsys, factory.landing.cmd_land_close, trees[1], "002")
    assert code == 1 and "no landing review has passed it" in out["refusals"][0], out
    assert _git(root, "log", "-1", "--format=%s", "main") == "init", "nothing closed"
    readings = drive_train(factory, root, capsys, resolve=_resolving)
    assert readings[-1]["next"] == "done" and len(readings[-1]["landed"]) == 2, readings[-1]
    assert (root / "README.md").read_text(encoding="utf-8").startswith("first's one, and second's")


@needs_uv
def test_a_train_conflict_goes_to_the_resolver_with_every_change(tmp_path, capsys, monkeypatch):
    """R3 (147), 149 R1-R3, R9, R10: the conflict goes to the resolver as `train-resolve`, a fresh
    session whose prompt names every change in the train, its spec (`spec.md`, or `intent.md` at
    Tier 1) and its diff; its session id and cost land under `resolver`, the builder's records
    untouched; a file the commit staged cleanly passes the fence, as the rebase left it; the
    counter still settles itself."""
    root, trees = _conflicting(tmp_path, tier2=True, extra={"notes.txt": "second's notes\n"})
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    last = readings[-1]
    assert last["change"] == trees[1].name and last["files"] == ["README.md"], last
    folder = _folder(trees[1])
    pre = {n: c["pre"] for n, c in last["changes"].items()}
    prompt, target, append = factory._land_task(trees[1], folder, "train-resolve", "resolver")
    assert target == folder / "build" / "land-1.md" and append is False
    for tree in trees:
        intent = _git(tree, "show", f"{pre[tree.name]}:.sdlc/work/{tree.name}/intent.md")
        title = next(ln[2:] for ln in intent.splitlines() if ln.startswith("# "))
        assert title in prompt, (title, prompt)
        spec = "spec.md" if tree is trees[1] else "intent.md"
        assert f"git show {pre[tree.name]}:.sdlc/work/{tree.name}/{spec}" in prompt, prompt
        assert f"git show {pre[tree.name]}`" in prompt, prompt
    assert "README.md" in prompt and "## Evidence" in prompt
    ident = trees[1].name.split("-", 1)[0]
    assert f"factory.py check {ident}`: it waits for a gate slot." in prompt, "155 R6"
    calls: list[list[str]] = []

    def fake(argv: list[str], cwd: Path):
        calls.append(argv)
        _resolving(trees[1], ["README.md"])
        figures = {"usd": 0.25, "duration_ms": 900, "turns": 2}
        return 0, "Kept both lines.\n\n## Evidence\n\n$ true\nexit: 0\n", None, figures

    monkeypatch.setattr(factory, "_claude", fake)
    runs = folder / "runs"
    builder = runs / "builder.sessions"
    before = builder.read_bytes() if builder.is_file() else None
    costs = runs / "costs.jsonl"
    rows_before = costs.read_text(encoding="utf-8").splitlines() if costs.is_file() else []
    untouched = (trees[1] / "notes.txt").read_bytes()
    code, out = _run(capsys, factory.cmd_agent, trees[1], "002", "train-resolve", None, None)
    assert code == 0 and out["role"] == "resolver" and out["model"] == "sonnet", out
    argv = calls[0]
    assert "--session-id" in argv and "--resume" not in argv, "never a resumed session"
    assert argv[argv.index("--agent") + 1] == "sdlc-factory:resolver", argv
    assert argv[argv.index("--model") + 1] == "sonnet", argv
    session = out["session"]
    assert (runs / "resolver.sessions").read_text(encoding="utf-8").split() == [session]
    assert (builder.read_bytes() if builder.is_file() else None) == before, "builder's untouched"
    rows = costs.read_text(encoding="utf-8").splitlines()
    assert rows[: len(rows_before)] == rows_before
    added = [json.loads(r) for r in rows[len(rows_before) :]]
    assert [(r["role"], r["model"], r["session"]) for r in added] == [
        ("resolver", "sonnet", session)
    ], added
    code, out = _run(capsys, factory.landing.cmd_resolve, trees[1], "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert (trees[1] / "notes.txt").read_bytes() == untouched, "R10: left as the rebase left it"
    assert (trees[1] / ".sdlc" / "last-id").read_text(encoding="utf-8").strip() == "002"
    dirty = _git(trees[1], "status", "--porcelain").splitlines()
    assert not any("resolver.sessions" in d for d in dirty), "the session id went into the commit"
    committed = _git(trees[1], "show", f"HEAD:.sdlc/work/{trees[1].name}/runs/resolver.sessions")
    assert committed.split() == [session]
    readings = drive_train(factory, root, capsys)
    assert readings[-1]["next"] == "done" and len(readings[-1]["landed"]) == 2, readings[-1]


@needs_uv
def test_a_train_conflict_in_a_non_ascii_path_resolves(tmp_path, capsys) -> None:
    """149 R14 (bug 2026-11-18-73): stacking conflicts in a file whose name holds non-ASCII
    characters; the conflict names it as it is, never git's quoted form, and `--continue` stages it
    by that name and continues."""
    name = "docs/café.md"
    root = _repo(tmp_path, "true")
    (root / "docs").mkdir()
    (root / name).write_text("one\ntwo\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a non-ASCII file")
    _ready(root, "first", {name: "first's one\ntwo\n"})
    second = _ready(root, "second", {name: "second's one\ntwo\n"})
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    assert readings[-1]["files"] == [name], readings[-1]
    assert factory._conflicted(second) == [name]
    (second / name).write_text("first's one, and second's\ntwo\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_resolve, second, "002", True)
    assert (code, out["state"], out["resolved"]) == (0, "resolved", [name]), out
    assert _git(second, "show", f"HEAD:{name}").startswith("first's one, and second's")


@needs_uv
def test_train_resolve_runs_no_role_but_the_resolver(tmp_path, capsys, monkeypatch) -> None:
    """149 R4: `train-resolve --role builder` is refused before any session starts or any
    `.sessions` file is written; `--role resolver` is the one it takes."""
    root, trees = _conflicting(tmp_path)
    _begin(root, capsys)
    drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    calls: list[list[str]] = []
    monkeypatch.setattr(
        factory, "_claude", lambda argv, cwd: calls.append(argv) or (1, "", "x", None)
    )
    runs = _folder(trees[1]) / "runs"
    before = sorted(p.name for p in runs.glob("*.sessions"))
    for role in ("builder", "code", "arbiter"):
        code, out = _run(capsys, factory.cmd_agent, trees[1], "002", "train-resolve", role, None)
        assert code == 1 and "resolver" in out["refusals"][0], out
    assert not calls and sorted(p.name for p in runs.glob("*.sessions")) == before


@needs_uv
def test_a_stack_conflicting_on_last_id_too_resolves(tmp_path, capsys) -> None:
    """171 R11 (nit 2026-11-18-84): a stack that conflicts on both README.md and `.sdlc/last-id`
    (each change numbered locally, the base holding no counter) goes to the resolver with
    README.md alone; it writes only that, and `--continue` goes through, the counter holding the
    higher number: `_settle_counter()` staged it before `_stray()` reads the status, so the fence
    never counts it."""
    root, trees = _conflicting(tmp_path)
    counter = ".sdlc/last-id"
    assert _git(root, "ls-tree", "--name-only", "main", counter) == "", "the base has none"
    assert [(t / counter).read_text(encoding="utf-8").strip() for t in trees] == ["001", "002"]
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    tree = trees[1]
    assert readings[-1]["files"] == ["README.md"], readings[-1]
    sides = [_git(tree, "show", f"{rev}:{counter}") for rev in ("HEAD", "REBASE_HEAD")]
    assert sides == ["001", "002"], "both sides added the counter: it conflicted"
    status = {line[3:]: line[:2] for line in _git(tree, "status", "--porcelain").splitlines()}
    assert status[counter][1] == " ", ("settled and staged, never left to the resolver", status)
    _resolving(tree, ["README.md"])
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert _git(tree, "show", f"HEAD:{counter}") == "002"
    assert (tree / counter).read_text(encoding="utf-8").strip() == "002"


@needs_uv
def test_a_resolution_outside_its_files_is_refused(tmp_path, capsys) -> None:
    """149 R8, R9: a resolution that also edits a tracked file the conflict didn't name, or
    leaves an untracked one, is refused by `--continue`, naming it, with nothing staged, no
    marker, and the rebase left under way; undone, the same resolution goes through, the file
    the replayed commit staged cleanly passing as the commit's own."""
    root, trees = _conflicting(tmp_path, extra={"notes.txt": "second's notes\n"})
    _begin(root, capsys)
    drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    tree, folder = trees[1], _folder(trees[1])
    _resolving(tree, ["README.md"])
    marker = folder / "runs" / "land-resolved"

    def refused(label: str, stray: str) -> None:
        code, out = _run(capsys, factory.landing.cmd_resolve, tree, "002", True)
        assert code == 1 and out["state"] == "refused", (label, out)
        why = out["refusals"][0]
        assert stray in why and "outside its conflicted files" in why, (label, why)
        assert not marker.exists(), f"{label}: no marker"
        assert factory.landing._rebasing(tree), f"{label}: the rebase is left under way"
        assert factory._conflicted(tree) == ["README.md"], f"{label}: nothing staged"
        step = factory.read_land_step((folder / factory.LAND_STEP).read_text(encoding="utf-8"))
        assert any("resolve 002 --continue" in p for p in step["problems"]), (label, step)

    (tree / "LICENSE.txt").write_text("not the conflict's\n", encoding="utf-8")
    refused("untracked", "LICENSE.txt")
    (tree / "LICENSE.txt").unlink()
    with (tree / ".gitignore").open("a", encoding="utf-8") as f:
        f.write("# touched\n")
    refused("tracked", ".gitignore")
    _git(tree, "checkout", "--", ".gitignore")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert _git(tree, "show", "HEAD:notes.txt") == "second's notes"


def _moving(tmp_path: Path, deletes_second: bool) -> tuple[Path, list[Path]]:
    """Two ready changes over `old.txt`: one moves it to `new.txt` (deletes it, adds the copy),
    the other edits its first line. With `deletes_second`, the second moves it (git's `UD` when it
    stacks); else the first does (`DU`)."""
    root = _repo(tmp_path, "true")
    (root / "old.txt").write_text("one\ntwo\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "old.txt")
    edit = {"old.txt": "edited one\ntwo\n"}
    move = {"new.txt": "one\nthree\nfour\nfive\n"}  # a split, never a rename git detects
    first = _ready(
        root, "first", edit if deletes_second else move, gone=() if deletes_second else ("old.txt",)
    )
    second = _ready(
        root,
        "second",
        move if deletes_second else edit,
        gone=("old.txt",) if deletes_second else (),
    )
    return root, [first, second]


def _carrying(tree: Path, files: list[str]) -> None:
    """The resolver's answer to a modify/delete: the deletion stands and the edit goes where the
    content went."""
    assert files == ["old.txt"], files
    (tree / "old.txt").unlink()
    (tree / "new.txt").write_text("edited one\nthree\nfour\nfive\n", encoding="utf-8")


@needs_uv
@pytest.mark.parametrize("deletes_second", [True, False], ids=["UD", "DU"])
def test_a_modify_delete_conflict_reaches_the_resolver_and_lands(
    tmp_path, capsys, deletes_second
) -> None:
    """196 (bug 2026-11-20-14): a stack where one change deletes a file the other edited goes to
    the resolver, told which side deleted it, where the surviving text is, what the other side
    changed and where the content went; it keeps the deletion and carries the edit into the moved
    file, `--continue` stages both and continues, the marker names both for the review, and the
    train lands."""
    root, trees = _moving(tmp_path, deletes_second)
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    assert readings[-1]["files"] == ["old.txt"], readings[-1]
    tree, folder = trees[1], _folder(trees[1])
    prompt, _, _ = factory._land_task(tree, folder, "train-resolve", "resolver")
    side = "this change" if deletes_second else "the change it is stacked on"
    stage = ":2:" if deletes_second else ":3:"
    assert f"old.txt is deleted by {side}" in prompt, prompt
    assert f"git show {stage}old.txt" in prompt and "new.txt" in prompt, prompt
    assert "git diff " in prompt and " -- old.txt" in prompt, prompt
    _carrying(tree, ["old.txt"])
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert _git(tree, "ls-tree", "--name-only", "HEAD", "old.txt") == "", "the deletion stands"
    assert _git(tree, "show", "HEAD:new.txt") == "edited one\nthree\nfour\nfive"
    marker = (folder / "runs" / "land-resolved").read_text(encoding="utf-8").splitlines()
    assert marker[1] == "old.txt, new.txt", marker
    assert _git(tree, "status", "--porcelain") == ""
    readings = drive_train(factory, root, capsys, resolve=_carrying)
    assert readings[-1]["next"] == "done" and len(readings[-1]["landed"]) == 2, readings[-1]
    assert not (root / "old.txt").exists()
    assert (root / "new.txt").read_text(encoding="utf-8") == "edited one\nthree\nfour\nfive\n"


@needs_uv
def test_a_modify_delete_resolution_outside_the_moved_files_is_refused(tmp_path, capsys) -> None:
    """196: the files the deleting commit added or changed are the only ones beyond the conflict a
    modify/delete resolution may edit: another tracked file is still refused."""
    root, trees = _moving(tmp_path, deletes_second=True)
    _begin(root, capsys)
    drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")
    tree = trees[1]
    _carrying(tree, ["old.txt"])
    (tree / "README.md").write_text("not the conflict's\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "002", True)
    assert code == 1 and "README.md" in out["refusals"][0], out
    assert "new.txt" not in out["refusals"][0], out


# ------------------------------------------------------------- the base moves under the train (R10)


@needs_uv
def test_a_train_stop_has_a_plain_line_over_its_raw_text(tmp_path, capsys) -> None:
    """2026-11-18-20, in the train: a stray file refusing the stack, a stack git refuses and
    markers left after `resolve --continue` each record a plain line naming the way on, git's or
    the script's raw words under it, and the refusal keeps the raw words."""

    def stop(tree: Path) -> list[str]:
        return factory.read_land_step(
            (_folder(tree) / factory.LAND_STEP).read_text(encoding="utf-8")
        )["problems"]

    for sub in ("three", "two"):
        (tmp_path / sub).mkdir()
    root, _ = _three(tmp_path / "three", check="true")
    _begin(root, capsys)
    out = drive_train(factory, root, capsys, until=lambda r: r.get("next") == "stack")[-1]
    tree, num = Path(out["worktree"]), out["change"].split("-")[0]
    (tree / "stray.txt").write_text("not the change's\n", encoding="utf-8")
    code, done = _run(capsys, factory.landing.cmd_resolve, tree, num, False, onto=out["onto"])
    assert code == 1 and done["refusals"][0].startswith("uncommitted outside"), done
    plain, raw = stop(tree)
    assert (
        "stray.txt" in plain and f"/sdlc-factory:land {num}" in plain and raw == done["refusals"][0]
    )
    (tree / "stray.txt").unlink()
    code, done = _run(capsys, factory.landing.cmd_resolve, tree, num, False, onto="0" * 40)
    assert code == 1 and done["refusals"][0].startswith("git rebase --onto"), done
    plain, raw = stop(tree)
    assert plain.startswith("stacking it onto") and f"/sdlc-factory:land {num}" in plain
    assert raw == done["refusals"][0]

    root, (_, second) = _conflicting(tmp_path / "two")
    _begin(root, capsys)
    drive_train(factory, root, capsys, until=lambda r: r.get("next") == "resolve")
    code, done = _run(capsys, factory.landing.cmd_resolve, second, "002", True)
    assert code == 1 and "conflict markers left" in done["refusals"][0], "not resolved yet"
    plain, raw = stop(second)
    assert "sdlc.py resolve 002 --continue" in plain, "a plain line first"
    assert raw.startswith("conflict markers left in: README.md"), "the raw text"


def _file_an_idea(root: Path, capsys, n: int) -> None:
    """Another session files an idea on the base branch: `inbox-commit`, a `File` commit."""
    text = (root / INBOX).read_text(encoding="utf-8")
    (root / INBOX).write_text(
        text + f"\n## [2026-10-02-{n}] [idea] Late {n}\n\nFiled meanwhile.\n", encoding="utf-8"
    )
    code, out = _run(capsys, sdlc.cmd_inbox_commit, root)
    assert code == 0, out


@needs_uv
def test_a_move_mid_train_re_stacks_the_rest_and_counts_once(tmp_path, capsys) -> None:
    """R10: an `inbox-commit` between `Close A` and B is a move: B and C re-stack onto the base,
    the new tip is gated once more, each is reviewed again, the move counts once for the train,
    and B and C land with `Close B`'s parent being B."""
    root, trees = _three(tmp_path, check="true")
    names = [t.name for t in trees]
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("landed") == names[:1])
    assert readings[-1]["next"] == "close" and readings[-1]["change"] == names[1], readings[-1]
    _file_an_idea(root, capsys, 1)
    more = drive_train(factory, root, capsys)
    last = more[-1]
    assert last["next"] == "done" and last["landed"] == names, last
    assert last["moves"] == 1, "one move, counted once for the train"
    steps = [(r["next"], r.get("change")) for r in readings + more]
    assert [c for step, c in steps if step == "gate"] == [names[2], names[2]], "one more gate"
    assert [c for step, c in steps if step == "stack"].count(names[1]) == 2, "B re-stacked"
    assert [c for step, c in steps if step == "review"].count(names[1]) == 2, "B reviewed again"
    subjects = _first_parent(root)
    assert subjects[:4] == [f"Close {names[2]}", _title(root, names[2]), f"Close {names[1]}",
                            _title(root, names[1])], subjects  # fmt: skip
    assert "File 2026-10-02-1" in subjects and subjects.index("File 2026-10-02-1") == 4
    assert "Late 1" in (root / INBOX).read_text(encoding="utf-8")
    own = _closes(root)
    text = _git(root, "show", f"{own[names[1]]}:.sdlc/work/{names[1]}/runs/land-train.md")
    assert "STACKED ON: " + names[0] in text and "TIP GATE: PASS" in text


def _title(root: Path, name: str) -> str:
    """A landed change's commit subject: its intent's title, as `land_message()` writes it."""
    own = _closes(root)
    return _git(root, "log", "-1", "--format=%s", own[name])


@needs_uv
def test_a_train_stops_past_land_moves(tmp_path, capsys) -> None:
    """R10: with `[land] moves = 1` on the base branch, the first move is followed and the second
    stops the train, every change not landed back at its pre-train commit."""
    root = _repo(tmp_path, check="true")
    (root / ".sdlc" / "factory.toml").write_text("[land]\nmoves = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "land.moves = 1")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb", "cc")]
    names = [t.name for t in trees]
    base = _git(root, "rev-parse", "main")
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("landed") == names[:1])
    pre = {n: c["pre"] for n, c in readings[-1]["changes"].items()}
    _file_an_idea(root, capsys, 1)
    more = drive_train(
        factory, root, capsys, until=lambda o: o.get("next") == "close" and o["moves"] == 1
    )
    assert more[-1]["change"] == names[1], more[-1]
    _file_an_idea(root, capsys, 2)
    rest = drive_train(factory, root, capsys)
    assert rest[-2]["next"] == "stop" and "moved 2 times" in rest[-2]["reason"], rest[-2]
    assert rest[-1]["state"] == "stopped"
    assert len([s for s in _first_parent(root) if s.startswith("Close ")]) == 1
    for tree in trees[1:]:
        assert tree.exists() and _git(tree, "rev-parse", "HEAD^") == base, tree.name
        assert _git(tree, "status", "--porcelain") == ""
        assert subprocess.run(
            ["git", "-C", str(tree), "diff", "--quiet", pre[tree.name], "HEAD", "--", ".",
             ":(exclude).sdlc/work"], capture_output=True,
        ).returncode == 0, tree.name  # fmt: skip
    assert not _state_file(root).exists()


# ---------------------------------------------------------------- waiting its turn (145 R22)


def _waits(tree: Path) -> tuple[str, str | None]:
    rec = factory.read_land_step((_folder(tree) / factory.LAND_STEP).read_text(encoding="utf-8"))
    return rec["step"], rec["waits"]


@needs_uv
def test_a_waiting_change_records_what_it_waits_on(tmp_path, capsys) -> None:
    """145 R22: as the train turns to a change, each committed change after it records `wait`
    and the live change before it: to stack on while it isn't stacked, to close after once it is;
    the train lands all three as before."""
    root, trees = _three(tmp_path)
    names = [t.name for t in trees]
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "stack")
    assert readings[-1]["change"] == names[1], readings[-1]
    assert _waits(trees[2]) == ("wait", f"stack on {names[1]}")
    assert _waits(trees[0])[0] != "wait", "a change before the one acted on never waits"
    readings = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "close")
    assert readings[-1]["change"] == names[0], readings[-1]
    assert _waits(trees[1]) == ("wait", f"close after {names[0]}")
    assert _waits(trees[2]) == ("wait", f"close after {names[1]}")
    times = factory.read_land_times(
        (_folder(trees[2]) / factory.LAND_TIMES).read_text(encoding="utf-8")
    )
    assert any(row["step"] == "wait" for row in times), times
    drive_train(factory, root, capsys)
    assert [s for s in _first_parent(root) if s.startswith("Close ")] == [
        f"Close {n}" for n in reversed(names)
    ]


# ------------------------------------------------------------- why each ejection (147 R16)


@needs_uv
def test_every_ejection_names_its_cause(tmp_path, capsys) -> None:
    """147 R16: every `eject` reading carries `cause`: `gate` from a red tip's bisection, `review`
    from a landing round that stops, `refusal` from a landing command's own refusal; `--eject`
    keeps it, and the reading's `ejected` list carries it."""

    def ejections(readings: list[dict]) -> list[dict]:
        found = [r for r in readings if r.get("next") == "eject"]
        assert found and all(r.get("cause") for r in found), found
        return found

    (tmp_path / "gate").mkdir()
    root, trees = _three(tmp_path / "gate", check="test ! -f bb.txt")
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys)
    assert [r["cause"] for r in ejections(readings)] == ["gate"]
    assert readings[-1]["ejected"][0]["cause"] == "gate", readings[-1]["ejected"]

    (tmp_path / "review").mkdir()
    root, trees = _three(tmp_path / "review", check="true")
    _begin(root, capsys)

    review, arbitrate = _keeping(trees[1].name)

    readings = drive_train(factory, root, capsys, review=review, arbitrate=arbitrate)
    assert [r["cause"] for r in ejections(readings)] == ["review"]
    assert readings[-1]["ejected"][0]["cause"] == "review"

    (tmp_path / "refusal").mkdir()
    root, trees = _three(tmp_path / "refusal", check="true")
    _begin(root, capsys)
    out = drive_train(factory, root, capsys, until=lambda r: r.get("next") == "stack")[-1]
    tree, num = Path(out["worktree"]), out["change"].split("-")[0]
    (tree / "stray.txt").write_text("not the change's\n", encoding="utf-8")
    assert _run(capsys, factory.landing.cmd_resolve, tree, num, False, onto=out["onto"])[0] == 1
    (tree / "stray.txt").unlink()
    readings = drive_train(factory, root, capsys)
    assert [r["cause"] for r in ejections(readings)] == ["refusal"]
    assert readings[-1]["ejected"][0]["cause"] == "refusal"
    state_ejections = [r["did"] for r in readings if r.get("next") == "eject"]
    assert state_ejections[0]["cause"] == "refusal", state_ejections


# ------------------------------------------------------- a resolution leaves it clean (147 R14)


@needs_uv
def test_a_resolution_leaves_the_worktree_clean(tmp_path, capsys) -> None:
    """147 R14: after `resolve --continue`, the landing agent's reply and `runs/land-resolved`
    are in the rebased commit, and the worktree is clean."""
    root, trees = _conflicting(tmp_path)
    _begin(root, capsys)
    out = drive_train(factory, root, capsys, until=lambda o: o.get("next") == "resolve")[-1]
    tree, folder = trees[1], _folder(trees[1])
    reply = folder / "build" / f"land-{out['round']}.md"
    reply.parent.mkdir(exist_ok=True)
    reply.write_text("Kept both lines.\n\n## Evidence\n\n$ true\nexit: 0\n", encoding="utf-8")
    _resolving(tree, out["files"])
    code, done = _run(capsys, factory.landing.cmd_resolve, tree, "002", True)
    assert (code, done["state"]) == (0, "resolved"), done
    assert _git(tree, "status", "--porcelain") == "", "nothing left uncommitted"
    rel = f".sdlc/work/{tree.name}"
    marker = _git(tree, "show", f"HEAD:{rel}/runs/land-resolved")
    assert marker.splitlines() == [f"land-{out['round']}", "README.md"], marker
    assert "Kept both lines." in _git(tree, "show", f"HEAD:{rel}/build/land-{out['round']}.md")


@needs_uv
def test_a_failed_resolution_leaves_no_marker(tmp_path, capsys) -> None:
    """147 R14: a second conflict aborts the rebase, and the abort takes the staged marker with
    it: the branch is where it was, and no `runs/land-resolved` is left."""
    root = _repo(tmp_path)
    tree = _ready(root, "twice", {"README.md": "twice's one\ntwo\nthree\n"})
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "built")
    (tree / "README.md").write_text("twice's one, again\ntwo\nthree\n", encoding="utf-8")
    _git(tree, "commit", "-q", "-am", "built again")
    (root / "README.md").write_text("main's one\ntwo\nthree\n", encoding="utf-8")
    _git(root, "commit", "-q", "-am", "main moves")
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", False, onto="main")
    assert (code, out["state"]) == (0, "conflict"), out
    (tree / "README.md").write_text("main's one, and twice's\ntwo\nthree\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "001", True)
    assert code == 1 and "second conflict" in out["refusals"][0], out
    assert _git(tree, "rev-parse", "HEAD") == head, "the abort put the branch back"
    assert not (_folder(tree) / "runs" / "land-resolved").exists(), "no marker left"


# ------------------------------------------------------------- one driver for a train (147 R15)


@pytest.mark.portable
def test_the_train_driver_takes_every_step_a_reading_names() -> None:
    """147 R15: `TRAIN_STEPS` lists every `next` `_train_reading()` can emit (its own `done()`
    calls, `_train_gate()`'s and the landing round's, as `land_verdict()` names them), and both
    the shared test driver and the loop (`RUN_STEPS`, a stop in `RUN_STOPS`, or `done`) take
    each; no test file keeps a driver of its own."""
    emitted = set(
        re.findall(r'done\(\s*"(\w+)"', inspect.getsource(factory.landing._train_reading))
    )
    for steps in (factory.landing._train_gate, factory.landing._train_build):
        emitted |= set(re.findall(r'"next": "(\w+)"', inspect.getsource(steps)))
    emitted |= {"checks"}  # `checks_clearance()`'s `step`, named through `done()`
    verdicts = inspect.getsource(factory.landing.land_verdict)
    emitted |= set(re.findall(r'out\["next"\](?:, out\["\w+"\])? = \(?\s*"(\w+)"', verdicts))
    emitted |= {"eject", "stop"}  # `ejecting()` and `stopping()`
    emitted.discard("pass")  # a passing round goes on to the next change, never a step
    assert {"commit", "stack", "gate", "build", "review", "close", "fix", "done"} <= emitted
    assert emitted <= set(factory.landing.TRAIN_STEPS), emitted - set(factory.landing.TRAIN_STEPS)
    assert set(factory.landing.TRAIN_STEPS) <= DRIVER_STEPS
    covered = set(factory.landing.RUN_STEPS) | set(factory.landing.RUN_STOPS) | {"done"}
    assert covered == set(factory.landing.TRAIN_STEPS), covered ^ set(factory.landing.TRAIN_STEPS)
    # 185: `accept` is both, the loop's own step while cleared and the person's while not.
    assert set(factory.landing.RUN_STEPS) & set(factory.landing.RUN_STOPS) == {"accept"}
    own = [f"def _{name}(" for name in ("drive", "land_train")]  # never this test's own text
    for path in (ROOT / "tests").glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(d in text for d in own), path.name


# ------------------------------------------------------------- the loop: train --run (147)

SCRIPT = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
KEEPS = "VERDICT: CHANGES\n- CHANGE: bb.txt:1: say more\n\n## Evidence\n$ true\nexit: 0\n"


def _loop(root: Path, capsys) -> tuple[int, dict, str]:
    """`train --run` in process, its own steps each a subprocess: exit, JSON, progress lines."""
    capsys.readouterr()
    code = factory.landing.cmd_train(root, run=True)
    said = capsys.readouterr()
    return code, json.loads(said.out), said.err


def _committed_step(root: Path, name: str) -> dict:
    """The `runs/land-step.md` a landed change's own commit holds."""
    own = _closes(root)[name]
    return factory.read_land_step(
        _git(root, "show", f"{own}:.sdlc/work/{name}/{factory.LAND_STEP.as_posix()}")
    )


def _kept_at_two(tmp_path: Path, capsys, monkeypatch) -> tuple[Path, list[Path], dict]:
    """Three changes whose loop stops at the second: its behaviour check asks for a change and
    the arbiter keeps it. Returns the repo, the worktrees and the loop's JSON."""
    root, trees = _three(tmp_path, check="true")
    two = trees[1].name
    fake_claude(tmp_path, monkeypatch, {
        f"{two}:reviewer-behaviour": {"reply": KEEPS},
        f"{two}:arbiter": {"reply": "- KEPT: behaviour: bb.txt:1: say more\n"},
    })  # fmt: skip
    _begin(root, capsys)
    code, out, _ = _loop(root, capsys)
    assert code == 1, out
    return root, trees, out


@needs_uv
def test_train_run_lands_a_batch_of_three(tmp_path, capsys, monkeypatch) -> None:
    """147 R1: one `train --run`, its agents stood in for by a fake `claude`, ends `done` with
    three `Close` commits on the base branch's first-parent line, in order."""
    root, trees = _three(tmp_path, check="true")
    calls = fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, _ = _loop(root, capsys)
    names = [t.name for t in trees]
    assert (code, out.get("done")) == (0, True), out
    assert out["landed"] == names and out["ejected"] == [] and out["gates"] == 1, out
    closes = [s for s in _first_parent(root) if s.startswith("Close ")]
    assert closes == [f"Close {n}" for n in reversed(names)]
    assert {c["agent"] for c in calls()} == {"reviewer-behaviour"}, "the stacked ones reviewed"
    assert not _state_file(root).exists()


@needs_uv
def test_train_run_records_each_step(tmp_path, capsys, monkeypatch) -> None:
    """147 R2: each step the loop takes is recorded by its command in the change's
    `runs/land-step.md`, which each landed commit holds as `close` with its place in the train;
    the loop says each step on stderr, one line a step."""
    root = _repo(tmp_path, check="true")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, err = _loop(root, capsys)
    assert code == 0, out
    lines = err.splitlines()
    for step, tree in (("commit", trees[0]), ("commit", trees[1]), ("stack", trees[1]),
                       ("gate", trees[1]), ("review", trees[1]), ("close", trees[0]),
                       ("close", trees[1])):  # fmt: skip
        assert any(ln.startswith(f"train: {step} {tree.name}") for ln in lines), (step, err)
    for k, tree in enumerate(trees, 1):
        step = _committed_step(root, tree.name)
        assert step["step"] == "close" and step["train"] == {"k": k, "n": 2}, step
    review = _git(root, "show", f"{_closes(root)[trees[1].name]}:.sdlc/work/{trees[1].name}/"
                  "reviews/land-1/behaviour.md")  # fmt: skip
    assert review.startswith("VERDICT: PASS"), review


@pytest.mark.portable
def test_the_loop_runs_only_its_named_commands() -> None:
    """147 R3: `RUN_STEPS` names exactly the commands the loop may run; never `cases` or
    `--stop`, `--eject` only as the gate's step, and since 185 `accept` only as stacked and
    cleared (`_run_plan()`), the approver's `land-checks`, and `gate --land --build`."""
    commands = {" ".join(argv) for argvs in factory.landing.RUN_STEPS.values() for argv in argvs}
    assert commands == {
        "land {change} --by {by}", "resolve {change} --onto {onto}",
        "agent {change} --task train-resolve", "resolve {change} --continue",
        "gate {change} --land", "train --eject {change}",
        "agent {change} --task land-review --role {role}", "agent {change} --task land-arbitrate",
        "agent {change} --task land-mend --role {role}", "land-fix {change} --ask {ask}",
        "agent {change} --task land-fix", "land-fix {change} --commit", "land {change} --close",
        "accept {change}", "agent {change} --task land-checks", "gate {change} --land --build",
    }, commands  # fmt: skip
    assert factory.landing.RUN_EJECTS == ("gate",)
    assert set(factory.landing.RUN_STOPS) == {"accept", "stop"}


def _stubbed_loop(
    tmp_path: Path, capsys, monkeypatch, reading: dict, result: dict | None = None
) -> tuple[int, dict, list]:
    """`train --run` over a train that names `reading` once and `done` after, its steps' commands
    answering `result` (exit 0 and no JSON when None), with no process started: the loop's own
    stops, apart from the commands they follow. Returns its exit, its JSON and the groups run."""
    readings = iter([reading, {"next": "done"}])
    ran: list = []
    monkeypatch.setattr(
        factory.landing, "_run_one", lambda main, argv, cwd: (0, next(readings), "")
    )

    def group(main: Path, members: list) -> list[dict]:
        ran.append(members)
        answer = {"code": 0, "said": "", "out": None, **(result or {})}
        return [{"argv": argv, **answer} for argv, _ in members]

    monkeypatch.setattr(factory.landing, "_run_group", group)
    capsys.readouterr()
    code = factory.landing._run_loop(tmp_path)
    return code, json.loads(capsys.readouterr().out), ran


def _step(nxt: str, **parts) -> dict:
    return {"next": nxt, "change": "002-bb", "worktree": "nowhere", "by": "auto", **parts}


@pytest.mark.portable
def test_train_run_stops_at_a_failed_step(tmp_path, capsys, monkeypatch) -> None:
    """171 R13 (nit 2026-11-18-70): a step whose command exits non-zero stops the loop, naming
    the exit, and runs nothing after it."""
    code, out, ran = _stubbed_loop(tmp_path, capsys, monkeypatch, _step("commit"), {"code": 2})
    assert code == 1 and len(ran) == 1, (out, ran)
    assert out["stopped"]["next"] == "commit" and out["stopped"]["reason"] == "exit 2", out
    assert factory.landing.PUT_BACK in out["stopped"]["way_on"], out


@pytest.mark.portable
def test_train_run_stops_at_an_agents_problem(tmp_path, capsys, monkeypatch) -> None:
    """171 R13: an agent whose JSON holds `problem`, though it exited 0, stops the loop, naming
    the problem."""
    problem = {"out": {"problem": "the arbiter's reply holds no KEPT or DROPPED line"}}
    code, out, ran = _stubbed_loop(tmp_path, capsys, monkeypatch, _step("arbitrate"), problem)
    assert code == 1 and len(ran) == 1, (out, ran)
    assert out["stopped"]["reason"] == problem["out"]["problem"], out


@pytest.mark.portable
def test_train_run_stops_at_a_resolve_with_no_conflict(tmp_path, capsys, monkeypatch) -> None:
    """171 R13: `resolve` named with no conflicted file stops the loop before any agent starts,
    telling the person to run git status in the change's worktree."""
    reading = _step("resolve", files=[])
    code, out, ran = _stubbed_loop(tmp_path, capsys, monkeypatch, reading)
    assert code == 1 and ran == [], (out, ran)
    assert "with no conflicted file" in out["stopped"]["reason"], out
    assert out["stopped"]["way_on"].startswith("run git status in its worktree"), out


@pytest.mark.portable
def test_train_run_stops_at_the_trains_stop(tmp_path, capsys, monkeypatch) -> None:
    """171 R13: a train that reads `stop` (past `land.moves`) stops the loop with the train's own
    reason, and the way on puts every change not landed back."""
    why = "main moved 4 times while landing, past land.moves (3)"
    code, out, ran = _stubbed_loop(tmp_path, capsys, monkeypatch, _step("stop", reason=why))
    assert code == 1 and ran == [], (out, ran)
    assert out["stopped"]["reason"] == why, out
    assert factory.landing.PUT_BACK in out["stopped"]["way_on"], out


@needs_uv
def test_train_run_never_runs_a_prompted_command(tmp_path, capsys, monkeypatch) -> None:
    """147 R3: a change with an acceptance check not yet run stops the loop at its commit, whose
    `before` names `accept`; the loop never runs it, so `build/land-accept.md` is never written."""
    root = _repo(tmp_path, check="true")
    tree = _ready(root, "checked", {"checked.txt": "checked\n"})
    (_folder(tree) / "checks.md").write_text(
        "# Checks\n\n> Acceptance checks.\n\n## Its file\n\n```sh\ntest -f checked.txt\n```\n",
        encoding="utf-8",
    )
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys, "person")
    code, out, _ = _loop(root, capsys)
    assert code == 1 and out["stopped"]["next"] == "commit", out
    assert out["stopped"]["change"] == tree.name and "accept" in out["stopped"]["way_on"], out
    assert not (_folder(tree) / "build" / "land-accept.md").exists(), "accept never ran"
    assert "Sdlc-Landed" not in _git(tree, "log", "-1", "--format=%B"), "nothing committed"


@needs_uv
def test_train_run_stops_at_a_kept_change(tmp_path, capsys, monkeypatch) -> None:
    """147 R4, R2: the landing reviewer of change two keeps a change: the loop exits naming
    `eject`, cause `review`, change two, its reason and the way on, recorded as a `stop` in two's
    `runs/land-step.md`; two is still at its stacked commit, and nothing is closed."""
    root, trees, out = _kept_at_two(tmp_path, capsys, monkeypatch)
    two = trees[1].name
    stopped = out["stopped"]
    assert (stopped["next"], stopped["cause"], stopped["change"]) == ("eject", "review", two), out
    assert "kept 1 change" in stopped["reason"], stopped
    assert "/sdlc-factory:land" in stopped["way_on"] and "train --stop" in stopped["way_on"]
    reading = _run(capsys, factory.landing.cmd_train, root)[1]
    assert _git(trees[1], "rev-parse", "HEAD") == reading["changes"][two]["stacked"]
    assert not [s for s in _first_parent(root) if s.startswith("Close ")], "nothing closed"
    step = factory.read_land_step(
        (_folder(trees[1]) / factory.LAND_STEP).read_text(encoding="utf-8")
    )
    assert step["step"] == "stop" and step["problems"] == [stopped["reason"], stopped["way_on"]]


@needs_uv
def test_train_run_resumes_after_a_kept_change(tmp_path, capsys, monkeypatch) -> None:
    """147 R5: after the stop at a kept change, the person's `train --eject <two>`, then
    `train --run`, lands one and three."""
    root, trees, out = _kept_at_two(tmp_path, capsys, monkeypatch)
    code, ejected = _run(capsys, factory.landing.cmd_train, root, eject=trees[1].name)
    assert code == 0 and ejected["cause"] == "review", ejected
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    assert out["landed"] == [trees[0].name, trees[2].name]
    assert [(e["change"], e["cause"]) for e in out["ejected"]] == [(trees[1].name, "review")]


@needs_uv
def test_train_run_stops_at_a_refusal(tmp_path, capsys, monkeypatch) -> None:
    """147 R4: a step command that refuses stops the loop with its words; the rerun's reading
    names the change's ejection, cause `refusal`, which the loop leaves to the person."""
    root, trees = _three(tmp_path, check="true")
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    out = drive_train(factory, root, capsys, until=lambda r: r.get("next") == "stack")[-1]
    tree = Path(out["worktree"])
    (tree / "stray.txt").write_text("not the change's\n", encoding="utf-8")
    code, out, _ = _loop(root, capsys)
    assert code == 1 and out["stopped"]["next"] == "stack", out
    assert out["stopped"]["reason"].startswith("uncommitted outside"), out
    (tree / "stray.txt").unlink()
    code, out, _ = _loop(root, capsys)
    stopped = out["stopped"]
    assert code == 1 and (stopped["next"], stopped["cause"]) == ("eject", "refusal"), out
    assert stopped["change"] == tree.name and "/sdlc-factory:land" in stopped["way_on"]
    assert not out["ejected"], "the loop ejected nothing itself"


@needs_uv
def test_train_run_stops_at_a_refused_push(tmp_path, capsys, monkeypatch) -> None:
    """147 R4: a close whose push is refused has landed the change, and stops the loop with
    close's own words."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "config.toml").write_text('[git]\npush = ["close"]\n', encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "push on close")
    _git(root, "remote", "add", "origin", str(tmp_path / "no-such-remote"))
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, _ = _loop(root, capsys)
    stopped = out["stopped"]
    assert code == 1 and (stopped["next"], stopped["change"]) == ("close", trees[0].name), out
    assert "/sdlc:publish" in stopped["way_on"], stopped
    assert out["landed"] == [trees[0].name], "the change has landed"
    assert _first_parent(root)[0] == f"Close {trees[0].name}"


@needs_uv
def test_train_run_stops_when_nothing_moves(tmp_path, capsys, monkeypatch) -> None:
    """147 R4: the same step named for the same change twice in a row, with the train's state
    unchanged, is a stop: here every step is stood in for by one that does nothing."""
    root, trees = _three(tmp_path, check="true")
    _begin(root, capsys)
    ran: list[list[str]] = []

    def idle(main: Path, group: list[tuple[list[str], Path]]) -> list[dict]:
        ran.extend(argv for argv, _ in group)
        return [{"argv": argv, "code": 0, "out": {}, "said": ""} for argv, _ in group]

    monkeypatch.setattr(factory.landing, "_run_group", idle)
    code, out, _ = _loop(root, capsys)
    stopped = out["stopped"]
    assert code == 1 and (stopped["next"], stopped["change"]) == ("commit", trees[0].name), out
    assert "twice" in stopped["reason"] and "/sdlc-factory:land" in stopped["way_on"], stopped
    assert ran == [["land", trees[0].name, "--by", "auto"]], "one try, then the stop"


@needs_uv
def test_train_run_ejects_a_gate_fault_and_lands_the_rest(tmp_path, capsys, monkeypatch) -> None:
    """147 R5: a check that fails whenever change two's file exists: one `train --run` ends
    `done` with one and three landed; two is back at its pre-train commit, its committed
    `runs/land-step.md` says `eject` and names its gate file, and the exit JSON lists it under
    `ejected` with cause `gate` and the undo `--eject` printed."""
    root, trees = _three(tmp_path, check="test ! -f bb.txt")
    base = _git(root, "rev-parse", "main")
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    assert out["landed"] == [trees[0].name, trees[2].name]
    [ejected] = out["ejected"]
    assert (ejected["change"], ejected["cause"]) == (trees[1].name, "gate"), ejected
    assert out["undos"] and out["undos"][0]["undo"].startswith("git reset --keep "), out
    tree = trees[1]
    assert _git(tree, "rev-parse", "HEAD^") == base and _git(tree, "status", "--porcelain") == ""
    rel = f".sdlc/work/{tree.name}"
    step = factory.read_land_step(_git(tree, "show", f"HEAD:{rel}/{factory.LAND_STEP.as_posix()}"))
    assert step["step"] == "eject" and f"{tree.name}/build/land-1.gate.md" in step["problems"][0]


@needs_uv
def test_a_second_train_run_refuses_while_one_runs(tmp_path, capsys, monkeypatch) -> None:
    """147 R6: while the run lock is held, a second `--run`, `--begin`, `--eject` and `--stop`
    refuse and a plain reading says `running: true`, none of them touching the state file; with
    the loop's marker set (`TRAIN_RUN_ENV`), each goes ahead."""
    root, trees = _three(tmp_path)
    _begin(root, capsys)
    state = _state_file(root)
    before = state.read_bytes()
    monkeypatch.delenv(factory.landing.TRAIN_RUN_ENV, raising=False)
    with factory.landing.run_lock(root) as held:
        assert held
        for kwargs in ({"run": True}, {"begin": ["1"], "by": "auto"}, {"eject": "2"},
                       {"stop": True}):  # fmt: skip
            code, out = _run(capsys, factory.landing.cmd_train, root, **kwargs)
            assert code == 1 and "train --run is under way" in out["refusals"][0], (kwargs, out)
        code, out = _run(capsys, factory.landing.cmd_train, root)
        assert code == 0 and out == {"under_way": True, "running": True}, out
        assert state.read_bytes() == before, "nothing written"
        monkeypatch.setenv(factory.landing.TRAIN_RUN_ENV, "held")
        code, out = _run(capsys, factory.landing.cmd_train, root)
        assert code == 0 and out["next"] == "commit" and "running" not in out, out
        code, out = _run(capsys, factory.landing.cmd_train, root, eject="2")
        assert "no fault" in out["refusals"][0], "past the lock, to its own check"
        code, out = _run(capsys, factory.landing.cmd_train, root, begin=["1"], by="auto")
        assert "a train is under way" in out["refusals"][0], "past the lock, to its own check"
        code, out = _run(capsys, factory.landing.cmd_train, root, stop=True)
        assert code == 0 and out["state"] == "stopped", out
    with factory.landing.run_lock(root) as held:
        assert held, "let go when its holder ended"


@needs_uv
def test_train_run_cancels_between_steps(tmp_path, capsys, monkeypatch) -> None:
    """147 R7: `--cancel` with no loop running refuses; a cancel asked while change two's review
    runs lets that step finish, then the loop exits `cancel`, removes the file and leaves the
    train under way; a rerun lands the batch."""
    root, trees = _three(tmp_path, check="true")
    code, out = _run(capsys, factory.landing.cmd_train, root, cancel=True)
    assert code == 1 and "no train --run is under way" in out["refusals"][0], out
    cancel = [sys.executable, str(SCRIPT), "train", "--cancel"]
    calls = fake_claude(tmp_path, monkeypatch, {
        f"{trees[1].name}:reviewer-behaviour": {"run": cancel},
    })  # fmt: skip
    _begin(root, capsys)
    code, out, _ = _loop(root, capsys)
    assert code == 1 and out["stopped"]["next"] == "cancel", out
    assert [c["change"] for c in calls()] == [trees[1].name], "the step in flight finished"
    assert not (_state_file(root).parent / factory.landing.TRAIN_CANCEL).exists()
    assert factory.read_train(root) is not None, "the train is still under way"
    assert not [s for s in _first_parent(root) if s.startswith("Close ")]
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    assert len(out["landed"]) == 3


@needs_uv
def test_train_run_makes_the_stored_fix_once(tmp_path, capsys, monkeypatch) -> None:
    """147 R9: `--begin … --fix 001=R1` stores the person's fix; the loop makes it once, as
    soon as change one sits in the stack (154): `land-fix --ask`, the builder, `land-fix
    --commit`, then the train stacks two on it, gates the tip once, and every reviewer at one's
    depth reads the fix."""
    root = _repo(tmp_path, check="true")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    (_folder(trees[0]) / "decisions.md").write_text(
        "# Decisions\n\n- [x] R1 (person, fix): say it louder\n", encoding="utf-8"
    )
    (_folder(trees[0]) / "runs").mkdir()  # the builder's session, as its build left it
    (_folder(trees[0]) / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    calls = fake_claude(tmp_path, monkeypatch, {
        f"{trees[0].name}:builder": {"write": {"aa.txt": "AA\n"}},
    })  # fmt: skip
    code, out = _run(
        capsys, factory.landing.cmd_train, root, begin=["1", "2"], by="auto", fix="1=R1"
    )
    assert code == 1 and "--by person" in out["refusals"][0], out
    code, out = _run(
        capsys, factory.landing.cmd_train, root, begin=["1", "2"], by="person", fix="1=R9"
    )
    assert code == 1 and "R9" in out["refusals"][0], out
    code, out = _run(
        capsys, factory.landing.cmd_train, root, begin=["1", "2"], by="person", fix="1=R1"
    )
    assert code == 0 and out["fix"] == {"change": trees[0].name, "ask": "R1"}, out
    code, out, err = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), (out, err)
    builders = [c for c in calls() if c["agent"] == "builder"]
    assert len(builders) == 1 and builders[0]["change"] == trees[0].name, "made once"
    own = _closes(root)
    assert _git(root, "show", f"{own[trees[0].name]}:aa.txt") == "AA"
    rel = f".sdlc/work/{trees[0].name}"
    assert _git(root, "show", f"{own[trees[0].name]}:{rel}/build/land-1.ask.md") == "say it louder"
    reviewed = {c["agent"] for c in calls() if c["change"] == trees[0].name}
    assert reviewed >= {f"reviewer-{r}" for r in factory.DEFAULTS["reviewers"]}, reviewed
    assert sum(ln.startswith(f"train: gate {trees[1].name}") for ln in err.splitlines()) == 1


# The builder's report that a landing fix was already made, for change `aa`.
ALREADY_MADE_REPLY = (
    "FIX: ALREADY MADE\n\naa.txt says it.\n\n## Evidence\n$ grep -c aa aa.txt\n1\nexit: 0\n"
)


def _fix_stored(tmp_path: Path, capsys) -> tuple[Path, list[Path]]:
    """Two changes, a train begun by the person with a fix stored for the first."""
    tmp_path.mkdir()
    root = _repo(tmp_path, check="true")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    (_folder(trees[0]) / "decisions.md").write_text(
        "# Decisions\n\n- [x] R1 (person, fix): say aa\n", encoding="utf-8"
    )
    (_folder(trees[0]) / "runs").mkdir()
    (_folder(trees[0]) / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    code, out = _run(
        capsys, factory.landing.cmd_train, root, begin=["1", "2"], by="person", fix="1=R1"
    )
    assert code == 0, out
    return root, trees


@needs_uv
def test_a_train_fix_already_made_goes_on_to_the_gate(tmp_path, capsys, monkeypatch) -> None:
    """181 R8: a stored fix the builder reports already made, with its evidence and no edit,
    goes on to the tip's gate and then the landing review at the run's full depth, with no stop:
    through the driver's steps, and through `train --run`."""

    def already(tree: Path) -> None:
        folder = _folder(tree)
        (folder / "build" / f"land-{factory.land_round(folder)}.md").write_text(ALREADY_MADE_REPLY)

    root, trees = _fix_stored(tmp_path / "driven", capsys)
    readings = drive_train(factory, root, capsys, fix=already)
    steps = [(r.get("next"), r.get("change")) for r in readings]
    one = trees[0].name
    after = steps[steps.index(("fix", one)) + 1 :]
    nexts = [s[0] for s in after]
    assert "gate" in nexts and nexts.index("gate") < after.index(("review", one)), "tip's gate"
    review = next(r for r in readings if (r.get("next"), r.get("change")) == ("review", one))
    assert set(review["verdict"]["missing"]) == set(factory.DEFAULTS["reviewers"]), review
    assert readings[-1]["next"] == "done" and "stop" not in [s[0] for s in steps], steps
    assert _git(root, "show", f"{_closes(root)[one]}:aa.txt") == "aa", "nothing edited"

    root, trees = _fix_stored(tmp_path / "run", capsys)
    calls = fake_claude(tmp_path / "run", monkeypatch, {
        f"{trees[0].name}:builder": {"reply": ALREADY_MADE_REPLY},
    })  # fmt: skip
    code, out, err = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), (out, err)
    assert len(out["landed"]) == 2 and out["ejected"] == [], out
    reviewed = {c["agent"] for c in calls() if c["change"] == trees[0].name}
    assert reviewed >= {f"reviewer-{r}" for r in factory.DEFAULTS["reviewers"]}, reviewed
    assert _git(root, "show", f"{_closes(root)[trees[0].name]}:aa.txt") == "aa"


@needs_uv
def test_a_fix_the_gate_needs_is_made_before_the_gate(tmp_path, capsys, monkeypatch) -> None:
    """154: a check that fails until change one's file says `AA`, and the person's fix that
    makes it so: the reading names `fix` for one as soon as it is stacked, before any gate, so
    the tip's first gate is green and both land, none ejected, the fix in one's own commit."""
    root = _repo(tmp_path, check="grep -qx AA aa.txt")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    (_folder(trees[0]) / "decisions.md").write_text(
        "# Decisions\n\n- [x] R1 (person, fix): make the gate green\n", encoding="utf-8"
    )
    (_folder(trees[0]) / "runs").mkdir()
    (_folder(trees[0]) / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    fake_claude(tmp_path, monkeypatch, {
        f"{trees[0].name}:builder": {"write": {"aa.txt": "AA\n"}},
    })  # fmt: skip
    code, out = _run(
        capsys, factory.landing.cmd_train, root, begin=["1", "2"], by="person", fix="1=R1"
    )
    assert code == 0, out
    steps = []
    while (out := _run(capsys, factory.landing.cmd_train, root)[1])["next"] in ("commit", "stack"):
        steps.append((out["next"], out["change"]))
        if out["next"] == "commit":
            code, said = _run(capsys, factory.landing.cmd_land, Path(out["worktree"]),
                              out["change"][:3], "person")  # fmt: skip
        else:
            code, said = _run(capsys, factory.landing.cmd_resolve, Path(out["worktree"]),
                              out["change"][:3], False, onto=out["onto"])  # fmt: skip
        assert code == 0, said
    assert (out["next"], out["change"]) == ("fix", trees[0].name), (steps, out)
    assert not factory.read_train(root)["gates"], "no gate before the fix"
    code, out, err = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), (out, err)
    assert out["ejected"] == [] and len(out["landed"]) == 2, out
    assert _git(root, "show", f"{_closes(root)[trees[0].name]}:aa.txt") == "AA"
    gates = [ln for ln in err.splitlines() if ln.startswith("train: gate ")]
    assert len(gates) == 1, gates


@needs_uv
def test_train_run_starts_a_rounds_reviewers_together(tmp_path, capsys, monkeypatch) -> None:
    """147 R10: a resolved conflict's landing round needs every reviewer at the run's depth; the
    loop starts their sessions together, so each starts before any ends."""
    root, trees = _conflicting(tmp_path)
    second = trees[1].name
    resolved = {"README.md": "first's one, and second's\ntwo\nthree\n"}
    plan = {f"{second}:resolver": {"write": resolved}}
    for role in factory.DEFAULTS["reviewers"]:
        plan[f"{second}:reviewer-{role}"] = {"sleep": 1}
    calls = fake_claude(tmp_path, monkeypatch, plan)
    _begin(root, capsys)
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    reviews = [c for c in calls() if c["change"] == second and c["agent"].startswith("reviewer-")]
    assert len(reviews) == len(factory.DEFAULTS["reviewers"]), reviews
    assert max(c["start"] for c in reviews) < min(c["end"] for c in reviews), "together"
    assert (root / "README.md").read_text(encoding="utf-8").startswith("first's one, and second's")


# How long a killed-loop test waits for its loop to reach the point it is killed at, in seconds:
# a bound on a hang, never a pause, since each poll ends the moment the marker file appears. The
# loop's startup takes a minute or more on a loaded machine; one bound for every kill test.
STARTED_WITHIN = 120


@needs_uv
@pytest.mark.skipif(not hasattr(os, "killpg"), reason="kills a process group")
def test_a_killed_train_run_resumes(tmp_path, capsys, monkeypatch) -> None:
    """147 R8: a loop killed while a stand-in reviewer blocks leaves state a second `train --run`
    resumes from: every change closed once, and no branch carries another change's commit."""
    root, trees = _three(tmp_path, check="true")
    flag = tmp_path / "blocked"
    fake_claude(tmp_path, monkeypatch, {
        f"{trees[1].name}:reviewer-behaviour": {"block": str(flag)},
    })  # fmt: skip
    _begin(root, capsys)
    loop = subprocess.Popen(
        [sys.executable, str(SCRIPT), "train", "--run"], cwd=root, start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    started = Path(str(flag) + ".started")
    deadline = time.monotonic() + STARTED_WITHIN
    while not started.exists() and loop.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert started.exists(), "the reviewer never started"
    os.killpg(loop.pid, signal.SIGKILL)
    loop.wait(30)
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    names = [t.name for t in trees]
    closes = [s for s in _first_parent(root) if s.startswith("Close ")]
    assert closes == [f"Close {n}" for n in reversed(names)], closes
    for name, own in _closes(root).items():
        touched = _git(root, "show", "--format=", "--name-only", own).splitlines()
        assert all(not p.startswith(".sdlc/work/") or p.startswith(f".sdlc/work/{name}/")
                   for p in touched), (name, touched)  # fmt: skip


# A host's `[commands] check` that blocks for good on its first call, writing `<flag>.started`,
# and passes once `<flag>` exists: a loop killed at its gate, with no shebang file to start.
BLOCKING_CHECK = """\
import pathlib, sys, time
flag = pathlib.Path(sys.argv[1])
if not flag.exists():
    pathlib.Path(sys.argv[1] + ".started").touch()
    while not flag.exists():
        time.sleep(0.1)
"""


def _killed_at_its_gate(tmp_path: Path, capsys, popen: dict, kill) -> None:
    """A `train --run` started with `popen`, killed by `kill(proc)` while the host's check blocks
    at the tip's gate, then run again: the second run gates afresh and ends `done`, each change
    closed once, and no `Close` commit carries another change's folder. The behaviour checks the
    stacked changes owe are written as the agent would reply, so no agent starts."""
    script, flag = tmp_path / "gate.py", tmp_path / "blocked"
    script.write_text(BLOCKING_CHECK, encoding="utf-8")
    py = Path(sys.executable).as_posix()
    root, trees = _three(tmp_path, check=f'"{py}" "{script.as_posix()}" "{flag.as_posix()}"')
    _begin(root, capsys)
    loop = subprocess.Popen(
        [sys.executable, str(SCRIPT), "train", "--run"], cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **popen,
    )  # fmt: skip
    started = Path(str(flag) + ".started")
    deadline = time.monotonic() + STARTED_WITHIN
    while not started.exists() and loop.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert started.exists(), f"the gate never started (exit {loop.poll()})"
    kill(loop)
    loop.wait(30)
    flag.touch()
    for tree in trees:
        for land in (_folder(tree) / "reviews").glob("land-*"):
            (land / "behaviour.md").write_text(verdict(factory, "behaviour"), encoding="utf-8")
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    names = [t.name for t in trees]
    closes = [s for s in _first_parent(root) if s.startswith("Close ")]
    assert closes == [f"Close {n}" for n in reversed(names)], closes
    for name, own in _closes(root).items():
        touched = _git(root, "show", "--format=", "--name-only", own).splitlines()
        assert all(not p.startswith(".sdlc/work/") or p.startswith(f".sdlc/work/{name}/")
                   for p in touched), (name, touched)  # fmt: skip


@needs_uv
@pytest.mark.skipif(not hasattr(os, "killpg"), reason="kills a process group")
def test_a_train_run_killed_at_its_gate_resumes(tmp_path, capsys) -> None:
    """171 R17's body on POSIX, so the Windows test's path through the gate is shown here too: a
    loop killed with its process group while the host's check blocks resumes."""
    _killed_at_its_gate(
        tmp_path, capsys, {"start_new_session": True},
        lambda proc: os.killpg(proc.pid, signal.SIGKILL),
    )  # fmt: skip


@needs_uv
@pytest.mark.portable
@pytest.mark.skipif(os.name != "nt", reason="kills a process tree with taskkill, on Windows")
def test_a_killed_train_run_resumes_on_windows(tmp_path, capsys) -> None:
    """171 R17 (idea 2026-11-18-67): `train --run` in a process group of its own, killed with its
    whole tree by `taskkill /T /F` while the host's check blocks at the gate, leaves state a
    second run resumes from. It blocks at the gate, not at an agent: the fake `claude` is a
    shebang file Windows can't start."""

    def kill(proc: subprocess.Popen) -> None:
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True, encoding="utf-8", errors="replace",
        )  # fmt: skip

    _killed_at_its_gate(
        tmp_path, capsys, {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}, kill
    )


# ------------------------------------------------------- an ejection leaves a durable record (174)


@needs_uv
def test_an_ejection_is_recorded_and_amended_in(tmp_path, capsys) -> None:
    """174 R4: `--eject` and `--stop` each append one row to `runs/ejections.jsonl` in each change
    they put back, its landing round and cause, amended into the change's commit; no row of
    `costs.jsonl` is rewritten."""
    (tmp_path / "eject").mkdir()
    root, trees = _three(tmp_path / "eject", check="test ! -f bb.txt")
    tree = trees[1]
    rel = f".sdlc/work/{tree.name}"
    costs = '{"session": "s-1", "role": "builder", "cost_usd": 0.5, "purpose": "build"}\n'
    (_folder(tree) / "runs").mkdir(exist_ok=True)
    (_folder(tree) / "runs" / "costs.jsonl").write_text(costs, encoding="utf-8")  # land commits it
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys)
    assert [e["change"] for e in readings[-1]["ejected"]] == [tree.name]
    assert _git(tree, "status", "--porcelain") == "", "the record is in its commit"
    shown = _git(tree, "show", f"HEAD:{rel}/runs/ejections.jsonl")
    rows = [json.loads(x) for x in shown.splitlines()]
    assert [(r["land"], r["cause"]) for r in rows] == [(1, "gate")], rows
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", rows[0]["at"]), rows
    assert _git(tree, "show", f"HEAD:{rel}/runs/costs.jsonl") + "\n" == costs, "never rewritten"

    (tmp_path / "stop").mkdir()
    root, trees = _three(tmp_path / "stop")
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o["next"] == "close")
    moved = [n for n, c in readings[-1]["changes"].items() if c.get("pre")]
    assert moved, readings[-1]
    code, out = _run(capsys, factory.landing.cmd_train, root, stop=True)
    assert code == 0 and out["state"] == "stopped", out
    for tree in trees:
        rel = f".sdlc/work/{tree.name}"
        found = subprocess.run(
            ["git", "-C", str(tree), "show", f"HEAD:{rel}/runs/ejections.jsonl"],
            capture_output=True, encoding="utf-8",
        ).stdout  # fmt: skip
        if tree.name not in moved:
            assert not found, "a change the train never moved has nothing to record"
            continue
        rows = [json.loads(x) for x in found.splitlines()]
        # Nit 2026-11-19-38: a stop's row has the eject's keys, its time and the landing round
        # the change had reached, which its commit still holds.
        land = factory.land_round(_folder(tree))
        assert [(r["land"], r["cause"]) for r in rows] == [(land, "stop")], (tree.name, rows)
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", rows[0]["at"]), rows


@pytest.mark.portable
def test_the_cores_train_gate_copy_reads_every_gate_line() -> None:
    """175 R10: `factory_records.TRAIN_GATE_RE` reads each `GATE:` line `train_record()` writes, a
    red prefix of two and a green tip, and the record's path is `factory.LAND_TRAIN`."""
    state = {"order": ["001-a", "002-b"], "base": "main", "changes": {"001-a": {}, "002-b": {}}}
    gates = [
        {"prefix": 2, "verdict": "FAIL", "commit": "ab" * 20, "file": "002-b/build/land-1.gate.md"},
        {"prefix": 1, "verdict": "PASS", "commit": "cd" * 20, "file": "001-a/build/land-1.gate.md"},
    ]
    text = factory.landing.train_record(state, "002-b", gates)
    lines = [ln for ln in text.splitlines() if ln.startswith("GATE: ")]
    read = [sdlc.factory_records.TRAIN_GATE_RE.match(ln) for ln in lines]
    assert len(lines) == 2 and all(read), lines
    assert [m.groups() for m in read] == [
        ("2", "FAIL", "ab" * 6, "002-b/build/land-1.gate.md"),
        ("1", "PASS", "cd" * 6, "001-a/build/land-1.gate.md"),
    ]
    assert not sdlc.factory_records.TRAIN_GATE_RE.match(text.splitlines()[4]), "TIP GATE: isn't"
    assert sdlc.factory_records.LAND_TRAIN == factory.LAND_TRAIN
    assert not hasattr(factory.landing, "LAND_TRAIN"), "one name, factory.py's"


# ------------------------------------------------- an ejection's row names its train (180 R4, R5)


@needs_uv
def test_a_stopped_trains_rows_name_it(tmp_path, capsys) -> None:
    """180 R4: a stopped train leaves a `stop` row in each committed change's commit, each naming
    the train by its `began`, 174's three keys first and `train` last."""
    root, trees = _three(tmp_path)
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o["next"] == "close")
    moved = [n for n, c in readings[-1]["changes"].items() if c.get("pre")]
    assert len(moved) >= 2, readings[-1]
    began = factory.read_train(root)["began"]
    code, out = _run(capsys, factory.landing.cmd_train, root, stop=True)
    assert code == 0 and out["state"] == "stopped" and out["problems"] == [], out
    for tree in (t for t in trees if t.name in moved):
        shown = _git(tree, "show", f"HEAD:.sdlc/work/{tree.name}/runs/ejections.jsonl")
        rows = [json.loads(x) for x in shown.splitlines()]
        assert [(r["cause"], r["train"]) for r in rows] == [("stop", began)], rows
        assert list(rows[0]) == ["at", "land", "cause", "train"], rows


@needs_uv
def test_an_ejection_that_cant_be_recorded_still_ejects(tmp_path, capsys) -> None:
    """180 R5: when the row can't be appended (`OSError`, here a directory where the file goes),
    the change is ejected all the same, its undo printed and the train's state written, and the
    failure is a problem naming the file."""
    root, trees = _three(tmp_path, check="test ! -f bb.txt")
    tree = trees[1]
    (_folder(tree) / "runs" / "ejections.jsonl").mkdir(parents=True)
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys)
    assert [e["change"] for e in readings[-1]["ejected"]] == [tree.name]
    [did] = [r["did"] for r in readings if r.get("next") == "eject"]
    assert did["state"] == "ejected" and did["undo"], did
    assert [p for p in did["problems"] if "runs/ejections.jsonl" in p], did


@needs_uv
def test_a_stop_that_cant_be_recorded_still_stops(tmp_path, capsys) -> None:
    """Nit 2026-11-19-55, 180 R5: the stop's half of it. When a change's row can't be appended,
    the train stops all the same, that change put back, and the failure is a problem naming the
    change and the file."""
    root, trees = _three(tmp_path)
    tree = trees[0]
    (_folder(tree) / "runs" / "ejections.jsonl").mkdir(parents=True)
    _begin(root, capsys)
    readings = drive_train(factory, root, capsys, until=lambda o: o["next"] == "close")
    assert readings[-1]["changes"][tree.name].get("pre"), readings[-1]
    code, out = _run(capsys, factory.landing.cmd_train, root, stop=True)
    assert code == 0 and out["state"] == "stopped", out
    assert tree.name in [p["change"] for p in out["put_back"]], out
    assert [p for p in out["problems"] if p.startswith(f"{tree.name}: ")
            and "runs/ejections.jsonl" in p], out  # fmt: skip
    assert factory.read_train(root) is None or factory.read_train(root)["state"] == "stopped"


@needs_uv
def test_a_stop_before_any_change_moved_leaves_no_row(tmp_path, capsys) -> None:
    """Nit 2026-11-19-57, 180's edge case: a train stopped before it stacked anything moved no
    branch, so each change has no undo and no row to count."""
    root, trees = _three(tmp_path)
    _begin(root, capsys)
    code, out = _run(capsys, factory.landing.cmd_train, root, stop=True)
    assert code == 0 and out["state"] == "stopped" and out["problems"] == [], out
    assert [p["undo"] for p in out["put_back"]] == [None, None, None], out
    for tree in trees:
        assert not (_folder(tree) / "runs" / "ejections.jsonl").exists(), tree.name


# ------------------------------------------------- acceptance checks as stacked (185 R1–R10)


READ_ONLY_PASSES = [
    "grep -q keep README.md",
    "test -f README.md && test ! -f gone.txt",
    "[ -f README.md ]",
    "cat README.md | wc -l",
    "head -n 2 README.md; tail -n 1 README.md",
    "true || false",
    "grep -rn 'a > b $x `y` (z)' src",
    "grep -rn -e keep src",
    'grep -c "keep" README.md',
    "git log --oneline -3",
    "git show HEAD:README.md",
    "git diff --stat HEAD~1 -- src",
    "git log --format=%H -1",
    "grep -r --directories=skip keep src",
    "grep -r --de keep src",
    "test -f README.md\ngrep -q one README.md",
]

READ_ONLY_REFUSALS = [
    ("cat README.md > out.txt", ">"),
    ("grep x < README.md", "<"),
    ("cat `ls`", "`"),
    ("cat $HOME/x", "$"),
    ('grep "$(id)" README.md', "$"),
    ("cat README\\.md", "\\"),
    ("true & false", "&"),
    ("(cat README.md)", "("),
    ("{ cat README.md; }", "{"),
    ("cat *.md", "*"),
    ("cat README.m?", "?"),
    ("cat [R]EADME.md", "["),
    ("rm -rf x", "rm"),
    ("sed -n 1p README.md", "sed"),
    ("awk '{print}' README.md", "awk"),
    ("/bin/cat README.md", "/bin/cat"),
    ("FOO=1 cat README.md", "FOO=1"),
    ("git status", "git status"),
    ("git -C . log", "git -C"),
    ("git push", "git push"),
    ("git diff --output=x.txt", "--output"),
    ("git diff --ext-diff", "--ext-diff"),
    ("git log -p --textconv", "--textconv"),
    ("cat /etc/passwd", "/etc/passwd"),
    ("cat ~/.ssh/id_rsa", "~/.ssh/id_rsa"),
    ("cat src/../../x", ".."),
    ("grep --file=/etc/passwd x", "/etc/passwd"),
    ("grep -f/etc/passwd x", "/etc/passwd"),
    ("cat out-link/secret", "out-link/secret"),
    ("grep -R keep .", "-R"),
    ("grep -rnS keep .", "-rnS"),
    ("grep -O -r keep .", "-O"),
    ("grep --dereference-recursive keep .", "--dereference-recursive"),
    ("grep --der keep .", "--der"),
    ("grep -n --dereference keep .", "--dereference"),
    ("grep --dereference-recursive=x keep .", "--dereference-recursive=x"),
    ("cat 'unclosed", "quote"),
    ("cat README.md &&", "empty"),
]


@pytest.mark.portable
@pytest.mark.parametrize("command", READ_ONLY_PASSES)
def test_read_only_command_passes(tmp_path, command) -> None:
    """185 R5: each command only reads inside the checkout, with the listed programs alone."""
    (tmp_path / "README.md").write_text("one\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    assert factory.landing.read_only_command(command, tmp_path) is None, command


@pytest.mark.portable
@pytest.mark.parametrize("command, named", READ_ONLY_REFUSALS)
def test_read_only_command(tmp_path, command, named) -> None:
    """185 R5: each rule refuses its case, saying why, the offending text named."""
    (tmp_path / "checkout").mkdir()
    checkout = tmp_path / "checkout"
    (checkout / "README.md").write_text("one\n", encoding="utf-8")
    (checkout / "src").mkdir()
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "secret").write_text("s\n", encoding="utf-8")
    if command.startswith("cat out-link"):
        if not hasattr(os, "symlink"):
            pytest.skip("no symlinks here")
        try:
            (checkout / "out-link").symlink_to(tmp_path / "outside", target_is_directory=True)
        except OSError:
            pytest.skip("this account can't make a symlink")
    why = factory.landing.read_only_command(command, checkout)
    assert why is not None and named in why, (command, why)


CHECKS_HEAD = "# Checks\n\n> Acceptance checks.\n"


def _checks(tree: Path, *checks: tuple[str, str]) -> Path:
    """Write the change's `checks.md`, one `## ` check per (name, command)."""
    body = "".join(f"\n## {name}\n\n```sh\n{command}\n```\n" for name, command in checks)
    path = _folder(tree) / "checks.md"
    path.write_text(CHECKS_HEAD + body, encoding="utf-8", newline="\n")
    return path


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _to_the_stack(root: Path, capsys, trees: list[Path], by: str = "person") -> None:
    """Begin a train over `trees` and drive it, in process, through each change's commit (its
    checks run first, as the land skill's Step 3 does): up to its first `stack`."""
    drive_train(factory, root, capsys, trees, by, until=lambda o: o.get("next") == "stack")


@needs_uv
def test_begin_records_each_changes_approved_checks(tmp_path, capsys) -> None:
    """185 R1: `--begin` records each change's `checks_sha` (its `checks.md`'s sha256, or null
    with none) and its `checks`, each name and command as `sdlc.py preflight` gives them."""
    root = _repo(tmp_path, check="true")
    checked = _ready(root, "checked", {"checked.txt": "checked\n"})
    plain = _ready(root, "plain", {"plain.txt": "plain\n"})
    path = _checks(
        checked, ("Its file", "test -f checked.txt"), ("Says it", "grep -q c checked.txt")
    )
    _begin(root, capsys, "person")
    state = json.loads(_state_file(root).read_text(encoding="utf-8"))
    mine, other = state["changes"][checked.name], state["changes"][plain.name]
    assert mine["checks_sha"] == _sha(path), mine
    assert mine["checks"] == [{"name": "Its file", "command": "test -f checked.txt"},
                              {"name": "Says it", "command": "grep -q c checked.txt"}]  # fmt: skip
    assert other["checks_sha"] is None and other["checks"] == [], other


@needs_uv
def test_unchanged_checks_run_as_stacked_without_a_stop(tmp_path, capsys, monkeypatch) -> None:
    """185 R2: two changes with checks, stacked over a base that moved: each reading names
    `accept` cleared `as approved`, and the loop runs it itself, to `done`; each landed commit's
    `build/land-accept.md` holds a second attempt, on its stacked commit."""
    root = _repo(tmp_path, check="true")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    for tree in trees:
        _checks(tree, ("Its file", f"test -f {tree.name.split('-', 1)[1]}.txt"))
    _move(root, 1)
    fake_claude(tmp_path, monkeypatch)
    _to_the_stack(root, capsys, trees)
    readings: list[dict] = []
    real = factory.landing._run_plan

    def plan(main: Path, reading: dict):
        readings.append(reading)
        return real(main, reading)

    monkeypatch.setattr(factory.landing, "_run_plan", plan)
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    assert out["landed"] == [t.name for t in trees], out
    accepts = [r for r in readings if r["next"] == "accept"]
    assert [r["change"] for r in accepts] == [t.name for t in trees], readings
    assert all(r["checks"] == {"clear": True, "why": "as approved"} for r in accepts), accepts
    for tree in trees:
        own = _closes(root)[tree.name]
        record = _git(root, "show", f"{own}:.sdlc/work/{tree.name}/build/land-accept.md")
        builds = re.findall(r"^Build: (\w+)$", record, re.M)
        assert record.startswith("ACCEPT: PASS") and len(builds) == 2, record
        assert builds[0] != builds[1], "run again on the stacked commit"


@needs_uv
def test_checks_failing_as_stacked_pause_as_a_review_ejection(tmp_path, capsys, monkeypatch):
    """185 R3: a check that passes alone and fails once stacked: the loop runs it, reads the train
    again, and stops at the reading's ejection with cause `review`, which pauses; never a failed
    command's stop, and the loop ejects nothing itself."""
    root, trees = _three(tmp_path, check="true")
    _checks(trees[1], ("No aa.txt", "test ! -f aa.txt"))
    fake_claude(tmp_path, monkeypatch)
    _to_the_stack(root, capsys, trees)
    code, out, _ = _loop(root, capsys)
    assert code == 1, out
    stopped = out["stopped"]
    assert (stopped["next"], stopped["change"], stopped["cause"]) == (
        "eject", trees[1].name, "review"), stopped  # fmt: skip
    assert "acceptance checks failed" in stopped["reason"], stopped
    assert not stopped["way_on"].startswith("fix what it says"), stopped
    assert out["ejected"] == [] and out["undos"] == [], "the loop ejected nothing"
    record = (_folder(trees[1]) / "build" / "land-accept.md").read_text(encoding="utf-8")
    assert record.startswith("ACCEPT: FAIL") and record.count("## Attempt") == 2, record


@needs_uv
def test_a_changed_check_off_the_list_stops_before_the_approver(tmp_path, capsys, monkeypatch):
    """185 R4: a check edited after the yes to run what the read-only list refuses stops the loop
    at `accept`, saying `checks.md` changed and naming the command and why; no approver runs,
    and no check runs."""
    root = _repo(tmp_path, check="true")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    _checks(trees[1], ("Its file", "test -f bb.txt"))
    calls = fake_claude(tmp_path, monkeypatch)
    _to_the_stack(root, capsys, trees)
    _checks(trees[1], ("Its file", "test -f bb.txt"), ("Tidy", "rm -f bb.txt"))
    code, out, _ = _loop(root, capsys)
    assert code == 1 and out["stopped"]["next"] == "accept", out
    reason = out["stopped"]["reason"]
    assert "checks.md changed since the yes" in reason and "rm -f bb.txt" in reason, reason
    assert "`rm` isn't a read-only program" in reason, reason
    assert "approver" not in {c["agent"] for c in calls()}, calls()
    record = (_folder(trees[1]) / "build" / "land-accept.md").read_text(encoding="utf-8")
    assert record.count("## Attempt") == 1, "only the run before the commit"


APPROVED = [{"name": "Its file", "command": "test -f bb.txt"}]


def _judging(tmp_path: Path, monkeypatch, current: list[dict]) -> tuple[Path, Path, dict]:
    """A change in a landing round whose `checks.md` changed since the yes to hold `current`,
    which `sdlc.py preflight` is stood in for to give; its train entry approved `APPROVED`."""
    tree = tmp_path / "002-bb"
    folder = tree / ".sdlc" / "work" / "002-bb"
    (folder / "reviews" / "land-1").mkdir(parents=True)
    (tree / "bb.txt").write_text("bb\n", encoding="utf-8")
    _checks(tree, *((c["name"], c["command"]) for c in current))
    monkeypatch.setattr(factory.landing, "_preflight",
                        lambda folder, tree: ({"checks": {"checks": current}}, ""))  # fmt: skip
    return tree, folder, {"checks_sha": "0" * 64, "checks": APPROVED}


def _judged(folder: Path, reply: str, sha: str | None = None) -> None:
    sha = sha or factory.landing.checks_sha(folder)
    path = factory.land_checks_path(folder, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"Judged: {sha[:16]}\n\n{reply}", encoding="utf-8")


@pytest.mark.portable
@pytest.mark.parametrize(
    "reply, clear, step, said",
    [
        ("CHECKS: HARMLESS\n\nIt only greps.\n", True, "accept", "judged harmless"),
        ("CHECKS: ESCALATE\n\nIt reads .env, a secret.\n", False, "accept", "reads .env"),
        ("It looks fine to me.\n", False, "accept", "holds no CHECKS: HARMLESS"),
        ("CHECKS: HARMLESS\nCHECKS: ESCALATE\n", False, "accept", "holds no CHECKS: HARMLESS"),
        ("Hm.\nCHECKS: HARMLESS\nCHECKS: ESCALATE\n", False, "accept", "holds no CHECKS"),
        (None, False, "checks", "the approver judges what changed"),
        ("stale", False, "checks", "the approver judges what changed"),
    ],
    ids=["harmless", "escalate", "unreadable", "disagreeing", "preamble", "missing", "stale"],
)
def test_the_approvers_answer_decides_a_changed_check(
    tmp_path, monkeypatch, reply, clear, step, said
) -> None:
    """185 R6, R7: a changed check the read-only list passes goes to the approver (`checks`)
    while no record judges the file as it stands, missing or stale; a current record clears it
    only when it opens `CHECKS: HARMLESS` with no `CHECKS:` line that disagrees; anything else
    stops at `accept`, saying why."""
    current = [*APPROVED, {"name": "Says it", "command": "grep -q bb bb.txt"}]
    tree, folder, mine = _judging(tmp_path, monkeypatch, current)
    if reply == "stale":
        _judged(folder, "CHECKS: HARMLESS\n", sha="f" * 64)
    elif reply is not None:
        _judged(folder, reply)
    found = factory.landing.checks_clearance(tree, folder, mine)
    assert (found["clear"], found["step"]) == (clear, step), found
    assert said in found["why"] and "checks.md changed since the yes" in found["why"], found
    assert found["changed"] == [current[1]] and found["off_list"] == [], found


@pytest.mark.portable
def test_harmless_never_clears_a_command_off_the_list(tmp_path, monkeypatch) -> None:
    """185 R8: a current `CHECKS: HARMLESS` record, written by hand, for a file holding a command
    the read-only list refuses: not clear, named, and the loop plans no `accept` for it."""
    current = [*APPROVED, {"name": "Tidy", "command": "rm -rf x"}]
    tree, folder, mine = _judging(tmp_path, monkeypatch, current)
    _judged(folder, "CHECKS: HARMLESS\n\nFine.\n")
    found = factory.landing.checks_clearance(tree, folder, mine)
    assert (found["clear"], found["step"]) == (False, "accept"), found
    assert "rm -rf x" in found["why"] and "isn't read-only" in found["why"], found
    state = {"order": ["002-bb"], "changes": {"002-bb": mine}}
    monkeypatch.setattr(factory, "read_train", lambda root: state)
    reading = _step("accept", worktree=str(tree), checks={"clear": True, "why": "as approved"})
    groups, stopped = factory.landing._run_plan(tmp_path, reading)
    assert groups is None and "rm -rf x" in stopped["reason"], stopped


@needs_uv
def test_the_loop_rechecks_before_it_runs_accept(tmp_path, capsys) -> None:
    """185 R9: a reading names `accept` cleared as approved; `checks.md` is edited before the loop
    plans the step: `_run_plan()` reads it again and stops, planning no `accept`. Unedited, it
    plans `accept`."""
    root = _repo(tmp_path, check="true")
    tree = _ready(root, "bb", {"bb.txt": "bb\n"})
    _checks(tree, ("Its file", "test -f bb.txt"))
    _move(root, 1)
    readings = drive_train(factory, root, capsys, [tree], "person",
                           until=lambda o: o.get("next") == "accept")  # fmt: skip
    reading = readings[-1]
    assert reading["checks"] == {"clear": True, "why": "as approved"}, reading
    groups, stopped = factory.landing._run_plan(root, reading)
    assert stopped is None and groups == [[(["accept", tree.name], tree)]], groups
    _checks(tree, ("Its file", "test -f bb.txt"), ("Tidy", "rm -f bb.txt"))
    groups, stopped = factory.landing._run_plan(root, reading)
    assert groups is None and stopped["next"] == "accept", stopped
    assert "checks.md changed since the yes" in stopped["reason"], stopped
    assert "rm -f bb.txt" in stopped["reason"], stopped
    # Nit 2026-11-19-73: an edit the read-only list passes still loses the yes's clearance, and
    # with no approver's judgement of the file as it stands the loop plans no `accept` either.
    _checks(tree, ("Its file", "test -f bb.txt"), ("Says it", "grep -q bb bb.txt"))
    groups, stopped = factory.landing._run_plan(root, reading)
    assert groups is None and stopped["next"] == "accept", stopped
    assert "checks.md changed since the yes" in stopped["reason"], stopped
    assert "the approver judges what changed" in stopped["reason"], stopped


@needs_uv
def test_changed_read_only_checks_go_to_the_approver(tmp_path, capsys, monkeypatch) -> None:
    """185 R6: a check added after the yes that the read-only list passes: the loop runs the
    approver (`agent --task land-checks`), told the approved, current and changed checks; its
    reply is filed in `build/land-1.checks.md` under `Judged: <sha16>`; HARMLESS, the loop runs
    the checks itself and lands it."""
    root = _repo(tmp_path, check="true")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    _checks(trees[1], ("Its file", "test -f bb.txt"))
    calls = fake_claude(tmp_path, monkeypatch, {
        "approver": {"reply": "CHECKS: HARMLESS\n\nThe new check only greps bb.txt.\n"},
    })  # fmt: skip
    _to_the_stack(root, capsys, trees)
    path = _checks(trees[1], ("Its file", "test -f bb.txt"), ("Says it", "grep -q bb bb.txt"))
    judged = _sha(path)[:16]
    code, out, _ = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    [asked_] = [c for c in calls() if c["agent"] == "approver"]
    assert asked_["change"] == trees[1].name, asked_
    assert 'Says it: "grep -q bb bb.txt"' in asked_["prompt"], asked_["prompt"]
    assert 'Its file: "test -f bb.txt"' in asked_["prompt"], asked_["prompt"]
    own = _closes(root)[trees[1].name]
    rel = f".sdlc/work/{trees[1].name}/build"
    record = _git(root, "show", f"{own}:{rel}/land-1.checks.md")
    assert record.startswith(f"Judged: {judged}\n\nCHECKS: HARMLESS"), record
    accept = _git(root, "show", f"{own}:{rel}/land-accept.md")
    assert accept.startswith("ACCEPT: PASS") and accept.count("## Attempt") == 2, accept
    assert "Says it: exit 0, passed" in accept, accept


@needs_uv
def test_land_checks_refuses_outside_a_changed_train_change(tmp_path, capsys, monkeypatch):
    """185 R6: `agent --task land-checks` refuses a change no live train names, and one whose
    `checks.md` still hashes to what the yes covered; no session starts."""
    root = _repo(tmp_path, check="true")
    tree = _ready(root, "bb", {"bb.txt": "bb\n"})
    _checks(tree, ("Its file", "test -f bb.txt"))
    calls = fake_claude(tmp_path, monkeypatch)
    (_folder(tree) / "reviews" / "land-1").mkdir(parents=True)
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-checks", None, None)
    assert code == 1 and "no train under way names" in out["refusals"][0], out
    (_folder(tree) / "reviews" / "land-1").rmdir()
    _move(root, 1)
    drive_train(factory, root, capsys, [tree], "person", until=lambda o: o.get("next") == "accept")
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-checks", None, None)
    assert code == 1 and "as approved" in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-checks", "code", None)
    assert code == 1 and "runs the approver" in out["refusals"][0], out
    (_folder(tree) / "checks.md").unlink()  # removed after the yes: nothing left to judge
    code, out = _run(capsys, factory.cmd_agent, tree, "001", "land-checks", None, None)
    assert code == 1 and "checks.md is gone" in out["refusals"][0], out
    assert calls() == [], "no session started"
    assert not factory.land_checks_path(_folder(tree), 1).exists()


# ------------------------------------------------------------- commands.build (185 R10–R16)


def _build_repo(tmp_path: Path, build: str | None = "true", when: str | None = None,
                sensitive: list[str] | None = None, check: str = "true") -> Path:  # fmt: skip
    """A scratch host whose base branch names `check`, and `build` and `build_when` when given,
    and `[review] sensitive` when given."""
    root = _repo(tmp_path, check=check)
    lines = [f"[commands]\ncheck = {json.dumps(check)}\n"]
    if build is not None:
        lines.append(f"build = {json.dumps(build)}\n")
    if when is not None:
        lines.append(f"build_when = {json.dumps(when)}\n")
    if sensitive is not None:
        lines.append(f"\n[review]\nsensitive = {json.dumps(sensitive)}\n")
    (root / ".sdlc" / "config.toml").write_text("".join(lines), encoding="utf-8")
    _git(root, "commit", "-q", "--allow-empty", "-am", "the base's commands")
    return root


@needs_uv
def test_gate_build_runs_the_bases_build_and_records_it(tmp_path, capsys) -> None:
    """185 R11: `gate --land --build` runs the base branch's `[commands] build`, never the
    checkout's, in a gate slot, and adds the attempt to `build/land-<n>.build.md`, first line
    `BUILD: <verdict>`, in the gate file's shape."""
    root = _build_repo(tmp_path, build="echo base-built")
    tree = _ready(root, "bb", {"bb.txt": "bb\n"})
    config = tree / ".sdlc" / "config.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(
        "echo base-built", "touch checkout-ran"), encoding="utf-8")  # fmt: skip
    (_folder(tree) / "reviews" / "land-1").mkdir(parents=True)
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True, build=True)
    assert (code, out["verdict"]) == (0, "PASS"), out
    assert out["to"] == f".sdlc/work/{tree.name}/build/land-1.build.md", out
    assert not (tree / "checkout-ran").exists(), "the checkout's build never runs"
    path = factory.land_build_path(_folder(tree), 1)
    text = path.read_text(encoding="utf-8")
    assert text.startswith("BUILD: PASS\n") and "Command: echo base-built" in text, text
    assert "base-built" in text.split("output:", 1)[1], text
    record = factory.read_gate_file(path)
    assert [a["verdict"] for a in record["attempts"]] == ["PASS"], record
    assert not factory.land_gate_path(_folder(tree), 1).exists(), "the gate's record is its own"


@needs_uv
def test_gate_build_refuses_without_a_build(tmp_path, capsys) -> None:
    """185 R11: with no `[commands] build` on the base branch, `gate --land --build` refuses and
    writes no record; `--build` without `--land` refuses too."""
    root = _build_repo(tmp_path, build=None)
    tree = _ready(root, "bb", {"bb.txt": "bb\n"})
    (_folder(tree) / "reviews" / "land-1").mkdir(parents=True)
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True, build=True)
    assert code == 1 and "[commands] build" in out["refusals"][0], out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", False, build=True)
    assert code == 1 and "--land" in out["refusals"][0], out
    assert not list((_folder(tree) / "build").glob("land-*")), "no record on a refusal"


@needs_uv
@pytest.mark.parametrize(
    "build, when, sensitive, edited, due",
    [
        (None, None, None, "src/a.py", False),
        ("true", None, None, "docs/a.md", True),
        ("true", "^src/", None, "src/a.py", True),
        ("true", "^src/", None, "docs/a.md", False),
        ("true", "^src/", ["docs/"], "docs/a.md", True),
        ("true", "([", None, "docs/a.md", True),
    ],
    ids=["no-build", "when-unset", "when-matches", "when-misses", "sensitive", "bad-regex"],
)
def test_which_changes_call_for_the_build(tmp_path, build, when, sensitive, edited, due) -> None:
    """185 R12: a change calls for the build when the base branch sets it and `build_when` is
    unset, matches a path in its diff, or isn't a valid regex, or a path in its diff is on the
    base branch's `[review] sensitive`; never when the base sets no build."""
    root = _build_repo(tmp_path, build=build, when=when, sensitive=sensitive)
    tree = _ready(root, "bb", {edited: "bb\n"})
    assert factory.landing.build_due(tree, "main") is due


@needs_uv
def test_a_train_of_one_runs_the_build_before_it_lands(tmp_path, capsys, monkeypatch) -> None:
    """185 R13: a train of one that never moved, whose change calls for the build: the train
    names `build` at its tip, the loop runs it, and its commit holds `build/land-1.build.md`."""
    root = _build_repo(tmp_path, build="true", when=".")
    tree = _ready(root, "bb", {"bb.txt": "bb\n"})
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, err = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    assert f"train: build {tree.name}" in err, err
    own = _closes(root)[tree.name]
    record = _git(root, "show", f"{own}:.sdlc/work/{tree.name}/build/land-1.build.md")
    assert record.startswith("BUILD: PASS"), record


@needs_uv
def test_a_red_build_stops_the_train(tmp_path, capsys, monkeypatch) -> None:
    """185 R14: a red build at the tip stops the train, naming the exit and the record's file;
    never bisected, and the loop ejects nothing."""
    root = _build_repo(tmp_path, build="false", when=".")
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, err = _loop(root, capsys)
    assert code == 1 and out["stopped"]["next"] == "stop", out
    reason = out["stopped"]["reason"]
    assert "exit 1" in reason and f"{trees[1].name}/build/land-1.build.md" in reason, reason
    assert out["ejected"] == [] and out["undos"] == [] and "eject" not in err, out
    assert err.count("train: build") == 1, "run once, at the tip, never bisected"
    assert not (_folder(trees[0]) / "build" / "land-1.build.md").exists()


@needs_uv
@pytest.mark.parametrize("build, when", [(None, None), ("true", "^nothing/")],
                         ids=["no-build", "none-calls"])  # fmt: skip
def test_no_build_runs_unless_a_change_calls_for_it(tmp_path, capsys, monkeypatch, build, when):
    """185 R15: with no `commands.build`, or none of the train's changes calling for it, no build
    is planned and no `.build.md` is written."""
    root = _build_repo(tmp_path, build=build, when=when)
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb")]
    fake_claude(tmp_path, monkeypatch)
    _begin(root, capsys)
    code, out, err = _loop(root, capsys)
    assert (code, out.get("done")) == (0, True), out
    assert "train: build" not in err, err
    for tree in trees:
        listed = _git(root, "ls-tree", "-r", "--name-only", _closes(root)[tree.name])
        assert ".build.md" not in listed, listed


@needs_uv
def test_a_build_rounds_gate_never_runs_the_build(tmp_path, capsys) -> None:
    """185 R16: a build round's gate runs `[commands] check` alone; a red build changes nothing."""
    root = _build_repo(tmp_path, build="false", when=".")
    tree = _ready(root, "bb", {"bb.txt": "bb\n"})
    code, out = _run(capsys, factory.cmd_gate, tree, "001")
    assert (code, out["verdict"]) == (0, "PASS"), out
    assert out["to"].endswith("build/round-1.gate.md"), out
