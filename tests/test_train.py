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
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

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
        with sdlc._main_lock(root):
            done.set()

    with sdlc._main_lock(root):
        with sdlc._main_lock(root):
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
    real = sdlc.measure_change

    def pausing(main, branch, cfg):
        paused.set()  # just after the merge, before the Close commit
        assert go.wait(10)
        return real(main, branch, cfg)

    monkeypatch.setattr(sdlc, "measure_change", pausing)
    results: dict = {}

    def closing() -> None:
        results["close"] = sdlc.cmd_close(root, "001")

    filed = threading.Event()

    def filing() -> None:
        with sdlc._main_lock(root):
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
    code, out = _run(capsys, sdlc.cmd_close, root, "002")
    assert code == 1, out
    assert any(a.name in r and "another change" in r for r in out["refusals"]), out["refusals"]
    assert out["done"] == [] and _git(root, "rev-parse", "main") == before
    assert b_tree.exists() and a_tree.exists()


def _close_env() -> dict[str, str]:
    """The environment a close is run in from a test: without this session's virtualenv, so `uv`
    builds the script's own, and without the flags a handed-off close reads."""
    dropped = ("VIRTUAL_ENV", sdlc.HANDOFF_ENV, sdlc.OWN_SCRIPT_ENV, sdlc.LOCK_HELD_ENV)
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
        return subprocess.run(
            ["uv", "run", "--quiet", "--script", str(script), *args],
            cwd=cwd, capture_output=True, encoding="utf-8", env=_close_env(), timeout=600,
        )  # fmt: skip

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
    lock = str(sdlc._lock_path(root))
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
    sdlc._handoff(root, ["001"], "merged", dict(report))
    assert sdlc.LOCK_HELD_ENV not in seen[-1], "not held: nothing to pass"
    with sdlc._main_lock(root):
        sdlc._handoff(root, ["001"], "merged", dict(report))
    assert seen[-1][sdlc.LOCK_HELD_ENV] == lock and seen[-1][sdlc.HANDOFF_ENV] == "merged"
    monkeypatch.undo()

    # The child's side: told the parent holds it, it runs while that hold stands.
    _, folder = _shipped(root, "reopen")
    carried: list[bool] = []

    def watching(argv, **kwargs):
        env = kwargs.get("env") or os.environ
        carried.append(sdlc.LOCK_HELD_ENV in env)
        return real(argv, **kwargs)

    monkeypatch.setattr(sdlc.subprocess, "run", watching)
    held, done = threading.Event(), threading.Event()
    result: dict = {}

    def holding() -> None:
        with sdlc._main_lock(root):
            held.set()
            assert done.wait(60), "the close never finished under the parent's hold"

    def closing() -> None:
        result["code"] = sdlc.cmd_close(root, "001")
        done.set()

    holder = threading.Thread(target=holding)
    holder.start()
    assert held.wait(10)
    monkeypatch.setenv(sdlc.LOCK_HELD_ENV, lock)  # as the parent sets it for its child
    closer = threading.Thread(target=closing)
    closer.start()
    closer.join(60)
    assert done.is_set(), "the close deadlocked on the lock its parent holds"
    holder.join(10)
    assert result["code"] == 0
    assert sdlc.LOCK_HELD_ENV not in os.environ, "popped at the close's entry"
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


def _verdict(role: str, verdict: str = "PASS", changes: tuple[str, ...] = ()) -> str:
    lines = [f"VERDICT: {verdict}", *(f"- CHANGE: {c}" for c in changes)]
    evidence = "\n## Evidence\n$ true\nexit: 0\n" if role in factory.RUNS_THE_CHANGE else ""
    return "\n".join(lines) + "\n" + evidence


