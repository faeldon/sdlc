"""The factory's landing: a batch of ready changes shipped, committed, brought up to date and
closed through `sdlc.py`'s own commands, which `factory.py` runs from its own version beside it.

Each test builds a bare scratch repo and makes its changes with `sdlc.py new`, as a host does, so
the landing runs the real ship, base and close, never a copy. Nothing here runs an agent: a
review or a resolution is written as the agent would reply.
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


factory = _load("factory_landing", ROOT / "plugins" / "factory" / "scripts" / "factory.py")

needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _run(capsys, fn, *args) -> tuple[int, dict]:
    code = fn(*args)
    return code, json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------- finding its own sdlc


def _plugin(root: Path, name: str, version: str) -> None:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": version}), encoding="utf-8"
    )


def test_the_landing_runs_the_sdlc_of_its_own_version_from_the_clone_or_the_cache(tmp_path):
    """Read in place, the factory sits at `plugins/factory/` in the clone, whose `scripts/sdlc.py`
    is sdlc's; installed, the marketplace cache holds each plugin by name and version side by
    side. Another version's sdlc is refused: landing runs the code the factory was released with."""
    found, why = factory.sdlc_path()
    assert why is None and found == ROOT / "scripts" / "sdlc.py", "this repo is a clone"
    cache = tmp_path / "cache" / "sdlc"
    mine = cache / "sdlc-factory" / "1.9.0"
    _plugin(mine, "sdlc-factory", "1.9.0")
    theirs = cache / "sdlc" / "1.9.0"
    _plugin(theirs, "sdlc", "1.9.0")
    (theirs / "scripts").mkdir()
    (theirs / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    assert factory.sdlc_path(mine) == (theirs / "scripts" / "sdlc.py", None)
    older = cache / "sdlc-factory" / "1.8.0"
    _plugin(older, "sdlc-factory", "1.8.0")
    found, why = factory.sdlc_path(older)
    assert found is None and "no sdlc 1.8.0" in why, "never another version's"
    clone = tmp_path / "clone"
    _plugin(clone, "sdlc", "1.7.0")
    (clone / "scripts").mkdir()
    (clone / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    _plugin(clone / "plugins" / "factory", "sdlc-factory", "1.8.0")
    found, why = factory.sdlc_path(clone / "plugins" / "factory")
    assert found is None and "version 1.7.0" in why and "one version" in why


# ---------------------------------------------------------------- the message


def test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count(tmp_path) -> None:
    folder = tmp_path / ".sdlc" / "work" / "008-reopen-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        "---\nid: 008\n---\n\n# 008 — Reopen saved drafts\n\n## Problem\n\nA saved draft can't be\n"
        "reopened. Nothing reads it back.\n\n## Outcome\n\nIt can.\n",
        encoding="utf-8",
    )
    message = factory.land_message(tmp_path, folder, "auto", True)
    assert message.splitlines()[0] == "Reopen saved drafts"
    assert "A saved draft can't be reopened. See .sdlc/work/008-reopen-drafts/." in message
    assert "Nothing reads it back" not in message, "the Problem's first sentence only"
    assert message.rstrip().endswith("Refs #8\nSdlc-Landed: by=auto")
    assert "Sdlc-Findings" not in message, "a missing line reads as unanswered, never as clean"
    assert "Refs" not in factory.land_message(tmp_path, folder, "person", False)


# ---------------------------------------------------------------- a batch, end to end


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "host"
    root.mkdir()
    (root / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _ready(root: Path, slug: str, first_line: str, impact: str = "minor") -> Path:
    """A change made by `sdlc.py new`, built (its README's first line), at `stage: test` with the
    approver's READY and its proposed impact, as a factory run leaves one."""
    code, _, said = factory._sdlc(["new", slug, "--tier", "1", "--worktree"], root)
    assert code == 0, said
    tree = next(p for p in (root / ".claude" / "worktrees").iterdir() if p.name.endswith(slug))
    folder = tree / ".sdlc" / "work" / tree.name
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("stage: plan", "stage: test"), encoding="utf-8"
    )
    (folder / "decision.md").write_text(
        f"DECISION: READY\n\nIt does what it says.\n\n- IMPACT: {impact} — a test change\n",
        encoding="utf-8",
    )
    (tree / "README.md").write_text(f"{first_line}\ntwo\nthree\n", encoding="utf-8")
    return tree


@needs_uv
def test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed(
    tmp_path, capsys
) -> None:
    """Two ready changes edit one line: the first lands as it is; the second's rebase conflicts,
    the rebase is left for the builder, its resolution is reviewed again at the run's depth, and
    it lands too. Each commit says who passed the gate, and nothing is left behind."""
    root = _repo(tmp_path)
    first, second = _ready(root, "first", "first's one"), _ready(root, "second", "second's one")
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert code == 0 and [c["change"] for c in batch["batch"]] == [first.name, second.name]
    assert batch["clear"] is True, batch
    assert [c["impact"] for c in batch["batch"]] == ["minor", "minor"]

    code, out = _run(capsys, factory.cmd_land, first, "001", "auto")
    assert (code, out["state"]) == (0, "current"), out
    assert "Sdlc-Landed: by=auto" in _git(first, "log", "-1", "--format=%B")
    code, out = _run(capsys, factory.cmd_land_close, first, "001")
    assert code == 0 and "merge" in out["done"], out
    assert not first.exists(), "its worktree is gone"

    code, out = _run(capsys, factory.cmd_land, second, "002", "auto")
    assert (code, out["state"], out["round"]) == (0, "conflict", 1), out
    code, out = _run(capsys, factory.cmd_resolve, second, "002", False)
    assert out["conflicted"] == ["README.md"]
    code, out = _run(capsys, factory.cmd_resolve, second, "002", True)
    assert code == 1 and "conflict markers left" in out["refusals"][0], "not resolved yet"
    (second / "README.md").write_text("first's one, and second's\ntwo\nthree\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_resolve, second, "002", True)
    assert (code, out["state"]) == (0, "resolved"), out
    folder = second / ".sdlc" / "work" / second.name
    signals, _ = factory.land_signals(folder, second, "READY", factory.load_config(second)[0])
    assert "a conflict was resolved while landing" in signals, "the next gate is the person's"

    code, out = _run(capsys, factory.cmd_land_verdicts, second, "002")
    assert out["next"] == "review" and set(out["missing"]) == set(factory.REVIEWERS)
    reviews = folder / "reviews" / "land-1"
    for role in factory.REVIEWERS:
        evidence = "\n\n## Evidence\n$ true\nexit: 0\n" if role == "behaviour" else "\n"
        (reviews / f"{role}.md").write_text(f"VERDICT: PASS{evidence}", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_land_verdicts, second, "002")
    assert out["next"] == "pass", out

    code, out = _run(capsys, factory.cmd_land_close, second, "002")
    assert code == 0 and "merge" in out["done"], out
    log = _git(root, "log", "--format=%s", "main").splitlines()
    assert log[0] == f"Close {second.name}" and f"Close {first.name}" in log
    assert (root / "README.md").read_text(encoding="utf-8").startswith("first's one, and second's")
    landed = _git(root, "log", "-1", "--format=%B", "main~1")
    assert "Sdlc-Landed: by=auto" in landed, "the resolution and its review amended in"
    assert ".sdlc/work/002-second/reviews/land-1/behaviour.md" in _git(
        root, "show", "--name-only", "--format=", "main~1"
    )


@needs_uv
def test_a_rebased_change_is_gated_by_the_script_before_its_review(tmp_path, capsys) -> None:
    """073 R12: the behaviour check no longer runs the gate, so after a rebase the landing runs the
    base branch's check itself, into `build/land-<n>.gate.md`, before any reviewer; a red gate on
    the change as rebased is a stop, for the person to ship by hand."""
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text(
        '[commands]\ncheck = "test ! -f broken.txt"\n', encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a gate")
    tree = _ready(root, "gated", "gated's one")
    # The base branch moves under it, touching nothing the change does: a clean rebase.
    (root / "elsewhere.txt").write_text("moved on\n", encoding="utf-8")
    _git(root, "add", "elsewhere.txt")
    _git(root, "commit", "-q", "-m", "main moves on")

    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert (code, out["state"], out["round"]) == (0, "rebased", 1), out
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "gate" and out["gate"]["command"] == "test ! -f broken.txt", out
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"]) == (0, "PASS") and out["to"].endswith("build/land-1.gate.md")
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert (out["next"], out["missing"]) == ("review", ["behaviour"]), out

    (tree / "broken.txt").write_text("", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_gate, tree, "001", True)
    assert (code, out["verdict"], out["attempt"]) == (1, "FAIL", 2)
    code, out = _run(capsys, factory.cmd_land_verdicts, tree, "001")
    assert out["next"] == "stop" and "ship it by hand" in out["problems"][0], out


@needs_uv
def test_a_refused_step_lands_nothing_of_that_change(tmp_path, capsys) -> None:
    """A change the approver proposed no impact for can't be shipped by land: it is refused before
    anything is written, and its folder and worktree stay as they were."""
    root = _repo(tmp_path)
    tree = _ready(root, "lone", "lone's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "decision.md").write_text("DECISION: READY\n\nNo impact here.\n", encoding="utf-8")
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert batch["clear"] is False and "proposes no `- IMPACT:`" in batch["batch"][0]["signals"][0]
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and "no impact" in out["refusals"][0]
    assert "stage: test" in (folder / "intent.md").read_text(encoding="utf-8")
    assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"


@needs_uv
def test_a_change_with_acceptance_checks_or_undone_items_is_shipped_by_hand(
    tmp_path, capsys
) -> None:
    root = _repo(tmp_path)
    tree = _ready(root, "checked", "checked's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "checks.md").write_text(
        "# Checks\n\n> Acceptance checks.\n\n## It runs\n\n```sh\ntrue\n```\n", encoding="utf-8"
    )
    (folder / "notes.md").write_text("# Notes\n\n- [ ] a thing left\n", encoding="utf-8")
    code, batch = _run(capsys, factory.cmd_land_check, root, [])
    assert batch["batch"] == [] and batch["clear"] is False
    why = batch["excluded"][0]["excluded"]
    assert any("undone" in w for w in why) and any("acceptance checks" in w for w in why)
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert code == 1 and out["refusals"][0].startswith("ship it by hand"), "whoever passed the gate"
    assert "stage: test" in (folder / "intent.md").read_text(encoding="utf-8")


@needs_uv
def test_a_risky_change_is_never_landed_by_auto_whatever_the_skill_says(tmp_path, capsys) -> None:
    """The gate's rule is the script's: `land --by auto` on a change with a risk signal (here the
    approver escalated) is refused before anything is written, and the person's yes lands it."""
    root = _repo(tmp_path)
    tree = _ready(root, "risky", "risky's one")
    folder = tree / ".sdlc" / "work" / tree.name
    (folder / "decision.md").write_text(
        "DECISION: ESCALATE\n\nA call for the person.\n\n- IMPACT: minor — a test change\n",
        encoding="utf-8",
    )
    code, out = _run(capsys, factory.cmd_land, tree, "001", "auto")
    assert code == 1 and "the approver escalated" in out["refusals"][0]
    assert _git(tree, "log", "-1", "--format=%s") == "init", "nothing committed"
    code, out = _run(capsys, factory.cmd_land, tree, "001", "person")
    assert (code, out["state"]) == (0, "current"), out
    assert "Sdlc-Landed: by=person" in _git(tree, "log", "-1", "--format=%B")
