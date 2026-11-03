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
                     "problems": []}  # fmt: skip


def test_the_template_is_never_read_as_a_finding() -> None:
    """Its section names every rank, pass and disposition, and a copy left as it is reads as a
    problem, never as a finding and never raising."""
    template = (ROOT / "templates" / "findings.md").read_text(encoding="utf-8")
    assert "## F1. [<important|nit|pre-existing>] [<correctness|contract|cost|context>]" in template
    assert "Disposition: <open|fixed|recorded|wrong|intentional|minor>" in template
    for key in ("Evidence:", "Class:", "Reason:"):
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
        "intentional=0 minor=0"
    )
    assert sdlc.findings_trailer([]).endswith("fixed=0 recorded=0 wrong=0 intentional=0 minor=0")


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
