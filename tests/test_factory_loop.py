"""`factory.py`'s loop: its config, `start` and `stage`, which step `verdicts` reads next, the
stop and step records, verified rework and `carry`, and rounds that converge.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import copy
import inspect
import re
from pathlib import Path

import pytest
from factory_helpers import (
    FULL,
    NAME,
    RECONSIDERED,
    ROOT,
    _build_report,
    _change,
    _escalated,
    _fields,
    _fixed,
    _gate,
    _gate_config,
    _git,
    _head,
    _main_moves,
    _record,
    _report,
    _restart,
    _review,
    _round,
    _run,
    _step,
    _verdicts,
    _verified,
    factory,
    sdlc,
)

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
        "park": {"exit": None, "deadline": 60, "retry": 5},
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
    round's reviewers, arbiter, builder resume and the builder's two fixes of a red gate."""
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
    assert (_verdicts(root, capsys)["next"], _verdicts(root, capsys)["round"]) == ("arbitrate", 1)
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


def _stopped(root: Path) -> Path:
    return root / ".sdlc" / "work" / NAME / factory.STOPPED


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
    assert set(factory.WAYS) == set(factory.WAYS_WHY) == {"ship", "mend", "rerun", "parked"}
    # A `parked` stop names what is held and by whom (222 R9), here a short resource and holder.
    words = {"id": "008", "resource": "staging db", "holder": "219-other"}
    for way, text in factory.WAYS.items():
        line = text.format(**words)
        assert len(line) <= 90, (way, len(line))
        # A park's way on is freeing what it waits on: shipping by hand would gate it busy again.
        assert way == "parked" or "/sdlc:ship 008" in line, way
        assert way == "ship" or "/sdlc-factory:build 008" in line, way
        assert len(line) < len(factory.WAYS_WHY[way].format(**words)), way
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
    assert _verdicts(root, capsys)["next"] == "arbitrate"
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


def test_the_verify_prompt_numbers_each_change_once(tmp_path) -> None:
    root = _change(tmp_path)
    _build_report(root, 1)
    _review(root, 1, "test", "VERDICT: CHANGES", "src/a.py:1: test it", "src/a.py:1: test it")
    _review(root, 1, "code", "VERDICT: CHANGES", "src/a.py:2: name it", "src/b.py:3: split it")
    _review(root, 1, "security", "VERDICT: PASS")
    _review(root, 1, "behaviour", "VERDICT: PASS", "src/c.py:4: not asked, the verdict passed")
    folder = root / ".sdlc" / "work" / NAME
    state, _ = factory.run_state.loop_state(root, "008", None)
    prompt, target, _ = factory._task(root, folder, state, "arbitrate", "arbiter", None)
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
    prompt, _, _ = factory._land_task(root, folder, "land-arbitrate", "arbiter")
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
    state, _ = factory.run_state.loop_state(root, "008", None)
    prompt, _, _ = factory._task(
        root, root / ".sdlc" / "work" / NAME, state, "rework", "builder", None
    )
    assert "- code: src/b.py:3: split it" in prompt, "the builder gets the reviewer's words"
    assert "two things" not in prompt and "name it" not in prompt


def test_an_answer_in_its_own_words_resolves_by_its_lead(tmp_path, capsys) -> None:
    """A round as the factory's first real run wrote it: one change, dropped, the arbiter's
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


def test_nits_are_read_and_never_verified(tmp_path) -> None:
    """A reviewer's `- NIT:` lines are read apart from its changes: they never make a verdict
    CHANGES, never reach the arbiter and are never reworked."""
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
    state, _ = factory.run_state.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "arbitrate", "arbiter", None)
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
    test2.write_text(test2.read_text() + "- NIT: src/t.py:4: a vague name {tests M med}\n")
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
    assert "Disposition: recorded\nTheme: tests\nCost: M\nValue: med\nBy: test\n" in f6
    assert "{tests M med}" not in text, "the weights are read off the nit's text"
    assert "Theme:" not in text.split("## F6.", 1)[0], "only a nit to file has them"
    assert sdlc.findings_trailer(entries).endswith(" agents=6 passes=0 passes_wrong=0")
    assert "fixed=0" in sdlc.findings_trailer(entries), "an agent's nit is never ship's count"


def _nits(root: Path, n: int, role: str, *nits: str) -> None:
    """Add `- NIT:` lines to round `n`'s `role` review."""
    path = root / ".sdlc" / "work" / NAME / "reviews" / f"round-{n}" / f"{role}.md"
    path.write_text(path.read_text() + "".join(f"- NIT: {x}\n" for x in nits))


