"""The optional factory's mechanism: which change a run is in, whether its stage lets a step
start, what each review file's first line says, which step the loop takes next, and that a change
the agents built reads to `sdlc` like any other.

`factory.py` is loaded by path, like `sdlc.py`. Each test builds a scratch repo on a change branch
with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
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
    """The verifier's answer for round `n`: each `role: change` kept, or dropped with a reason."""
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


# ---------------------------------------------------------------- config


def test_config_defaults_and_its_warnings(tmp_path: Path) -> None:
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg == {
        "reviewers": FULL,
        "rounds": 3,
        "light": {"reviewers": ["code"], "rounds": 2, "chosen": False},
        "models": {},
        "mode": "auto",
        "land": {"auto": True, "batch": 5, "moves": 3},
        "ui": factory.DEFAULTS["ui"],
        "gate_jobs": 1,
    }
    assert warnings == []
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "factory.toml").write_text(
        'reviewers = ["code", "secruity"]\nrounds = 9\nloops = 1\n'
        '[models]\nbuilder = "sonnet"\ndesigner = "opus"\n',
        encoding="utf-8",
    )
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["reviewers"] == ["code"] and cfg["rounds"] == 3
    assert cfg["models"] == {}, "[models] is the base branch's, and there is none"
    assert any("unknown reviewer 'secruity'" in w for w in warnings)
    assert any("rounds must be" in w for w in warnings)
    assert "unknown key loops" in warnings
    assert any("models is read from the base branch" in w for w in warnings)


