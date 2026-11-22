"""A change's `findings.md`: what ship's review found, each finding answered, counted into the
`Sdlc-Findings` trailer by the script, and a change that can't ship while one is still open."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_findings", "sdlc.py")
metrics = _load("metrics_findings", "metrics.py")

FINDINGS = """\
# Findings

> The note.

## F1. [important] [correctness] A second save keeps two drafts

The list holds both after a save.

Evidence: drafts/store.py:42
Class: a write that never checks for an existing row; the import path does the same
Disposition: fixed

## F2. [nit] [cost] A helper with one caller

Evidence: drafts/list.py:10
Class: a layer with one caller
Disposition: recorded

## F3. [pre-existing] [correctness] An empty title crashes the old exporter

Evidence: drafts/export.py:7
Class: bad input that crashes
Disposition: recorded

## F4. [nit] [cost] A loop that could be a comprehension

Evidence: drafts/list.py:20
Class: style
Disposition: wrong
Reason: the loop breaks early, which a comprehension can't
"""

INTENT = """\
---
id: 001
slug: reopen-drafts
tier: 1
impact: patch
stage: build
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
---

# 001 — Reopen drafts
"""


def _write(folder: Path, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "findings.md").write_text(text, encoding="utf-8")
    return folder


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


@pytest.fixture
def change(tmp_path: Path) -> tuple[Path, Path]:
    """A repo on a change's branch, its folder holding an intent and nothing else yet."""
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", "001-reopen-drafts")
    folder = root / ".sdlc" / "work" / "001-reopen-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "work")
    return root, folder


def test_entries_are_read_in_order_with_their_lines(tmp_path: Path) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS))
    assert found["problems"] == [] and found["open"] == []
    assert [e["id"] for e in found["entries"]] == ["F1", "F2", "F3", "F4"]
    first, _, third, fourth = found["entries"]
    assert first["evidence"] == "drafts/store.py:42" and first["disposition"] == "fixed"
    assert third["rank"] == "preexisting"
    assert fourth["reason"].startswith("the loop breaks early")


def test_no_file_is_no_findings_and_no_problem(tmp_path: Path) -> None:
    found = sdlc.findings_entries(tmp_path)
    assert found == {"path": "findings.md", "exists": False, "entries": [], "open": [],
                     "fix": [], "fresh": None, "cases": None,
                     "passes": dict.fromkeys(("security", "behaviour", "ui", "ux", "docs")),
                     "evidence": [], "problems": []}  # fmt: skip


def test_the_template_is_never_read_as_a_finding() -> None:
    """Its section names every rank, pass and disposition, and a copy left as it is reads as a
    problem, never as a finding and never raising."""
    template = (ROOT / "templates" / "findings.md").read_text(encoding="utf-8")
    assert "## F1. [<important|nit|pre-existing>] [<correctness|contract|cost|context>]" in template
    assert f"Disposition: <{'|'.join(sdlc.DISPOSITIONS)}>" in template
    for key in ("Evidence:", "Class:", "Reason:", "Fix:"):
        assert key in template
    found = sdlc.findings_entries(ROOT / "templates")
    assert found["entries"] == [] and found["problems"]


@pytest.mark.parametrize(
    "section, problem",
    [
        ("## A finding\n", "isn't `## F<n>. [rank] [pass] title`"),
        (
            "## F9. [major] [correctness] t\n\nEvidence: a:1\nClass: c\nDisposition: fixed\n",
            "rank must be one of",
        ),
        (
            "## F9. [nit] [style] t\n\nEvidence: a:1\nClass: c\nDisposition: fixed\n",
            "pass must be one of",
        ),
        ("## F9. [nit] [cost] t\n\nClass: c\nDisposition: fixed\n", "no `Evidence:` line"),
        ("## F9. [nit] [cost] t\n\nEvidence: a:1\nDisposition: fixed\n", "no `Class:` line"),
        (
            "## F9. [nit] [cost] t\n\nEvidence: a:1\nClass: c\nDisposition: done\n",
            "Disposition must be one of",
        ),
        (
            "## F9. [nit] [cost] t\n\nEvidence: a:1\nClass: c\nDisposition: wrong\n",
            "`wrong` with no `Reason:` line",
        ),
        (
            "## F1. [nit] [cost] t\n\nEvidence: a:1\nClass: c\nDisposition: fixed\n",
            "its id is used twice",
        ),
    ],
    ids=["heading", "rank", "pass", "evidence", "class", "disposition", "reason", "twice"],
)
def test_a_malformed_section_is_a_problem_and_left_out(tmp_path, section, problem) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS + "\n" + section))
    assert any(problem in p for p in found["problems"]), found["problems"]
    assert len(found["entries"]) == 4