def _reworked(root: Path, *nits: str) -> Path:
    """Round 1: code asks for a change the arbiter keeps and raises `nits`; round 2, the rework,
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
    """129 R2, 230 R5: the script, never a model, turns each nit's weights into its disposition:
    an `S` or `M` of `med` value is recorded to file, of `low` value minor, `high` value an
    important finding and `L` cost an idea, both carried to notes.md, and a nit without weights
    minor, as before."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    _nits(
        root, 1, "code",
        "src/a.py:1: cheap and worth it {style S med}",
        "src/b.py:2: rename it {refactor M low}",
        "src/c.py:3: users hit it {robustness S high}",
        "src/d.py:4: rethink the module {design L med}",
        "src/e.py:5: no weights",
        "src/f.py:6: split it {refactor M med}",
    )  # fmt: skip
    code, out = _run(capsys, factory.cmd_carry, root, "008")
    assert code == 0
    assert _rows(folder) == [
        ("nit", "recorded", "src/a.py:1", None),
        ("nit", "minor", "src/b.py:2", factory.LOW_REASON),
        ("important", "recorded", "src/c.py:3", factory.HIGH_REASON),
        ("nit", "recorded", "src/d.py:4", factory.IDEA_REASON),
        ("nit", "minor", "src/e.py:5", factory.NIT_REASON),
        ("nit", "recorded", "src/f.py:6", None),
    ]  # fmt: skip
    assert out["added"] == [
        "code: src/c.py:3: users hit it",
        "code: src/d.py:4: rethink the module",
    ]
    notes = (folder / "notes.md").read_text(encoding="utf-8")
    assert "- [ ] code: src/c.py:3: users hit it\n" in notes and "{" not in notes
    filed = [i["file"]["text"] for i in factory.agent_findings(_carried_rounds(root)) if i["file"]]
    assert filed == ["src/a.py:1: cheap and worth it", "src/f.py:6: split it"], "S/M, med only"


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


def _nit_rows(rounds: list[dict]) -> list[tuple]:
    found = factory.agent_findings(rounds)
    return [(i["text"], i["disposition"], bool(i["file"])) for i in found if i["rank"] == "nit"]


def test_a_nit_a_later_round_raises_reworded_is_filed_once(tmp_path) -> None:
    """230 R1: a role's nits are filed from its last round only, so a nit raised again in other
    words is filed once, as the later round says it."""
    root = _change(tmp_path)
    _reworked(root, "src/a.py:3: X {style M med}")
    _nits(root, 2, "code", "src/a.py:4: X, reworded {style M med}")
    filed = [
        (i["round"], i["file"]["text"])
        for i in factory.agent_findings(_carried_rounds(root))
        if i["file"]
    ]
    assert filed == [(2, "src/a.py:4: X, reworded")]


def test_a_nit_no_later_round_raises_is_fixed_whatever_its_weights(tmp_path) -> None:
    """230 R2 (reversing 129 R5): a nit a later complete round of its role doesn't raise again is
    never filed, whatever its weights and whether or not a rework was handed it, a restart's first
    round counting as a later round."""
    weighed = (
        "src/a.py:1: one {style M low}",
        "src/b.py:2: two {style S low}",
        "src/c.py:3: three {style M med}",
        "src/d.py:4: four {style S med}",
    )
    unfiled = [(x.split(" {")[0], "fixed", False) for x in weighed]
    root = _change(tmp_path)
    _reworked(root, *weighed)
    assert _nit_rows(_carried_rounds(root)) == unfiled, "after a rework"

    root = _change(tmp_path / "unhanded")
    _round(root, 1)
    _nits(root, 1, "code", *weighed)
    _round(root, 2)
    rounds = _carried_rounds(root)
    assert _nit_rows(rounds) == unfiled, "no rework was handed them"
    rounds[1]["start"] = True
    assert _nit_rows(rounds) == unfiled, "a restart's first round is a later round"
    assert [r[1:] for r in _nit_rows(rounds[:1])] == [
        ("minor", False), ("minor", False), ("recorded", True), ("recorded", True)
    ], "with no later round, filed by their weights"  # fmt: skip


