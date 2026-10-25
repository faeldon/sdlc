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
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SDLC_PY = REPO / "scripts" / "sdlc.py"


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
    """The `~` marker in `status` depends on this, and so does `check`'s unfilled-artifact problem.

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
    d = root / "work" / name
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
    `new` produces something that instantly fails its own `check` teaches you to ignore the check.
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
    """Present-but-empty must not read as done — the distinction `check` exists to draw."""
    scaffold = (REPO / "templates" / "spec.md").read_text(encoding="utf-8")
    _change(
        tmp_path,
        "001-x",
        _fm(tier=2, stage="build"),
        {"spec.md": scaffold, "plan.md": "# plan\n\nWritten.\n"},
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any("still the template" in p["detail"] for p in a["problems"])


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
        ("work/001-x", "dropped_at"),
        ("work/001-x", "stage:"),
        ("work/002-y", "stage:"),
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
    (tmp_path / "work").mkdir()
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
    assert (tmp_path / "work" / "008-z").is_dir()
    assert (tmp_path / ".sdlc" / "last-id").read_text(encoding="utf-8") == "008\n"
    assert not (tmp_path / ".sdlc" / "last-id.tmp").exists()


def test_a_number_is_never_reused_after_its_folder_is_deleted(tmp_path: Path) -> None:
    """Scanning the folders would hand 002 out again; the counter remembers it was spent."""
    assert sdlc.cmd_new(tmp_path, "a", 1, None) == 0
    assert sdlc.cmd_new(tmp_path, "b", 1, None) == 0
    shutil.rmtree(tmp_path / "work" / "002-b")
    assert sdlc.cmd_new(tmp_path, "c", 1, None) == 0
    assert (tmp_path / "work" / "003-c").is_dir()


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
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "ideas.md").write_text(
        "## [2026-10-01] [building] Column level lineage export\n\nSome prose.\n", encoding="utf-8"
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert any(p["kind"] == "orphan idea" for p in a["problems"])


def test_building_idea_with_a_folder_is_quiet(tmp_path: Path) -> None:
    """The slug match is deliberately loose both ways: a folder slug is a shortening of the idea's
    title, never a copy, so an exact comparison would nag about every idea being worked on."""
    _change(tmp_path, "001-column-lineage", _fm(slug="column-lineage"))
    (tmp_path / "work" / "ideas.md").write_text(
        "## [2026-10-01] [building] Column lineage\n", encoding="utf-8"
    )
    a = sdlc.analyze(tmp_path, today=date(2026, 10, 17))
    assert not any(p["kind"] == "orphan idea" for p in a["problems"])


def test_building_idea_linked_only_by_frontmatter_is_quiet(tmp_path: Path) -> None:
    """`idea:` is the explicit link /sdlc:intent writes, so it counts even when the slug has
    drifted from the title. The frontmatter keeps the heading as it read at
    promotion, `[seed]`, while work/ideas.md now says `[building]`, so the match is on the title."""
    _change(
        tmp_path,
        "001-search-front-end",
        _fm(slug="search-front-end", idea='"[2026-10-01] [seed] Search as its own page"'),
    )
    (tmp_path / "work" / "ideas.md").write_text(
        "## [2026-10-01] [building] Search as its own page\n", encoding="utf-8"
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
    (tmp_path / "work" / "ideas.md").write_text(
        "## [2026-10-01] [building] Search as its own page\n", encoding="utf-8"
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
    folder = next((tmp_path / "work").glob("*-quiet"))
    assert sorted(p.name for p in folder.iterdir()) == sorted(sdlc.TIER_ARTIFACTS[tier])


def test_a_hosts_ideas_and_notes_templates_win(tmp_path: Path) -> None:
    for name in ("ideas.md", "notes.md"):
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
    assert sorted(p.name for p in (tmp_path / "work").iterdir()) == ["001-x"]


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
    the four is wrong, so `check --strict` catches a typo before a release reads it."""
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
    assert out["notes"] == "work/001-x/notes.md"
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