def test_an_open_finding_is_listed_not_a_problem(tmp_path: Path) -> None:
    text = FINDINGS.replace("Disposition: fixed", "Disposition: open")
    found = sdlc.findings_entries(_write(tmp_path / "c", text))
    assert found["open"] == ["F1"] and found["problems"] == []


def test_the_trailer_counts_ranks_passes_and_dispositions(tmp_path: Path) -> None:
    entries = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS))["entries"]
    assert sdlc.findings_trailer(entries) == (
        "Sdlc-Findings: important=1 nit=2 preexisting=1 correctness=2 contract=0 cost=2 "
        "context=0 fixed=correctness:1 recorded=correctness:1,cost:1 wrong=cost:1 "
        "intentional=0 minor=0 fresh=0 fresh_wrong=0 agents=0 passes=0 passes_wrong=0"
    )
    assert sdlc.findings_trailer([]).endswith(
        "fixed=0 recorded=0 wrong=0 intentional=0 minor=0 fresh=0 fresh_wrong=0 agents=0 "
        "passes=0 passes_wrong=0"
    )


FRESH = """\

## F5. [important] [correctness] A guard that only one caller has

Evidence: drafts/store.py:50
Class: a check at one call site of several
Disposition: fixed
By: fresh

## F6. [nit] [cost] A name that could be shorter

Evidence: drafts/list.py:3
Class: style
Disposition: wrong
Reason: ship's passes couldn't confirm it: the name matches its neighbours
By: fresh
"""


def test_the_fresh_reviewer_s_findings_are_marked_and_counted(tmp_path: Path) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS + FRESH))
    assert found["problems"] == []
    assert [e["by"] for e in found["entries"]] == [None, None, None, None, "fresh", "fresh"]
    trailer = sdlc.findings_trailer(found["entries"])
    assert trailer.endswith("fresh=2 fresh_wrong=1 agents=0 passes=0 passes_wrong=0")
    parsed = metrics.parse_trailers("Ship it\n\n" + trailer)["findings"]
    assert (parsed["fresh"], parsed["fresh_wrong"]) == (2, 1)


def test_a_by_line_naming_anyone_else_is_a_problem(tmp_path: Path) -> None:
    text = FINDINGS + FRESH.replace("By: fresh", "By: someone", 1)
    found = sdlc.findings_entries(_write(tmp_path / "c", text))
    by = "By must be one of fresh|ship-security|ship-behaviour|ship-ui|ship-ux|ship-docs|code|"
    assert any(by in p and "got 'someone'" in p for p in found["problems"])


def test_an_old_and_a_new_trailer_both_parse_unchanged(tmp_path: Path) -> None:
    """The trailer is a contract: its old keys keep their meaning, and the parser needs nothing
    new to read the new ones."""
    old = metrics.parse_trailers("Ship it\n\nSdlc-Findings: important=1 nit=3 cost=2")
    assert old["findings"] == {"important": 1, "nit": 3, "cost": 2}
    entries = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS))["entries"]
    new = metrics.parse_trailers("Ship it\n\n" + sdlc.findings_trailer(entries))["findings"]
    assert (new["important"], new["nit"], new["preexisting"]) == (1, 2, 1)
    assert new["fixed"] == {"correctness": 1}
    assert new["recorded"] == {"correctness": 1, "cost": 1}
    assert new["minor"] == 0