def _ready(root: Path, slug: str, edit: dict[str, str], tier: int = 1) -> Path:
    """A change made by `sdlc.py new`, built (each path in `edit` written), at `stage: test` with
    the approver's READY and a minor impact, one build round every reviewer passed, as a factory
    run leaves one. Returns its worktree."""
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
    (folder / "build").mkdir()
    (folder / "build" / "round-1.md").write_text("Built.\n", encoding="utf-8")
    hashes = factory._tree_hashes(tree, "main")
    factory.snapshot_path(folder, 1).write_text(
        "".join(f"{digest}  {p}\n" for p, digest in hashes.items()), encoding="utf-8"
    )
    (folder / "reviews" / "round-1").mkdir(parents=True)
    for role in factory.DEFAULTS["reviewers"]:
        (folder / "reviews" / "round-1" / f"{role}.md").write_text(_verdict(role), "utf-8")
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
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "committed", None), out
    assert "Sdlc-Landed: by=auto" in _git(tree, "log", "-1", "--format=%B")
    assert _git(tree, "rev-parse", "HEAD^") == base, "not rebased: the train stacks it"
    assert _git(tree, "status", "--porcelain") == ""
    assert not list((_folder(tree) / "reviews").glob("land-*")), "no landing round opened"
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
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
    plain = factory.land_question([_entry("001-a"), _entry("002-b")], "main", 4)
    assert plain == (
        "Land 2 changes in this order, 001-a, 002-b, each shipped with its approver's impact, "
        "committed, stacked in this order on main, gated once at the tip (a red tip bisected, "
        "the change at fault left out with why and the rest landed; a conflict resolved by one "
        "landing agent and reviewed again), brought up to date as often as main moves while "
        "landing, up to 4 times, and closed in order, pushed as git.push says? "
        "(yes / yes, with a fix / leave one out / no)"
    )
    assert "its builder" not in plain, "one landing agent, never each change's own builder"
    one = factory.land_question([_entry("001-a", checks=[{"name": "x", "command": "true"}])], "t")
    assert one.startswith("Land 1 change in this order, 001-a, each shipped with its approver's "
                          "impact, its acceptance checks run as shown, committed, stacked in this "
                          "order on t, gated once at the tip")  # fmt: skip


# ---------------------------------------------------------------- driving a train as the skill does


def _begin(root: Path, capsys, by: str = "auto", *idents: str) -> dict:
    """Begin a train over `idents`, or over every ready change."""
    names = list(idents) or [r["change"] for r in factory.ready(root)]
    code, out = _run(capsys, factory.cmd_train, root, begin=names, by=by)
    assert code == 0 and out["state"] == "begun", out
    return out


def _verified(folder: Path, n: int, kept: list[str] = (), dropped: list[str] = ()) -> None:
    """The verifier's answers, each `<role>: <change>` as the reviewer asked it."""
    lines = [f"- KEPT: {c}" for c in kept] + [f"- DROPPED: {c}" for c in dropped]
    (folder / "reviews" / f"land-{n}" / factory.VERIFIED).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _asked(verdict: dict) -> list[str]:
    """Every change the round's reviewers asked for, as `<role>: <change>`."""
    return [
        f"{role}: {c}" for role, r in verdict["reviews"].items()
        if r["verdict"] == "CHANGES" for c in r["changes"]
    ]  # fmt: skip


def _drive(
    root: Path,
    capsys,
    resolve=None,
    review=None,
    verify=None,
    mend=None,
    limit: int = 80,
    until=None,
) -> list[dict]:
    """Run the train as the land skill does: each reading's step is done by the command it names,
    agents stood in for by files. `resolve(tree, files)` writes a resolution; `review(folder, n,
    role)` a verdict (PASS by default); `verify(folder, verdict)` the verifier's answer (every
    change dropped by default); `mend(folder, n, role)` the role's reply again (a passing one by
    default), recorded in `runs/mended` as `agent --task land-mend` records it. A `commit` runs
    what the reading says comes `before` it (`accept`, `cases`). Stops at `done`, at `stop` (after
    `--stop`), or once `until(reading)` holds. Returns every reading, an `eject`'s with what
    `--eject` printed as `did`."""
    readings: list[dict] = []
    for _ in range(limit):
        code, out = _run(capsys, factory.cmd_train, root)
        readings.append(out)
        nxt = out.get("next")
        if until is not None and until(out):
            return readings
        if nxt in (None, "done"):
            return readings
        if nxt == "stop":
            code, stopped = _run(capsys, factory.cmd_train, root, stop=True)
            assert code == 0, stopped
            readings.append(stopped)
            return readings
        tree, num = Path(out["worktree"]), out["change"].split("-")[0]
        folder = _folder(tree)
        if nxt == "commit":
            for first in out["before"]:
                assert _run(capsys, getattr(factory, f"cmd_{first}"), tree, num)[0] == 0
            code, done = _run(capsys, factory.cmd_land, tree, num, out["by"])
            assert code == 0, done
        elif nxt == "stack":
            code, done = _run(capsys, factory.cmd_resolve, tree, num, False, onto=out["onto"])
            assert code == 0 and done["state"] in ("current", "stacked", "conflict"), done
        elif nxt == "resolve":
            assert resolve is not None, out
            resolve(tree, out["files"])
            code, done = _run(capsys, factory.cmd_resolve, tree, num, True)
            assert code == 0, done
        elif nxt == "gate":
            _run(capsys, factory.cmd_gate, tree, num, True)
        elif nxt == "eject":
            code, done = _run(capsys, factory.cmd_train, root, eject=out["change"])
            assert code == 0, done
            out["did"] = done
        elif nxt == "accept":
            _run(capsys, factory.cmd_accept, tree, num)
        elif nxt == "review":
            for role in out["verdict"]["missing"]:
                if review is not None:
                    review(folder, out["verdict"]["round"], role)
                else:
                    reviews = folder / "reviews" / f"land-{out['verdict']['round']}"
                    (reviews / f"{role}.md").write_text(_verdict(role), encoding="utf-8")
        elif nxt == "verify":
            if verify is not None:
                verify(folder, out["verdict"])
            else:
                _verified(folder, out["verdict"]["round"], dropped=_asked(out["verdict"]))
        elif nxt == "mend":
            n = out["verdict"]["round"]
            for role in out["verdict"]["mend"]:
                if mend is not None:
                    mend(folder, n, role)
                else:
                    reply = folder / "reviews" / f"land-{n}" / f"{role}.md"
                    reply.write_text(_verdict(role), encoding="utf-8")
                with (folder / factory.MENDED).open("a", encoding="utf-8") as f:
                    f.write(f"{role} land-{n}\n")
        elif nxt == "close":
            code, done = _run(capsys, factory.cmd_land_close, tree, num)
            assert code == 0, done
        else:
            raise AssertionError(f"the test can't take the step {nxt!r}: {out}")
    raise AssertionError(f"the train didn't finish in {limit} steps: {readings[-1]}")