def test_a_nit_not_filed_says_why(tmp_path, capsys) -> None:
    """230 R3: an earlier round's nit left unfiled keeps its section in findings.md, with why:
    `fixed` when no later nit of its role names its path, `minor` when one does, reworded."""
    root = _change(tmp_path)
    folder = _reworked(root, "src/a.py:3: X {style M med}", "src/b.py:1: gone {style M low}")
    _nits(root, 2, "code", "src/a.py:4: X, reworded {style M med}")
    _run(capsys, factory.cmd_carry, root, "008")
    assert _rows(folder) == [
        ("important", "fixed", "reviews/round-1/code.md", None),
        ("nit", "minor", "src/a.py:3", factory.REPEAT_REASON.format(round=2)),
        ("nit", "fixed", "src/b.py:1", factory.FIXED_REASON),
        ("nit", "recorded", "src/a.py:4", None),
    ]  # fmt: skip
    assert factory.FIXED_REASON == "not raised again by a later round of its review"
    assert factory.REPEAT_REASON.format(round=2) == (
        "raised again, reworded, by round 2 of its review, which it is filed from"
    )
    assert not hasattr(factory, "HANDED_REASON"), "a handed nit is a case of FIXED_REASON"


def test_the_factory_files_no_low_value_nit(tmp_path, capsys) -> None:
    """230 R5: a weighed nit of `low` value is minor, below the factory's filing bar, so it never
    counts towards the landing's nits to file."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    _nits(
        root, 1, "code",
        "src/a.py:1: small {style S low}", "src/b.py:2: middling {style M low}",
        "src/c.py:3: worth it {style M med}",
    )  # fmt: skip
    _run(capsys, factory.cmd_carry, root, "008")
    assert [r[1:] for r in _rows(folder)] == [
        ("minor", "src/a.py:1", factory.LOW_REASON),
        ("minor", "src/b.py:2", factory.LOW_REASON),
        ("recorded", "src/c.py:3", None),
    ]
    assert factory.LOW_REASON == "weighed low value: below the factory's filing bar"
    rounds = _carried_rounds(root)
    assert [i["file"]["text"] for i in factory.agent_findings(rounds) if i["file"]] == [
        "src/c.py:3: worth it"
    ]


def test_a_landing_round_never_changes_the_nits_filed(tmp_path) -> None:
    """129 and 230 R6, at its landing: only the build's rounds are weighed, since the landing
    files its nits before a landing round reaches the record. A landing round that raises a handed
    cheap nit again leaves it fixed, and a nit only a landing round raised is minor, never one to
    file."""
    root = _change(tmp_path)
    _reworked(root, "src/a.py:1: cheap {style S med}", "src/b.py:2: rename it {refactor M med}")
    _nits(root, 2, "code", "src/b.py:2: rename it {refactor M med}")
    rounds = _carried_rounds(root)
    nits = _nit_rows
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
    _nits(root, 1, "code", "src/a1.py:1: one {style M med}", "the names are long {style M med}",
          *(f"src/a{i}.py:{i}: number {i} {{style M med}}" for i in range(2, 6)))  # fmt: skip
    _nits(root, 1, "test", "tests/t.py:1: six {tests S med}", "tests/u.py:2: seven {tests M med}")
    _run(capsys, factory.cmd_carry, root, "008")
    rows = _rows(folder)
    assert [r[1] for r in rows] == ["recorded", "minor", *["recorded"] * 4, "minor", "minor"]
    assert rows[1][3] == factory.NO_PATH_REASON
    assert rows[6][3] == rows[7][3] == factory.CAP_REASON
    assert factory.CAP_REASON == "past the cap of 5 nits a change files"
    assert factory.NO_PATH_REASON == "names no path, so it can't be filed as a nit"


def test_rework_hands_the_builder_its_cheap_nits(tmp_path) -> None:
    """129 R4: a rework round N lists round N's `S` `med` nits after its kept changes, in the
    reviewers' words; round N+1's review names to each role the ones it raised, to raise again any
    the rework didn't make."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    _nits(root, 1, "code", "src/a.py:1: cheap {style S med}", "src/b.py:2: later {style M low}")
    _nits(root, 1, "test", "[cost] tests/t.py:3: one fixture {tests S med}")
    _verified(root, 1, kept=["code: code fix 1"])
    state, _ = factory.run_state.loop_state(root, "008", None)
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
    state, _ = factory.run_state.loop_state(root, "008", None)
    assert (state["next"], state["round"]) == ("review", 2)
    prompt, _, _ = factory._task(root, folder, state, "review", "code", None)
    assert (
        " Nits handed to the builder last round: src/a.py:1: cheap; raise again, word for word "
        "with its weights, any the rework didn't make." in prompt
    )
    prompt, _, _ = factory._task(root, folder, state, "review", "security", None)
    assert "Nits handed" not in prompt, "security raised none"