def test_the_command_prints_the_trailer_and_exits_1_while_one_is_open(change, capsys) -> None:
    root, folder = change
    _write(folder, FINDINGS)
    assert sdlc.cmd_findings(root, "001") == 0
    out = json.loads(capsys.readouterr().out)
    assert out["counts"] == {"important": 1, "nit": 2, "preexisting": 1}
    assert out["trailer"].startswith("Sdlc-Findings: important=1 nit=2 preexisting=1")
    _write(folder, FINDINGS.replace("Disposition: fixed", "Disposition: open"))
    assert sdlc.cmd_findings(root, "001") == 1
    assert json.loads(capsys.readouterr().out)["open"] == ["F1"]


def test_preflight_carries_the_findings_part(change, capsys) -> None:
    root, folder = change
    _write(folder, FINDINGS)
    sdlc.cmd_preflight(root, "001")
    out = json.loads(capsys.readouterr().out)
    assert [e["id"] for e in out["findings"]["entries"]] == ["F1", "F2", "F3", "F4"]


def test_check_reports_a_malformed_file_but_not_an_open_finding(change) -> None:
    root, folder = change
    _write(folder, FINDINGS.replace("Disposition: fixed", "Disposition: open"))
    assert not [p for p in sdlc.analyze(root)["problems"] if p["kind"] == "findings"]
    _write(folder, FINDINGS + "\n## Not a finding\n")
    assert [p for p in sdlc.analyze(root)["problems"] if p["kind"] == "findings"]


def _flat(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").split())


def test_the_review_guide_asks_for_evidence_a_class_a_count_and_the_cause() -> None:
    guide = _flat("guide/review.md")
    rules = guide.split("## Reporting rules", 1)[1]
    assert "**Important**, **Nit** or **Pre-existing**" in rules
    assert "never blocks it" in rules and "A new call into old broken code is the diff's" in rules
    assert "cites the `path:line`" in rules and "never inferred from a name" in rules
    assert "**Name the class.**" in rules and "every instance" in rules
    assert "**Count first.**" in rules and '"nothing to fix"' in rules
    assert "### Paths this repo's review skips" in rules
    correctness = guide.split("## Pass 1", 1)[1].split("## Pass 2", 1)[0]
    assert "`fixes:`" in correctness and "**A symptom fixed in place of its cause.**" in correctness


def test_ship_writes_its_findings_every_run_and_counts_them_by_script() -> None:
    ship = _flat("skills/ship/SKILL.md")
    step3 = ship.split("## Step 3", 1)[1].split("## Step 4", 1)[0]
    assert "`.sdlc/work/NNN-slug/findings.md`" in step3 and "named exception" in step3
    assert "a run that stops included" in step3
    assert "keep every id" in step3 and "`fixed`" in step3 and "never raise again" in step3
    step4 = ship.split("## Step 4", 1)[1].split("## Step 5", 1)[0]
    assert "sdlc.py findings <NNN>" in step4 and "Never count it by hand" in step4
    assert "Pre-existing findings" in step4 and "[bug]" in step4


def test_retro_reads_the_review_s_noise_beside_answered() -> None:
    retro = _flat("skills/retro/SKILL.md")
    assert "`dispositions`" in retro and "`answered`" in retro
    assert "the review's noise" in retro and "`wrong`" in retro


def test_ship_refuses_an_open_finding_and_ships_with_no_file(change, capsys) -> None:
    root, folder = change
    _write(folder, FINDINGS.replace("Disposition: fixed", "Disposition: open"))
    assert sdlc.cmd_ship(root, "001") == 1
    assert "F1" in capsys.readouterr().err
    assert "stage: build" in (folder / "intent.md").read_text(encoding="utf-8")
    (folder / "findings.md").unlink()
    assert sdlc.cmd_ship(root, "001") == 0
    assert "stage: shipped" in (folder / "intent.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------- a fix ship recommends


FIX = FINDINGS.replace(
    "Class: a layer with one caller\nDisposition: recorded",
    "Class: a layer with one caller\nDisposition: fix\nFix: inline `_one_caller` into `render`",
)


def test_a_finding_proposed_for_fixing_carries_its_fix(tmp_path: Path) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FIX))
    assert found["problems"] == [] and found["fix"] == ["F2"] and found["open"] == []
    assert found["entries"][1]["fix"] == "inline `_one_caller` into `render`"


