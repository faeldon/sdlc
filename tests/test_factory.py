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
        "light": {"reviewers": ["code"], "rounds": 2},
        "models": {},
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
    assert cfg["models"] == {"builder": "sonnet"}
    assert any("unknown reviewer 'secruity'" in w for w in warnings)
    assert any("rounds must be" in w for w in warnings)
    assert "unknown key loops" in warnings
    assert any("unknown role 'designer'" in w for w in warnings)


def test_light_is_a_table_checked_like_the_top_level(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    config = tmp_path / ".sdlc" / "factory.toml"
    config.write_text('[light]\nreviewers = ["test"]\nrounds = 1\n', encoding="utf-8")
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["light"] == {"reviewers": ["test"], "rounds": 1} and warnings == []
    config.write_text('[light]\nreviewers = ["nobody"]\nrounds = 0\nloops = 2\n', encoding="utf-8")
    cfg, warnings = factory.load_config(tmp_path)
    assert cfg["light"] == {"reviewers": ["code"], "rounds": 2}, "a bad value keeps the default"
    assert "unknown key light.loops" in warnings
    assert any("unknown reviewer 'nobody' in light.reviewers" in w for w in warnings)
    assert any(w.startswith("light.rounds must be") for w in warnings)
    config.write_text('light = "deep"\n', encoding="utf-8")
    assert "light must be a table of reviewers and rounds" in factory.load_config(tmp_path)[1]


def test_max_runs_is_shown_before_the_cost_is_approved() -> None:
    """At the full depth, whatever the diff turns out to need: the builder, the approver, and each
    round's reviewers, verifier and builder resume."""
    cfg = {"reviewers": ["code", "security", "test"], "rounds": 3, "models": {}}
    assert factory.max_runs(cfg) == 2 + 3 * 5


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
        assert out["change"] == NAME and out["max_runs"] == 20, "2 + 3 rounds × (4 + 2)"


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


def test_carry_takes_the_kept_changes_and_the_pre_existing_problems(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _round(root, 1, code="CHANGES", security="CHANGES")
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "test.md"
    review.write_text(review.read_text() + "- PREEXISTING: src/old.py:3: an unclosed file\n")
    _verified(root, 1, kept=["code: code fix 1"], dropped=["security: security fix 1"])
    _, out = _run(capsys, factory.cmd_carry, root, "008")
    assert out["added"] == ["code: code fix 1", "pre-existing: src/old.py:3: an unclosed file"]


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
    root = _change(tmp_path, config=LISTED)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert (out["depth"], out["missing"], out["limit"]) == ("light", ["code"], 2)
    _review(root, 1, "code", "VERDICT: PASS")
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
    assert factory.max_runs(factory.load_config(tmp_path / "none")[0]) == 20


@pytest.mark.parametrize(
    "patterns",
    [["src/secret/"], ["*.toml"], ["check.sh", ".claude/*"], ["src/*/key.py"], []],
)
def test_the_risk_matcher_is_sdlc_s_own(patterns: list[str]) -> None:
    paths = ["src/secret/key.py", "check.sh", ".claude/settings.json", "pyproject.toml", "a.py"]
    assert factory.risk_paths(paths, patterns) == sdlc.risk_paths(paths, patterns)


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
    assert factory.bug_paths(fields.get("paths")) == sdlc._bug_paths(fields.get("paths"))


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
    assert factory.on_paths(evidence, paths) is sdlc._on_paths(evidence, paths)


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