# ---------------------------------------------------------------- worktrees


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    """A real repo on `main` that ignores its change worktrees and commits work/."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
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
    assert (tree / "work" / "001-here" / "intent.md").is_file()
    assert _git(root, "status", "--porcelain") == ""


def test_new_refuses_a_slug_already_in_the_main_checkout(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    _change(root, "003-same-thing", _fm(id="003"))
    assert sdlc.cmd_new(tree, "same-thing", 1, None) == 1
    assert not (tree / "work" / "004-same-thing").exists()


def test_new_refuses_a_slug_open_in_another_worktree(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "same-thing", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "same-thing", 1, None, worktree=True) == 1
    assert "002-same-thing" not in _git(root, "branch", "--list")


def test_new_refuses_while_work_is_ignored(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".gitignore").write_text("work/\n", encoding="utf-8")
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 1
    assert "remove the `work/` line from .gitignore" in capsys.readouterr().err
    assert "001-thing" not in _git(root, "branch", "--list")


def test_check_flags_an_ignored_work(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _change(root, "001-x", _fm())
    assert sdlc.analyze(root)["problems"] == []
    (root / ".gitignore").write_text("work/\n", encoding="utf-8")
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
    assert (tree / "work" / "001-fresh-thing" / "intent.md").is_file()
    assert not (root / "work").exists()
    assert _git(root, "status", "--porcelain") == ""


def test_new_worktree_from_inside_a_worktree_lands_under_the_main_checkout(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tree = _sibling(root, "side")
    assert sdlc.cmd_new(tree, "nested", 1, None, worktree=True) == 0
    made = root / ".claude" / "worktrees" / "001-nested"
    assert (made / "work" / "001-nested" / "intent.md").is_file()
    assert not (tree / "work").exists() and not (root / "work").exists()


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
    assert not (root / "work" / "001-thing").exists()
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
    assert {".sdlc/", "work/"} <= untracked
    assert not (root / ".sdlc" / "last-id").exists()


def test_an_open_change_holds_its_number_with_main_counter_behind(tmp_path: Path) -> None:
    """Main's counter never moved, and deleting the open change's folder doesn't free its
    number while its branch exists."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "first", 1, None, worktree=True) == 0
    assert sdlc.cmd_new(root, "second", 1, None, worktree=True) == 0
    assert not (root / ".sdlc" / "last-id").exists()
    shutil.rmtree(root / ".claude" / "worktrees" / "002-second" / "work" / "002-second")
    assert sdlc.next_id(root) == "003"


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
    before = sorted(p.name for p in (root / "work").iterdir())
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "next"])
    assert sdlc.main() == 0
    assert capsys.readouterr().out.strip() == "005"
    assert sorted(p.name for p in (root / "work").iterdir()) == before


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
    intent = tree / "work" / branch / "intent.md"
    # /sdlc:ship sets the impact the human approved before it runs `ship`.
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    assert sdlc.cmd_ship(root, branch[:3]) == 0
    (tree / f"{slug}.txt").write_text("the change\n", encoding="utf-8")
    # The change's own paths: its code, its folder and the counter `new` wrote beside it.
    _git(tree, "add", f"{slug}.txt", "work", ".sdlc")
    _git(tree, "commit", "-q", "-m", f"ship {branch}")
    return tree, branch


def _close(root: Path, ident, capsys, check_only: bool = False) -> tuple[int, dict]:
    capsys.readouterr()  # what new and ship printed while setting up
    code = sdlc.cmd_close(root, ident, check_only)
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
    assert not (root / "work" / branch).exists() and _git(root, "status", "--porcelain") == ""
    assert "stage: shipped" in _git(root, "show", f"{tip}:work/{branch}/intent.md")
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


def test_behind_main_counts_what_the_branch_lacks(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "thing", 1, None, worktree=True) == 0
    tree = root / ".claude" / "worktrees" / "001-thing"
    assert sdlc.behind_main(root, "001-thing") == 0
    _diverge(root, tree)
    _git(root, "commit", "-q", "--allow-empty", "-m", "main moved again")
    assert sdlc.behind_main(root, "001-thing") == 2
    assert sdlc.behind_main(root, "002-nothing") is None


