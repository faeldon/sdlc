"""Unit tests over the change-pipeline tool.

The subject is `scripts/sdlc.py`, loaded by path because the plugin is not an
installed package — the same file the `/sdlc:*` skills run and a host repo's gate audits.

The weight here sits on `stamp_shipped`, which is the one function that rewrites a file a human
authored. Its docstring explains why it edits frontmatter lines in place instead of round-tripping
through `frontmatter.dumps()`; these tests are what keeps that true, because the YAML round-trip is
the obvious refactor and it corrupts every intent it touches (`id: 001` returns as the integer 1,
keys come back alphabetised, an empty `idea:` becomes `idea: null`).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SDLC_PY = REPO / "scripts" / "sdlc.py"
# The core's code, which the guards that read source scan: retro.py and closing.py beside the
# script loading them.
CORE = [SDLC_PY, REPO / "scripts" / "retro.py", REPO / "scripts" / "closing.py"]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_under_test", SDLC_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


INTENT = """\
---
id: 007
slug: reopen-drafts
tier: 2
stage: build
created: 2026-10-01
updated: 2026-10-05
idea:
---

# 007 — Reopen saved drafts

## Problem

Real prose, not a template.
"""


# ---------------------------------------------------------------- stamp_shipped


def test_stamp_shipped_sets_stage_and_dates() -> None:
    out, unplaced = sdlc.stamp_shipped(INTENT, "2026-10-17")
    assert unplaced == []
    assert "stage: shipped" in out
    assert "updated: 2026-10-17" in out
    assert "shipped: 2026-10-17" in out


def test_stamp_shipped_preserves_id_as_written() -> None:
    """`id: 007` must stay the string `007`.

    A YAML round-trip reads it as the integer 7 and writes it back as `id: 7`, after which the
    shipped intent no longer matches the `NNN` convention every other change uses, and the folder
    name and the frontmatter disagree.
    """
    out, _ = sdlc.stamp_shipped(INTENT, "2026-10-17")
    assert "id: 007" in out


def test_stamp_shipped_preserves_key_order_and_empty_values() -> None:
    out, _ = sdlc.stamp_shipped(INTENT, "2026-10-17")
    keys = [ln.split(":", 1)[0] for ln in out.splitlines()[1:] if ln.strip() and ":" in ln]
    keys = keys[: keys.index("idea") + 1]
    assert keys == ["id", "slug", "tier", "stage", "created", "updated", "shipped", "idea"], (
        "frontmatter order changed; `shipped:` belongs directly under `updated:`"
    )
    # Not `idea: null`, which is what a YAML dump produces for an empty value.
    assert "\nidea:\n" in out


def test_stamp_shipped_leaves_body_untouched() -> None:
    out, _ = sdlc.stamp_shipped(INTENT, "2026-10-17")
    assert "# 007 — Reopen saved drafts" in out
    assert "Real prose, not a template." in out


def test_stamp_shipped_is_idempotent() -> None:
    once, _ = sdlc.stamp_shipped(INTENT, "2026-10-17")
    twice, unplaced = sdlc.stamp_shipped(once, "2026-10-17")
    assert unplaced == []
    assert once == twice, "a second ship must not insert a duplicate `shipped:` line"


@pytest.mark.parametrize(
    "text,expected_missing",
    [
        ("no frontmatter at all\n", "a --- frontmatter block"),
        ("---\nid: 1\nslug: x\n", "a --- frontmatter block"),  # never closed
    ],
)
def test_stamp_shipped_reports_rather_than_writing_past(text: str, expected_missing: str) -> None:
    """A pattern that matches nothing must be reported, not silently skipped.

    This is the repo's characteristic bug class in miniature: the dangerous outcome is not an
    exception, it is `ship` cheerfully moving a folder whose frontmatter it never actually stamped.
    """
    out, unplaced = sdlc.stamp_shipped(text, "2026-10-17")
    assert expected_missing in unplaced
    assert out == text, "refused to stamp, so it must not have modified anything"


def test_stamp_shipped_refuses_when_updated_is_absent() -> None:
    """`shipped:` is anchored under `updated:`. With no anchor, it reports instead of guessing."""
    text = "---\nid: 001\nslug: x\ntier: 1\nstage: build\ncreated: 2026-10-01\n---\n\n# x\n"
    _, unplaced = sdlc.stamp_shipped(text, "2026-10-17")
    assert "shipped" in unplaced
    assert "updated" in unplaced


# ---------------------------------------------------------------- slugify


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Reopen Saved Drafts", "reopen-saved-drafts"),
        ("order_totals daily", "order-totals-daily"),
        ("  spaces  everywhere  ", "spaces-everywhere"),
        ("already-kebab", "already-kebab"),
        ("Dashes---collapsed", "dashes-collapsed"),
        ("ingest Café Prémier", "ingest-cafe-premier"),
        ("!!!", ""),
    ],
)
def test_slugify(raw: str, expected: str) -> None:
    assert sdlc.slugify(raw) == expected


# ---------------------------------------------------------------- is_unfilled


def test_is_unfilled_detects_an_untouched_template(tmp_path: Path) -> None:
    """The `~` marker in `status` depends on this, and so does `vet`'s unfilled-artifact problem.

    Without it, a Tier 2 change whose spec.md is still the scaffold is indistinguishable from one
    that was actually written — "looks done, is empty", which is the failure the whole process is
    arranged against.
    """
    scaffold = REPO / "templates" / "spec.md"
    p = tmp_path / "spec.md"
    p.write_text(scaffold.read_text(encoding="utf-8"), encoding="utf-8")
    assert sdlc.is_unfilled(p)


def test_is_unfilled_passes_real_prose(tmp_path: Path) -> None:
    p = tmp_path / "spec.md"
    p.write_text(
        "---\nid: 001\n---\n\n# 001 — x · spec\n\n## Requirements\n\n1. R1. It works.\n",
        encoding="utf-8",
    )
    assert not sdlc.is_unfilled(p)


def test_is_unfilled_tolerates_one_stray_bracket(tmp_path: Path) -> None:
    """Two prompt lines is the threshold, so prose with one `<tag>` is not read as a stub."""
    p = tmp_path / "intent.md"
    p.write_text("# 001 — x\n\nThe payload arrives as <record> elements, which we flatten.\n")
    assert not sdlc.is_unfilled(p)


# ---------------------------------------------------------------- check / analyze


def _change(root: Path, name: str, frontmatter_body: str, extra: dict[str, str] | None = None):
    d = root / ".sdlc" / "work" / name
    d.mkdir(parents=True)
    (d / "intent.md").write_text(frontmatter_body, encoding="utf-8")
    for fname, text in (extra or {}).items():
        (d / fname).write_text(text, encoding="utf-8")
    return d


def _fm(**kw) -> str:
    base = {
        "id": "001",
        "slug": "x",
        "tier": 1,
        "stage": "plan",
        "created": "2026-10-01",
        "updated": "2026-10-01",
    }
    base.update(kw)
    lines = "\n".join(f"{k}: {v}" for k, v in base.items())
    return f"---\n{lines}\n---\n\n# 001 — Written prose here, at length.\n\nBody text.\n"


def test_tier2_at_design_without_spec_is_a_problem(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm(tier=2, stage="design"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    details = [p["detail"] for p in a["problems"]]
    assert any("no spec.md" in d for d in details), details


def test_tier2_at_plan_without_spec_is_silent(tmp_path: Path) -> None:
    """Deliberate: `sdlc.py new --tier 2` scaffolds a change at stage: plan, and a tool whose own
    `new` produces something that instantly fails its own `vet` teaches you to ignore it.
    `status`'s `~` marker and the age column are what surface a stub left here for months."""
    _change(tmp_path, "001-x", _fm(tier=2, stage="plan"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert a["problems"] == []


def test_a_spike_owes_nothing_and_is_a_stage_check_accepts(tmp_path: Path) -> None:
    """A spike is exploration meant to be thrown away: no spec or plan is owed for it, whatever
    stage the change left to take it."""
    _change(tmp_path, "001-x", _fm(tier=2, stage="spike"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert a["problems"] == []
    assert sdlc.STAGES.index("plan") < sdlc.STAGES.index("spike") < sdlc.STAGES.index("design")


def test_tier2_at_build_needs_a_plan(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm(tier=2, stage="build"), {"spec.md": "# spec\n\nWritten.\n"})
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any("no plan.md" in p["detail"] for p in a["problems"])


def test_unfilled_spec_at_build_is_a_problem(tmp_path: Path) -> None:
    """Present-but-empty must not read as done — the distinction `vet` exists to draw."""
    scaffold = (REPO / "templates" / "spec.md").read_text(encoding="utf-8")
    _change(
        tmp_path,
        "001-x",
        _fm(tier=2, stage="build"),
        {"spec.md": scaffold, "plan.md": "# plan\n\nWritten.\n"},
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any("still the template" in p["detail"] for p in a["problems"])


PLAN_PROBLEM = "plan.md is still the template at stage: build"


def _first_build(root: Path, **files: str) -> Path:
    """A Tier 2 change at stage: build, its plan the scaffold, whose factory builder has started:
    `runs/builder.sessions` just written, no report yet. `files` adds or overrides run files."""
    plan = (REPO / "templates" / "plan.md").read_text(encoding="utf-8")
    d = _change(root, "001-x", _fm(tier=2, stage="build"),
                {"spec.md": "# spec\n\nWritten.\n", "plan.md": plan})  # fmt: skip
    (d / "runs").mkdir()
    (d / "runs" / "builder.sessions").write_text("s-1\n", encoding="utf-8")
    for rel, text in files.items():
        path = d / rel.replace("__", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return d


def _details(root: Path) -> list[str]:
    return [p["detail"] for p in sdlc.analyze(root, today=date(2026, 10, 17))["problems"]]


@pytest.mark.portable
@pytest.mark.parametrize(
    "step",
    [None, "STEP: build\nROUND: 1\n", "STEP: build\nROUND:\n"],
    ids=["no-step", "round-1", "no-round"],
)
def test_check_leaves_out_the_template_plan_during_a_live_first_build(tmp_path, step) -> None:
    """105 R10: the builder writes plan.md as its first step; while that build is live, the
    scaffold is no problem."""
    _first_build(tmp_path, **({"runs__step.md": step} if step else {}))
    assert PLAN_PROBLEM not in _details(tmp_path)


@pytest.mark.portable
@pytest.mark.parametrize(
    "case",
    ["report", "stopped", "stale", "review-step", "later-round", "no-sessions"],
)
def test_the_template_plan_shows_once_the_first_build_is_not_live(tmp_path, case) -> None:
    """105 R10: a report written, a stop recorded, a session past the agent timeout, a step other
    than the first build, or no factory session at all: the problem is back."""
    files = {
        "report": {"build__round-1.md": "Built.\n"},
        "stopped": {"runs__stopped.md": "STOPPED: rerun\nNEXT: rerun it\n"},
        "review-step": {"runs__step.md": "STEP: review\nROUND: 1\n"},
        "later-round": {"runs__step.md": "STEP: build\nROUND: 2\n"},
    }.get(case, {})
    d = _first_build(tmp_path, **files)
    sessions = d / "runs" / "builder.sessions"
    if case == "stale":
        old = time.time() - sdlc.factory_records.AGENT_TIMEOUT - 60
        os.utime(sessions, (old, old))
    if case == "no-sessions":
        sessions.unlink()
    assert PLAN_PROBLEM in _details(tmp_path)


def _upgraded_build(root: Path, **files: str) -> Path:
    """112: a change upgraded to Tier 2 before round 2, its spec approved, at stage: build, its
    plan the scaffold, whose resumed builder is building round 2 now: the supervisor's reading
    names it, just written. `files` adds or overrides run files."""
    plan = (REPO / "templates" / "plan.md").read_text(encoding="utf-8")
    d = _change(root, "001-x", _fm(tier=2, stage="build"),
                {"spec.md": "# spec\n\nWritten.\n", "plan.md": plan})  # fmt: skip
    files = {
        "build__round-1.md": "Built round 1.\n",
        "build__round-2.upgraded.md": "UPGRADED: D1\n",
        "runs__builder.sessions": "s-1\n",
        "runs__step.md": "STEP: build\nROUND: 2\n",
        **files,
    }
    for rel, text in files.items():
        path = d / rel.replace("__", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    old = time.time() - sdlc.factory_records.AGENT_TIMEOUT - 60
    os.utime(d / "runs" / "builder.sessions", (old, old))  # the session began in round 1
    return d


@pytest.mark.portable
def test_check_leaves_out_the_template_plan_during_a_live_upgraded_build(tmp_path) -> None:
    """112 R12: the resumed builder rewrites plan.md first; while round P is live, the scaffold is
    no problem, and nothing else is hidden."""
    d = _upgraded_build(tmp_path)
    assert PLAN_PROBLEM not in _details(tmp_path)
    (d / "spec.md").write_text(
        (REPO / "templates" / "spec.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    details = _details(tmp_path)
    assert PLAN_PROBLEM not in details
    assert "spec.md is still the template at stage: build" in details


@pytest.mark.portable
@pytest.mark.parametrize(
    "case", ["report", "stopped", "stale", "review-step", "other-round", "no-record", "no-step"]
)
def test_the_template_plan_shows_once_the_upgraded_build_is_not_live(tmp_path, case) -> None:
    """112 R12: round P's report written, a stop recorded, a reading past the agent timeout, a step
    other than round P's build, no upgrade record, or no reading: the problem is back."""
    files = {
        "report": {"build__round-2.md": "Built round 2.\n"},
        "stopped": {"runs__stopped.md": "STOPPED: rerun\nNEXT: rerun it\n"},
        "review-step": {"runs__step.md": "STEP: review\nROUND: 2\n"},
        "other-round": {"runs__step.md": "STEP: build\nROUND: 3\n"},
    }.get(case, {})
    d = _upgraded_build(tmp_path, **files)
    if case == "stale":
        old = time.time() - sdlc.factory_records.AGENT_TIMEOUT - 60
        os.utime(d / "runs" / "step.md", (old, old))
    if case == "no-record":
        (d / "build" / "round-2.upgraded.md").unlink()
    if case == "no-step":
        (d / "runs" / "step.md").unlink()
    assert PLAN_PROBLEM in _details(tmp_path)


@pytest.mark.portable
def test_a_live_first_build_hides_no_other_problem(tmp_path) -> None:
    """105 R10: only the plan's problem is left out: an unfilled spec or intent still shows."""
    d = _first_build(tmp_path)
    (d / "spec.md").write_text(
        (REPO / "templates" / "spec.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (d / "intent.md").write_text(
        _fm(tier=2, stage="build") + "\n<a prompt>\n<another prompt>\n", encoding="utf-8"
    )
    details = _details(tmp_path)
    assert PLAN_PROBLEM not in details
    assert "spec.md is still the template at stage: build" in details
    assert "intent.md is still the template at stage: build" in details


@pytest.mark.parametrize(
    "bad,needle",
    [
        ({"tier": 3}, "tier must be 1 or 2"),
        ({"stage": "finished"}, "stage must be one of"),
        ({"created": ""}, "missing created"),
    ],
)
def test_bad_frontmatter_is_reported_not_raised(tmp_path: Path, bad: dict, needle: str) -> None:
    _change(tmp_path, "001-x", _fm(**bad))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any(needle in p["detail"] for p in a["problems"]), a["problems"]


def test_unparseable_yaml_is_reported_not_raised(tmp_path: Path) -> None:
    """A broken intent must show up in the report rather than crash it — otherwise one bad file
    makes the whole pipeline unreadable, which is when people stop running the tool."""
    _change(tmp_path, "001-x", "---\nid: 001\n  bad: [indent\n---\n\n# x\n")
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any(p["kind"] == "frontmatter" for p in a["problems"])


def test_a_shipped_change_still_open_is_not_a_problem(tmp_path: Path) -> None:
    """Shipped and waiting for close: its folder stays where it is until close removes it."""
    _change(tmp_path, "001-x", _fm(stage="shipped"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert a["problems"] == []


def test_dropped_changes_are_exempt_from_their_tiers_artifacts(tmp_path: Path) -> None:
    text = _fm(tier=2, stage="dropped", dropped_at="build") + "\n## Dropped\n\nNot needed.\n"
    _change(tmp_path, "001-x", text)
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert a["problems"] == []


def test_a_dropped_change_owes_its_reason_and_a_real_stage(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm(stage="dropped", dropped_at="lunch"))
    _change(tmp_path, "002-y", _fm(id="002", slug="y", stage="dropped") + "\n## Dropped\n\n<why>\n")
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    details = sorted((p["dir"], p["detail"].split(" ")[0]) for p in a["problems"])
    assert details == [
        (".sdlc/work/001-x", "dropped_at"),
        (".sdlc/work/001-x", "stage:"),
        (".sdlc/work/002-y", "stage:"),
    ]


def test_stamp_dropped_edits_its_three_lines_and_nothing_else() -> None:
    text = "---\nid: 015\nslug: x\nstage: build\nupdated: 2026-10-01\nidea:\n---\n\n# body\n"
    out, unplaced = sdlc.stamp_dropped(text, "2026-10-24", "build")
    assert unplaced == []
    assert out == (
        "---\nid: 015\nslug: x\nstage: dropped\nupdated: 2026-10-24\ndropped_at: build\nidea:\n"
        "---\n\n# body\n"
    )
    again, _ = sdlc.stamp_dropped(out, "2026-10-25", "build")
    assert again.count("dropped_at:") == 1


def test_age_is_computed_for_the_status_signal(tmp_path: Path) -> None:
    """Age is the signal the process doc names as worth watching: an intent sitting at stage: plan
    for weeks is an unmade decision rather than a queued task."""
    _change(tmp_path, "001-x", _fm(created="2026-10-01"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert a["open"][0]["age_days"] == 16


def test_next_id_allocates_sequentially(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm())
    _change(tmp_path, "007-y", _fm(id="007", slug="y"))
    assert sdlc.next_id(tmp_path) == "008"


def test_next_id_starts_at_001_on_an_empty_pipeline(tmp_path: Path) -> None:
    (tmp_path / ".sdlc" / "work").mkdir(parents=True)
    assert sdlc.next_id(tmp_path) == "001"


def _counter(root: Path, text: str) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "last-id").write_text(text, encoding="utf-8")


@pytest.mark.parametrize("last, folder, expected", [("041", "001", "042"), ("003", "007", "008")])
def test_next_id_reads_the_counter_and_the_folders(
    tmp_path: Path, last: str, folder: str, expected: str
) -> None:
    """Main's counter trails the open changes, so the higher of the two wins."""
    _change(tmp_path, f"{folder}-x", _fm(id=folder))
    _counter(tmp_path, f"{last}\n")
    assert sdlc.next_id(tmp_path) == expected


def test_new_seeds_a_missing_counter_from_the_folders_then_writes_it(tmp_path: Path) -> None:
    """Outside git there is no worktree, so `new` writes the counter in the checkout itself."""
    _change(tmp_path, "007-y", _fm(id="007", slug="y"))
    assert sdlc.cmd_new(tmp_path, "z", 1, None) == 0
    assert (tmp_path / ".sdlc" / "work" / "008-z").is_dir()
    assert (tmp_path / ".sdlc" / "last-id").read_text(encoding="utf-8") == "008\n"
    assert not (tmp_path / ".sdlc" / "last-id.tmp").exists()


def test_a_number_is_never_reused_after_its_folder_is_deleted(tmp_path: Path) -> None:
    """Scanning the folders would hand 002 out again; the counter remembers it was spent."""
    assert sdlc.cmd_new(tmp_path, "a", 1, None) == 0
    assert sdlc.cmd_new(tmp_path, "b", 1, None) == 0
    shutil.rmtree(tmp_path / ".sdlc" / "work" / "002-b")
    assert sdlc.cmd_new(tmp_path, "c", 1, None) == 0
    assert (tmp_path / ".sdlc" / "work" / "003-c").is_dir()


def test_check_flags_an_unreadable_counter(tmp_path: Path) -> None:
    _change(tmp_path, "007-y", _fm(id="007", slug="y"))
    _counter(tmp_path, "seven\n")
    problems = sdlc.analyze(tmp_path)["problems"]
    assert [p["kind"] for p in problems] == ["last id"]
    assert "doesn't hold a number" in problems[0]["detail"]


@pytest.mark.parametrize("last", [None, "003\n", "009\n"])
def test_check_is_quiet_with_no_counter_or_one_behind_or_ahead_of_the_folders(
    tmp_path: Path, last: str | None
) -> None:
    """Behind is normal: main's counter only moves when a change merges."""
    _change(tmp_path, "007-y", _fm(id="007", slug="y"))
    if last:
        _counter(tmp_path, last)
    assert sdlc.analyze(tmp_path)["problems"] == []


def test_orphan_building_idea_is_flagged(tmp_path: Path) -> None:
    (tmp_path / ".sdlc" / "work").mkdir(parents=True)
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(
        "## [2026-10-01-1] [building] Column level lineage export\n\nSome prose.\n",
        encoding="utf-8",
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any(p["kind"] == "orphan idea" for p in a["problems"])


def test_building_idea_with_a_folder_is_quiet(tmp_path: Path) -> None:
    """The slug match is deliberately loose both ways: a folder slug is a shortening of the idea's
    title, never a copy, so an exact comparison would nag about every idea being worked on."""
    _change(tmp_path, "001-column-lineage", _fm(slug="column-lineage"))
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(
        "## [2026-10-01-1] [building] Column lineage\n", encoding="utf-8"
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert not any(p["kind"] == "orphan idea" for p in a["problems"])


def test_building_idea_linked_only_by_frontmatter_is_quiet(tmp_path: Path) -> None:
    """`idea:` is the explicit link /sdlc:intent writes, so it counts even when the slug has
    drifted from the title. The frontmatter keeps the heading as it read at
    promotion, `[seed]`, while work/inbox.md now says `[building]`, so the match is on the title."""
    _change(
        tmp_path,
        "001-search-front-end",
        _fm(slug="search-front-end", idea='"[2026-10-01] [seed] Search as its own page"'),
    )
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(
        "## [2026-10-01-1] [building] Search as its own page\n", encoding="utf-8"
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert not any(p["kind"] == "orphan idea" for p in a["problems"])


def test_building_idea_linked_only_to_a_dropped_change_is_flagged(tmp_path: Path) -> None:
    """A dropped change isn't building anything, so its `idea:` can't vouch for the seed."""
    _change(
        tmp_path,
        "001-search-widget",
        _fm(
            slug="search-widget",
            stage="dropped",
            idea='"[2026-10-01] [seed] Search as its own page"',
        ),
    )
    (tmp_path / ".sdlc" / "work" / "inbox.md").write_text(
        "## [2026-10-01-1] [building] Search as its own page\n", encoding="utf-8"
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any(p["kind"] == "orphan idea" for p in a["problems"])


def test_templates_exist_for_every_tier() -> None:
    """`new --tier N` refuses rather than half-scaffolding if a template is missing, so the
    templates shipping with the plugin is a precondition worth asserting."""
    for artifacts in sdlc.TIER_ARTIFACTS.values():
        for name in artifacts:
            assert (sdlc.TEMPLATE_DIR / name).is_file(), f"{name} missing from {sdlc.TEMPLATE_DIR}"


@pytest.mark.parametrize("tier", [1, 2])
def test_new_starts_no_notes(tmp_path: Path, tier: int) -> None:
    """Notes are optional: a skill starts the file when there's something to note, so an untouched
    one never lands as an empty comment on the change's issue."""
    assert sdlc.cmd_new(tmp_path, "quiet", tier, None) == 0
    folder = next((tmp_path / ".sdlc" / "work").glob("*-quiet"))
    assert sorted(p.name for p in folder.iterdir()) == sorted(sdlc.TIER_ARTIFACTS[tier])


def test_a_hosts_inbox_and_notes_templates_win(tmp_path: Path) -> None:
    for name in ("inbox.md", "notes.md"):
        assert sdlc.template_path(tmp_path, name) == (sdlc.TEMPLATE_DIR / name, "plugin")
        (tmp_path / ".sdlc" / "templates").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".sdlc" / "templates" / name).write_text("# Mine\n", encoding="utf-8")
        assert sdlc.template_path(tmp_path, name) == (
            tmp_path / ".sdlc" / "templates" / name, "host",
        )  # fmt: skip


def test_ship_stamps_in_place(tmp_path: Path) -> None:
    """The folder stays where its branch commits it; close removes it once the change lands."""
    d = _change(tmp_path, "001-x", _fm(stage="build", impact="patch"))
    assert sdlc.cmd_ship(tmp_path, "001") == 0
    assert "stage: shipped" in (d / "intent.md").read_text(encoding="utf-8")
    assert sorted(p.name for p in (tmp_path / ".sdlc" / "work").iterdir()) == ["001-x"]


# ---------------------------------------------------------------- release impact


def test_ship_refuses_without_a_release_impact_then_ships_once_set(tmp_path: Path, capsys) -> None:
    """A change with no impact would reach a release that can't propose its bump, and the bump
    would be picked from memory again. Refused before stamping."""
    d = _change(tmp_path, "001-x", _fm(stage="build"))
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(tmp_path, "001") == 1
    assert "impact must be one of major|minor|patch|none, got ''" in capsys.readouterr().err
    assert (d / "intent.md").read_text(encoding="utf-8") == before and d.is_dir()

    (d / "intent.md").write_text(_fm(stage="build", impact="big"), encoding="utf-8")
    assert sdlc.cmd_ship(tmp_path, "001") == 1
    assert "got 'big'" in capsys.readouterr().err

    (d / "intent.md").write_text(_fm(stage="build", impact="none"), encoding="utf-8")
    assert sdlc.cmd_ship(tmp_path, "001") == 0
    shipped = (d / "intent.md").read_text(encoding="utf-8")
    assert "impact: none" in shipped and "stage: shipped" in shipped


def test_an_invalid_impact_is_a_frontmatter_error_and_an_empty_one_is_not(tmp_path: Path) -> None:
    """Empty until ship settles it, and absent on changes shipped before 033; only a value outside
    the four is wrong, so `vet --strict` catches a typo before a release reads it."""
    bad = _change(tmp_path, "001-x", _fm(impact="mnior"))
    assert any("impact must be one of" in e for e in sdlc.load_change(bad, tmp_path)["errors"])
    empty = _change(tmp_path, "002-y", _fm(id="002", slug="y", impact=""))
    rec = sdlc.load_change(empty, tmp_path)
    assert rec["errors"] == [] and rec["impact"] == ""


def test_the_intent_template_has_an_empty_impact_line() -> None:
    template = (sdlc.TEMPLATE_DIR / "intent.md").read_text(encoding="utf-8")
    assert "\ntier: 1\nimpact:\nstage: plan\n" in template


# ---------------------------------------------------------------- undone notes

NOTES = """\
# Notes

## V1

- [ ] Desktop chat and Cowork
  * [ ] nested, with a star
- [x] claude.ai chat
- [X] uppercase tick
Prose that mentions [ ] in passing, and - [ ] not at the start.

```
- [ ] an example of the marker, in a code block
```

- [ ] V2 upload limit
"""


def test_open_items_finds_unticked_lines_with_their_line_numbers(tmp_path: Path) -> None:
    d = _change(tmp_path, "001-x", _fm(stage="build"), {"notes.md": NOTES})
    assert sdlc.open_items(d) == [
        {"file": "notes.md", "line": 5, "text": "Desktop chat and Cowork"},
        {"file": "notes.md", "line": 6, "text": "nested, with a star"},
        {"file": "notes.md", "line": 15, "text": "V2 upload limit"},
    ]


def test_open_items_without_notes_is_empty(tmp_path: Path) -> None:
    assert sdlc.open_items(_change(tmp_path, "001-x", _fm(stage="build"))) == []


def test_status_counts_undone_items(tmp_path: Path, capsys) -> None:
    _change(tmp_path, "001-x", _fm(stage="build"), {"notes.md": NOTES})
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert len(a["changes"][0]["undone"]) == 3
    sdlc.print_status(a)
    assert "· 3 undone" in capsys.readouterr().out


def test_undone_prints_the_items_as_json(tmp_path: Path, capsys) -> None:
    _change(tmp_path, "001-x", _fm(stage="build"), {"notes.md": NOTES})
    assert sdlc.cmd_undone(tmp_path, "001") == 0
    out = json.loads(capsys.readouterr().out)
    assert out["change"] == "001-x"
    assert out["notes"] == ".sdlc/work/001-x/notes.md"
    assert [i["line"] for i in out["items"]] == [5, 6, 15]


def test_ship_refuses_while_an_item_is_undone_then_ships_once_each_is_answered(
    tmp_path: Path, capsys
) -> None:
    d = _change(tmp_path, "001-x", _fm(stage="build", impact="patch"), {"notes.md": NOTES})
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(tmp_path, "001") == 1
    err = capsys.readouterr().err
    assert "3 undone item(s)" in err
    assert "notes.md:5  Desktop chat and Cowork" in err and "notes.md:15  V2 upload limit" in err
    assert (d / "intent.md").read_text(encoding="utf-8") == before  # not stamped

    answered = (
        NOTES.replace("- [ ] Desktop chat", "- [x] Desktop chat")
        .replace("* [ ] nested, with a star", "* [x] nested, with a star → dropped: a test")
        .replace("- [ ] V2 upload limit", "- [x] V2 upload limit → seed: Measure the limit")
    )
    (d / "notes.md").write_text(answered, encoding="utf-8")
    assert sdlc.cmd_ship(tmp_path, "001") == 0
    assert "stage: shipped" in (d / "intent.md").read_text(encoding="utf-8")


def test_ship_refusal_names_every_disposition(tmp_path: Path, capsys) -> None:
    """114 R19: an undone item is answered by a seed, a bug or a drop, and the refusal names all
    three, so a `pre-existing:` item filed as a bug isn't sent back as a seed."""
    _change(tmp_path, "001-x", _fm(stage="build", impact="patch"), {"notes.md": NOTES})
    assert sdlc.cmd_ship(tmp_path, "001") == 1
    err = " ".join(capsys.readouterr().err.split())
    for said in ("→ seed: <id>", "→ bug: <id>", "→ dropped: <reason>"):
        assert said in err, err


# ---------------------------------------------------------------- worktrees


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, trunk: str = "main") -> Path:
    """A real repo on `trunk` that ignores its change worktrees and commits work/. Any other
    trunk is named in its config, since a repo with no `main` and no remote has no base."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    if trunk != "main":
        (root / ".sdlc").mkdir(exist_ok=True)
        (root / ".sdlc" / "config.toml").write_text(f'[git]\nbase = "{trunk}"\n', "utf-8")
    _git(root, "init", "-q", "-b", trunk)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _sibling(root: Path, name: str) -> Path:
    tree = root.parent / name
    _git(root, "worktree", "add", "-q", "-b", name, str(tree), "main")
    return tree


def test_next_id_reads_the_main_checkout_from_a_worktree(tmp_path: Path) -> None:
    """A worktree reading only its own work/ would hand out a number the main checkout already
    holds. Run from the worktree, it reads the main checkout's."""
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    _change(root, "020-in-the-main-checkout", _fm(id="020"))
    assert sdlc.next_id(sdlc.main_root(tree)) == "021"


def test_next_id_counts_worktrees_but_not_bare_branches_or_their_folders(tmp_path: Path) -> None:
    """An open change's number is in its worktree until its counter merges, so a branch checked
    out in one holds its number. A bare branch that only looks like a change (`2024-cleanup`)
    claims nothing, or it would push the numbering forward for good; nor does a folder in a
    worktree that isn't a change's."""
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    _change(tree, "004-over-there", _fm(id="004"))
    _git(root, "branch", "2024-cleanup")
    _git(root, "branch", "100-days-plan")
    assert sdlc.next_id(root) == "001"
    _sibling(root, "009-claimed")
    assert sdlc.next_id(root) == "010"


def test_an_abandoned_change_frees_its_number(tmp_path: Path) -> None:
    """By design: removed before it reached main, it left no counter, branch or folder, and
    nothing that was ever committed refers to its number."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "dropped", 1, None, worktree=True) == 0
    tree = root / ".claude" / "worktrees" / "001-dropped"
    _git(root, "worktree", "remove", "--force", str(tree))
    _git(root, "branch", "-D", "001-dropped")
    assert sdlc.next_id(root) == "001"


def test_new_without_a_worktree_writes_the_counter_where_it_runs(tmp_path: Path) -> None:
    """Run from inside a worktree, the folder and the counter go there, to be committed with that
    branch. Untracked ones in the main checkout would stop close's fast-forward part-way."""
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    assert sdlc.cmd_new(tree, "here", 1, None) == 0
    assert (tree / ".sdlc" / "last-id").read_text(encoding="utf-8") == "001\n"
    assert (tree / ".sdlc" / "work" / "001-here" / "intent.md").is_file()
    assert _git(root, "status", "--porcelain") == ""


def test_new_refuses_a_slug_already_in_the_main_checkout(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    _change(root, "003-same-thing", _fm(id="003"))
    assert sdlc.cmd_new(tree, "same-thing", 1, None) == 1
    assert not (tree / ".sdlc" / "work" / "004-same-thing").exists()


def test_new_refuses_a_slug_open_in_another_worktree(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "same-thing", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "same-thing", 1, None, worktree=True) == 1
    assert "002-same-thing" not in _git(root, "branch", "--list")


def test_new_refuses_while_work_is_ignored(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".gitignore").write_text(".sdlc/work/\n", encoding="utf-8")
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 1
    assert "is gitignored: remove the line that ignores it" in capsys.readouterr().err
    assert "001-thing" not in _git(root, "branch", "--list")


def test_check_flags_an_ignored_work(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _change(root, "001-x", _fm())
    assert sdlc.analyze(root)["problems"] == []
    (root / ".gitignore").write_text(".sdlc/work/\n", encoding="utf-8")
    assert [p["kind"] for p in sdlc.analyze(root)["problems"]] == ["ignored"]


def test_new_worktree_makes_the_folder_in_the_worktree_and_leaves_main_untouched(
    tmp_path: Path,
) -> None:
    """The folder is committed on the change's branch, and the branch is cut from main, not from
    whatever this checkout has out, which is how one change ends up inside another's branch."""
    root = _repo(tmp_path)
    main_sha = _git(root, "rev-parse", "main")
    _git(root, "checkout", "-q", "-b", "elsewhere")
    _git(root, "commit", "-q", "--allow-empty", "-m", "someone else's work")

    assert sdlc.cmd_new(root, "fresh-thing", 1, None, worktree=True) == 0

    tree = root / ".claude" / "worktrees" / "001-fresh-thing"
    assert _git(tree, "branch", "--show-current") == "001-fresh-thing"
    assert _git(tree, "rev-parse", "HEAD") == main_sha
    assert (tree / ".sdlc" / "work" / "001-fresh-thing" / "intent.md").is_file()
    assert not (root / ".sdlc" / "work").exists()
    assert _git(root, "status", "--porcelain") == ""


def test_new_worktree_from_inside_a_worktree_lands_under_the_main_checkout(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    assert sdlc.cmd_new(tree, "nested", 1, None, worktree=True) == 0
    made = root / ".claude" / "worktrees" / "001-nested"
    assert (made / ".sdlc" / "work" / "001-nested" / "intent.md").is_file()
    assert not (tree / ".sdlc" / "work").exists() and not (root / ".sdlc" / "work").exists()


def test_status_sees_changes_in_every_worktree_from_any_checkout(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "first", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "second", 2, None, worktree=True) == 0
    trees = root / ".claude" / "worktrees"
    for where in (root, trees / "001-first", trees / "002-second"):
        assert [r["id"] for r in sdlc.analyze(where)["open"]] == ["001", "002"], where


def test_a_path_left_under_worktrees_holds_its_number(tmp_path: Path) -> None:
    """Or every `new` would land on the same path and fail."""
    root = _repo(tmp_path)
    (root / ".claude" / "worktrees" / "001-taken").mkdir(parents=True)
    assert sdlc.cmd_new(root, "taken", 1, None, worktree=True) == 0
    assert (root / ".claude" / "worktrees" / "002-taken").is_dir()


def test_new_worktree_makes_no_folder_and_writes_no_counter_when_the_worktree_fails(
    tmp_path: Path,
) -> None:
    """Nothing holds 001 afterwards, no folder, branch or path, so it is free to hand out."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True, base="no-such-branch") == 1
    assert "001-thing" not in _git(root, "branch", "--list")
    assert not (root / ".sdlc" / "work" / "001-thing").exists()
    assert not (root / ".sdlc" / "last-id").exists()
    assert sdlc.next_id(root) == "001"


def test_new_worktree_writes_the_counter_in_the_worktree_not_under_git(tmp_path: Path) -> None:
    """The bump rides the change's branch, and the main checkout stays as it was."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 0
    tree = root / ".claude" / "worktrees" / "001-thing"
    assert _git(root, "status", "--porcelain") == ""
    assert (tree / ".sdlc" / "last-id").read_text(encoding="utf-8") == "001\n"
    untracked = {ln[3:] for ln in _git(tree, "status", "--porcelain").splitlines()}
    assert {".sdlc/"} <= untracked
    assert not (root / ".sdlc" / "last-id").exists()


def test_an_open_change_holds_its_number_with_main_counter_behind(tmp_path: Path) -> None:
    """Main's counter never moved, and deleting the open change's folder doesn't free its
    number while its branch exists."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "first", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "second", 1, None, worktree=True) == 0
    assert not (root / ".sdlc" / "last-id").exists()
    shutil.rmtree(root / ".claude" / "worktrees" / "002-second" / ".sdlc" / "work" / "002-second")
    assert sdlc.next_id(root) == "003"


@pytest.mark.portable
def test_concurrent_claims_get_distinct_numbers(tmp_path: Path, monkeypatch) -> None:
    """Sessions that read the next id at the same moment, for different slugs. A bare `mkdir`
    would hand every one of them 001; the lock makes them take turns."""
    real = sdlc.next_id

    def slow(home: Path) -> str:
        nid = real(home)
        time.sleep(0.05)  # widen the gap between reading the id and making its folder
        return nid

    monkeypatch.setattr(sdlc, "next_id", slow)
    start = threading.Barrier(4)
    made: list[Path | None] = []

    def one(slug: str) -> None:
        start.wait()
        made.append(sdlc.claim(tmp_path, slug)[0])

    threads = [threading.Thread(target=one, args=(s,)) for s in ("a", "b", "c", "d")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(p.name[:3] for p in made if p) == ["001", "002", "003", "004"]


@pytest.mark.portable
def test_concurrent_worktree_claims_get_distinct_numbers(tmp_path: Path, monkeypatch) -> None:
    """With worktrees, the branch made under the lock is what the next claim counts."""
    root = _repo(tmp_path)
    real = sdlc.next_id

    def slow(home: Path) -> str:
        nid = real(home)
        time.sleep(0.05)
        return nid

    monkeypatch.setattr(sdlc, "next_id", slow)
    start = threading.Barrier(2)
    made: list[Path | None] = []

    def one(slug: str) -> None:
        start.wait()
        made.append(sdlc.claim(root, slug, base="main")[0])

    threads = [threading.Thread(target=one, args=(s,)) for s in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(p.name[:3] for p in made if p) == ["001", "002"]


# ---------------------------------------------------------------- numbers and closing


def test_next_prints_the_id_and_writes_nothing(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _repo(tmp_path)
    _change(root, "004-there", _fm(id="004"))
    before = sorted(p.name for p in (root / ".sdlc" / "work").iterdir())
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "next"])
    assert sdlc.main() == 0
    assert capsys.readouterr().out.strip() == "005"
    assert sorted(p.name for p in (root / ".sdlc" / "work").iterdir()) == before


def test_new_names_the_main_checkout_for_worktree_setup(tmp_path: Path, capsys) -> None:
    """`worktree_setup`'s `{main}` comes from this line, as `{worktree}` does."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 0
    line = next(x for x in capsys.readouterr().out.splitlines() if "created  worktree" in x)
    assert f"main checkout {root}" in line


def test_two_changes_opened_one_after_another_get_consecutive_ids(tmp_path: Path) -> None:
    """What two sessions drafting at once do: both were shown the same next id, and whichever
    creates second simply gets the following one."""
    root = _repo(tmp_path)
    assert sdlc.next_id(root) == "001"
    assert sdlc.cmd_new(root, "first", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "second", 1, None, worktree=True) == 0
    trees = sorted(p.name for p in (root / ".claude" / "worktrees").iterdir())
    assert trees == ["001-first", "002-second"]


def _shipped_change(root: Path, slug: str = "thing") -> tuple[Path, str]:
    """A change opened in its worktree, shipped, and committed there with its folder, as
    /sdlc:ship leaves it."""
    assert sdlc.cmd_new(root, slug, 1, None, worktree=True) == 0
    branch = next(b for _, b in sdlc.worktrees(root) if b.endswith(f"-{slug}"))
    tree = root / ".claude" / "worktrees" / branch
    intent = tree / ".sdlc" / "work" / branch / "intent.md"
    # /sdlc:ship sets the impact the human approved before it runs `ship`.
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    assert sdlc.cmd_ship(root, branch[:3]) == 0
    (tree / f"{slug}.txt").write_text("the change\n", encoding="utf-8")
    # The change's own paths: its code, its folder and the counter `new` wrote beside it.
    _git(tree, "add", f"{slug}.txt", ".sdlc")
    _git(tree, "commit", "-q", "-m", f"ship {branch}")
    return tree, branch


def _close(root: Path, ident, capsys, check_only: bool = False) -> tuple[int, dict]:
    capsys.readouterr()  # what new and ship printed while setting up
    code = sdlc.closing.cmd_close(root, ident, check_only)
    return code, json.loads(capsys.readouterr().out)


def test_close_lands_removes_the_folder_in_a_commit_and_tidies(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """With nowhere to mirror to (no GitHub remote), the folder is still removed: the change's own
    commit, now on main, is the copy."""
    root = _repo(tmp_path)
    tree, branch = _shipped_change(root)
    tip = _git(tree, "rev-parse", "HEAD")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert out["done"] == [
        "merge",
        "verify",
        "measure",
        "remove folder",
        "remove worktree",
        "delete branch",
    ]
    assert out["archive"]["kept_because"] == "archive.target is none"
    assert _git(root, "rev-parse", "main~1") == tip
    assert _git(root, "log", "-1", "--format=%s%n%b", "main").splitlines()[0] == f"Close {branch}"
    assert (
        not (root / ".sdlc" / "work" / branch).exists()
        and _git(root, "status", "--porcelain") == ""
    )
    assert "stage: shipped" in _git(root, "show", f"{tip}:.sdlc/work/{branch}/intent.md")
    assert not tree.exists()
    assert branch not in _git(root, "branch", "--list")


def test_close_check_writes_nothing(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    tree, branch = _shipped_change(root)
    before = _git(root, "rev-parse", "main")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys, check_only=True)
    assert code == 0 and out["refusals"] == [] and out["done"] == []
    assert _git(root, "rev-parse", "main") == before and tree.is_dir()


def _with_main_files(root: Path, *names: str) -> None:
    for name in names:
        (root / name).write_text(f"{name}\n", encoding="utf-8")
    _git(root, "add", *names)
    _git(root, "commit", "-q", "-m", "files main holds")


def test_close_check_names_what_the_merge_deletes_from_the_main_checkout(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """A file the change stops tracking and ignores goes from the main checkout's disk at the
    fast-forward all the same: the question names it, apart from a file simply deleted."""
    root = _repo(tmp_path)
    _with_main_files(root, "data.db", "old.txt")
    tree, branch = _shipped_change(root)
    _git(tree, "rm", "-q", "--cached", "data.db")
    with (tree / ".gitignore").open("a", encoding="utf-8", newline="\n") as f:
        f.write("data.db\n")
    _git(tree, "rm", "-q", "old.txt")
    _git(tree, "add", ".gitignore")
    _git(tree, "commit", "-q", "-m", "keep the data out of git")
    before = _git(root, "rev-parse", "main")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys, check_only=True)
    assert code == 0, out
    assert out["deletes"] == {"ignored": ["data.db"], "other": ["old.txt"]}
    assert _git(root, "rev-parse", "main") == before and (root / "data.db").is_file()
    assert _git(root, "status", "--porcelain") == ""


def test_close_check_counts_a_rename_as_no_deletion(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _with_main_files(root, "notes.txt")
    tree, _ = _shipped_change(root)
    _git(tree, "mv", "notes.txt", "renamed.txt")
    _git(tree, "commit", "-q", "-m", "rename")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys, check_only=True)
    assert code == 0 and out["deletes"] == {"ignored": [], "other": []}, out


def test_close_check_says_nothing_deleted_as_empty_lists(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    _shipped_change(root)
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys, check_only=True)
    assert code == 0 and out["deletes"] == {"ignored": [], "other": []}, out


def test_close_reports_no_deletions_once_merged_or_dropped(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """Neither a rerun after the merge nor a drop's `-s ours` record removes a file."""
    root = _repo(tmp_path)
    tree, _ = _shipped_change(root)
    monkeypatch.chdir(tree)
    assert _close(tree, None, capsys)[0] == 3
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys, check_only=True)
    assert code == 0 and "deletes" not in out, out

    assert sdlc.cmd_new(root, "gone", 1, None, worktree=True) == 0
    branch = next(b for _, b in sdlc.worktrees(root) if b.endswith("-gone"))
    dropped = root / ".claude" / "worktrees" / branch
    intent = dropped / ".sdlc" / "work" / branch / "intent.md"
    intent.write_text(
        intent.read_text().replace("stage: plan\n", "stage: dropped\n", 1) + "\n## Dropped\n\nNo.\n"
    )
    assert sdlc.cmd_drop(dropped, None) == 0
    code, out = _close(root, branch[:3], capsys, check_only=True)
    assert code == 0 and out["kind"] == "dropped" and "deletes" not in out, out


def test_close_goes_ahead_when_the_deletions_cant_be_read(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    _shipped_change(root)
    real = sdlc._git

    def failing(where, *args):
        return None if "--diff-filter=D" in args else real(where, *args)

    monkeypatch.setattr(sdlc, "_git", failing)
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert "unknown" in out["deletes"] and "remove folder" in out["done"], out


def _diverge(root: Path, tree: Path) -> None:
    (root / "other.txt").write_text("x", encoding="utf-8")
    _git(root, "add", "other.txt")
    _git(root, "commit", "-q", "-m", "main moved")


@pytest.mark.parametrize(
    "spoil, needle",
    [
        ("unshipped", "isn't shipped"),
        ("dirty_tree", "uncommitted or untracked"),
        ("main_off_main", "isn't on main"),
        ("main_dirty", "has uncommitted changes"),
        ("diverged", "can't fast-forward"),
    ],
)
def test_close_refuses_before_writing_anything(
    tmp_path: Path, capsys, monkeypatch, spoil: str, needle: str
) -> None:
    root = _repo(tmp_path)
    if spoil == "unshipped":
        assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 0
        tree = root / ".claude" / "worktrees" / "001-thing"
        _git(tree, "commit", "-q", "--allow-empty", "-m", "open")
    else:
        tree, _ = _shipped_change(root)
    if spoil == "dirty_tree":
        (tree / "stray.txt").write_text("x", encoding="utf-8")
    if spoil == "main_off_main":
        _git(root, "checkout", "-q", "-b", "elsewhere")
    if spoil == "main_dirty":
        (root / "README.md").write_text("edited\n", encoding="utf-8")
    if spoil == "diverged":
        _diverge(root, tree)
    main_before = _git(root, "rev-parse", "main")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 1 and any(needle in r for r in out["refusals"]), out
    assert out["done"] == []
    assert _git(root, "rev-parse", "main") == main_before and tree.is_dir()


def test_behind_trunk_counts_what_the_branch_lacks(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 0
    tree = root / ".claude" / "worktrees" / "001-thing"
    assert sdlc.behind_trunk(root, "001-thing", "main") == 0
    _diverge(root, tree)
    _git(root, "commit", "-q", "--allow-empty", "-m", "main moved again")
    assert sdlc.behind_trunk(root, "001-thing", "main") == 2
    assert sdlc.behind_trunk(root, "002-nothing", "main") is None
    assert sdlc.behind_trunk(root, "001-thing", None) is None


def test_status_marks_a_stale_base_and_check_ignores_it(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """Ship stops on the mark before the gate runs; close would refuse the branch anyway. A nudge,
    never a problem: `vet --strict` is a gate."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "open-one", 1, None, worktree=True) == 0
    _shipped_change(root, "shipped-one")
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "status"])
    capsys.readouterr()
    assert sdlc.main() == 0
    assert "behind main" not in capsys.readouterr().out

    _diverge(root, root)
    assert sdlc.main() == 0
    out = capsys.readouterr().out
    open_line = next(ln for ln in out.splitlines() if "open-one" in ln)
    assert "behind main by 1: /sdlc:ship brings it up to date" in open_line
    ready_line = next(ln for ln in out.splitlines() if "shipped-one" in ln and "/sdlc:close" in ln)
    assert "(behind main by 1: rebase and ship again)" in ready_line

    monkeypatch.setattr(sys, "argv", ["sdlc.py", "vet", "--strict"])
    sdlc.main()
    assert "behind main" not in capsys.readouterr().out


def _base(root: Path, ident, capsys) -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_base(root, ident)
    return code, json.loads(capsys.readouterr().out)


def _opened(root: Path) -> Path:
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 0
    return root / ".claude" / "worktrees" / "001-thing"


def _commit_on_main(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text, encoding="utf-8")
    _git(root, "add", path)
    _git(root, "commit", "-q", "-m", f"main changes {path}")


def test_base_is_current_when_main_hasnt_moved(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _base(tree, None, capsys)
    assert code == 0 and out["action"] == "current" and out["behind"] == 0
    assert _git(tree, "rev-parse", "HEAD") == head


def test_base_fast_forwards_and_carries_uncommitted_edits(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("our edit\n", encoding="utf-8")
    (tree / "new.txt").write_text("new\n", encoding="utf-8")
    _commit_on_main(root, "other.txt", "theirs\n")
    main_sha, main_status = _git(root, "rev-parse", "main"), _git(root, "status", "--porcelain")

    code, out = _base(tree, "001", capsys)
    assert code == 0 and out["action"] == "fast-forwarded" and out["behind"] == 1, out
    assert _git(tree, "rev-parse", "HEAD") == main_sha == out["to"]
    assert (tree / "README.md").read_text(encoding="utf-8") == "our edit\n"
    assert (tree / "new.txt").read_text(encoding="utf-8") == "new\n"
    assert (tree / "other.txt").read_text(encoding="utf-8") == "theirs\n"
    assert _git(root, "rev-parse", "main") == main_sha
    assert _git(root, "status", "--porcelain") == main_status
    assert _base(tree, "001", capsys)[1]["action"] == "current"


def test_base_refuses_when_main_touched_a_file_the_work_did(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("our edit\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "their edit\n")
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _base(tree, "001", capsys)
    assert code == 1 and out["action"] == "refused" and "README.md" in out["reason"], out
    assert _git(tree, "rev-parse", "HEAD") == head == out["to"]
    assert (tree / "README.md").read_text(encoding="utf-8") == "our edit\n"


def test_base_rebases_a_clean_branch_with_commits(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "ours.txt").write_text("ours\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours")
    _commit_on_main(root, "theirs.txt", "theirs\n")
    code, out = _base(tree, "001", capsys)
    assert code == 0 and out["action"] == "rebased", out
    assert _git(tree, "merge-base", "--is-ancestor", "main", "HEAD") == ""
    assert (tree / "ours.txt").is_file() and (tree / "theirs.txt").is_file()


def test_base_says_which_refusals_resolve_can_take_on(tmp_path: Path, capsys) -> None:
    """The three conflicts are `resolvable`, and their words are as before: the factory's landing
    reads `action` and `reason`."""
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("our edit\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "their edit\n")
    code, out = _base(tree, "001", capsys)
    assert (code, out["action"], out["resolvable"]) == (1, "refused", True), out
    assert out["reason"].startswith("main changed what this change's uncommitted work changes")

    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours")
    (tree / "more.txt").write_text("more\n", encoding="utf-8")
    code, out = _base(tree, "001", capsys)
    assert (code, out["resolvable"]) == (1, True) and "commit the work" in out["reason"], out

    (tree / "more.txt").unlink()
    code, out = _base(tree, "001", capsys)
    assert (code, out["resolvable"]) == (1, True), out
    assert "conflicts, so it was aborted" in out["reason"]
    assert _base(tree, "001", capsys)[1]["resolvable"] is True, "aborted, so it can be asked again"


def _resolve(root: Path, ident, capsys, mode: str = "start") -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_resolve(root, ident, mode)
    return code, json.loads(capsys.readouterr().out)


def _ref(tree: Path, kind: str, branch: str = "001-thing") -> str | None:
    return _git_or_none(tree, "rev-parse", "--verify", "-q", f"refs/sdlc/{kind}/{branch}")


def _git_or_none(root: Path, *args: str) -> str | None:
    return sdlc._git(root, *args)


def test_resolve_takes_uncommitted_work_over_a_file_main_changed(tmp_path: Path, capsys) -> None:
    """071's shape: no commits of its own, uncommitted work over a file main changed, and an
    untracked file beside it. The work ends uncommitted on main, merged, and named in
    conflicts.md; nothing is ever committed on the branch."""
    root = _repo(tmp_path)
    tree = _opened(root)
    start = _git(tree, "rev-parse", "HEAD")
    (tree / "README.md").write_text("our line\n", encoding="utf-8")
    (tree / "new.txt").write_text("new\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "their line\n")

    code, out = _resolve(tree, "001", capsys)
    assert (code, out["state"], out["conflicted"]) == (0, "conflict", ["README.md"]), out
    assert "--abort" in out["undo"] and _ref(tree, "aside") and _ref(tree, "start") == start
    code, out = _resolve(tree, "001", capsys, "continue")
    assert code == 1 and "conflict markers left in: README.md" in out["reason"], "not merged yet"

    (tree / "README.md").write_text("their line, and our line\n", encoding="utf-8")
    code, out = _resolve(tree, "001", capsys, "continue")
    assert (code, out["state"], out["resolved"]) == (0, "clean", ["README.md"]), out
    assert _git(tree, "rev-parse", "HEAD") == _git(root, "rev-parse", "main"), "nothing committed"
    status = _git(tree, "status", "--porcelain", "--untracked-files=all").splitlines()
    assert "M README.md" in status and "?? new.txt" in status, status
    record = (tree / ".sdlc" / "work" / "001-thing" / "conflicts.md").read_text(encoding="utf-8")
    assert "onto main" in record and "- README.md" in record
    assert _ref(tree, "aside") and _ref(tree, "end") and _ref(tree, "pending") is None
    assert _resolve(tree, "001", capsys)[1]["state"] == "current"
    capsys.readouterr()
    assert sdlc.cmd_ship_question(tree, "001", False, False, [], []) == 0
    asked = capsys.readouterr().out
    assert "with the conflicts in README.md resolved" in asked, "ship can't leave it out"


def test_resolve_takes_commits_of_its_own_one_stop_at_a_time(tmp_path: Path, capsys) -> None:
    """Two commits of its own, each conflicting with main: two stops, both named in the record;
    a branch with commits and nothing uncommitted keeps its commits."""
    root = _repo(tmp_path)
    tree = _opened(root)
    for name in ("a.txt", "b.txt"):
        (tree / name).write_text(f"ours {name}\n", encoding="utf-8")
        _git(tree, "add", "-A")
        _git(tree, "commit", "-q", "-m", f"ours {name}")
    _commit_on_main(root, "a.txt", "theirs a\n")
    _commit_on_main(root, "b.txt", "theirs b\n")

    code, out = _resolve(tree, "001", capsys)
    assert out["conflicted"] == ["a.txt"] and _ref(tree, "aside") is None, out
    (tree / "a.txt").write_text("both a\n", encoding="utf-8")
    code, out = _resolve(tree, "001", capsys, "continue")
    assert (out["state"], out["conflicted"]) == ("conflict", ["b.txt"]), out
    (tree / "b.txt").write_text("both b\n", encoding="utf-8")
    code, out = _resolve(tree, "001", capsys, "continue")
    assert (code, out["state"], out["resolved"]) == (0, "clean", ["a.txt", "b.txt"]), out
    log = _git(tree, "log", "--format=%s", "main..HEAD").splitlines()
    assert log == ["ours b.txt", "ours a.txt"], "its own commits, rebased"


def test_resolve_with_commits_and_uncommitted_work(tmp_path: Path, capsys) -> None:
    """What base can't take at all: commits of its own and uncommitted work. The work rides on a
    temporary commit through the rebase and comes back uncommitted."""
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "a.txt").write_text("ours\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours")
    (tree / "README.md").write_text("our readme\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "their readme\n")
    code, out = _resolve(tree, "001", capsys)
    assert out["conflicted"] == ["README.md"], out
    (tree / "README.md").write_text("their readme and ours\n", encoding="utf-8")
    code, out = _resolve(tree, "001", capsys, "continue")
    assert out["state"] == "clean", out
    assert _git(tree, "log", "--format=%s", "main..HEAD") == "ours", "the aside commit is gone"
    assert "M README.md" in _git(tree, "status", "--porcelain").splitlines()


def test_resolve_skips_a_commit_the_base_already_holds(tmp_path: Path, capsys) -> None:
    """Nit 2026-11-17-11: a conflict resolved to what the base holds leaves the branch's commit
    with nothing of its own, which git's apply backend refuses to continue past ("No changes").
    That commit is skipped; the next is kept, and the aside commit is still undone at the end."""
    root = _repo(tmp_path)
    tree = _opened(root)
    _git(tree, "config", "rebase.backend", "apply")
    for name in ("a.txt", "b.txt"):
        (tree / name).write_text(f"ours {name}\n", encoding="utf-8")
        _git(tree, "add", name)
        _git(tree, "commit", "-q", "-m", f"ours {name}")
    (tree / "README.md").write_text("our readme\n", encoding="utf-8")
    _commit_on_main(root, "a.txt", "theirs a\n")

    code, out = _resolve(tree, "001", capsys)
    assert out["conflicted"] == ["a.txt"] and _ref(tree, "aside"), out
    (tree / "a.txt").write_text("theirs a\n", encoding="utf-8")
    code, out = _resolve(tree, "001", capsys, "continue")
    assert (code, out["state"], out["resolved"]) == (0, "clean", ["a.txt"]), out
    log = _git(tree, "log", "--format=%s", "main..HEAD").splitlines()
    assert log == ["ours b.txt"], "the emptied commit skipped, the aside commit undone"
    status = _git(tree, "status", "--porcelain").splitlines()
    assert status == ["M README.md", "?? .sdlc/"], "the work, uncommitted again"


def test_resolve_abort_puts_everything_back(tmp_path: Path, capsys) -> None:
    """Mid-rebase or after it finished, abort leaves the worktree as resolve found it, and keeps
    the resolved work under refs/sdlc/end; once the branch moves on, it refuses."""
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("our line\n", encoding="utf-8")
    (tree / "new.txt").write_text("new\n", encoding="utf-8")
    _commit_on_main(root, "README.md", "their line\n")
    head = _git(tree, "rev-parse", "HEAD")
    status = _git(tree, "status", "--porcelain", "--untracked-files=all")

    _resolve(tree, "001", capsys)
    code, out = _resolve(tree, "001", capsys, "abort")
    assert (code, out["state"]) == (0, "aborted"), out
    assert _git(tree, "rev-parse", "HEAD") == head
    assert _git(tree, "status", "--porcelain", "--untracked-files=all") == status
    assert (tree / "README.md").read_text(encoding="utf-8") == "our line\n"

    _resolve(tree, "001", capsys)
    (tree / "README.md").write_text("both\n", encoding="utf-8")
    assert _resolve(tree, "001", capsys, "continue")[1]["state"] == "clean"
    code, out = _resolve(tree, "001", capsys, "abort")
    assert (code, out["state"]) == (0, "aborted"), out
    assert _git(tree, "rev-parse", "HEAD") == head
    assert _git(tree, "status", "--porcelain", "--untracked-files=all") == status
    assert not (tree / ".sdlc" / "work" / "001-thing" / "conflicts.md").exists()
    end = _ref(tree, "end")
    assert end and _git(tree, "show", f"{end}:README.md") == "both", "the resolved work is kept"

    _resolve(tree, "001", capsys)
    (tree / "README.md").write_text("both\n", encoding="utf-8")
    _resolve(tree, "001", capsys, "continue")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "shipped")
    code, out = _resolve(tree, "001", capsys, "abort")
    assert code == 1 and "moved since the resolution" in out["reason"], out


def test_resolve_settles_the_counter_and_keeps_an_earlier_record(tmp_path: Path, capsys) -> None:
    """`.sdlc/last-id` is the script's: the higher number, never listed. A change that resolved
    before, its conflicts.md committed, resolves again with the file untouched mid-rebase."""
    root = _repo(tmp_path)
    tree = _opened(root)
    folder = tree / ".sdlc" / "work" / "001-thing"
    (folder / "conflicts.md").write_text("# Conflicts\n\n## earlier\n\n- x\n", encoding="utf-8")
    (tree / "README.md").write_text("ours\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours, with an earlier record")
    (tree / ".sdlc" / "last-id").write_text("007\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "our counter")
    _commit_on_main(root, ".sdlc/last-id", "009\n")
    _commit_on_main(root, "README.md", "theirs\n")

    code, out = _resolve(tree, "001", capsys)
    assert out["conflicted"] == ["README.md"], out
    (tree / "README.md").write_text("both\n", encoding="utf-8")
    code, out = _resolve(tree, "001", capsys, "continue")
    assert (code, out["state"], out["resolved"]) == (0, "clean", ["README.md"]), out
    assert (tree / ".sdlc" / "last-id").read_text(encoding="utf-8") == "009\n"
    record = (folder / "conflicts.md").read_text(encoding="utf-8")
    assert "## earlier" in record and record.rstrip().endswith("- README.md")
    assert sdlc.conflicts_resolved(folder) == ["x", "README.md"]


def test_base_follows_a_trunk_that_isnt_main(tmp_path: Path, capsys) -> None:
    """Fast-forward with no commits of its own, rebase with some: both onto `git.base`."""
    root = _repo(tmp_path, "master")
    tree = _opened(root)
    _commit_on_main(root, "theirs.txt", "theirs\n")
    code, out = _base(tree, "001", capsys)
    assert code == 0 and out["action"] == "fast-forwarded" and out["behind"] == 1, out
    assert _git(tree, "rev-parse", "HEAD") == _git(root, "rev-parse", "master")
    (tree / "ours.txt").write_text("ours\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours")
    _commit_on_main(root, "more.txt", "more\n")
    code, out = _base(tree, "001", capsys)
    assert code == 0 and out["action"] == "rebased", out
    assert _git(tree, "merge-base", "--is-ancestor", "master", "HEAD") == ""


def test_status_context_and_nits_read_a_trunk_that_isnt_main(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path, "master")
    tree = _opened(root)
    (tree / "src").mkdir()
    (tree / "src" / "a.py").write_text("x\n", encoding="utf-8")
    _commit_on_main(root, "theirs.txt", "theirs\n")
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "status"])
    capsys.readouterr()
    sdlc.main()
    assert "behind master by 1" in capsys.readouterr().out
    code = sdlc.cmd_context(tree)
    assert code == 0 and json.loads(capsys.readouterr().out)["base"] == "master"
    assert sdlc.cmd_nits(tree, None, "001") == 0, capsys.readouterr().err


def test_base_refuses_without_a_base_branch(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[git]\nbase = "gone"\n', encoding="utf-8")
    head = _git(tree, "rev-parse", "HEAD")
    code, out = _base(tree, "001", capsys)
    assert code == 1 and "base branch 'gone' doesn't exist here" in out["reason"], out
    assert _git(tree, "rev-parse", "HEAD") == head


def test_base_aborts_a_conflicting_rebase(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("ours\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours")
    head = _git(tree, "rev-parse", "HEAD")
    _commit_on_main(root, "README.md", "theirs\n")
    code, out = _base(tree, "001", capsys)
    assert code == 1 and out["action"] == "refused" and "aborted" in out["reason"], out
    assert _git(tree, "rev-parse", "HEAD") == head
    assert _git(tree, "status", "--porcelain") == ""
    assert not Path(_git(tree, "rev-parse", "--git-path", "rebase-merge")).exists()


def test_base_refuses_commits_plus_uncommitted_work(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "ours")
    head = _git(tree, "rev-parse", "HEAD")
    (tree / "wip.txt").write_text("wip\n", encoding="utf-8")
    _commit_on_main(root, "theirs.txt", "theirs\n")
    code, out = _base(tree, "001", capsys)
    assert code == 1 and "commit the work" in out["reason"], out
    assert _git(tree, "rev-parse", "HEAD") == head and (tree / "wip.txt").is_file()


@pytest.mark.parametrize("theirs, kept", [("007\n", 7), ("000\n", 1)])
def test_base_keeps_the_higher_counter(tmp_path: Path, capsys, theirs: str, kept: int) -> None:
    """Under local numbering `new` leaves the counter untracked in the worktree; a change closed
    meanwhile committed main's. Neither number may go backwards."""
    root = _repo(tmp_path)
    tree = _opened(root)
    assert (tree / ".sdlc" / "last-id").read_text(encoding="utf-8") == "001\n"
    _commit_on_main(root, ".sdlc/last-id", theirs)
    code, out = _base(tree, "001", capsys)
    assert code == 0 and out["action"] == "fast-forwarded", out
    assert sdlc._read_number(tree / ".sdlc" / "last-id") == kept  # the worktree's, not main's


def test_base_puts_the_counter_back_when_it_refuses(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("our edit\n", encoding="utf-8")
    _commit_on_main(root, ".sdlc/last-id", "007\n")
    _commit_on_main(root, "README.md", "their edit\n")
    code, out = _base(tree, "001", capsys)
    assert code == 1 and out["action"] == "refused", out
    assert (tree / ".sdlc" / "last-id").read_text(encoding="utf-8") == "001\n"


def test_base_carries_a_factory_run_intact(tmp_path: Path, capsys) -> None:
    """The factory leaves everything uncommitted for ship: all of it survives the update."""
    root = _repo(tmp_path)
    tree = _opened(root)
    folder = tree / ".sdlc" / "work" / "001-thing"
    files = {
        folder / "decision.md": "DECISION: READY\n",
        folder / "decisions.md": "- [x] D1 (scope, default): kept small\n",
        folder / "reviews" / "round-1" / "code.md": "VERDICT: PASS\n",
        tree / "code.py": "print('built')\n",
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    before = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file()}
    _commit_on_main(root, "other.txt", "theirs\n")
    code, out = _base(tree, "001", capsys)
    assert code == 0 and out["action"] == "fast-forwarded", out
    assert {p: p.read_bytes() for p in folder.rglob("*") if p.is_file()} == before
    assert (tree / "code.py").read_text(encoding="utf-8") == "print('built')\n"


def test_base_undo_puts_the_branch_back(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = _opened(root)
    (tree / "README.md").write_text("our edit\n", encoding="utf-8")
    _commit_on_main(root, "other.txt", "theirs\n")
    code, out = _base(tree, "001", capsys)
    assert code == 0
    subprocess.run(out["undo"].split(), check=True, capture_output=True)
    assert _git(tree, "rev-parse", "HEAD") == out["from"]
    assert (tree / "README.md").read_text(encoding="utf-8") == "our edit\n"


def test_close_from_inside_the_worktree_merges_then_keeps_it(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """Never remove the directory the session stands in. The change lands; the removal
    waits for a run from the main checkout, which then finishes it."""
    root = _repo(tmp_path)
    tree, branch = _shipped_change(root)
    tip = _git(tree, "rev-parse", "HEAD")
    monkeypatch.chdir(tree)
    code, out = _close(tree, None, capsys)
    assert code == 3, out
    assert out["done"] == ["merge", "verify", "measure", "remove folder"]
    assert out["skipped"] == ["remove worktree", "delete branch"]
    assert _git(root, "rev-parse", "main~1") == tip and tree.is_dir()

    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert not tree.exists() and branch not in _git(root, "branch", "--list")
    assert _git(root, "rev-parse", "main~1") == tip, "the rerun made no second Close commit"


def test_check_after_the_last_close_still_audits_ideas(tmp_path: Path, capsys, monkeypatch) -> None:
    """With every folder gone from main, `vet` passes, and still flags an orphan seed."""
    root = _repo(tmp_path)
    _shipped_change(root)
    monkeypatch.chdir(root)
    assert _close(root, "001", capsys)[0] == 0
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "vet", "--strict"])
    assert sdlc.main() == 0
    (root / ".sdlc" / "work").mkdir(parents=True, exist_ok=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "## [2026-10-01-1] [building] Orphan\n", encoding="utf-8"
    )
    assert sdlc.main() == 1
    assert [p["kind"] for p in sdlc.analyze(root)["problems"]] == ["orphan idea"]


def test_ready_to_close_lists_a_shipped_worktree_until_it_lands(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    assert sdlc.ready_to_close(root) == []
    _shipped_change(root)
    assert [r["id"] for r in sdlc.ready_to_close(root)] == ["001"]
    monkeypatch.chdir(root)
    _close(root, "001", capsys)
    assert sdlc.ready_to_close(root) == []


def test_close_removes_a_worktree_holding_only_ignored_files(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """A real worktree has a .venv symlink, local settings and build output, all gitignored.
    `git worktree remove` without --force must still take it, and the precondition must not call
    it dirty."""
    root = _repo(tmp_path)
    (root / ".gitignore").write_text(
        ".claude/worktrees/\n.venv\nlocal.toml\nbuild/\n", encoding="utf-8"
    )
    _git(root, "add", ".gitignore")
    _git(root, "commit", "-q", "-m", "ignore")
    tree, branch = _shipped_change(root)
    (root / ".venv").mkdir()
    (tree / ".venv").symlink_to(root / ".venv")
    (tree / "local.toml").write_text("[env]\n", encoding="utf-8")
    (tree / "build").mkdir()
    (tree / "build" / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert not tree.exists() and branch not in _git(root, "branch", "--list")


# ---------------------------------------------------------------- context docs


def _context(root: Path, capsys, base: str = "main") -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_context(root, base)
    out = capsys.readouterr().out
    return code, (json.loads(out) if out else {})


def _with_docs(tmp_path: Path) -> Path:
    """A repo with a root CLAUDE.md, one above src/api/ and one above an untouched folder."""
    root = _repo(tmp_path)
    for rel, text in {
        "CLAUDE.md": "# ctx\nRun `make check`. The entry point is src/api/old.py.\n",
        "src/api/CLAUDE.md": "# api\nHandlers live in src/api/handlers.py.\n",
        "src/api/handlers.py": "x = 1\n",
        "src/api/old.py": "y = 1\n",
        "lib/CLAUDE.md": "# lib\n",
        "lib/util.py": "z = 1\n",
    }.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "docs")
    _git(root, "checkout", "-q", "-b", "001-change")
    return root


def test_context_lists_configured_docs_and_the_claude_md_above_a_changed_path(
    tmp_path: Path, capsys
) -> None:
    root = _with_docs(tmp_path)
    (root / "src" / "api" / "handlers.py").write_text("x = 2\n", encoding="utf-8")
    code, out = _context(root, capsys)
    assert code == 0, out
    assert {d["path"]: d["why"] for d in out["docs"]} == {
        "CLAUDE.md": "docs.context",
        "src/api/CLAUDE.md": "above src/api/handlers.py",
    }
    assert out["stale"] == []


def test_context_counts_untracked_files_as_changed(tmp_path: Path, capsys) -> None:
    root = _with_docs(tmp_path)
    (root / "lib" / "new.py").write_text("n = 1\n", encoding="utf-8")
    _, out = _context(root, capsys)
    assert "lib/CLAUDE.md" in {d["path"] for d in out["docs"]}


def test_context_finds_lines_naming_a_deleted_or_renamed_path(tmp_path: Path, capsys) -> None:
    root = _with_docs(tmp_path)
    _git(root, "mv", "src/api/old.py", "src/api/entry.py")
    _git(root, "rm", "-q", "src/api/handlers.py")
    _git(root, "commit", "-q", "-m", "move things")
    _, out = _context(root, capsys)
    found = {(s["doc"], s["path"], s["status"], s["to"]) for s in out["stale"]}
    assert found == {
        ("CLAUDE.md", "src/api/old.py", "renamed", "src/api/entry.py"),
        ("src/api/CLAUDE.md", "src/api/handlers.py", "deleted", None),
    }


def test_context_lists_an_agents_md_above_a_changed_path_alone_or_beside_a_claude_md(
    tmp_path: Path, capsys
) -> None:
    root = _with_docs(tmp_path)
    (root / "AGENTS.md").write_text(
        "# agents\nThe entry point is src/api/old.py.\n", encoding="utf-8"
    )
    (root / "lib" / "AGENTS.md").write_text("# lib agents\n", encoding="utf-8")
    (root / "src" / "api" / "CLAUDE.md").unlink()
    (root / "src" / "api" / "AGENTS.md").write_text(
        "# api\nSee src/api/handlers.py.\n", encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "agents")
    _git(root, "mv", "src/api/old.py", "src/api/entry.py")
    _git(root, "rm", "-q", "src/api/handlers.py")
    (root / "lib" / "util.py").write_text("z = 2\n", encoding="utf-8")
    _git(root, "commit", "-q", "-am", "move things")
    _, out = _context(root, capsys)
    listed = {d["path"]: d["why"] for d in out["docs"]}
    assert listed["AGENTS.md"] == "docs.context", "in the default docs.context"
    # The branch adds these too, so which changed path found each first is beside the point.
    assert set(listed) == {
        "CLAUDE.md",
        "AGENTS.md",
        "src/api/AGENTS.md",
        "lib/AGENTS.md",
        "lib/CLAUDE.md",
    }, "both files in lib/, the AGENTS.md alone in src/api/"
    found = {(s["doc"], s["path"], s["status"]) for s in out["stale"]}
    assert ("AGENTS.md", "src/api/old.py", "renamed") in found
    assert ("src/api/AGENTS.md", "src/api/handlers.py", "deleted") in found


def test_context_writes_nothing(tmp_path: Path, capsys) -> None:
    root = _with_docs(tmp_path)
    (root / "src" / "api" / "handlers.py").write_text("x = 2\n", encoding="utf-8")
    before = _git(root, "status", "--porcelain")
    _context(root, capsys)
    assert _git(root, "status", "--porcelain") == before


def test_context_refuses_without_the_base(tmp_path: Path, capsys) -> None:
    root = _with_docs(tmp_path)
    capsys.readouterr()
    assert sdlc.cmd_context(root, "no-such-branch") == 1
    assert "no merge base" in capsys.readouterr().err


# ---------------------------------------------------------------- open questions


def test_status_counts_open_questions_that_are_not_struck(tmp_path: Path, capsys) -> None:
    """The count /sdlc:status reads, once a shell loop over every intent. A struck bullet is a
    question closed; prose and prompts in the section are not questions."""
    body = (
        "---\nid: 001\nslug: x\ntier: 1\nstage: plan\ncreated: 2026-10-01\n"
        "updated: 2026-10-01\n---\n\n# 001 — x\n\n## Open questions\n\n"
        "- Which page loads slowly?\n- ~~Is it cached?~~ Resolved: no.\n- Who reads it?\n"
        "Some prose.\n\n## Approach\n\n- not a question\n"
    )
    _change(tmp_path, "001-x", body)
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert a["open"][0]["open_questions"] == 2
    sdlc.print_status(a)
    assert "2 open question(s)" in capsys.readouterr().out


# ---------------------------------------------------------------- trackers and the issue

TRACKERS = REPO / "scripts" / "trackers"


def _gh_calls(core: str) -> list[str]:
    # GitHub's closing keyword too: core writes the line the tracker hands it, never its own.
    return [needle for needle in ('"gh"', "_gh(", "github.com", "Closes #") if needle in core]


@pytest.mark.parametrize("script", CORE, ids=lambda p: p.name)
def test_core_never_calls_gh_itself(script: Path) -> None:
    """Every call to GitHub is the GitHub tracker's, so a host without it runs no GitHub code."""
    found = _gh_calls(script.read_text(encoding="utf-8"))
    assert not found, f"{found} belong in scripts/trackers/github.py"
    github = (TRACKERS / "github.py").read_text(encoding="utf-8")
    assert '"gh"' in github and "github.com" in github and "Closes #" in github


def _main_refs(source: str) -> list[str]:
    """Each string the code runs naming `main` as a ref, docstrings and `DEFAULT_TRUNK` aside."""
    import ast

    tree = ast.parse(source)
    docstrings, allowed = set(), set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        first = body[0] if isinstance(body, list) and body else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            docstrings.add(id(first.value))
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DEFAULT_TRUNK" for t in node.targets
        ):
            allowed.add(id(node.value))
    ref = re.compile(r"^main$|refs/heads/main\b|\.\.main\b|^main[:^~]")
    return [
        f"line {node.lineno}: {node.value!r}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings | allowed
        and ref.search(node.value)
    ]


@pytest.mark.parametrize("script", CORE, ids=lambda p: p.name)
def test_no_git_call_names_main_itself(script: Path) -> None:
    """Every use of the base branch reads `git.base` as resolved (018): a `main` written into a
    ref is a host on `master` stuck at that step. `DEFAULT_TRUNK`, which detection tries first,
    is the one name allowed."""
    found = _main_refs(script.read_text(encoding="utf-8"))
    assert not found, "read the base branch from git.base:\n  " + "\n  ".join(found)


def test_the_source_guards_reach_retro_py() -> None:
    """The guards above read `retro.py` too: one planted there is found, not passed over."""
    retro = CORE[1].read_text(encoding="utf-8")
    assert not _main_refs(retro) and not _gh_calls(retro)
    assert _main_refs(retro + '\nREF = "refs/heads/main"\n')
    assert _gh_calls(retro + '\nRUN = ["gh", "issue"]\n')


def test_the_source_guards_reach_closing_py() -> None:
    """153 R8: close moved out of `sdlc.py`; the guards above read `closing.py` too, so moving
    the code didn't move it out of their reach. The spec's other two plants sit beside the
    guards they test: a literal `work/` in `test_work_folder.py`'s
    `test_the_work_path_guard_reaches_closing_py`, and a second push in `test_skills.py`'s
    `test_the_push_guard_reaches_closing_py`."""
    closing = CORE[2].read_text(encoding="utf-8")
    assert CORE[2].name == "closing.py"
    assert not _main_refs(closing) and not _gh_calls(closing)
    assert _main_refs(closing + '\nREF = "refs/heads/main"\n')
    assert _gh_calls(closing + '\nRUN = ["gh", "issue"]\n')


def test_archive_targets_are_the_tracker_modules() -> None:
    """A module added to scripts/trackers/ is a target, with no edit to the config code."""
    stems = {p.stem for p in TRACKERS.glob("*.py") if not p.stem.startswith("_")}
    assert set(sdlc.ARCHIVE_TARGETS) == stems | {"none"}
    assert sdlc.ARCHIVE_TARGETS[0] == "github" and sdlc.ARCHIVE_TARGETS[-1] == "none"


def test_target_none_runs_a_change_without_loading_a_tracker(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[archive]\ntarget = "none"\n', encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "no tracker")
    sdlc._TRACKERS.clear()
    tree, branch = _shipped_change(root)
    capsys.readouterr()
    assert sdlc.cmd_sync(tree, None) == 0
    assert json.loads(capsys.readouterr().out)["nothing to sync"] == "archive.target is none"
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert sdlc._TRACKERS == {}, "no tracker module was loaded"


INTENT_FULL = _fm(tier=2, stage="design", depends_on='["003"]').replace(
    "Body text.\n", "## Problem\n\nIt broke.\n\n## Outcome\n\nIt works.\n"
)
SPEC = (
    "---\nid: 001\nkind: spec\n---\n\n# 001 — x · spec\n\n## Requirements\n\n1. R1.\n\n"
    "### Detail\n\n```sh\n# not a heading\n```\n"
)


def _render(tmp_path: Path, extra: dict[str, str]):
    folder = _change(tmp_path, "001-x", INTENT_FULL, extra)
    rec = sdlc.load_change(folder, tmp_path)
    return sdlc.render_issue(tmp_path, folder, rec, "001-x", "abc1234")


def test_the_issue_reads_top_down_from_its_template(tmp_path: Path) -> None:
    marker, body, comments = _render(tmp_path, {"spec.md": SPEC})
    assert marker == "<!-- sdlc:001-x -->" and body.startswith(marker + "\n")
    assert "| 2 | design | — | `001-x` | `abc1234` | 003 |" in body
    assert body.index("It broke.") < body.index("<details>"), "Problem comes before the artifacts"
    assert "<summary><b>intent.md</b> — Problem · Outcome</summary>" in body
    assert "<summary><b>spec.md</b> — Requirements</summary>" in body
    assert "id: 001" not in body and "```yaml" not in body, "frontmatter is in the table"
    assert "# 001 — x · spec" not in body, "the title is the issue's own"
    assert "#### Requirements" in body and "##### Detail" in body
    assert "```sh\n# not a heading\n```" in body, "a fenced # is left alone"
    assert "{{" not in body and comments == []


def test_the_default_issue_template_uses_only_known_placeholders() -> None:
    text = (sdlc.TEMPLATE_DIR / "issue.md").read_text(encoding="utf-8")
    found = set(re.findall(r"\{\{(\w+)\}\}", text))
    assert found and found <= set(sdlc.ISSUE_FIELDS)


def test_artifacts_that_dont_fit_become_comments_in_order(tmp_path: Path) -> None:
    extra = {"spec.md": "s" * 40_000, "plan.md": "p" * 40_000, "notes.md": "n" * 100}
    _, body, comments = _render(tmp_path, extra)
    assert len(body) <= sdlc.ISSUE_LIMIT and "<b>spec.md</b>" in body
    assert "posted as comments at close: `plan.md`, `notes.md`" in body
    firsts = [c.split("\n", 1)[0] for c in comments]
    assert firsts == ["<!-- sdlc:001-x:plan.md -->", "<!-- sdlc:001-x:notes.md -->"]


def test_an_artifact_too_long_for_any_part_is_refused(tmp_path: Path) -> None:
    assert "over GitHub's" in _render(tmp_path, {"spec.md": "s" * 70_000})


def test_depends_on_is_read_as_written_not_as_yaml_octal(tmp_path: Path) -> None:
    """YAML 1.1 reads `012` as 10 and `010` as 8: a padded id would point at the wrong change."""
    _change(tmp_path, "001-x", _fm(depends_on="[003, 012, 010]"))
    [rec] = sdlc.analyze(tmp_path, today=date(2026, 10, 17))["open"]
    assert rec["depends_on"] == [3, 12, 10]


@pytest.mark.parametrize("line", ["[003, 012]", "\n  - 003\n  - 012"])
def test_reworks_is_read_as_written_inline_or_as_a_block(line: str, tmp_path: Path) -> None:
    """R1: the earlier changes a change fixes, kept as written (`012` never becomes 10)."""
    _change(tmp_path, "020-x", _fm(id="020", reworks=line))
    [rec] = sdlc.analyze(tmp_path, today=date(2026, 10, 17))["open"]
    assert rec["reworks"] == ["003", "012"]


def test_check_reports_a_rework_that_isnt_a_change_id(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm(reworks="[abc, 001]"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    details = " ".join(pr["detail"] for pr in a["problems"])
    assert "reworks: 'abc' isn't a change id" in details
    assert "reworks names this change itself" in details


def test_stamp_shipped_leaves_a_reworks_line_as_written() -> None:
    """R10: ship stamps lines in place, so the ids an intent declares reach history untouched."""
    text = INTENT.replace("idea:\n", "idea:\nreworks: [003, 012]\n", 1)
    out, _ = sdlc.stamp_shipped(text, "2026-10-17")
    assert "\nreworks: [003, 012]\n" in out


def test_check_reports_a_dependency_that_isnt_a_change(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm(depends_on="[abc, 001]"))
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    details = " ".join(pr["detail"] for pr in a["problems"])
    assert "'abc' isn't a change id" in details and "names this change itself" in details


# ---------------------------------------------------------------- the project doc


def _fm_text(lines: str) -> str:
    return f"---\n{lines}\n---\n\nbody\n"


@pytest.mark.parametrize(
    ("line", "values"),
    [
        ('milestone: "Q4 2026"', ["Q4 2026"]),
        ("milestone: Q4 2026  # the quarter", ["Q4 2026"]),
        ("project: [1.10, 2.0]", ["1.10", "2.0"]),
        ('project: [Roadmap, "Ops, west"]', ["Roadmap", "Ops, west"]),
        ("assignees:\n  - ana\n  - 'bo'", ["ana", "bo"]),
        ("assignees:", []),
        ("project: []", []),
    ],
)
def test_frontmatter_values_are_read_as_written(line: str, values: list[str]) -> None:
    assert sdlc.frontmatter_list(_fm_text(f"id: 001\n{line}\nidea:"), line.split(":")[0]) == values


def test_a_key_left_out_reads_as_none() -> None:
    assert sdlc.frontmatter_list(_fm_text("id: 001"), "milestone") is None


def _project(root: Path, text: str) -> tuple[dict, list[str]]:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "PROJECT.md").write_text(text, encoding="utf-8")
    return sdlc.project_doc(root, sdlc.load_config(root)[0])


def test_the_project_doc_names_each_field_and_its_lookup(tmp_path: Path) -> None:
    fields, warnings = _project(
        tmp_path,
        _fm_text('milestone: tracker\nproject: [1.10, "Q4 2026"]\nassignees: ./team.sh {field}'),
    )
    assert fields == {
        "milestone": {"lookup": "tracker"},
        "project": {"lookup": "list", "values": ["1.10", "Q4 2026"]},
        "assignees": {"lookup": "command", "command": "./team.sh {field}"},
    }
    assert warnings == []


def test_an_unknown_field_is_warned_about_and_a_blank_one_is_off(tmp_path: Path) -> None:
    fields, warnings = _project(tmp_path, _fm_text("milestone:\nsprint: tracker\n# project: x"))
    assert fields == {} and len(warnings) == 1 and "'sprint'" in warnings[0]


def test_with_no_project_doc_config_has_no_fields_and_no_warning(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    capsys.readouterr()
    assert sdlc.cmd_config(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["docs"]["project"]["exists"] is False and out["docs"]["project"]["fields"] == {}
    assert not [w for w in out["warnings"] if "project" in w]


def test_the_health_doc_defaults_to_sdlc_and_is_off_while_absent(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    capsys.readouterr()
    sdlc.cmd_config(root)
    out = json.loads(capsys.readouterr().out)
    assert out["docs"]["health"] == {
        "path": ".sdlc/HEALTH.md", "exists": False, "source": "host",
    }  # fmt: skip
    assert not [w for w in out["warnings"] if "health" in w], "off, not missing"


def _health_config(root: Path, toml: str, capsys) -> dict:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(f"[docs]\n{toml}", "utf-8")
    (root / "docs").mkdir(exist_ok=True)
    for name in ("mine.md", "theirs.md"):
        (root / "docs" / name).write_text("# Health\n", "utf-8")
    capsys.readouterr()
    sdlc.cmd_config(root)
    return json.loads(capsys.readouterr().out)


def _lookup(root: Path, capsys, *names: str) -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_lookup(root, list(names))
    return code, json.loads(capsys.readouterr().out)


def test_lookup_echoes_a_list_and_runs_a_command(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[archive]\ntarget = "none"\n', encoding="utf-8")
    _project(
        root,
        _fm_text(
            "milestone: printf '1.10\\n\\nQ4 {field}\\n'\nproject: [Roadmap]\nassignees: tracker"
        ),
    )
    code, out = _lookup(root, capsys)
    assert code == 0
    assert out["fields"]["milestone"]["values"] == ["1.10", "Q4 milestone"]
    assert out["fields"]["project"]["values"] == ["Roadmap"]
    assert out["fields"]["assignees"]["values"] == []
    assert "no tracker" in out["fields"]["assignees"]["error"]


def test_a_failing_lookup_command_is_that_fields_error(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _project(root, _fm_text("milestone: echo nope >&2; exit 3"))
    code, out = _lookup(root, capsys, "milestone", "sprint")
    assert code == 1, "a field that doesn't exist is the caller's mistake"
    row = out["fields"]["milestone"]
    assert row["values"] == [] and "exited 3: nope" in row["error"]


def test_check_reports_fields_the_doc_doesnt_allow(tmp_path: Path) -> None:
    _project(tmp_path, _fm_text("milestone: [1.10]\nproject: [Roadmap]"))
    _change(tmp_path, "001-x", _fm(milestone="[1.10, 2.0]", project="Ops", assignees="ana"))
    details = [p["detail"] for p in sdlc.analyze(tmp_path, today=date(2026, 10, 17))["problems"]]
    assert any("milestone: one value, got 2" in d for d in details), details
    assert any("milestone: '2.0' isn't one the project doc lists" in d for d in details)
    assert any("project: 'Ops' isn't one" in d for d in details)
    assert any("assignees: set, but the project doc doesn't turn it on" in d for d in details)


def test_stamp_shipped_leaves_a_block_list_as_written() -> None:
    text = INTENT.replace("idea:\n", "idea:\nassignees:\n  - ana\n  - 'bo'\n")
    out, unplaced = sdlc.stamp_shipped(text, "2026-10-17")
    assert unplaced == []
    assert "assignees:\n  - ana\n  - 'bo'\n" in out
    assert (
        out.replace("stage: shipped", "stage: build").replace(
            "updated: 2026-10-17\nshipped: 2026-10-17", "updated: 2026-10-05"
        )
        == text
    )


# ---------------------------------------------------------------- the product doc and serves:

PRODUCT = """\
# Product

## Outcomes

- O1. **Unaided setup.** A new user finishes setup unaided
- ~~O2. Drafts sync across devices~~ Dropped: nobody asked for it
"""


def _product(root: Path, text: str = PRODUCT) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "PRODUCT.md").write_text(text, encoding="utf-8")


def _details(root: Path) -> list[str]:
    return [p["detail"] for p in sdlc.analyze(root, today=date(2026, 10, 17))["problems"]]


def test_with_no_product_doc_check_and_config_are_unchanged(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _change(root, "001-x", _fm())
    assert _details(root) == []
    capsys.readouterr()
    assert sdlc.cmd_config(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["docs"]["product"] == {
        "path": ".sdlc/PRODUCT.md", "exists": False, "source": "host", "outcomes": [],
    }  # fmt: skip
    assert not [w for w in out["warnings"] if "product" in w or "evidence" in w]


def test_config_offers_only_the_open_outcomes(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _product(root)
    capsys.readouterr()
    sdlc.cmd_config(root)
    out = json.loads(capsys.readouterr().out)
    assert out["docs"]["product"]["outcomes"] == [
        {"id": "O1", "name": "Unaided setup", "title": "A new user finishes setup unaided"}
    ]


def test_an_open_outcome_needs_a_short_name_and_a_struck_one_does_not() -> None:
    """The skills show the name beside the id; without one a person sees only `O1`."""
    out = sdlc.product_items("- O1. A new user finishes setup\n- ~~O2. Exports~~ Done: 001\n")
    assert out["problems"] == ["O1 has no short name: write `- O1. **<name>.** …`"]
    assert [i["id"] for i in out["items"]] == ["O1", "O2"], "reported, never skipped or raised"
    named = sdlc.product_items("- O1. **First change** A new user finishes setup\n")
    assert named["problems"] == [] and named["items"][0]["name"] == "First change"
    assert named["items"][0]["title"] == "A new user finishes setup"


def test_evidence_without_a_product_doc_is_warned(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[retro]\nevidence = ["echo 3"]\n', "utf-8")
    capsys.readouterr()
    sdlc.cmd_config(root)
    warnings = json.loads(capsys.readouterr().out)["warnings"]
    assert any("retro.evidence is set, but it runs only with a product doc" in w for w in warnings)


def test_evidence_must_be_a_list_of_commands(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "config.toml").write_text('[retro]\nevidence = "echo"\n', "utf-8")
    _, warnings, _ = sdlc.load_config(tmp_path)
    assert "retro.evidence must be a list of commands" in warnings


def test_test_times_must_be_a_list_of_commands(tmp_path: Path) -> None:
    """130 R1: `retro.test_times` is checked as `evidence` is: a string is a warning, never a
    crash, and a list of commands is read."""
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    config = tmp_path / ".sdlc" / "config.toml"
    config.write_text('[retro]\ntest_times = "cat junit.xml"\n', "utf-8")
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert "retro.test_times must be a list of commands" in warnings
    assert cfg["retro"]["test_times"] == []
    config.write_text('[retro]\ntest_times = ["cat junit.xml"]\n', "utf-8")
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert (cfg["retro"]["test_times"], warnings) == (["cat junit.xml"], [])


@pytest.mark.parametrize(
    ("serves", "stage", "error"),
    [
        (None, "plan", "serves: missing"),
        (None, "dropped", None),
        ("[]", "plan", "serves: empty"),
        ("[O9]", "plan", "serves: 'O9' isn't an outcome in the product doc"),
        ("[none, O1]", "plan", "serves: none can't be mixed with outcomes"),
        ("none", "plan", None),
        ("[O1]", "plan", None),
        ("O2", "plan", None),  # struck: retro's `stale`, not check's
    ],
)
def test_with_a_product_doc_every_open_change_says_what_it_serves(
    tmp_path: Path, serves: str | None, stage: str, error: str | None
) -> None:
    _product(tmp_path)
    kw = {"stage": stage} | ({"serves": serves} if serves is not None else {})
    _change(tmp_path, "001-x", _fm(**kw))
    serving = [d for d in _details(tmp_path) if d.startswith("serves:")]
    assert len(serving) == (0 if error is None else 1), serving
    if error:
        assert error in serving[0]


def test_a_change_owes_serves_only_once_its_own_branch_has_the_product_doc(tmp_path: Path) -> None:
    """A product doc landing on one branch mustn't fail `vet` for changes on others, which have
    never seen it: each is checked against the doc its own checkout holds."""
    root = _repo(tmp_path)
    tree = tmp_path / "002-other"
    subprocess.run(["git", "-C", str(root), "worktree", "add", "-q", "-b", "002-other", str(tree)],
                   check=True, capture_output=True)  # fmt: skip
    _change(tree, "002-other", _fm(id="002", slug="other"))
    _product(root)
    _change(root, "001-x", _fm())
    details = _details(root)
    assert any(d.startswith("serves: missing") for d in details), details
    assert len([d for d in details if d.startswith("serves:")]) == 1, "002 is on its own branch"


def test_serves_with_no_product_doc_is_an_error(tmp_path: Path) -> None:
    _change(tmp_path, "001-x", _fm(serves="[O1]"))
    assert "serves: set, but there is no product doc" in _details(tmp_path)


def test_serves_is_read_as_text(tmp_path: Path) -> None:
    _product(tmp_path)
    folder = _change(tmp_path, "001-x", _fm(serves="[O01, none]"))
    assert sdlc.load_change(folder, tmp_path)["serves"] == ["O01", "none"]


# ---------------------------------------------------------------- what close does to the register

IDEAS = (
    "# Ideas\n\n> Seeds, not a backlog.\n\n"
    "## [2026-10-01-1] [seed] Keep drafts\n\nThe first.\n\n"
    "## [2026-10-02-1] [building] Reopen drafts\n\nThe one being built.\nTwo lines.\n\n"
    "## [2026-10-03-1] [seed] Share drafts\n\nThe last.\n"
)


def _seeded(tmp_path: Path, idea: str, ideas: str = IDEAS) -> tuple[Path, Path]:
    """A change in a real repo, ready to ship, whose `idea:` is `idea`, beside `ideas`, which the
    repo has committed."""
    root = _repo(tmp_path)
    register = root / ".sdlc" / "work" / "inbox.md"
    register.parent.mkdir(parents=True, exist_ok=True)
    register.write_text(ideas, encoding="utf-8")
    _git(root, "add", "--", ".sdlc/work/inbox.md")
    _git(root, "commit", "-q", "-m", "a register")
    d = _change(root, "001-reopen-drafts", _fm(stage="build", impact="patch", idea=idea))
    return root, d


def _planned(idea: str, ideas: str = IDEAS, held: str = "", fixes: str = "") -> dict:
    """What close would make of `ideas` for a change whose `idea:` is `idea`, holding `held`."""
    intent = _fm(stage="shipped", idea=idea, **({"fixes": fixes} if fixes else {}))
    return sdlc.closing.register_plan(ideas, intent, sdlc.held_entries(held))


def _staged(root: Path) -> list[str]:
    return sorted(_git(root, "diff", "--cached", "--name-only").splitlines())


@pytest.mark.parametrize(
    "idea",
    [
        "Reopen drafts",
        '"## [2026-10-02] [seed] Reopen drafts"',
        '"[2026-10-02] [seed] Reopen drafts"',
        "Reopen drafts → work/001-reopen-drafts/",
    ],
)
def test_close_retires_the_seed_its_idea_names_and_nothing_else(idea) -> None:
    plan = _planned(idea)
    assert plan["refusals"] == [] and len(plan["retire"]) == 1 and plan["gone"] == []
    assert plan["text"] == (
        "# Ideas\n\n> Seeds, not a backlog.\n\n"
        "## [2026-10-01-1] [seed] Keep drafts\n\nThe first.\n\n"
        "## [2026-10-03-1] [seed] Share drafts\n\nThe last.\n"
    )


@pytest.mark.parametrize("tag", ["idea", "seed"])
def test_close_retires_an_idea_or_an_older_seed_by_its_id(tag: str) -> None:
    ideas = (
        f"# Inbox\n\n## [2026-10-02-1] [{tag}] Reopen drafts\n\nThe one.\n\n"
        "## [2026-10-03-1] [idea] Share drafts\n\nThe last.\n"
    )
    assert _planned("2026-10-02-1", ideas)["text"] == (
        "# Inbox\n\n## [2026-10-03-1] [idea] Share drafts\n\nThe last.\n"
    )


def test_close_matches_a_heading_that_carries_a_pointer() -> None:
    ideas = IDEAS.replace("Reopen drafts\n", "Reopen drafts → work/001-reopen-drafts/\n")
    assert "Reopen drafts" not in _planned("Reopen drafts", ideas)["text"]


def test_an_idea_without_the_heading_marker_finds_a_heading_with_a_pointer() -> None:
    ideas = IDEAS.replace("Reopen drafts\n", "Reopen drafts → work/001-reopen-drafts/\n")
    assert _planned('"[2026-10-02] [seed] Reopen drafts"', ideas)["text"] == (
        "# Ideas\n\n> Seeds, not a backlog.\n\n"
        "## [2026-10-01-1] [seed] Keep drafts\n\nThe first.\n\n"
        "## [2026-10-03-1] [seed] Share drafts\n\nThe last.\n"
    )


def test_a_title_holding_an_arrow_is_kept_whole() -> None:
    ideas = IDEAS.replace("[seed] Keep drafts", "[seed] Map intent").replace(
        "Reopen drafts\n", "Map intent → spec\n"
    )
    text = _planned("Map intent → spec", ideas)["text"]
    assert "Map intent → spec" not in text and "## [2026-10-01-1] [seed] Map intent\n" in text


def test_a_body_line_shaped_like_a_heading_is_never_a_seed() -> None:
    ideas = IDEAS.replace("The first.", "[2026-10-02] [seed] Reopen drafts, as said.").replace(
        "[building] Reopen drafts", "[building] Rename drafts"
    )
    assert _planned("Reopen drafts", ideas)["text"] == ideas


def test_close_retires_the_last_seed_without_a_trailing_blank_line() -> None:
    text = _planned("Share drafts")["text"]
    assert text.endswith("Two lines.\n") and "Share drafts" not in text


@pytest.mark.parametrize(
    "line, ideas",
    [
        ("2026-10-02-1", ["2026-10-02-1"]),
        ('"Reopen drafts"', ["Reopen drafts"]),
        ("[2026-10-01-1, 2026-10-03-1]", ["2026-10-01-1", "2026-10-03-1"]),
        ("\n  - 2026-10-01-1\n  - 2026-10-03-1", ["2026-10-01-1", "2026-10-03-1"]),
        ("", []),
    ],
)
def test_idea_names_one_seed_or_a_theme_s_several(tmp_path: Path, line: str, ideas) -> None:
    """R4: `idea:` is read as text, one id or title as before, or a list; `idea` is the first."""
    folder = _change(tmp_path, "001-x", _fm(idea=line))
    rec = sdlc.load_change(folder, tmp_path)
    assert rec["ideas"] == ideas and rec["idea"] == (ideas or [""])[0]


def test_close_retires_every_seed_a_theme_s_change_took() -> None:
    """R5: a change that took two seeds removes both; the one between them stays."""
    plan = _planned("[2026-10-01-1, 2026-10-03-1]")
    assert plan["text"] == (
        "# Ideas\n\n> Seeds, not a backlog.\n\n"
        "## [2026-10-02-1] [building] Reopen drafts\n\nThe one being built.\nTwo lines.\n"
    )
    assert plan["retire"] == ["2026-10-01-1", "2026-10-03-1"]


def test_an_ambiguous_second_seed_refuses_before_any_write(tmp_path: Path, capsys) -> None:
    """R5: every seed is found before any is deleted, so the first isn't lost to the second's
    refusal; ship refuses on it, and so would close."""
    ideas = IDEAS + "\n## [2026-10-04-1] [seed] Share drafts\n\nA twin.\n"
    assert _planned('[2026-10-01-1, "Share drafts"]', ideas)["refusals"]
    root, d = _seeded(tmp_path, '[2026-10-01-1, "Share drafts"]', ideas)
    assert sdlc.cmd_ship(root, "001") == 1
    assert "2 entries named 'Share drafts'" in capsys.readouterr().err
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == ideas


def test_two_seeds_with_the_idea_s_title_refuse_before_any_write(tmp_path: Path, capsys) -> None:
    ideas = IDEAS + "\n## [2026-10-04-1] [seed] Reopen drafts\n\nA twin.\n"
    root, d = _seeded(tmp_path, "Reopen drafts", ideas)
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(root, "001") == 1
    err = capsys.readouterr().err
    assert "2 entries named 'Reopen drafts'" in err and "lines 9, 18" in err
    assert (d / "intent.md").read_text(encoding="utf-8") == before
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == ideas
    assert _staged(root) == []


@pytest.mark.parametrize("ideas", [None, IDEAS.replace("Reopen", "Rename")])
def test_close_with_no_seed_to_remove_says_so(ideas) -> None:
    plan = _planned("Reopen drafts", ideas or "")
    assert plan["refusals"] == [] and plan["gone"] == ["Reopen drafts"]
    assert plan["text"] == (ideas or "")


def test_ship_leaves_the_seed_for_close_and_says_so(tmp_path: Path, capsys) -> None:
    """R1: ship deletes nothing from the register; it says what close will retire, and a rerun
    after a refused commit is harmless."""
    root, d = _seeded(tmp_path, "Reopen drafts")
    assert sdlc.cmd_ship(root, "001") == 0
    assert "close retires seed 'Reopen drafts'" in capsys.readouterr().out
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == IDEAS
    assert ".sdlc/work/inbox.md" not in _staged(root)
    assert sdlc.cmd_ship(root, "001") == 0, "a rerun after a refused commit"
    assert "stage: shipped" in (d / "intent.md").read_text(encoding="utf-8")


def test_ship_with_no_idea_mentions_no_seed(tmp_path: Path, capsys) -> None:
    root, _ = _seeded(tmp_path, "")
    assert sdlc.cmd_ship(root, "001") == 0
    out = capsys.readouterr().out
    assert (
        "seed" not in out
        and (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == IDEAS
    )


# ---------------------------------------------------------------- a change's held entries

HELD = (
    "# 001-reopen-drafts — entries\n\n"
    "Retire 2026-10-01-1: taken in by 001-reopen-drafts\n\n"
    "## [2026-10-09-1] [idea] Page the drafts\n\nLeft undone.\n\n"
    "## [2026-10-09-2] [nit] Terse wording\n\nSay more.\n\n```\n## not a heading\n```\n"
)


def test_held_entries_read_their_retirements_and_their_entries() -> None:
    held = sdlc.held_entries(HELD)
    assert held["problems"] == []
    assert held["retire"] == [("2026-10-01-1", "taken in by 001-reopen-drafts")]
    assert held["ids"] == ["2026-10-09-1", "2026-10-09-2"]
    assert held["chunks"]["2026-10-09-2"].endswith("```\n## not a heading\n```\n")


@pytest.mark.parametrize(
    "text, said",
    [
        ("# t\n\nstray words\n", "line 3"),
        ("# t\n\nRetire soon: why\n", "line 3"),
        ("# t\n\n## Not an entry\n", "line 3"),
        ("# t\n\n## [2026-10-09-1] [idea] A\n\n## [2026-10-09-1] [idea] B\n", "twice"),
    ],
)
def test_a_held_file_that_cant_be_read_says_where(text: str, said: str) -> None:
    problems = sdlc.held_entries(text)["problems"]
    assert problems and said in problems[0], problems


def test_close_files_each_held_entry_and_retires_each_named_nit() -> None:
    ideas = IDEAS.replace("[seed] Keep drafts", "[nit] Keep drafts")
    plan = _planned("2026-10-02-1", ideas, HELD)
    assert plan["refusals"] == []
    assert plan["file"] == ["2026-10-09-1", "2026-10-09-2"]
    assert plan["retire"] == ["2026-10-02-1", "2026-10-01-1"]
    assert plan["text"] == (
        "# Ideas\n\n> Seeds, not a backlog.\n\n"
        "## [2026-10-03-1] [seed] Share drafts\n\nThe last.\n\n"
        "## [2026-10-09-1] [idea] Page the drafts\n\nLeft undone.\n\n"
        "## [2026-10-09-2] [nit] Terse wording\n\nSay more.\n\n```\n## not a heading\n```\n"
    )


def test_close_skips_what_the_base_holds_word_for_word_and_refuses_what_it_holds_otherwise():
    """R6: a rerun's state is skipped; the same id with other text is refused."""
    done = _planned("", _planned("", IDEAS, HELD)["text"], HELD)
    assert done["refusals"] == [] and done["file"] == []
    assert done["skipped"] == ["2026-10-09-1", "2026-10-09-2"]
    assert done["gone"] == ["2026-10-01-1"], "a retirement already done is reported, not refused"
    other = IDEAS + "\n## [2026-10-09-1] [idea] Someone else's\n\nx\n"
    refused = _planned("", other, HELD)["refusals"]
    assert refused and "2026-10-09-1" in refused[0]


def test_close_retires_each_bug_the_change_fixes_and_says_which_are_gone() -> None:
    ideas = IDEAS.replace("[seed] Share drafts", "[bug] Share drafts")
    plan = _planned("", ideas, fixes="[2026-10-03-1, 2026-10-01-9]")
    assert plan["retire"] == ["2026-10-03-1"] and plan["gone"] == ["2026-10-01-9"]
    assert plan["text"].endswith("Two lines.\n")


def test_ship_stages_the_change_and_leaves_what_it_is_told_to(tmp_path: Path, capsys) -> None:
    root, _ = _seeded(tmp_path, "Reopen drafts")
    (root / "drafts.py").write_text("x = 1\n", encoding="utf-8")
    (root / "with space.txt").write_text("x\n", encoding="utf-8")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "last-id").write_text("1\n", encoding="utf-8")
    (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
    head = _git(root, "rev-parse", "HEAD")
    assert sdlc.cmd_ship(root, "001", ["unrelated.txt"]) == 0
    assert _staged(root) == [
        ".sdlc/last-id", ".sdlc/work/001-reopen-drafts/intent.md", "drafts.py",
        "with space.txt",
    ]  # fmt: skip
    assert "  staged with space.txt" in capsys.readouterr().out
    assert _git(root, "rev-parse", "HEAD") == head, "ship never commits"


def test_ship_stages_beside_a_deletion_already_staged(tmp_path: Path, capsys) -> None:
    root, _ = _seeded(tmp_path, "Reopen drafts")
    for name in ("gone.txt", "half.txt"):
        (root / name).write_text("x\n", encoding="utf-8")
    _git(root, "add", "gone.txt", "half.txt")
    _git(root, "commit", "-q", "-m", "two files")
    _git(root, "rm", "-q", "gone.txt")
    (root / "half.txt").write_text("y\n", encoding="utf-8")
    _git(root, "add", "half.txt")
    (root / "half.txt").write_text("z\n", encoding="utf-8")
    (root / "drafts.py").write_text("x = 1\n", encoding="utf-8")
    assert sdlc.cmd_ship(root, "001") == 0
    assert _staged(root) == [
        ".sdlc/work/001-reopen-drafts/intent.md", "drafts.py", "gone.txt", "half.txt",
    ]  # fmt: skip
    assert _git(root, "diff", "--name-only") == "", "the later edit is staged too"
    assert "  staged gone.txt" in capsys.readouterr().out


@pytest.mark.parametrize("left", ["./unrelated.txt", "unrelatd.txt"])
def test_a_left_path_that_matches_nothing_refuses_before_any_write(
    tmp_path: Path, capsys, left
) -> None:
    root, d = _seeded(tmp_path, "Reopen drafts")
    (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(root, "001", [left]) == 1
    assert f"--leave {left}: not a path the checkout has uncommitted" in capsys.readouterr().err
    assert (d / "intent.md").read_text(encoding="utf-8") == before
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == IDEAS
    assert _staged(root) == []


def test_a_left_path_already_staged_refuses_before_any_write(tmp_path: Path, capsys) -> None:
    root, d = _seeded(tmp_path, "Reopen drafts")
    (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "unrelated.txt")
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(root, "001", ["unrelated.txt"]) == 1
    assert "already staged" in capsys.readouterr().err
    assert (d / "intent.md").read_text(encoding="utf-8") == before
    assert (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == IDEAS


# 093: whether the factory is enabled, from Claude Code's own settings files and nothing else.
def _settings(where: Path, name: str, text: str) -> None:
    (where / ".claude").mkdir(parents=True, exist_ok=True)
    (where / ".claude" / name).write_text(text, encoding="utf-8", newline="\n")


def _plugins(**enabled: bool) -> str:
    return json.dumps(
        {"enabledPlugins": {k.replace("_", "-") + "@sdlc": v for k, v in enabled.items()}}
    )


def _user_home(tmp_path: Path, monkeypatch) -> Path:
    user = tmp_path / "user"
    user.mkdir()
    monkeypatch.setenv("HOME", str(user))
    monkeypatch.setenv("USERPROFILE", str(user))
    return user


@pytest.mark.portable
def test_config_reports_the_factory_by_scope(tmp_path: Path, monkeypatch, capsys) -> None:
    """R1: each of the three files names the factory on its own, and the most specific decides,
    so a person who turns it off for one repo isn't offered it there."""
    user = _user_home(tmp_path, monkeypatch)
    for name, scope in (
        ("settings.local.json", "local"),
        ("settings.json", "project"),
        (None, "user"),
    ):
        home = tmp_path / f"repo-{scope}"
        home.mkdir()
        _settings(
            user if name is None else home, name or "settings.json", _plugins(sdlc_factory=True)
        )
        assert sdlc.factory_enabled(home) == (True, scope)
        if name is None:
            (user / ".claude" / "settings.json").unlink()
    home = tmp_path / "both"
    home.mkdir()
    _settings(user, "settings.json", _plugins(sdlc_factory=True))
    _settings(home, "settings.local.json", _plugins(sdlc_factory=False))
    assert sdlc.factory_enabled(home) == (False, "local")
    # Any marketplace counts; another plugin never does.
    _settings(home, "settings.local.json", json.dumps({"enabledPlugins": {"sdlc@sdlc": True}}))
    _settings(home, "settings.json", json.dumps({"enabledPlugins": {"sdlc-factory@fork": True}}))
    assert sdlc.factory_enabled(home) == (True, "project")
    root = _repo(tmp_path)
    _settings(root, "settings.json", _plugins(sdlc_factory=True))
    capsys.readouterr()
    assert sdlc.cmd_config(root) == 0
    assert json.loads(capsys.readouterr().out)["factory"] == {"enabled": True, "scope": "project"}


@pytest.mark.portable
def test_config_reports_no_factory_without_settings(tmp_path: Path, monkeypatch, capsys) -> None:
    """R2: nothing names it, a file won't parse, or `enabledPlugins` isn't an object: no factory,
    no traceback, no warning, exit 0. Wrong here only hides an option."""
    user = _user_home(tmp_path, monkeypatch)
    root = _repo(tmp_path)
    capsys.readouterr()
    assert sdlc.cmd_config(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["factory"] == {"enabled": False, "scope": None}
    assert not [w for w in out["warnings"] if "factory" in w or "settings" in w]
    _settings(root, "settings.local.json", "{not json")
    _settings(root, "settings.json", json.dumps({"enabledPlugins": ["sdlc-factory@sdlc"]}))
    _settings(user, "settings.json", json.dumps(["no", "object"]))
    capsys.readouterr()
    assert sdlc.cmd_config(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["factory"] == {"enabled": False, "scope": None}
    assert not [w for w in out["warnings"] if "factory" in w or "settings" in w]


@pytest.mark.portable
def test_factory_detection_runs_nothing(tmp_path: Path, monkeypatch) -> None:
    """R3: three files read, nothing run: no `claude plugin list`, no git, nothing of the
    factory's own."""
    user = _user_home(tmp_path, monkeypatch)
    _settings(user, "settings.json", _plugins(sdlc_factory=True))

    def refuse(*args, **kwargs):
        raise AssertionError(f"ran {args}")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    assert sdlc.factory_enabled(tmp_path) == (True, "user")


# ---------------------------------------------------------------- what a change needs (107)


def _rec(**fields) -> dict:
    """A record as `needs_of()` reads it: an open change with nothing to say, then `fields`."""
    rec = {
        "stage": "build", "tier": 2, "problems": [], "stopped": None, "decision": None,
        "reconsider": False, "pending": [], "assumed": [], "ledger_lines": 0,
        "spec_filled": False,
    }  # fmt: skip
    return rec | fields


def _d(*ids: str) -> list[dict]:
    return [{"id": i, "by": "code round 1", "text": "which?"} for i in ids]


@pytest.mark.portable
def test_needs_of_reads_nothing() -> None:
    """R1: the rules are a pure function of the record, so the board and status can't disagree."""
    reads = []

    def refuse(*args, **kwargs):
        reads.append(args)
        raise AssertionError(f"needs_of read something: {args}")

    rec = _rec(stage="test", decision="ESCALATE", pending=_d("D2"), ledger_lines=1)
    with pytest.MonkeyPatch.context() as mp:
        for name in ("read_text", "read_bytes", "is_file", "is_dir", "exists", "open", "stat"):
            mp.setattr(Path, name, refuse)
        mp.setattr(subprocess, "run", refuse)
        mp.setattr("builtins.open", refuse)
        got = (sdlc.needs_of(rec), sdlc.answered(rec))
    assert reads == [] and got == (["decide D2"], False)


@pytest.mark.portable
def test_a_stop_needs_its_way_on() -> None:
    """R2: at `build` a stop needs its way on; a record that won't read, to be read; elsewhere
    nothing."""
    for way, need in (
        ("rerun", "stopped: fix its cause and rerun"),
        ("mend", "stopped: rerun to ask an agent again"),
        ("ship", "stopped: review an agent's commit"),
    ):
        assert sdlc.needs_of(_rec(stopped={"way": way, "next": "x"})) == [need]
    assert sdlc.needs_of(_rec(stopped={"way": None, "next": "x"})) == [
        "stopped: read runs/stopped.md"
    ]
    for stage in ("plan", "design", "test"):
        assert sdlc.needs_of(_rec(stage=stage, stopped={"way": "rerun"})) == [], stage


@pytest.mark.portable
def test_a_park_past_its_deadline_needs_the_person() -> None:
    """222 R16: a park past its deadline with no stop recorded (a supervisor that died) needs the
    resource freed; one within it needs nothing; a stop recorded says its own way on."""
    park = {"resource": "staging db", "holder": "219-other", "retry": "2026-11-21T15:05:00Z",
            "deadline": "2026-11-21T16:00:00Z"}  # fmt: skip
    assert sdlc.needs_of(_rec(parked=park, now="2026-11-21T15:30:00Z")) == []
    assert sdlc.needs_of(_rec(parked=park, now="2026-11-21T16:00:00Z")) == [
        "parked past its deadline: free staging db"
    ]
    stopped = _rec(parked=park, now="2026-11-21T17:00:00Z", stopped={"way": "parked"})
    assert sdlc.needs_of(stopped) == ["stopped: free what it waits on and rerun"]
    assert sdlc.needs_of(_rec(stage="test", parked=park, now="2026-11-21T17:00:00Z")) == []


@pytest.mark.portable
def test_a_mend_under_way_needs_nobody_until_its_timeout() -> None:
    """233: a `mend` stop whose mend has started needs nothing while the agent's timeout holds,
    and past it says so, in words with no comma; a stop whose mend is used up (`rerun`) needs the
    person at once, whatever the step record still says."""
    mend = {"role": "builder", "round": 1, "since": "2026-11-22T14:02:00Z",
            "deadline": "2026-11-22T17:02:00Z"}  # fmt: skip
    stop = {"way": "mend", "next": "x"}
    under_way = _rec(id="230", stopped=stop, mending=mend, now="2026-11-22T15:00:00Z")
    assert sdlc.needs_of(under_way) == [] and sdlc.mend_running(under_way) == mend
    assert sdlc.column(under_way | {"needs": [], "mode": "factory"}) == "building"
    left = under_way | {"now": "2026-11-22T17:02:00Z"}
    [need] = sdlc.needs_of(left)
    assert need == (
        "stopped: mending the builder since 14:02 with no reply: rerun /sdlc-factory:build 230 if "
        "no session runs it"
    )
    assert "," not in need and sdlc.mend_running(left) is None
    used_up = under_way | {"stopped": {"way": "rerun", "next": "x"}}
    assert sdlc.needs_of(used_up) == ["stopped: fix its cause and rerun"]
    assert sdlc.mend_running(used_up) is None
    assert sdlc.needs_of(under_way | {"mending": None}) == ["stopped: rerun to ask an agent again"]
    assert sdlc.needs_of(under_way | {"now": None}) == ["stopped: rerun to ask an agent again"]


@pytest.mark.portable
def test_a_stop_s_need_is_in_plain_words() -> None:
    """120 (2026-11-17-84): a stop's need never says the factory's own word for a way, and holds
    no comma, since `status` joins a change's needs with one."""
    for way in ("rerun", "mend", "ship", "parked"):
        [need] = sdlc.needs_of(_rec(stopped={"way": way, "next": "x"}))
        assert need.startswith("stopped: ") and "," not in need, need
        assert "mend" not in need, need


@pytest.mark.portable
def test_a_blocking_decision_needs_its_id() -> None:
    """R3: one `decide D<n>` per unticked blocking decision, in ledger order, after the stop."""
    rec = _rec(stopped={"way": "rerun"}, pending=_d("D3", "D1"), assumed=_d("D2"))
    assert sdlc.needs_of(rec) == ["stopped: fix its cause and rerun", "decide D3", "decide D1"]
    assert sdlc.needs_of(_rec(stage="test", pending=_d("D1"))) == [], "no ESCALATE: nothing"
    assert sdlc.needs_of(_rec(stage="test", decision="READY", pending=_d("D1"))) == []


@pytest.mark.portable
def test_a_landing_stop_needs_the_person() -> None:
    """141: a landing that stopped (`land_stop`, from `runs/land-step.md`) needs the person at the
    landing's stages, `test` before its commit and `shipped` after, naming the step it stopped
    after; a problem still comes first, and at any other stage the record is history."""
    stop = {"after": "close", "problems": ["sdlc.py close refused"]}
    assert sdlc.needs_of(_rec(stage="shipped", land_stop=stop)) == ["landing stopped at close"]
    assert sdlc.needs_of(_rec(stage="test", land_stop=stop | {"after": "ship"})) == [
        "landing stopped at ship"
    ]
    assert sdlc.needs_of(_rec(stage="test", land_stop=stop | {"after": None})) == [
        "landing stopped at a step"
    ]
    rec = _rec(stage="shipped", problems=["findings.md couldn't be read"], land_stop=stop)
    assert sdlc.needs_of(rec) == ["fix: findings.md couldn't be read", "landing stopped at close"]
    for stage in ("plan", "design", "build", "dropped"):
        assert sdlc.needs_of(_rec(stage=stage, land_stop=stop)) == [], stage
    assert sdlc.needs_of(_rec(stage="shipped", land_stop=None)) == []
    [need] = sdlc.needs_of(_rec(stage="shipped", land_stop=stop))
    assert "," not in need, "status joins a change's needs with one"


WEIGHED = (
    "# Decisions\n\n"
    "- [x] D1 (code round 1, default): Log the draft id? → settled by the approver: spec R4\n"
    "- [ ] D2 (builder round 1, default): Page the drafts list at 50?\n"
    "  - OPTION: 50 — one screen's worth; a second page past it\n"
    "  - OPTION: 100 — fewer pages; a slower first paint\n"
    "  - WHY: the spec's list view shows 50\n"
)


@pytest.mark.portable
def test_a_ledger_with_alternatives_is_not_garbled(tmp_path) -> None:
    """137 R2: the indented OPTION and WHY lines are no lines of the ledger, and no open box."""
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "decisions.md").write_text(
        "".join(ln + "\n" for ln in WEIGHED.splitlines() if not ln.startswith("  ")),
        encoding="utf-8",
    )
    weighed = tmp_path / "weighed"
    weighed.mkdir()
    (weighed / "decisions.md").write_text(WEIGHED, encoding="utf-8")
    a, b = sdlc.factory_records.reading(plain), sdlc.factory_records.reading(weighed)
    assert (b["pending"], b["assumed"], b["problems"]) == (a["pending"], a["assumed"], [])
    assert [d["id"] for d in b["assumed"]] == ["D2"]


@pytest.mark.portable
def test_an_escalation_with_only_settled_defaults_is_not_answered(tmp_path) -> None:
    """137 R10: an approver's call is never the person's answer, so a ledger holding only settled
    lines leaves the escalation to be read."""
    (tmp_path / "decision.md").write_text("DECISION: ESCALATE\n\nWhy.\n", encoding="utf-8")
    (tmp_path / "decisions.md").write_text(WEIGHED.split("- [ ] D2")[0], encoding="utf-8")
    found = sdlc.factory_records.reading(tmp_path)
    assert found["ledger_lines"] == 0 and found["problems"] == [], found
    rec = _rec(stage="test", **{k: found[k] for k in ("decision", "assumed", "ledger_lines")})
    assert sdlc.needs_of(rec) == ["read the escalation"] and sdlc.answered(rec) is False
    (tmp_path / "decisions.md").write_text(WEIGHED, encoding="utf-8")
    found = sdlc.factory_records.reading(tmp_path)
    rec = _rec(stage="test", **{k: found[k] for k in ("decision", "assumed", "ledger_lines")})
    assert sdlc.needs_of(rec) == ["confirm 1 default"], "only the open default"


@pytest.mark.portable
def test_ready_with_assumed_defaults_is_ready(tmp_path) -> None:
    """202 R6: a READY at `test` carrying open defaults to the landing needs nothing of the
    person before it: Ready, no decide step; the card still counts the defaults assumed."""
    (tmp_path / "decision.md").write_text(
        "DECISION: READY\n\nWhy.\n\n- CONFIRM: D2: 50 a page\n", encoding="utf-8"
    )
    (tmp_path / "decisions.md").write_text(WEIGHED, encoding="utf-8")
    found = sdlc.factory_records.reading(tmp_path)
    assert [d["id"] for d in found["assumed"]] == ["D2"], found
    rec = _rec(stage="test", **{k: found[k] for k in ("decision", "assumed", "ledger_lines")})
    rec |= {"id": "008", "mode": "factory"}
    assert sdlc.needs_of(rec) == [], rec
    rec["needs"] = sdlc.needs_of(rec)
    assert sdlc.column(rec) == "ready" and sdlc.decide_step(rec) is None
    page = (REPO / "scripts" / "board.html").read_text(encoding="utf-8")
    assert "default(s) assumed" in page, "the card still counts them"


@pytest.mark.portable
def test_an_escalation_needs_what_its_ledger_holds() -> None:
    """R4: what the ledger and decision still hold, in order; an empty ledger needs reading."""
    esc = {"stage": "test", "decision": "ESCALATE"}
    full = _rec(**esc, pending=_d("D2", "D4"), assumed=_d("D1", "D3", "D5"), ledger_lines=6,
                reconsider=True)  # fmt: skip
    assert sdlc.needs_of(full) == ["decide D2", "decide D4", "confirm 3 defaults",
                                   "reconsider the approach"]  # fmt: skip
    assert sdlc.needs_of(_rec(**esc, assumed=_d("D1"), ledger_lines=2)) == ["confirm 1 default"]
    assert sdlc.needs_of(_rec(**esc)) == ["read the escalation"]
    assert sdlc.needs_of(_rec(**esc, reconsider=True)) == [
        "reconsider the approach", "read the escalation",
    ]  # fmt: skip
    assert sdlc.needs_of(_rec(**esc, ledger_lines=2)) == [], "every line ticked"
    assert sdlc.answered(_rec(**esc, ledger_lines=2)) is True
    for rec in (_rec(**esc), _rec(**esc, ledger_lines=2, reconsider=True),
                _rec(**esc, ledger_lines=2, problems=["x"]), _rec(stage="test", decision="READY"),
                _rec(stage="build", decision="ESCALATE", ledger_lines=2)):  # fmt: skip
        assert sdlc.answered(rec) is False, rec


@pytest.mark.portable
def test_a_written_unapproved_spec_needs_approval() -> None:
    """R7: a Tier 2 at `plan` whose `spec.md` is written but whose stage never moved."""
    assert sdlc.needs_of(_rec(stage="plan", spec_filled=True)) == ["approve its spec"]
    assert sdlc.needs_of(_rec(stage="plan", spec_filled=False)) == []
    assert sdlc.needs_of(_rec(stage="plan", tier=1, spec_filled=True)) == []
    assert sdlc.needs_of(_rec(stage="design", spec_filled=True)) == []


@pytest.mark.portable
def test_a_problem_needs_fixing_at_any_stage_and_a_closed_change_nothing_more() -> None:
    """R8: every problem first, at any stage; a shipped or dropped change needs nothing else."""
    rec = _rec(problems=["decision.md doesn't open"], pending=_d("D1"))
    assert sdlc.needs_of(rec) == ["fix: decision.md doesn't open", "decide D1"]
    shipped = _rec(stage="shipped", problems=["p"], decision="ESCALATE")
    assert sdlc.needs_of(shipped) == ["fix: p"]
    assert sdlc.needs_of(_rec(stage="dropped", decision="ESCALATE")) == []


# ---------------------------------------------------------------- upgrade (112)

UPGRADE_NAME = "012-reopen-drafts"
UPGRADE_INTENT = """\
---
id: 012
slug: reopen-drafts
tier: {tier}
impact:
stage: {stage}
created: 2026-10-01
updated: 2026-10-02
idea:
depends_on: [003]
---

# 012 — Reopen saved drafts

## Problem

Real prose, not a template.
"""


def _upgradable(tmp_path: Path, tier: int = 1, stage: str = "build") -> tuple[Path, Path]:
    """A repo on change 012's branch, its Tier 1 folder as a factory run leaves it: (root,
    folder)."""
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", UPGRADE_NAME)
    folder = root / ".sdlc" / "work" / UPGRADE_NAME
    folder.mkdir(parents=True)
    text = UPGRADE_INTENT.format(tier=tier, stage=stage)
    (folder / "intent.md").write_text(text, encoding="utf-8", newline="\n")
    return root, folder


def _upgrade(root: Path, capsys, ident: str = "012") -> tuple[int, dict]:
    code = sdlc.cmd_upgrade(root, ident)
    return code, json.loads(capsys.readouterr().out)


def _folder_bytes(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*")
            if p.is_file()}  # fmt: skip


@pytest.mark.portable
def test_upgrade_sets_tier_and_stage_by_line(tmp_path, capsys) -> None:
    """R1: three lines change in place; every other byte, `id: 012` and the key order kept."""
    root, folder = _upgradable(tmp_path)
    before = (folder / "intent.md").read_text(encoding="utf-8")
    code, out = _upgrade(root, capsys)
    assert code == 0, out
    assert (out["change"], out["tier"], out["stage"]) == (UPGRADE_NAME, 2, "plan")
    after = (folder / "intent.md").read_text(encoding="utf-8")
    today = date.today().isoformat()
    expected = (
        before.replace("tier: 1", "tier: 2")
        .replace("stage: build", "stage: plan")
        .replace("updated: 2026-10-02", f"updated: {today}")
    )
    assert after == expected
    assert "id: 012\n" in after and "idea:\n" in after and "depends_on: [003]\n" in after


@pytest.mark.portable
def test_upgrade_scaffolds_only_what_is_missing(tmp_path, capsys) -> None:
    """R1: spec.md and plan.md from the templates with new's substitutions; a plan the Tier 1
    builder already wrote is kept, byte for byte."""
    root, folder = _upgradable(tmp_path)
    code, out = _upgrade(root, capsys)
    assert (code, out["created"], out["kept"]) == (0, ["spec.md", "plan.md"], []), out
    spec = (folder / "spec.md").read_text(encoding="utf-8")
    assert spec.startswith("---\nid: 012\nslug: reopen-drafts\nkind: spec\n")
    assert "# 012 — Reopen saved drafts · spec" in spec and sdlc.is_unfilled(folder / "spec.md")
    assert "NNN" not in spec and "YYYY-MM-DD" not in spec

    (tmp_path / "b").mkdir()
    root, folder = _upgradable(tmp_path / "b", stage="plan")
    (folder / "plan.md").write_text("# a plan\n\nWritten by the builder.\n", encoding="utf-8")
    code, out = _upgrade(root, capsys)
    assert (code, out["created"], out["kept"]) == (0, ["spec.md"], ["plan.md"]), out
    written = "# a plan\n\nWritten by the builder.\n"
    assert (folder / "plan.md").read_text(encoding="utf-8") == written


@pytest.mark.portable
def test_upgrade_leaves_check_strict_clean(tmp_path, capsys) -> None:
    """R1, R12: a Tier 2 at `plan` with its scaffolds owes nothing yet."""
    root, folder = _upgradable(tmp_path)
    assert _upgrade(root, capsys)[0] == 0
    problems = sdlc.analyze(root, today=date(2026, 10, 17))["problems"]
    assert [p for p in problems if p["dir"].endswith(UPGRADE_NAME)] == []


@pytest.mark.portable
@pytest.mark.parametrize("case", ["tier-2", "stage-design", "another-change", "base-branch"])
def test_upgrade_refuses_and_writes_nothing(tmp_path, capsys, case) -> None:
    """R2: each refusal leaves the folder as it was."""
    tier = 2 if case == "tier-2" else 1
    stage = {"tier-2": "plan", "stage-design": "design"}.get(case, "build")
    root, folder = _upgradable(tmp_path, tier, stage)
    ident = "013" if case == "another-change" else "012"
    if case == "base-branch":
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "012's folder")
        _git(root, "checkout", "-q", "main")
        _git(root, "checkout", "-q", UPGRADE_NAME, "--", ".sdlc")
    before = _folder_bytes(folder)
    code, out = _upgrade(root, capsys, ident)
    assert code == 1 and out["refusals"], out
    assert _folder_bytes(folder) == before
    needle = {"tier-2": "already Tier 2", "stage-design": "stage: design",
              "another-change": "013", "base-branch": "main"}[case]  # fmt: skip
    assert any(needle in r for r in out["refusals"]), out["refusals"]


# ---------------------------------------------------------------- escalations that clear (145)

GREEN = {"verdict": "PASS", "current": True}
GATE = {"kind": "gate", "text": "the gate is red", "cleared": False, "filed": True}
LOOK = {"kind": "look", "text": "it reads oddly", "cleared": False, "filed": True}
SEEN = LOOK | {"cleared": True}
UNFILED = LOOK | {"filed": False}
LOOKS = [{"id": "D4", "text": "it reads oddly"}]


@pytest.mark.portable
@pytest.mark.parametrize(
    ("fields", "needs"),
    [
        ({"pending": _d("D2"), "assumed": _d("D3", "D5"), "ledger_lines": 3},
         ["decide D2", "confirm 2 defaults"]),
        ({"reconsider": True}, ["reconsider the approach", "read the escalation"]),
        ({"reasons": [LOOK], "looks": LOOKS}, ["acknowledge D4"]),
        ({"reasons": [SEEN], "looks": []}, []),
        ({"reasons": [GATE, GATE | {"text": "lint"}]}, ["gate it green"]),
        ({"reasons": [GATE], "gate": GREEN}, []),
        ({"reasons": [GATE], "gate": {"verdict": "PASS", "current": False}}, ["gate it green"]),
        ({"reasons": [GATE], "gate": {"verdict": "FAIL", "current": True}}, ["gate it green"]),
        ({"reasons": [GATE, LOOK], "looks": LOOKS, "pending": _d("D1"), "ledger_lines": 1},
         ["decide D1", "acknowledge D4", "gate it green"]),
        ({"reasons": [UNFILED], "looks": []}, ["read the escalation"]),
        ({}, ["read the escalation"]),
        ({"ledger_lines": 1}, []),
    ],
    ids=["ledger", "reconsider", "look", "seen", "gate", "gate-green", "gate-stale", "gate-red",
         "all", "unfiled", "old-decision", "ticked"],
)  # fmt: skip
def test_needs_of_an_escalation_by_its_reasons(fields, needs) -> None:
    """145 R9: an ESCALATE at `test` needs what its ledger and its reasons still hold, a gate
    reason cleared only by a current green hand gate; one that needs nothing is answered."""
    rec = _rec(stage="test", decision="ESCALATE") | fields
    assert sdlc.needs_of(rec) == needs
    assert sdlc.answered(rec) == (needs == [])
    step = sdlc.decide_step(rec | {"id": "008", "needs": needs})
    assert (step is not None) == any(
        n.startswith(("decide ", "confirm ", "acknowledge ")) for n in needs
    )


# ---------------------------------------------------------------- opened (162)

OPENED_RE = r"^opened: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z)$"


@pytest.mark.portable
@pytest.mark.parametrize("tier", [1, 2])
def test_new_writes_when_the_change_was_opened_to_the_minute(tmp_path: Path, tier: int) -> None:
    """162 R1: local numbering; `opened:` in UTC after `created:`, the id kept as written, and
    every other line the template's own."""
    (tmp_path / ".sdlc").mkdir()
    (tmp_path / ".sdlc" / "last-id").write_text("011\n", encoding="utf-8")
    before = datetime.now(UTC).replace(second=0, microsecond=0)
    assert sdlc.cmd_new(tmp_path, "reopen-drafts", tier, None) == 0
    text = (tmp_path / ".sdlc" / "work" / "012-reopen-drafts" / "intent.md").read_text("utf-8")
    [stamp] = re.findall(OPENED_RE, text, re.M)
    opened = datetime.strptime(stamp, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)
    assert before <= opened <= datetime.now(UTC)
    assert sdlc.frontmatter_list(text, "opened") == [stamp]
    assert "\nid: 012\n" in text
    lines = text.splitlines()
    assert lines[lines.index(f"opened: {stamp}") - 1].startswith("created: ")
    rendered, _ = sdlc.render_template(
        tmp_path, "intent.md", "012", "reopen-drafts", date.today().isoformat(), "reopen drafts"
    )
    rendered = rendered.replace("tier: 1", f"tier: {tier}", 1)
    assert text.replace(f"opened: {stamp}\n", "", 1) == rendered


@pytest.mark.portable
def test_opened_goes_before_the_closing_line_without_created() -> None:
    text = "---\nid: 012\nstage: plan\n---\n\n# 012 — x\n"
    got = sdlc._with_opened(text, "2026-11-19T10:05Z")
    assert got == "---\nid: 012\nstage: plan\nopened: 2026-11-19T10:05Z\n---\n\n# 012 — x\n"
    assert sdlc._with_opened("no frontmatter\n", "2026-11-19T10:05Z") == "no frontmatter\n"


@pytest.mark.portable
def test_shipping_dropping_and_upgrading_keep_opened(tmp_path, capsys) -> None:
    """162 R2: every stamp edits its own lines and leaves `opened:` as it is."""
    text = "---\nid: 012\nstage: build\ncreated: 2026-11-18\nopened: 2026-11-18T09:07Z\n"
    text += "updated: 2026-11-18\n---\n\n# 012 — x\n"
    for stamped, _ in (sdlc.stamp_shipped(text, "2026-11-19"),
                       sdlc.stamp_dropped(text, "2026-11-19", "build")):  # fmt: skip
        assert "\nopened: 2026-11-18T09:07Z\n" in stamped
    root, folder = _upgradable(tmp_path)
    intent = folder / "intent.md"
    lines = intent.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(i for i, ln in enumerate(lines) if ln.startswith("created:"))
    lines.insert(at + 1, "opened: 2026-10-01T08:30Z\n")
    intent.write_text("".join(lines), encoding="utf-8", newline="\n")
    code, out = _upgrade(root, capsys)
    assert code == 0, out
    assert "\nopened: 2026-10-01T08:30Z\n" in intent.read_text(encoding="utf-8")


# ---------------------------------------------------------------- status's nits (169)


def test_held_by_rebase_walks_the_change_trees_once(tmp_path: Path, monkeypatch) -> None:
    """169 R13: `held_by_rebase()` reads every change's checkout once, and hands the list to
    `rebasing_branches()` rather than having it walk them again."""
    calls = []

    def trees(root: Path) -> list:
        calls.append(root)
        return [(tmp_path / "wt", "030-draft-land")]

    monkeypatch.setattr(sdlc, "_change_trees", trees)
    monkeypatch.setattr(sdlc, "worktrees", lambda root: [])
    monkeypatch.setattr(sdlc, "_stage", lambda folder: "shipped")
    held = sdlc.held_by_rebase(tmp_path)
    assert [h["branch"] for h in held] == ["030-draft-land"]
    assert len(calls) == 1, calls
    assert sdlc.rebasing_branches(tmp_path) == {"030-draft-land"}, "alone, it still walks them"


@pytest.mark.parametrize("mode", ["factory", "manual"])
@pytest.mark.parametrize("stage", sdlc.STAGES)
def test_by_state_places_a_record_without_a_column_as_column_does(stage: str, mode: str) -> None:
    """169 R14: a record read without a `column` sits where `column()` puts it: one rule."""
    rec = {"stage": stage, "mode": mode, "errors": []}
    shown = sdlc._by_state({"open": [rec]})
    [key] = [k for k, (recs, _) in shown.items() if recs]
    assert key == sdlc.column({"stage": stage, "problems": [], "mode": mode})


def test_vet_strict_fails_on_a_problem(tmp_path: Path, capsys, monkeypatch) -> None:
    """`vet` reports the problems and exits 0; `vet --strict` exits 1 on any of them."""
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    (root / ".sdlc" / "work").mkdir(parents=True, exist_ok=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "## [2026-10-01-1] [building] Orphan\n", encoding="utf-8"
    )
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "vet"])
    capsys.readouterr()
    assert sdlc.main() == 0
    assert "■ Problems: 1" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "vet", "--strict"])
    assert sdlc.main() == 1


def test_check_is_no_longer_a_command(tmp_path: Path, capsys, monkeypatch) -> None:
    """The old name has no alias: argparse refuses it, and the help lists `vet` where it stood."""
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "check", "--strict"])
    with pytest.raises(SystemExit) as stop:
        sdlc.main()
    assert stop.value.code == 2
    assert "invalid choice: 'check'" in capsys.readouterr().err
    assert "check" not in sdlc.HELP_ORDER and "vet" in sdlc.HELP_ORDER


# ---------------------------------------------------------------- origin


def test_origin_values_are_host_and_self() -> None:
    """Two words, one list: found using the plugin in another repo, or found working on this one,
    a retrospective, a review finding or a nit included."""
    assert sdlc.ORIGINS == ("host", "self")


def test_vet_strict_passes_a_change_with_no_origin(tmp_path: Path, capsys, monkeypatch) -> None:
    """Older changes and hosts that never set the line keep working: a missing `origin:` is
    unknown, never a problem."""
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    d = _change(root, "001-x", _fm())
    rec = sdlc.load_change(d, root)
    assert rec["origin"] is None and rec["errors"] == []
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "vet", "--strict"])
    capsys.readouterr()
    assert sdlc.main() == 0, capsys.readouterr().out


@pytest.mark.parametrize("line", ["elsewhere", "[host, self]"])
def test_an_origin_outside_host_and_self_is_an_error(tmp_path: Path, line: str) -> None:
    d = _change(tmp_path, "001-x", _fm(origin=line))
    errors = sdlc.load_change(d, tmp_path)["errors"]
    assert any(e.startswith("origin:") for e in errors), errors
    for good in sdlc.ORIGINS:
        ok = _change(tmp_path, f"00{2 + sdlc.ORIGINS.index(good)}-{good}", _fm(origin=good))
        rec = sdlc.load_change(ok, tmp_path)
        assert rec["origin"] == good and rec["errors"] == []


def test_a_closed_change_without_origin_reads_none() -> None:
    """`closed_changes()` builds each record with `_change_record()`: the line's word when it is
    one of the two, None otherwise, never `self` guessed for a change that named none."""

    def rec(origin: str | None) -> dict:
        text = INTENT.replace("tier: 2\n", "tier: 2\nimpact: patch\n", 1)
        if origin is not None:
            text = text.replace("idea:\n", f"idea:\norigin: {origin}\n", 1)
        return sdlc._change_record("007-reopen-drafts", text, "abc1234", True)

    assert rec("host")["origin"] == "host"
    assert rec("self")["origin"] == "self"
    assert rec(None)["origin"] is None
    assert rec("elsewhere")["origin"] is None
    assert rec("")["origin"] is None
    assert (
        sdlc._change_record("007-reopen-drafts", None, "abc1234", True, read=False)["origin"]
        is None
    )


def test_an_entry_reads_its_origin_line() -> None:
    text = (
        "## [2026-11-20-3] [idea] Reopen saved drafts\n\nA draft once saved can be reopened.\n"
        "Origin: host\nTheme: drafts\n"
    )
    [entry] = sdlc.parse_entries(text)
    assert entry["fields"]["Origin"] == "host"