def _three(tmp_path: Path, check: str | None = None) -> tuple[Path, list[Path]]:
    """A host with three ready changes, each editing a file of its own."""
    root = _repo(tmp_path, check)
    trees = [_ready(root, slug, {f"{slug}.txt": f"{slug}\n"}) for slug in ("aa", "bb", "cc")]
    return root, trees


def _first_parent(root: Path) -> list[str]:
    return _git(root, "log", "--first-parent", "--format=%s", "main").splitlines()


def _state_file(root: Path) -> Path:
    common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / factory.TRAIN_STATE


# ---------------------------------------------------------- stacking and closing (R1, R9, R11, R19)


@needs_uv
def test_a_train_stacks_each_change_on_the_one_before(tmp_path, capsys) -> None:
    """R1: change 1 goes onto the base branch's tip and change k onto stacked commit k−1, each
    rebased in its own worktree; `<trunk>..<k>` holds exactly changes 1..k's commits."""
    root, trees = _three(tmp_path)
    _begin(root, capsys)
    readings = _drive(root, capsys, until=lambda o: o.get("next") == "close")
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
    readings = _drive(root, capsys)
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
    assert _run(capsys, factory.cmd_train, root)[1]["under_way"] is False


@needs_uv
def test_a_rerun_resumes_the_train_and_a_second_refuses(tmp_path, capsys) -> None:
    """R19: the train's state lives in the git common dir, never in a tree; a second `--begin`
    refuses while one is under way, and a later reading carries on where it was."""
    root, trees = _three(tmp_path)
    begun = _begin(root, capsys)
    assert begun["order"] == [t.name for t in trees]
    assert _state_file(root).is_file() and ".git" in _state_file(root).parts, "the common dir"
    assert _git(root, "status", "--porcelain") == "", "the main checkout is untouched"
    _drive(root, capsys, until=lambda o: o["next"] == "stack")
    code, again = _run(capsys, factory.cmd_train, root, begin=["1", "2"], by="person")
    assert code == 1 and "under way" in again["refusals"][0], again
    # A new session: the reading resumes from the state alone.
    readings = _drive(root, capsys)
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
    readings = _drive(root, capsys, until=lambda o: o["next"] == "close")
    pre = {n: c["pre"] for n, c in readings[-1]["changes"].items()}
    code, out = _run(capsys, factory.cmd_train, root, stop=True)
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
    readings = _drive(root, capsys)
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
    assert _drive(root, capsys)[-1]["next"] == "done"
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
    readings = _drive(root, capsys)
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

    def review(folder: Path, n: int, role: str) -> None:
        asks = folder.name == trees[1].name and role == "behaviour"
        text = _verdict(role, "CHANGES", ("bb.txt:1: say more",)) if asks else _verdict(role)
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(text, encoding="utf-8")

    def verify(folder: Path, verdict: dict) -> None:
        _verified(folder, verdict["round"], kept=_asked(verdict))

    readings = _drive(root, capsys, review=review, verify=verify)
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

    def review(folder: Path, n: int, role: str) -> None:
        asks = folder.name == trees[1].name and role == "behaviour"
        text = _verdict(role, "CHANGES", ("bb.txt:1: say more",)) if asks else _verdict(role)
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(text, encoding="utf-8")

    def verify(folder: Path, verdict: dict) -> None:
        _verified(folder, verdict["round"], kept=_asked(verdict))

    first = _drive(root, capsys, review=review, verify=verify)[-1]
    assert [e["change"] for e in first["ejected"]] == [trees[1].name], first
    folder = _folder(trees[1])
    ejected_round = factory.land_round(folder)
    code, out, said = factory._sdlc(["resolve", trees[1].name], trees[1])
    assert code == 0 and out["state"] == "clean", said
    _begin(root, capsys, "person", trees[1].name)
    readings = _drive(root, capsys)
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
    readings = _drive(root, capsys)
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
    unreadable = "I ran it first.\n\nVERDICT: CHANGES\n- CHANGE: x\n" + _verdict("behaviour")

    def review(folder: Path, n: int, role: str) -> None:
        text = unreadable if folder.name == trees[1].name else _verdict(role)
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(text, encoding="utf-8")

    def mend(folder: Path, n: int, role: str) -> None:
        (folder / "reviews" / f"land-{n}" / f"{role}.md").write_text(unreadable, encoding="utf-8")

    readings = _drive(root, capsys, review=review, mend=mend)
    last = readings[-1]
    assert last["next"] == "done", last
    assert last["landed"] == [trees[0].name, trees[2].name]
    assert [e["change"] for e in last["ejected"]] == [trees[1].name]
    assert "doesn't open with a VERDICT" in last["ejected"][0]["reason"], last["ejected"]
    steps = [(r["next"], r.get("change")) for r in readings]
    assert steps.count(("mend", trees[1].name)) == 1, "mended once, then a stop"
    assert ("eject", trees[1].name) in steps
    mended = _git(trees[1], "show", f"HEAD:.sdlc/work/{trees[1].name}/{factory.MENDED.as_posix()}")
    assert mended.split("\n")[0] == "behaviour land-1"
    assert len([s for s in _first_parent(root) if s.startswith("Close ")]) == 2