def test_light_is_a_table_checked_like_the_top_level(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    config = tmp_path / ".sdlc" / "factory.toml"
    config.write_text('[light]\nreviewers = ["test"]\nrounds = 1\n', encoding="utf-8")
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["light"] == {"reviewers": ["test"], "rounds": 1, "chosen": True} and warnings == []
    config.write_text('[light]\nreviewers = ["nobody"]\nrounds = 0\nloops = 2\n', encoding="utf-8")
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["light"] == {"reviewers": ["code"], "rounds": 2, "chosen": False}, (
        "a bad value keeps the default"
    )
    assert "unknown key light.loops" in warnings
    assert any("unknown reviewer 'nobody' in light.reviewers" in w for w in warnings)
    assert any(w.startswith("light.rounds must be") for w in warnings)
    config.write_text('light = "deep"\n', encoding="utf-8")
    assert "light must be a table of reviewers and rounds" in factory.load_config(tmp_path)[1]


def test_max_runs_is_shown_before_the_cost_is_approved() -> None:
    """At the full depth, whatever the diff turns out to need: the builder, the approver, and each
    round's reviewers, verifier, builder resume and the builder's two fixes of a red gate."""
    cfg = {"reviewers": ["code", "security", "test"], "rounds": 3, "models": {}}
    assert factory.max_runs(cfg) == 2 + 3 * (3 + 2 + 2)


# ---------------------------------------------------------------- start


@pytest.mark.parametrize(
    "tier, stage, purpose, ok",
    [
        (2, "plan", "spec", True),
        (2, "design", "spec", False),
        (1, "plan", "spec", False),
        (2, "design", "build", True),
        (2, "plan", "build", True),  # the supervisor has the spec-writer draft the spec first
        (1, "plan", "build", True),
        (2, "build", "build", True),
        (2, "test", "build", False),
    ],
)
def test_start_checks_the_tier_and_stage(tmp_path, capsys, tier, stage, purpose, ok) -> None:
    root = _change(tmp_path, tier, stage)
    code, out = _run(capsys, factory.cmd_start, root, "008", purpose)
    assert (code == 0) is ok and (not out["refusals"]) is ok, out["refusals"]
    assert out["head"] == _git(root, "rev-parse", "--short", "HEAD")
    if ok:
        assert out["change"] == NAME and out["max_runs"] == 26, "2 + 3 rounds × (4 + 2 + 2)"


def _main_moves(root: Path, *names: str) -> None:
    """A commit on `main` for each name, adding that file, then back on the change's branch."""
    _git(root, "checkout", "-q", "main")
    for name in names:
        (root / name).write_text(f"{name}\n", encoding="utf-8")
        _git(root, "add", name)
        _git(root, "commit", "-q", "-m", f"main adds {name}")
    _git(root, "checkout", "-q", NAME)


@pytest.mark.parametrize("purpose", ["build", "spec"])
def test_start_says_how_far_behind_the_base_the_change_is(tmp_path, capsys, purpose) -> None:
    """101 R1: the base branch and how many of its commits `HEAD` lacks, writing nothing."""
    root = _change(tmp_path, 2, "plan")
    _main_moves(root, "one.txt", "two.txt")
    status = _git(root, "status", "--porcelain")
    _, out = _run(capsys, factory.cmd_start, root, "008", purpose)
    assert (out["base"], out["behind"]) == ("main", 2), out
    assert _git(root, "status", "--porcelain") == status, "start writes nothing"
    _git(root, "merge", "-q", "--ff-only", "main")
    _, out = _run(capsys, factory.cmd_start, root, "008", purpose)
    assert (out["base"], out["behind"]) == ("main", 0)
    _git(root, "branch", "-q", "-m", "main", "trunk")
    _, out = _run(capsys, factory.cmd_start, root, "008", purpose)
    assert (out["base"], out["behind"]) == (None, None), "no base, no count"


def test_a_tier_1_spec_is_told_its_approach_is_the_spec(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, "plan")
    _, out = _run(capsys, factory.cmd_start, root, "008", "spec")
    assert any("Approach is the spec" in r for r in out["refusals"])


def test_start_refuses_outside_the_changes_own_worktree(tmp_path, capsys) -> None:
    root = _change(tmp_path, branch="main-ish")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 1 and "own worktree" in out["refusals"][0]
    code, out = _run(capsys, factory.cmd_start, _change(tmp_path / "b"), "9", "build")
    assert code == 1, "id 9 doesn't name 008-reopen-drafts"


# ---------------------------------------------------------------- stage


def test_stage_edits_only_the_two_lines(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    intent = root / ".sdlc" / "work" / NAME / "intent.md"
    before = intent.read_text(encoding="utf-8")
    code, out = _run(capsys, factory.cmd_stage, root, "008", "build")
    assert code == 0 and out["stage"] == "build"
    after = intent.read_text(encoding="utf-8")
    pairs = zip(before.splitlines(), after.splitlines(), strict=True)
    changed = [(a, b) for a, b in pairs if a != b]
    assert [a.split(":")[0] for a, _ in changed] == ["stage", "updated"]
    assert "id: 008" in after, "never round-tripped: 008 stays 008"
    code, out = _run(capsys, factory.cmd_stage, root, "008", "shipped")
    assert code == 1 and "plan, design, build, test" in out["refusals"][0]


# ---------------------------------------------------------------- verdicts and the loop


def _verdicts(root, capsys, head=None) -> dict:
    return _run(capsys, factory.cmd_verdicts, root, "008", head)[1]


def test_nothing_built_yet_is_a_build(tmp_path, capsys) -> None:
    out = _verdicts(_change(tmp_path), capsys)
    assert (out["next"], out["round"], out["built"]) == ("build", 1, 0)


def test_a_build_with_no_review_is_a_review_of_its_round(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("review", 1)
    assert out["missing"] == FULL


def test_an_incomplete_round_is_reviewed_again_for_the_missing(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == (
        "review",
        1,
        ["security", "test", "behaviour"],
    )


def test_changes_rework_until_the_rounds_run_out(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, security="CHANGES")
    assert (_verdicts(root, capsys)["next"], _verdicts(root, capsys)["round"]) == ("verify", 1)
    _verified(root, 1, kept=["security: security fix 1"])
    assert (_verdicts(root, capsys)["next"], _verdicts(root, capsys)["round"]) == ("rework", 1)
    # The step the first version got wrong: once the builder has reworked, round 2 is reviewed,
    # not reworked again.
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == ("review", 2, FULL)
    _round(root, 2, test="CHANGES")
    _verified(root, 2, kept=["test: test fix 2"])
    assert _verdicts(root, capsys)["next"] == "rework"
    _round(root, 3, test="CHANGES")
    _verified(root, 3, kept=["test: test fix 3"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["exhausted"]) == ("approve", 3, True)
    assert out["rounds"][2]["reviews"]["test"]["changes"] == ["test fix 3"]


def test_all_pass_goes_to_the_approver_then_done(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["exhausted"]) == ("approve", False)
    (root / ".sdlc" / "work" / NAME / "decision.md").write_text("DECISION: READY\n\nAll pass.\n")
    out = _verdicts(root, capsys)
    assert (out["next"], out["decision"]) == ("done", "READY")


def test_a_reply_without_a_verdict_stops_the_run(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1)
    _review(root, 1, "code", "Looks fine to me!")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and "round-1/code.md" in out["problems"][0]
    (root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "code.md").write_text(
        "VERDICT: PASS\n"
    )
    (root / ".sdlc" / "work" / NAME / "decision.md").write_text("Ship it\n")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and "decision.md" in out["problems"][0]


def test_work_on_an_answer_after_a_passing_round_is_reviewed(tmp_path, capsys) -> None:
    """A reviewer's decision in an otherwise passing round: the person answers, the builder acts
    on it, and that work is a new round to review, never straight to the approver."""
    root = _change(tmp_path)
    _round(root, 1)
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "code.md"
    review.write_text(review.read_text() + "- DECISION: [blocking] Soft delete or hard?\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    assert _verdicts(root, capsys)["next"] == "decide"
    ledger = root / ".sdlc" / "work" / NAME / "decisions.md"
    ledger.write_text(
        ledger.read_text().replace("- [ ] D1", "- [x] D1").replace("hard?", "hard? → decided: soft")
    )
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("review", 2)


def test_reviews_without_a_build_report_are_a_problem(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _review(root, 1, "code", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and "no build/round-1.md" in out["problems"][0]


def test_head_moving_stops_the_run(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    head = _git(root, "rev-parse", "--short", "HEAD")
    assert _verdicts(root, capsys, head)["next"] == "build"
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "an agent committed")
    out = _verdicts(root, capsys, head)
    assert out["next"] == "stop" and out["head_moved"] is True
    assert "no agent may commit" in out["problems"][0]


# ---------------------------------------------------------------- the stop record (085)


def _record(root, capsys, head: str) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_verdicts, root, "008", head, True)


def _stopped(root: Path) -> Path:
    return root / ".sdlc" / "work" / NAME / factory.STOPPED


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "--short", "HEAD")


@pytest.mark.portable
def test_record_writes_a_stop_and_removes_it_once_clear(tmp_path, capsys) -> None:
    """R1: a stopped reading leaves the record, a clear one takes it away."""
    root = _change(tmp_path)
    _round(root, 1)
    _review(root, 1, "code", "Looks fine to me!")
    code, out = _record(root, capsys, _head(root))
    assert code == 0 and out["next"] == "stop"
    assert _stopped(root).is_file(), "a stopped reading leaves no record"
    _review(root, 1, "code", "VERDICT: PASS")
    code, out = _record(root, capsys, _head(root))
    assert out["next"] == "approve" and not _stopped(root).exists(), "a clear reading keeps it"
    code, out = _record(root, capsys, _head(root))
    assert code == 0 and not _stopped(root).exists(), "removing what isn't there is fine"


@pytest.mark.portable
def test_the_record_is_verdicts_own_reading(tmp_path, capsys) -> None:
    """R2: every problem word for word, in its order, and the way the call named."""
    root = _change(tmp_path)
    _round(root, 1)
    _review(root, 1, "code", "Looks fine to me!")
    _review(root, 1, "test", "Also fine.\nwith a second line")
    (root / ".sdlc" / "work" / NAME / "decision.md").write_text("Ship it\n", encoding="utf-8")
    _, out = _record(root, capsys, _head(root))
    assert len(out["problems"]) == 3, out["problems"]
    lines = _stopped(root).read_text(encoding="utf-8").splitlines()
    assert lines[0] == f"STOPPED: {out['way']}"
    found = [m.group(1) for m in map(factory.PROBLEM_RE.match, lines) if m]
    assert found == out["problems"]
    assert _stopped(root).read_text(encoding="utf-8") == factory.stop_text(
        NAME, out["way"], out["problems"]
    )


@pytest.mark.portable
def test_a_problem_spanning_lines_is_one_line_of_the_record() -> None:
    text = factory.stop_text(NAME, "rerun", ["one\nproblem", "two"])
    assert [m.group(1) for m in map(factory.PROBLEM_RE.match, text.splitlines()) if m] == [
        "one problem",
        "two",
    ]
    assert factory.STOPPED_RE.match(text.splitlines()[0]).group(1) == "rerun"
    nxt = [m.group(1) for m in map(factory.NEXT_RE.match, text.splitlines()) if m]
    assert nxt == [factory.WAYS["rerun"].format(id="008")]


@pytest.mark.portable
def test_each_way_on_fits_two_lines_at_phone_width() -> None:
    """120 (2026-11-17-82): a stop's `NEXT:` is the command and a few words, two lines at most of
    a 390px card's 12px monospace, and still names the command that moves the run on; the longer
    sentence is `WAYS_WHY`'s, in the record's body."""
    assert set(factory.WAYS) == set(factory.WAYS_WHY) == {"ship", "mend", "rerun"}
    for way, text in factory.WAYS.items():
        line = text.format(id="008")
        assert len(line) <= 90, (way, len(line))
        assert "/sdlc:ship 008" in line, way
        assert way == "ship" or "/sdlc-factory:build 008" in line, way
        assert len(line) < len(factory.WAYS_WHY[way].format(id="008")), way
        # Round 1's ux: the person reads both, so neither says the factory's word for asking again.
        assert "mend" not in line and "mend" not in factory.WAYS_WHY[way], way


@pytest.mark.portable
def test_verdicts_alone_writes_nothing(tmp_path, capsys) -> None:
    """R3: without the flag the folder is left byte for byte, a record in it included."""
    root = _change(tmp_path)
    _round(root, 1)
    _review(root, 1, "code", "Looks fine to me!")
    record = _stopped(root)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("left as it was\n", encoding="utf-8")
    folder = root / ".sdlc" / "work" / NAME

    def tree() -> dict:
        return {p: p.read_bytes() for p in folder.rglob("*") if p.is_file()}

    before = tree()
    assert _verdicts(root, capsys, _head(root))["next"] == "stop"
    assert tree() == before, "a stopped reading wrote"
    _review(root, 1, "code", "VERDICT: PASS")
    before = tree()
    assert _verdicts(root, capsys, _head(root))["next"] == "approve"
    assert tree() == before


@pytest.mark.portable
def test_record_without_a_head_is_refused(tmp_path, capsys) -> None:
    """R3: a call that can't see a HEAD move never removes a HEAD-moved stop."""
    root = _change(tmp_path)
    code, out = _run(capsys, factory.cmd_verdicts, root, "008", None, True)
    assert code == 1 and "--head" in out["refusals"][0]
    assert not _stopped(root).exists()


@pytest.mark.portable
def test_a_stop_names_its_way(tmp_path, capsys) -> None:
    """R4: HEAD moved is ship, a missing evidence alone is mend, anything else is rerun."""
    root = _change(tmp_path / "verdict")
    _round(root, 1)
    _review(root, 1, "code", "Looks fine to me!")
    assert _verdicts(root, capsys)["way"] == "rerun"

    root = _change(tmp_path / "evidence")
    _report(root, 1, "Built it. The gate passed.\n")
    assert _verdicts(root, capsys)["way"] == "mend"
    _round(root, 1)
    _report(root, 1, "Built it. The gate passed.\n")
    behaviour = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "behaviour.md"
    behaviour.write_text("VERDICT: PASS\n\n## Notes\n\nIt ran fine.\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["way"], len(out["problems"])) == ("mend", 2)
    _review(root, 1, "code", "Looks fine to me!")
    assert _verdicts(root, capsys)["way"] == "rerun", "a missing evidence and another problem"

    root = _change(tmp_path / "moved")
    head = _head(root)
    _report(root, 1, "Built it.\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "an agent committed")
    _, out = _record(root, capsys, head)
    assert out["way"] == "ship"
    assert "/sdlc:ship 008" in _stopped(root).read_text(encoding="utf-8")

    assert "way" not in _verdicts(_change(tmp_path / "clear"), capsys), "only a stop has a way"


def test_a_third_red_gate_names_rerun(tmp_path, capsys) -> None:
    """R4, the fourth fixture: a third red gate in a round is fixed by its cause, then rerun."""
    root = _change(tmp_path)
    _gate_config(root, "exit 3")
    _build_report(root, 1)
    for _ in range(factory.GATE_FIXES):
        _gate(root, capsys)
        _fixed(root)
    _gate(root, capsys)
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun")


@pytest.mark.portable
def test_a_stale_record_never_stops_the_loop(tmp_path, capsys) -> None:
    """R5: the loop reads the rounds alone; the next recording call clears what was left."""
    root = _change(tmp_path)
    _build_report(root, 1)
    _stopped(root).parent.mkdir(parents=True, exist_ok=True)
    _stopped(root).write_text(factory.stop_text(NAME, "rerun", ["old"]), encoding="utf-8")
    assert _verdicts(root, capsys)["next"] == "review"
    _, out = _record(root, capsys, _head(root))
    assert out["next"] == "review" and not _stopped(root).exists()


@pytest.mark.portable
def test_the_supervisor_records_each_reading() -> None:
    """R14: the build skill's `verdicts` call records, and the skill never edits the record."""
    skill = (ROOT / "plugins" / "factory" / "skills" / "build" / "SKILL.md").read_text("utf-8")
    calls = [
        line
        for line in skill.splitlines()
        if "factory.py verdicts <" in line and not line.lstrip().startswith("- 'Bash(")
    ]
    assert calls and all("--head <head> --record" in line for line in calls), calls
    assert "runs/stopped.md" in skill


def test_carry_writes_the_unresolved_changes_to_notes_once(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, code="CHANGES", security="CHANGES")
    code, out = _run(capsys, factory.cmd_carry, root, "008")
    assert code == 0 and out["added"] == ["code: code fix 1", "security: security fix 1"]
    notes = (root / ".sdlc" / "work" / NAME / "notes.md").read_text(encoding="utf-8")
    assert "- [ ] code: code fix 1\n" in notes and "- [ ] security: security fix 1\n" in notes
    assert _run(capsys, factory.cmd_carry, root, "008")[1]["added"] == [], "never twice"
    items = sdlc.open_items(root / ".sdlc" / "work" / NAME)
    assert [i["text"] for i in items] == ["code: code fix 1", "security: security fix 1"]


# ---------------------------------------------------------------- decisions that are a person's


def test_decisions_reach_the_ledger_once_with_stable_ids(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [blocking] Keep drafts 30 days or forever? Recommend 30.\n")
    _review(root, 1, "security", "VERDICT: PASS", "")
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "security.md"
    review.write_text(review.read_text() + "- DECISION: [default] Log the draft id? Assuming no.\n")
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["added"] == ["D1", "D2"]
    assert (out["pending"], out["assumed"]) == (["D1"], ["D2"])
    ledger = (root / ".sdlc" / "work" / NAME / "decisions.md").read_text(encoding="utf-8")
    assert "- [ ] D1 (builder round 1, blocking): Keep drafts 30 days" in ledger
    assert "- [ ] D2 (security round 1, default): Log the draft id?" in ledger
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["added"] == [], "never twice"


def test_a_blocking_decision_pauses_the_run_until_the_person_answers(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [blocking] Keep drafts 30 days or forever?\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    out = _verdicts(root, capsys)
    assert (out["next"], out["pending"]) == ("decide", ["D1"])
    ledger = root / ".sdlc" / "work" / NAME / "decisions.md"
    ledger.write_text(
        ledger.read_text().replace(
            "- [ ] D1 (builder round 1, blocking): Keep drafts 30 days or forever?",
            "- [x] D1 (builder round 1, blocking): Keep drafts 30 days or forever?"
            " → decided: 30 days",
        )
    )
    out = _verdicts(root, capsys)
    assert out["next"] == "review" and out["pending"] == []
    [d1] = factory.read_ledger(root / ".sdlc" / "work" / NAME)
    assert (d1["decided"], d1["answer"], d1["text"]) == (
        True, "30 days", "Keep drafts 30 days or forever?"
    )  # fmt: skip


def test_a_default_decision_lets_the_run_go_on_as_assumed(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [default] Paginate at 50? Assuming 50.\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    _round(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["assumed"]) == ("approve", ["D1"])


def _ledger(root: Path) -> list[str]:
    return (
        (root / ".sdlc" / "work" / NAME / "decisions.md").read_text(encoding="utf-8").splitlines()
    )


def test_a_default_supersedes_an_earlier_one_once(tmp_path, capsys) -> None:
    """105 R5: a later default naming the one it replaces ticks that line, and only that line, as
    superseded; the new line keeps its own words; a rerun changes nothing."""
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [blocking] Keep drafts 30 days or forever?\n",
                  "- DECISION: [default] No badge on a shipped escalated card.\n")  # fmt: skip
    _review(root, 1, "code", "VERDICT: PASS")
    code_md = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "code.md"
    code_md.write_text(code_md.read_text() + "- DECISION: [default] Log the draft id? No.\n")
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["added"] == ["D1", "D2", "D3"]
    before = _ledger(root)
    _build_report(root, 2, "- DECISION: [default] (supersedes D2) Keep `was ESCALATE` on a card.\n")
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["added"] == ["D4"] and out["superseded"] == ["D2"], out
    assert out["unmarked"] == [] and out["assumed"] == ["D3", "D4"], out
    after = _ledger(root)
    assert after[:-1] == [
        line + " → superseded by D4" if " D2 " in line else line for line in
        [ln.replace("- [ ] D2", "- [x] D2") for ln in before]
    ], "only D2's line changes"  # fmt: skip
    assert after[-1] == "- [ ] D4 (builder round 2, default): Keep `was ESCALATE` on a card."
    d2 = next(d for d in factory.read_ledger(root / ".sdlc" / "work" / NAME) if d["id"] == "D2")
    assert (d2["superseded_by"], d2["decided"], d2["open"], d2["answer"]) == (
        "D4",
        False,
        False,
        None,
    )
    assert d2["text"] == "No badge on a shipped escalated card."
    _run(capsys, factory.cmd_decisions, root, "008")
    assert _ledger(root) == after, "a rerun marks nothing twice"


def test_a_default_can_supersede_one_raised_in_the_same_pass(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [default] Page at 50.\n",
                  "- DECISION: [default] (supersedes D1) Page at 100.\n")  # fmt: skip
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert (out["added"], out["superseded"], out["assumed"]) == (["D1", "D2"], ["D1"], ["D2"])
    assert _ledger(root)[-2:] == [
        "- [x] D1 (builder round 1, default): Page at 50. → superseded by D2",
        "- [ ] D2 (builder round 1, default): Page at 100.",
    ]


@pytest.mark.parametrize(
    "case, earlier, target, why",
    [
        ("missing", [], "D9", "no D9"),
        ("blocking", ["- DECISION: [blocking] Keep 30 days?\n"], "D1", "not a default"),
        ("decided", ["- DECISION: [default] Page at 50.\n"], "D1", "decided"),
        (
            "superseded",
            [
                "- DECISION: [default] Page at 50.\n",
                "- DECISION: [default] (supersedes D1) Page at 100.\n",
            ],
            "D1",
            "already superseded",
        ),  # fmt: skip
        ("itself", ["- DECISION: [default] Page at 50.\n"], "D2", "itself"),
    ],
)
def test_a_supersede_that_can_t_apply_marks_nothing(tmp_path, capsys, case, earlier, target, why):
    """105 R6: the new default is added, unmarked and listed with why; no line is marked."""
    root = _change(tmp_path)
    _build_report(root, 1, *earlier)
    _run(capsys, factory.cmd_decisions, root, "008")
    if case == "decided":
        path = root / ".sdlc" / "work" / NAME / "decisions.md"
        text = path.read_text().replace("- [ ] D1", "- [x] D1").replace("50.", "50. → decided: 50")
        path.write_text(text)
    before = _ledger(root) if earlier else []
    new_id = f"D{len(earlier) + 1}"
    _build_report(root, 2, f"- DECISION: [default] ({'supersedes'} {target}) Page at 25.\n")
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["added"] == [new_id] and out["superseded"] == [], out
    [unmarked] = out["unmarked"]
    assert (unmarked["id"], unmarked["supersedes"]) == (new_id, target)
    assert why in unmarked["why"], unmarked
    after = _ledger(root)
    assert after[: len(before)] == before, "no line is marked"
    assert after[-1] == f"- [ ] {new_id} (builder round 2, default): Page at 25."


def test_a_superseded_default_is_neither_assumed_nor_a_signal_nor_a_decision(
    tmp_path, capsys, monkeypatch
) -> None:
    """105 R7: only the default that replaced it is assumed; the landing sees no open decision once
    that one is decided, and `--decision` refuses the superseded id."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1, "- DECISION: [default] Page at 50.\n",
                  "- DECISION: [default] (supersedes D1) Page at 100.\n")  # fmt: skip
    _run(capsys, factory.cmd_decisions, root, "008")
    _round(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["assumed"], out["pending"]) == ("approve", ["D2"], [])
    code, out = _run(capsys, factory.cmd_agent, root, "008", "decided", None, "D1")
    assert code == 1 and "D1 isn't a decided line" in out["refusals"][0], out

    monkeypatch.setattr(factory, "_sdlc", lambda args, cwd: (0, {}, ""))
    cfg = factory.load_config(root)[0]
    open_signal = "decisions still open or assumed in decisions.md"
    assert open_signal in factory.landing.land_signals(folder, root, "READY", cfg)[0], (
        "D2 is assumed"
    )
    path = folder / "decisions.md"
    path.write_text(path.read_text().replace("- [ ] D2", "- [x] D2").replace(
        "Page at 100.", "Page at 100. → decided: 100"))  # fmt: skip
    assert open_signal not in factory.landing.land_signals(folder, root, "READY", cfg)[0], (
        "D1 isn't open"
    )
    assert factory.landing.land_parts(folder, {})["assumed"] == [], (
        "a superseded line isn't assumed"
    )


# ---------------------------------------------------------------- a default's alternatives

PAGING = (
    "- DECISION: [default] Page the drafts list at 50?\n"
    "  - OPTION: 50 — one screen's worth; long lists need a second page\n"
    "  - OPTION: 100 — fewer pages; a slower first paint\n"
    "  - WHY: the spec's list view shows 50\n"
)
PAGING_LEDGER = (
    "- [ ] D1 (builder round 1, default): Page the drafts list at 50?\n"
    "  - OPTION: 50 — one screen's worth; long lists need a second page\n"
    "  - OPTION: 100 — fewer pages; a slower first paint\n"
    "  - WHY: the spec's list view shows 50\n"
)


def _ledger_text(root: Path) -> str:
    return (root / ".sdlc" / "work" / NAME / "decisions.md").read_text(encoding="utf-8")


def test_a_defaults_alternatives_reach_the_ledger_under_its_line(tmp_path, capsys) -> None:
    """137 R1: the OPTION and WHY lines after a DECISION line are filed under its ledger line,
    indented two spaces, in the reply's order; the line after them is no part of it."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING, "Then the next slice.\n  - OPTION: stray — not a decision's\n")
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["added"] == ["D1"] and out["bare"] == [], out
    assert _ledger_text(root) == "# Decisions\n\n" + PAGING_LEDGER
    [d1] = out["decisions"]
    assert d1["options"] == [
        {"option": "50", "notes": "one screen's worth; long lists need a second page"},
        {"option": "100", "notes": "fewer pages; a slower first paint"},
    ]
    assert d1["why"] == "the spec's list view shows 50"


def test_a_ledger_without_alternatives_reads_as_before(tmp_path) -> None:
    """137 R2: a ledger written before alternatives existed gives the same records, plus the new
    fields, empty."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "decisions.md").write_text(
        "# Decisions\n\n- [ ] D1 (builder round 1, default): Page at 50.\n"
        "- [x] D2 (code round 1, blocking): Keep 30 days? → decided: 30 days\n",
        encoding="utf-8",
    )
    assert factory.read_ledger(folder) == [
        {"id": "D1", "source": "builder round 1", "kind": "default", "text": "Page at 50.",
         "decided": False, "open": True, "answer": None, "superseded_by": None,
         "settled": None, "options": [], "why": None, "current": True},
        {"id": "D2", "source": "code round 1", "kind": "blocking", "text": "Keep 30 days?",
         "decided": True, "open": False, "answer": "30 days", "superseded_by": None,
         "settled": None, "options": [], "why": None, "current": True},
    ]  # fmt: skip


def test_options_fill_a_bare_line_once(tmp_path, capsys) -> None:
    """137 R3: a later raise of the same text with options fills a bare line; a line that has
    options never gets more; a rerun changes no byte."""
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [default] Page the drafts list at 50?\n")
    out = _run(capsys, factory.cmd_decisions, root, "008")[1]
    assert out["bare"] == ["D1"], out
    _build_report(root, 2, PAGING)
    _build_report(root, 3, PAGING.replace("100 —", "25 —"))
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["bare"] == []
    assert _ledger_text(root) == "# Decisions\n\n" + PAGING_LEDGER
    _run(capsys, factory.cmd_decisions, root, "008")
    assert _ledger_text(root) == "# Decisions\n\n" + PAGING_LEDGER, "a rerun changes nothing"


# ---------------------------------------------------------------- the approver weighs defaults


def _decision(root: Path, *lines: str, head: str = "DECISION: ESCALATE") -> None:
    path = root / ".sdlc" / "work" / NAME / "decision.md"
    path.write_text(head + "\n\nWhy.\n\n" + "".join(lines), encoding="utf-8")


def test_the_approver_settles_one_default_and_escalates_another(tmp_path, capsys) -> None:
    """137 R6: a SETTLED default is ticked as the approver's, its sub-lines kept; an ESCALATED one
    stays open, its options filed from the approver's reply; `decision.md` is never edited."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING, "- DECISION: [default] Log the draft id? Assuming no.\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    _decision(
        root,
        "- SETTLED: D1: spec R4 shows 50 a page\n",
        "- ESCALATED: D2: logging is a policy call\n",
        "  - OPTION: no — nothing to leak; harder to trace\n",
        "  - OPTION: yes — easy to trace; the id is personal data\n",
        "  - WHY: the safer default\n",
    )
    shown = (root / ".sdlc" / "work" / NAME / "decision.md").read_bytes()
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["settled"] == ["D1"] and out["unsettled"] == [], out
    assert out["assumed"] == ["D2"] and out["bare"] == [], out
    assert _ledger_text(root).splitlines()[2:] == [
        "- [x] D1 (builder round 1, default): Page the drafts list at 50?"
        " → settled by the approver: spec R4 shows 50 a page",
        *PAGING_LEDGER.splitlines()[1:],
        "- [ ] D2 (builder round 1, default): Log the draft id? Assuming no.",
        "  - OPTION: no — nothing to leak; harder to trace",
        "  - OPTION: yes — easy to trace; the id is personal data",
        "  - WHY: the safer default",
    ]
    assert (root / ".sdlc" / "work" / NAME / "decision.md").read_bytes() == shown
    before = _ledger_text(root)
    again = _run(capsys, factory.cmd_decisions, root, "008")[1]
    assert (again["settled"], again["unsettled"]) == ([], []), again
    assert _ledger_text(root) == before, "a rerun changes nothing"


@pytest.mark.parametrize("case", ["blocking", "decided", "superseded", "unknown", "twice"])
def test_a_settle_that_cant_apply_marks_nothing(tmp_path, capsys, case) -> None:
    """137 R6: the approver never settles a blocking, decided, superseded or unknown line; the
    second of two settles for one id is refused; each refusal is listed with why."""
    root = _change(tmp_path)
    _build_report(root, 1, "- DECISION: [blocking] Keep drafts 30 days?\n",
                  "- DECISION: [default] Page at 50.\n",
                  "- DECISION: [default] (supersedes D2) Page at 100.\n",
                  "- DECISION: [default] Log the draft id?\n")  # fmt: skip
    _run(capsys, factory.cmd_decisions, root, "008")
    path = root / ".sdlc" / "work" / NAME / "decisions.md"
    path.write_text(path.read_text().replace("- [ ] D4", "- [x] D4").replace(
        "draft id?", "draft id? → decided: no"))  # fmt: skip
    target = {"blocking": "D1", "decided": "D4", "superseded": "D2", "unknown": "D9"}.get(
        case, "D3"
    )
    lines = [f"- SETTLED: {target}: the spec says so\n"]
    if case == "twice":
        lines.insert(0, "- ESCALATED: D3: the person's call\n")
    before = _ledger_text(root)
    _decision(root, *lines)
    out = _run(capsys, factory.cmd_decisions, root, "008")[1]
    assert out["settled"] == [] and _ledger_text(root) == before, out
    [refused] = out["unsettled"]
    assert refused["id"] == target and refused["why"], refused


def test_a_settled_default_is_not_the_persons_word(tmp_path, capsys) -> None:
    """137 R7: a settled line is neither open nor decided: `verdicts` doesn't count it assumed,
    `--decision` refuses it, and it is never an upgrade answer."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1, "- DECISION: [default] Page at 50.\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    _round(root, 1)
    _decision(root, "- SETTLED: D1: upgrade to Tier 2: the spec says 50\n", head="DECISION: READY")
    _run(capsys, factory.cmd_decisions, root, "008")
    [d1] = factory.read_ledger(folder)
    assert (d1["settled"], d1["decided"], d1["open"], d1["answer"]) == (
        "upgrade to Tier 2: the spec says 50", False, False, None
    )  # fmt: skip
    assert _verdicts(root, capsys)["assumed"] == []
    code, out = _run(capsys, factory.cmd_agent, root, "008", "decided", None, "D1")
    assert code == 1 and "D1 isn't a decided line" in out["refusals"][0], out
    assert factory.upgrade_answer([d1 | {"kind": "blocking"}]) is None


def test_the_approver_is_asked_to_weigh_each_open_default(tmp_path, capsys) -> None:
    """137 R5: the approve prompt names every open default by id, and both line shapes."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING, "- DECISION: [default] Log the draft id?\n",
                  "- DECISION: [blocking] Keep drafts 30 days?\n")  # fmt: skip
    _run(capsys, factory.cmd_decisions, root, "008")
    path = root / ".sdlc" / "work" / NAME / "decisions.md"
    path.write_text(path.read_text().replace("- [ ] D3", "- [x] D3").replace(
        "30 days?", "30 days? → decided: 30"))  # fmt: skip
    _round(root, 1)
    state, _ = factory.loop_state(root, "008", None)
    assert state["next"] == "approve", state
    prompt, target, _ = factory._task(root, root / ".sdlc" / "work" / NAME, state, "approve",
                                      "approver", None)  # fmt: skip
    assert target.name == "decision.md"
    assert "D1, D2" in prompt and "D3" not in prompt, prompt
    assert "- SETTLED: D<n>: " in prompt and "- ESCALATED: D<n>: " in prompt, prompt
    assert "no options yet: D2." in prompt, prompt


# ---------------------------------------------------------------- what the person decides (ask)


def _weighed(tmp_path: Path, capsys, stage: str = "test") -> Path:
    """A change the approver escalated with one default settled and one escalated, and a reviewer's
    blocking line still open."""
    root = _change(tmp_path, stage=stage)
    _build_report(root, 1, PAGING, "- DECISION: [default] Log the draft id? Assuming no.\n")
    _review(root, 1, "security", "VERDICT: PASS")
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "security.md"
    review.write_text(review.read_text() + "- DECISION: [blocking] Keep drafts 30 days?\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    _decision(root, "- ESCALATED: D1: the page size is the product's call\n",
              "- SETTLED: D2: spec R4 forbids logging ids\n")  # fmt: skip
    _run(capsys, factory.cmd_decisions, root, "008")
    return root


def _tree_bytes(root: Path) -> dict[str, bytes]:
    folder = root / ".sdlc" / "work" / NAME
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*")
            if p.is_file()}  # fmt: skip


def test_ask_lists_open_items_with_their_background_and_writes_nothing(tmp_path, capsys) -> None:
    """137 R13: every open line in id order with where it came from, its options and the
    approver's reason; the settled ones apart; no byte of the folder changes."""
    root = _weighed(tmp_path, capsys)
    before = _tree_bytes(root)
    code, out = _run(capsys, factory.cmd_ask, root, "008", None)
    assert code == 0 and out["decision"] == "ESCALATE", out
    assert out["items"] == [
        {"id": "D1", "kind": "default", "source": "builder round 1",
         "reply": "build/round-1.md", "question": "Page the drafts list at 50?",
         "options": [
             {"option": "50", "notes": "one screen's worth; long lists need a second page"},
             {"option": "100", "notes": "fewer pages; a slower first paint"},
         ],
         "why": "the spec's list view shows 50",
         "escalated": "the page size is the product's call"},
        {"id": "D3", "kind": "blocking", "source": "security round 1",
         "reply": "reviews/round-1/security.md", "question": "Keep drafts 30 days?",
         "options": [], "why": None, "escalated": None},
    ]  # fmt: skip
    assert out["settled"] == [
        {
            "id": "D2",
            "text": "Log the draft id? Assuming no.",
            "reason": "spec R4 forbids logging ids",
        }
    ]
    assert "next" not in out
    assert _tree_bytes(root) == before, "ask writes nothing"


@pytest.mark.parametrize("stage", ["build", "design", "shipped"])
def test_ask_refuses_a_change_not_at_test(tmp_path, capsys, stage) -> None:
    """137 R13: a run still building asks its own blocking decisions, through the supervisor."""
    root = _weighed(tmp_path, capsys, stage=stage)
    code, out = _run(capsys, factory.cmd_ask, root, "008", None)
    assert code == 1 and "stage: test" in out["refusals"][0], out


def _answer(root: Path, ident: str, answer: str) -> None:
    path = root / ".sdlc" / "work" / NAME / "decisions.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines = [
        "- [x]" + ln[5:] + factory.DECIDED + answer if ln.startswith(f"- [ ] {ident} ") else ln
        for ln in lines
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_ask_says_rebuild_when_an_answer_overturns_a_default(tmp_path, capsys) -> None:
    """137 R14: with a line open, `decide`; once all are answered, an answer that isn't the kept
    default means a rebuild, by `build` for an ESCALATE and by ship for a READY."""
    root = _weighed(tmp_path, capsys)
    _answer(root, "D1", factory.KEPT_ANSWER)
    out = _run(capsys, factory.cmd_ask, root, "008", "D1")[1]
    assert out["next"] == "decide", out
    _answer(root, "D3", "forever")
    out = _run(capsys, factory.cmd_ask, root, "008", "D1,D3")[1]
    assert out["next"] == "rebuild" and out["then"] == "/sdlc-factory:build 008", out
    path = root / ".sdlc" / "work" / NAME / "decision.md"
    path.write_text(path.read_text().replace("DECISION: ESCALATE", "DECISION: READY"))
    out = _run(capsys, factory.cmd_ask, root, "008", "D1,D3")[1]
    assert out["next"] == "rebuild" and out["then"] == "/sdlc:ship 008", out


def test_ask_says_ship_when_every_default_is_kept(tmp_path, capsys) -> None:
    """137 R14: every answer keeps the default: ship. An id that isn't a decided line is refused."""
    root = _change(tmp_path, stage="test")
    _build_report(root, 1, PAGING)
    _run(capsys, factory.cmd_decisions, root, "008")
    _decision(root, "- ESCALATED: D1: the product's call\n")
    code, out = _run(capsys, factory.cmd_ask, root, "008", "D1")
    assert code == 1 and "D1 isn't a decided line" in out["refusals"][0], out
    _answer(root, "D1", factory.KEPT_ANSWER)
    code, out = _run(capsys, factory.cmd_ask, root, "008", "D1")
    assert code == 0 and out["items"] == [] and out["next"] == "ship", out
    code, out = _run(capsys, factory.cmd_ask, root, "008", "D1,D7")
    assert code == 1 and "D7 isn't a decided line" in out["refusals"][0], out


# ---------------------------------------------------------------- sdlc reads it like any other


def test_sdlc_reads_a_factory_built_change_like_any_other(tmp_path) -> None:
    root = _change(tmp_path, stage="test")
    _round(root, 1)
    _build_report(root, 1, "- DECISION: [default] Paginate at 50? Assuming 50.\n")
    assert factory.cmd_decisions(root, "008") == 0, "a ledger in the folder too"
    (root / ".sdlc" / "work" / NAME / "decision.md").write_text("DECISION: READY\n\nAll pass.\n")
    a = sdlc.analyze(root)
    assert a["problems"] == []
    [rec] = a["changes"]
    assert (rec["id"], rec["tier"], rec["stage"], rec["impact"]) == ("008", 2, "test", "minor")
    assert rec["unfilled"] == [] and rec["undone"] == []
    # Shipped and closed the way close leaves it, the outer loops read it unchanged.
    intent = root / ".sdlc" / "work" / NAME / "intent.md"
    intent.write_text(intent.read_text().replace("stage: test", "stage: shipped"))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "ship 008")
    _git(root, "rm", "-r", "-q", f".sdlc/work/{NAME}")
    _git(root, "commit", "-q", "-m", f"Close {NAME}")
    _git(root, "branch", "-q", "-f", "main", "HEAD")
    [closed] = sdlc.closed_changes(root, None, "main")
    assert (closed["name"], closed["impact"], closed["problems"]) == (NAME, "minor", [])


# ---------------------------------------------------------------- verified rework


def test_a_change_is_verified_before_any_rework(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, code="CHANGES", security="CHANGES")
    assert _verdicts(root, capsys)["next"] == "verify"
    _verified(root, 1, kept=["code: code fix 1"], dropped=["security: security fix 1"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("rework", 1)
    verified = out["rounds"][0]["verified"]
    assert verified["kept"] == [{"role": "code", "change": "code fix 1"}]
    assert verified["dropped"] == [
        {"role": "security", "change": "security fix 1", "why": "not in the code"}
    ]


def test_a_round_whose_changes_are_all_dropped_goes_to_the_approver(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, code="CHANGES")
    _verified(root, 1, dropped=["code: code fix 1"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["exhausted"]) == ("approve", False)


@pytest.mark.parametrize(
    "kept, dropped, problem",
    [
        ([], [], "answers code: code fix 1 0 times, not once"),
        (["code: code fix 1"], ["code: code fix 1"], "answers code: code fix 1 2 times"),
        (["code: code fix 1", "test: made up"], [], "test: made up, which no review"),
    ],
)
def test_every_change_is_answered_exactly_once(tmp_path, capsys, kept, dropped, problem) -> None:
    root = _change(tmp_path)
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=kept, dropped=dropped)
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and any(problem in p for p in out["problems"]), out["problems"]


def test_the_verify_prompt_numbers_each_change_once(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "test", "VERDICT: CHANGES", "src/a.py:1: test it", "src/a.py:1: test it")
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:2: name it", "src/b.py:3: split it")
    _review(root, 1, "security", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS", "src/c.py:4: not asked, the verdict passed")
    folder = root / ".sdlc" / "work" / NAME
    state, _ = factory.loop_state(root, "008", None)
    prompt, target, _ = factory._task(root, folder, state, "verify", "verifier", None)
    listed = [line for line in prompt.splitlines() if line.startswith("- ")]
    assert listed == [
        "- C1: code: src/a.py:2: name it",
        "- C2: code: src/b.py:3: split it",
        "- C3: test: src/a.py:1: test it",
    ]
    assert target.name == "verified.md"


def test_the_landings_verify_prompt_numbers_as_its_read_does(tmp_path) -> None:
    """The landing's prompt and `land-verdicts`' read number one set of changes: the `CHANGES`
    verdicts' lines, in `REVIEWERS` order, whatever order the files are found in."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    land = folder / "reviews" / "land-1"
    land.mkdir(parents=True)
    texts = {
        "test": "VERDICT: CHANGES\n- CHANGE: src/a.py:1: test it\n",
        "behaviour": "VERDICT: PASS\n- CHANGE: src/c.py:4: not asked\n",
        "code": "VERDICT: CHANGES\n- CHANGE: src/a.py:2: name it\n",
    }
    for role, text in texts.items():
        (land / f"{role}.md").write_text(text, encoding="utf-8")
    prompt, _, _ = factory._land_task(root, folder, "land-verify", "verifier")
    listed = [line for line in prompt.splitlines() if line.startswith("- ")]
    assert listed == ["- C1: code: src/a.py:2: name it", "- C2: test: src/a.py:1: test it"]
    (land / "verified.md").write_text("- KEPT: code: C1: x\n- DROPPED: test: C2: y — z\n")
    reviews = {
        role: {"verdict": t.split()[1], "changes": [t.split("CHANGE: ")[1].strip()]}
        for role, t in texts.items()
    }
    verified, problems = factory.read_verified(land / "verified.md", 1, reviews)
    assert problems == [] and verified["kept"] == [
        {"role": "code", "change": "src/a.py:2: name it"}
    ]


def test_an_answer_by_id_takes_the_reviewers_text(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:2: name it", "src/b.py:3: split it")
    for role in ("security", "test", "behaviour"):
        _review(root, 1, role, "VERDICT: PASS")
    folder = root / ".sdlc" / "work" / NAME / "reviews" / "round-1"
    (folder / "verified.md").write_text(
        "- KEPT: code: C2: the function does two things\n"
        "- DROPPED: code: C1: a rename — the name is the module's own\n",
        encoding="utf-8",
    )
    out = _verdicts(root, capsys)
    assert out["problems"] == [] and (out["next"], out["round"]) == ("rework", 1)
    verified = out["rounds"][0]["verified"]
    assert verified["kept"] == [{"role": "code", "change": "src/b.py:3: split it"}]
    assert verified["dropped"] == [
        {"role": "code", "change": "src/a.py:2: name it", "why": "the name is the module's own"}
    ]
    _, carried = _run(capsys, factory.cmd_carry, root, "008")
    assert carried["added"] == ["code: src/b.py:3: split it"]
    state, _ = factory.loop_state(root, "008", None)
    prompt, _, _ = factory._task(
        root, root / ".sdlc" / "work" / NAME, state, "rework", "builder", None
    )
    assert "- code: src/b.py:3: split it" in prompt, "the builder gets the reviewer's words"
    assert "two things" not in prompt and "name it" not in prompt


def test_an_answer_in_its_own_words_resolves_by_its_lead(tmp_path, capsys) -> None:
    """A round as the factory's first real run wrote it: one change, dropped, the verifier's
    summary of it in place of the reviewer's two sentences. Its files, as they are."""
    root = _change(tmp_path)
    _build_report(root, 1)
    for role in ("security", "test", "behaviour"):
        _review(root, 1, role, "VERDICT: PASS")
    folder = root / ".sdlc" / "work" / NAME / "reviews" / "round-1"
    for name in ("code.md", "verified.md"):
        text = (ROOT / "tests" / "fixtures" / "verified-in-own-words" / name).read_text()
        (folder / name).write_text(text, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert out["problems"] == [] and out["next"] == "approve", out["problems"]
    verified = out["rounds"][0]["verified"]
    asked = out["rounds"][0]["reviews"]["code"]["changes"]
    assert verified["kept"] == [] and [d["change"] for d in verified["dropped"]] == asked
    assert verified["dropped"][0]["why"].startswith("The attribution matches the history.")


@pytest.mark.parametrize(
    "answers, problem",
    [
        (["KEPT: code: C9: made up"], "answers code: C9, which no change of round 1 is"),
        (["KEPT: test: C1: wrong role"], "answers test: C1, which is code's change, not test's"),
        (["KEPT: code: src/a.py:9: reworded"], "src/a.py:9: reworded, which no review of round 1"),
        (["KEPT: code: src/b.py:3: reworded"], "whose lead src/b.py:3 2 of code's changes"),
        (["KEPT: code: C1: once", "DROPPED: code: src/a.py:2: name it — no"], "name it 2 times"),
    ],
)
def test_an_answer_that_names_no_one_change_is_a_stop(tmp_path, capsys, answers, problem) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(
        root, 1, "code", "VERDICT: CHANGES",
        "src/a.py:2: name it", "src/b.py:3: split it", "src/b.py:3: and test it",
    )  # fmt: skip
    for role in ("security", "test", "behaviour"):
        _review(root, 1, role, "VERDICT: PASS")
    folder = root / ".sdlc" / "work" / NAME / "reviews" / "round-1"
    (folder / "verified.md").write_text("".join(f"- {a}\n" for a in answers), encoding="utf-8")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and any(problem in p for p in out["problems"]), out["problems"]
    assert any("0 times, not once" in p for p in out["problems"]), "the rest go unanswered"


def test_carry_takes_the_kept_changes_and_the_pre_existing_problems(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, code="CHANGES", security="CHANGES")
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "test.md"
    review.write_text(review.read_text() + "- PREEXISTING: src/old.py:3: an unclosed file\n")
    _verified(root, 1, kept=["code: code fix 1"], dropped=["security: security fix 1"])
    _, out = _run(capsys, factory.cmd_carry, root, "008")
    assert out["added"] == ["code: code fix 1", "pre-existing: src/old.py:3: an unclosed file"]


@pytest.mark.parametrize(
    ("role", "text", "found"),
    [
        ("code", "[context] docs/a.md:3: old flag", ("context", "docs/a.md:3: old flag")),
        ("code", "[cost] src/a.py:1: one caller", ("cost", "src/a.py:1: one caller")),
        ("security", "[correctness] src/a.py:2: wrong", ("correctness", "src/a.py:2: wrong")),
        ("code", "src/a.py:1: no tag", ("correctness", "src/a.py:1: no tag")),
        ("security", "src/a.py:1: no tag", ("contract", "src/a.py:1: no tag")),
        ("test", "[style] src/a.py:1: unknown", ("correctness", "[style] src/a.py:1: unknown")),
        ("security", "[style] src/a.py:1: unknown", ("contract", "[style] src/a.py:1: unknown")),
    ],
)  # fmt: skip
def test_a_finding_takes_its_tagged_pass_else_its_roles(role, text, found) -> None:
    """A line may open with one of the four passes; otherwise, or with any other tag left in its
    text, its role's: `security` is contract, every other reviewer correctness."""
    assert factory.finding_pass(role, text) == found
    if not text.startswith("[style]"):
        assert factory._change_path(text) == found[1].split(":", 1)[0], "a tag is no path"
    assert factory.CHANGE_RE.pattern == r"^\s*- CHANGE:\s*(.+?)\s*$", "unchanged"


def test_nits_are_read_and_never_verified(tmp_path, capsys) -> None:
    """A reviewer's `- NIT:` lines are read apart from its changes: they never make a verdict
    CHANGES, never reach the verifier and are never reworked."""
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:2: name it")
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "code.md"
    review.write_text(review.read_text() + "- NIT: src/a.py:9: a long line\n")
    _review(root, 1, "security", "VERDICT: PASS")
    sec = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "security.md"
    sec.write_text(sec.read_text() + "- NIT: [cost] src/b.py:1: a helper with one caller\n")
    for role in ("test", "behaviour"):
        _review(root, 1, role, "VERDICT: PASS")
    folder = root / ".sdlc" / "work" / NAME
    [r1], problems = factory.read_rounds(folder, FULL)
    assert problems == []
    assert r1["reviews"]["code"]["changes"] == ["src/a.py:2: name it"]
    unweighed = {"theme": None, "cost": None, "value": None}
    assert r1["reviews"]["code"]["nits"] == [{"text": "src/a.py:9: a long line", **unweighed}]
    assert r1["reviews"]["security"] == {
        "verdict": "PASS", "changes": [], "preexisting": [],
        "nits": [{"text": "[cost] src/b.py:1: a helper with one caller", **unweighed}],
    }  # fmt: skip
    state, _ = factory.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "verify", "verifier", None)
    assert "a long line" not in prompt and "one caller" not in prompt
    assert [line for line in prompt.splitlines() if line.startswith("- ")] == [
        "- C1: code: src/a.py:2: name it"
    ]


def test_a_nit_is_read_with_its_weights(tmp_path) -> None:
    """129 R1: a nit's trailing `{theme cost value}` is read as its weights and taken off its
    text; a line without them, or with words the rubric doesn't have, is read as it is."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: PASS")
    review = folder / "reviews" / "round-1" / "code.md"
    review.write_text(
        review.read_text()
        + "- NIT: src/a.py:9: a long line {style S low}\n"
        + "- NIT: [cost] src/b.py:1: one caller  {refactor M med}  \n"
        + "- NIT: src/c.py:2: no weights\n"
        + "- NIT: src/d.py:3: odd {style XL low}\n"
    )
    [r1], problems = factory.read_rounds(folder, ["code"])
    assert problems == []
    assert r1["reviews"]["code"]["nits"] == [
        {"text": "src/a.py:9: a long line", "theme": "style", "cost": "S", "value": "low"},
        {"text": "[cost] src/b.py:1: one caller", "theme": "refactor", "cost": "M",
         "value": "med"},
        {"text": "src/c.py:2: no weights", "theme": None, "cost": None, "value": None},
        {"text": "src/d.py:3: odd {style XL low}", "theme": None, "cost": None, "value": None},
    ]  # fmt: skip


def test_the_nit_words_are_sdlcs() -> None:
    """129: the cost and value words a filed nit may hold are copies of `sdlc.py`'s."""
    assert factory.NIT_COSTS == sdlc.NIT_COSTS
    assert factory.NIT_VALUES == sdlc.NIT_VALUES


def _two_rounds(root: Path) -> Path:
    """Two reviewed rounds: kept, dropped, pre-existing and nit lines, and a kept change round 2
    asks for again word for word."""
    folder = root / ".sdlc" / "work" / NAME
    for n in (1, 2):
        _build_report(root, n)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:1: fix a",
            "[context] docs/x.md:3: says the old flag")  # fmt: skip
    _review(root, 1, "security", "VERDICT: CHANGES", "src/b.py:2: escape it")
    _review(root, 1, "test", "VERDICT: PASS")
    test = folder / "reviews" / "round-1" / "test.md"
    test.write_text(
        test.read_text()
        + "- PREEXISTING: src/old.py:3: an unclosed file\n- NIT: src/a.py:9: a long line\n"
    )
    _review(root, 1, "behaviour", "VERDICT: PASS")
    _verified(root, 1,
              kept=["code: src/a.py:1: fix a", "code: [context] docs/x.md:3: says the old flag"],
              dropped=["security: src/b.py:2: escape it"])  # fmt: skip
    _review(root, 2, "code", "VERDICT: CHANGES", "[context] docs/x.md:3: says the old flag")
    for role in ("security", "test", "behaviour"):
        _review(root, 2, role, "VERDICT: PASS")
    _verified(root, 2, kept=["code: [context] docs/x.md:3: says the old flag"])
    return folder


def test_carry_writes_each_agent_finding_once_by_its_role(tmp_path, capsys) -> None:
    """114 R7: every distinct finding of every complete round, once, by its role, ranked and
    disposed by what became of it, in a findings.md core reads with no problem."""
    root = _change(tmp_path)
    folder = _two_rounds(root)
    test2 = folder / "reviews" / "round-2" / "test.md"
    test2.write_text(test2.read_text() + "- NIT: src/t.py:4: a vague name {tests M low}\n")
    code, out = _run(capsys, factory.cmd_carry, root, "008")
    assert code == 0 and out["findings"] == 6
    text = (folder / "findings.md").read_text(encoding="utf-8")
    assert text.startswith(factory.FINDINGS_HEAD)
    found = sdlc.findings_entries(folder)
    assert found["problems"] == [] and found["open"] == [] and found["fix"] == []
    rows = [(e["id"], e["rank"], e["pass"], e["disposition"], e["by"], e["evidence"], e["class"])
            for e in found["entries"]]  # fmt: skip
    assert rows == [
        ("F1", "important", "correctness", "fixed", "code", "src/a.py:1", "code review, round 1"),
        ("F2", "important", "context", "recorded", "code", "docs/x.md:3", "code review, round 1"),
        ("F3", "important", "contract", "wrong", "security", "src/b.py:2",
         "security review, round 1"),
        ("F4", "preexisting", "correctness", "recorded", "test", "src/old.py:3",
         "test review, round 1"),
        ("F5", "nit", "correctness", "minor", "test", "src/a.py:9", "test review, round 1"),
        ("F6", "nit", "correctness", "recorded", "test", "src/t.py:4", "test review, round 2"),
    ]  # fmt: skip
    entries = found["entries"]
    assert entries[2]["reason"] == "not in the code"
    assert entries[4]["reason"] == "raised by an agent; not weighed or filed"
    assert text.count("says the old flag") == 2, "its heading and body once: round 2 repeats it"
    # 129 R7: a nit to file carries its weights, which core's parser passes over.
    f6 = text.split("## F6.", 1)[1]
    assert "Disposition: recorded\nTheme: tests\nCost: M\nValue: low\nBy: test\n" in f6
    assert "{tests M low}" not in text, "the weights are read off the nit's text"
    assert "Theme:" not in text.split("## F6.", 1)[0], "only a nit to file has them"
    assert sdlc.findings_trailer(entries).endswith(" agents=6 passes=0 passes_wrong=0")
    assert "fixed=0" in sdlc.findings_trailer(entries), "an agent's nit is never ship's count"


def _nits(root: Path, n: int, role: str, *nits: str) -> None:
    """Add `- NIT:` lines to round `n`'s `role` review."""
    path = root / ".sdlc" / "work" / NAME / "reviews" / f"round-{n}" / f"{role}.md"
    path.write_text(path.read_text() + "".join(f"- NIT: {x}\n" for x in nits))


def _reworked(root: Path, *nits: str) -> Path:
    """Round 1: code asks for a change the verifier keeps and raises `nits`; round 2, the rework,
    every reviewer passes and raises none."""
    _round(root, 1, code="CHANGES")
    _nits(root, 1, "code", *nits)
    _verified(root, 1, kept=["code: code fix 1"])
    _round(root, 2)
    return root / ".sdlc" / "work" / NAME


def _rows(folder: Path) -> list[tuple]:
    found = sdlc.findings_entries(folder)
    assert found["problems"] == [], found["problems"]
    return [(e["rank"], e["disposition"], e["evidence"], e["reason"]) for e in found["entries"]]


def test_carry_disposes_each_nit_by_its_weights(tmp_path, capsys) -> None:
    """129 R2: the script, never a model, turns each nit's weights into its disposition: `S` with
    `med` handed to the rework and not raised again is fixed, any other `S`/`M` with `med`/`low`
    recorded to file, `high` value an important finding and `L` cost an idea, both carried to
    notes.md, and a nit without weights minor, as before."""
    root = _change(tmp_path)
    folder = _reworked(
        root,
        "src/a.py:1: cheap and worth it {style S med}",
        "src/b.py:2: rename it {refactor M low}",
        "src/c.py:3: users hit it {robustness S high}",
        "src/d.py:4: rethink the module {design L med}",
        "src/e.py:5: no weights",
    )
    code, out = _run(capsys, factory.cmd_carry, root, "008")
    assert code == 0
    assert _rows(folder) == [
        ("important", "fixed", "reviews/round-1/code.md", None),
        ("nit", "fixed", "src/a.py:1", factory.HANDED_REASON),
        ("nit", "recorded", "src/b.py:2", None),
        ("important", "recorded", "src/c.py:3", factory.HIGH_REASON),
        ("nit", "recorded", "src/d.py:4", factory.IDEA_REASON),
        ("nit", "minor", "src/e.py:5", factory.NIT_REASON),
    ]  # fmt: skip
    assert out["added"] == [
        "code: src/c.py:3: users hit it",
        "code: src/d.py:4: rethink the module",
    ]
    notes = (folder / "notes.md").read_text(encoding="utf-8")
    assert "- [ ] code: src/c.py:3: users hit it\n" in notes and "{" not in notes
    filed = [i["file"]["text"] for i in factory.agent_findings(_carried_rounds(root)) if i["file"]]
    assert filed == ["src/b.py:2: rename it"], "only an S/M, med/low nit is filed"


def _carried_rounds(root: Path) -> list[dict]:
    cfg, _ = factory.load_config(root)
    return factory._rounds_at_depth(root, root / ".sdlc" / "work" / NAME, cfg)[0]


def test_carry_never_leaves_a_fix_for_ship_to_refuse(tmp_path, capsys) -> None:
    """129 R3: a cheap nit no rework was handed, or one the round after the rework raises again,
    is recorded to file, so `sdlc.py ship` never finds an agent's `fix` or `open`."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    _nits(root, 1, "code", "src/a.py:1: cheap {style S med}")
    _run(capsys, factory.cmd_carry, root, "008")
    found = sdlc.findings_entries(folder)
    assert (found["fix"], found["open"]) == ([], [])
    assert _rows(folder) == [("nit", "recorded", "src/a.py:1", None)], "never handed on"

    root = _change(tmp_path / "again")
    folder = _reworked(root, "src/a.py:1: cheap {style S med}")
    _nits(root, 2, "code", "src/a.py:1: cheap {style S med}")
    _run(capsys, factory.cmd_carry, root, "008")
    found = sdlc.findings_entries(folder)
    assert (found["fix"], found["open"]) == ([], [])
    assert _rows(folder)[1] == ("nit", "recorded", "src/a.py:1", None), "raised again: not made"


def test_a_nit_not_raised_again_is_still_filed(tmp_path, capsys) -> None:
    """129 R5: only a cheap nit handed to the builder is fixed by a later round's silence; one
    recorded, or a cheap one a restart's first round never handed on, is still filed."""
    root = _change(tmp_path)
    folder = _reworked(root, "src/b.py:2: rename it {refactor M low}")
    _run(capsys, factory.cmd_carry, root, "008")
    assert _rows(folder)[1] == ("nit", "recorded", "src/b.py:2", None)

    rounds = _carried_rounds(root)
    rounds[0]["reviews"]["code"]["nits"] = [factory.read_nit("src/a.py:1: cheap {style S med}")]
    assert [i["disposition"] for i in factory.agent_findings(rounds) if i["rank"] == "nit"] == [
        "fixed"
    ]
    rounds[1]["start"] = True
    assert [i["disposition"] for i in factory.agent_findings(rounds) if i["rank"] == "nit"] == [
        "recorded"
    ], "a restart's first round was handed nothing"


def test_a_landing_round_never_changes_the_nits_filed(tmp_path, capsys) -> None:
    """129, at its landing: only the build's rounds are weighed, since the landing files its nits
    before a landing round reaches the record. A landing round that raises a handed cheap nit again
    leaves it fixed, and a nit only a landing round raised is minor, never one to file."""
    root = _change(tmp_path)
    _reworked(root, "src/a.py:1: cheap {style S med}", "src/b.py:2: rename it {refactor M low}")
    rounds = _carried_rounds(root)

    def nits(rs: list[dict]) -> list[tuple]:
        found = factory.agent_findings(rs)
        return [(i["text"], i["disposition"], bool(i["file"])) for i in found if i["rank"] == "nit"]

    before = nits(rounds)
    assert before == [
        ("src/a.py:1: cheap", "fixed", False),
        ("src/b.py:2: rename it", "recorded", True),
    ]
    land = copy.deepcopy(rounds[-1])
    land.update(kind="land", round=1)
    land["reviews"]["code"]["nits"] = [
        factory.read_nit(x)
        for x in ("src/a.py:1: cheap {style S med}", "src/c.py:3: landing only {style M low}")
    ]
    assert nits([*rounds, land]) == [*before, ("src/c.py:3: landing only", "minor", False)]


def test_carry_caps_the_nits_it_files_at_five(tmp_path, capsys) -> None:
    """129 R6: a change files at most five nits, the first five in order; past them, and any nit
    that names no path, is minor, with why."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    _nits(root, 1, "code", "src/a1.py:1: one {style M low}", "the names are long {style M low}",
          *(f"src/a{i}.py:{i}: number {i} {{style M low}}" for i in range(2, 6)))  # fmt: skip
    _nits(root, 1, "test", "tests/t.py:1: six {tests S low}", "tests/u.py:2: seven {tests M med}")
    _run(capsys, factory.cmd_carry, root, "008")
    rows = _rows(folder)
    assert [r[1] for r in rows] == ["recorded", "minor", *["recorded"] * 4, "minor", "minor"]
    assert rows[1][3] == factory.NO_PATH_REASON
    assert rows[6][3] == rows[7][3] == factory.CAP_REASON
    assert factory.CAP_REASON == "past the cap of 5 nits a change files"
    assert factory.NO_PATH_REASON == "names no path, so it can't be filed as a nit"


def test_rework_hands_the_builder_its_cheap_nits(tmp_path, capsys) -> None:
    """129 R4: a rework round N lists round N's `S` `med` nits after its kept changes, in the
    reviewers' words; round N+1's review names to each role the ones it raised, to raise again any
    the rework didn't make."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    _nits(root, 1, "code", "src/a.py:1: cheap {style S med}", "src/b.py:2: later {style M low}")
    _nits(root, 1, "test", "[cost] tests/t.py:3: one fixture {tests S med}")
    _verified(root, 1, kept=["code: code fix 1"])
    state, _ = factory.loop_state(root, "008", None)
    assert state["next"] == "rework"
    assert state["handed"] == [
        {"role": "code", "text": "src/a.py:1: cheap"},
        {"role": "test", "text": "[cost] tests/t.py:3: one fixture"},
    ]
    prompt, _, _ = factory._task(root, folder, state, "rework", "builder", None)
    assert prompt.endswith(
        "- code: code fix 1\nAlso make these nits, each weighed cheap and worth it:\n"
        "- code: src/a.py:1: cheap\n- test: [cost] tests/t.py:3: one fixture\n\n"
        + factory.check_line(folder)
    )
    assert "later" not in prompt, "an M nit is filed, never handed on"
    _build_report(root, 2)
    state, _ = factory.loop_state(root, "008", None)
    assert (state["next"], state["round"]) == ("review", 2)
    prompt, _, _ = factory._task(root, folder, state, "review", "code", None)
    assert (
        " Nits handed to the builder last round: src/a.py:1: cheap; raise again, word for word "
        "with its weights, any the rework didn't make." in prompt
    )
    prompt, _, _ = factory._task(root, folder, state, "review", "security", None)
    assert "Nits handed" not in prompt, "security raised none"


def test_a_round_with_only_nits_is_never_reworked(tmp_path, capsys) -> None:
    """129 R4: cheap nits and no kept change go to the approver, never to a rework; and a
    restart's first round starts fresh, handed nothing."""
    root = _change(tmp_path)
    _round(root, 1)
    _nits(root, 1, "code", "src/a.py:1: cheap {style S med}")
    state, _ = factory.loop_state(root, "008", None)
    assert (state["next"], state["handed"]) == ("approve", [])
    assert all(r["verdict"] == "PASS" for r in state["rounds"][0]["reviews"].values())

    root = _change(tmp_path / "restarted", 2, "test")
    _escalated(root)
    _nits(root, 3, "code", "src/a.py:1: cheap {style S med}")
    assert _restart(root, capsys)[0] == 0
    _build_report(root, 4)
    state, _ = factory.loop_state(root, "008", None)
    assert (state["next"], state["round"], state["handed"]) == ("review", 4, [])


def test_carry_with_no_complete_round_writes_the_note_alone(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:1: fix a")
    _run(capsys, factory.cmd_carry, root, "008")
    assert (folder / "findings.md").read_text(encoding="utf-8") == factory.FINDINGS_HEAD
    assert sdlc.findings_entries(folder)["problems"] == []


def test_carry_rewrites_only_the_agents_findings(tmp_path, capsys) -> None:
    """114 R8: a rerun replaces only the sections a factory role raised, keeps the note's lines
    and every other section as written, numbers its own after the highest it kept, and changes no
    byte when nothing is new."""
    root = _change(tmp_path)
    folder = _two_rounds(root)
    ship = (
        "## F1. [important] [correctness] Ship's own\n\nEvidence: src/a.py:4\nClass: logic\n"
        "Disposition: fixed\n"
    )
    path = folder / "findings.md"
    path.write_text(factory.FINDINGS_HEAD + "Fresh review: skipped, no Agent tool\n\n" + ship)
    _run(capsys, factory.cmd_carry, root, "008")
    once = path.read_text(encoding="utf-8")
    assert "Fresh review: skipped, no Agent tool\n" in once and ship in once
    ids = [(e["id"], e["by"]) for e in sdlc.findings_entries(folder)["entries"]]
    assert ids == [("F1", None), ("F2", "code"), ("F3", "code"), ("F4", "security"),
                   ("F5", "test"), ("F6", "test")]  # fmt: skip
    _run(capsys, factory.cmd_carry, root, "008")
    assert path.read_text(encoding="utf-8") == once, "a rerun with nothing new is the same bytes"
    fresh = ship.replace("F1.", "F9.").replace("Ship's own", "A fresh one") + "By: fresh\n"
    path.write_text(once.rstrip("\n") + "\n\n" + fresh)
    _run(capsys, factory.cmd_carry, root, "008")
    ids = [(e["id"], e["by"]) for e in sdlc.findings_entries(folder)["entries"]]
    assert ids[:2] == [("F1", None), ("F9", "fresh")]
    assert [i for i, _ in ids[2:]] == ["F10", "F11", "F12", "F13", "F14"]
    assert factory.FINDINGS_HEAD + "Fresh review: skipped" in path.read_text(encoding="utf-8")


def test_an_exhausted_run_must_escalate_and_ask_to_reconsider(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    for n in (1, 2, 3):
        _round(root, n, code="CHANGES")
        _verified(root, n, kept=[f"code: code fix {n}"])
    assert _verdicts(root, capsys)["exhausted"] is True
    decision = root / ".sdlc" / "work" / NAME / "decision.md"
    decision.write_text("DECISION: READY\n\nClose enough.\n")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and "Reconsider the approach" in out["problems"][0]
    decision.write_text("DECISION: ESCALATE\n\nStuck.\n")
    assert _verdicts(root, capsys)["next"] == "stop", "an ESCALATE without the section too"
    decision.write_text("DECISION: ESCALATE\n\nStuck.\n\n## Reconsider the approach\n\nSplit it.\n")
    assert _verdicts(root, capsys)["next"] == "done"


def _kept_again(root: Path, rounds: int = 2, change: str = "src/a.py:1: rename a") -> Path:
    """`rounds` full rounds whose code reviewer asks for `change` each time and the verifier keeps
    it, the rest passing."""
    for n in range(1, rounds + 1):
        _build_report(root, n)
        _review(root, n, "code", "VERDICT: CHANGES", change)
        for role in ("security", "test", "behaviour"):
            _review(root, n, role, "VERDICT: PASS")
        _verified(root, n, kept=[f"code: {change}"])
    return root / ".sdlc" / "work" / NAME


def test_a_change_kept_twice_escalates_before_the_rounds_run_out(tmp_path, capsys) -> None:
    """136 R3: the verifier keeping the same `(role, change)` in two rounds of one run means a
    further round won't move it: round 2 of 3 goes to the approver, `exhausted` and `stuck` set,
    and only an ESCALATE with its section will do."""
    folder = _kept_again(_change(tmp_path))
    out = _verdicts(tmp_path / "repo", capsys)
    assert (out["next"], out["round"], out["limit"]) == ("approve", 2, 3), out
    assert out["exhausted"] is True and out["stuck"] == ["code: src/a.py:1: rename a"]
    (folder / "decision.md").write_text("DECISION: READY\n\nClose enough.\n")
    out = _verdicts(tmp_path / "repo", capsys)
    assert out["next"] == "stop" and "Reconsider the approach" in out["problems"][0]
    (folder / "decision.md").write_text(RECONSIDERED)
    assert _verdicts(tmp_path / "repo", capsys)["next"] == "done"
    # A different change kept in round 2 is a rework, as before.
    root = _change(tmp_path / "other")
    _kept_again(root, 1)
    _build_report(root, 2)
    _review(root, 2, "code", "VERDICT: CHANGES", "src/a.py:2: another")
    for role in ("security", "test", "behaviour"):
        _review(root, 2, role, "VERDICT: PASS")
    _verified(root, 2, kept=["code: src/a.py:2: another"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["stuck"], out["exhausted"]) == ("rework", [], False)
    # A restart between the two starts a fresh run: its first round never repeats the old one's.
    root = _change(tmp_path / "restarted")
    folder = _kept_again(root, 2)
    (folder / "decision-1.md").write_text(RECONSIDERED)
    (folder / "build" / "round-2.restart.md").write_text("RESTART: decision-1.md\n")
    out = _verdicts(root, capsys)
    assert (out["next"], out["stuck"]) == ("rework", []), out
    # A round before with no `verified.md` kept nothing, so the same change is kept once.
    root = _change(tmp_path / "unverified")
    (_kept_again(root) / "reviews" / "round-1" / "verified.md").unlink()
    out = _verdicts(root, capsys)
    assert (out["next"], out["stuck"]) == ("rework", []), out


def test_an_untestable_requirement_escalates_after_its_round(tmp_path, capsys) -> None:
    """136 R5: a builder report saying a requirement can't be tested sends its round, once
    reviewed and verified, to the approver with rounds left, `exhausted` set, kept changes or
    none."""
    line = "R4: the drawer reads well: judged by eye, no test can show it"
    root = _change(tmp_path)
    _build_report(root, 1, f"- UNTESTABLE: {line}\n")
    _round(root, 1, code="CHANGES")
    assert _verdicts(root, capsys)["next"] == "verify", "verified first, as any round is"
    _verified(root, 1, kept=["code: code fix 1"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["exhausted"]) == ("approve", 1, True), out
    assert out["untestable"] == [line] and out["stuck"] == []
    root = _change(tmp_path / "passed")
    _build_report(root, 1, f"- UNTESTABLE: {line}\n")
    _round(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["exhausted"], out["untestable"]) == ("approve", True, [line])


EMPTY_UNTESTABLE = ("none", "none.", "None", "NONE.", "n/a", "N/A.", "na")


def test_an_empty_untestable_answer_is_no_requirement(tmp_path, capsys) -> None:
    """166: a builder writing `- UNTESTABLE: none` (any case, `n/a`, with or without a period)
    names no untestable requirement, so `verdicts` doesn't stop on it; a real one still stops."""
    for n, empty in enumerate(EMPTY_UNTESTABLE):
        root = _change(tmp_path / str(n))
        _build_report(root, 1, f"- UNTESTABLE: {empty}\n")
        _round(root, 1)
        out = _verdicts(root, capsys)
        assert (out["untestable"], out["exhausted"]) == ([], False), (empty, out)
    root = _change(tmp_path / "real")
    _build_report(root, 1, "- UNTESTABLE: R3 needs a live GitHub\n")
    _round(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["exhausted"]) == ("approve", True), out
    assert out["untestable"] == ["R3 needs a live GitHub"]
    for word in ("nonetheless", "none of R3 can run here", "n/a: R2 needs a live service"):
        assert factory.UNTESTABLE_RE.match(f"- UNTESTABLE: {word}"), "only an empty answer"


NEXT_STEP = (
    "Under `## Reconsider the approach`, name the next step you'd take: a requirement to "
    "rewrite, a model to try, or an approach to change."
)


def test_an_early_escalation_names_its_reason_to_the_approver(tmp_path, capsys) -> None:
    """136 R7: an approver sent a run that stopped early is told why, the repeated changes or the
    untestable lines, and asked to name its next step; a run with nothing kept is asked neither."""
    folder = _kept_again(_change(tmp_path))
    root = tmp_path / "repo"
    state, _ = factory.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "approve", "approver", None)
    assert (
        " Round 2 kept again what round 1 kept: code: src/a.py:1: rename a; nothing a further "
        "round does will change it." in prompt
    ), prompt
    assert NEXT_STEP in prompt
    line = "R4: the drawer reads well: judged by eye"
    root = _change(tmp_path / "untestable")
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1, f"- UNTESTABLE: {line}\n")
    _round(root, 1)
    state, _ = factory.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "approve", "approver", None)
    assert f" The builder reports these requirements can't be tested: {line}." in prompt, prompt
    assert NEXT_STEP in prompt and "kept again" not in prompt
    root = _change(tmp_path / "plain")
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    state, _ = factory.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "approve", "approver", None)
    assert NEXT_STEP not in prompt and "can't be tested" not in prompt


REASK = (
    "A kept change the rework didn't make, raise again word for word, as the prompt quotes it: the "
    "run tells a change kept twice by its words, and stops for the person rather than rework it a "
    "third time."
)


def test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word(tmp_path, capsys) -> None:
    """136 R4: round N+1's reviewers are told to raise again, word for word, a change kept last
    round that the rework didn't make, so the run can tell one kept twice; each reviewer's own
    prompt says the same, in the same sentence."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=["code: code fix 1"])
    _build_report(root, 2)
    (folder / "build" / "round-1.files").write_text("", encoding="utf-8")
    (folder / "build" / "round-2.files").write_text("", encoding="utf-8")
    state, _ = factory.loop_state(root, "008", None)
    assert (state["next"], state["round"]) == ("review", 2), state
    prompt, _, _ = factory._task(root, folder, state, "review", "code", None)
    assert "Kept last round: code: code fix 1." in prompt
    assert (
        " Raise again, word for word, any change kept last round that the rework didn't make."
        in prompt
    ), prompt
    for role in factory.REVIEWERS:
        text = (ROOT / "plugins" / "factory" / "agents" / f"reviewer-{role}.md").read_text("utf-8")
        assert REASK in " ".join(text.split()).split("## Later rounds")[1], role


# ---------------------------------------------------------------- rounds that converge


def test_a_snapshot_says_what_the_rework_changed(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("a = 1\n")
    (root / "src" / "b.py").write_text("b = 1\n")
    _build_report(root, 1)
    code, out = _run(capsys, factory.cmd_snapshot, root, "008", 1)
    assert code == 0 and out["paths"] == 2
    assert _verdicts(root, capsys)["reworked"] == ["src/a.py", "src/b.py"], "round 1: all of it"
    snap = (root / ".sdlc" / "work" / NAME / "build" / "round-1.files").read_text()
    assert ".sdlc/work" not in snap, "the change's own folder is never a reworked path"
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=["code: code fix 1"])
    (root / "src" / "b.py").write_text("b = 2\n")
    (root / "src" / "c.py").write_text("c = 1\n")
    _build_report(root, 2)
    _run(capsys, factory.cmd_snapshot, root, "008", 2)
    assert _verdicts(root, capsys)["reworked"] == ["src/b.py", "src/c.py"]
    assert not (root / ".git" / "refs" / "stash").exists(), "never a stash"


def test_a_round_without_its_snapshot_is_reviewed_whole(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    assert _verdicts(root, capsys)["reworked"] is None


def test_what_earlier_rounds_answered_is_settled_and_a_repeat_is_named(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("a = 1\n")
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:1: rename a", "src/a.py:1: add a doc")
    _review(root, 1, "security", "VERDICT: PASS")
    _review(root, 1, "test", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS")
    _verified(root, 1, kept=["code: src/a.py:1: rename a"], dropped=["code: src/a.py:1: add a doc"])
    _build_report(root, 2)
    _review(root, 2, "code", "VERDICT: CHANGES", "src/a.py:1: add a doc", "README.md:1: old")
    _review(root, 2, "security", "VERDICT: PASS")
    _review(root, 2, "test", "VERDICT: PASS")
    _review(root, 2, "behaviour", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert out["next"] == "verify"
    assert out["settled"] == ["code: src/a.py:1: add a doc", "code: src/a.py:1: rename a"]
    assert out["repeats"] == ["code: src/a.py:1: add a doc"]
    assert out["untouched"] == ["code: README.md:1: old"], "pre-existing, never reworked"


def test_a_change_asking_for_a_new_file_is_never_pre_existing(tmp_path, capsys) -> None:
    """The test reviewer's usual ask names a file that doesn't exist yet: the change is to create
    it, so it reaches the verifier as any other, never as pre-existing."""
    root = _change(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("a = 1\n")
    _build_report(root, 1)
    asks = ("tests/test_new.py: add a test for R4", "README.md:1: stale", "src/a.py:1: rename")
    _review(root, 1, "test", "VERDICT: CHANGES", *asks)
    _review(root, 1, "code", "VERDICT: PASS")
    _review(root, 1, "security", "VERDICT: PASS")
    assert _verdicts(root, capsys)["untouched"] == ["test: README.md:1: stale"]


def test_a_changes_verdict_with_nothing_to_change_stops_the_run(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop" and "lists no - CHANGE: line" in out["problems"][0]


# ---------------------------------------------------------------- depth set by risk

LISTED = '[review]\nsensitive = ["src/secret/"]\n'


def _touch(root: Path, path: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text("x\n")


def test_with_no_sensitive_list_every_run_is_full(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("full", FULL, 3)


def test_a_diff_touching_no_sensitive_path_runs_light(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, config=LISTED)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("light", ["code", "behaviour"], 2)
    _review(root, 1, "code", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS")
    assert _verdicts(root, capsys)["next"] == "approve", "light's reviewers complete the round"


def test_a_sensitive_path_deepens_the_run_and_it_never_lightens(tmp_path, capsys) -> None:
    root = _change(tmp_path, config=LISTED)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:1: move it")
    _verified(root, 1, kept=["code: src/a.py:1: move it"])
    _touch(root, "src/secret/key.py")
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["sensitive"]) == ("full", ["src/secret/key.py"])
    assert out["missing"] == FULL and out["limit"] == 3
    for role in ("code", "security", "test"):
        _review(root, 2, role, "VERDICT: PASS")
    (root / "src" / "secret" / "key.py").unlink()
    out = _verdicts(root, capsys)
    assert out["depth"] == "full" and "never lightens" in out["why"]


def test_the_sensitive_list_is_the_base_branch_s_not_the_change_s(tmp_path, capsys) -> None:
    root = _change(tmp_path, config=LISTED)
    (root / ".sdlc" / "config.toml").write_text('[review]\nsensitive = ["src/"]\n')
    _touch(root, "src/a.py")
    _build_report(root, 1)
    assert _verdicts(root, capsys)["depth"] == "light", "editing the list here changes nothing"


def test_the_landing_code_is_reviewed_in_depth(tmp_path, capsys) -> None:
    """153 R10: this repo's own `[review] sensitive` names `closing.py` and `landing.py`, so a
    diff touching either runs full depth, while one elsewhere in `sdlc.py` or `factory.py` stays
    light; and ship's `risk_paths()` names the same two modules and not the scripts."""
    import tomllib

    listed = tomllib.loads((ROOT / ".sdlc" / "config.toml").read_text(encoding="utf-8"))
    sensitive = listed["review"]["sensitive"]
    config = "[review]\nsensitive = " + json.dumps(sensitive) + "\n"
    closing, landing = "scripts/closing.py", "plugins/factory/scripts/landing.py"
    scripts = ["scripts/sdlc.py", "plugins/factory/scripts/factory.py"]
    for path in (closing, landing, *scripts):
        assert (ROOT / path).exists(), path
    for n, path in enumerate((closing, landing)):
        root = _change(tmp_path / f"module-{n}", config=config)
        _touch(root, path)
        _build_report(root, 1)
        out = _verdicts(root, capsys)
        assert out["depth"] == "full" and path in out["sensitive"], (path, out)
    for n, path in enumerate(scripts):
        root = _change(tmp_path / f"script-{n}", config=config)
        _touch(root, path)
        _build_report(root, 1)
        out = _verdicts(root, capsys)
        assert out["depth"] == "light" and not out["sensitive"], (path, out)
    risky = sdlc.risk_paths([closing, landing, *scripts], sensitive)
    assert risky == [closing, landing], risky


def _light_round(tmp_path: Path, tier: object, factory_toml: str | None = None) -> Path:
    """A change at `tier` whose first build touches no sensitive path, with no review yet."""
    root = _change(tmp_path, tier, "build", config=LISTED)
    if factory_toml is not None:
        (root / ".sdlc" / "factory.toml").write_text(factory_toml, encoding="utf-8")
    _touch(root, "src/a.py")
    _build_report(root, 1)
    return root


def _on_base(root: Path, factory_toml: str) -> None:
    """`factory_toml` committed on the base branch too, where `[models]` and the rest of what
    shapes a run are read from, and left in the change's checkout as it was."""
    config = root / ".sdlc" / "factory.toml"
    _git(root, "checkout", "-q", "main")
    config.write_text(factory_toml, encoding="utf-8")
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "factory.toml")
    _git(root, "checkout", "-q", NAME)
    config.write_text(factory_toml, encoding="utf-8")


def test_a_tier_2_light_round_includes_the_test_reviewer(tmp_path, capsys) -> None:
    """R1, R2, R3, R7: a Tier 2's light rounds expect the test reviewer; a Tier 1's, or one whose
    tier won't read, don't; `start` names the same list for the run's one question."""
    both = ["code", "behaviour"]
    for tier, want in ((2, ["code", "test", "behaviour"]), (1, both), ("", both)):
        root = _light_round(tmp_path / f"tier-{tier or 'none'}", tier)
        out = _verdicts(root, capsys)
        assert (out["depth"], out["missing"], out["limit"]) == ("light", want, 2), tier
        _, start = _run(capsys, factory.cmd_start, root, "008", "build")
        assert start["light"]["reviewers"] == want and start["light"]["chosen"] is False, tier
    root = tmp_path / "tier-2" / "repo"
    _review(root, 1, "code", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert (out["next"], out["missing"]) == ("review", ["test"]), "code alone is incomplete"
    _review(root, 1, "test", "VERDICT: PASS")
    assert _verdicts(root, capsys)["next"] == "approve"


def test_a_set_light_list_is_kept_at_either_tier(tmp_path, capsys) -> None:
    """R4, R5: a host's own `[light] reviewers` is used as set, and the Tier 2 default adds
    `test` only when the full depth runs it."""
    root = _light_round(tmp_path / "set", 2, '[light]\nreviewers = ["code"]\n')
    assert _verdicts(root, capsys)["missing"] == ["code"], "a list set by hand is kept"
    cfg = factory.load_config(root)[0]
    assert cfg["light"]["chosen"] is True
    assert factory.light_reviewers(cfg, 2) == factory.light_reviewers(cfg, 1) == ["code"]
    root = _light_round(tmp_path / "no-test", 2, 'reviewers = ["code", "security"]\n')
    assert _verdicts(root, capsys)["missing"] == ["code"], "never a reviewer the full depth lacks"


def test_a_light_round_includes_the_behaviour_reviewer(tmp_path, capsys) -> None:
    """136 R1: unset, `[light]` runs `behaviour` beside `code` at either tier, as the landing's
    own first check does, so a Tier 1 light round isn't complete without it."""
    root = _light_round(tmp_path, 1)
    cfg = factory.load_config(root)[0]
    assert factory.light_reviewers(cfg, 1) == ["code", "behaviour"]
    assert factory.light_reviewers(cfg, 2) == ["code", "test", "behaviour"], "REVIEWERS order"
    _review(root, 1, "code", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert (out["next"], out["missing"]) == ("review", ["behaviour"]), "code alone is incomplete"
    _review(root, 1, "behaviour", "VERDICT: PASS")
    assert _verdicts(root, capsys)["next"] == "approve"


def test_the_behaviour_reviewer_never_deepens_a_light_run(tmp_path, capsys) -> None:
    """136 R1: a light round holding `behaviour` keeps a Tier 1 run light into its next round."""
    root = _light_round(tmp_path, 1)
    for role in ("code", "behaviour"):
        _review(root, 1, role, "VERDICT: CHANGES", f"src/a.py:1: {role} fix")
    _verified(root, 1, kept=["code: src/a.py:1: code fix", "behaviour: src/a.py:1: behaviour fix"])
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("light", ["code", "behaviour"], 2)


def test_the_test_reviewer_never_deepens_a_tier_2_light_run(tmp_path, capsys) -> None:
    """R6: a Tier 2 light round holding `code`, `test` and `behaviour` keeps the run light."""
    root = _light_round(tmp_path, 2)
    for role in ("code", "test", "behaviour"):
        _review(root, 1, role, "VERDICT: CHANGES", f"src/a.py:1: {role} fix")
    _verified(root, 1, kept=[f"{r}: src/a.py:1: {r} fix" for r in ("code", "test", "behaviour")])
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    want = ["code", "test", "behaviour"]
    assert (out["depth"], out["missing"], out["limit"]) == ("light", want, 2), out


def test_readme_names_the_light_reviewers_and_models() -> None:
    """136 R6: the README's rule for a Tier 1 light run says the reviewers `light_reviewers()`
    gives and the model `model_for()` gives each scaled reviewer, and gives its reasons."""
    text = " ".join((ROOT / "plugins" / "factory" / "README.md").read_text("utf-8").split())
    cfg = factory.load_config(Path("/nonexistent"))[0]
    light = factory._listed(factory.light_reviewers(cfg, 1))
    assert f"a Tier 1's light rounds run the {light} reviewers" in text, light
    models = {factory.model_for(r, cfg, 1, "light") for r in factory.SCALED}
    assert len(models) == 1, models
    (model,) = models
    assert f"Each reviewer runs on {model} at either depth and tier" in text, model
    assert f"Every scaled reviewer runs on {model}**" in text
    # The table under "Why these defaults" (changes 124, 125, 129 and 131) is history, not a rule:
    # no test can read it, so it is checked by hand against each change's `Close` commit.
    assert "### Why these defaults" in text and "Landing catches: k of n" in text


def test_a_host_s_own_depth_and_models_are_kept(tmp_path, capsys) -> None:
    """136 R9: a host that set `rounds`, `[light]` and `[models]` gets what it set from `start`:
    no default this change moved reaches it, at either tier."""
    own = (
        'reviewers = ["code", "security", "test", "behaviour"]\nrounds = 4\n'
        '[light]\nreviewers = ["code"]\nrounds = 1\n'
        '[models]\ncode = "haiku"\nbehaviour = "haiku"\ntest = "opus"\n'
    )
    for tier in (1, 2):
        root = _light_round(tmp_path / f"tier-{tier}", tier, own)
        _on_base(root, own)
        _, out = _run(capsys, factory.cmd_start, root, "008", "build")
        assert (out["reviewers"], out["rounds"]) == (FULL, 4), tier
        assert out["light"] == {"reviewers": ["code"], "rounds": 1, "chosen": True}, tier
        for level in ("light", "full"):
            models = out["models_at"][level]
            assert (models["code"], models["behaviour"], models["test"]) == (
                "haiku", "haiku", "opus"), (tier, level)  # fmt: skip
        assert out["max_runs"] == 2 + 4 * (4 + 2 + 2), tier
        assert _verdicts(root, capsys)["missing"] == ["code"], tier


def test_the_landing_review_judges_a_tier_2_light_run_with_its_test_reviewer(
    tmp_path, capsys
) -> None:
    """R8: after a resolved conflict, the landing review asks for the same tier's reviewers."""
    root = _light_round(tmp_path, 2)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "reviews" / "land-1").mkdir(parents=True)
    (folder / "runs").mkdir()
    (folder / "runs" / "land-resolved").write_text("", encoding="utf-8")
    _, out = _run(capsys, factory.landing.cmd_land_verdicts, root, "008")
    assert out["missing"] == ["code", "test", "behaviour"], out


def _report(root: Path, n: int, text: str) -> None:
    """A builder report written as-is, evidence or not."""
    folder = root / ".sdlc" / "work" / NAME / "build"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"round-{n}.md").write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "text, problem",
    [
        ("Built it. The gate passed.\n", "has no `## Evidence` section"),
        ("Built it.\n\n## Evidence\n\nAll green.\n", "shows no command run"),
        ("Built.\n\n## Evidence\n\n$ ./check.sh\n12 passed\n$ pytest\nexit: 0\n", "`./check.sh`"),
        ("Built.\n\n## Evidence\n\n$ ./check.sh\n12 passed\n\n## Notes\n\nexit: 0\n", "no `exit:`"),
        (
            "Built.\n\n## Evidence\n\n$ uv run pytest -q | grep passed\n12 passed\n",
            "`uv run pytest -q | grep passed` has no `exit:`",
        ),
    ],
)
def test_a_builder_report_without_its_evidence_stops_the_run(
    tmp_path, capsys, text: str, problem: str
) -> None:
    root = _change(tmp_path)
    _report(root, 1, text)
    out = _verdicts(root, capsys)
    assert out["next"] == "stop"
    assert any("build/round-1.md" in p and problem in p for p in out["problems"]), out["problems"]


# 123 R1: what the script can tell changes nothing, and what it can't.
READS = [
    "cat plan.md",
    "grep -n x a ; grep -n x b ; cmp a b",
    "git -C . show HEAD:a",
    "sed -n '1,5p' f",
    "jq '.a | .b' f.json",
    "awk '$2 > 0 {print $1}' f",
    "awk -F, -v n=2 '{print $n}' f",
    "cat a 2>&1",
    "rg -n x src",
    "file x",
    "file -b -m magic x",
    "git diff",
    "git diff --text --no-ext-diff --no-textconv",
    "git log -p --exit-code",
    "git log --format='%H %s'",
    "git show HEAD",
    "git log --no-show-signature -1",
]
NON_READS = [
    "./check.sh",
    "uv run pytest -q | grep passed",
    "sed -i s/a/b/ f",
    "cat a > b",
    "cat $(x)",
    "find . -delete",
    "git diff --output=f",
    "tee f",
    "xargs rm",
    "X=1 cat f",
    "jq . f > g",
    "awk '{print > \"out\"}' f",
    "awk '{print | \"sh\"}' f",
    "awk 'BEGIN{system(\"rm f\")}'",
    "awk -i inplace '{print}' f",
    "awk -f prog.awk f",
    "awk 'BEGIN{system (\"rm f\")}'",
    "cat a >2",
    "cat a > 2",
    "echo hi >> 1",
    "cat a 2>1",
    "cat a &>1",
    "rg --pre ./x y",
    "rg --pre=./x y",
    "rg --pre-glob '*.gz' --pre ./x y",
    "file -C -m magic",
    "file -bC -m magic",
    "file --compile -m magic",
    "file --comp -m magic",
    "git diff --ext-diff",
    "git log -p --ext",
    "git show --textconv HEAD:a",
    "git -C . blame --textc a",
    "git cat-file --textconv HEAD:a",
    "git -c diff.external=./x diff",
    "git log --show-signature",
    "git show --show-signature HEAD",
    "git -C . log -1 --show-signature --oneline",
    "git log --format=%G?",
    "git log --pretty=format:'%h %GS'",
    "git log --pretty=tformat:%GK",
    "git show -s --format='%GG' HEAD",
    "git shortlog --format=%GS",
    "git log --format %G?",
    "git log --pretty %GF",
    "git -c log.showSignature=true log",
]


@pytest.mark.portable
def test_a_read_is_only_what_the_script_can_tell_changes_nothing() -> None:
    """123 R1: `is_read()` passes only the closed allowlist, judged stage by stage; anything it
    can't see into, or that writes, redirects or runs something else, is not a read."""
    wrong = [c for c in READS if not factory.is_read(c)]
    wrong += [c for c in NON_READS if factory.is_read(c)]
    assert not wrong, wrong


@pytest.mark.portable
def test_a_read_showing_its_output_needs_no_exit() -> None:
    """123 R2: a read followed by a non-blank, non-fence line owes no `exit:`, fenced or not."""
    plain = "## Evidence\n\n$ cat plan.md\n# Plan\n$ grep -n x a ; cmp a b\n3:x\n"
    fenced = "## Evidence\n\n```\n$ git -C . show HEAD:a\nline\n```\n"
    assert factory.read_evidence(plain, "r") == []
    assert factory.read_evidence(fenced, "r") == []


@pytest.mark.portable
def test_a_read_naming_a_mark_is_still_a_read() -> None:
    """135: a filed reply names this machine's paths by `<home>` and `<path-to-clone>`, whose `<`
    and `>` are words there, never redirects: a read naming one owes no `exit:`, as the path it
    replaced didn't. A real redirect beside a mark still makes it a non-read."""
    for mark in (factory.HOME_MARK, factory.CLONE_MARK):
        command = f"ls {mark}/.nvm/bin"
        assert factory.is_read(command), command
        text = f"## Evidence\n\n$ {command}\nnode\n"
        assert factory.read_evidence(text, "r") == [], text
        assert not factory.is_read(f"cat {mark}/a > {mark}/b")
        assert not factory.is_read(f"cat {mark}/a >out")


@pytest.mark.portable
def test_a_silent_read_still_needs_its_exit() -> None:
    """123 R3: a read that prints nothing, before the next `$` or the end, a fence or a blank line
    all it shows, still owes its exit: the exit is its only result."""
    for text in (
        "## Evidence\n\n$ cmp a b\n$ ./check.sh\n1 passed\nexit: 0\n",
        "## Evidence\n\n```\n$ cmp a b\n\n```\n",
    ):
        assert factory.read_evidence(text, "r") == ["r: `cmp a b` has no `exit:` line"], text


@pytest.mark.portable
def test_evidence_citing_the_gate_record_is_a_read() -> None:
    """155 R10: a reviewer's evidence may cite the gate's record by reading it, which owes no
    exit; a run of `factory.py check` is a command like any other, and owes its own."""
    record = ".sdlc/work/008-reopen-drafts/build/round-1.gate.md"
    for cite in (f"cat {record}", f"head -n 3 {record}"):
        text = f"## Evidence\n\n$ {cite}\nGATE: PASS\n"
        assert factory.read_evidence(text, "r") == [], cite
    run = "uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 008"
    assert factory.read_evidence(f"## Evidence\n\n$ {run}\n12 passed\n", "r") == [
        f"r: `{run}` has no `exit:` line"
    ]


def test_a_builders_read_needs_no_exit(tmp_path, capsys) -> None:
    """123 R6: the builder's report goes through the same parser: its gate shows its exit, a read
    after it shows only its output, and the run goes on to review."""
    root = _change(tmp_path)
    evidence = "$ ./check.sh\n12 passed\nexit: 0\n$ cat plan.md\n# Plan\n"
    _report(root, 1, f"Built.\n\n## Evidence\n\n{evidence}")
    out = _verdicts(root, capsys)
    assert (out["next"], out["problems"]) == ("review", []), out


def test_a_report_showing_each_command_and_its_exit_goes_on(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    fenced = "```\n$ ./check.sh\n12 passed\nexit: 0\n$ uv run pytest -q\n3 failed\nexit: 1\n```\n"
    _report(root, 1, f"Built.\n\n## Evidence\n\n{fenced}")
    out = _verdicts(root, capsys)
    assert (out["next"], out["problems"]) == ("review", []), "a failing exit is evidence too"


def test_only_the_newest_report_owes_evidence(tmp_path, capsys) -> None:
    """A run started before the rule keeps its old reports; the next one is checked."""
    root = _change(tmp_path)
    _report(root, 1, "Built before evidence was asked for.\n")
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=["code: code fix 1"])
    _build_report(root, 2)
    assert _verdicts(root, capsys)["next"] == "review"


def test_the_behaviour_check_owes_evidence_too(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1)
    reply = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "behaviour.md"
    reply.write_text("VERDICT: PASS\n\n## Notes\n\nIt ran fine.\n")
    out = _verdicts(root, capsys)
    assert out["next"] == "stop"
    assert any("reviews/round-1/behaviour.md" in p for p in out["problems"]), out["problems"]


def test_a_host_s_own_reviewers_are_kept_and_behaviour_is_one_it_can_name(tmp_path) -> None:
    (tmp_path / ".sdlc").mkdir()
    config = tmp_path / ".sdlc" / "factory.toml"
    config.write_text('reviewers = ["code", "test"]\n', encoding="utf-8")
    assert factory.load_config(tmp_path)[0]["reviewers"] == ["code", "test"]
    config.write_text('reviewers = ["behaviour"]\n', encoding="utf-8")
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["reviewers"] == ["behaviour"] and warnings == []
    assert factory.max_runs(factory.load_config(tmp_path / "none")[0]) == 26


@pytest.mark.parametrize(
    "patterns",
    [["src/secret/"], ["*.toml"], ["check.sh", ".claude/*"], ["src/*/key.py"], []],
)
def test_the_risk_matcher_is_sdlc_s_own(patterns: list[str]) -> None:
    paths = ["src/secret/key.py", "check.sh", ".claude/settings.json", "pyproject.toml", "a.py"]
    assert factory.risk_paths(paths, patterns) == sdlc.risk_paths(paths, patterns)


def test_the_factorys_copies_of_ships_notes_and_cap_match_sdlcs() -> None:
    """103: the landing writes the `Skill evals:` and `Fresh review:` lines ship reads, and names
    the cases' cost cap, each from a copy, since the factory's cached copy has no `sdlc.py`."""
    assert factory.CASES_RE.pattern == sdlc.CASES_RE.pattern
    assert factory.FRESH_RE.pattern == sdlc.FRESH_RE.pattern
    assert str(factory.CASE_CAP_USD) == sdlc.CASE_CAP["change"][1]


def test_the_factorys_reading_of_case_failures_matches_sdlcs() -> None:
    """156 R13: the landing names a failed case's graders from the run's record with a copy of
    `sdlc.py`'s reading."""
    record = {"verdicts": {
        "a": {"result": "failed", "runs": [{"graders": [{"name": "x"}, {"name": "y"}]},
                                           {"graders": [{"name": "y"}, {"name": "z"}]}]},
        "b": {"result": "passed on rerun", "runs": [{"graders": [{"name": "x"}]}]},
        "c": {"result": "failed", "runs": []}, "d": "nonsense"}}  # fmt: skip
    assert sdlc.cases_failures(record) == {"a": ["x", "y", "z"], "c": []}
    for r in (record, {}, None, {"verdicts": []}):
        assert factory.landing.cases_failures(r) == sdlc.cases_failures(r)


# ---------------------------------------------------------------- the eval: what escaped

REGISTER = """\
# Inbox

## [2026-10-20-1] [bug] Drafts list shows deleted ones

What happens.

Severity: high
Paths: `src/list.py`, src/views/
Introduced by: 001-start

## [2026-10-21-1] [idea] Not a bug

Paths: src/x.py

## [2026-10-22-1] [bug] Nobody knows where

Severity: low

```
## [2026-10-23-1] [bug] Fenced, not an entry
```
"""


def _history(tmp_path: Path) -> Path:
    """Main with two closed changes: 001-start (with its base recorded) and 002-fix (without),
    whose close says it fixed a bug 001 let in; then a register with open bugs."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    start = _git(root, "rev-parse", "HEAD")
    (root / "src").mkdir()
    (root / "src" / "drafts.py").write_text("v1\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-start")
    one = _git(root, "rev-parse", "HEAD")
    _git(
        root, "commit", "-q", "--allow-empty", "-m", "Close 001-start", "-m", f"Sdlc-Base: {start}"
    )
    (root / "src" / "drafts.py").write_text("v2\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 002-fix")
    fixes = [
        "Sdlc-Fixes: 2026-10-05-1 severity=high reported=2026-10-05 introduced_by=001-start "
        "paths=src/drafts.py",
        "Sdlc-Fixes: 2026-10-06-1 severity=low reported=2026-10-06 introduced_by=001-start",
        "Sdlc-Fixes: 2026-10-07-1 severity=low reported=2026-10-07 introduced_by=099-gone "
        "paths=src/x.py",
    ]
    _git(root, "commit", "-q", "--allow-empty", "-m", "Close 002-fix", "-m", "\n".join(fixes))
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "File bugs")
    root.joinpath(".one").write_text(one)
    return root


def test_escapes_lists_each_bug_with_the_diff_that_let_it_in(tmp_path, capsys) -> None:
    root = _history(tmp_path)
    one = root.joinpath(".one").read_text()
    root.joinpath(".one").unlink()
    code, out = _run(capsys, factory.cmd_escapes, root, 10)
    assert code == 0
    got = [(e["id"], e["change"], e["paths"], e["partial"]) for e in out["escapes"]]
    assert got == [
        ("2026-10-20-1", "001-start", ["src/list.py", "src/views/"], False),
        ("2026-10-06-1", "001-start", None, False),
        ("2026-10-05-1", "001-start", ["src/drafts.py"], False),
    ], "newest reported first; a pathless one listed, not dropped"
    first = out["escapes"][-1]
    assert first["commit"] == one and first["title"] is None, "a fixed bug's title left with it"
    assert first["base"] == _git(root, "rev-parse", "HEAD~5")
    assert out["escapes"][0]["title"] == "Drafts list shows deleted ones"
    assert (out["unattributed"], out["unknown_change"]) == (1, 1)
    assert _run(capsys, factory.cmd_escapes, root, 1)[1]["escapes"][0]["id"] == "2026-10-20-1"


def test_a_close_without_its_base_replays_the_last_commit_alone(tmp_path, capsys) -> None:
    root = _history(tmp_path)
    _git(root, "commit", "-q", "--allow-empty", "-m", "Ship 003-later")
    change = _git(root, "rev-parse", "HEAD")
    _git(root, "commit", "-q", "--allow-empty", "-m", "Close 003-later")
    register = root / ".sdlc" / "work" / "inbox.md"
    register.write_text(
        register.read_text()
        + "\n## [2026-10-30-1] [bug] Later\n\nSeverity: low\nIntroduced by: 003\n"
    )
    _, out = _run(capsys, factory.cmd_escapes, root, 10)
    [later] = [e for e in out["escapes"] if e["id"] == "2026-10-30-1"]
    assert (later["commit"], later["base"], later["partial"]) == (change, f"{change}^", True)


def test_the_register_is_read_as_sdlc_reads_it(tmp_path) -> None:
    (tmp_path / ".sdlc" / "work").mkdir(parents=True)
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(REGISTER)
    keys = ("id", "title", "reported", "severity", "paths", "introduced_by")
    ours = [{k: b[k] for k in keys} for b in factory.open_bugs(tmp_path)]
    theirs = [{k: b[k] for k in keys} for b in sdlc.bug_entries(tmp_path, ["high", "low"])[0]]
    assert ours == theirs


@pytest.mark.parametrize(
    "line",
    [
        "2026-10-05-1 severity=high reported=2026-10-05 introduced_by=001-start paths=a.py,b/",
        "2026-10-06-1 severity=low reported=unknown introduced_by=unknown",
        "2026-10-07-1 severity=med reported=2026-10-07 introduced_by=002-fix paths=unknown",
    ],
)
def test_fixes_lines_are_read_as_sdlc_reads_them(line: str) -> None:
    name, fields = factory._words(line)
    parsed = sdlc.metrics.parse_trailers(f"Sdlc-Fixes: {line}")["fixes"]
    assert {name: fields} == {k: {f: str(v) for f, v in d.items()} for k, d in parsed.items()}
    assert factory.bug_paths(fields.get("paths")) == sdlc.retro._bug_paths(fields.get("paths"))


@pytest.mark.parametrize(
    "evidence, paths",
    [
        ("src/drafts.py:3", ["src/drafts.py"]),
        ("src/list/view.py:9", ["src/list/"]),
        ("src/list:1", ["src/list/view.py"]),
        ("src/drafts_old.py:3", ["src/drafts.py"]),
        ("src/drafts.py:3", None),
    ],
)
def test_on_paths_is_sdlc_s_own(evidence: str, paths: list[str] | None) -> None:
    assert factory.on_paths(evidence, paths) is sdlc.retro._on_paths(evidence, paths)


# ---------------------------------------------------------------- reports and scores


def test_a_report_folder_ignores_itself(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the change so far")
    _, first = _run(capsys, factory.cmd_report_dir, root, "eval")
    _, second = _run(capsys, factory.cmd_report_dir, root, "eval")
    assert first["run"].endswith("-1") and second["run"].endswith("-2")
    (root / second["run"] / "note.md").write_text("x\n")
    assert _git(root, "status", "--porcelain") == "", "nothing a report writes dirties a checkout"


def _scored(root: Path, capsys, run: str, escapes: list[dict], replies: dict) -> dict:
    (root / run / "escapes.json").write_text(json.dumps({"escapes": escapes}))
    for (bug, role), text in replies.items():
        (root / run / bug).mkdir(exist_ok=True)
        (root / run / bug / f"{role}.md").write_text(text)
    return _run(capsys, factory.cmd_score, root, run)[1]


def test_a_reviewer_caught_a_bug_when_a_change_sits_on_its_paths(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    run = _run(capsys, factory.cmd_report_dir, root, "eval")[1]["run"]
    escapes = [
        {"id": "b1", "change": "001-start", "paths": ["src/drafts.py"]},
        {"id": "b2", "change": "001-start", "paths": None},
    ]
    replies = {
        ("b1", "code"): "VERDICT: CHANGES\n- CHANGE: src/drafts.py:3: saves twice\n",
        ("b1", "test"): "VERDICT: CHANGES\n- CHANGE: tests/test_x.py: add a test\n",
        ("b2", "code"): "VERDICT: CHANGES\n- CHANGE: src/drafts.py:3: saves twice\n",
    }
    out = _scored(root, capsys, run, escapes, replies)
    assert out["reviewers"]["code"] == {"caught": 1, "scored": 1, "previous": None}
    assert out["reviewers"]["test"] == {"caught": 0, "scored": 1, "previous": None}
    [b1, b2] = out["bugs"]
    assert b1["results"]["code"] == {"result": "caught", "lines": ["src/drafts.py:3: saves twice"]}
    assert b2["results"]["code"]["result"] == "unknown", "no paths: never scored as missed"
    report = (root / f"{run}.md").read_text()
    assert "- code: 1 of 1 caught" in report and "- test: 0 of 1 caught" in report


def test_each_eval_is_compared_with_the_last(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    escapes = [{"id": "b1", "change": "001-start", "paths": ["src/drafts.py"]}]
    first = _run(capsys, factory.cmd_report_dir, root, "eval")[1]["run"]
    _scored(root, capsys, first, escapes, {("b1", "code"): "VERDICT: PASS\n"})
    second = _run(capsys, factory.cmd_report_dir, root, "eval")[1]["run"]
    caught = {("b1", "code"): "VERDICT: CHANGES\n- CHANGE: src/drafts.py:1: x\n"}
    out = _scored(root, capsys, second, escapes, caught)
    assert out["reviewers"]["code"]["previous"] == {"caught": 0, "scored": 1}
    assert "- code: 1 of 1 caught (was 0 of 1)" in (root / f"{second}.md").read_text()


# ---------------------------------------------------------------- the review: old code


def _slice(root: Path, capsys, *paths: str, limit: int = 10) -> dict:
    return _run(capsys, factory.cmd_slice, root, list(paths), limit)[1]


def test_a_review_takes_the_sensitive_paths_first(tmp_path, capsys) -> None:
    root = _change(tmp_path, config=LISTED)
    (root / "src" / "secret").mkdir(parents=True)
    (root / "src" / "secret" / "key.py").write_text("k\n")
    (root / "src" / "other.py").write_text("o\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "more code")
    _git(root, "branch", "-q", "-f", "main", "HEAD")
    out = _slice(root, capsys)
    assert out["paths"] == ["src/secret/key.py"] and "sensitive" in out["why"]
    assert _slice(root, capsys, "src/other.py")["paths"] == ["src/other.py"], "named wins"


def test_without_sensitive_paths_the_least_recently_changed_come_first(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the change so far")
    (root / "newer.py").write_text("n\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "newer", "--date", "2030-01-01T00:00:00")
    out = _slice(root, capsys, limit=1)
    assert out["paths"] == ["README.md"] and "least recently changed" in out["why"]


def test_a_review_leaves_out_what_an_open_change_touches(tmp_path, capsys) -> None:
    root = _change(tmp_path, branch="main-work")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the work")
    _git(root, "branch", "-q", "-f", "main", "HEAD")
    tree = tmp_path / "wt"
    _git(root, "worktree", "add", "-q", "-b", "009-open", str(tree), "main")
    (tree / "README.md").write_text("an open change edits this\n")
    out = _slice(root, capsys, "README.md", "other.md")
    assert out["paths"] == ["other.md"] and out["left_out"] == ["README.md"]


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


def test_a_change_is_found_in_its_worktree_from_the_main_checkout(tmp_path, capsys) -> None:
    root, tree = _from_main(tmp_path)
    assert factory.change_root(root, "8").resolve() == tree.resolve()
    assert factory.change_root(tree, "008") == tree, "already in it"
    assert factory.change_root(root, "9") == root, "no worktree: left for find_change to refuse"
    code, out = _run(capsys, factory.cmd_start, factory.change_root(root, "008"), "008", "build")
    assert code == 0 and Path(out["worktree"]).resolve() == tree.resolve()


def test_the_worktree_lister_is_sdlc_s_own(tmp_path) -> None:
    root, _ = _from_main(tmp_path)
    assert factory.worktrees(root) == sdlc.worktrees(root)


def test_a_tier_two_at_plan_starts_with_a_spec_draft_and_shows_its_models(tmp_path, capsys):
    root = _change(tmp_path, tier=2, stage="plan")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0 and out["spec"] is True
    light = out["models_at"]["light"]
    assert light["code"] == "sonnet", "a Tier 2's reviewers are sonnet at either depth"
    assert (light["security"], light["builder"], light["approver"]) == ("opus",) * 3
    code, out = _run(capsys, factory.cmd_start, _change(tmp_path / "b", tier=2), "008", "build")
    assert out["spec"] is False, "a spec is already approved at stage: design"


@pytest.mark.parametrize(
    "role, tier, level, model",
    [("code", 1, "light", "sonnet"), ("test", 1, "full", "sonnet"),
     ("behaviour", 2, "light", "sonnet"), ("security", 1, "light", "opus"),
     ("builder", 1, "light", "opus"), ("approver", 1, "light", "opus"),
     ("verifier", 1, "light", "sonnet"), ("spec-writer", 2, "full", "opus")],
)  # fmt: skip
def test_each_role_runs_on_its_model(role, tier, level, model) -> None:
    """136 R2: the scaled reviewers run on sonnet at either depth and tier, haiku nowhere unless
    `[models]` names it; what builds, decides or hunts exploits is opus."""
    cfg, _ = factory.load_config(Path("/nonexistent"))
    assert factory.model_for(role, cfg, tier, level) == model
    assert "haiku" not in {factory.model_for(role, cfg, t, d) for t in (1, 2, None)
                           for d in ("light", "full")}  # fmt: skip
    cfg["models"] = {role: "fable"}
    assert factory.model_for(role, cfg, tier, level) == "fable", "factory.models wins"


def test_the_resolver_has_a_model_of_its_own(tmp_path, capsys) -> None:
    """149 R7: the resolver runs on sonnet at either depth and tier unless `[models] resolver`
    names another, which `start`'s `models_at` shows and no warning calls unknown; the builder's
    model never reaches it."""
    cfg, _ = factory.load_config(Path("/nonexistent"))
    assert {factory.model_for("resolver", cfg, t, d) for t in (1, 2, None)
            for d in ("light", "full")} == {"sonnet"}  # fmt: skip
    cfg["models"] = {"builder": "haiku"}
    assert factory.model_for("resolver", cfg, 1, "full") == "sonnet", "never the builder's"
    root, tree = _from_main(tmp_path)
    _, out = _run(capsys, factory.cmd_start, tree, "008", "build")
    assert {out["models_at"][d]["resolver"] for d in ("light", "full")} == {"sonnet"}
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(
        '[models]\nresolver = "opus"\nbuilder = "haiku"\n', encoding="utf-8"
    )
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "models")
    cfg, warnings = factory.load_config(tree)
    assert not any("unknown role" in w for w in warnings), warnings
    assert factory.model_for("resolver", cfg, 1, "light") == "opus"
    _, out = _run(capsys, factory.cmd_start, tree, "008", "build")
    assert {out["models_at"][d]["resolver"] for d in ("light", "full")} == {"opus"}


def test_the_agents_mode_is_the_base_branchs(tmp_path) -> None:
    root = _change(tmp_path)
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text('mode = "acceptEdits"\n', encoding="utf-8")
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "mode")
    _git(root, "checkout", "-q", NAME)
    (root / ".sdlc" / "factory.toml").write_text('mode = "bypassPermissions"\n', encoding="utf-8")
    cfg, warnings = factory.load_config(root)
    assert cfg["mode"] == "acceptEdits", "a change can't widen what its own agents may do"
    assert any("read from the base branch" in w for w in warnings)
    (root / ".sdlc" / "factory.toml").write_text('mode = "acceptEdits"\n', encoding="utf-8")
    assert factory.load_config(root)[1] == []


def test_models_are_the_base_branch_s_even_for_an_older_worktree(tmp_path, capsys, claude) -> None:
    """Bug 2026-11-18-41: a `[models]` entry committed on the base branch after a change's
    worktree was made reaches that change's `start` and its agents; one in the change's own
    checkout changes nothing, and says so."""
    root, tree = _from_main(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(
        '[models]\nbuilder = "fable"\ndesigner = "opus"\n', encoding="utf-8"
    )
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "models")
    cfg, warnings = factory.load_config(tree)
    assert any("unknown role 'designer'" in w for w in warnings), "the base's entries are checked"
    assert not (tree / ".sdlc" / "factory.toml").exists(), "the worktree predates it"
    _, out = _run(capsys, factory.cmd_start, tree, "008", "build")
    assert {out["models_at"][d]["builder"] for d in ("light", "full")} == {"fable"}
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "build", None, None)
    assert code == 0 and out["model"] == "fable", out
    argv = claude()[-1]["argv"]
    assert argv[argv.index("--model") + 1] == "fable"

    (tree / ".sdlc" / "factory.toml").write_text(
        '[models]\nbuilder = "haiku"\ncode = "haiku"\n', encoding="utf-8"
    )
    cfg, warnings = factory.load_config(tree)
    assert cfg["models"] == {"builder": "fable"}, "a change can't pick its own agents' models"
    assert any("models is read from the base branch" in w for w in warnings), warnings
    (tree / ".sdlc" / "factory.toml").write_text(
        '[models]\nbuilder = "fable"\ndesigner = "opus"\n', encoding="utf-8"
    )
    assert not [w for w in factory.load_config(tree)[1] if "read from the base branch" in w]


@pytest.mark.parametrize("bad", ["0", "true", '"two"', "1.5"])
def test_gate_jobs_is_read_from_the_base_branch_and_checked(tmp_path, capsys, bad) -> None:
    """101 R7: how many gates run at once is the base branch's to set, never the change's own,
    and a value that isn't a whole number of 1 or more is a warning that leaves 1."""
    root = _change(tmp_path)
    _on_main(root, "gate_jobs = 3\n")
    (root / ".sdlc" / "factory.toml").write_text("gate_jobs = 8\n", encoding="utf-8")
    cfg, warnings = factory.load_config(root)
    assert cfg["gate_jobs"] == 3, "a change can't give itself more gates"
    assert any("gate_jobs is read from the base branch" in w for w in warnings), warnings
    _, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert out["gate_jobs"] == 3
    (root / ".sdlc" / "factory.toml").write_text("gate_jobs = 3\n", encoding="utf-8")
    assert factory.load_config(root)[1] == []
    (root / ".sdlc" / "factory.toml").unlink()
    _on_main(root, f"gate_jobs = {bad}\n")
    cfg, warnings = factory.load_config(root)
    assert cfg["gate_jobs"] == 1 and any("gate_jobs must be" in w for w in warnings), warnings


UI = '[ui]\nserve = "serve {port}"\nshoot = "shoot {url} {out}"\npaths = ["web/"]\n'


def _on_main(root: Path, factory_toml: str) -> None:
    """Commit `factory_toml` as the base branch's `.sdlc/factory.toml`, back on the change after."""
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "factory.toml").write_text(factory_toml, encoding="utf-8")
    _git(root, "add", ".sdlc/factory.toml")
    _git(root, "commit", "-q", "-m", "factory")
    _git(root, "checkout", "-q", NAME)


def test_without_a_complete_ui_table_no_ui_review_runs(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _on_main(root, '[ui]\nserve = "serve {port}"\npaths = ["web/"]\n')
    _touch(root, "web/page.html")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert out["missing"] == FULL, "no shoot command: the run is today's"
    cfg = factory.load_config(root)[0]
    assert not factory.ui_complete(cfg["ui"]) and factory.max_runs(cfg) == 26


def test_the_ui_reviewers_join_on_a_ui_path_at_either_depth(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, config=LISTED)
    _on_main(root, UI)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    light = ["code", "behaviour"]
    assert (out["depth"], out["missing"]) == ("light", light), "no UI path, no UI review"
    _touch(root, "web/page.html")
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"]) == ("light", [*light, "ui", "ux"])
    for role in (*light, "ui", "ux"):
        _review(root, 1, role, "VERDICT: CHANGES", f"web/page.html:1: {role} fix")
    _verified(root, 1, kept=[f"{r}: web/page.html:1: {r} fix" for r in (*light, "ui", "ux")])
    (root / "web" / "page.html").unlink()
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert out["depth"] == "light", "UI reviews never make a run full"
    assert out["missing"] == [*light, "ui", "ux"], "a run that looked at the page keeps looking"
    # Each round: four reviewers, the two UI ones, the verifier, the rework and two gate fixes.
    assert factory.max_runs(factory.load_config(root)[0]) == 2 + 3 * (4 + 2 + 2 + 2)


def test_ui_reviewers_are_never_chosen_and_the_table_is_the_base_branch_s(tmp_path) -> None:
    root = _change(tmp_path)
    _on_main(root, UI)
    (root / ".sdlc" / "factory.toml").write_text(
        'reviewers = ["code", "ui"]\n' + UI.replace("web/", "src/"), encoding="utf-8"
    )
    cfg, warnings = factory.load_config(root)
    assert cfg["ui"]["paths"] == ["web/"], "a change can't point the UI review elsewhere"
    assert cfg["reviewers"] == ["code"]
    assert any("'ui' joins on its own" in w for w in warnings)
    assert any("ui is read from the base branch" in w for w in warnings)
    table, wrong = factory._ui_table({"timeout": "soon", "widths": [[1, 2, 3]], "colour": 1})
    assert table["timeout"] == 60 and table["widths"] == factory.DEFAULTS["ui"]["widths"]
    assert len(wrong) == 3 and "unknown key ui.colour" in wrong


def test_ui_fixture_is_checked_like_the_other_keys() -> None:
    """R9: `fixture` is a path inside the checkout, unset by default; anything else is a warning
    that leaves it unset."""
    assert factory.DEFAULTS["ui"]["fixture"] is None
    table, wrong = factory._ui_table({"fixture": "tests/fixtures/board/changes"})
    assert (table["fixture"], wrong) == ("tests/fixtures/board/changes", [])
    for bad in (3, ["a"], "", "/etc/board", "tests/../../elsewhere", "..", "C:/board"):
        table, wrong = factory._ui_table({"fixture": bad})
        assert table["fixture"] is None and len(wrong) == 1, bad
        assert "ui.fixture" in wrong[0], bad
    assert "fixture" in factory._ui_table("nonsense")[1][0], "the table's message names it"


@pytest.mark.parametrize("role", ["ui", "ux"])
def test_the_ui_reviewers_scale_like_the_others(role) -> None:
    cfg = factory.load_config(Path("/nonexistent"))[0]
    assert factory.model_for(role, cfg, 1, "light") == "sonnet"
    assert factory.model_for(role, cfg, 2, "light") == "sonnet"
    assert factory.model_for(role, {**cfg, "models": {role: "opus"}}, 1, "light") == "opus"
    assert factory.model_for(role, {**cfg, "models": {role: "haiku"}}, 1, "light") == "haiku"


FAKE_CLAUDE = """\
#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_CLAUDE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
code = int(os.environ.get("FAKE_CLAUDE_EXIT", "0"))
replies = json.loads(os.environ.get("FAKE_CLAUDE_REPLIES") or "null")
replies = replies or [os.environ.get("FAKE_CLAUDE_REPLY", "")]
figures = json.loads(os.environ.get("FAKE_CLAUDE_FIGURES", "{}"))
# As `--output-format stream-json --verbose` prints a session: each reply an assistant event and
# the result event after it, one JSON object a line.
print(json.dumps({"type": "system", "subtype": "init", "session_id": "s"}))
for reply in replies:
    content = [{"type": "text", "text": reply}] if reply else []
    print(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": content}}))
    print(json.dumps({"type": "result", "is_error": code != 0, "result": reply, **figures}))
sys.exit(code)
"""


@pytest.fixture
def claude(tmp_path: Path, monkeypatch):
    """A fake `claude` on PATH that records each call's argv and cwd; returns a reader for them."""
    bin_dir = tmp_path / "claude-bin"
    bin_dir.mkdir()
    (bin_dir / "claude").write_text(FAKE_CLAUDE, encoding="utf-8")
    (bin_dir / "claude").chmod(0o755)
    log = tmp_path / "claude.jsonl"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "the report\n\n## Evidence\n$ ./check.sh\nok\nexit: 0")
    monkeypatch.delenv("FAKE_CLAUDE_EXIT", raising=False)
    monkeypatch.delenv("FAKE_CLAUDE_FIGURES", raising=False)
    monkeypatch.delenv("FAKE_CLAUDE_REPLIES", raising=False)
    return lambda: [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []


def _figures(cost: float | None, tokens_in: int = 10, tokens_out: int = 5) -> str:
    """A result's figures as Claude Code reports them: on a resume, `total_cost_usd` is the
    session's total so far, and `usage` the run's own."""
    usage = {"input_tokens": tokens_in, "output_tokens": tokens_out,
             "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000}  # fmt: skip
    figures = {"duration_ms": 1200, "num_turns": 3, "usage": usage}
    return json.dumps(figures if cost is None else {**figures, "total_cost_usd": cost})


def test_each_agent_run_records_its_figures_and_a_resume_is_not_counted_twice(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    root, tree = _from_main(tmp_path)
    worktree = factory.change_root(root, "008")
    folder = tree / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.5))
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "build", None, None)
    assert code == 0, out
    session = out["session"]
    rows = [json.loads(x) for x in (folder / "runs" / "costs.jsonl").read_text().splitlines()]
    # 162 R9: when the run began and ended, around the `claude` call, for close's lead time.
    started, ended = rows[0].pop("started"), rows[0].pop("ended")
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    assert datetime.strptime(started, fmt) <= datetime.strptime(ended, fmt)
    assert rows == [{
        "session": session, "role": "builder", "model": "opus", "cost_usd": 0.5,
        "duration_ms": 1200, "turns": 3, "in": 10, "out": 5, "cache_create": 100,
        "cache_read": 1000,
    }]  # fmt: skip
    sessions = (folder / "runs" / "builder.sessions").read_text()
    assert sessions == session + "\n", "one id a line, as measuring reads it"

    # The mend resumes the builder, whose total so far is 0.75: 0.25 more, never 1.25. It mends
    # only a report `verdicts` names: here one without its evidence.
    (folder / "build" / "round-1.md").write_text("Built, no evidence.\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.75, tokens_in=20))
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "mend", "builder", None)
    assert code == 0 and out["session"] == session
    cost = factory.run_cost(folder)
    assert cost["usd"] == 0.75 and cost["by_role"] == {"builder": 0.75}
    assert cost["by_model"] == {"opus": 0.75} and cost["runs"] == 2 and cost["unknown"] == 0
    assert cost["tokens"] == {"in": 30, "out": 10, "cache_create": 200, "cache_read": 2000}


def test_a_run_reporting_no_cost_or_failing_still_counts(tmp_path, capsys, claude, monkeypatch):
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(None))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0 and (folder / "build" / "round-1.md").exists(), "a missing cost stops nothing"
    cost = factory.run_cost(folder)
    assert cost["usd"] == 0.0 and cost["unknown"] == 1 and cost["tokens"]["in"] == 10

    # A failed session files no reply, but what it spent is still recorded.
    (folder / "build" / "round-1.md").unlink()
    monkeypatch.setenv("FAKE_CLAUDE_EXIT", "1")
    monkeypatch.setenv("FAKE_CLAUDE_FIGURES", _figures(0.2))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 1 and not (folder / "build" / "round-1.md").exists()
    assert factory.run_cost(folder)["usd"] == 0.2

    # A line that doesn't parse is skipped and counted, never raised.
    with (folder / "runs" / "costs.jsonl").open("a", encoding="utf-8") as f:
        f.write("not json\n")
    assert factory.run_cost(folder)["unknown"] == 2


class _Done:
    """What `subprocess.run` returns, for `_claude()` read without a process."""

    def __init__(self, stdout: str, returncode: int = 0, stderr: str = "") -> None:
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def _stream(monkeypatch, stdout: str, returncode: int = 0) -> None:
    monkeypatch.setattr(factory.subprocess, "run", lambda *a, **k: _Done(stdout, returncode))


def _event(kind: str, text: str | None = None, **fields) -> str:
    if kind == "assistant":
        message = {"role": "assistant", "content": [{"type": "text", "text": text}]}
        return json.dumps({"type": "assistant", "message": message})
    return json.dumps({"type": "result", "is_error": False, "result": text, **fields})


@pytest.mark.portable
def test_claude_returns_every_reply_in_order(tmp_path, monkeypatch) -> None:
    """140 R1: each assistant event's text and each result's, a result that repeats the reply
    before it counted once, in the order the session gave them."""
    lines = [
        json.dumps({"type": "system", "subtype": "init"}),
        _event("assistant", "VERDICT: PASS\n\nFine."),
        _event("result", "VERDICT: PASS\n\nFine."),
        "not json",
        "[1, 2]",
        _event("assistant", "My verdict stands."),
        _event("result", "My verdict stands."),
    ]
    _stream(monkeypatch, "\n".join(lines) + "\n")
    code, replies, problem, _ = factory._claude(["claude"], tmp_path)
    assert (code, problem) == (0, None)
    assert replies == ["VERDICT: PASS\n\nFine.", "My verdict stands."]
    # A result that differs from its assistant text is a reply of its own, after it.
    _stream(monkeypatch, "\n".join([_event("assistant", "one"), _event("result", "one\ntwo")]))
    assert factory._claude(["claude"], tmp_path)[1] == ["one", "one\ntwo"]


@pytest.mark.portable
def test_a_recorded_stream_with_two_replies_reads_both(tmp_path, monkeypatch) -> None:
    """140 R3: a real session's stream (`tests/fixtures/stream-two-replies.jsonl`): a reviewer
    that started a background task, replied with its verdict, and was woken by the task's notice
    to reply again. The verdict is among the replies, and it is the one a reviewer's holds."""
    text = (Path(__file__).parent / "fixtures" / "stream-two-replies.jsonl").read_text("utf-8")
    _stream(monkeypatch, text)
    code, replies, problem, figures = factory._claude(["claude"], tmp_path)
    assert (code, problem) == (0, None)
    assert replies[0] == "VERDICT: PASS\nThe draft reopens.", replies
    assert len(replies) == 2 and replies[1].startswith("The background command finished")
    assert [r for r in replies if factory.holds("code", r)] == [replies[0]]
    assert figures["cost_usd"] == 0.00477998, "the session's total, the last result's"
    assert figures["turns"] == 3 and figures["duration_ms"] == 2322 + 954


@pytest.mark.portable
def test_a_stream_without_a_result_or_with_an_error_fails(tmp_path, monkeypatch) -> None:
    """140 R4: no result event, an error on the last one, no reply's text, or a non-zero exit is
    a failed session: no reply, only its figures."""
    figures = {"total_cost_usd": 0.1, "num_turns": 1}
    cases = {
        "no result": ([_event("assistant", "VERDICT: PASS")], 0),
        "last result errs": (
            [
                _event("result", "VERDICT: PASS"),
                json.dumps({"type": "result", "is_error": True, "result": "", **figures}),
            ],
            0,
        ),
        "no text": ([_event("result", "  ", **figures)], 0),
        "exit": ([_event("result", "VERDICT: PASS", **figures)], 2),
        "nothing": (["garbage"], 0),
    }
    for name, (lines, exit_code) in cases.items():
        _stream(monkeypatch, "\n".join(lines) + "\n", exit_code)
        code, replies, problem, got = factory._claude(["claude"], tmp_path)
        assert code != 0 and replies == [] and problem, name
        if name in ("last result errs", "exit"):
            assert got and got["cost_usd"] == 0.1, name


@pytest.mark.portable
def test_figures_sum_a_session_s_turns_and_take_its_last_cost() -> None:
    """140 R5: `total_cost_usd` is the session's total so far, so the last result's; each
    result's usage, duration and turns are its own turn's, so they are summed."""
    usage = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 100,
             "cache_read_input_tokens": 1000}  # fmt: skip
    first = {"total_cost_usd": 0.4, "duration_ms": 100, "num_turns": 2, "usage": usage}
    second = {"total_cost_usd": 0.5, "duration_ms": 50, "num_turns": 1, "usage": usage}
    figures = factory._figures([first, second])
    assert figures == {"cost_usd": 0.5, "duration_ms": 150, "turns": 3, "in": 20, "out": 10,
                       "cache_create": 200, "cache_read": 2000}  # fmt: skip
    assert factory._figures([{"result": "x"}]) is None
    one = factory._figures([{"usage": {"input_tokens": 3}}])
    assert one["in"] == 3 and one["cost_usd"] is None and one["out"] is None


def test_a_second_reply_never_replaces_the_verdict(tmp_path, capsys, claude, monkeypatch):
    """140 R2, bug 2026-11-18-26: a reviewer that replies with its verdict, then is woken by a
    background task's notice and replies again, has its verdict filed, never the note."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    for role in FULL[1:]:
        _review(root, 1, role, "VERDICT: PASS")
    verdict = "VERDICT: PASS\n\n## Notes\n\nEach requirement has its code."
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps([verdict, "My verdict stands."]))
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    filed = (folder / "reviews" / "round-1" / "code.md").read_text(encoding="utf-8")
    assert filed == verdict + "\n"
    assert _verdicts(root, capsys)["next"] == "approve"

    # The last reply that holds one wins: a verdict the reviewer changed on waking is its latest.
    changed = "VERDICT: CHANGES\n- CHANGE: src/drafts.py:3: the check I waited on failed"
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps([verdict, changed, "Done."]))
    (folder / "reviews" / "round-1" / "code.md").unlink()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    assert (
        (folder / "reviews" / "round-1" / "code.md")
        .read_text(encoding="utf-8")
        .startswith("VERDICT: CHANGES")
    )

    # No reply holds a verdict: the last is filed, and it stops the run as it would have.
    monkeypatch.setenv("FAKE_CLAUDE_REPLIES", json.dumps(["Reading the diff.", "I ran out."]))
    (folder / "reviews" / "round-1" / "code.md").unlink()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    filed = (folder / "reviews" / "round-1" / "code.md").read_text(encoding="utf-8")
    assert filed == "I ran out.\n"
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), out


@pytest.mark.portable
def test_holds_picks_each_role_s_answer() -> None:
    """140 R2: what each role's reply must hold for `agent` to file it over a later one."""
    assert factory.holds("behaviour", "Ran it.\nVERDICT: PASS")
    assert not factory.holds("code", "My verdict stands: PASS.")
    assert factory.holds("approver", "DECISION: READY") and not factory.holds("approver", "Ready.")
    assert factory.holds("verifier", "- KEPT: code: C1: real")
    assert factory.holds("verifier", "- DROPPED: code: C1: x — not there")
    assert not factory.holds("verifier", "Nothing to keep.")
    assert factory.holds("builder", "Built.\n\n## Evidence\n$ ./check.sh\nexit: 0")
    assert not factory.holds("builder", "Built.")
    assert factory.holds("spec-writer", "---\nid: 008\n---\n# 008")
    assert not factory.holds("spec-writer", "Here is my thinking.")


@pytest.mark.portable
def test_no_reviewer_runs_the_gate_or_waits_in_the_background() -> None:
    """140 R9: every reviewer and the verifier is told the gate is the script's, where its record
    is, and to start nothing in the background, whose notice wakes the session after its reply;
    none is told to run the gate."""
    agents = Path(__file__).parents[1] / "plugins" / "factory" / "agents"
    files = [*sorted(agents.glob("reviewer-*.md")), agents / "verifier.md"]
    assert len(files) == len(factory.REVIEWERS) + 1
    runs_gate = re.compile(r"(?<!never )\brun (?:the repo's )?(?:tests or )?(?:the )?gate\b", re.I)
    for path in files:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "`[commands] check`" in text and "gate.md" in text, path.name
        assert "background" in text, path.name
        assert not runs_gate.search(text), (path.name, runs_gate.search(text))
        assert "Run the repo's tests" not in text, path.name


OPENING_CASES = json.loads(
    (Path(__file__).parent / "fixtures" / "opening-cases.json").read_text(encoding="utf-8")
)


@pytest.mark.portable
@pytest.mark.parametrize("case", OPENING_CASES, ids=[c["name"] for c in OPENING_CASES])
def test_opening_reads_the_answer_line(case) -> None:
    """140 R6: the first line when it matches; else the first matching line when every matching
    line names the same answer; else none. `board.py` and `sdlc.py` pin their copies to this
    same table."""
    regex = {"verdict": factory.VERDICT_RE, "decision": factory.DECISION_RE}[case["kind"]]
    found = factory.opening(case["lines"], regex)
    got = [found[0], found[1].group(1)] if found else None
    assert got == case["answer"]


def test_a_verdict_after_prose_is_read(tmp_path, capsys) -> None:
    """140 R6: `preamble()`'s cases as they stood, each read as its answer where it stands, the
    prose kept in the file, with no mend; a reply with no verdict is still a stop."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    reply = folder / "reviews" / "round-1" / "code.md"
    text = "Both kept changes are in the code.\n\nVERDICT: PASS\n"
    reply.write_text(text, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert out["next"] == "approve" and not out["problems"], out
    assert reply.read_text(encoding="utf-8") == text, "read in place, never rewritten"
    reply.write_text("Status: reviewed\nVERDICT: CHANGES\n- CHANGE: code fix 1\n", "utf-8")
    out = _verdicts(root, capsys)
    assert out["next"] == "verify" and out["rounds"][0]["reviews"]["code"]["changes"] == [
        "code fix 1"
    ], out
    reply.write_text("VERDICT: PASS\n", encoding="utf-8")
    decision = folder / "decision.md"
    decision.write_text("I read every round.\n\nDECISION: READY\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["decision"]) == ("done", "READY"), out
    decision.unlink()
    reply.write_text("I couldn't review it.\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), out


def test_a_cost_line_written_mid_rebase_goes_into_the_resolved_commit(tmp_path, capsys) -> None:
    """The builder's resolve run appends to the change's committed `runs/costs.jsonl` while the
    landing's rebase is stopped: `resolve --continue` stages it, or git refuses to continue."""
    root, tree = _from_main(tmp_path)
    costs = tree / ".sdlc" / "work" / NAME / "runs" / "costs.jsonl"
    costs.parent.mkdir()
    costs.write_text('{"session": "s-1", "cost_usd": 0.5}\n', encoding="utf-8")
    (tree / "README.md").write_text("the change's line\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "the change")
    (root / "README.md").write_text("main's line\n", encoding="utf-8")
    _git(root, "commit", "-q", "-am", "main moves")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "008", False, "main")
    assert out["conflicted"] == ["README.md"], out
    with costs.open("a", encoding="utf-8", newline="\n") as f:
        f.write('{"session": "s-2", "role": "builder", "cost_usd": 0.25}\n')
    (tree / "README.md").write_text("main's line, and the change's\n", encoding="utf-8")
    code, out = _run(capsys, factory.landing.cmd_resolve, tree, "008", True)
    assert (code, out["state"]) == (0, "resolved"), out
    assert "s-2" in _git(tree, "show", f"HEAD:.sdlc/work/{NAME}/runs/costs.jsonl")


def test_the_hand_back_says_what_the_run_cost(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "runs").mkdir()
    rows = [
        {"session": "s-1", "role": "builder", "model": "opus", "cost_usd": 1.0},
        {"session": "s-2", "role": "code", "model": "sonnet", "cost_usd": 0.25},
        {"session": "s-3", "role": "verifier", "model": "sonnet", "cost_usd": 0.125},
    ]
    text = "".join(json.dumps(r) + "\n" for r in rows)
    (folder / "runs" / "costs.jsonl").write_text(text, encoding="utf-8")
    code, out = _run(capsys, factory.cmd_stage, root, "008", "test")
    assert code == 0 and out["cost"]["usd"] == 1.375
    assert out["cost"]["by_role"] == {"builder": 1.0, "code": 0.25, "verifier": 0.125}
    assert out["cost"]["by_model"] == {"opus": 1.0, "sonnet": 0.375}
    code, out = _run(capsys, factory.cmd_stage, root, "008", "build")
    assert "cost" not in out, "only the hand-back reports it"


def test_an_agent_runs_as_its_own_session_in_the_worktree_and_files_its_reply(
    tmp_path, capsys, claude
) -> None:
    root, tree = _from_main(tmp_path)
    worktree = factory.change_root(root, "008")
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "build", None, None)
    assert code == 0, out
    folder = tree / ".sdlc" / "work" / NAME
    assert (folder / "build" / "round-1.md").read_text().startswith("the report")
    session = (folder / "runs" / "builder.sessions").read_text().split()
    call = claude()[-1]
    assert Path(call["cwd"]).resolve() == tree.resolve()
    argv = call["argv"]
    assert argv[0] == "-p" and argv[1].startswith("Change folder: .sdlc/work/")
    assert argv.count("--verbose") == 1, "stream-json needs it in print mode"
    flags = [a for a in argv[2:] if a != "--verbose"]
    pairs = dict(zip(flags[::2], flags[1::2], strict=True))
    assert pairs["--agent"] == "sdlc-factory:builder" and pairs["--model"] == "opus"
    assert pairs["--permission-mode"] == "auto" and pairs["--output-format"] == "stream-json"
    assert pairs["--session-id"] == session[0] == out["session"]

    # A mend resumes the same builder, with its context, and writes over the report it mends:
    # one `verdicts` names, here a report without its evidence.
    (folder / "build" / "round-1.md").write_text("Built, no evidence.\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_agent, worktree, "008", "mend", "builder", None)
    assert code == 0 and claude()[-1]["argv"][-2:] == ["--resume", session[0]]
    assert (folder / "runs" / "builder.sessions").read_text().split() == session


DISAGREEING = "Both kept changes are in the code.\n\nVERDICT: CHANGES\n\nVERDICT: PASS\n"


def test_a_reviewer_s_disagreeing_verdicts_are_mended_by_the_same_reviewer(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """Bug 2026-11-17-18, 140 R7: a reply whose verdict lines disagree, none of them first, is a
    stop the run mends, asking the reviewer that wrote it, in its own session, to reply again
    with one verdict first, written over the old reply. It is never read as either verdict."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    reply = folder / "reviews" / "round-1" / "code.md"
    reply.write_text(DISAGREEING, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["code"]), out
    assert out["problems"] == [factory._no_verdict(1, "code")]

    (folder / "runs").mkdir()
    (folder / "runs" / "reviewer-code.sessions").write_text("s-code\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "VERDICT: PASS\n\n## Notes\n\nFine.")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "code", None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/reviews/round-1/code.md", out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-code"] and "sdlc-factory:reviewer-code" in argv
    assert "VERDICT:" in argv[1] and "first line" in argv[1]
    assert reply.read_text(encoding="utf-8").startswith("VERDICT: PASS\n"), "written over"
    assert (folder / "runs" / "reviewer-code.sessions").read_text() == "s-code\n"
    assert _verdicts(root, capsys)["next"] == "approve"

    # A reviewer whose reply opens with its verdict has nothing to mend.
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "security", None)
    assert code == 1 and "not a mend for security" in out["refusals"][0]

    # Once: a second such reply from the same reviewer in the same round is a stop like any other.
    reply.write_text("Still.\n\nVERDICT: PASS\nVERDICT: CHANGES\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "rerun", []), out
    calls = len(claude())
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "code", None)
    assert code == 1 and "mended once" in out["refusals"][0] and len(claude()) == calls


def test_an_approver_s_disagreeing_decisions_are_mended_by_the_approver(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """109 R10, 140 R7: a decision.md whose DECISION: lines disagree, none of them first, is a
    stop the run mends once, resuming the approver's own session and writing its whole new reply
    over the old."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    decision = folder / "decision.md"
    decision.write_text("So:\n\nDECISION: ESCALATE\nDECISION: READY\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["approver"]), out
    (folder / "runs").mkdir()
    (folder / "runs" / "approver.sessions").write_text("s-a\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "DECISION: READY\n\nFine.")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "approver", None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/decision.md", out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-a"] and "sdlc-factory:approver" in argv
    assert "DECISION:" in argv[1] and "first line" in argv[1]
    assert decision.read_text(encoding="utf-8") == "DECISION: READY\n\nFine.\n"
    assert _verdicts(root, capsys)["next"] == "done"
    decision.write_text("Again.\n\nDECISION: READY\nDECISION: ESCALATE\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), "once a round"
    # No DECISION: line at all is nothing to mend: there is no answer to put first.
    decision.write_text("I couldn't decide.\n", encoding="utf-8")
    (folder / "runs" / "mended").unlink()
    assert _verdicts(root, capsys)["way"] == "rerun"


def test_a_verifier_s_unread_answers_are_mended_once(tmp_path, capsys, claude, monkeypatch):
    """109 R10: a verified.md whose answers the script can't read (here in another shape) is a
    stop the run mends once, resuming the verifier, told what the script found; a second is a
    stop like any other."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    verified = folder / "reviews" / "round-1" / "verified.md"
    verified.write_text("- **KEPT:** code: C1: code fix 1\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["verifier"]), out
    (folder / "runs").mkdir()
    (folder / "runs" / "verifier.sessions").write_text("s-v\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "- KEPT: code: C1: code fix 1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "verifier", None)
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/reviews/round-1/verified.md", out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-v"] and "sdlc-factory:verifier" in argv
    assert "code fix 1 0 times, not once" in argv[1] and "- KEPT: <role>: C<n>:" in argv[1]
    assert verified.read_text(encoding="utf-8") == "- KEPT: code: C1: code fix 1\n"
    assert _verdicts(root, capsys)["next"] == "rework"
    verified.write_text("- **KEPT:** code: C1: code fix 1\n", encoding="utf-8")
    assert _verdicts(root, capsys)["way"] == "rerun"
    calls = len(claude())
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "verifier", None)
    assert code == 1 and "mended once" in out["refusals"][0] and len(claude()) == calls


def test_a_build_mend_is_refused_when_verdicts_names_none(tmp_path, capsys, claude) -> None:
    """109 R5, the 103 case: a change at `stage: test`, its landing round's behaviour check missing
    an exit. The build loop's `mend` runs only for a role `verdicts` names in a `mend` stop, so
    nothing runs and nothing appears under `reviews/round-1/`."""
    root = _change(tmp_path, stage="test")
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    (folder / "decision.md").write_text("DECISION: READY\n\nFine.\n", encoding="utf-8")
    land = folder / "reviews" / "land-1"
    land.mkdir(parents=True)
    (land / "behaviour.md").write_text(
        "VERDICT: PASS\n\n## Evidence\n\n$ uv run pytest -q\n3 passed\n", encoding="utf-8"
    )
    before = _files(folder / "reviews" / "round-1")
    assert _verdicts(root, capsys)["next"] == "done"
    for role in ("behaviour", "builder", "code"):
        code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", role, None)
        assert code == 1 and out["refusals"] == [f"verdicts says 'done', not a mend for {role}"]
    assert not claude() and _files(folder / "reviews" / "round-1") == before


@pytest.mark.portable
def test_the_builder_s_evidence_is_mended_once_a_round(tmp_path, capsys, claude, monkeypatch):
    """The same marker holds the evidence mend to once: a second report without it stops."""
    root = _change(tmp_path)
    _report(root, 1, "Built it. The gate passed.\n")
    (root / ".sdlc" / "work" / NAME / "runs").mkdir()
    (root / ".sdlc" / "work" / NAME / "runs" / "builder.sessions").write_text("s-b\n")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "Built it again, no evidence.")
    assert _verdicts(root, capsys)["mend"] == ["builder"]
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "builder", None)
    assert code == 0, out
    assert _verdicts(root, capsys)["way"] == "rerun"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "builder", None)
    assert code == 1 and "mended once" in out["refusals"][0]


def test_an_agent_out_of_turn_or_failing_files_nothing(tmp_path, capsys, claude, monkeypatch):
    root = _change(tmp_path)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 1 and "verdicts says 'build'" in out["refusals"][0] and not claude()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "rework", None, None)
    assert code == 1, "no step out of turn"
    monkeypatch.setenv("FAKE_CLAUDE_EXIT", "1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    folder = root / ".sdlc" / "work" / NAME
    assert code == 1 and out["exit"] == 1 and "failed" in out["problem"]
    assert not (folder / "build" / "round-1.md").exists()


# A spec-writer's reply as it comes: a sentence before the draft, the draft's frontmatter, a body
# holding a fenced block with its own `---` line and a longer fence nesting a shorter one, then the
# separator and the questions.
FENCED_DRAFT = """\
---
id: 008
kind: spec
---

# 008 — Reopen saved drafts · spec

## Requirements

R1. The config reads as:

```yaml
---
drafts: 30
---
```

````markdown
```sh
echo inside
```
---
````

~~~
---
~~~

R2. Nothing else.

"""
FENCED_REPLY = "Here is the draft.\n\n" + FENCED_DRAFT + "---\n\n- Resolved: none.\n- Left: none.\n"


@pytest.mark.portable
def test_split_draft_cuts_at_the_last_separator_outside_a_fence() -> None:
    """105 R2: the draft runs from the frontmatter to the last bare `---` outside a fence, whole."""
    preamble, draft, questions = factory.split_draft(FENCED_REPLY)
    assert draft == FENCED_DRAFT, "cut at a fence, or a line lost"
    assert questions == "\n- Resolved: none.\n- Left: none.\n"
    assert preamble == "Here is the draft."


@pytest.mark.portable
@pytest.mark.parametrize(
    "reply, expected",
    [
        (FENCED_DRAFT, (None, FENCED_DRAFT, None)),
        ("no frontmatter at all\n", (None, "no frontmatter at all\n", None)),
        ("---\nid: 008\n---\n\nbody\n", (None, "---\nid: 008\n---\n\nbody\n", None)),
        ("---\nid: 008\n", (None, "---\nid: 008\n", None)),
        ("Hi.\n---\nid: 008\n---\nbody\n---\nq\n", ("Hi.", "---\nid: 008\n---\nbody\n", "q\n")),
        ("---\nid: 1\n---\n```\n---\n", (None, "---\nid: 1\n---\n```\n---\n", None)),
    ],
    ids=["no-separator", "no-frontmatter", "body-only", "unclosed", "preamble", "open-fence"],
)
def test_split_draft_without_a_separator_keeps_the_whole_draft(reply, expected) -> None:
    assert factory.split_draft(reply) == expected


def test_the_spec_draft_is_written_whole_to_runs(tmp_path, capsys, claude, monkeypatch) -> None:
    """105 R1: the draft and its questions go to `runs/`, byte for byte; spec.md is untouched and
    the JSON names the files, never carrying the draft itself."""
    root = _change(tmp_path, tier=2, stage="plan")
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", FENCED_REPLY)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    assert code == 0, out
    assert claude()[-1]["argv"][3] == "sdlc-factory:spec-writer"
    assert out["to"] == f".sdlc/work/{NAME}/runs/spec-draft.md"
    assert out["questions"] == f".sdlc/work/{NAME}/runs/spec-questions.md"
    assert out["preamble"] == "Here is the draft." and "reply" not in out
    assert (folder / "runs" / "spec-draft.md").read_bytes() == FENCED_DRAFT.encode()
    questions = (folder / "runs" / "spec-questions.md").read_text(encoding="utf-8")
    assert questions == "\n- Resolved: none.\n- Left: none.\n"
    assert (folder / "spec.md").read_text() == "# 008 — spec.md\n\nWritten.\n", "untouched"

    # A recheck writes over both; one with no separator leaves no stale questions behind.
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "---\nid: 008\n---\n\nSecond draft.\n")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, None, True)
    assert code == 0 and out["questions"] is None and out["preamble"] is None, out
    draft = (folder / "runs" / "spec-draft.md").read_text(encoding="utf-8")
    assert draft == "---\nid: 008\n---\n\nSecond draft.\n"
    assert not (folder / "runs" / "spec-questions.md").exists()


SCAFFOLD = "---\nid: 008\nkind: spec\n---\n\n# 008 — spec\n\n<requirements>\n\n<design>\n"


def _drafted(tmp_path: Path, tier: int = 2, stage: str = "plan") -> Path:
    """A change whose spec.md is the scaffold and whose spec-writer left a fenced draft."""
    root = _change(tmp_path, tier=tier, stage=stage)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "spec.md").write_text(SCAFFOLD, encoding="utf-8", newline="\n")
    (folder / "runs").mkdir()
    (folder / "runs" / "spec-draft.md").write_bytes(FENCED_DRAFT.encode())
    return root


@pytest.mark.portable
def test_write_spec_copies_the_draft_byte_for_byte(tmp_path, capsys) -> None:
    """105 R3: spec.md becomes the draft exactly, and nothing else is written."""
    root = _drafted(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    before = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file() and p.name != "spec.md"}
    code, out = _run(capsys, factory.cmd_write_spec, root, "008")
    assert code == 0 and out["to"] == f".sdlc/work/{NAME}/spec.md", out
    assert (folder / "spec.md").read_bytes() == FENCED_DRAFT.encode()
    after = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file() and p.name != "spec.md"}
    assert after == before, "writes nothing else"
    # A rerun is refused: spec.md is no longer the scaffold.
    code, out = _run(capsys, factory.cmd_write_spec, root, "008")
    assert code == 1 and "scaffold" in out["refusals"][0]


@pytest.mark.portable
@pytest.mark.parametrize(
    "case, why",
    [
        ("no-draft", "no runs/spec-draft.md"),
        ("tier-1", "Tier 2"),
        ("past-plan", "stage: plan"),
        ("written", "scaffold"),
    ],
)
def test_write_spec_refuses_and_writes_nothing(tmp_path, capsys, case, why) -> None:
    root = _drafted(tmp_path, tier=1 if case == "tier-1" else 2,
                    stage="design" if case == "past-plan" else "plan")  # fmt: skip
    folder = root / ".sdlc" / "work" / NAME
    if case == "no-draft":
        (folder / "runs" / "spec-draft.md").unlink()
    if case == "written":
        (folder / "spec.md").write_text("# 008 — spec\n\nA person's words.\n", encoding="utf-8")
    before = (folder / "spec.md").read_bytes()
    code, out = _run(capsys, factory.cmd_write_spec, root, "008")
    assert code == 1 and why in out["refusals"][0], out
    assert (folder / "spec.md").read_bytes() == before


@pytest.mark.portable
def test_the_scaffold_rule_is_sdlc_s_own() -> None:
    """`write-spec` never writes over a person's text: its copy of `is_unfilled()`'s rule."""
    assert factory.PROMPT_RE.pattern == sdlc.PROMPT_RE.pattern
    assert factory.UNFILLED_THRESHOLD == sdlc.UNFILLED_THRESHOLD
    for text in (SCAFFOLD, "<one>\n", "plain\n", "<a>\n<b>\n<c>\n"):
        assert factory._scaffold(text) == (len(sdlc.PROMPT_RE.findall(text)) >= 2), text


def test_a_revision_reaches_the_same_spec_writer_through_the_ledger(tmp_path, capsys, claude):
    """A person's words never go in a command line: a revision is a ticked `R<n>` line in
    `decisions.md`, read by `agent`, and the spec-writer that drafted is resumed with them; a
    recheck resumes it with fixed text. Neither is a decision the loop waits on."""
    root = _change(tmp_path, tier=2, stage="plan")
    folder = root / ".sdlc" / "work" / NAME
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, "R1")
    assert code == 1 and "R1" in out["refusals"][0], "no spec-writer yet, and no R1 line"
    _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    session = (folder / "runs" / "spec-writer.sessions").read_text().split()
    words = 'drop R3; it\'s "out of scope" & $(nothing) runs'
    (folder / "decisions.md").write_text(
        f"# Decisions\n\n- [x] R1 (person, revise): {words}\n", encoding="utf-8"
    )
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, "R1")
    argv = claude()[-1]["argv"]
    assert code == 0 and argv[1].endswith(words) and argv[-2:] == ["--resume", session[0]]
    draft = (folder / "runs" / "spec-draft.md").read_text(encoding="utf-8")
    assert draft.startswith("the report"), "a revision writes over the draft"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None, None, True)
    assert code == 0 and claude()[-1]["argv"][1] == factory.prompt_part("spec", "recheck")
    assert factory.read_ledger(folder) == [], "a revision is no decision the loop waits on"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None, None, True)
    assert code == 1 and "for --task spec" in out["refusals"][0]


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


def test_the_gate_runs_the_base_branchs_check_and_records_each_attempt(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """R1–R4: the base branch's command, never the checkout's; each attempt appended, the first
    line the latest; a red gate is a fix for the same builder, appended to the round's report,
    and the fixed build is gated again before any review."""
    root = _change(tmp_path)
    _gate_config(root, 'echo base-ran; test -z "$FAKE_GATE_FAIL"')
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "echo mine"\n')
    folder = root / ".sdlc" / "work" / NAME
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("gate", 1) and out["gate"]["current"] is None

    monkeypatch.setenv("FAKE_GATE_FAIL", "1")
    code, out = _gate(root, capsys)
    assert code == 1 and (out["verdict"], out["attempt"], out["exit"]) == ("FAIL", 1, "1")
    record = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    assert record.startswith("GATE: FAIL\n") and "    base-ran" in record and "mine" not in record
    out = _verdicts(root, capsys)
    assert (out["next"], out["gate"]["fails"]) == ("fix", 1), "no reviewer on a red build"

    (folder / "runs").mkdir()
    (folder / "runs" / "builder.sessions").write_text("builder-1\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "fix", None, None)
    assert code == 0 and out["to"].endswith("build/round-1.md"), out
    argv = claude()[-1]["argv"]
    assert "The gate failed on round 1" in argv[1] and argv[-2:] == ["--resume", "builder-1"]
    report = (folder / "build" / "round-1.md").read_text(encoding="utf-8")
    assert report.startswith("Built slice 1.") and "the report" in report, "added, not replaced"
    assert _verdicts(root, capsys)["next"] == "gate", "a fixed build is gated again"

    monkeypatch.delenv("FAKE_GATE_FAIL")
    code, out = _gate(root, capsys)
    assert code == 0 and (out["verdict"], out["attempt"]) == ("PASS", 2)
    record = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    assert record.startswith("GATE: PASS\n") and record.count("## Attempt ") == 2
    assert [a["verdict"] for a in factory.read_gate(folder, 1)["attempts"]] == ["FAIL", "PASS"]
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == ("review", 1, FULL)


def test_the_gate_records_no_path_of_this_machine(tmp_path, capsys, monkeypatch) -> None:
    """087: `claude plugin validate` prints its manifests' absolute paths and `pytest -n auto` a
    failing worker's venv, and the record is committed with the change, so the checkout reads
    `<path-to-clone>` and the home directory `<home>`. Home holds the checkout here: the checkout
    is written first, so it never reads `<home>/…`."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _change(tmp_path)
    _gate_config(
        root,
        'echo "Validating marketplace manifest: $PWD/.claude-plugin/marketplace.json"; '
        'echo "[gw0] crashed under $HOME/.cache/uv/venv"; exit 1',
    )
    _build_report(root, 1)
    code, out = _gate(root, capsys)
    assert code == 1 and (out["verdict"], out["exit"]) == ("FAIL", "1")
    folder = root / ".sdlc" / "work" / NAME
    record = (folder / "build" / "round-1.gate.md").read_text(encoding="utf-8")
    for path in {str(root), str(root.resolve()), str(tmp_path), str(tmp_path.resolve())}:
        assert path not in record, path
    assert "    Validating marketplace manifest: <path-to-clone>/.claude-plugin/" in record
    assert "    [gw0] crashed under <home>/.cache/uv/venv" in record
    assert [(a["verdict"], a["exit"]) for a in factory.read_gate(folder, 1)["attempts"]] == [
        ("FAIL", "1")
    ]


def test_the_gate_records_no_temp_path_or_user_name(tmp_path, capsys, monkeypatch) -> None:
    """A failing test's `tmp_path` sits under the temp directory, in pytest's `pytest-of-<login>`:
    the record reads `<tmp>`, and the login name `<user>` inside a marked path, while the same
    word in prose stays as it was printed."""
    temp = tmp_path / "T"
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        monkeypatch.setenv(name, "drafter")
    monkeypatch.setenv("FAKE_TMP_PATH", f"{temp}/pytest-of-drafter/popen-gw4/test_x0")
    root = _change(tmp_path)
    _gate_config(
        root,
        'echo "tmp_path = PosixPath(\'$FAKE_TMP_PATH\')"; echo "drafter said hi"; exit 1',
    )
    _build_report(root, 1)
    code, out = _gate(root, capsys)
    assert code == 1 and out["verdict"] == "FAIL"
    record = (root / ".sdlc" / "work" / NAME / "build" / "round-1.gate.md").read_text("utf-8")
    assert "    tmp_path = PosixPath('<tmp>/pytest-of-<user>/popen-gw4/test_x0')" in record
    assert "    drafter said hi" in record
    for path in {str(temp), str(temp.resolve()), "pytest-of-drafter"}:
        assert path not in record, path
    assert factory.is_read("ls <tmp>/pytest-of-<user>/x")


def _forbidden_shapes() -> re.Pattern:
    """`tests/test_nothing_local.py`'s `PATTERNS`, the shapes the gate refuses in any record."""
    scan = _load("nothing_local_for_factory", ROOT / "tests" / "test_nothing_local.py")
    return re.compile("|".join(scan.PATTERNS), re.IGNORECASE)


def test_a_path_under_home_is_filed_in_a_form_the_scan_accepts(tmp_path, monkeypatch) -> None:
    """135: a path under the home directory but outside the clone, or a clone path that output
    cut short, keeps the directory after home: written `~/…`, it reads as a home path to the scan
    and the gate fails on a record whose change is fine."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _change(tmp_path)
    text = (
        f"node at {tmp_path}/.nvm/versions/node/bin/node\n"
        f"cut short: {tmp_path}/repo-but-cut/s...\n"
        f"elsewhere: {tmp_path.resolve().as_posix()}/projects/other/x.py\n"
    )
    filed = factory._placeholders(text, root)
    assert str(tmp_path) not in filed and str(tmp_path.resolve()) not in filed
    assert f"{factory.HOME_MARK}/projects/other/x.py" in filed
    assert _forbidden_shapes().search(filed) is None, filed


def test_a_path_is_marked_only_as_a_whole_path(tmp_path, monkeypatch) -> None:
    """A temp directory as short as Linux's `/tmp` is a substring of `/var/tmp` and `/tmpfoo`:
    each is left as printed, and only the temp directory itself, whole, reads `<tmp>`."""
    temp = tmp_path / "t"
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    root = _change(tmp_path)
    text = f"{temp}/x and {temp}, then /var{temp}/y and {temp}foo/z\n"
    filed = factory._placeholders(text, root)
    assert filed == f"<tmp>/x and <tmp>, then /var{temp}/y and {temp}foo/z\n", filed


def test_every_reply_is_filed_without_this_machine_s_paths(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """135: an agent quoting `git worktree list` names the main checkout and the change's own
    worktree, and a reply is committed with the change: the builder's report and the spec draft
    read `<path-to-clone>` and the home mark, never the path, and what the agent concluded
    stays as it said it."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root, tree = _from_main(tmp_path)
    folder = tree / ".sdlc" / "work" / NAME
    quoted = (
        f"- CHANGE: scripts/x.py: keep it\n\n## Evidence\n\n$ git worktree list\n"
        f"{root.resolve()}  abc123 [main]\n{tree}  def456 [{NAME}]\n"
        f"$ which node\n{tmp_path}/.nvm/bin/node\nexit: 0\n"
    )
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "Built it.\n" + quoted)
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "build", None, None)
    assert code == 0, out
    report = (tree / out["to"]).read_text(encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "---\nid: 008\n---\n\n# 008 — spec\n\n" + quoted)
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "spec", None, None)
    assert code == 0, out
    draft = (folder / "runs" / "spec-draft.md").read_text(encoding="utf-8")
    for filed in (report, draft):
        for path in {str(root), str(root.resolve()), str(tree), str(tmp_path)}:
            assert path not in filed, path
        assert "<path-to-clone>  abc123 [main]\n" in filed
        assert f"<path-to-clone>  def456 [{NAME}]\n" in filed
        assert f"{factory.HOME_MARK}/.nvm/bin/node\n" in filed
        assert "- CHANGE: scripts/x.py: keep it\n" in filed
        assert _forbidden_shapes().search(filed) is None, filed


def test_a_reply_citing_its_own_change_by_number_is_filed_by_its_full_name(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """Bug 2026-11-18-42: an agent that cites its own change's folder by bare number or glob
    has it filed as the full folder name, which the gate's scan accepts; another change's number,
    a longer number, a path already named in full and a `*` followed by more of a name (nit
    2026-11-18-62) are left as the agent wrote them, but for the scan's placeholder."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    # Built from parts: written whole, each citation is the shape the scan refuses in this file.
    w, n = "work/", "008"
    reply = (
        "Built it.\n\n## Evidence\n\n"
        f"$ ls .sdlc/{w}{n}*/build\nround-1.md\nexit: 0\n"
        f"$ cat .sdlc/{w}{n}/intent.md\nid: 008\nexit: 0\n"
        f"Seen in {w}{n}, and in {w}{n}* too.\n"
        f"Already whole: {w}{NAME}/plan.md, {w}{n}9, {w}009 and {w}{n}-*.\n"
        f"Not a glob: {w}{n}*x.\n"
    )
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", reply)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    filed = (root / out["to"]).read_text(encoding="utf-8")
    assert f"$ ls .sdlc/{w}{NAME}/build\n" in filed
    assert f"$ cat .sdlc/{w}{NAME}/intent.md\n" in filed
    assert f"Seen in {w}{NAME}, and in {w}{NAME} too.\n" in filed
    assert f"Already whole: {w}{NAME}/plan.md, {w}<{n}9>, {w}<009> and {w}{n}-*.\n" in filed
    assert f"Not a glob: {w}<{n}>*x.\n" in filed, "never backtracked off its `*`"
    assert "Built it.\n\n## Evidence\n" in filed and "round-1.md\nexit: 0\n" in filed
    assert _forbidden_shapes().search(filed) is None, filed
    assert (folder / "build" / "round-1.md").is_file()


def test_the_shapes_the_factory_defuses_are_the_scan_s() -> None:
    """`DEFUSE` holds `tests/test_nothing_local.py`'s `PATTERNS`, in order: a shape the scan
    gains is one the factory writes as a placeholder too."""
    scan = _load("nothing_local_for_defuse", ROOT / "tests" / "test_nothing_local.py")
    assert [shape for shape, _ in factory.DEFUSE] == scan.PATTERNS


def test_a_record_quoting_the_tests_fixtures_is_filed_in_a_form_the_scan_accepts(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """A reply quoting a test's output names the fixtures' changes and homes, which the scan
    refuses in any committed record: each is filed as its placeholder, and the gate's own copy of
    a failing test's output too, so a red gate never makes the next one red."""
    root = _change(tmp_path)
    w = "work/"
    quoted = (
        f"E  assert '$ ls .sdlc/{w}046*/build' in report\n"
        "Cloned to /Users/"
        "someone/code/x, /home/"
        "someone/code/x and ~/"
        "code/x.\n"
        "Kept: ~/.claude/plugins/ and /Users/<name>/.\n"
    )
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "Built it.\n\n" + quoted)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    filed = (root / out["to"]).read_text(encoding="utf-8")
    assert f"$ ls .sdlc/{w}<046>*/build" in filed
    assert "/Users/<name>/code/x, /home/<name>/code/x and ~/<dir>/x" in filed
    assert "Kept: ~/.claude/plugins/ and /Users/<name>/." in filed
    assert _forbidden_shapes().search(filed) is None, filed
    (root / "quoted.txt").write_text(quoted, encoding="utf-8")
    _gate_config(root, "cat quoted.txt; exit 1")
    _gate(root, capsys)
    record = factory.gate_path(root / ".sdlc" / "work" / NAME, 1).read_text(encoding="utf-8")
    assert f"{w}<046>*" in record and _forbidden_shapes().search(record) is None, record


def test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """Nit 2026-11-18-72: the scan also refuses each regex in the main checkout's gitignored
    `.sdlc/terms.local`, so a reply quoting one is filed with it as `<term>`, from the change's
    own worktree, where the file has no copy. A line written by hand is named by `defuse` and
    the approver by its path and line, never the term, and `defuse` rewrites it."""
    root, tree = _from_main(tmp_path)
    folder = tree / ".sdlc" / "work" / NAME
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "terms.local").write_text("# kept out\n\n\\bstale widgets\\b\n")
    reply = "Built it for Stale Widgets.\n\n## Evidence\n\n$ grep x\nstale widgets\nexit: 0\n"
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", reply)
    code, out = _run(capsys, factory.cmd_agent, tree, "008", "build", None, None)
    assert code == 0, out
    filed = (tree / out["to"]).read_text(encoding="utf-8")
    assert "Built it for <term>.\n" in filed and "\n<term>\nexit: 0\n" in filed, filed
    assert "widgets" not in filed.lower()
    (folder / "notes.md").write_text("Seen in stale widgets first.\n", encoding="utf-8")
    assert factory.forbidden_lines(folder, tree) == ["notes.md:1"]
    code, out = _run(capsys, factory.cmd_defuse, tree, "008")
    assert code == 0 and out["changed"] == ["notes.md"] and out["left"] == [], out
    assert (folder / "notes.md").read_text(encoding="utf-8") == "Seen in <term> first.\n"
    assert "widgets" not in json.dumps(out)


def test_an_approver_s_decision_stops_on_a_folder_the_scan_would_refuse(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """The approver ends a build: a line the scan refuses anywhere in the folder, written by
    hand or filed before the rule, stops the change then, naming the file and line and the
    command that rewrites it, never at the landing's gate."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    (folder / "notes.md").write_text("Seen in work/" + "046 first.\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "DECISION: READY\n\n**Why.** Fine.\n")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 1 and "notes.md:1" in out["problem"], out
    assert "factory.py defuse 008" in out["problem"] and "046" not in out["problem"]
    assert (folder / "decision.md").is_file()
    code, out = _run(capsys, factory.cmd_defuse, root, "008")
    assert code == 0 and out["changed"] == ["notes.md"] and out["left"] == [], out
    assert (folder / "notes.md").read_text(encoding="utf-8") == "Seen in work/<046> first.\n"
    assert factory.forbidden_lines(folder) == []
    (folder / "decision.md").unlink()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 0 and "problem" not in out, out


def test_a_third_red_gate_in_a_round_is_a_stop(tmp_path, capsys) -> None:
    """R5: two fixes a round; the third red gate stops the change, never a review."""
    root = _change(tmp_path)
    _gate_config(root, "exit 3")
    _build_report(root, 1)
    for fix in range(factory.GATE_FIXES):
        _gate(root, capsys)
        assert _verdicts(root, capsys)["next"] == "fix", fix
        _fixed(root)
    _gate(root, capsys)
    out = _verdicts(root, capsys)
    assert out["next"] == "stop"
    assert any("the gate failed 3 times in round 1: exit 3" in p for p in out["problems"])


def test_a_gate_that_changes_the_tree_or_runs_too_long_fails(tmp_path, capsys, monkeypatch):
    """R2: PASS only on exit 0, within the timeout, with the tree as the gate found it."""
    root = _change(tmp_path)
    _gate_config(root, "printf more >> README.md")
    _build_report(root, 1)
    code, out = _gate(root, capsys)
    assert code == 1 and out["exit"] == "0" and out["tree"] == "changed: README.md"
    _gate_config(root, "exec sleep 5")
    monkeypatch.setattr(factory, "GATE_TIMEOUT", 0.5)
    code, out = _gate(root, capsys)
    assert code == 1 and out["exit"] == "timeout" and out["attempt"] == 2


def test_with_no_gate_the_build_goes_to_review(tmp_path, capsys) -> None:
    """R6: no `[commands] check` on the base branch, no step and no file, and why."""
    root = _change(tmp_path)
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert out["next"] == "review" and out["gate"] is None and "[commands] check" in out["gate_why"]
    code, out = _gate(root, capsys)
    assert code == 1 and "no [commands] check" in out["refusals"][0]
    assert not (root / ".sdlc" / "work" / NAME / "build" / "round-1.gate.md").exists()


def test_the_light_depth_is_gated_too(tmp_path, capsys) -> None:
    """R7: a diff touching no sensitive path runs light, and its build is gated all the same."""
    root = _change(tmp_path)
    _gate_config(root, "true", '[review]\nsensitive = ["secrets/"]\n')
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["next"]) == ("light", "gate")


def test_a_reviewed_round_is_never_gated_after_the_fact(tmp_path, capsys) -> None:
    """R14: a run from before the gate, its round reviewed with no gate file, reads as it did."""
    root = _change(tmp_path)
    _gate_config(root, "true")
    _round(root, 1, code="CHANGES")
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"]) == ("verify", 1) and out["problems"] == []


def test_close_counts_the_red_gates_only_for_a_run_that_had_one(tmp_path, capsys) -> None:
    """R10: `gate_fail` from the committed gate files reaches `Sdlc-Rework`; a run with no gate
    file says nothing, never 0, so an old trailer reads as unknown."""
    metrics = sdlc.metrics
    root = _change(tmp_path)
    _gate_config(root, "test -f fixed.txt")
    _round(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "decision.md").write_text("DECISION: READY\n\nAll pass.\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "built, no gate yet")
    assert "gate_fail" not in sdlc.closing._factory_files(root, NAME)
    _gate(root, capsys)
    (root / "fixed.txt").write_text("ok\n", encoding="utf-8")
    _fixed(root)
    _gate(root, capsys)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "gated")
    found = sdlc.closing._factory_files(root, NAME)
    assert found["gate_fail"] == 1 and found["rounds"] == 1, "the gate file is no review round"
    done = metrics.rework([], {}, found, None, 2)
    assert done["gate_fail"] == 1
    assert any("gate_fail=1" in line for line in metrics.in_change_trailers(done, {}, None))
    old = {k: v for k, v in found.items() if k != "gate_fail"}
    assert "gate_fail" not in metrics.rework([], {}, old, None, 2)


def test_a_fix_is_refused_unless_the_gate_is_red(tmp_path, capsys, claude) -> None:
    root = _change(tmp_path)
    _gate_config(root, "true")
    _build_report(root, 1)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "fix", None, None)
    assert code == 1 and "verdicts says 'gate'" in out["refusals"][0] and not claude()


def test_measuring_reads_which_sessions_were_the_factorys_agents(tmp_path) -> None:
    root = _change(tmp_path)
    runs = root / ".sdlc" / "work" / NAME / "runs"
    runs.mkdir()
    (runs / "builder.sessions").write_text("s-1\ns-2\n", encoding="utf-8")
    (runs / "reviewer-code.sessions").write_text("s-3\n", encoding="utf-8")
    (runs / "reviewer-ui.sessions").write_text("s-4\n", encoding="utf-8")
    (runs / "reviewer-ux.sessions").write_text("s-5\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the run")
    found = sdlc.closing._agent_sessions(root, NAME, f".sdlc/work/{NAME}")
    assert found == {"s-1": "builder", "s-2": "builder", "s-3": "reviewer-code",
                     "s-4": "reviewer-ui", "s-5": "reviewer-ux"}  # fmt: skip


def test_a_resolver_session_is_its_own_role(tmp_path) -> None:
    """149 R12: a session in `runs/resolver.sessions` is named `resolver`, never `builder`."""
    root = _change(tmp_path)
    runs = root / ".sdlc" / "work" / NAME / "runs"
    runs.mkdir()
    (runs / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    (runs / "resolver.sessions").write_text("s-2\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the run")
    found = sdlc.closing._agent_sessions(root, NAME, f".sdlc/work/{NAME}")
    assert found == {"s-1": "builder", "s-2": "resolver"}


def test_ready_lists_what_can_ship_in_the_order_to_ship_it(tmp_path, capsys) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    changes = (
        ("009-second", "[008]", "test"),
        ("008-first", "", "test"),
        ("010-busy", "", "build"),
    )
    for name, deps, stage in changes:
        tree = tmp_path / name
        _git(root, "worktree", "add", "-q", "-b", name, str(tree), "main")
        folder = tree / ".sdlc" / "work" / name
        folder.mkdir(parents=True)
        text = INTENT.format(tier=2, stage=stage).replace("idea:\n", f"idea:\ndepends_on: {deps}\n")
        (folder / "intent.md").write_text(text, encoding="utf-8")
        (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
        (tree / "README.md").write_text(f"{name} edits this\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_ready, root)
    assert code == 0
    assert [r["change"] for r in out["ready"]] == ["008-first", "009-second"], "010 isn't ready"
    first, second = out["ready"]
    assert second["depends_on"] == ["008"] and first["overlaps"] == ["009-second"]
    assert first["cost"]["usd"] == 0.0 and first["cost"]["runs"] == 0, "no runs recorded yet"


def test_ready_leaves_a_stopped_run_out(tmp_path, capsys) -> None:
    """R13: a stopped run sits at `stage: build`, its record or not, and is never ready."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    tree = tmp_path / NAME
    _git(root, "worktree", "add", "-q", "-b", NAME, str(tree), "main")
    folder = tree / ".sdlc" / "work" / NAME
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(INTENT.format(tier=2, stage="build"), encoding="utf-8")
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    (folder / "runs").mkdir()
    (folder / factory.STOPPED).write_text(
        factory.stop_text(NAME, "rerun", ["a problem"]), encoding="utf-8"
    )
    code, out = _run(capsys, factory.cmd_ready, root)
    assert code == 0 and out["ready"] == []


# A dev server and a screenshot command, as a host's `[ui]` would name them: the server writes its
# pid, then serves; the shooter writes a PNG to its `out` unless `FAKE_SHOOT_EXIT` says to fail.
FAKE_SERVE = """\
import http.server, os, sys
open(sys.argv[2], "w").write(str(os.getpid()))
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])),
                                http.server.SimpleHTTPRequestHandler).serve_forever()
"""
FAKE_SHOOT = """\
import os, sys
code = int(os.environ.get("FAKE_SHOOT_EXIT", "0"))
if not code:
    open(sys.argv[2], "wb").write(b"\\x89PNG fake " + sys.argv[1].encode())
print("shot " + sys.argv[1], file=sys.stderr)
sys.exit(code)
"""
SLEEPER = "import os, sys, time\nopen(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(60)\n"


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # A zombie still answers kill(0); `ps` says whether it has gone.
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
    return bool(state.stdout.strip()) and not state.stdout.strip().startswith("Z")


def _ui(tmp_path: Path, serve: str | None = None, **more) -> dict:
    py = sys.executable
    (tmp_path / "serve.py").write_text(FAKE_SERVE)
    (tmp_path / "shoot.py").write_text(FAKE_SHOOT)
    pid = tmp_path / "server.pid"
    table = {
        "serve": serve or f'"{py}" "{tmp_path / "serve.py"}" {{port}} "{pid}"',
        "shoot": f'"{py}" "{tmp_path / "shoot.py"}" "{{url}}" "{{out}}"',
        "paths": ["web/"], "pages": ["/", "/drafts/"], "timeout": 20, **more,
    }  # fmt: skip
    return factory._ui_table(table)[0]


def test_shots_start_the_declared_server_shoot_each_page_and_stop_it(tmp_path) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    ui = _ui(tmp_path)
    paths, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert record["problem"] is None, record
    names = sorted(p.name for p in paths)
    assert names == ["drafts-1280x800.png", "drafts-390x844.png", "index-1280x800.png",
                     "index-390x844.png"]  # fmt: skip
    assert all(p.is_file() for p in paths)
    where = root / ".sdlc" / "reports" / "shots" / NAME / "round-1" / "ui"
    assert paths[0].parent == where and (where / "shots.json").is_file()
    assert (root / ".sdlc" / "reports" / ".gitignore").read_text() == "*\n"
    assert _git(root, "status", "--porcelain", "--", ".sdlc/reports") == "", "none reach git"
    assert not factory._answers("127.0.0.1", record["port"]), "the server it started is stopped"
    assert not _alive(int((tmp_path / "server.pid").read_text()))
    assert any("/drafts/" in s["command"] for s in record["shots"])
    first = record["shots"][0]["command"]
    assert first.endswith(f'"{(where / "index-1280x800.png").relative_to(root).as_posix()}"')
    # A round already shot is reused, never shot again.
    (tmp_path / "server.pid").unlink()
    again, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert again == paths and not (tmp_path / "server.pid").exists()


def test_shots_wait_for_the_server_where_the_url_says(tmp_path) -> None:
    """F1: the readiness check goes to `[ui] url`'s host, resolved to each of its addresses."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    ui = _ui(tmp_path, url="http://localhost:{port}", pages=["/"], widths=[[390, 844]])
    paths, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert record["problem"] is None and paths[0].is_file(), record
    assert "http://localhost:" in record["shots"][0]["command"]


def test_a_failed_shot_or_a_silent_server_still_stops_the_server(tmp_path, monkeypatch) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_SHOOT_EXIT", "3")
    paths, record = factory.shots(root, folder, "round-1", _ui(tmp_path), "ui")
    assert "exited 3" in record["problem"] and not any(p.is_file() for p in paths)
    assert not _alive(int((tmp_path / "server.pid").read_text()))
    monkeypatch.delenv("FAKE_SHOOT_EXIT")
    (tmp_path / "sleep.py").write_text(SLEEPER)
    sleeper = f'"{sys.executable}" "{tmp_path / "sleep.py"}" "{tmp_path / "sleep.pid"}"'
    paths, record = factory.shots(root, folder, "round-2", _ui(tmp_path, sleeper, timeout=1), "ui")
    assert "didn't answer" in record["problem"]
    assert not _alive(int((tmp_path / "sleep.pid").read_text())), "never left running"


def test_a_ui_review_never_runs_blind(tmp_path, capsys, claude, monkeypatch) -> None:
    root = _change(tmp_path)
    ui = _ui(tmp_path)
    toml = "[ui]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in ui.items() if v is not None)
    _on_main(root, toml)
    _touch(root, "web/page.html")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_SHOOT_EXIT", "1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "ui", None)
    assert code == 1 and "doesn't run blind" in out["refusals"][0] and not claude()
    assert not (folder / "reviews" / "round-1" / "ui.md").exists()
    monkeypatch.delenv("FAKE_SHOOT_EXIT")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "ux", None)
    assert code == 0, out
    argv = claude()[-1]["argv"]
    assert argv[3] == "sdlc-factory:reviewer-ux" and "Screenshots: " in argv[1]
    assert "index-390x844.png" in argv[1] and "web/page.html" in argv[1]
    assert f"/shots/{NAME}/round-1/ux/index-390x844.png" in argv[1], "ux's own folder"
    assert (folder / "reviews" / "round-1" / "ux.md").is_file()
    assert (folder / "runs" / "reviewer-ux.sessions").is_file()


# A dev server that serves fixture data and writes into it, as a real one may: it refuses a copy an
# earlier server already wrote to, so only a fresh copy lets it answer.
FIXTURE_SERVE = """\
import http.server, os, sys
port, fixture, pid = sys.argv[1:4]
open(pid, "w").write(str(os.getpid()))
with open(os.path.join(fixture, "written.txt"), "x") as f:
    f.write(open(os.path.join(fixture, "seed.txt")).read())
http.server.ThreadingHTTPServer(("127.0.0.1", int(port)),
                                http.server.SimpleHTTPRequestHandler).serve_forever()
"""


def _fixture_ui(tmp_path: Path, root: Path, fixture: str = "fixtures/drafts") -> dict:
    (tmp_path / "fixture_serve.py").write_text(FIXTURE_SERVE)
    serve = f'"{sys.executable}" "{tmp_path / "fixture_serve.py"}" {{port}} {{fixture}} '
    serve += f'"{tmp_path / "server.pid"}"'
    return _ui(tmp_path, serve, fixture=fixture, pages=["/"], widths=[[390, 844]])


def test_shots_serve_a_fresh_copy_of_the_fixture(tmp_path) -> None:
    """R10: each shot serves its own copy of the fixture, the committed one never written, and the
    record names the copy by a path relative to the checkout."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _touch(root, "fixtures/drafts/seed.txt")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a fixture")
    ui = _fixture_ui(tmp_path, root)
    paths, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert record["problem"] is None, record
    copy = root / ".sdlc" / "reports" / "shots" / NAME / "round-1" / "ui" / "fixture"
    assert (copy / "written.txt").read_text() == "x\n", "the server read and wrote its copy"
    assert not (root / "fixtures" / "drafts" / "written.txt").exists()
    assert _git(root, "status", "--porcelain") == "", "the committed fixture is as it was"
    rel = copy.relative_to(root).as_posix()
    assert f" {rel} " in record["serve"]
    assert str(root) not in record["serve"], "the record names no machine's checkout"
    # A second label gets a clean copy of its own; a copy a failed attempt left is replaced.
    stale = root / ".sdlc" / "reports" / "shots" / NAME / "round-2" / "ui" / "fixture"
    stale.mkdir(parents=True)
    (stale / "written.txt").write_text("stale\n")
    _, record = factory.shots(root, folder, "round-2", ui, "ui")
    assert record["problem"] is None, record
    assert (stale / "written.txt").read_text() == "x\n"
    # A fixture that is one file is copied into the folder, and `{fixture}` names the file.
    _, record = factory.shots(
        root, folder, "round-3", _ui(tmp_path, "true", fixture="README.md"), "ui"
    )
    copied = (
        root / ".sdlc" / "reports" / "shots" / NAME / "round-3" / "ui" / "fixture" / "README.md"
    )
    assert copied.read_text() == "a repo\n"


def test_a_missing_fixture_refuses_the_ui_review(tmp_path, capsys, claude) -> None:
    """R11: a fixture the checkout lacks is a problem, so no server starts and the UI review is
    refused; a `serve` naming `{fixture}` with none set is a config warning."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    paths, record = factory.shots(root, folder, "round-1", _fixture_ui(tmp_path, root), "ui")
    assert "fixtures/drafts" in record["problem"] and "doesn't exist" in record["problem"]
    assert not (tmp_path / "server.pid").exists(), "no server started"
    ui = _fixture_ui(tmp_path, root)
    toml = "[ui]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in ui.items() if v is not None)
    _on_main(root, toml)
    _touch(root, "web/page.html")
    _build_report(root, 1)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "ui", None)
    assert code == 1 and "doesn't run blind" in out["refusals"][0] and not claude()
    _on_main(root, toml.replace('fixture = "fixtures/drafts"\n', ""))
    assert "ui.serve names {fixture}, but no ui.fixture is set" in factory.load_config(root)[1]


# A dev server that builds its data inside the fixture copy and refuses a copy that already holds
# it, as this repo's `serve.sh` does through `build.sh`.
BUILDING_SERVE = """\
import http.server, os, sys
port, fixture = sys.argv[1:3]
os.mkdir(os.path.join(fixture, "drafts"))
http.server.ThreadingHTTPServer(("127.0.0.1", int(port)),
                                http.server.SimpleHTTPRequestHandler).serve_forever()
"""


def test_the_ui_and_ux_reviews_of_a_round_run_at_once(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """119: the ui and ux reviewers started together each take their shots in a folder of their
    own, with their own fixture copy and server, so neither's serve finds the other's data."""
    import threading

    root = _change(tmp_path)
    _touch(root, "fixtures/drafts/seed.txt")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a fixture")
    (tmp_path / "building_serve.py").write_text(BUILDING_SERVE)
    serve = f'"{sys.executable}" "{tmp_path / "building_serve.py"}" {{port}} {{fixture}}'
    ui = _ui(tmp_path, serve, fixture="fixtures/drafts", pages=["/"], widths=[[390, 844]])
    toml = "[ui]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in ui.items() if v is not None)
    _on_main(root, toml)
    _touch(root, "web/page.html")
    _build_report(root, 1)
    # Both copy their fixture before either serves, as two reviewers started together may.
    together, copy = threading.Barrier(2, timeout=20), factory._fixture_copy

    def held(*args):
        served = copy(*args)
        together.wait()
        return served

    monkeypatch.setattr(factory, "_fixture_copy", held)
    codes: dict = {}

    def review(role: str) -> None:
        codes[role] = factory.cmd_agent(root, "008", "review", role, None)

    threads = [threading.Thread(target=review, args=(role,)) for role in ("ui", "ux")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    printed = capsys.readouterr().out
    assert codes == {"ui": 0, "ux": 0}, printed
    folder = root / ".sdlc" / "work" / NAME
    shots = root / ".sdlc" / "reports" / "shots" / NAME / "round-1"
    for role in ("ui", "ux"):
        assert (folder / "reviews" / "round-1" / f"{role}.md").is_file()
        assert (shots / role / "fixture" / "drafts").is_dir()
        prompt = next(c["argv"][1] for c in claude() if c["argv"][3].endswith(f"-{role}"))
        assert f"Screenshots: {(shots / role / 'index-390x844.png').as_posix()}." in prompt


# ---------------------------------------------------------------- the step record (088)


def _step(root: Path) -> Path:
    return root / ".sdlc" / "work" / NAME / factory.STEP


def _fields(root: Path) -> dict:
    return factory.read_step(_step(root).read_text(encoding="utf-8"))


@pytest.mark.portable
def test_record_writes_the_step_it_read(tmp_path, capsys) -> None:
    """R1: every field is `verdicts`' own reading, a stop included."""
    root = _change(tmp_path)
    for setup in (lambda: None, lambda: _build_report(root, 1),
                  lambda: _review(root, 1, "code", "Looks fine to me!")):  # fmt: skip
        setup()
        _, out = _record(root, capsys, _head(root))
        got = _fields(root)
        assert got["step"] == out["next"]
        assert got["round"] == out["round"] and got["limit"] == out["limit"]
        assert got["reviewers"] == out["reviewers"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", got["since"])
    assert got["step"] == "stop" and _stopped(root).is_file(), "stopped.md does as it did"


@pytest.mark.portable
def test_record_writes_an_early_stops_reason(tmp_path, capsys) -> None:
    """2026-11-18-33: a run stopped early, `stuck` (a change its verifier kept two rounds running)
    or `untestable` (the requirements its builder says no test can show), has the reason in
    `runs/step.md` as `- STUCK:` and `- UNTESTABLE:` lines `read_step()` reads back, for the
    board's card; a run not stopped early has none; a stop's record carries them too."""
    root = tmp_path / "repo"
    _kept_again(_change(tmp_path))
    _, out = _record(root, capsys, _head(root))
    assert (out["next"], out["stuck"]) == ("approve", ["code: src/a.py:1: rename a"])
    text = (root / ".sdlc" / "work" / NAME / factory.STEP).read_text(encoding="utf-8")
    assert "\n- STUCK: code: src/a.py:1: rename a\n" in text, text
    got = factory.read_step(text)
    assert (got["stuck"], got["untestable"]) == (["code: src/a.py:1: rename a"], [])
    line = "R4: the drawer reads well: judged by eye, no test can show it"
    root = _change(tmp_path / "untestable")
    _build_report(root, 1, f"- UNTESTABLE: {line}\n")
    _round(root, 1)
    _, out = _record(root, capsys, _head(root))
    assert (out["next"], out["untestable"]) == ("approve", [line])
    got = _fields(root)
    assert (got["stuck"], got["untestable"]) == ([], [line])
    root = _change(tmp_path / "plain")
    _round(root, 1)
    _, out = _record(root, capsys, _head(root))
    assert out["next"] == "approve" and _fields(root)["stuck"] == [] == _fields(root)["untestable"]
    stop = factory.stop_text(NAME, "rerun", ["it broke"], stuck=["code: a"], untestable=[line])
    assert stop.endswith(f"- PROBLEM: it broke\n- STUCK: code: a\n- UNTESTABLE: {line}\n"), stop
    assert factory.stop_text(NAME, "rerun", ["it broke"]).endswith("- PROBLEM: it broke\n")


@pytest.mark.portable
def test_the_step_record_keeps_its_since_while_the_step_holds(
    tmp_path, capsys, monkeypatch
) -> None:
    """R2: a repeated reading keeps the time; a new step or round sets it anew."""
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: PASS")
    times = iter(["2026-11-17T10:00:00Z", "2026-11-17T10:05:00Z", "2026-11-17T10:09:00Z"])
    monkeypatch.setattr(factory, "_utc_now", lambda: next(times))
    _record(root, capsys, _head(root))
    assert (_fields(root)["step"], _fields(root)["round"]) == ("review", 1)
    _review(root, 1, "test", "VERDICT: PASS")
    _record(root, capsys, _head(root))
    assert _fields(root)["since"] == "2026-11-17T10:00:00Z", "reviewers still missing: same step"
    for role in ("security", "behaviour"):
        _review(root, 1, role, "VERDICT: PASS")
    _record(root, capsys, _head(root))
    assert (_fields(root)["step"], _fields(root)["since"]) == ("approve", "2026-11-17T10:05:00Z")


@pytest.mark.portable
def test_a_decide_record_keeps_the_step_it_paused_at(tmp_path, capsys) -> None:
    """R4's paused position: `decide` carries the step the record held before it."""
    root = _change(tmp_path)
    _build_report(root, 1)
    _record(root, capsys, _head(root))
    assert _fields(root)["step"] == "review"
    ledger = root / ".sdlc" / "work" / NAME / "decisions.md"
    ledger.write_text("- [ ] D1 (code round 1, blocking): soft or hard?\n", encoding="utf-8")
    _record(root, capsys, _head(root))
    _record(root, capsys, _head(root))
    assert (_fields(root)["step"], _fields(root)["after"]) == ("decide", "review")


@pytest.mark.portable
def test_the_step_record_never_reaches_the_loop(tmp_path, capsys) -> None:
    """R3: the reading is the same with the record present, absent or garbled, and `verdicts`
    without `--record` never writes it."""
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:1: a")

    def reading() -> dict:
        return _verdicts(root, capsys, _head(root))

    bare = reading()
    assert not _step(root).exists(), "verdicts alone wrote the step record"
    _record(root, capsys, _head(root))
    assert reading() == bare
    _step(root).write_text("STEP: approve\nROUND: 9\n", encoding="utf-8")
    assert reading() == bare
    _step(root).write_text("garbled \x00 text\n", encoding="utf-8")
    assert reading() == bare
    source = inspect.getsource(factory.loop_state)
    assert "STEP" not in source and "read_step" not in source


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


def _tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def _restart(root, capsys, words: str | None = None) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_restart, root, "008", words)


def _stage_of(root: Path) -> str:
    text = (root / ".sdlc" / "work" / NAME / "intent.md").read_text(encoding="utf-8")
    return factory.frontmatter(text)["stage"]


@pytest.mark.parametrize("tier", [1, 2])
def test_start_takes_back_an_escalated_change(tmp_path, capsys, tier) -> None:
    """R1: read-only, with what the restart will do."""
    root = _change(tmp_path, tier, "test")
    _escalated(root)
    before = _tree(root)
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0 and out["refusals"] == [], out["refusals"]
    restart = out["restart"]
    shown = (restart["archive"], restart["round"], restart["reconsider"])
    assert shown == ("decision-1.md", 4, True)
    assert restart["reasons"] == RECONSIDERED and out["spec"] is False
    assert _tree(root) == before, "start writes nothing"


def test_start_refuses_a_ready_or_unreadable_test_change(tmp_path, capsys) -> None:
    """R2: only an ESCALATE is taken back; a READY is ship's, and no decision is no restart."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    decision = folder / "decision.md"
    decision.write_text("DECISION: READY\n\nFine.\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 1 and "restart" not in out
    assert any("/sdlc:ship" in r and "/sdlc-factory:land" in r for r in out["refusals"])
    decision.write_text("I think it's fine.\n", encoding="utf-8")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 1 and any(factory.NO_DECISION in r for r in out["refusals"]), out
    decision.unlink()
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 1 and any("no decision.md" in r for r in out["refusals"])
    decision.write_text(RECONSIDERED, encoding="utf-8")
    code, out = _run(capsys, factory.cmd_start, root, "008", "spec")
    assert code == 1 and "restart" not in out, "a spec never restarts"


def test_restart_keeps_the_decision_as_history(tmp_path, capsys) -> None:
    """R3: the record, the archive byte for byte, then the stage, edited in place."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    before = (folder / "decision.md").read_bytes()
    code, out = _restart(root, capsys)
    assert code == 0, out
    assert (out["archive"], out["round"], out["stage"]) == ("decision-1.md", 4, "build")
    assert (folder / "decision-1.md").read_bytes() == before
    assert not (folder / "decision.md").exists()
    record = (folder / "build" / "round-4.restart.md").read_text(encoding="utf-8")
    assert record == "RESTART: decision-1.md\n"
    assert _stage_of(root) == "build"
    assert "id: 008" in (folder / "intent.md").read_text(encoding="utf-8")


def test_restart_numbers_archives_from_one_and_never_overwrites(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    _restart(root, capsys)
    first = (folder / "decision-1.md").read_bytes()
    # The second run: round 4 built and reviewed, escalated again.
    _round(root, 4)
    (folder / "decision.md").write_text("DECISION: ESCALATE\n\nAgain.\n", encoding="utf-8")
    _run(capsys, factory.cmd_stage, root, "008", "test")  # the hand-back
    code, out = _restart(root, capsys)
    assert code == 0 and (out["archive"], out["round"]) == ("decision-2.md", 5)
    assert (folder / "decision-1.md").read_bytes() == first
    assert (folder / "decision-2.md").read_text() == "DECISION: ESCALATE\n\nAgain.\n"
    # An archive already there under the next number is never written over.
    (folder / "decision.md").write_text("DECISION: ESCALATE\n\nThird.\n", encoding="utf-8")
    _run(capsys, factory.cmd_stage, root, "008", "test")
    (folder / "decision-9.md").write_text("kept\n", encoding="utf-8")
    code, out = _restart(root, capsys)
    assert code == 0 and out["archive"] == "decision-10.md", "one past the highest"
    assert (folder / "decision-9.md").read_text() == "kept\n"


def test_restart_refuses_to_overwrite_an_archive(tmp_path, capsys, monkeypatch) -> None:
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    (folder / "decision-1.md").write_text("kept\n", encoding="utf-8")
    monkeypatch.setattr(factory, "next_archive", lambda folder: 1)
    code, out = _restart(root, capsys)
    assert code == 1 and "decision-1.md" in out["refusals"][0]
    assert (folder / "decision-1.md").read_text() == "kept\n"
    assert (folder / "decision.md").exists() and _stage_of(root) == "test"


def test_restart_moves_no_head(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "test")
    _escalated(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the run so far")
    head = _head(root)
    code, _ = _restart(root, capsys)
    assert code == 0 and _head(root) == head
    changed = _git(root, "status", "--porcelain").splitlines()
    assert changed and all(f".sdlc/work/{NAME}/" in line for line in changed), changed


def test_restart_refuses_what_start_refuses(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "build")
    _build_report(root, 1)
    code, out = _restart(root, capsys)
    assert code == 1 and "stage: test" in out["refusals"][0]
    root = _change(tmp_path / "b", 2, "test")
    folder = _escalated(root)
    (folder / "decision.md").write_text("DECISION: READY\n", encoding="utf-8")
    code, out = _restart(root, capsys)
    assert code == 1 and "/sdlc:ship" in out["refusals"][0]
    assert not (folder / "build" / "round-4.restart.md").exists()


def test_a_restart_cut_short_finishes_on_rerun(tmp_path, capsys) -> None:
    """R4: the archive made and the record written, the stage still `test`."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    (folder / "decision.md").rename(folder / "decision-1.md")
    (folder / "build" / "round-4.restart.md").write_text("RESTART: decision-1.md\n")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0, out["refusals"]
    assert out["restart"]["record"] == "build/round-4.restart.md"
    assert (out["restart"]["archive"], out["restart"]["round"]) == ("decision-1.md", 4)
    code, out = _restart(root, capsys)
    assert code == 0 and out["stage"] == "build"
    assert sorted(p.name for p in folder.glob("decision*.md")) == ["decision-1.md"]
    assert _stage_of(root) == "build"


def test_restart_then_verdicts_builds_round_r(tmp_path, capsys, claude) -> None:
    """R5: a builder step at round R, then the gate and the review, as for any round."""
    root = _change(tmp_path, 2, "test")
    _escalated(root)
    _gate_config(root, "true")
    assert _verdicts(root, capsys)["next"] == "done", "escalated: the run is over"
    _restart(root, capsys)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["decision"]) == ("build", 4, None)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0 and out["to"].endswith("build/round-4.md"), out
    assert (_verdicts(root, capsys)["next"], _verdicts(root, capsys)["round"]) == ("gate", 4)
    _gate(root, capsys)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == ("review", 4, FULL)


def test_the_restart_prompt_carries_the_escalation(tmp_path, capsys, claude) -> None:
    """R6: a fresh builder, told the archive and its Reconsider section word for word."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    _restart(root, capsys)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    argv = claude()[-1]["argv"]
    prompt = argv[1]
    assert f".sdlc/work/{NAME}/decision-1.md" in prompt and "round 4" in prompt
    assert (
        "## Reconsider the approach\n\nSplit the writer from the format.\nThen build the CSV first."
        in prompt
    )
    assert "## Notes" not in prompt and "Nothing else." not in prompt
    assert argv[-2] == "--session-id" and argv[-1] == out["session"]
    assert (folder / "build" / "round-4.md").read_text().startswith("the report")

    # An ESCALATE with no Reconsider section: the prompt has no such heading.
    root = _change(tmp_path / "b", 2, "test")
    _round(root, 1)
    plain = "DECISION: ESCALATE\n\nD2 is still assumed.\n"
    (root / ".sdlc" / "work" / NAME / "decision.md").write_text(plain, encoding="utf-8")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0 and out["restart"]["reconsider"] is False and out["restart"]["round"] == 2
    _restart(root, capsys)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    prompt = claude()[-1]["argv"][1]
    assert code == 0 and "decision-1.md" in prompt and "Reconsider" not in prompt


def test_the_restart_prompt_carries_the_persons_words(tmp_path, capsys, claude) -> None:
    """R6, R12: the person's words reach the builder through the ledger, by id alone."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    code, out = _restart(root, capsys, "R1")
    assert code == 1 and "R1" in out["refusals"][0], "no such line yet"
    assert (folder / "decision.md").exists(), "a refused restart writes nothing"
    words = 'keep the CSV writer; "split" it & $(nothing) runs'
    (folder / "decisions.md").write_text(
        f"# Decisions\n\n- [x] R1 (person, restart): {words}\n", encoding="utf-8"
    )
    code, out = _restart(root, capsys, "R1")
    assert code == 0, out
    record = (folder / "build" / "round-4.restart.md").read_text(encoding="utf-8")
    assert record == "RESTART: decision-1.md\nWORDS: R1\n"
    assert factory.read_ledger(folder) == [], "a restart's words are no decision the loop waits on"
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    told = claude()[-1]["argv"][1]
    assert code == 0 and told.endswith(f"The person adds: {words}\n\n{factory.check_line(folder)}")


def test_the_round_limit_counts_from_the_restart(tmp_path, capsys) -> None:
    """R7: escalated at round 3 of 3, restarted, round 4 with a kept change is a rework."""
    root = _change(tmp_path, 2, "test")
    _escalated(root)
    _restart(root, capsys)
    _round(root, 4, code="CHANGES")
    _verified(root, 4, kept=["code: code fix 4"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["limit"]) == ("rework", 4, 6)
    for n in (5, 6):
        _round(root, n, code="CHANGES")
        _verified(root, n, kept=[f"code: code fix {n}"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["exhausted"]) == ("approve", True), "and it can run out again"


def test_a_restarted_light_run_stays_light_and_a_full_one_stays_full(tmp_path, capsys) -> None:
    """R8: a round's place in its own run, not its number, says whether it ran beyond light."""
    root = _change(tmp_path, 2, "test", config=LISTED)
    _touch(root, "src/a.py")
    folder = root / ".sdlc" / "work" / NAME
    for n in (1, 2):
        _build_report(root, n)
        _review(root, n, "code", "VERDICT: CHANGES", f"src/a.py:{n}: move it")
        _verified(root, n, kept=[f"code: src/a.py:{n}: move it"])
    (folder / "decision.md").write_text(RECONSIDERED, encoding="utf-8")
    _restart(root, capsys)
    _build_report(root, 3)
    _review(root, 3, "code", "VERDICT: CHANGES", "src/a.py:3: move it")
    out = _verdicts(root, capsys)
    assert (out["depth"], out["limit"]) == ("light", 4), out["why"]

    root = _change(tmp_path / "b", 2, "test", config=LISTED)
    _touch(root, "src/a.py")
    _round(root, 1)
    (root / ".sdlc" / "work" / NAME / "decision.md").write_text("DECISION: ESCALATE\n\nNo.\n")
    _restart(root, capsys)
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert out["depth"] == "full" and "never lightens" in out["why"]


def test_a_restart_round_gets_its_own_gate_fixes(tmp_path, capsys) -> None:
    """R9: round N's red gates never count against round R."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    attempt = "## Attempt {k}\n\nVerdict: FAIL\nBuild: 0\nExit: 3\n\n"
    text = "GATE: FAIL\n\n" + attempt.format(k=1) + attempt.format(k=2)
    (folder / "build" / "round-3.gate.md").write_text(text, encoding="utf-8")
    _gate_config(root, "exit 3")
    _restart(root, capsys)
    _build_report(root, 4)
    _gate(root, capsys)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["gate"]["fails"]) == ("fix", 4, 1)


@pytest.mark.parametrize(
    "record, problem",
    [
        ("Restarted from the first decision.\n", "doesn't open with RESTART"),
        ("RESTART: decision-7.md\n", "decision-7.md, which doesn't exist"),
        ("RESTART: decision-1.md\nWORDS: R3\n", "R3"),
    ],
)
def test_a_bad_restart_record_stops_the_run(tmp_path, capsys, record, problem) -> None:
    """R10."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    _restart(root, capsys)
    (folder / "build" / "round-4.restart.md").write_text(record, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun")
    assert any(problem in p for p in out["problems"]), out["problems"]


def test_a_restarted_change_is_not_ready(tmp_path, capsys) -> None:
    """R11: only the current decision.md makes a change ready; an archive never does."""
    root = _change(tmp_path, 2, "test")
    folder = _escalated(root)
    assert [r["change"] for r in _run(capsys, factory.cmd_ready, root)[1]["ready"]] == [NAME]
    _restart(root, capsys)
    assert _run(capsys, factory.cmd_ready, root)[1]["ready"] == []
    assert factory.read_decision(folder) == (None, None)
    _round(root, 4)
    (folder / "decision.md").write_text("DECISION: READY\n\nDone now.\n", encoding="utf-8")
    _run(capsys, factory.cmd_stage, root, "008", "test")
    ready = _run(capsys, factory.cmd_ready, root)[1]["ready"]
    assert [(r["change"], r["decision"]) for r in ready] == [(NAME, "READY")]


# ---------------------------------------------------------------- a build starts current (101)

needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _behind(tmp_path: Path, slug: str = "fresh") -> tuple[Path, Path]:
    """A host repo and a change made by `sdlc.py new --worktree`, its folder uncommitted, as
    `/sdlc:intent` leaves one: (main checkout, the change's worktree)."""
    root = tmp_path / "host"
    root.mkdir(parents=True)
    (root / "README.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    code, _, said = factory._sdlc(["new", slug, "--tier", "2", "--worktree"], root)
    assert code == 0, said
    tree = next(p for p in (root / ".claude" / "worktrees").iterdir() if p.name.endswith(slug))
    return root, tree


def _commit_on_main(root: Path, name: str, text: str) -> None:
    (root / name).write_text(text, encoding="utf-8")
    _git(root, "add", name)
    _git(root, "commit", "-q", "-m", f"main changes {name}")


def _files(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*")
            if p.is_file()}  # fmt: skip


def _no_stash_or_merge(root: Path) -> None:
    assert _git(root, "stash", "list") == "", "never a stash"
    assert _git(root, "rev-list", "--merges", "--all") == "", "never a merge"


@needs_uv
def test_fresh_fast_forwards_a_change_behind_the_base(tmp_path, capsys) -> None:
    """101 R2: a change with no commits of its own, two behind, moves onto `main`'s tip through
    `sdlc.py base`, its uncommitted folder carried across byte for byte, with the undo."""
    root, tree = _behind(tmp_path)
    folder = tree / ".sdlc" / "work" / tree.name
    _commit_on_main(root, "one.txt", "1\n")
    _commit_on_main(root, "two.txt", "2\n")
    before, files = _git(tree, "rev-parse", "HEAD"), _files(folder)
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"], out["behind"]) == (0, "fast-forwarded", 2), out
    assert _git(tree, "rev-parse", "HEAD") == _git(root, "rev-parse", "main")
    assert before.startswith(out["from"]) and out["head"] == _git(tree, "rev-parse", "--short",
                                                                  "HEAD")  # fmt: skip
    assert f"reset --keep {before}" in out["undo"] and out["refusals"] == []
    assert _files(folder) == files, "the change's folder, as it was"
    _no_stash_or_merge(root)
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"], out["behind"]) == (0, "current", 0), out


def test_fresh_holds_a_run_that_stopped_part_way(tmp_path, capsys, monkeypatch) -> None:
    """101 R3: at `stage: build` its rounds were gated and reviewed on the base they had, so
    nothing moves, and `sdlc.py` isn't run at all."""
    root = _change(tmp_path, 2, "build")
    _main_moves(root, "one.txt")
    monkeypatch.setattr(factory, "_sdlc", lambda *a: pytest.fail("held: nothing to run"))
    head = _git(root, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"], out["behind"]) == (0, "held", 1), out
    assert "landing rebases and gates it again" in out["reason"]
    assert _git(root, "rev-parse", "HEAD") == head and out["head"] == out["from"]


def test_fresh_refuses_a_stage_no_fresh_run_starts_from(tmp_path, capsys, monkeypatch) -> None:
    root = _change(tmp_path, 2, "test")
    monkeypatch.setattr(factory, "_sdlc", lambda *a: pytest.fail("refused: nothing to run"))
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"]) == (1, "refused") and "no decision.md" in out["refusals"][0]
    root = _change(tmp_path / "b", 1, "design")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert code == 1 and "tier 1 at stage: design" in out["refusals"][0], out
    root = _change(tmp_path / "c", 2, "test")
    _escalated(root)
    ran = []
    monkeypatch.setattr(factory, "_sdlc", lambda args, cwd: ran.append(args) or (
        0, {"action": "current", "undo": None}, ""))  # fmt: skip
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"], ran) == (0, "current", [["base", NAME]]), "a restart starts fresh"


@needs_uv
def test_fresh_resolves_what_git_can_and_stops_on_a_real_conflict(tmp_path, capsys) -> None:
    """101 R4: (a) uncommitted work `main` then changes differently: `resolve` meets a real
    conflict, `fresh` aborts it and refuses, the worktree as it found it; (b) a commit of its own
    and uncommitted work, `main` changing another file: resolved, the work still uncommitted."""
    root, tree = _behind(tmp_path / "a")
    folder = tree / ".sdlc" / "work" / tree.name
    (tree / "README.md").write_text("the change's one\ntwo\nthree\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "main's one\ntwo\nthree\n")
    head, files, status = _git(tree, "rev-parse", "HEAD"), _files(folder), _git(tree, "status")
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"]) == (1, "refused"), out
    assert "README.md" in out["refusals"][0] and "/sdlc:ship" in out["refusals"][0]
    assert _git(tree, "rev-parse", "HEAD") == head and out["head"] == out["from"]
    assert (tree / "README.md").read_text(encoding="utf-8") == "the change's one\ntwo\nthree\n"
    assert _files(folder) == files and _git(tree, "status") == status
    _no_stash_or_merge(root)

    root, tree = _behind(tmp_path / "b")
    (tree / "mine.txt").write_text("a commit of its own\n", encoding="utf-8")
    _git(tree, "add", "mine.txt")
    _git(tree, "commit", "-q", "-m", "the change's own")
    (tree / "README.md").write_text("the change's one\ntwo\nthree\n", encoding="utf-8")
    _commit_on_main(root, "other.txt", "elsewhere\n")
    code, out = _run(capsys, factory.cmd_fresh, tree, "001")
    assert (code, out["state"]) == (0, "resolved"), out
    assert "--abort" in out["undo"]
    main = _git(root, "rev-parse", "main")
    assert _git(tree, "rev-parse", "HEAD^") == main, "its own commit, onto main's tip"
    assert (tree / "README.md").read_text(encoding="utf-8").startswith("the change's one")
    assert "README.md" in _git(tree, "status", "--porcelain"), "the work still uncommitted"
    _no_stash_or_merge(root)


def test_fresh_refuses_without_its_own_sdlc(tmp_path, capsys, monkeypatch) -> None:
    """101 R5: no `sdlc.py` of the factory's version, and nothing moves."""
    root = _change(tmp_path, 2, "design")
    _main_moves(root, "one.txt")
    monkeypatch.setattr(factory, "sdlc_path", lambda *a: (None, "no sdlc 9.9 beside this factory"))
    head = _git(root, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"]) == (1, "refused") and "no sdlc 9.9" in out["refusals"][0], out
    assert _git(root, "rev-parse", "HEAD") == head


# ---------------------------------------------------------------- gates share the machine (101)

FACTORY_PY = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
# A gate that stamps when it starts and ends, from the worktree it runs in, and takes a second.
STAMP = (
    "import os, sys, time\n"
    "with open(sys.argv[2], 'a', encoding='utf-8', newline='\\n') as f:\n"
    "    f.write(f'{os.path.basename(os.getcwd())} {sys.argv[1]} {time.time()}\\n')\n"
)


def _second_change(root: Path, tmp_path: Path) -> Path:
    """Another change, `009-other`, in its own worktree of `root`'s repo, with a build report."""
    tree = tmp_path / "other"
    _git(root, "worktree", "add", "-q", "-b", "009-other", str(tree), "main")
    folder = tree / ".sdlc" / "work" / "009-other"
    (folder / "build").mkdir(parents=True)
    text = INTENT.format(tier=2, stage="build").replace("008", "009")
    (folder / "intent.md").write_text(text.replace("reopen-drafts", "other"), encoding="utf-8")
    (folder / "build" / "round-1.md").write_text("Built.\n" + EVIDENCE, encoding="utf-8")
    return tree


@pytest.mark.parametrize("jobs", [1, 2])
def test_two_gates_with_a_limit_of_one_run_one_after_the_other(tmp_path, jobs) -> None:
    """101 R8, R9: two changes' gates started at once in two worktrees. With `gate_jobs = 1` the
    second waits for the first's slot, says so, and its wait isn't in its time; with 2 they run
    side by side, so the limit is what orders them."""
    root = _change(tmp_path)
    log, stamp = tmp_path / "stamps.log", tmp_path / "stamp.py"
    stamp.write_text(STAMP, encoding="utf-8")
    py = Path(sys.executable).as_posix()
    run = f'"{py}" "{stamp.as_posix()}" {{}} "{log.as_posix()}"'
    _gate_config(root, f"{run.format('start')} && sleep 1 && {run.format('end')}")
    _on_main(root, f"gate_jobs = {jobs}\n")
    _build_report(root, 1)
    other = _second_change(root, tmp_path)
    gates = [
        subprocess.Popen([sys.executable, str(FACTORY_PY), "gate", ident], cwd=tree,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        for tree, ident in ((root, "008"), (other, "009"))
    ]  # fmt: skip
    done = [g.communicate(timeout=60) for g in gates]
    assert [g.returncode for g in gates] == [0, 0], done
    outs = [json.loads(out) for out, _ in done]
    times: dict[str, dict[str, float]] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        where, what, when = line.split()
        times.setdefault(where, {})[what] = float(when)
    (a, b) = times.values()
    overlap = a["start"] < b["end"] and b["start"] < a["end"]
    waiting = [err for _, err in done if "waiting for a gate slot" in err]
    if jobs == 1:
        assert not overlap, times
        assert len(waiting) == 1 and "(1 of 1 in use)" in waiting[0], done
        waited = max(outs, key=lambda o: o["waited"])
        assert waited["waited"] >= 0.5 and waited["seconds"] < 1.8, outs
        assert min(o["waited"] for o in outs) == 0.0
    else:
        assert overlap, times
        assert not waiting and [o["waited"] for o in outs] == [0.0, 0.0], done


HOLD = """\
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("factory_child", sys.argv[1])
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)
with factory.gate_slot(Path(sys.argv[2]), 1, "008-reopen-drafts") as (slot, waited):
    print(f"held {slot}", flush=True)
    time.sleep(60)
"""


@pytest.mark.portable
def test_a_killed_gate_frees_its_slot(tmp_path) -> None:
    """101 R10: a slot is a lock on an open descriptor, so the OS frees it however its gate ends,
    and the next gate takes it at once."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD, str(FACTORY_PY), str(root)],
        stdout=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        assert child.stdout.readline().strip() == "held 0"
        lock = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        lock = lock / "sdlc-factory-gate-0.lock"
        fd = os.open(lock, os.O_RDWR)
        try:
            assert not factory._try_lock(fd), "held while its gate runs"
        finally:
            os.close(fd)
    finally:
        child.kill()
        child.wait()
    import time

    start = time.monotonic()
    with factory.gate_slot(root, 1, NAME) as (slot, waited):
        assert slot == 0
    assert time.monotonic() - start < 2, "the slot outlived its gate"
    assert lock.is_file(), "the file stays; only the lock goes"


# A child that holds slot 0 through `sdlc.py`'s `_hand_slot()`, the hand gate's, until killed.
HOLD_HAND = """\
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("sdlc_child", sys.argv[1])
sdlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdlc)
with sdlc._hand_slot(Path(sys.argv[2]), 1, "009-other", 60) as (slot, waited):
    print(f"held {slot}", flush=True)
    time.sleep(60)
"""


def test_a_factory_gate_waits_for_a_hand_gates_slot(tmp_path) -> None:
    """113 R2: a slot `sdlc.py gate` holds is one the factory's gate waits for, and takes once
    the hand gate ends."""
    import time

    root = _change(tmp_path)
    _gate_config(root, "true")
    _build_report(root, 1)
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD_HAND, str(ROOT / "scripts" / "sdlc.py"), str(root)],
        stdout=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        assert child.stdout.readline().strip() == "held 0"
        gate = subprocess.Popen(
            [sys.executable, str(FACTORY_PY), "gate", "008"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
        )  # fmt: skip
        line = gate.stderr.readline()
        assert f"{NAME}: waiting for a gate slot (1 of 1 in use)" in line, line
        time.sleep(0.6)
    finally:
        child.kill()
        child.wait()
    out, err = gate.communicate(timeout=60)
    assert gate.returncode == 0, (out, err)
    got = json.loads(out)
    assert got["waited"] >= 0.5 and got["slot"] == 0, got


# ---------------------------------------------------- agents' full runs take a slot too (155)


def test_check_runs_the_base_branchs_command_and_exits_with_its_code(tmp_path, capfd) -> None:
    """155 R1: the base branch's `[commands] check`, never the checkout's, its output straight
    through and its exit code the command's."""
    root = _change(tmp_path)
    _gate_config(root, "echo base-ran; exit 3")
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "echo mine"\n')
    code = factory.cmd_check(root, "008")
    out = capfd.readouterr().out
    assert code == 3 and "base-ran" in out and "mine" not in out, out


@pytest.mark.parametrize("case", ["no base", "no check", "no change"])
def test_check_refuses_and_runs_nothing(tmp_path, capfd, case) -> None:
    """155 R2: no base branch, no `[commands] check` on it, or no such change: a refusal, in
    `gate`'s words, and the command never runs."""
    root = _change(tmp_path)
    stamp = tmp_path / "ran"
    if case != "no check":
        _gate_config(root, f'touch "{stamp.as_posix()}"')
    if case == "no base":
        _git(root, "branch", "-q", "-m", "main", "trunk")
    ident = "099" if case == "no change" else "008"
    code = factory.cmd_check(root, ident)
    out = json.loads(capfd.readouterr().out)
    assert code == 1 and out["refusals"], out
    why = {"no base": "no base branch", "no check": "has no [commands] check", "no change": "099"}
    assert why[case] in out["refusals"][0], out
    assert not stamp.exists()


def test_two_checks_with_one_slot_run_one_after_the_other(tmp_path) -> None:
    """155 R3: two `check` runs at once in two worktrees, with `gate_jobs = 1`: the second waits
    for the first's slot and says so."""
    root = _change(tmp_path)
    log, stamp = tmp_path / "stamps.log", tmp_path / "stamp.py"
    stamp.write_text(STAMP, encoding="utf-8")
    py = Path(sys.executable).as_posix()
    run = f'"{py}" "{stamp.as_posix()}" {{}} "{log.as_posix()}"'
    _gate_config(root, f"{run.format('start')} && sleep 1 && {run.format('end')}")
    _on_main(root, "gate_jobs = 1\n")
    other = _second_change(root, tmp_path)
    checks = [
        subprocess.Popen([sys.executable, str(FACTORY_PY), "check", ident], cwd=tree,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        for tree, ident in ((root, "008"), (other, "009"))
    ]  # fmt: skip
    done = [c.communicate(timeout=60) for c in checks]
    assert [c.returncode for c in checks] == [0, 0], done
    times: dict[str, dict[str, float]] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        where, what, when = line.split()
        times.setdefault(where, {})[what] = float(when)
    (a, b) = times.values()
    assert not (a["start"] < b["end"] and b["start"] < a["end"]), times
    waiting = [err for _, err in done if "waiting for a gate slot (1 of 1 in use)" in err]
    assert len(waiting) == 1, done


def test_a_check_waits_for_a_gates_slot(tmp_path) -> None:
    """155 R3: a slot a gate holds is one `check` waits for: gates and checks share the slots."""
    import time

    root = _change(tmp_path)
    _gate_config(root, "echo checked")
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD, str(FACTORY_PY), str(root)],
        stdout=subprocess.PIPE, encoding="utf-8",
    )  # fmt: skip
    try:
        assert child.stdout.readline().strip() == "held 0"
        check = subprocess.Popen(
            [sys.executable, str(FACTORY_PY), "check", "008"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
        )  # fmt: skip
        line = check.stderr.readline()
        assert f"{NAME}: waiting for a gate slot (1 of 1 in use)" in line, line
        time.sleep(0.5)
        assert check.poll() is None, "it ran while the gate held the slot"
    finally:
        child.kill()
        child.wait()
    out, err = check.communicate(timeout=60)
    assert check.returncode == 0 and "checked" in out, (out, err)


def test_a_killed_check_frees_its_slot(tmp_path) -> None:
    """155 R4: the slot is a lock on `check`'s own descriptor, never inherited by the command it
    runs, so killing `check` frees it even while the command lives on."""
    import time

    root = _change(tmp_path)
    started = tmp_path / "started"
    _gate_config(root, f'touch "{started.as_posix()}"; sleep 30')
    check = subprocess.Popen(
        [sys.executable, str(FACTORY_PY), "check", "008"], cwd=root, start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    try:
        deadline = time.monotonic() + 30
        while not started.exists():
            assert time.monotonic() < deadline, "the command never started"
            time.sleep(0.05)
        check.kill()
        check.wait()
        start = time.monotonic()
        with factory.gate_slot(root, 1, NAME) as (slot, _):
            assert slot == 0
        assert time.monotonic() - start < 2, "the slot outlived its check"
    finally:
        import contextlib
        import signal

        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(check.pid, signal.SIGKILL)


def test_a_check_past_the_timeout_is_killed(tmp_path, capfd, monkeypatch) -> None:
    """155 R4: past `GATE_TIMEOUT` the command is killed, said on stderr, and `check` fails."""
    root = _change(tmp_path)
    _gate_config(root, "exec sleep 5")
    monkeypatch.setattr(factory, "GATE_TIMEOUT", 0.5)
    code = factory.cmd_check(root, "008")
    assert code != 0 and "timed out after 0.5s" in capfd.readouterr().err


def test_a_green_check_writes_nothing_and_never_clears_the_gate(tmp_path, capfd) -> None:
    """155 R5: a green `check` writes no record, leaves the folder as it was, and `verdicts`
    still asks for the gate: the script's gate stays the one proof of the suite."""
    root = _change(tmp_path)
    _gate_config(root, "true")
    _build_report(root, 1)
    rel = ".sdlc/work/" + NAME
    assert _verdicts(root, capfd)["next"] == "gate"
    before = _git(root, "status", "--porcelain", "--untracked-files=all", "--", rel)
    capfd.readouterr()
    assert factory.cmd_check(root, "008") == 0
    assert _git(root, "status", "--porcelain", "--untracked-files=all", "--", rel) == before
    assert not list((root / rel / "build").glob("*.gate.md"))
    capfd.readouterr()
    assert _verdicts(root, capfd)["next"] == "gate"


def test_the_builders_prompts_name_the_check_command(tmp_path, capsys) -> None:
    """155 R6: every prompt the builder is sent names the full `check` command, this factory's
    own script by its absolute path; no reviewer's, verifier's or approver's does."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    line = f"uv run --quiet --script {factory.FACTORY_SCRIPT.as_posix()} check 008"
    assert factory.FACTORY_SCRIPT.is_absolute()

    def prompt(state: dict, task: str, role: str, decided: str | None = None) -> str:
        planned = factory._task(root, folder, state, task, role, decided)
        assert not isinstance(planned, str), planned
        return planned[0]

    state, _ = factory.loop_state(root, "008", None)
    assert state["next"] == "build"
    assert line in prompt(state, "build", "builder")
    assert line in prompt({**state, "next": "fix", "round": 1}, "fix", "builder")
    _build_report(root, 1, "- DECISION: [default] Page at 50.\n")
    _run(capsys, factory.cmd_decisions, root, "008")
    path = folder / "decisions.md"
    path.write_text(path.read_text().replace("- [ ] D1", "- [x] D1").replace(
        "50.", "50. → decided: 50"))  # fmt: skip
    _round(root, 1, code="CHANGES")
    _verified(root, 1, kept=["code: code fix 1"])
    state, _ = factory.loop_state(root, "008", None)
    assert state["next"] == "rework", state
    assert line in prompt(state, "rework", "builder")
    assert line in prompt(state, "decided", "builder", "D1")
    assert line in prompt(state, "mend", "builder")
    for task, role, step in (("review", "code", "review"), ("verify", "verifier", "verify"),
                             ("approve", "approver", "approve")):  # fmt: skip
        told = prompt({**state, "next": step, "missing": ["code"]}, task, role)
        assert "check 008" not in told, (task, told)


def test_a_landing_verifiers_answer_names_its_landing_round(tmp_path) -> None:
    """111: a problem in a landing round's `verified.md` names the round `land-<n>`, as its file
    does, and a build round's names it `round <n>`."""
    reviews = {"code": {"verdict": "CHANGES", "changes": ["src/a.py:2: name it"]}}
    for kind, label in (("land", "land-1"), ("round", "round 1")):
        where = tmp_path / kind / "reviews" / f"{kind}-1"
        where.mkdir(parents=True)
        (where / "verified.md").write_text(
            "- KEPT: code: C9: made up\n- KEPT: code: src/b.py:1: reworded\n", encoding="utf-8"
        )
        _, problems = factory.read_verified(where / "verified.md", 1, reviews)
        assert f"C9, which no change of {label} is" in problems[1], problems
        assert f"reworded, which no review of {label} asks for" in problems[2], problems


def _held(listening: bool):
    """A socket holding a port on 127.0.0.1, as a parallel run's server would: one that answers,
    or one bound that a second server can't bind."""
    import socket

    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    if listening:
        held.listen()
    return held


def test_shots_take_a_new_port_when_theirs_is_lost(tmp_path, monkeypatch) -> None:
    """111: a port another process takes between `_free_port()` and the serve is tried again on a
    new one, and the record says so: taken before the serve started (it already answers), or bound
    so the serve exits before answering. Every try lost is a problem, with no server left."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    ui = _ui(tmp_path, pages=["/"], widths=[[390, 844]])
    answering, bound = _held(True), _held(False)
    ports = [answering.getsockname()[1], bound.getsockname()[1]]
    free = iter([*ports, factory._free_port()])
    monkeypatch.setattr(factory, "_free_port", lambda: next(free))
    try:
        paths, record = factory.shots(root, folder, "round-1", ui, "ui")
        assert record["problem"] is None and paths[0].is_file(), record
        assert [r["port"] for r in record["retries"]] == ports, record
        assert "already answered" in record["retries"][0]["why"], record
        assert "exited" in record["retries"][1]["why"], record
        assert record["port"] not in ports and f" {record['port']} " in record["serve"]
        assert not _alive(int((tmp_path / "server.pid").read_text()))
        monkeypatch.setattr(factory, "_free_port", lambda: ports[0])
        (tmp_path / "server.pid").unlink()
        _, record = factory.shots(root, folder, "round-2", ui, "ui")
        assert len(record["retries"]) == factory.SERVE_TRIES, record
        assert "already answered" in record["problem"], record
        assert not (tmp_path / "server.pid").exists(), "no server started on a port taken"
    finally:
        answering.close()
        bound.close()


def test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended(tmp_path) -> None:
    """111 round 3: every way `_up()` sees the server end decides lost the same way, by whether the
    port binds. One that answered, then exited with the port free, failed on its own; one whose
    port is still held (another's server answering) lost it."""

    class Ended:
        """A server running on `held` when first asked, exited 1 when asked again, letting the
        port go when `frees`."""

        returncode = 1

        def __init__(self, held, frees: bool) -> None:
            self.held, self.frees, self.asked = held, frees, 0

        def poll(self) -> int | None:
            self.asked += 1
            if self.asked == 1:
                return None
            if self.frees:
                self.held.close()
            return 1

    for frees, lost in ((True, False), (False, True)):
        held = _held(True)
        port = held.getsockname()[1]
        try:
            why, got = factory._up(Ended(held, frees), "127.0.0.1", port, 5)
        finally:
            held.close()
        assert why == f"port {port} answered, but the dev server had exited 1", why
        assert got is lost, (frees, why)


def test_a_server_that_answered_and_closed_first_has_not_lost_its_port(tmp_path) -> None:
    """111 round 4: a server that answered a real request, closing the connection first as a
    server ending its reply does (its port's side left in TIME_WAIT), then exited on its own,
    failed on its own: its port is free to bind again, so it is not lost."""
    import socket

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        conn, _ = listener.accept()
        conn.close()
        assert client.recv(1) == b"", "the server's side closed first"

    class Answered:
        """Running when first asked; exited 1, its port let go, when asked again."""

        returncode, asked = 1, 0

        def poll(self) -> int | None:
            self.asked += 1
            if self.asked == 1:
                return None
            listener.close()
            return 1

    try:
        why, lost = factory._up(Answered(), "127.0.0.1", port, 5)
    finally:
        listener.close()
    assert why == f"port {port} answered, but the dev server had exited 1", why
    assert lost is False, why


@pytest.mark.skipif(os.name == "nt", reason="Windows binds a held port with SO_REUSEADDR")
def test_a_port_a_wildcard_listener_holds_is_lost() -> None:
    """111 ship F1: a server holding its port on every address (`0.0.0.0`) holds it for
    `127.0.0.1` too, so the port reads as held and a server that lost it is retried."""
    import socket

    with socket.socket() as held:
        held.bind(("0.0.0.0", 0))
        held.listen()
        port = held.getsockname()[1]
        assert factory._binds("127.0.0.1", port) is False
        assert factory._lost("127.0.0.1", port) is True


def test_a_server_that_fails_on_its_own_is_started_once(tmp_path, monkeypatch) -> None:
    """A serve that exits before answering, on a port that still binds, failed on its own, not
    because another process took the port: one start, no retry, and its exit is the problem."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    starts = tmp_path / "starts"
    serve = f'echo started >> "{starts}"; exit 1'
    ports = []
    real = factory._free_port
    monkeypatch.setattr(factory, "_free_port", lambda: ports.append(real()) or ports[-1])
    _, record = factory.shots(root, folder, "round-1", _ui(tmp_path, serve, timeout=5), "ui")
    assert starts.read_text().splitlines() == ["started"], "started once"
    assert len(ports) == 1 and record["retries"] == [], record
    assert "exited 1 before answering" in record["problem"], record


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


def _upgrade(root, capsys) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_upgrade, root, "008")


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


@pytest.mark.portable
def test_verdicts_names_upgrade_on_an_upgrade_answer(tmp_path, capsys) -> None:
    """R3: a ticked blocking answer starting `upgrade to Tier 2`, in any case, on a Tier 1."""
    root, _ = _tier1_run(tmp_path)
    out = _verdicts(root, capsys)
    assert (out["next"], out["upgrading"], out["upgraded"]) == ("upgrade", "D1", None), out


@pytest.mark.portable
@pytest.mark.parametrize(
    "ledger, step",
    [
        (f"- [ ] D1 (builder round 1, blocking): {UPGRADE_Q}\n", "decide"),
        (
            f"- [x] D1 (builder round 1, default): {UPGRADE_Q} → decided: upgrade to Tier 2\n",
            "review",
        ),
        (
            f"- [x] D1 (builder round 1, blocking): {UPGRADE_Q} → superseded by D2 → decided: "
            "upgrade to Tier 2\n",
            "review",
        ),
        (
            f"- [x] D1 (builder round 1, blocking): {UPGRADE_Q} → decided: stay Tier 1, upgrade to "
            "Tier 2 later\n",
            "review",
        ),
    ],
    ids=["open", "default", "superseded", "another-answer"],
)
def test_only_a_decided_blocking_answer_upgrades(tmp_path, capsys, ledger, step) -> None:
    """R3: an open line, a default, a superseded line or another answer is never an upgrade."""
    root, _ = _tier1_run(tmp_path, ledger)
    out = _verdicts(root, capsys)
    assert (out["next"], out["upgrading"]) == (step, None), out


@pytest.mark.portable
def test_a_tier_2_answer_never_upgrades(tmp_path, capsys) -> None:
    """R3: only a Tier 1 change is upgraded."""
    root = _change(tmp_path, 2, "build")
    _build_report(root, 1)
    ledger = root / ".sdlc" / "work" / NAME / "decisions.md"
    ledger.write_text(UPGRADE_LINE, encoding="utf-8")
    assert _verdicts(root, capsys)["next"] == "review"


@needs_uv
def test_upgrade_writes_the_record_then_the_tier(tmp_path, capsys) -> None:
    """R4: refused unless verdicts names it; then the record, then sdlc.py's tier and scaffolds."""
    root, folder = _tier1_run(tmp_path, ledger=None)
    code, out = _upgrade(root, capsys)
    assert code == 1 and "not 'upgrade'" in out["refusals"][0], out
    assert not list((folder / "build").glob("*.upgraded.md"))
    (folder / "decisions.md").write_text(UPGRADE_LINE, encoding="utf-8")
    code, out = _upgrade(root, capsys)
    assert code == 0, out
    assert (out["change"], out["round"], out["decision"]) == (NAME, 2, "D1")
    assert (out["tier"], out["stage"], out["created"], out["kept"]) == (
        2,
        "plan",
        ["spec.md", "plan.md"],
        [],
    )
    assert (folder / "build" / "round-2.upgraded.md").read_text() == "UPGRADED: D1\n"
    meta = factory.frontmatter((folder / "intent.md").read_text(encoding="utf-8"))
    assert (meta["id"], meta["tier"], meta["stage"]) == ("008", "2", "plan")


@needs_uv
def test_upgrade_moves_no_head(tmp_path, capsys) -> None:
    """R4: it commits nothing, and writes only the change's folder."""
    root, _ = _tier1_run(tmp_path)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the run so far")
    head = _head(root)
    code, out = _upgrade(root, capsys)
    assert code == 0 and _head(root) == head, out
    changed = _git(root, "status", "--porcelain").splitlines()
    assert changed and all(f".sdlc/work/{NAME}/" in line for line in changed), changed


@needs_uv
def test_an_upgrade_cut_short_finishes_on_rerun(tmp_path, capsys) -> None:
    """R4: the record written, the tier still 1: verdicts names upgrade again, and the rerun sets
    the tier without a second record."""
    root, folder = _tier1_run(tmp_path)
    (folder / "build" / "round-2.upgraded.md").write_text("UPGRADED: D1\n", encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["upgrading"]) == ("upgrade", "D1"), out
    code, out = _upgrade(root, capsys)
    assert (code, out["round"], out["tier"]) == (0, 2, 2), out
    assert [p.name for p in (folder / "build").glob("*.upgraded.md")] == ["round-2.upgraded.md"]
    assert (folder / "build" / "round-2.upgraded.md").read_text() == "UPGRADED: D1\n"


@needs_uv
def test_no_second_upgrade(tmp_path, capsys) -> None:
    """R5: once upgraded, a later upgrade answer is no upgrade, and the command refuses."""
    root, folder = _tier1_run(tmp_path)
    assert _upgrade(root, capsys)[0] == 0
    ledger = folder / "decisions.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8")
        + "- [x] D2 (code round 2, blocking): Bigger still? → decided: upgrade to Tier 2 again\n",
        encoding="utf-8",
    )
    assert _verdicts(root, capsys)["next"] != "upgrade"
    code, out = _upgrade(root, capsys)
    assert code == 1 and out["refusals"], out
    assert [p.name for p in (folder / "build").glob("*.upgraded.md")] == ["round-2.upgraded.md"]
    assert not hasattr(factory, "cmd_downgrade")


@pytest.mark.portable
@pytest.mark.parametrize(
    "record, problem",
    [
        ("Upgraded on the person's word.\n", "doesn't open with UPGRADED"),
        ("UPGRADED: D2\n", "D2"),
    ],
)
def test_a_bad_upgrade_record_stops_the_run(tmp_path, capsys, record, problem) -> None:
    """A record that won't read, or names no decided upgrade answer, is a stop, never a guess."""
    root, folder = _tier1_run(tmp_path)
    _upgraded(root, folder)
    (folder / "build" / "round-2.upgraded.md").write_text(record, encoding="utf-8")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"]) == ("stop", "rerun"), out
    assert any(problem in p for p in out["problems"]), out["problems"]


def _approved(folder: Path) -> None:
    """Step 3 after the upgraded spec's yes: `write-spec`, then `stage design` and `stage build`."""
    (folder / "spec.md").write_text("# 008 — spec\n\n1. **R1.** Written.\n", encoding="utf-8")
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("stage: plan", "stage: build"), encoding="utf-8"
    )


@pytest.mark.portable
def test_an_upgraded_run_specs_then_builds_round_p(tmp_path, capsys) -> None:
    """R6: `spec` at P while the stage isn't build, `written` once the spec is, then `build`."""
    root, folder = _tier1_run(tmp_path)
    _upgraded(root, folder)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["written"]) == ("spec", 2, False), out
    assert out["upgraded"]["round"] == 2 and out["upgraded"]["decision"] == "D1"
    (folder / "spec.md").write_text("# 008 — spec\n\nWritten.\n", encoding="utf-8")
    _run(capsys, factory.cmd_stage, root, "008", "design")
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["written"]) == ("spec", 2, True), out
    _run(capsys, factory.cmd_stage, root, "008", "build")
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["limit"]) == ("build", 2, 4), out
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == ("review", 2, FULL), out


@pytest.mark.portable
def test_an_upgraded_run_counts_its_rounds_from_p(tmp_path, capsys) -> None:
    """R6: the limit, `exhausted` and the light depth's places all count from round P."""
    root, folder = _tier1_run(tmp_path)
    _upgraded(root, folder)
    _approved(folder)
    for n in (2, 3):
        _round(root, n, code="CHANGES")
        _verified(root, n, kept=[f"code: code fix {n}"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["limit"]) == ("rework", 3, 4), out
    _round(root, 4, code="CHANGES")
    _verified(root, 4, kept=["code: code fix 4"])
    out = _verdicts(root, capsys)
    assert (out["next"], out["exhausted"]) == ("approve", True), out

    root, folder = _tier1_run(tmp_path / "b", config=LISTED)
    _touch(root, "src/a.py")
    _upgraded(root, folder)
    _approved(folder)
    for n in (2, 3):
        _build_report(root, n)
        _review(root, n, "code", "VERDICT: CHANGES", f"src/a.py:{n}: move it")
        _verified(root, n, kept=[f"code: src/a.py:{n}: move it"])
    out = _verdicts(root, capsys)
    assert (out["depth"], out["limit"]) == ("light", 3), out["why"]


def test_the_spec_prompt_names_the_upgrade(tmp_path, capsys, claude) -> None:
    """R7: the round, the question and the answer, and the build so far; the reply only in runs/."""
    root, folder = _tier1_run(tmp_path)
    _upgraded(root, folder)
    scaffold = (folder / "spec.md").read_bytes()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "spec", None, None)
    assert code == 0 and out["to"].endswith("runs/spec-draft.md"), out
    prompt = claude()[-1]["argv"][1]
    assert "Draft spec.md" in prompt and "round 2" in prompt and "D1" in prompt
    assert UPGRADE_Q in prompt and "Upgrade to Tier 2: keep 30 days" in prompt
    assert "build so far" in prompt
    assert (folder / "spec.md").read_bytes() == scaffold, "spec.md waits for write-spec"


def test_the_upgraded_build_resumes_the_builder_into_round_p(tmp_path, capsys, claude) -> None:
    """R8: the builder's own session, told the answer and the spec, its report a new round-P."""
    root, folder = _tier1_run(tmp_path)
    (folder / "runs").mkdir()
    (folder / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    _upgraded(root, folder)
    _approved(folder)
    first = (folder / "build" / "round-1.md").read_bytes()
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0 and out["to"].endswith("build/round-2.md"), out
    argv = claude()[-1]["argv"]
    assert argv[-2:] == ["--resume", "s-1"], "resumed, never a new session"
    prompt = argv[1]
    assert "D1" in prompt and "Upgrade to Tier 2: keep 30 days" in prompt
    assert "Tier 2" in prompt and "spec.md" in prompt and "plan.md" in prompt
    assert "round 2" in prompt and "test first" in prompt
    assert (folder / "build" / "round-2.md").read_text().startswith("the report")
    assert (folder / "build" / "round-1.md").read_bytes() == first, "never added to round 1"
    assert (folder / "runs" / "builder.sessions").read_text() == "s-1\n"


def test_decided_refuses_while_an_upgrade_is_under_way(tmp_path, capsys, claude) -> None:
    """R9: the upgrading decision never, and no decision at upgrade, spec or round P's build."""
    other = "- [x] D2 (builder round 1, blocking): CSV or JSON? → decided: CSV\n"
    root, folder = _tier1_run(tmp_path, UPGRADE_LINE + other)
    (folder / "runs").mkdir()
    (folder / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")

    def refused(decision: str) -> list[str]:
        code, out = _run(capsys, factory.cmd_agent, root, "008", "decided", None, decision)
        assert code == 1, out
        return out["refusals"]

    assert _verdicts(root, capsys)["next"] == "upgrade"
    assert refused("D1") and refused("D2")
    _upgraded(root, folder)
    assert _verdicts(root, capsys)["next"] == "spec"
    assert refused("D1") and refused("D2")
    _approved(folder)
    assert _verdicts(root, capsys)["next"] == "build"
    assert refused("D1") and refused("D2")
    _build_report(root, 2)
    assert any("D1" in r for r in refused("D1")), "the upgrading decision, ever"
    assert claude() == [], "no agent ran"


def test_reviewers_and_approver_are_told_of_the_upgrade(tmp_path, capsys, claude) -> None:
    """R10: round P's reviewers, and the approver of an upgraded run."""
    root, folder = _tier1_run(tmp_path)
    _upgraded(root, folder)
    _approved(folder)
    _build_report(root, 2)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "code", None)
    assert code == 0, out
    prompt = claude()[-1]["argv"][1]
    assert "to Tier 2 before this round" in prompt and "spec.md" in prompt
    _round(root, 2)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "approve", None, None)
    assert code == 0, out
    prompt = claude()[-1]["argv"][1]
    assert "upgraded" in prompt and "round 2" in prompt and "D1" in prompt
    assert "spec.md" in prompt


@pytest.mark.portable
def test_start_reports_an_upgrade(tmp_path, capsys) -> None:
    """R11: `upgraded` with its round, decision and answer; null before."""
    root, folder = _tier1_run(tmp_path)
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0 and out["upgraded"] is None, out
    _upgraded(root, folder)
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 0 and out["spec"] is True, out
    assert out["upgraded"] == {
        "round": 2,
        "decision": "D1",
        "answer": "Upgrade to Tier 2: keep 30 days",
    }


@pytest.mark.portable
@pytest.mark.parametrize("stage", ["plan", "design", "build"])
def test_fresh_holds_an_upgraded_run(tmp_path, capsys, monkeypatch, stage) -> None:
    """R11: its earlier rounds were gated on the base they had, so nothing moves."""
    root, folder = _tier1_run(tmp_path)
    _upgraded(root, folder)
    _run(capsys, factory.cmd_stage, root, "008", stage)
    _main_moves(root, "one.txt")
    monkeypatch.setattr(factory, "_sdlc", lambda *a: pytest.fail("held: nothing to run"))
    head = _git(root, "rev-parse", "HEAD")
    code, out = _run(capsys, factory.cmd_fresh, root, "008")
    assert (code, out["state"]) == (0, "held"), out
    assert "upgraded" in out["reason"] and _git(root, "rev-parse", "HEAD") == head


@pytest.mark.portable
def test_the_upgraded_record_pattern_is_a_pinned_copy() -> None:
    """R12: `sdlc.py`'s `check` reads the record by its own copy of the factory's pattern."""
    assert sdlc.factory_records.UPGRADED_FILE_RE.pattern == factory.UPGRADED_FILE_RE.pattern
    assert sdlc.factory_records.UPGRADED_FILE_RE.match("round-12.upgraded.md").group(1) == "12"


@pytest.mark.portable
def test_an_upgrade_or_spec_record_keeps_the_step_it_paused_at(tmp_path, capsys) -> None:
    """R13: `AFTER:` on an `upgrade` and a `spec` reading, as on a `decide`; none once building."""
    root, folder = _tier1_run(tmp_path, ledger=None)
    _record(root, capsys, _head(root))
    assert _fields(root)["step"] == "review"
    (folder / "decisions.md").write_text(UPGRADE_LINE, encoding="utf-8")
    _record(root, capsys, _head(root))
    assert (_fields(root)["step"], _fields(root)["after"]) == ("upgrade", "review")
    _upgraded(root, folder)
    _record(root, capsys, _head(root))
    assert (_fields(root)["step"], _fields(root)["after"]) == ("spec", "review")
    _approved(folder)
    _record(root, capsys, _head(root))
    assert (_fields(root)["step"], _fields(root)["round"], _fields(root)["after"]) == (
        "build",
        2,
        None,
    )


# ---------------------------------------------------------------- the build gate's question

TAIL = (
    "a verifier checks each round's changes, the approver decides, at most 26 agent runs, agents "
    "in auto, all left uncommitted at stage: test?"
)


def _question(root: Path, capsys) -> str | None:
    _, out = _run(capsys, factory.cmd_start, root, "008", "build")
    return out["question"]


def test_start_words_the_build_question_without_a_spec(tmp_path, capsys) -> None:
    """The plain form, word for word as the skill held it: no gate, no sensitive list, no `[ui]`."""
    root = _change(tmp_path, 1, "plan")
    assert _question(root, capsys) == (
        f"Run the factory on {NAME}: the builder plans and builds it, with no gate configured, "
        "code, security, test and behaviour review it in up to 3 rounds, "
        + TAIL
        + " (yes / change the reviewers or rounds / no)"
    )


def test_the_build_question_names_the_base_branch_s_gate_and_light_depth(tmp_path, capsys):
    """The gate clause and the light parenthesis come from the base branch's config alone."""
    config = '[commands]\ncheck = "./check.sh"\n\n[review]\nsensitive = ["src/auth/"]\n'
    root = _change(tmp_path, 1, "plan", config=config)
    assert _question(root, capsys) == (
        f"Run the factory on {NAME}: the builder plans and builds it, the base branch's gate "
        "./check.sh runs on each build before any reviewer (up to 2 fixes a round), code, "
        "security, test and behaviour review it in up to 3 rounds (or code and behaviour in up "
        "to 2 rounds when the diff touches no sensitive path), "
        + TAIL
        + " (yes / change the reviewers or rounds / no)"
    )
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    assert "gate ./check.sh runs" in _question(root, capsys), "the change's own copy never counts"


UI_TABLE = '[ui]\nserve = "npm run dev"\nshoot = "shot {url} {out}"\npaths = ["web/", "*.css"]\n'


@pytest.mark.parametrize("missing", [None, "serve", "shoot", "paths"])
def test_the_build_question_names_ui_review_only_when_it_can_run(tmp_path, capsys, missing):
    root = _change(tmp_path, 1, "plan")
    ui = "\n".join(
        line for line in UI_TABLE.splitlines() if not missing or not line.startswith(missing)
    )
    _git(root, "checkout", "-q", "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    _commit_on_main(root, ".sdlc/factory.toml", ui + "\n")
    _git(root, "checkout", "-q", NAME)
    clause = (
        "review it in up to 3 rounds, and, on a diff touching web/, *.css, the ui and ux "
        "reviewers, which start npm run dev, a verifier"
    )
    assert (clause in _question(root, capsys)) is (missing is None)


def test_the_build_question_asks_to_write_a_spec_draft(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "plan")
    assert _question(root, capsys) == (
        f"Write this spec and run the factory on {NAME}: the builder plans and builds it, with no "
        "gate configured, code, security, test and behaviour review it in up to 3 rounds, "
        + TAIL
        + " (yes / revise a requirement / change the reviewers or rounds / no)"
    )


def test_the_build_question_sends_an_escalated_change_back(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, "test")
    _escalated(root)
    assert _question(root, capsys) == (
        f"Send {NAME} back to the factory: decision.md kept as decision-1.md, the builder rebuilds "
        "from round 4 with the approver's reasons, with no gate configured, code, security, test "
        "and behaviour review it in up to 3 more rounds, a verifier checks each round's changes, "
        "the approver decides again, at most 26 agent runs, agents in auto, all left uncommitted "
        "at stage: test? (yes / change the reviewers or rounds / no)"
    )


def test_the_build_question_carries_on_an_upgraded_run(tmp_path, capsys) -> None:
    root, folder = _tier1_run(tmp_path, config='[review]\nsensitive = ["src/auth/"]\n')
    _upgraded(root, folder)
    assert _question(root, capsys) == (
        f"Write this spec and carry on {NAME}'s factory run as Tier 2: the builder, resumed, "
        "rewrites plan.md against it and builds round 2, with no gate configured, code, security, "
        "test and behaviour review it in up to 3 more rounds (or code, test and behaviour in up "
        "to 2 rounds when the diff touches no sensitive path), a verifier checks each round's "
        "changes, the approver decides, at most 26 more agent runs, agents in auto, all left "
        "uncommitted at stage: test? (yes / revise a requirement / change the reviewers or "
        "rounds / no)"
    )


def test_no_build_question_for_a_refusal_or_a_tier_1_spec(tmp_path, capsys) -> None:
    root = _change(tmp_path, 2, "test")
    assert _question(root, capsys) is None, "a test change with no decision is refused"
    _, out = _run(capsys, factory.cmd_start, _change(tmp_path / "b", 1, "plan"), "008", "spec")
    assert out["refusals"] and out["question"] is None, "a Tier 1 change has no spec to ask about"
    code, out = _run(
        capsys, factory.cmd_start, _change(tmp_path / "c", branch="main-ish"), "008", "build"
    )
    assert code == 1 and out["question"] is None, "no worktree of its own"


def test_start_words_the_spec_question(tmp_path, capsys) -> None:
    """2026-11-18-10: the spec gate's question is the script's, as the build gate's is."""
    _, out = _run(capsys, factory.cmd_start, _change(tmp_path, 2, "plan"), "008", "spec")
    assert out["question"] == (
        f"Write this as .sdlc/work/{NAME}/spec.md and advance the change to stage: design? "
        "(yes / revise a requirement)"
    )


def test_no_build_question_without_a_base_branch(tmp_path, capsys) -> None:
    """125: the gate and depth clauses are the base branch's, so with none `start` refuses rather
    than word a question saying there is no gate."""
    root = _change(tmp_path, 1, "plan")
    _git(root, "branch", "-q", "-m", "main", "trunk")
    code, out = _run(capsys, factory.cmd_start, root, "008", "build")
    assert code == 1 and out["question"] is None
    assert "no base branch: set [git] base in .sdlc/config.toml" in out["refusals"]


@pytest.mark.parametrize(
    "names, said",
    [([], "no reviewer"), (["code"], "code"), (["code", "test"], "code and test"),
     (["code", "security", "test"], "code, security and test")],
)  # fmt: skip
def test_the_build_question_lists_reviewers_as_a_sentence(names, said) -> None:
    assert factory._listed(names) == said


# ---------------------------------------------------------------- escalations that clear (145)

GATE_REASON = "- ESCALATED: gate: tests/test_nothing_local.py fails on the behaviour record\n"
LOOK_REASON = "- ESCALATED: look: the drafts page reads oddly at phone width\n"


def _escalated_for(tmp_path: Path, capsys, *reasons: str) -> Path:
    """A change at `test` the approver escalated for `reasons`, round 1 built and reviewed, its
    ledger filed by `decisions`."""
    root = _change(tmp_path, stage="test")
    _round(root, 1)
    _decision(root, *reasons)
    _run(capsys, factory.cmd_decisions, root, "008")
    return root


def test_escalation_reasons_read_the_current_decision_alone(tmp_path) -> None:
    """145 R2: each `gate` and `look` line in order; an unknown word is a look; a `D<n>` line is
    the weighing's, never a reason; an archived decision is never read."""
    root = _change(tmp_path, stage="test")
    folder = root / ".sdlc" / "work" / NAME
    _decision(
        root,
        "- ESCALATED: D2: the page size is the product's call\n",
        GATE_REASON,
        "- ESCALATED: taste: the copy is flat\n",
        LOOK_REASON,
    )
    (folder / "decision-1.md").write_text(
        "DECISION: ESCALATE\n\n- ESCALATED: look: an old reason\n", encoding="utf-8"
    )
    assert factory.escalation_reasons(folder) == [
        {"kind": "gate", "text": "tests/test_nothing_local.py fails on the behaviour record"},
        {"kind": "look", "text": "taste: the copy is flat"},
        {"kind": "look", "text": "the drafts page reads oddly at phone width"},
    ]
    assert factory.approver_weighing(folder)[1].keys() == {"D2"}, "ESCALATED_RE reads D<n> alone"
    for line in (GATE_REASON, LOOK_REASON):
        assert not factory.ESCALATED_RE.match(line)
    (folder / "decision.md").unlink()
    assert factory.escalation_reasons(folder) == []


def test_a_look_reason_is_filed_once(tmp_path, capsys) -> None:
    """145 R3: a look reason becomes one `look` line, sourced by the newest round; a gate reason
    none; a rerun writes nothing."""
    root = _escalated_for(tmp_path, capsys, GATE_REASON, LOOK_REASON)
    assert _ledger_text(root) == (
        "# Decisions\n\n- [ ] D1 (approver round 1, look): the drafts page reads oddly at phone "
        "width\n"
    )
    before = _ledger_text(root)
    _, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert out["added"] == [] and _ledger_text(root) == before


def test_a_look_reason_is_filed_again_after_a_restart(tmp_path, capsys) -> None:
    """145 R3, R6: after a restart, the new decision's reason is a new line even with the same
    words, and the old line is history: never open, so never asked."""
    root = _escalated_for(tmp_path, capsys, LOOK_REASON)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "decision.md").rename(folder / "decision-1.md")
    assert [d["open"] for d in factory.read_ledger(folder)] == [False], "no current reason"
    _round(root, 2)
    _decision(root, LOOK_REASON)
    _, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert out["added"] == ["D2"], out
    ledger = factory.read_ledger(folder)
    assert [(d["id"], d["source"], d["open"]) for d in ledger] == [
        ("D1", "approver round 1", False),
        ("D2", "approver round 2", True),
    ]


def test_a_look_line_is_counted_in_no_ledger_figure(tmp_path, capsys) -> None:
    """145 R4: a look line is never pending, assumed or garbled, on the factory's, status's and
    the board's readings, and counts in no measured figure."""
    root = _escalated_for(tmp_path, capsys, LOOK_REASON)
    folder = root / ".sdlc" / "work" / NAME
    path = folder / "decisions.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "- [ ] D2 (builder round 1, blocking): keep drafts 30 days?\n"
        + "- [ ] D3 (builder round 1, default): page at 50\n"
        + "- [x] D4 (builder round 1, default): log ids → settled by the approver: R4\n",
        encoding="utf-8",
    )
    for pattern in (factory.LEDGER_RE, sdlc.factory_records.LEDGER_RE):
        assert pattern.match("- [ ] D1 (approver round 1, look): it reads oddly")
    reading = sdlc.factory_records.reading(folder)
    assert [d["id"] for d in reading["pending"]] == ["D2"]
    assert [d["id"] for d in reading["assumed"]] == ["D3"]
    assert [d["id"] for d in reading["looks"]] == ["D1"] and reading["problems"] == []
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "built")
    found = sdlc.closing._factory_files(root, NAME)
    assert (found["blocking"], found["defaults"], found["defaults_open"],
            found["defaults_settled"]) == (1, 2, 1, 1)  # fmt: skip
    assert _verdicts(root, capsys)["assumed"] == ["D3"]


def test_only_the_person_ticks_a_look_line(tmp_path, capsys) -> None:
    """145 R5: the approver's SETTLED is refused, a landing's yes never confirms one, and it is
    never an upgrade answer."""
    root = _escalated_for(tmp_path, capsys, LOOK_REASON)
    folder = root / ".sdlc" / "work" / NAME
    _decision(root, LOOK_REASON, "- SETTLED: D1: the copy is fine\n")
    before = _ledger_text(root)
    _, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert out["unsettled"] == [{"id": "D1", "why": "D1 is the person's to acknowledge"}], out
    assert _ledger_text(root) == before
    pre = {"undone": {"items": []}, "checks": {"checks": []}}
    parts = factory.landing.land_parts(folder, pre)
    assert parts["assumed"] == [], "a look is no default to confirm"
    (folder / "notes.md").write_text("# Notes\n", encoding="utf-8")
    factory.landing._dispose(root, folder, pre)
    assert _ledger_text(root) == before, "the landing's yes ticks no look line"
    path = folder / "decisions.md"
    path.write_text(before.replace("- [ ] D1", "- [x] D1").replace(
        "width\n", "width → decided: upgrade to Tier 2\n"), encoding="utf-8")  # fmt: skip
    assert factory.upgrade_answer(factory.read_ledger(folder)) is None


def test_ask_lists_look_items_and_the_gate(tmp_path, capsys) -> None:
    """145 R11: a look line is an item replying to decision.md; `gate` says each gate reason and
    whether it is cleared; with `--answered`, a look never means rebuild, and an uncleared gate
    reason alone means `gate`."""
    root = _escalated_for(tmp_path, capsys, GATE_REASON, LOOK_REASON)
    code, out = _run(capsys, factory.cmd_ask, root, "008", None)
    assert code == 0, out
    assert out["items"] == [{
        "id": "D1", "kind": "look", "source": "approver round 1", "reply": "decision.md",
        "question": "the drafts page reads oddly at phone width", "options": [], "why": None,
        "escalated": None,
    }]  # fmt: skip
    assert out["gate"] == {
        "reasons": [{"text": "tests/test_nothing_local.py fails on the behaviour record",
                     "cleared": False}],
        "record": f".sdlc/work/{NAME}/build/gate.md",
    }  # fmt: skip
    _answer(root, "D1", "seen")
    out = _run(capsys, factory.cmd_ask, root, "008", "D1")[1]
    assert (out["next"], out["then"]) == ("gate", "sdlc.py gate 008"), out


def test_ask_says_ship_once_a_look_is_seen_and_no_gate_is_owed(tmp_path, capsys) -> None:
    """145 R11: a look acknowledged in the person's own words is no rebuild."""
    root = _escalated_for(tmp_path, capsys, LOOK_REASON)
    _answer(root, "D1", "checked it at 390px: it reads fine")
    out = _run(capsys, factory.cmd_ask, root, "008", "D1")[1]
    assert out["next"] == "ship" and out["gate"] is None, out


def test_a_restart_makes_a_look_line_history(tmp_path, capsys) -> None:
    """145 R6: once a restart archives the decision that filed an open look line, the line is in
    none of `ask`'s items, `needs_of()`'s needs or the landing's signals."""
    root = _escalated_for(tmp_path, capsys, LOOK_REASON)
    folder = root / ".sdlc" / "work" / NAME
    (folder / "decision.md").rename(folder / "decision-1.md")
    _round(root, 2)
    _decision(root, GATE_REASON)
    _run(capsys, factory.cmd_decisions, root, "008")
    assert _ledger_text(root).count("- [ ] D1 (approver round 1, look)") == 1, "kept as written"
    out = _run(capsys, factory.cmd_ask, root, "008", None)[1]
    assert out["items"] == [], out
    reading = sdlc.factory_records.reading(folder)
    assert reading["looks"] == []
    rec = {"stage": "test", "problems": [], **reading}
    assert sdlc.needs_of(rec) == ["gate it green"]
    cfg = factory.load_config(root)[0]
    signals, _ = factory.landing.land_signals(folder, root, "ESCALATE", cfg, pre={})
    assert "decisions still open or assumed in decisions.md" not in signals, signals