def test_a_review_names_its_roles_earlier_nits(tmp_path, capsys) -> None:
    """230 R4: the review of round N+1 names to each role the nits it raised in its latest
    complete build round before, with their weights, to raise again any still true: never another
    role's, never one the handed part already names, and across a restart too."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1, code="CHANGES")
    _nits(root, 1, "code", "src/a.py:1: cheap {style S med}", "src/b.py:2: later {style M low}",
          "src/n.py:3: unweighed")  # fmt: skip
    _nits(root, 1, "test", "tests/t.py:3: one fixture {tests M med}")
    _verified(root, 1, kept=["code: code fix 1"])
    _build_report(root, 2)
    state, _ = factory.run_state.loop_state(root, "008", None)
    assert (state["next"], state["round"]) == ("review", 2)
    prompt, _, _ = factory._task(root, folder, state, "review", "code", None)
    assert (
        " Nits you raised in round 1: src/b.py:2: later {style M low}; src/n.py:3: unweighed;"
        " raise again, word for word with its weights, any that are still true." in prompt
    )
    assert prompt.count("src/a.py:1: cheap") == 1, "a handed nit is named once"
    assert "tests/t.py:3" not in prompt, "another role's nit"
    prompt, _, _ = factory._task(root, folder, state, "review", "test", None)
    assert "Nits you raised in round 1: tests/t.py:3: one fixture {tests M med};" in prompt
    assert "src/b.py:2" not in prompt
    prompt, _, _ = factory._task(root, folder, state, "review", "security", None)
    assert "Nits you raised" not in prompt, "security raised none"

    root = _change(tmp_path / "restarted", 2, "test")
    folder = root / ".sdlc" / "work" / NAME
    _escalated(root)
    _nits(root, 3, "code", "src/a.py:1: cheap {style S med}")
    assert _restart(root, capsys)[0] == 0
    _build_report(root, 4)
    state, _ = factory.run_state.loop_state(root, "008", None)
    assert (state["next"], state["round"], state["handed"]) == ("review", 4, [])
    prompt, _, _ = factory._task(root, folder, state, "review", "code", None)
    assert " Nits you raised in round 3: src/a.py:1: cheap {style S med};" in prompt


def test_a_round_with_only_nits_is_never_reworked(tmp_path, capsys) -> None:
    """129 R4: cheap nits and no kept change go to the approver, never to a rework; and a
    restart's first round starts fresh, handed nothing."""
    root = _change(tmp_path)
    _round(root, 1)
    _nits(root, 1, "code", "src/a.py:1: cheap {style S med}")
    state, _ = factory.run_state.loop_state(root, "008", None)
    assert (state["next"], state["handed"]) == ("approve", [])
    assert all(r["verdict"] == "PASS" for r in state["rounds"][0]["reviews"].values())

    root = _change(tmp_path / "restarted", 2, "test")
    _escalated(root)
    _nits(root, 3, "code", "src/a.py:1: cheap {style S med}")
    assert _restart(root, capsys)[0] == 0
    _build_report(root, 4)
    state, _ = factory.run_state.loop_state(root, "008", None)
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
    """`rounds` full rounds whose code reviewer asks for `change` each time and the arbiter keeps
    it, the rest passing."""
    for n in range(1, rounds + 1):
        _build_report(root, n)
        _review(root, n, "code", "VERDICT: CHANGES", change)
        for role in ("security", "test", "behaviour"):
            _review(root, n, role, "VERDICT: PASS")
        _verified(root, n, kept=[f"code: {change}"])
    return root / ".sdlc" / "work" / NAME


