"""The decisions that are a person's: the ledger and a default's alternatives, the approver's
weighing, `ask`, an escalated change sent back (`restart`), a run upgraded to Tier 2, and
escalations that clear.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from factory_helpers import (
    FULL,
    LISTED,
    NAME,
    RECONSIDERED,
    UPGRADE_LINE,
    UPGRADE_Q,
    _build_report,
    _change,
    _escalated,
    _fields,
    _gate,
    _gate_config,
    _git,
    _head,
    _main_moves,
    _record,
    _restart,
    _review,
    _round,
    _run,
    _tier1_run,
    _touch,
    _upgraded,
    _verdicts,
    _verified,
    factory,
    needs_uv,
    sdlc,
)

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
         "settled": None, "options": [], "why": None, "current": True, "decided_by": None},
        {"id": "D2", "source": "code round 1", "kind": "blocking", "text": "Keep 30 days?",
         "decided": True, "open": False, "answer": "30 days", "superseded_by": None,
         "settled": None, "options": [], "why": None, "current": True, "decided_by": "person"},
    ]  # fmt: skip


REWORDED = (
    "- DECISION: [default] I reworded more than R7 and R9 list:\n"
    '  - "gate" meaning a yes became approval;\n'
    "  - NOTICE lists `agents/arbiter.md`.\n"
    "\n"
    "  Going ahead with all of it.\n"
    "  - OPTION: reword everywhere — one meaning per word; a larger diff\n"
    "  - OPTION: only the listed spots — a smaller diff; leaves the old meaning\n"
    "  - WHY: the intent's outcome\n"
    "Then the next slice.\n"
)
REWORDED_TEXT = (
    'I reworded more than R7 and R9 list: "gate" meaning a yes became approval; NOTICE lists '
    "`agents/arbiter.md`. Going ahead with all of it."
)
REWORDED_SUBS = (
    "  - OPTION: reword everywhere — one meaning per word; a larger diff\n"
    "  - OPTION: only the listed spots — a smaller diff; leaves the old meaning\n"
    "  - WHY: the intent's outcome\n"
)


def test_a_question_in_sub_bullets_keeps_every_line_and_its_options(tmp_path, capsys) -> None:
    """193 (bug 2026-11-19-79): the lines a DECISION's question continues in, indented under it,
    are folded into its ledger line, and the OPTION and WHY run after them is read."""
    root = _change(tmp_path)
    _build_report(root, 1, REWORDED)
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["added"] == ["D1"] and out["bare"] == [], out
    assert _ledger_text(root) == (
        f"# Decisions\n\n- [ ] D1 (builder round 1, default): {REWORDED_TEXT}\n{REWORDED_SUBS}"
    )
    [d1] = factory.read_ledger(root / ".sdlc" / "work" / NAME)
    assert d1["text"] == REWORDED_TEXT and len(d1["options"]) == 2
    assert d1["why"] == "the intent's outcome"


def test_a_ledger_holding_a_question_s_first_line_is_matched(tmp_path, capsys) -> None:
    """193: a ledger written before continuations were read holds the first line alone; the same
    raise read again files nothing new, and fills the bare line's options once."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    first = "- [ ] D1 (builder round 1, default): I reworded more than R7 and R9 list:\n"
    (folder / "decisions.md").write_text("# Decisions\n\n" + first, encoding="utf-8")
    _build_report(root, 1, REWORDED)
    out = _run(capsys, factory.cmd_decisions, root, "008")[1]
    assert out["added"] == [] and out["bare"] == [], out
    assert _ledger_text(root) == "# Decisions\n\n" + first + REWORDED_SUBS
    _run(capsys, factory.cmd_decisions, root, "008")
    assert _ledger_text(root) == "# Decisions\n\n" + first + REWORDED_SUBS, "a rerun: no change"