@pytest.mark.parametrize(
    "text, problem",
    [
        (FIX.replace("Fix: inline `_one_caller` into `render`\n", ""), "`fix` with no `Fix:`"),
        (
            FINDINGS.replace(
                "Class: bad input that crashes\nDisposition: recorded",
                "Class: bad input that crashes\nDisposition: fix\nFix: guard the empty title",
            ),
            "a pre-existing finding is filed as a bug, never `fix`",
        ),
    ],
    ids=["no-fix-line", "pre-existing"],
)
def test_a_fix_needs_its_change_and_never_a_pre_existing_finding(tmp_path, text, problem) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", text))
    assert any(problem in p for p in found["problems"])


def test_the_trailer_never_counts_a_fix(tmp_path: Path) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FIX))
    assert " fix=" not in sdlc.findings_trailer(found["entries"])


@pytest.mark.parametrize(
    "note, fresh",
    [
        ("> The note.\n> Fresh review: ran\n", {"ran": True}),
        (
            "> The note.\n> Fresh review: skipped, no Agent tool here\n",
            {"ran": False, "why": "no Agent tool here"},
        ),
        ("> The note.\n", None),
    ],
    ids=["ran", "skipped", "unsaid"],
)
def test_the_note_says_whether_the_fresh_review_ran(tmp_path, note, fresh) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS.replace("> The note.\n", note)))
    assert found["fresh"] == fresh and found["problems"] == []


@pytest.mark.parametrize(
    "note, cases",
    [
        ("> The note.\n> Skill evals: ran, 2 of 2\n", {"ran": True, "said": "2 of 2"}),
        (
            "> The note.\n> Skill evals: skipped, plugin eval is unavailable\n",
            {"ran": False, "why": "plugin eval is unavailable"},
        ),
        ("> The note.\n> Fresh review: ran\n", None),
    ],
    ids=["ran", "skipped", "unsaid"],
)
def test_the_note_says_whether_the_skill_evals_ran(tmp_path, note, cases) -> None:
    found = sdlc.findings_entries(_write(tmp_path / "c", FINDINGS.replace("> The note.\n", note)))
    assert found["cases"] == cases and found["problems"] == []


def test_ship_refuses_a_diff_with_cases_whose_note_says_nothing_of_them(
    change, capsys, monkeypatch
) -> None:
    """R10: in this plugin's repo, a diff that reaches a skill with cases never lands with them
    silently unrun; anywhere else `_cases_report` is `available: false` and this never fires."""
    root, folder = change
    monkeypatch.setattr(sdlc, "_cases_report", lambda r, p: {"available": True, "scope": ["ship"]})
    _write(folder, FINDINGS)
    assert sdlc.cmd_ship(root, "001") == 1
    assert "Skill evals" in capsys.readouterr().err
    skipped = "> The note.\n> Skill evals: skipped, no claude on PATH\n"
    _write(folder, FINDINGS.replace("> The note.\n", skipped))
    assert sdlc.cmd_ship(root, "001") == 0


def test_the_question_names_skill_evals_that_didnt_run() -> None:
    def asked(cases: dict | None) -> str:
        question, _ = sdlc.ship_question(".sdlc/work/001-x", [], "none", False, False, [], [],
                                         ".sdlc/work/inbox.md", cases=cases)  # fmt: skip
        return question

    assert "without the skill evals (no claude on PATH)" in asked(
        {"ran": False, "why": "no claude on PATH"}
    )
    assert "skill evals" not in asked({"ran": True}) and "skill evals" not in asked(None)


def test_ship_refuses_a_fix_still_proposed(change, capsys) -> None:
    root, folder = change
    _write(folder, FIX)
    assert sdlc.cmd_ship(root, "001") == 1
    assert "F2" in capsys.readouterr().err
    assert "stage: build" in (folder / "intent.md").read_text(encoding="utf-8")


NEW_F5 = (
    "\n## F5. [nit] [cost] A new one\n\nEvidence: a.py:1\nClass: c\nDisposition: minor\nReason: r\n"
)