def test_a_change_kept_twice_escalates_before_the_rounds_run_out(tmp_path, capsys) -> None:
    """136 R3: the arbiter keeping the same `(role, change)` in two rounds of one run means a
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
    assert _verdicts(root, capsys)["next"] == "arbitrate", "verified first, as any round is"
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


def test_an_early_escalation_names_its_reason_to_the_approver(tmp_path) -> None:
    """136 R7: an approver sent a run that stopped early is told why, the repeated changes or the
    untestable lines, and asked to name its next step; a run with nothing kept is asked neither."""
    folder = _kept_again(_change(tmp_path))
    root = tmp_path / "repo"
    state, _ = factory.run_state.loop_state(root, "008", None)
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
    state, _ = factory.run_state.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "approve", "approver", None)
    assert f" The builder reports these requirements can't be tested: {line}." in prompt, prompt
    assert NEXT_STEP in prompt and "kept again" not in prompt
    root = _change(tmp_path / "plain")
    folder = root / ".sdlc" / "work" / NAME
    _round(root, 1)
    state, _ = factory.run_state.loop_state(root, "008", None)
    prompt, _, _ = factory._task(root, folder, state, "approve", "approver", None)
    assert NEXT_STEP not in prompt and "can't be tested" not in prompt


REASK = (
    "A kept change the rework didn't make, raise again word for word, as the prompt quotes it: the "
    "run tells a change kept twice by its words, and stops for the person rather than rework it a "
    "third time."
)


def test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word(tmp_path) -> None:
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
    state, _ = factory.run_state.loop_state(root, "008", None)
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
    assert out["next"] == "arbitrate"
    assert out["settled"] == ["code: src/a.py:1: add a doc", "code: src/a.py:1: rename a"]
    assert out["repeats"] == ["code: src/a.py:1: add a doc"]
    assert out["untouched"] == ["code: README.md:1: old"], "pre-existing, never reworked"


def test_a_change_asking_for_a_new_file_is_never_pre_existing(tmp_path, capsys) -> None:
    """The test reviewer's usual ask names a file that doesn't exist yet: the change is to create
    it, so it reaches the arbiter as any other, never as pre-existing."""
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


# ---------------------------------------------------------------- the step record (088)


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
def test_record_writes_the_runs_depth(tmp_path, capsys) -> None:
    """175 R6: every reading names its depth in `runs/step.md` as `DEPTH:`, read back as `depth`;
    a record without the line reads as None."""
    root = _change(tmp_path)
    _build_report(root, 1)
    _, out = _record(root, capsys, _head(root))
    assert out["depth"] in ("full", "light")
    text = _step(root).read_text(encoding="utf-8")
    assert f"DEPTH: {out['depth']}" in text.splitlines()
    assert _fields(root)["depth"] == out["depth"]
    assert factory.read_step("STEP: build\nROUND: 1\n")["depth"] is None
    assert "DEPTH" not in factory.step_text({"next": "build", "round": 1}, "2026-11-19T10:00:00Z")


@pytest.mark.portable
def test_record_writes_an_early_stops_reason(tmp_path, capsys) -> None:
    """2026-11-18-33: a run stopped early, `stuck` (a change its arbiter kept two rounds running)
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
    source = inspect.getsource(factory.run_state.loop_state)
    assert "STEP" not in source and "read_step" not in source
