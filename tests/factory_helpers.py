"""What the factory's test files share: `factory.py` and `sdlc.py` loaded by path, once, and the
scratch change, its reviews and its rounds that each test builds. Imported by name, as
`train_driver.py` is, never copied.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


factory = _load("factory_under_test", ROOT / "plugins" / "factory" / "scripts" / "factory.py")
sdlc = _load("sdlc_for_factory", ROOT / "scripts" / "sdlc.py")

NAME = "008-reopen-drafts"
INTENT = """\
---
id: 008
slug: reopen-drafts
tier: {tier}
impact: minor
stage: {stage}
created: 2026-10-01
updated: 2026-10-02
idea:
---

# 008 — Reopen saved drafts

## Problem

Real prose, not a template.
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _change(
    tmp_path: Path,
    tier: int = 2,
    stage: str = "design",
    branch: str = NAME,
    config: str | None = None,
) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    if config is not None:
        (root / ".sdlc").mkdir()
        (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", branch)
    folder = root / ".sdlc" / "work" / NAME
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(tier=tier, stage=stage), encoding="utf-8")
    for artifact in ("spec.md", "plan.md"):
        (folder / artifact).write_text(f"# 008 — {artifact}\n\nWritten.\n", encoding="utf-8")
    return root


def _run(capsys, fn, *args) -> tuple[int, dict]:
    code = fn(*args)
    return code, json.loads(capsys.readouterr().out)


def _review(root: Path, n: int, role: str, verdict: str, *changes: str) -> None:
    folder = root / ".sdlc" / "work" / NAME / "reviews" / f"round-{n}"
    folder.mkdir(parents=True, exist_ok=True)
    body = "".join(f"- CHANGE: {c}\n" for c in changes)
    tail = EVIDENCE if role == "behaviour" else ""
    text = f"{verdict}\n{body}\n## Notes\n\nFine.\n{tail}"
    (folder / f"{role}.md").write_text(text, encoding="utf-8")


# What a builder report and a behaviour check end with: each command, its output's tail, its exit.
EVIDENCE = "\n## Evidence\n\n$ ./check.sh\n12 passed\nexit: 0\n"
FULL = ["code", "security", "test", "behaviour"]


def _build_report(root: Path, n: int, *lines: str) -> None:
    folder = root / ".sdlc" / "work" / NAME / "build"
    folder.mkdir(parents=True, exist_ok=True)
    text = "Built slice 1.\n" + "".join(lines) + EVIDENCE
    (folder / f"round-{n}.md").write_text(text, encoding="utf-8")


def _verified(root: Path, n: int, kept: list[str] = (), dropped: list[str] = ()) -> None:
    """The arbiter's answer for round `n`: each `role: change` kept, or dropped with a reason."""
    folder = root / ".sdlc" / "work" / NAME / "reviews" / f"round-{n}"
    folder.mkdir(parents=True, exist_ok=True)
    lines = [f"- KEPT: {k}\n" for k in kept] + [
        f"- DROPPED: {d} — not in the code\n" for d in dropped
    ]
    (folder / "verified.md").write_text("".join(lines), encoding="utf-8")


def _round(root: Path, n: int, **verdicts: str) -> None:
    """Review round `n`, as the loop makes one: after the builder's report for that round."""
    if not (root / ".sdlc" / "work" / NAME / "build" / f"round-{n}.md").exists():
        _build_report(root, n)
    for role in FULL:
        verdict = verdicts.get(role, "PASS")
        changes = (f"{role} fix {n}",) if verdict == "CHANGES" else ()
        _review(root, n, role, f"VERDICT: {verdict}", *changes)


# ---------------------------------------------------------------- start


def _main_moves(root: Path, *names: str) -> None:
    """A commit on `main` for each name, adding that file, then back on the change's branch."""
    _git(root, "checkout", "-q", "main")
    for name in names:
        (root / name).write_text(f"{name}\n", encoding="utf-8")
        _git(root, "add", name)
        _git(root, "commit", "-q", "-m", f"main adds {name}")
    _git(root, "checkout", "-q", NAME)


# ---------------------------------------------------------------- verdicts and the loop


def _verdicts(root, capsys, head=None) -> dict:
    return _run(capsys, factory.cmd_verdicts, root, "008", head)[1]


# ---------------------------------------------------------------- the stop record (085)


def _record(root, capsys, head: str) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_verdicts, root, "008", head, True)


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "--short", "HEAD")


# ---------------------------------------------------------------- depth set by risk


LISTED = '[review]\nsensitive = ["src/secret/"]\n'


def _touch(root: Path, path: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text("x\n")


def _report(root: Path, n: int, text: str) -> None:
    """A builder report written as-is, evidence or not."""
    folder = root / ".sdlc" / "work" / NAME / "build"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"round-{n}.md").write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- the supervisor


def _from_main(tmp_path: Path, stage: str = "design") -> tuple[Path, Path]:
    """A main checkout on `main`, and change 008's own worktree beside it, its folder committed on
    its branch: where the supervisor, a session in the main checkout, finds it."""
    root = _change(tmp_path, stage=stage)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "008's folder")
    _git(root, "checkout", "-q", "main")
    tree = tmp_path / "wt-008"
    _git(root, "worktree", "add", "-q", str(tree), NAME)
    return root, tree