@pytest.mark.parametrize(
    "text, fixed, through, said",
    [
        (FIX.replace("Disposition: fix\n", "Disposition: recorded\n"), ["F2"], "F4", "F2"),
        (FINDINGS + NEW_F5, [], "F4", "F5"),
        (FINDINGS, [], "five", "not a finding id"),
    ],
    ids=["left-unfixed", "raised-after", "bad-through"],
)
def test_ship_after_a_fix_refuses_unless_the_rerun_is_clean(
    change, capsys, text, fixed, through, said
) -> None:
    root, folder = change
    _write(folder, text)
    assert sdlc.cmd_ship(root, "001", (), fixed, through) == 1
    assert said in capsys.readouterr().err
    assert "stage: build" in (folder / "intent.md").read_text(encoding="utf-8")


def test_ship_after_a_clean_rerun_stamps(change) -> None:
    root, folder = change
    _write(folder, FINDINGS)
    assert sdlc.cmd_ship(root, "001", (), ["F1"], "F4") == 0
    assert "stage: shipped" in (folder / "intent.md").read_text(encoding="utf-8")


def test_ship_refuses_a_deep_diff_whose_note_says_nothing_of_the_fresh_review(change, capsys):
    root, folder = change
    (root / ".sdlc" / "config.toml").write_text(
        '[review]\nsensitive = ["drafts/"]\n', encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "config")
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "-q", "--ff-only", "001-reopen-drafts")
    _git(root, "checkout", "-q", "001-reopen-drafts")
    (root / "drafts").mkdir()
    (root / "drafts" / "store.py").write_text("x = 1\n", encoding="utf-8")
    _write(folder, FINDINGS)
    assert sdlc.cmd_ship(root, "001") == 1
    assert "Fresh review" in capsys.readouterr().err
    _write(folder, FINDINGS.replace("> The note.\n", "> The note.\n> Fresh review: ran\n"))
    assert sdlc.cmd_ship(root, "001") == 1, "a deep diff gets the security review too (143)"
    assert "Security review" in capsys.readouterr().err
    note = "> The note.\n> Fresh review: ran\n> Security review: ran\n> Docs review: ran\n"
    _write(folder, FINDINGS.replace("> The note.\n", note))
    assert sdlc.cmd_ship(root, "001") == 0


AGENTS = """\

## F7. [important] [context] The docs say the old command

Evidence: docs/REFERENCE.md:12
Class: code review, round 1
Disposition: fixed
By: code

## F8. [nit] [cost] A name that could be shorter

Evidence: drafts/list.py:3
Class: security review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: security

## F9. [pre-existing] [correctness] An old crash

Evidence: drafts/old.py:9
Class: test review, round 2
Disposition: recorded
By: test

## F10. [important] [correctness] A guard no caller needs

Evidence: drafts/store.py:1
Class: code review, round 1
Disposition: wrong
Reason: the verifier found the guard is reached
By: code
"""


SHIP_SECURITY = """\

## F11. [important] [contract] A path from the request reaches the shell

Evidence: drafts/export.py:14
Class: untrusted input into a command line
Disposition: wrong
Reason: the title is checked against a fixed list at drafts/export.py:9
By: ship-security
"""


def test_finding_by_names_every_factory_reviewer() -> None:
    """Core's copy of the factory's reviewers, so a factory role's `By:` is never a problem."""
    path = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
    spec = importlib.util.spec_from_file_location("factory_findings_by", path)
    factory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory)
    assert sdlc.AGENT_ROLES == factory.REVIEWERS
    assert sdlc.SHIP_PASSES == (
        "ship-security",
        "ship-behaviour",
        "ship-ui",
        "ship-ux",
        "ship-docs",
    )
    assert ("fresh", *sdlc.SHIP_PASSES, *factory.REVIEWERS) == sdlc.FINDING_BY
    assert not set(sdlc.SHIP_PASSES) & set(factory.REVIEWERS), "never a factory role's name"
    assert factory.PASSES == sdlc.FINDING_PASSES, "the factory's copy of the passes"