def test_status_marks_a_stale_base_and_check_ignores_it(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """Ship stops on the mark before the gate runs; close would refuse the branch anyway. A nudge,
    never a problem: `check --strict` is a gate."""
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

    monkeypatch.setattr(sys, "argv", ["sdlc.py", "check", "--strict"])
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
    folder = tree / "work" / "001-thing"
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
    """With every folder gone from main, `check` passes, and still flags an orphan seed."""
    root = _repo(tmp_path)
    _shipped_change(root)
    monkeypatch.chdir(root)
    assert _close(root, "001", capsys)[0] == 0
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "check", "--strict"])
    assert sdlc.main() == 0
    (root / "work").mkdir(exist_ok=True)
    (root / "work" / "ideas.md").write_text("## [2026-10-01] [building] Orphan\n", encoding="utf-8")
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


def test_core_never_calls_gh_itself() -> None:
    """Every call to GitHub is the GitHub tracker's, so a host without it runs no GitHub code."""
    core = SDLC_PY.read_text(encoding="utf-8")
    # GitHub's closing keyword too: core writes the line the tracker hands it, never its own.
    for needle in ('"gh"', "_gh(", "github.com", "Closes #"):
        assert needle not in core, f"{needle} belongs in scripts/trackers/github.py"
    github = (TRACKERS / "github.py").read_text(encoding="utf-8")
    assert '"gh"' in github and "github.com" in github and "Closes #" in github


def test_archive_targets_are_the_tracker_modules() -> None:
    """A module added to scripts/trackers/ is a target, with no edit to the config code."""
    stems = {p.stem for p in TRACKERS.glob("*.py") if not p.stem.startswith("_")}
    assert set(sdlc.ARCHIVE_TARGETS) == stems | {"none"}
    assert sdlc.ARCHIVE_TARGETS[0] == "github" and sdlc.ARCHIVE_TARGETS[-1] == "none"