def test_a_decision_reworded_with_the_same_alternatives_lands_once(tmp_path, capsys) -> None:
    """193 (nit 2026-11-20-1): a resumed agent rewording a decision it raised, with the same
    options and why from the same source, files nothing new."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING)
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["added"] == ["D1"]
    _build_report(root, 1, PAGING.replace("at 50?", "at 50, one screen?"))
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["added"] == []
    assert _ledger_text(root) == "# Decisions\n\n" + PAGING_LEDGER


@pytest.mark.parametrize(
    "rnd, again",
    [
        (2, PAGING.replace("at 50?", "at 50, one screen?")),
        (1, PAGING.replace("at 50?", "at 50 again?").replace("100 —", "25 —")),
        (1, PAGING.replace("[default] Page", "[blocking] Page").replace("at 50?", "at 50 or not?")),
    ],
    ids=["another-source", "other-alternatives", "another-kind"],
)
def test_a_decision_raised_again_otherwise_is_another(tmp_path, capsys, rnd, again) -> None:
    """193 (nit 2026-11-20-1; nit 2026-11-20-10, one case a test): reworded, from another round,
    with other alternatives or as another kind, it is another decision."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING)
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["added"] == ["D1"]
    _build_report(root, rnd, again)
    assert _run(capsys, factory.cmd_decisions, root, "008")[1]["added"] == ["D2"]


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
    state, _ = factory.run_state.loop_state(root, "008", None)
    assert state["next"] == "approve", state
    prompt, target, _ = factory._task(root, root / ".sdlc" / "work" / NAME, state, "approve",
                                      "approver", None)  # fmt: skip
    assert target.name == "decision.md"
    assert "D1, D2" in prompt and "D3" not in prompt, prompt
    assert "- SETTLED: D<n>: " in prompt and "- ESCALATED: D<n>: " in prompt, prompt
    assert "no options yet: D2." in prompt, prompt


# ---------------------------------------------------------------- defaults carried to the landing


LOG_ID = "- DECISION: [default] Log the draft id? Assuming no.\n"


def test_a_confirm_line_leaves_the_default_open(tmp_path, capsys) -> None:
    """202 R2: a CONFIRM line is read apart and never marks the ledger: D2 stays `- [ ]` and
    assumed, never settled; a SETTLED beside it still ticks D1."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING, LOG_ID)
    _run(capsys, factory.cmd_decisions, root, "008")
    _decision(root, "- SETTLED: D1: spec R4 shows 50 a page\n",
              "- CONFIRM: D2: assumed no logging; the person's yes at the landing is enough\n",
              head="DECISION: READY")  # fmt: skip
    folder = root / ".sdlc" / "work" / NAME
    _, _, confirms = factory.approver_weighing(folder)
    assert confirms == {"D2": "assumed no logging; the person's yes at the landing is enough"}, (
        confirms
    )
    code, out = _run(capsys, factory.cmd_decisions, root, "008")
    assert code == 0 and out["settled"] == ["D1"] and out["unsettled"] == [], out
    assert out["assumed"] == ["D2"], out
    assert "- [ ] D2 (builder round 1, default): Log the draft id?" in _ledger_text(root)
    assert "D2" not in [d["id"] for d in factory.read_ledger(folder) if d["settled"]]


def test_a_confirm_and_an_escalated_line_are_named_twice(tmp_path, capsys) -> None:
    """202 R2: an id given two of SETTLED, ESCALATED and CONFIRM is named twice, and marks
    nothing."""
    root = _change(tmp_path)
    _build_report(root, 1, PAGING, LOG_ID)
    _run(capsys, factory.cmd_decisions, root, "008")
    before = _ledger_text(root)
    _decision(root, "- CONFIRM: D1: 50 a page\n", "- SETTLED: D1: spec R4\n",
              "- CONFIRM: D2: no logging\n", "- ESCALATED: D2: the person's call\n")  # fmt: skip
    out = _run(capsys, factory.cmd_decisions, root, "008")[1]
    assert out["settled"] == [] and _ledger_text(root) == before, out
    assert sorted(u["id"] for u in out["unsettled"]) == ["D1", "D2"], out
    assert all("named twice" in u["why"] for u in out["unsettled"]), out


def _carried(tmp_path: Path, capsys, *lines: str, head: str = "DECISION: READY",
             config: str | None = None) -> Path:  # fmt: skip
    """A change one round in, its default D1 open, the approver's decision `head` with `lines`."""
    root = _change(tmp_path, config=config)
    _build_report(root, 1, PAGING)
    _run(capsys, factory.cmd_decisions, root, "008")
    _round(root, 1)
    _decision(root, *lines, "\n- IMPACT: minor — a test change\n", head=head)
    _run(capsys, factory.cmd_decisions, root, "008")
    return root


