"""The optional factory's mechanism: which change a run is in, whether its stage lets a step
start, what each review file's first line says, which step the loop takes next, and that a change
the agents built reads to `sdlc` like any other.

`factory.py` is loaded by path, like `sdlc.py`. Each test builds a scratch repo on a change branch
with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import importlib.util
import json
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


def _change(tmp_path: Path, tier: int = 2, stage: str = "design", branch: str = NAME) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
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
    (folder / f"{role}.md").write_text(f"{verdict}\n{body}\n## Notes\n\nFine.\n", encoding="utf-8")


def _build_report(root: Path, n: int, *lines: str) -> None:
    folder = root / ".sdlc" / "work" / NAME / "build"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"round-{n}.md").write_text("Built slice 1.\n" + "".join(lines), encoding="utf-8")


def _round(root: Path, n: int, **verdicts: str) -> None:
    """Review round `n`, as the loop makes one: after the builder's report for that round."""
    if not (root / ".sdlc" / "work" / NAME / "build" / f"round-{n}.md").exists():
        _build_report(root, n)
    for role in ("code", "security", "test"):
        verdict = verdicts.get(role, "PASS")
        changes = (f"{role} fix {n}",) if verdict == "CHANGES" else ()
        _review(root, n, role, f"VERDICT: {verdict}", *changes)


# ---------------------------------------------------------------- config


def test_config_defaults_and_its_warnings(tmp_path: Path) -> None:
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg == {"reviewers": ["code", "security", "test"], "rounds": 3, "models": {}}
    assert warnings == []
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "factory.toml").write_text(
        'reviewers = ["code", "secruity"]\nrounds = 9\nloops = 1\n'
        '[models]\nbuilder = "sonnet"\ndesigner = "opus"\n',
        encoding="utf-8",
    )
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["reviewers"] == ["code"] and cfg["rounds"] == 3
    assert cfg["models"] == {"builder": "sonnet"}
    assert any("unknown reviewer 'secruity'" in w for w in warnings)
    assert any("rounds must be" in w for w in warnings)
    assert "unknown key loops" in warnings
    assert any("unknown role 'designer'" in w for w in warnings)


def test_max_runs_is_shown_before_the_cost_is_approved() -> None:
    cfg = {"reviewers": ["code", "security", "test"], "rounds": 3, "models": {}}
    assert factory.max_runs(cfg) == 2 + 3 * 4


# ---------------------------------------------------------------- start


@pytest.mark.parametrize(
    "tier, stage, purpose, ok",
    [
        (2, "plan", "spec", True),
        (2, "design", "spec", False),
        (1, "plan", "spec", False),
        (2, "design", "build", True),
        (2, "plan", "build", False),
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
        assert out["change"] == NAME and out["max_runs"] == 14


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
    assert out["missing"] == ["code", "security", "test"]


def test_an_incomplete_round_is_reviewed_again_for_the_missing(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "code", "VERDICT: PASS")
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == ("review", 1, ["security", "test"])


def test_changes_rework_until_the_rounds_run_out(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, security="CHANGES")
    assert (_verdicts(root, capsys)["next"], _verdicts(root, capsys)["round"]) == ("rework", 1)
    # The step the first version got wrong: once the builder has reworked, round 2 is reviewed,
    # not reworked again.
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert (out["next"], out["round"], out["missing"]) == (
        "review",
        2,
        ["code", "security", "test"],
    )
    _round(root, 2, test="CHANGES")
    assert _verdicts(root, capsys)["next"] == "rework"
    _round(root, 3, test="CHANGES")
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