def test_the_trailer_never_counts_an_agent_finding(tmp_path: Path, change, capsys) -> None:
    """Every key the trailer has counts ship's own findings (no `By:`, or `fresh`) alone, and
    `agents=` says how many the agents raised: their findings move nothing else."""
    own = sdlc.findings_entries(_write(tmp_path / "a", FINDINGS + FRESH))
    both = sdlc.findings_entries(_write(tmp_path / "b", FINDINGS + FRESH + AGENTS))
    assert both["problems"] == []
    assert [e["by"] for e in both["entries"]][-4:] == ["code", "security", "test", "code"]
    mine = sdlc.findings_trailer(own["entries"])
    tail = " agents=0 passes=0 passes_wrong=0"
    assert mine.endswith(tail)
    assert sdlc.findings_trailer(both["entries"]) == (
        mine.removesuffix(tail) + " agents=4 passes=0 passes_wrong=0"
    )
    # 143 R9: a ship pass's finding is ship's own: in the rank, pass and disposition keys and
    # `passes=`, never in `agents=`.
    passes = sdlc.findings_entries(
        _write(tmp_path / "p", FINDINGS + FRESH + SHIP_SECURITY + AGENTS)
    )
    assert passes["problems"] == []
    words = dict(w.split("=", 1) for w in sdlc.findings_trailer(passes["entries"]).split()[1:])
    before = dict(w.split("=", 1) for w in mine.split()[1:])
    assert int(words["important"]) == int(before["important"]) + 1
    assert int(words["contract"]) == int(before["contract"]) + 1
    assert words["wrong"] == "contract:1," + before["wrong"]
    assert (words["agents"], words["passes"], words["passes_wrong"]) == ("4", "security:1", "1")
    assert words["fresh"] == before["fresh"], "never counted as the fresh reviewer's"
    root, folder = change
    _write(folder, FINDINGS + AGENTS)
    assert sdlc.cmd_findings(root, "001") == 0
    out = json.loads(capsys.readouterr().out)
    assert out["counts"] == {"important": 1, "nit": 2, "preexisting": 1}
    assert out["agents"] == 4


OLD_TRAILER = (
    "Sdlc-Findings: important=1 nit=2 preexisting=1 correctness=2 contract=0 cost=2 context=0 "
    "fixed=correctness:1 recorded=correctness:1,cost:1 wrong=cost:1 intentional=0 minor=0 "
    "fresh=0 fresh_wrong=0 agents=0"
)


def test_an_old_findings_file_keeps_its_trailer(tmp_path: Path) -> None:
    """143 R10: with no `ship-*` finding, everything up to `agents=` is what it always was; the
    new keys only follow it."""
    for text in (FINDINGS, FINDINGS + AGENTS):
        trailer = sdlc.findings_trailer(
            sdlc.findings_entries(_write(tmp_path / "c", text))["entries"]
        )
        head, _, rest = trailer.partition(" agents=")
        assert head == OLD_TRAILER.partition(" agents=")[0]
        assert rest.split(" ", 1)[1] == "passes=0 passes_wrong=0"


@pytest.mark.parametrize(
    "line, key",
    [("Security review", "security"), ("Behaviour check", "behaviour"), ("UI review", "ui"),
     ("UX review", "ux")],
)  # fmt: skip
def test_the_note_says_whether_each_pass_ran(tmp_path, line, key) -> None:
    """143 R11: each pass's note line, read as the fresh review's is."""

    def said(note: str) -> dict:
        text = FINDINGS.replace("> The note.\n", f"> The note.\n{note}")
        found = sdlc.findings_entries(_write(tmp_path / "c", text))
        assert found["problems"] == [] or key == "behaviour", found["problems"]
        return found["passes"]

    assert said("")[key] is None
    assert said(f"> {line}: skipped, no current screenshots\n")[key] == {
        "ran": False,
        "why": "no current screenshots",
    }
    if key != "behaviour":
        assert said(f"> {line}: ran\n")[key] == {"ran": True}
    others = [k for k in sdlc.PASS_LINES if k != key]
    assert all(said(f"> {line}: ran\n")[k] is None for k in others)