@pytest.mark.parametrize("case", ["unlined", "escalated", "sensitive", "closes", "settled"])
def test_ready_with_an_uncarried_default_is_mended(tmp_path, capsys, case) -> None:
    """202 R3: a READY resting on an open default it may not carry (no CONFIRM line, an ESCALATED
    one, a CONFIRM on a sensitive path or on a `closes:` change) is a stop the approver mends,
    each id named with why; a CONFIRM on a plain change is done. 235 R1: a default SETTLED but
    still open (`decisions` never ticked it) says so, not "no `- CONFIRM:` line"."""
    line = {"unlined": "", "settled": "", "escalated": "- ESCALATED: D1: the person's call\n"}.get(
        case, "- CONFIRM: D1: 50 a page; the landing's yes is enough\n"
    )
    root = _carried(tmp_path, capsys, line, config=LISTED if case == "sensitive" else None)
    folder = root / ".sdlc" / "work" / NAME
    if case == "sensitive":
        _touch(root, "src/secret/key.py")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "touch")
    if case == "closes":
        _closing(root, "[12]")
        assert factory.intent_closes(folder) == "[12]", "the fixture must take the line"
    if case == "settled":
        # Written after `_carried()` ran `decisions`, so the ledger never ticks D1.
        with (folder / "decision.md").open("a", encoding="utf-8", newline="\n") as f:
            f.write("- SETTLED: D1: spec R4 shows 50 a page\n")
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "mend", ["approver"]), out
    [problem] = [p for p in out["problems"] if p.startswith(factory.UNCARRIED)]
    why = {"unlined": "no `- CONFIRM:`", "escalated": "ESCALATED", "settled": "SETTLED",
           "sensitive": "src/secret/key.py", "closes": "closes: [12]"}[case]  # fmt: skip
    assert "D1" in problem and why in problem, problem
    if case == "settled":
        assert "no `- CONFIRM:` line" not in problem, problem


def _closes_rows(root: Path) -> list[dict]:
    """The records ledger's `closes` rows."""
    ledger = factory._slot_dir(root) / factory.RECORDS_LEDGER
    lines = ledger.read_text(encoding="utf-8").splitlines() if ledger.is_file() else []
    return [row for row in map(json.loads, lines) if "closes" in row]


def _closing(root: Path, value: str | None) -> Path:
    """Change 008's folder, its intent's `closes:` set to `value`, or taken out with None."""
    intent = root / ".sdlc" / "work" / NAME / "intent.md"
    text = re.sub(r"^closes:.*\n", "", intent.read_text(encoding="utf-8"), flags=re.M)
    if value is not None:
        text = text.replace("idea:", f"closes: {value}\nidea:")
    intent.write_text(text, encoding="utf-8")
    return intent.parent


def test_closes_recorded_at_start_outlives_an_edit(tmp_path, capsys) -> None:
    """219: `start` records the intent's `closes:` in the ledger once, and what the change closes
    is the union of that and the working copy: a build that drops it still can't carry a
    default with CONFIRM, nor land without the `issue` signal; one that adds an issue adds it."""
    root = _change(tmp_path)
    folder = _closing(root, "[12]")
    assert _run(capsys, factory.cmd_start, root, "008", "build")[0] == 0
    assert _closes_rows(root) == [{"change": NAME, "closes": "[12]"}]
    assert _run(capsys, factory.cmd_start, root, "008", "build")[0] == 0
    assert len(_closes_rows(root)) == 1, "once, not once a start"
    _closing(root, None)
    assert factory.intent_closes(folder) == "[12]"
    assert "the change closes an issue (closes: [12])" in factory.no_confirm_why(
        [], factory.intent_closes(folder)
    )
    cfg = factory.load_config(root)[0]
    kinds: list[str] = []
    signals, _ = factory.landing.land_signals(folder, root, "READY", cfg, pre={}, kinds=kinds)
    assert "came from a public issue (closes:)" in signals and "issue" in kinds, signals
    _closing(root, "[12, 15]")
    assert factory.intent_closes(folder) == "[12, 15]", "the working copy's text, as today"
    _closing(root, "[15]")
    assert factory.intent_closes(folder) == "[12, 15]", "a build adds an issue, never drops one"


def test_a_change_closing_nothing_records_nothing(tmp_path, capsys) -> None:
    """219: no `closes:`, no ledger line, and nothing closed, as before."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    assert _run(capsys, factory.cmd_start, root, "008", "build")[0] == 0
    assert _closes_rows(root) == [] and factory.intent_closes(folder) is None
    cfg = factory.load_config(root)[0]
    signals, _ = factory.landing.land_signals(folder, root, "READY", cfg, pre={})
    assert "came from a public issue (closes:)" not in signals, signals


def test_an_agent_run_records_closes_without_start(tmp_path, capsys, claude) -> None:
    """219: autopilot never runs `start`, so an agent's run records `closes:` before it runs."""
    root = _change(tmp_path)
    folder = _closing(root, "[12]")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "build", None, None)
    assert code == 0, out
    assert _closes_rows(root) == [{"change": NAME, "closes": "[12]"}]
    _closing(root, None)
    assert factory.intent_closes(folder) == "[12]"