def test_target_none_runs_a_change_without_loading_a_tracker(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir()
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
    (root / ".sdlc").mkdir()
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
    (tmp_path / ".sdlc").mkdir()
    (tmp_path / ".sdlc" / "config.toml").write_text('[retro]\nevidence = "echo"\n', "utf-8")
    _, warnings, _ = sdlc.load_config(tmp_path)
    assert "retro.evidence must be a list of commands" in warnings


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
    """A product doc landing on one branch mustn't fail `check` for changes on others, which have
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


# ---------------------------------------------------------------- ship's landing edits

IDEAS = (
    "# Ideas\n\n> Seeds, not a backlog.\n\n"
    "## [2026-10-01] [seed] Keep drafts\n\nThe first.\n\n"
    "## [2026-10-02] [building] Reopen drafts\n\nThe one being built.\nTwo lines.\n\n"
    "## [2026-10-03] [seed] Share drafts\n\nThe last.\n"
)


def _seeded(tmp_path: Path, idea: str, ideas: str = IDEAS) -> tuple[Path, Path]:
    """A change in a real repo, ready to ship, whose `idea:` is `idea`, beside `ideas`."""
    root = _repo(tmp_path)
    d = _change(root, "001-reopen-drafts", _fm(stage="build", impact="patch", idea=idea))
    (root / "work" / "ideas.md").write_text(ideas, encoding="utf-8")
    return root, d


def _staged(root: Path) -> list[str]:
    return sorted(_git(root, "diff", "--cached", "--name-only").splitlines())


@pytest.mark.parametrize(
    "idea",
    [
        "Reopen drafts",
        '"## [2026-10-02] [seed] Reopen drafts"',
        "Reopen drafts → work/001-reopen-drafts/",
    ],
)
def test_ship_deletes_the_seed_its_idea_names_and_nothing_else(tmp_path: Path, idea) -> None:
    root, _ = _seeded(tmp_path, idea)
    assert sdlc.cmd_ship(root, "001") == 0
    assert (root / "work" / "ideas.md").read_text(encoding="utf-8") == (
        "# Ideas\n\n> Seeds, not a backlog.\n\n"
        "## [2026-10-01] [seed] Keep drafts\n\nThe first.\n\n"
        "## [2026-10-03] [seed] Share drafts\n\nThe last.\n"
    )


def test_ship_matches_a_heading_that_carries_a_pointer(tmp_path: Path) -> None:
    ideas = IDEAS.replace("Reopen drafts\n", "Reopen drafts → work/001-reopen-drafts/\n")
    root, _ = _seeded(tmp_path, "Reopen drafts", ideas)
    assert sdlc.cmd_ship(root, "001") == 0
    assert "Reopen drafts" not in (root / "work" / "ideas.md").read_text(encoding="utf-8")


def test_ship_deletes_the_last_seed_without_a_trailing_blank_line(tmp_path: Path) -> None:
    root, _ = _seeded(tmp_path, "Share drafts")
    assert sdlc.cmd_ship(root, "001") == 0
    text = (root / "work" / "ideas.md").read_text(encoding="utf-8")
    assert text.endswith("Two lines.\n") and "Share drafts" not in text


def test_two_seeds_with_the_idea_s_title_refuse_before_any_write(tmp_path: Path, capsys) -> None:
    ideas = IDEAS + "\n## [2026-10-04] [seed] Reopen drafts\n\nA twin.\n"
    root, d = _seeded(tmp_path, "Reopen drafts", ideas)
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(root, "001") == 1
    err = capsys.readouterr().err
    assert "2 entries titled 'Reopen drafts'" in err and "lines 9, 18" in err
    assert (d / "intent.md").read_text(encoding="utf-8") == before
    assert (root / "work" / "ideas.md").read_text(encoding="utf-8") == ideas
    assert _staged(root) == []


@pytest.mark.parametrize("ideas", [None, IDEAS.replace("Reopen", "Rename")])
def test_ship_with_no_seed_to_remove_says_so_and_ships_twice(tmp_path: Path, capsys, ideas):
    root, d = _seeded(tmp_path, "Reopen drafts", ideas or "")
    if ideas is None:
        (root / "work" / "ideas.md").unlink()
    assert sdlc.cmd_ship(root, "001") == 0
    assert "no seed to remove" in capsys.readouterr().out
    assert sdlc.cmd_ship(root, "001") == 0, "a rerun after a refused commit"
    assert "stage: shipped" in (d / "intent.md").read_text(encoding="utf-8")


def test_ship_with_no_idea_mentions_no_seed(tmp_path: Path, capsys) -> None:
    root, _ = _seeded(tmp_path, "")
    assert sdlc.cmd_ship(root, "001") == 0
    out = capsys.readouterr().out
    assert "seed" not in out and (root / "work" / "ideas.md").read_text(encoding="utf-8") == IDEAS


def test_ship_stages_the_change_and_leaves_what_it_is_told_to(tmp_path: Path, capsys) -> None:
    root, _ = _seeded(tmp_path, "Reopen drafts")
    (root / "drafts.py").write_text("x = 1\n", encoding="utf-8")
    (root / "with space.txt").write_text("x\n", encoding="utf-8")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "last-id").write_text("1\n", encoding="utf-8")
    (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
    head = _git(root, "rev-parse", "HEAD")
    assert sdlc.cmd_ship(root, "001", ["unrelated.txt"]) == 0
    assert _staged(root) == [
        ".sdlc/last-id", "drafts.py", "with space.txt",
        "work/001-reopen-drafts/intent.md", "work/ideas.md",
    ]  # fmt: skip
    assert "  staged with space.txt" in capsys.readouterr().out
    assert _git(root, "rev-parse", "HEAD") == head, "ship never commits"


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
    assert (root / "work" / "ideas.md").read_text(encoding="utf-8") == IDEAS
    assert _staged(root) == []


def test_a_left_path_already_staged_refuses_before_any_write(tmp_path: Path, capsys) -> None:
    root, d = _seeded(tmp_path, "Reopen drafts")
    (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "unrelated.txt")
    before = (d / "intent.md").read_text(encoding="utf-8")
    assert sdlc.cmd_ship(root, "001", ["unrelated.txt"]) == 1
    assert "already staged" in capsys.readouterr().err
    assert (d / "intent.md").read_text(encoding="utf-8") == before
    assert (root / "work" / "ideas.md").read_text(encoding="utf-8") == IDEAS