EVIDENCE = """\

## Evidence

$ python -c "import drafts; drafts.save('a', 'b'); print(drafts.reopen('a'))"
b
exit: 0

$ python -m pytest -q
```
2 passed in 0.01s
```
exit: 0
"""


def test_behaviour_evidence_is_read_not_counted(tmp_path: Path) -> None:
    """143 R13: `## Evidence` is evidence, never a malformed finding, and a command must carry
    its exit; `Behaviour check: ran` needs at least one."""
    ran = FINDINGS.replace("> The note.\n", "> The note.\n> Behaviour check: ran\n")
    found = sdlc.findings_entries(_write(tmp_path / "c", ran + EVIDENCE))
    assert found["problems"] == [], found["problems"]
    assert [e["id"] for e in found["entries"]] == ["F1", "F2", "F3", "F4"]
    assert found["evidence"] == [
        {"command": "python -c \"import drafts; drafts.save('a', 'b'); print(drafts.reopen('a'))\"",
         "exit": 0},
        {"command": "python -m pytest -q", "exit": 0},
    ]  # fmt: skip
    trailer = sdlc.findings_trailer(found["entries"])
    assert trailer == sdlc.findings_trailer(
        sdlc.findings_entries(_write(tmp_path / "d", FINDINGS))["entries"]
    )
    no_exit = EVIDENCE.replace("b\nexit: 0\n", "b\n", 1)
    found = sdlc.findings_entries(_write(tmp_path / "c", ran + no_exit))
    assert any("no `exit:`" in p for p in found["problems"]), found["problems"]
    found = sdlc.findings_entries(_write(tmp_path / "c", ran))
    assert any("Behaviour check: ran" in p for p in found["problems"]), found["problems"]
    # A finding written after the evidence still parses as one.
    after = ran + EVIDENCE + NEW_F5
    found = sdlc.findings_entries(_write(tmp_path / "c", after))
    assert found["problems"] == [] and found["entries"][-1]["id"] == "F5"


# ---------------------------------------------------------------- ship's passes at ship (143)


def _applying(monkeypatch, *names: str) -> None:
    """`_passes_report` saying `names` apply, as preflight finds them."""
    report = {n: {"applies": n in names, "why": None} for n in sdlc.PASS_NAMES}
    report["ui"]["shots"] = []
    monkeypatch.setattr(sdlc, "_passes_report", lambda root, path, risk: report)


def _ships_only_with(change, capsys, monkeypatch, applies: str, note: str, unsaid: str) -> None:
    """With `applies`, ship refuses a note missing `unsaid`, naming it, and stamps with `note`."""
    root, folder = change
    _applying(monkeypatch, applies)
    _write(folder, FINDINGS)
    assert sdlc.cmd_ship(root, "001") == 1
    assert f"`{unsaid}: ran`" in capsys.readouterr().err
    assert "stage: build" in (folder / "intent.md").read_text(encoding="utf-8")
    _write(folder, FINDINGS.replace("> The note.\n", f"> The note.\n{note}"))
    assert sdlc.cmd_ship(root, "001") == 0, capsys.readouterr().err


def test_ship_refuses_a_security_pass_unsaid(change, capsys, monkeypatch) -> None:
    _ships_only_with(change, capsys, monkeypatch, "security", "> Security review: ran\n",
                     "Security review")  # fmt: skip


def test_ship_refuses_a_behaviour_check_unsaid(change, capsys, monkeypatch) -> None:
    note = "> Behaviour check: skipped, the spec names no path to run\n"
    _ships_only_with(change, capsys, monkeypatch, "behaviour", note, "Behaviour check")


def test_ship_refuses_a_docs_review_unsaid(change, capsys, monkeypatch) -> None:
    """227 R9."""
    _ships_only_with(change, capsys, monkeypatch, "docs", "> Docs review: ran\n", "Docs review")


def test_a_change_with_no_findings_file_ships_without_a_docs_line(change, monkeypatch) -> None:
    """227: the docs pass applies to nearly every diff, so its line is asked of a findings.md
    ship wrote, never of a change with none, which predates the file."""
    root, folder = change
    _applying(monkeypatch, "docs")
    (folder / "findings.md").unlink(missing_ok=True)
    assert sdlc.cmd_ship(root, "001") == 0