def test_a_confirmed_default_on_a_plain_change_is_done(tmp_path, capsys) -> None:
    """202 R3: a CONFIRM the change may give leaves the run done, READY."""
    root = _carried(tmp_path, capsys, "- CONFIRM: D1: 50 a page; the landing's yes is enough\n")
    out = _verdicts(root, capsys)
    assert (out["next"], out["decision"], out["assumed"]) == ("done", "READY", ["D1"]), out


def test_a_second_uncarried_ready_is_a_rerun(tmp_path, capsys, claude, monkeypatch) -> None:
    """202 R3: the approver is asked again once a round, by the `confirm` part naming each id; a
    second READY still resting on it is a rerun stop."""
    root = _carried(tmp_path, capsys, "")
    folder = root / ".sdlc" / "work" / NAME
    (folder / "runs").mkdir()
    (folder / "runs" / "approver.sessions").write_text("s-a\n", encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", "DECISION: READY\n\nStill fine.")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "mend", "approver", None)
    assert code == 0, out
    told = claude()[-1]["argv"][1]
    assert "may not carry to the landing: D1: no `- CONFIRM:` line" in told, told
    out = _verdicts(root, capsys)
    assert (out["next"], out["way"], out["mend"]) == ("stop", "rerun", []), out


def test_confirm_on_an_escalate_still_needs_deciding(tmp_path, capsys) -> None:
    """202 R5: on an ESCALATE a CONFIRMed default is an open default to decide, as before: the
    run is done, `ask` lists it, and core's needs still confirm it at /sdlc-factory:decide."""
    root = _carried(tmp_path, capsys, "- CONFIRM: D1: 50 a page\n",
                    head="DECISION: ESCALATE")  # fmt: skip
    out = _verdicts(root, capsys)
    assert (out["next"], out["problems"], out["assumed"]) == ("done", [], ["D1"]), out
    folder = root / ".sdlc" / "work" / NAME
    found = sdlc.factory_records.reading(folder)
    rec = {"id": "008", "stage": "test", "problems": []}
    rec |= {k: found[k] for k in ("decision", "assumed", "ledger_lines")}
    rec["needs"] = sdlc.needs_of(rec)
    assert rec["needs"] == ["confirm 1 default"], rec
    assert sdlc.decide_step(rec) == "/sdlc-factory:decide 008"


@pytest.mark.parametrize("answer", ["kept", "changed"])
def test_decide_answers_a_ready_changes_carried_defaults(tmp_path, capsys, answer) -> None:
    """202 R10: `ask` lists a READY change's carried default with the approver's CONFIRM reason
    (`confirm`), never as escalated; the kept default answered means ship, any other rebuild,
    then `/sdlc:ship`."""
    root = _carried(tmp_path, capsys, "- CONFIRM: D1: 50 a page; the landing's yes is enough\n")
    intent = root / ".sdlc" / "work" / NAME / "intent.md"
    intent.write_text(intent.read_text().replace("stage: design", "stage: test"))
    code, out = _run(capsys, factory.cmd_ask, root, "008", None)
    assert code == 0 and out["decision"] == "READY", out
    [item] = out["items"]
    assert (item["id"], item["escalated"]) == ("D1", None), item
    assert item["confirm"] == "50 a page; the landing's yes is enough", item
    words = factory.KEPT_ANSWER if answer == "kept" else "100 a page"
    path = root / ".sdlc" / "work" / NAME / "decisions.md"
    path.write_text(path.read_text().replace("- [ ] D1", "- [x] D1").replace(
        "at 50?", f"at 50? → decided: {words}"))  # fmt: skip
    code, out = _run(capsys, factory.cmd_ask, root, "008", "D1")
    assert code == 0, out
    if answer == "kept":
        assert out["next"] == "ship", out
    else:
        assert (out["next"], out["then"]) == ("rebuild", "/sdlc:ship 008"), out


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
         "escalated": "the page size is the product's call", "confirm": None},
        {"id": "D3", "kind": "blocking", "source": "security round 1",
         "reply": "reviews/round-1/security.md", "question": "Keep drafts 30 days?",
         "options": [], "why": None, "escalated": None, "confirm": None},
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