def _conflicting(
    tmp_path: Path, check: str | None = "true", tier2: bool = False
) -> tuple[Path, list[Path]]:
    """Two ready changes that edit README's first line: stacking the second conflicts."""
    root = _repo(tmp_path, check)
    first = _ready(root, "first", {"README.md": "first's one\ntwo\nthree\n"})
    second = _ready(root, "second", {"README.md": "second's one\ntwo\nthree\n"},
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
    readings = _drive(root, capsys, resolve=_resolving, until=lambda o: o.get("next") == "review")
    last = readings[-1]
    assert last["change"] == trees[1].name and set(last["verdict"]["missing"]) == set(
        factory.DEFAULTS["reviewers"]
    ), last
    steps = [(r["next"], r.get("change")) for r in readings]
    assert ("resolve", trees[1].name) in steps and ("gate", trees[1].name) in steps
    assert steps.index(("gate", trees[1].name)) < steps.index(("review", trees[1].name))
    code, out = _run(capsys, factory.cmd_land_close, trees[1], "002")
    assert code == 1 and "no landing review has passed it" in out["refusals"][0], out
    assert _git(root, "log", "-1", "--format=%s", "main") == "init", "nothing closed"
    readings = _drive(root, capsys, resolve=_resolving)
    assert readings[-1]["next"] == "done" and len(readings[-1]["landed"]) == 2, readings[-1]
    assert (root / "README.md").read_text(encoding="utf-8").startswith("first's one, and second's")


@needs_uv
def test_a_train_conflict_goes_to_one_agent_with_every_change(tmp_path, capsys, monkeypatch):
    """R3: the conflict goes to the builder as `train-resolve`, a fresh session whose prompt names
    every change in the train, its spec (`spec.md`, or `intent.md` at Tier 1) and its diff; its
    session id lands in change 2's `runs/builder.sessions`; the counter still settles itself."""
    root, trees = _conflicting(tmp_path, tier2=True)
    _begin(root, capsys)
    readings = _drive(root, capsys, until=lambda o: o.get("next") == "resolve")
    last = readings[-1]
    assert last["change"] == trees[1].name and last["files"] == ["README.md"], last
    folder = _folder(trees[1])
    pre = {n: c["pre"] for n, c in last["changes"].items()}
    prompt, target, append = factory._land_task(trees[1], folder, "train-resolve", "builder")
    assert target == folder / "build" / "land-1.md" and append is False
    for tree in trees:
        intent = _git(tree, "show", f"{pre[tree.name]}:.sdlc/work/{tree.name}/intent.md")
        title = next(ln[2:] for ln in intent.splitlines() if ln.startswith("# "))
        assert title in prompt, (title, prompt)
        spec = "spec.md" if tree is trees[1] else "intent.md"
        assert f"git show {pre[tree.name]}:.sdlc/work/{tree.name}/{spec}" in prompt, prompt
        assert f"git show {pre[tree.name]}`" in prompt, prompt
    assert "README.md" in prompt and "## Evidence" in prompt
    calls: list[list[str]] = []

    def fake(argv: list[str], cwd: Path):
        calls.append(argv)
        _resolving(trees[1], ["README.md"])
        return 0, "Kept both lines.\n\n## Evidence\n\n$ true\nexit: 0\n", None, None

    monkeypatch.setattr(factory, "_claude", fake)
    sessions = folder / "runs" / "builder.sessions"
    before = sessions.read_text(encoding="utf-8").split() if sessions.is_file() else []
    code, out = _run(capsys, factory.cmd_agent, trees[1], "002", "train-resolve", None, None)
    assert code == 0 and out["role"] == "builder", out
    assert "--session-id" in calls[0] and "--resume" not in calls[0], "never a resumed session"
    session = out["session"]
    assert sessions.read_text(encoding="utf-8").split() == [*before, session]
    assert "sdlc-factory:builder" in calls[0]
    code, out = _run(capsys, factory.cmd_resolve, trees[1], "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert (trees[1] / ".sdlc" / "last-id").read_text(encoding="utf-8").strip() == "002"
    dirty = _git(trees[1], "status", "--porcelain").splitlines()
    assert not any("builder.sessions" in d for d in dirty), "the session id went into the commit"
    committed = _git(trees[1], "show", f"HEAD:.sdlc/work/{trees[1].name}/runs/builder.sessions")
    assert committed.split()[-1] == session
    readings = _drive(root, capsys)
    assert readings[-1]["next"] == "done" and len(readings[-1]["landed"]) == 2, readings[-1]


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
    out = _drive(root, capsys, until=lambda r: r.get("next") == "stack")[-1]
    tree, num = Path(out["worktree"]), out["change"].split("-")[0]
    (tree / "stray.txt").write_text("not the change's\n", encoding="utf-8")
    code, done = _run(capsys, factory.cmd_resolve, tree, num, False, onto=out["onto"])
    assert code == 1 and done["refusals"][0].startswith("uncommitted outside"), done
    plain, raw = stop(tree)
    assert (
        "stray.txt" in plain and f"/sdlc-factory:land {num}" in plain and raw == done["refusals"][0]
    )
    (tree / "stray.txt").unlink()
    code, done = _run(capsys, factory.cmd_resolve, tree, num, False, onto="0" * 40)
    assert code == 1 and done["refusals"][0].startswith("git rebase --onto"), done
    plain, raw = stop(tree)
    assert plain.startswith("stacking it onto") and f"/sdlc-factory:land {num}" in plain
    assert raw == done["refusals"][0]

    root, (_, second) = _conflicting(tmp_path / "two")
    _begin(root, capsys)
    _drive(root, capsys, until=lambda r: r.get("next") == "resolve")
    code, done = _run(capsys, factory.cmd_resolve, second, "002", True)
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
    readings = _drive(root, capsys, until=lambda o: o.get("landed") == names[:1])
    assert readings[-1]["next"] == "close" and readings[-1]["change"] == names[1], readings[-1]
    _file_an_idea(root, capsys, 1)
    more = _drive(root, capsys)
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
    readings = _drive(root, capsys, until=lambda o: o.get("landed") == names[:1])
    pre = {n: c["pre"] for n, c in readings[-1]["changes"].items()}
    _file_an_idea(root, capsys, 1)
    more = _drive(root, capsys, until=lambda o: o.get("next") == "close" and o["moves"] == 1)
    assert more[-1]["change"] == names[1], more[-1]
    _file_an_idea(root, capsys, 2)
    rest = _drive(root, capsys)
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