# ---------------------------------------------------------------- the [ui] table and its reviewers


def _on_main(root: Path, factory_toml: str) -> None:
    """Commit `factory_toml` as the base branch's `.sdlc/factory.toml`, back on the change after."""
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(factory_toml, encoding="utf-8")
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "factory")
    _git(root, "checkout", "-q", NAME)


# ---------------------------------------------------------------- the gate


def _gate_config(root: Path, command: str, extra: str = "") -> None:
    """Commit `[commands] check` on `main`, the base branch, and go back to the change's branch,
    whose own checkout then has no config of its own."""
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    text = f"[commands]\ncheck = {json.dumps(command)}\n{extra}"
    (root / ".sdlc" / "config.toml").write_text(text, encoding="utf-8")
    _git(root, "add", ".sdlc/config.toml")
    _git(root, "commit", "-q", "-m", "gate")
    _git(root, "checkout", "-q", NAME)


def _gate(root, capsys) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_gate, root, "008")


def _fixed(root: Path, n: int = 1) -> None:
    """What a fix does to the round's report and snapshot: added to, so the build is a new one."""
    report = root / ".sdlc" / "work" / NAME / "build" / f"round-{n}.md"
    report.write_text(report.read_text(encoding="utf-8") + "\nFixed it.\n", encoding="utf-8")


# ---------------------------------------------------------------- the step record (088)


def _step(root: Path) -> Path:
    return root / ".sdlc" / "work" / NAME / factory.STEP


def _fields(root: Path) -> dict:
    return factory.read_step(_step(root).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- an escalated change sent back


RECONSIDERED = (
    "DECISION: ESCALATE\n\nThe export kept failing review.\n\n"
    "## Reconsider the approach\n\nSplit the writer from the format.\nThen build the CSV first.\n\n"
    "## Notes\n\nNothing else.\n"
)


def _escalated(root: Path, rounds: int = 3, decision: str = RECONSIDERED) -> Path:
    """A run whose rounds ran out with a change kept every round, escalated by the approver."""
    for n in range(1, rounds + 1):
        _round(root, n, code="CHANGES")
        _verified(root, n, kept=[f"code: code fix {n}"])
    folder = root / ".sdlc" / "work" / NAME
    (folder / "decision.md").write_text(decision, encoding="utf-8")
    return folder


def _restart(root, capsys, words: str | None = None) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_restart, root, "008", words)


# ---------------------------------------------------------------- a build starts current (101)


needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _commit_on_main(root: Path, name: str, text: str) -> None:
    (root / name).write_text(text, encoding="utf-8")
    _git(root, "add", name)
    _git(root, "commit", "-q", "-m", f"main changes {name}")


def _files(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*")
            if p.is_file()}  # fmt: skip


# ---------------------------------------------------------------- gates share the machine (101)


FACTORY_PY = ROOT / "plugins" / "factory" / "scripts" / "factory.py"


# ---------------------------------------------------------------- a run upgraded to Tier 2 (112)


UPGRADE_Q = (
    "Upgrade to Tier 2? Drafts need a retention policy. Options: upgrade to Tier 2; stay Tier 1"
)
UPGRADE_LINE = (
    f"- [x] D1 (builder round 1, blocking): {UPGRADE_Q} → decided: "
    "Upgrade to Tier 2: keep 30 days\n"
)


def _tier1_run(
    tmp_path: Path, ledger: str | None = UPGRADE_LINE, config: str | None = None
) -> tuple[Path, Path]:
    """A Tier 1 run at `stage: build` whose builder raised an upgrade in round 1, unreviewed, and
    the person's answer in the ledger: (root, folder). No spec.md or plan.md, as `new` left it."""
    root = _change(tmp_path, 1, "build", config=config)
    folder = root / ".sdlc" / "work" / NAME
    for name in ("spec.md", "plan.md"):
        (folder / name).unlink()
    _build_report(root, 1, f"- DECISION: [blocking] {UPGRADE_Q}\n")
    if ledger is not None:
        (folder / "decisions.md").write_text(f"# Decisions\n\n{ledger}", encoding="utf-8")
    return root, folder


def _upgraded(root: Path, folder: Path, n: int = 2) -> None:
    """What `factory.py upgrade` leaves, written by hand for the tests that don't run `sdlc.py`."""
    (folder / "build" / f"round-{n}.upgraded.md").write_text("UPGRADED: D1\n", encoding="utf-8")
    intent = folder / "intent.md"
    text = intent.read_text(encoding="utf-8").replace("tier: 1", "tier: 2")
    intent.write_text(text.replace("stage: build", "stage: plan"), encoding="utf-8")
    spec = (ROOT / "templates" / "spec.md").read_text(encoding="utf-8")
    (folder / "spec.md").write_text(spec, encoding="utf-8")
    plan = (ROOT / "templates" / "plan.md").read_text(encoding="utf-8")
    (folder / "plan.md").write_text(plan, encoding="utf-8")