def _reviewer_default(tmp_path: Path, capsys) -> Path:
    """216's case: the builder's default D1 and the security reviewer's default D2, both open."""
    root = _change(tmp_path, stage="test")
    _build_report(root, 1, PAGING)
    _review(root, 1, "security", "VERDICT: PASS")
    review = root / ".sdlc" / "work" / NAME / "reviews" / "round-1" / "security.md"
    review.write_text(
        review.read_text() + "- DECISION: [default] Guard the sensitive paths? Assuming yes.\n"
    )
    _run(capsys, factory.cmd_decisions, root, "008")
    _decision(root, "- ESCALATED: D2: a guard is the person's call\n")
    return root


def test_ask_says_rebuild_for_a_reviewer_s_default_never_built(tmp_path, capsys) -> None:
    """218: a reviewer's default confirmed, with no later builder report saying it built it, is a
    call the build never made: `rebuild`, naming it, by `build` for an ESCALATE and by ship for a
    READY. The builder's own default confirmed still means ship."""
    root = _reviewer_default(tmp_path, capsys)
    _answer(root, "D1", factory.KEPT_ANSWER)
    _answer(root, "D2", factory.KEPT_ANSWER)
    out = _run(capsys, factory.cmd_ask, root, "008", "D1")[1]
    assert out["next"] == "ship" and out["unbuilt"] == [], out
    code, out = _run(capsys, factory.cmd_ask, root, "008", "D1,D2")
    assert code == 0 and out["next"] == "rebuild", out
    assert out["then"] == "/sdlc-factory:build 008", out
    assert out["unbuilt"] == [
        {"id": "D2", "source": "security round 1", "question": "Guard the sensitive paths? "
         "Assuming yes."}
    ], out  # fmt: skip
    path = root / ".sdlc" / "work" / NAME / "decision.md"
    path.write_text(path.read_text().replace("DECISION: ESCALATE", "DECISION: READY"))
    out = _run(capsys, factory.cmd_ask, root, "008", "D1,D2")[1]
    assert (out["next"], out["then"]) == ("rebuild", "/sdlc:ship 008"), out


@pytest.mark.parametrize(
    ("rnd", "line", "then"),
    [
        (2, "- BUILT: D2: the sensitive paths are guarded\n", "ship"),
        (1, "- BUILT: D2: the sensitive paths are guarded\n", "rebuild"),
        (2, "- BUILT: D1: paged at 50\n", "rebuild"),
        (2, "```\n- BUILT: D2: quoted\n```\n", "rebuild"),
        (2, "~~~~\n- BUILT: D2: quoted\n~~~\n~~~~\n", "rebuild"),
        (2, "```text\n- BUILT: D2: quoted, the fence never closed\n", "rebuild"),
        (2, "```\nquoted\n```\n- BUILT: D2: the sensitive paths are guarded\n", "ship"),
    ],
    ids=[
        "later-round",
        "same-round",
        "another-id",
        "fenced",
        "tilde-fenced",
        "unclosed-fence",
        "after-a-fence",
    ],  # fmt: skip
)
def test_ask_says_ship_once_a_later_builder_report_built_it(tmp_path, capsys, rnd, line, then):
    """218: a `- BUILT: D<n>` line in a builder report of a round after the one that raised it
    is the build making the call; the raising round's own report, or a line naming another id,
    isn't. 228 R8: nor is one quoted inside a code fence, a fence that never closes running to
    the report's end; the line after a closed fence is read."""
    root = _reviewer_default(tmp_path, capsys)
    _answer(root, "D1", factory.KEPT_ANSWER)
    _answer(root, "D2", factory.KEPT_ANSWER)
    _build_report(root, rnd, PAGING, line)
    out = _run(capsys, factory.cmd_ask, root, "008", "D1,D2")[1]
    assert out["next"] == then, out


# ---------------------------------------------------------------- an escalated change sent back


def _tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


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


# ---------------------------------------------------------------- a run upgraded to Tier 2 (112)


def _upgrade(root, capsys) -> tuple[int, dict]:
    return _run(capsys, factory.cmd_upgrade, root, "008")


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
    """R12: `sdlc.py`'s `vet` reads the record by its own copy of the factory's pattern."""
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
        "escalated": None, "confirm": None,
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