def test_the_question_says_a_skipped_docs_review() -> None:
    """227 R9."""
    skipped = _asked({"docs": {"ran": False, "why": "no doc it could make false"}})
    assert "without the docs review (no doc it could make false)" in skipped
    assert _asked({"docs": {"ran": True}}).startswith("Commit this, after the docs review, and ")


def test_ship_refuses_a_ui_review_unsaid(change, capsys, monkeypatch) -> None:
    note = "> UI review: ran\n> UX review: ran\n"
    _ships_only_with(change, capsys, monkeypatch, "ui", note, "UI review")


def test_ship_refuses_a_ux_review_unsaid(change, capsys, monkeypatch) -> None:
    root, folder = change
    _applying(monkeypatch, "ui")
    _write(folder, FINDINGS.replace("> The note.\n", "> The note.\n> UI review: ran\n"))
    assert sdlc.cmd_ship(root, "001") == 1
    err = capsys.readouterr().err
    assert "`UX review: ran`" in err and "`UI review: ran`" not in err


def test_a_pass_that_doesn_t_apply_needs_no_line(change, monkeypatch) -> None:
    root, folder = change
    _applying(monkeypatch)
    _write(folder, FINDINGS)
    assert sdlc.cmd_ship(root, "001") == 0


def test_a_skipped_ui_review_still_ships(change, monkeypatch) -> None:
    """143 R12: a pass that can't run is no stop once its line says why."""
    root, folder = change
    _applying(monkeypatch, "ui")
    note = (
        "> UI review: skipped, no current screenshots\n"
        "> UX review: skipped, no current screenshots\n"
    )
    _write(folder, FINDINGS.replace("> The note.\n", f"> The note.\n{note}"))
    assert sdlc.cmd_ship(root, "001") == 0
    assert "stage: shipped" in (folder / "intent.md").read_text(encoding="utf-8")


def _asked(passes: dict | None) -> str:
    question, why = sdlc.ship_question(".sdlc/work/001-x", [], "none", False, False, [], [],
                                       ".sdlc/work/inbox.md", passes=passes)  # fmt: skip
    assert why is None
    return question


def test_the_question_names_the_passes() -> None:
    """143 R14: the passes that ran in one clause, each skip with why; none, the question as it
    was."""
    ran = {"ran": True}
    every = _asked({"security": ran, "behaviour": ran, "ui": ran, "ux": ran})
    assert "after the security review, the behaviour check and the UI and UX reviews," in every
    assert _asked({"security": ran}).startswith("Commit this, after the security review, and ")
    assert "after the UX review," in _asked({"ui": {"ran": False, "why": "w"}, "ux": ran})
    skipped = _asked({"behaviour": ran, "ui": {"ran": False, "why": "no current screenshots"},
                      "ux": {"ran": False, "why": ""}})  # fmt: skip
    assert "after the behaviour check, without the UI review (no current screenshots), " in skipped
    assert "without the UX review (no reason given)" in skipped
    assert (
        _asked(None)
        == _asked({})
        == "Commit this, with .sdlc/work/001-x/ stamped shipped? (yes / edit the message)"
    )


def test_the_command_asks_with_the_passes_that_apply(change, capsys, monkeypatch) -> None:
    """The script reads the passes and the note itself: a line for a pass that doesn't apply is
    never named."""
    root, folder = change
    _applying(monkeypatch, "security", "ui")
    note = (
        "> Security review: ran\n> UI review: skipped, no screenshots of this change\n"
        "> UX review: skipped, no screenshots of this change\n> Behaviour check: ran\n"
    )
    _write(
        folder,
        FINDINGS.replace("> The note.\n", f"> The note.\n{note}")
        + "\n## Evidence\n\n$ true\nexit: 0\n",
    )
    assert sdlc.cmd_ship_question(root, "001", False, False, [], []) == 0
    question = capsys.readouterr().out
    assert (
        "after the security review, without the UI review (no screenshots of this change)"
        in question
    )
    assert "behaviour check" not in question
