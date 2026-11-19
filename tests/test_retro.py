"""The retrospective loop: what `retro` counts, the transcripts it reads only when asked, and the
one commit `retro-commit` makes.

Each repo is built the way close leaves one, as in `test_release.py`: a change's own commit
holding its shipped intent.md, then a `Close NNN-slug` commit removing the folder. Transcripts are
fixtures under a fake HOME, so nothing here reads the machine's own.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_retro", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

INTENT = """\
---
id: {id}
slug: {slug}
tier: {tier}
impact: {impact}
stage: shipped
created: {created}
updated: {created}
idea:
---

# {id} — {title}

## Problem

Drafts reopen as empty
when saved twice.

Second paragraph, not read.

## Outcome

One draft.
"""


def _git(root: Path, *args: str, when: str | None = None) -> str:
    env = os.environ | ({"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when} if when else {})
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True, env=env
    )
    return out.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _close(
    root: Path,
    name: str,
    *,
    tier: int = 1,
    impact: str = "patch",
    created: str = "2026-10-01",
    closed: str = "2026-10-02",
    files: tuple[str, ...] = (),
    intent: str | None = None,
    idea: str = "",
    later: tuple[str, ...] = (),
    before: tuple[str, ...] = (),
    based: bool = False,
    reworks: str = "",
    fixes: str = "",
    rewrite: tuple[str, ...] = (),
    trailers: tuple[str, ...] = (),
    texts: dict[str, str] | None = None,
) -> None:
    """A change's own commit, with its intent and the files it touches, then its `Close`. `later`
    is a second commit on the change, touching those files, before it closes; `before` a first
    one, without its folder. `based` writes where the change started on the `Close`, as close
    does. Each file gets the change's name appended, but those in `rewrite`, which it replaces
    whole. `reworks` is the intent's line; `trailers` go on the `Close`; `texts` are files the
    change's own commit writes whole, beside the rest. `fixes` is the intent's `fixes:` line."""
    start = _git(root, "rev-parse", "HEAD")
    when = f"{closed}T12:00:00"
    for rel in before:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{path.read_text() if path.exists() else ''}{name}\n", "utf-8")
    if before:
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"start {name}", when=when)
    nid, slug = name.split("-", 1)
    folder = root / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    text = intent or INTENT.format(
        id=nid, slug=slug, tier=tier, impact=impact, created=created, title=slug.replace("-", " ")
    )
    if idea:
        text = text.replace("idea:\n", f'idea: "{idea}"\n', 1)
    if reworks:
        text = text.replace("idea:", f"reworks: {reworks}\nidea:", 1)
    if fixes:
        text = text.replace("idea:", f"fixes: {fixes}\nidea:", 1)
    (folder / "intent.md").write_text(text, encoding="utf-8")
    for rel in (*(files or (f"{slug}.txt",)), *rewrite):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        kept = path.read_text() if path.exists() and rel not in rewrite else ""
        path.write_text(f"{kept}{name}\n", encoding="utf-8")
    for rel, body in (texts or {}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}", when=when)
    if later:
        for rel in later:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{path.read_text() if path.exists() else ''}{name}\n", "utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"follow up {name}", when=when)
    _git(root, "rm", "-r", "-q", f".sdlc/work/{name}")
    said = ["-m", "\n".join([*([f"Sdlc-Base: {start}"] if based else []), *trailers])]
    said = said if said[1] else []
    _git(root, "commit", "-q", "-m", f"Close {name}", *said, when=when)


def _retro(root: Path) -> dict:
    return sdlc.retro.retro(root, sdlc.load_config(root)[0], date(2026, 10, 24))


def _state(root: Path) -> tuple[str, str]:
    return _git(root, "status", "--porcelain"), _git(root, "rev-parse", "HEAD")


def _record(root: Path, day: str = "2026-10-10") -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(f"# Direction\n\n{day}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Retrospective {day}")


# ---------------------------------------------------------------- where retro's code lives

# What `scripts/retro.py` holds and `scripts/sdlc.py` no longer does (068).
MOVED = [
    "prose_metrics", "_release_of", "_evidence", "_product", "COMPARED", "_stop_target",
    "metrics_summary", "_prompt_report", "_extra_report", "_no_findings", "_add_findings",
    "_in_change_summary", "DROPPED_COST", "dropped_cost", "CLOCKS", "process_views", "RETROS",
    "report_rel", "_hm", "_table", "render_report", "retro_report", "rankable_entries", "_rework",
    "retro", "_change_rows", "_kind", "_line_counts", "_architecture", "bugs_retro", "_bug_paths",
    "_on_paths", "_review_at", "cmd_retro", "RERANK_KEYS", "register_drift", "cmd_retro_commit",
    "RATE_MIN_CHANGES", "ARCH_LOOKBACK", "EVIDENCE_TIMEOUT", "EVIDENCE_LIMIT", "UNMEASURED",
    "_load_indicators", "indicators",
]  # fmt: skip


def _defined(path: Path) -> set[str]:
    import ast

    names = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def test_retro_lives_in_its_own_file() -> None:
    """Retro's readers are defined in `retro.py` alone, and reached only through `sdlc.retro`: one
    name each, so a change can't edit one copy and test the other."""
    in_retro = _defined(ROOT / "scripts" / "retro.py")
    in_sdlc = _defined(ROOT / "scripts" / "sdlc.py")
    assert set(MOVED) <= in_retro, set(MOVED) - in_retro
    assert not set(MOVED) & (in_sdlc - {"retro"}), set(MOVED) & in_sdlc
    assert sdlc.retro.__file__ == str(ROOT / "scripts" / "retro.py")
    assert not [n for n in MOVED if n != "retro" and hasattr(sdlc, n)]


def test_retro_reads_sdlcs_names_when_it_runs(tmp_path: Path, monkeypatch) -> None:
    """A stand-in set on the loaded `sdlc` module after it loaded is the one retro calls: retro
    reads `sdlc.<name>` live, never a copy taken at load."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    seen = []
    real = sdlc.last_retrospective

    def standing_in(home, trunk):
        seen.append(home)
        return real(home, trunk)

    monkeypatch.setattr(sdlc, "last_retrospective", standing_in)
    _retro(root)
    assert seen


def test_retro_has_no_entry_point_of_its_own() -> None:
    """Only `sdlc.py` loads `retro.py`, by path: no dependency block of its own, no `__main__`, and
    no edit to `sys.path`."""
    text = (ROOT / "scripts" / "retro.py").read_text(encoding="utf-8")
    for needle in ("# /// script", "__main__", "sys.path"):
        assert needle not in text, needle


# ---------------------------------------------------------------- what retro counts


def test_it_reports_every_key_and_writes_nothing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    before = _state(root)
    assert sdlc.retro.cmd_retro(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out) >= {
        "since", "changes", "dropped", "dropped_at_counts", "problems", "rework",
        "rework_questions", "open", "ideas", "tiers", "impacts", "releases", "unmeasured", "prose",
        "architecture", "tests",
    }  # fmt: skip
    assert _state(root) == before


def test_the_boundary_is_the_last_retrospective_commit(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    _record(root, "2026-10-10")
    _close(root, "002-keep-one-draft")
    out = _retro(root)
    assert out["since"]["date"] == "2026-10-10"
    assert [c["name"] for c in out["changes"]] == ["002-keep-one-draft"]


def test_without_a_retrospective_the_whole_history_is_in_range(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    _git(root, "commit", "-q", "--allow-empty", "-m", "Retrospective notes, not the marker")
    _close(root, "002-keep-one-draft")
    out = _retro(root)
    assert out["since"] is None
    assert [c["name"] for c in out["changes"]] == ["001-reopen-drafts", "002-keep-one-draft"]


def test_each_change_carries_its_fields_and_problem(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", tier=2, impact="minor", files=("src/a.py", "src/b.py"))
    (change,) = _retro(root)["changes"]
    assert change["title"] == "reopen drafts"
    assert (change["tier"], change["impact"], change["created"]) == (2, "minor", "2026-10-01")
    assert change["close_date"] == "2026-10-02" and change["days_open"] == 1
    assert change["problem"] == "Drafts reopen as empty when saved twice."
    assert change["files"] == 3  # its intent too
    assert change["lines"] >= 3


def test_a_change_is_sized_by_every_commit_on_its_branch(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/a.py", "src/b.py"), later=("src/c.py",))
    (change,) = _retro(root)["changes"]
    # The intent and a.py, b.py from the first commit, c.py from the second: not c.py alone.
    assert change["files"] == 4 and change["lines"] > 3


def test_a_change_is_sized_from_where_its_close_says_it_started(tmp_path: Path) -> None:
    """A first commit without the change's folder counts once the `Close` names the start."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/b.py",), before=("src/a.py",), based=True)
    (change,) = _retro(root)["changes"]
    assert change["files"] == 3, "a.py from the first commit, b.py and the intent from ship's"


def test_without_its_start_a_change_is_sized_from_its_intent(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/b.py",), before=("src/a.py",))
    (change,) = _retro(root)["changes"]
    assert change["files"] == 2, "a close from before Sdlc-Base reads as it did"


def test_an_intent_committed_early_never_counts_another_changes_commits(tmp_path: Path) -> None:
    """Nit 2026-10-25-18: the intent landed on main, another change closed, then this one."""
    root = _repo(tmp_path)
    folder = root / ".sdlc" / "work" / "002-share-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        INTENT.format(id="002", slug="share-drafts", tier=1, impact="patch",
                      created="2026-10-01", title="share drafts"),
        encoding="utf-8",
    )  # fmt: skip
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "an intent committed outside its branch")
    _close(root, "001-reopen-drafts", files=("src/other.py",))
    start = _git(root, "rev-parse", "HEAD")
    (root / "src" / "share.py").write_text("share\n", encoding="utf-8")
    (folder / "intent.md").write_text(
        (folder / "intent.md").read_text(encoding="utf-8") + "\nMore.\n", encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "ship 002-share-drafts")
    _git(root, "rm", "-r", "-q", ".sdlc/work/002-share-drafts")
    _git(root, "commit", "-q", "-m", "Close 002-share-drafts", "-m", f"Sdlc-Base: {start}")
    share = next(c for c in _retro(root)["changes"] if c["name"] == "002-share-drafts")
    assert share["files"] == 2, "its intent and share.py, never 001's other.py"


def test_a_question_sees_lines_an_earlier_change_s_later_commit_wrote(tmp_path: Path) -> None:
    """R5: a change is every commit on its branch, so lines its second commit wrote are its own."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/drafts.py",), later=("src/other.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-04", rewrite=("src/other.py",))
    out = _retro(root)
    assert out["rework"] == []
    assert out["rework_questions"] == [
        {"change": "002-keep-one-draft", "touches": "001-reopen-drafts",
         "files": ["src/other.py"], "lines": 1}
    ]  # fmt: skip


@pytest.mark.parametrize("run", ["retro", "retro_report"])
def test_a_retrospective_reads_each_change_s_diff_once(tmp_path: Path, monkeypatch, run) -> None:
    """122: rework's blame and spend's comment count share one `git diff -U0` per change."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-04", rewrite=("src/drafts.py",))
    real, diffs = sdlc._git, Counter()

    def counting(home, *args):
        if args[:2] == ("diff", "-U0"):
            diffs[args[-1]] += 1
        return real(home, *args)

    monkeypatch.setattr(sdlc, "_git", counting)
    cfg = sdlc.load_config(root)[0]
    getattr(sdlc.retro, run)(root, cfg, date(2026, 10, 24))
    assert len(diffs) == 2 and set(diffs.values()) == {1}, diffs


def test_a_change_with_no_start_has_no_size(tmp_path: Path, monkeypatch) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-04", files=("src/drafts.py",))
    monkeypatch.setattr(sdlc, "_change_base", lambda *a: None)
    out = _retro(root)
    assert all(c["files"] is None and c["lines"] is None for c in out["changes"])
    assert [p for p in out["problems"] if "size is unknown" in p] == [
        "001-reopen-drafts: no commit holds .sdlc/work/001-reopen-drafts/intent.md, so its size "
        "is unknown",
        "002-keep-one-draft: no commit holds .sdlc/work/002-keep-one-draft/intent.md, so its "
        "size is unknown",
    ]
    assert out["rework_questions"] == [], "with no start, there is nothing to blame against"


def test_an_unparseable_intent_is_a_problem_not_a_raise(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", intent="---\nid: [unclosed\n---\n# x\n")
    out = _retro(root)
    assert any("001-reopen-drafts" in p for p in out["problems"])
    assert "problems" not in out["changes"][0]


def test_rework_is_what_a_later_change_declares_whatever_the_gap(tmp_path: Path) -> None:
    """R3: a `reworks:` line is the signal; three changes adding to one file are not rework."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", closed="2026-10-02", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-09", files=("src/drafts.py",))
    _close(root, "003-draft-titles", closed="2026-10-22", files=("src/drafts.py",),
           reworks="[001]")  # fmt: skip
    out = _retro(root)
    assert out["rework"] == [
        {"change": "003-draft-titles", "reworks": "001-reopen-drafts", "via": ["reworks"],
         "days": 20}
    ]  # fmt: skip
    assert out["rework_questions"] == [], "appending to a shared file touches nothing"


def test_a_reworks_id_naming_no_change_is_a_problem(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", reworks="[099]")
    out = _retro(root)
    assert out["rework"] == []
    assert "001-reopen-drafts: reworks '099' names no change" in out["problems"]


def _drop(
    root: Path,
    name: str,
    *,
    at: str = "build",
    created: str = "2026-10-01",
    dropped: str = "2026-10-03",
    files: tuple[str, ...] = (),
    trailers: tuple[str, ...] = (),
) -> None:
    """What drop and close leave: the branch's commit, then `Drop NNN-slug`, a merge that keeps
    main's tree and ends with what close measured, and the branch gone."""
    nid, slug = name.split("-", 1)
    _git(root, "checkout", "-q", "-b", name)
    folder = root / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    text = INTENT.format(
        id=nid, slug=slug, tier=2, impact="", created=created, title=slug.replace("-", " ")
    ).replace("stage: shipped\n", f"stage: dropped\ndropped_at: {at}\n", 1)
    (folder / "intent.md").write_text(text + "\n## Dropped\n\nNobody needed it.\n")
    for rel in files or (f"{slug}.txt",):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{name}\n", encoding="utf-8")
    when = f"{dropped}T12:00:00"
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Record why {name} was dropped", when=when)
    _git(root, "checkout", "-q", "main")
    message = ["-m", f"Drop {name}", *(["-m", "\n".join(trailers)] if trailers else [])]
    _git(root, "merge", "-q", "-s", "ours", "--no-ff", *message, name, when=when)
    _git(root, "branch", "-q", "-d", name)


def test_dropped_changes_are_counted_apart_and_by_how_far_they_got(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    _drop(root, "002-draft-sync", at="build")
    _drop(root, "003-draft-export", at="plan", dropped="2026-10-04")
    out = _retro(root)
    assert [c["name"] for c in out["changes"]] == ["001-reopen-drafts"]
    assert [d["name"] for d in out["dropped"]] == ["002-draft-sync", "003-draft-export"]
    first = out["dropped"][0]
    assert first["dropped_at"] == "build" and first["reason"] == "Nobody needed it."
    assert first["days_open"] == 2 and first["tier"] == 2 and first["files"] == 2
    assert out["dropped_at_counts"] == {"build": 1, "plan": 1}
    assert out["problems"] == [], "a dropped change never settles an impact"
    assert out["impacts"] == {"patch": 1}


def test_retro_prints_each_change_s_numbers_only_when_asked(tmp_path: Path, capsys) -> None:
    """R3, R4: the per-change `metrics` of closed and dropped changes are left out of what retro
    prints, and nothing else moves: every summary is built from the full records first."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    _drop(root, "002-draft-sync", at="build", trailers=(
        "Sdlc-Mode: manual",
        "Sdlc-Totals: elapsed=120 agent=40 response=5 away=0 blocked=0 stops=3 required=4",
    ))  # fmt: skip
    assert sdlc.retro.cmd_retro(root) == 0
    lean = json.loads(capsys.readouterr().out)
    assert sdlc.retro.cmd_retro(root, metrics=True) == 0
    full = json.loads(capsys.readouterr().out)
    assert full["dropped"][0]["metrics"]["mode"] == "manual"
    for key in ("changes", "dropped"):
        assert all("metrics" not in r for r in lean[key]), key
        full[key] = [{k: v for k, v in r.items() if k != "metrics"} for r in full[key]]
    assert "changes" not in lean["spend"] and full["spend"].pop("changes")
    assert "changes" not in lean["spend"]["agents"]
    full["spend"]["agents"].pop("changes")  # 146 R15: each change's own agent counts
    assert full == lean, "the summaries, dropped_cost and bugs are the same either way"


def test_what_a_dropped_change_cost_is_read_from_its_drop_commit(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _drop(root, "001-draft-sync", at="build", trailers=(
        "Sdlc-Mode: manual",
        "Sdlc-Coverage: transcripts=1 stages=design,build",
        "Sdlc-Totals: elapsed=120 agent=40 response=5 away=0 blocked=0 stops=3 required=4 "
        "target=2 permission=0 ship_runs=0 reenter=0 in=2 cache_read=300 out=20",
    ))  # fmt: skip
    _drop(root, "002-draft-export", at="plan")
    out = _retro(root)
    assert out["dropped"][0]["metrics"]["mode"] == "manual"
    assert out["dropped"][1]["metrics"] is None, "dropped before close measured anything"
    cost = out["dropped_cost"]
    assert (cost["captured"], cost["uncaptured"]) == (1, 1)
    sums = {"changes": 1, "elapsed": 120, "agent": 40, "in": 2, "cache_read": 300, "out": 20}
    assert cost["by_stage"] == {"build": sums}
    assert cost["by_group"] == {"tier 2, manual": sums}
    assert out["metrics"]["captured"] == 0, "dropped changes stay out of the closed ones' numbers"


def test_a_change_picking_up_a_dropped_one_says_so(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _drop(root, "001-draft-sync", dropped="2026-10-03", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-06", files=("src/drafts.py",),
           reworks="[001]")  # fmt: skip
    assert _retro(root)["rework"] == [
        {"change": "002-keep-one-draft", "reworks": "001-draft-sync", "via": ["reworks"],
         "days": 3, "dropped": True}
    ]  # fmt: skip


def test_replacing_an_earlier_change_s_lines_is_a_question_until_declared(tmp_path) -> None:
    """R5: replacing what an earlier change in the window wrote is asked about, never counted; a
    `reworks:` line answers it, and the pair is rework instead."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-04", rewrite=("src/drafts.py",))
    out = _retro(root)
    assert out["rework"] == [] and [
        (q["change"], q["touches"], q["files"]) for q in out["rework_questions"]
    ] == [("002-keep-one-draft", "001-reopen-drafts", ["src/drafts.py"])]
    (tmp_path / "declared").mkdir()
    root = _repo(tmp_path / "declared")
    _close(root, "001-reopen-drafts", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-04", rewrite=("src/drafts.py",),
           reworks="[001]")  # fmt: skip
    out = _retro(root)
    assert [(r["change"], r["reworks"]) for r in out["rework"]] == [
        ("002-keep-one-draft", "001-reopen-drafts")
    ]
    assert out["rework_questions"] == []


def test_a_fixed_bug_s_introducer_is_rework_merged_with_a_declared_link(tmp_path) -> None:
    """R4: the bug a change fixed names the change that let it through; declared both ways, the
    pair is one entry with both reasons."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/drafts.py",))
    _close(root, "002-draft-titles", files=("src/titles.py",))
    fixes = (
        "Sdlc-Fixes: 2026-10-05-1 severity=high reported=2026-10-05 introduced_by=001",
        "Sdlc-Fixes: 2026-10-06-1 severity=low reported=2026-10-06 introduced_by=002-draft-titles",
    )
    _close(root, "003-keep-one-draft", closed="2026-10-08", reworks="[001]", trailers=fixes)
    rows = {r["reworks"]: r["via"] for r in _retro(root)["rework"]}
    assert rows == {
        "001-reopen-drafts": ["reworks", "bug 2026-10-05-1"],
        "002-draft-titles": ["bug 2026-10-06-1"],
    }


def test_a_closed_change_carries_its_fixes_line(tmp_path: Path) -> None:
    """168 R4: read as text, as `reworks:` is; [] with no line."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", fixes="[2026-10-01-1, 2026-10-02-1]")
    _close(root, "002-draft-sync")
    assert [c["fixes"] for c in _retro(root)["changes"]] == [["2026-10-01-1", "2026-10-02-1"], []]


def test_counts_tiers_impacts_and_what_history_cannot_measure(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", tier=1, impact="patch")
    _close(root, "002-keep-one-draft", tier=2, impact="minor")
    _close(root, "003-draft-titles", tier=2, impact="minor")
    out = _retro(root)
    assert out["tiers"] == {"1": 1, "2": 2}
    assert out["impacts"] == {"patch": 1, "minor": 2}
    assert any("findings caught at ship" in u["signal"] for u in out["unmeasured"])


def test_releases_are_the_tags_since_the_last_retrospective(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _git(root, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    _record(root, "2026-10-10")
    _close(root, "001-reopen-drafts")
    _git(root, "tag", "-a", "v0.2.0", "-m", "v0.2.0")
    assert [r["tag"] for r in _retro(root)["releases"]] == ["v0.2.0"]


def test_a_repo_with_nothing_still_answers(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    assert sdlc.retro.cmd_retro(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["since"] is None
    assert out["changes"] == out["rework"] == out["releases"] == out["problems"] == []
    assert out["ideas"] == {"open": 0, "oldest": None}


@pytest.mark.parametrize("tag", ["idea", "seed"])
def test_open_changes_and_seeds_are_counted(tmp_path: Path, tag: str) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc" / "work" / "004-open-one").mkdir(parents=True)
    (root / ".sdlc" / "work" / "004-open-one" / "intent.md").write_text(
        INTENT.format(id="004", slug="open-one", tier=1, impact="", created="2026-10-20",
                      title="open one").replace("stage: shipped", "stage: build"),
        encoding="utf-8",
    )  # fmt: skip
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        f"# Ideas\n\n## [2026-09-01-1] [{tag}] Old one\n\nx\n\n"
        f"## [2026-10-01-1] [{tag}] New one\n\nx\n"
        "\n## [2026-10-02-1] [building] Taken\n\nx\n",
        encoding="utf-8",
    )
    out = _retro(root)
    assert [(o["name"], o["title"], o["age_days"]) for o in out["open"]] == [
        ("004-open-one", "open one", 4)
    ]
    assert out["ideas"] == {"open": 2, "oldest": "2026-09-01"}


def test_prose_counts_each_of_the_plugins_skills(tmp_path: Path) -> None:
    prose = _retro(_repo(tmp_path))["prose"]
    assert set(prose["skills"]) == {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    retro = prose["skills"]["retro"]
    assert retro["est_tokens"] == retro["bytes"] // 4 and retro["script_calls"] >= 3
    # A skill's size is what every run reads; the files beside it are its branches.
    ship = prose["skills"]["ship"]
    skill = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    assert ship["lines"] == len(skill.splitlines())
    beside = {p.name for p in (ROOT / "skills" / "ship").glob("*.md")} - {"SKILL.md"}
    assert set(ship["branches"]) == beside and "branches" not in retro
    setup = prose["skills"]["setup"]
    skill = (ROOT / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
    assert setup["lines"] == len(skill.splitlines()) and set(setup["branches"]) == {"drafts.md"}
    assert prose["sdlc_py_lines"] > 1000


# ---------------------------------------------------------------- transcripts


def _home(tmp_path: Path, monkeypatch) -> Path:
    home = tmp_path / "home"
    (home / ".claude" / "projects").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    return home / ".claude" / "projects"


def _encoded(path: Path) -> str:
    return "".join(c if c.isalnum() else "-" for c in str(path))


def test_only_this_repos_own_transcript_folders_are_read(tmp_path, monkeypatch) -> None:
    main = tmp_path / "code" / "drafts"
    main.mkdir(parents=True)
    projects = _home(tmp_path, monkeypatch)
    enc = _encoded(main)
    for name in (enc, f"{enc}--claude-worktrees-007-x", f"{enc}-other", f"{enc}--claude-x"):
        (projects / name).mkdir()
    assert [p.name for p in sdlc._project_dirs(main)] == [enc, f"{enc}--claude-worktrees-007-x"]


SENTINEL = "a phrase only the person typed"


# ---------------------------------------------------------------- retro-commit


def _direction(root: Path) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text("# Direction\n\nGoals.\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True, exist_ok=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Ideas\n\n## [2026-10-24-1] [seed] X\n\nx\n"
    )


REGISTER = (
    "# Inbox\n\n"
    "## [2026-10-01-1] [idea] Reopen drafts\n\nWhy it matters.\n\nTheme: drafts\n\n"
    "## [2026-10-02-1] [bug] Drafts vanish\n\nWhat happens.\n\nSeverity: high\n\n"
    "## [2026-10-03-1] [nit] A small thing\n\nTheme: style\nPaths: `a.py`\nCost: S\nValue: low\n"
    "Raised by: 001-x (cost)\n\n"
    "## [2026-10-04-1] [building] Share drafts\n\nBuilding in .sdlc/work/002-share/.\n\n"
    "## [2026-10-05-1] [idea] Sync drafts\n\nOne an open change names.\n\nPriority: low\n"
)


def test_retro_lists_the_entries_it_may_rerank(tmp_path: Path) -> None:
    """064 R1: open ideas and bugs with their rank and theme; never a nit, nor an entry being
    built, by its tag or by an open change's `idea:`."""
    root = _repo(tmp_path)
    (root / ".sdlc" / "work" / "009-sync").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(REGISTER, encoding="utf-8")
    intent = "---\nid: 009\nslug: sync\ntier: 1\nstage: build\nidea: 2026-10-05-1\n---\n\n# Sync\n"
    (root / ".sdlc" / "work" / "009-sync" / "intent.md").write_text(intent, encoding="utf-8")
    got = _retro(root)["entries"]
    assert got == [
        {"id": "2026-10-01-1", "title": "Reopen drafts", "kind": "idea", "priority": None,
         "theme": "drafts", "age_days": 23},
        {"id": "2026-10-02-1", "title": "Drafts vanish", "kind": "bug", "priority": None,
         "theme": None, "age_days": 22},
    ]  # fmt: skip


@pytest.mark.parametrize(
    "edit, problem",
    [
        (lambda t: t.replace("Why it matters.\n", "Why it matters.\n\nPriority: high\n"), None),
        (lambda t: t.replace("Theme: drafts", "Theme: editing"), None),
        (lambda t: t.replace("Priority: low\n", ""), None),
        (lambda t: t + "\n## [2026-10-24-1] [idea] A new seed\n\nFrom the retro.\n", None),
        (lambda t: t.split("## [2026-10-05-1]")[0], "2026-10-05-1 was removed"),
        (lambda t: t.replace("Why it matters.", "Why it matters less."), "2026-10-01-1 changed"),
        (lambda t: t.replace("Severity: high", "Severity: low"), "2026-10-02-1 changed"),
        (lambda t: t.replace("[idea] Reopen drafts", "[idea] Reopen saved drafts"), "changed"),
    ],
)
def test_a_retro_only_reranks_and_appends_to_the_register(edit, problem) -> None:
    """064 R5: a retrospective sets `Priority:` and `Theme:` lines and appends its seeds; an entry
    leaves, or is rewritten, through /sdlc:idea or ship, never through a retro."""
    got = sdlc.retro.register_drift(REGISTER, edit(REGISTER))
    if problem is None:
        assert got == []
    else:
        assert len(got) == 1 and problem in got[0]


def test_retro_commit_refuses_a_register_entry_it_removed(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _direction(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    (root / ".sdlc" / "DIRECTION.md").write_text("# Direction\n\nNew goals.\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text("# Ideas\n", encoding="utf-8")
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert refusals == ["2026-10-24-1 was removed: retire it with /sdlc:idea, not a retro"]


def test_it_commits_the_direction_doc_and_the_seeds_and_nothing_else(tmp_path, capsys) -> None:
    root = _repo(tmp_path)
    _direction(root)
    code = sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24))
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out["refusals"]
    assert _git(root, "log", "-1", "--format=%s") == "Retrospective 2026-10-24"
    assert _git(root, "show", "--name-only", "--format=", "HEAD").splitlines() == [
        ".sdlc/DIRECTION.md",
        ".sdlc/retros/2026-10-24.md",
        ".sdlc/work/inbox.md",
    ]
    assert _git(root, "status", "--porcelain") == ""
    assert sdlc.last_retrospective(root, "main")["date"] == "2026-10-24"


def test_retro_commit_writes_the_report_it_would_print(tmp_path: Path, capsys) -> None:
    """R5, R6: the committed report is the one `retro --report` renders for the window the commit
    closes, figures from history and no placeholder left."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", trailers=(TOTALS.format(elapsed=90, agent=30),))
    _direction(root)
    shown = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 0
    committed = (root / ".sdlc" / "retros" / "2026-10-24.md").read_text(encoding="utf-8")
    assert committed == shown
    assert "{{" not in committed and "| 1 | 1 | 1h 30m | 1h 30m | 30m |" in committed


def test_retro_commit_refuses_a_report_already_there(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _direction(root)
    (root / ".sdlc" / "retros").mkdir()
    (root / ".sdlc" / "retros" / "2026-10-24.md").write_text("by hand\n", encoding="utf-8")
    before = _state(root)
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert refusals == [".sdlc/retros/2026-10-24.md already exists: retro-commit writes the "
                        "report itself"]  # fmt: skip
    assert _state(root) == before


def _stray(root: Path) -> None:
    _direction(root)
    (root / "README.md").write_text("edited\n", encoding="utf-8")


def _review_too(root: Path) -> None:
    """A retro's lesson for the review doc goes through a change and its ship review, never its
    own commit (nit 2026-11-04-1)."""
    _direction(root)
    (root / ".sdlc" / "REVIEW.md").write_text("# Review\n\nA new pass.\n", encoding="utf-8")


def _config_too(root: Path) -> None:
    _direction(root)
    (root / ".sdlc" / "config.toml").write_text('[review]\nsensitive = ["x/"]\n', encoding="utf-8")


def _nothing(root: Path) -> None:
    pass


def _today_already(root: Path) -> None:
    _record(root, "2026-10-24")
    _direction(root)


def _off_main(root: Path) -> None:
    _git(root, "switch", "-q", "-c", "elsewhere")
    _direction(root)


@pytest.mark.parametrize(
    "spoil, why",
    [
        (_stray, "also changed: README.md"),
        (_review_too, "also changed: .sdlc/REVIEW.md"),
        (_config_too, "also changed: .sdlc/config.toml"),
        (_nothing, "nothing to record"),
        (_today_already, "one a day"),
        (_off_main, "isn't on main"),
    ],
)
def test_it_refuses_before_writing_anything(tmp_path: Path, capsys, spoil, why) -> None:
    root = _repo(tmp_path)
    spoil(root)
    before = _state(root)
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    assert any(why in r for r in json.loads(capsys.readouterr().out)["refusals"])
    assert _state(root) == before


def test_it_refuses_from_a_change_worktree(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = tmp_path / "tree"
    _git(root, "worktree", "add", "-q", "-b", "001-x", str(tree))
    _direction(tree)
    before = _state(root), _state(tree)
    assert sdlc.retro.cmd_retro_commit(tree, date(2026, 10, 24)) == 1
    assert any("main checkout" in r for r in json.loads(capsys.readouterr().out)["refusals"])
    assert (_state(root), _state(tree)) == before


# ---------------------------------------------------------------- follow-through: ids and statuses


def _template_example() -> str:
    """The example the plugin's direction template shows, out of its quote and fence."""
    text = (ROOT / "templates" / "direction.md").read_text(encoding="utf-8")
    quoted = "\n".join(
        ln[2:] if ln.startswith("> ") else ln.lstrip(">") for ln in text.splitlines()
    )
    return quoted.split("```\n", 2)[1]


def test_the_templates_example_parses_to_its_ids() -> None:
    out = sdlc.direction_items(_template_example())
    assert out["problems"] == []
    assert [(i["id"], i["status"]) for i in out["items"]] == [
        ("G1", "open"), ("G2", "dropped"), ("M1", "open"), ("M2", "revised"), ("M3", "open"),
    ]  # fmt: skip
    m1 = next(i for i in out["items"] if i["id"] == "M1")
    assert m1["groups"] == {
        "changes": ["006"],
        "seeds": ["2026-10-01-2"],
    }
    g1 = next(i for i in out["items"] if i["id"] == "G1")
    assert (g1["serves"], m1["serves"]) == (["O1"], ["G1"])


def test_the_template_itself_holds_no_items() -> None:
    """The example is fenced: a scaffold copied as it is has nothing open to carry."""
    text = (ROOT / "templates" / "direction.md").read_text(encoding="utf-8")
    assert sdlc.direction_items(text)["items"] == []


DOC = """\
# Direction

## Goals

- G1. Drafts are never lost
- ~~G2. Drafts sync across devices~~ Done: 012 shipped it
- ~~G3. Offline drafts~~ Dropped: nobody asked for it

## Milestones

### M1. One draft per document

Saving twice keeps one.

Groups: 011-keep-one-draft, "Reopen drafts from the list"

### ~~M2. Draft titles~~ Revised → M3: titles come from the first line

### M3. Titles from the first line

Groups: 014
"""


def test_statuses_reasons_successors_and_next_ids() -> None:
    out = sdlc.direction_items(DOC)
    assert out["problems"] == []
    by = {i["id"]: i for i in out["items"]}
    assert by["G2"]["status"] == "done" and by["G2"]["reason"] == "012 shipped it"
    assert by["G3"]["status"] == "dropped"
    assert (by["M2"]["status"], by["M2"]["successor"]) == ("revised", "M3")
    assert by["M1"]["groups"] == {"changes": ["011"], "seeds": ["Reopen drafts from the list"]}
    assert by["M3"]["groups"]["changes"] == ["014"]
    assert out["next_ids"] == {"G": "G4", "M": "M4"}


@pytest.mark.parametrize(
    "line, problem",
    [
        ("- ~~G1. Gone~~", "with no Done, Dropped or Revised"),
        ("- ~~G1. Gone~~ Dropped:", "dropped without a reason"),
        ("- ~~G1. Gone~~ Revised → G9: narrower", "G9, which isn't in the doc"),
        ("- G1. Once\n- G1. Twice", "G1 is used twice"),
    ],
)
def test_a_bad_item_is_a_problem_not_a_raise(line: str, problem: str) -> None:
    out = sdlc.direction_items(f"## Goals\n\n{line}\n")
    assert any(problem in p for p in out["problems"]), out["problems"]


def test_a_doc_without_ids_or_no_doc_is_a_first_retrospective(tmp_path: Path) -> None:
    assert sdlc.direction_items("# Direction\n\n## Goals\n\nShip releases.\n")["items"] == []
    assert sdlc.direction_items("# Direction\n\n## Goals\n\nShip releases.\n")["problems"] == []
    direction = _retro(_repo(tmp_path))["direction"]
    assert direction["items"] == [] and direction["next_ids"] == {"G": "G1", "M": "M1"}


# ---------------------------------------------------------------- what goals and milestones serve


def test_a_goal_cites_the_outcomes_at_the_end_of_its_line() -> None:
    """092 R1: a trailing `(O1, O3)`, as text and in order; anything else in it cites nothing, and
    the title keeps it."""
    doc = (
        "## Goals\n\n"
        "- G6. Each rule is said once (O2)\n"
        "- G7. **Lean.** The loop costs less (O1, O3,O6)\n"
        "- ~~G8. Offline drafts (O4)~~ Dropped: nobody asked for it\n"
        "- G9. Drafts are kept (see below)\n"
        "- G10. Drafts sync\n"
        "- G11. Drafts merge (O1, later)\n"
        "- G12. Drafts survive a crash, a restart and a move between the\n"
        "  devices a person uses (O2, O5)\n"
        "- G13. Drafts are small\n\n  (O3)\n"
        "- ~~G14. Drafts are shared~~ Dropped: nobody asked, not even\n  for (O1)\n"
        "- G15. Drafts are fast\n- O1. In the wrong doc\n  (O4)\n"
    )
    by = {i["id"]: i for i in sdlc.direction_items(doc)["items"]}
    assert by["G6"]["serves"] == ["O2"] and by["G6"]["title"] == "Each rule is said once (O2)"
    assert by["G7"]["serves"] == ["O1", "O3", "O6"] and by["G7"]["name"] == "Lean"
    assert by["G8"]["serves"] == ["O4"] and by["G8"]["status"] == "dropped"
    assert by["G9"]["serves"] == [] and by["G10"]["serves"] == [] and by["G11"]["serves"] == []
    # A goal wrapped onto indented lines cites at the end of its last one; a later paragraph
    # isn't the goal's.
    assert by["G12"]["serves"] == ["O2", "O5"]
    assert by["G12"]["title"] == "Drafts survive a crash, a restart and a move between the"
    assert by["G13"]["serves"] == [] and by["G14"]["serves"] == [] and by["G15"]["serves"] == []


def test_a_milestone_cites_on_its_serves_line() -> None:
    """092 R2: the `G<n>`/`O<n>` tokens of a milestone's first `Serves:` line; other words are
    ignored, and a `Serves:` line anywhere but under a milestone is nothing."""
    doc = (
        "## Goals\n\n- G1. Drafts are kept (O1)\n\nServes: O9\n\n"
        "## Milestones\n\n"
        '### M1. One draft\n\nGroups: 011, "Reopen drafts"\nServes: G1, O4 and then some\n'
        "Serves: O5\n\n"
        "### M2. Titles\n\nGroups: 012\n\n"
        "## Next major release\n\nServes: O7\n"
    )
    by = {i["id"]: i for i in sdlc.direction_items(doc)["items"]}
    assert by["M1"]["serves"] == ["G1", "O4"]
    assert by["M1"]["groups"] == {"changes": ["011"], "seeds": ["Reopen drafts"]}
    assert by["M2"]["serves"] == [] and by["M2"]["groups"]["changes"] == ["012"]
    assert by["G1"]["serves"] == ["O1"]
    product = sdlc.product_items("## Outcomes\n\n- O1. **Setup.** Unaided\n\nServes: O2\n")
    assert product["items"][0]["serves"] == []


@pytest.mark.parametrize(
    "doc",
    [
        "## Goals\n\n- G1. Kept\n\n## Milestones\n\n### M1. One\n\nGroups: 011\n",
        "## Goals\n\n- G1. Kept (O1,\n\n## Milestones\n\n### M1. One\n\nServes: nonsense, G\n",
        "## Goals\n\n- G1. Kept (O99)\n\n## Milestones\n\n### M1. One\n\nServes: G9, O42\n",
    ],
)
def test_citations_never_add_a_problem(doc: str) -> None:
    """092 R3: no citation, a malformed one, or one naming nothing is reported by `retro`, never a
    format problem `retro-commit` would refuse."""
    assert sdlc.direction_items(doc)["problems"] == []


def test_retro_commit_takes_an_uncited_goal(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _direction(root)
    (root / ".sdlc" / "DIRECTION.md").write_text(
        "# Direction\n\n## Goals\n\n- G1. Drafts are kept\n\n## Milestones\n\n"
        "### M1. One draft\n\nGroups: 011\n",
        encoding="utf-8",
    )
    code = sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24))
    assert code == 0, capsys.readouterr().out
    assert _git(root, "log", "-1", "--format=%s") == "Retrospective 2026-10-24"


def test_each_grouped_seed_and_change_says_what_it_became(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Ideas\n\n## [2026-10-01-1] [seed] Still waiting\n\nx\n", encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _close(root, "011-keep-one-draft", idea="Reopen drafts from the list")
    (root / ".sdlc" / "work" / "012-open-one").mkdir(parents=True)
    (root / ".sdlc" / "work" / "012-open-one" / "intent.md").write_text(
        INTENT.format(id="012", slug="open-one", tier=1, impact="", created="2026-10-20",
                      title="open one").replace("stage: shipped", "stage: build"),
        encoding="utf-8",
    )  # fmt: skip
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(
        '## Milestones\n\n### M1. Drafts\n\nGroups: 011, 012, 099, "Reopen drafts from the list",'
        ' "Still waiting", "Thrown away"\n',
        encoding="utf-8",
    )
    rows = _retro(root)["direction"]["milestones"]["M1"]
    verdicts = {r["entry"]: (r["verdict"], r.get("change")) for r in rows}
    assert verdicts == {
        "011": ("closed", "011-keep-one-draft"),
        "012": ("open", None),
        "099": ("unknown", None),
        "Reopen drafts from the list": ("shipped", "011-keep-one-draft"),
        "Still waiting": ("open", None),
        "Thrown away": ("vanished", None),
    }


def test_a_seed_named_by_id_reads_shipped_open_or_vanished(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n## [2026-10-01-2] [seed] Still waiting\n\nx\n", encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _close(root, "011-keep-one-draft", idea="2026-10-01-1")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(
        "## Milestones\n\n### M1. Drafts\n\nGroups: 2026-10-01-1, 2026-10-01-2, 2026-10-01-3\n",
        encoding="utf-8",
    )
    rows = _retro(root)["direction"]["milestones"]["M1"]
    assert {r["entry"]: (r["verdict"], r.get("change")) for r in rows} == {
        "2026-10-01-1": ("shipped", "011-keep-one-draft"),
        "2026-10-01-2": ("open", None),
        "2026-10-01-3": ("vanished", None),
    }


def test_a_seed_shipped_by_an_idea_holding_its_heading_reads_shipped(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "011-keep-one-draft", idea="[2026-10-01] [seed] Reopen drafts from the list")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(
        '## Milestones\n\n### M1. Drafts\n\nGroups: "Reopen drafts from the list"\n',
        encoding="utf-8",
    )
    rows = _retro(root)["direction"]["milestones"]["M1"]
    assert [(r["verdict"], r.get("change")) for r in rows] == [("shipped", "011-keep-one-draft")]


def _committed_direction(root: Path, text: str) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Retrospective 2026-10-10")


@pytest.mark.parametrize(
    "new, refused",
    [
        ("## Goals\n\n- G2. Something else\n", "G1 was open and the new direction doc drops it"),
        ("## Goals\n\n- ~~G1. Ship~~ Done: 011\n", None),
        ("## Goals\n\n- G1. Ship, still\n", None),
        ("## Goals\n\n- ~~G1. Ship~~\n", "with no Done, Dropped or Revised"),
    ],
)
def test_retro_commit_refuses_a_doc_that_drops_an_open_id(tmp_path, capsys, new, refused) -> None:
    root = _repo(tmp_path)
    _committed_direction(root, "## Goals\n\n- G1. Ship\n- ~~G9. Old~~ Done: long ago\n")
    (root / ".sdlc" / "DIRECTION.md").write_text(new, encoding="utf-8")
    before = _git(root, "rev-parse", "HEAD")
    code = sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24))
    out = json.loads(capsys.readouterr().out)
    if refused:
        assert code == 1 and any(refused in r for r in out["refusals"]), out["refusals"]
        assert _git(root, "rev-parse", "HEAD") == before
    else:
        # G9 was already struck, so leaving it out is fine.
        assert code == 0, out["refusals"]


def test_the_first_direction_doc_has_nothing_to_carry(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text("## Goals\n\n- G1. Ship\n", encoding="utf-8")
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 0, capsys.readouterr().out


# ---------------------------------------------------------------- when one is due


def _due(root: Path, config: str = "") -> dict:
    if config:
        (root / ".sdlc").mkdir(exist_ok=True)
        (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    return sdlc.retro_due(root, sdlc.load_config(root)[0])


def _tag(root: Path, version: str) -> None:
    _git(root, "commit", "-q", "--allow-empty", "-m", f"Release {version}")
    _git(root, "tag", "-a", f"v{version}", "-m", f"v{version}")


def test_one_release_is_not_due_and_two_are(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _tag(root, "0.1.0")
    assert _due(root) == {"due": False, "why": [], "releases": ["v0.1.0"]}
    _tag(root, "0.2.0")
    due = _due(root)
    assert due["due"] and "2 releases since the start, with none yet" in due["why"][0]


def test_a_major_release_alone_is_due(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _tag(root, "1.4.0")
    _record(root, "2026-10-10")
    _tag(root, "2.0.0")
    due = _due(root)
    assert due["releases"] == ["v2.0.0"]
    assert due["why"] == ["major release v2.0.0"]


def test_releases_before_the_last_retrospective_dont_count(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _tag(root, "0.1.0")
    _tag(root, "0.2.0")
    _record(root, "2026-10-10")
    _tag(root, "0.3.0")
    assert _due(root) == {"due": False, "why": [], "releases": ["v0.3.0"]}


def test_zero_turns_the_count_off_but_not_a_major(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    for version in ("0.1.0", "0.2.0", "0.3.0"):
        _tag(root, version)
    assert not _due(root, "[retro]\nafter_releases = 0\n")["due"]
    _tag(root, "1.0.0")
    assert _due(root)["why"] == ["major release v1.0.0"]


def test_a_tag_template_without_a_version_counts_and_never_raises(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """`release.tag = "stable*"` names no version, so there is no major rule, only the count, and
    `status`, which asks on every run, still answers."""
    root = _repo(tmp_path)
    for name in ("stable-a", "stable-b"):
        _git(root, "commit", "-q", "--allow-empty", "-m", name)
        _git(root, "tag", "-a", name, "-m", name)
    due = _due(root, '[release]\ntag = "stable-*"\n')
    assert due["releases"] == ["stable-a", "stable-b"] and due["why"][0].startswith("2 releases")
    (root / ".sdlc" / "config.toml").write_text('[release]\ntag = "stable"\n', encoding="utf-8")
    _git(root, "tag", "-a", "stable", "-m", "stable")
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    assert sdlc.main() == 0
    assert "■ Problems" in capsys.readouterr().out


def test_an_item_written_as_the_other_kind_is_a_problem() -> None:
    out = sdlc.direction_items("## Milestones\n\n- M1. A milestone as a bullet\n\n### G1. A goal\n")
    assert out["items"] == []
    assert any("M1 is written as the other kind" in p and "`### M1.`" in p for p in out["problems"])
    assert any("G1 is written as the other kind" in p and "`- G1.`" in p for p in out["problems"])


def test_an_open_items_own_words_are_its_title_not_a_status() -> None:
    (item,) = sdlc.direction_items("- G1. Done: nothing yet, Revised → M2: maybe\n")["items"]
    assert item["status"] == "open"
    assert item["title"] == "Done: nothing yet, Revised → M2: maybe"
    assert (item["reason"], item["successor"]) == ("", None)


# ---------------------------------------------------------------- what close measured


def _measured(
    root: Path, name: str, agent: int, stops: int, extra: tuple = (), targets: str = "target=2"
) -> None:
    """Close a change, then give its `Close` commit the trailers close writes. `targets` is how
    its `Sdlc-Totals` states the target: one flat `target=2`, as close wrote before it recorded an
    allowance, unless a test says otherwise."""
    _close(root, name, tier=2)
    close = _git(root, "log", "-1", "--format=%B")
    _git(root, "commit", "-q", "--amend", "-m", close + "\n\n" + "\n".join([
        "Sdlc-Mode: manual",
        "Sdlc-Coverage: transcripts=2 stages=design,ship",
        f"Sdlc-Totals: elapsed=90 agent={agent} response=10 away=0 blocked=0 stops={stops} "
        f"required=5 {targets} permission=1 ship_runs=1 reenter=0 in=1 cache_read=100 out=10",
        f"Sdlc-Stage: design segments=1 elapsed=30 agent={agent} gate=1 extra=1 cache_read=50",
        f"Sdlc-Role: builder runs=1 agent={agent} cache_read=20 out=5",
        *extra,
    ]))  # fmt: skip


def test_retro_reads_rework_within_each_change_apart_from_follow_up_rework(tmp_path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-before-measuring", tier=2)
    _measured(root, "002-keep-one-draft", 10, 6, (
        "Sdlc-Rework: revise=0 check_fail_first=0 written=100 final=100 rewrite=100",
        "Sdlc-Happy: intent=yes design=yes build=yes test=unknown ship=yes close=yes first=5 of=5",
    ))  # fmt: skip
    _measured(root, "003-draft-titles", 20, 8, (
        "Sdlc-Rework: revise=2 check_fail_first=3 written=300 final=100 rewrite=300",
        "Sdlc-Happy: intent=yes design=no build=no test=yes ship=yes close=yes first=4 of=6",
        "Sdlc-Spike: segments=2 elapsed=40 agent=12 in=1 cache_create=1 cache_read=1 out=1 "
        "edits=5 lines=80",
    ))  # fmt: skip
    out = _retro(root)
    group = out["metrics"]["groups"]["tier 2, manual"]["in_change"]
    assert group["first_time"] == {"intent": 1.0, "design": 0.5, "build": 0.5, "test": 1.0,
                                   "ship": 1.0, "close": 1.0}  # fmt: skip
    assert group["all_first"] == 0.5
    assert group["rework"]["revise"] == 1 and group["rework"]["rewrite"] == 200
    assert group["spike"] == {"changes": 1, "segments": 2, "agent": 12, "edits": 5}
    assert "rework" in out, "retro's own rework, a later change fixing one, is still there"
    assert group["ship_fixed"] == 0.0


def test_a_ship_stopped_for_its_own_findings_counts_as_first_time(tmp_path) -> None:
    root = _repo(tmp_path)
    _measured(root, "001-keep-one-draft", 10, 6, (
        "Sdlc-Happy: intent=yes design=yes build=yes test=unknown ship=fixed close=yes "
        "first=5 of=5",
    ))  # fmt: skip
    _measured(root, "002-draft-titles", 10, 6, (
        "Sdlc-Happy: intent=yes design=yes build=yes test=unknown ship=no close=yes first=4 of=5",
    ))  # fmt: skip
    group = _retro(root)["metrics"]["groups"]["tier 2, manual"]["in_change"]
    assert group["first_time"]["ship"] == 0.5
    assert group["ship_fixed"] == 0.5


def test_retro_reads_what_close_measured_and_counts_what_it_didnt(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-before-measuring", tier=2)
    _measured(root, "002-keep-one-draft", agent=10, stops=6)
    _measured(root, "003-draft-titles", agent=20, stops=8)
    out = _retro(root)["metrics"]
    assert (out["captured"], out["uncaptured"]) == (2, 1)
    group = out["groups"]["tier 2, manual"]
    assert group["changes"] == 2
    assert group["median"]["agent"] == 15 and group["median"]["stops"] == 7
    assert group["target"] == 6, "an old flat target=2 is worked out again from required=5"
    assert group["median"]["over"] == 1
    assert group["stages"]["design"]["agent"] == 15
    assert group["roles"]["builder"] == {"runs": 2, "agent": 30, "cache_read": 40, "out": 10}


def test_old_and_new_trailers_read_against_their_own_targets(tmp_path: Path) -> None:
    """A commit that recorded its allowance is read as written; one from before is read against
    its own gates plus the allowance retro is given, never against its flat target=2."""
    root = _repo(tmp_path)
    _measured(root, "001-keep-one-draft", agent=10, stops=9)  # old: required=5 target=2
    _measured(root, "002-draft-titles", agent=10, stops=6, targets="target=5 allowance=0")
    changes = sdlc.closed_changes(root, None, "main")
    group = sdlc.retro.metrics_summary(changes, allowance=1)["groups"]["tier 2, manual"]
    assert group["target"] == 5.5, "6 for the old commit, 5 as the new one recorded"
    assert group["median"]["over"] == 2, "9 - 6 and 6 - 5"
    groups = sdlc.retro.metrics_summary(changes, allowance=3)["groups"]
    assert groups["tier 2, manual"]["target"] == 6.5


def test_ship_findings_are_read_from_the_changes_own_commit(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    nid, slug = "004", "found-things"
    folder = root / ".sdlc" / "work" / f"{nid}-{slug}"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        INTENT.format(id=nid, slug=slug, tier=2, impact="patch", created="2026-10-01",
                      title="found things"), encoding="utf-8",
    )  # fmt: skip
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship it", "-m", "Sdlc-Findings: important=1 nit=3 cost=2")
    _git(root, "rm", "-r", "-q", f".sdlc/work/{nid}-{slug}")
    _git(root, "commit", "-q", "-m", f"Close {nid}-{slug}", "-m",
         "Sdlc-Mode: manual\nSdlc-Totals: agent=5 stops=5 required=5 target=2")  # fmt: skip
    [rec] = sdlc.closed_changes(root, None, "main")
    assert rec["findings"] == {"important": 1, "nit": 3, "cost": 2}
    group = sdlc.retro.metrics_summary([rec])["groups"]["tier 2, manual"]
    found = group["findings"]
    assert (found["important"], found["nit"], found["preexisting"]) == (1, 3, 0)
    assert found["passes"]["cost"] == 2
    # A trailer from before dispositions is unknown there, never zero answers.
    assert found["answered"] == 0


NEW_FINDINGS = (
    "Sdlc-Findings: important=1 nit=2 preexisting=1 correctness=2 contract=0 cost=2 context=0 "
    "fixed=correctness:1 recorded=cost:1,correctness:1 wrong=cost:1 intentional=0 minor=0 "
    "fresh=2 fresh_wrong=1"
)


def test_findings_with_dispositions_add_up_beside_an_old_trailer(tmp_path: Path) -> None:
    """Counts add from every trailer; dispositions only from the ones that carry them."""
    root = _repo(tmp_path)
    for nid, slug, trailer in (
        ("004", "old-trailer", "Sdlc-Findings: important=1 nit=3 cost=2"),
        ("005", "new-trailer", NEW_FINDINGS),
    ):
        folder = root / ".sdlc" / "work" / f"{nid}-{slug}"
        folder.mkdir(parents=True)
        (folder / "intent.md").write_text(
            INTENT.format(id=nid, slug=slug, tier=2, impact="patch", created="2026-10-01",
                          title=slug), encoding="utf-8",
        )  # fmt: skip
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "Ship it", "-m", trailer)
        _git(root, "rm", "-r", "-q", f".sdlc/work/{nid}-{slug}")
        _git(root, "commit", "-q", "-m", f"Close {nid}-{slug}", "-m",
             "Sdlc-Mode: manual\nSdlc-Totals: agent=5 stops=5 required=5 target=2")  # fmt: skip
    recs = sdlc.closed_changes(root, None, "main")
    found = sdlc.retro.metrics_summary(recs)["groups"]["tier 2, manual"]["findings"]
    assert (found["important"], found["nit"], found["preexisting"]) == (2, 5, 1)
    assert found["passes"]["correctness"] == 2 and found["passes"]["cost"] == 4
    assert found["answered"] == 1
    d = found["dispositions"]
    assert d["fixed"]["correctness"] == 1 and d["wrong"]["cost"] == 1
    assert d["recorded"] == {"correctness": 1, "contract": 0, "cost": 1, "context": 0}
    assert sum(d["minor"].values()) == 0
    # The fresh reviewer's numbers come only from the trailer that carries them.
    assert (found["fresh"], found["fresh_wrong"], found["fresh_counted"]) == (2, 1, 1)


# ---------------------------------------------------------------- the product doc's outcomes

PRODUCT = """\
# Product

## Outcomes

- O1. **Unaided setup.** A new user finishes setup unaided
- ~~O2. Drafts sync across devices~~ Dropped: nobody asked for it
- O3. **Exports.** Exports open in a spreadsheet
"""


def test_outcomes_have_statuses_and_next_ids() -> None:
    out = sdlc.product_items(PRODUCT + "- ~~O4. Teams share drafts~~ Revised → O3: exports\n")
    assert out["problems"] == []
    assert [(i["id"], i["status"]) for i in out["items"]] == [
        ("O1", "open"), ("O2", "dropped"), ("O3", "open"), ("O4", "revised"),
    ]  # fmt: skip
    assert out["next_ids"] == {"O": "O5"}


@pytest.mark.parametrize(
    "parse, text, problem",
    [
        (sdlc.direction_items, "- O1. An outcome\n", "outcomes belong in the product doc"),
        (sdlc.product_items, "- G1. A goal\n", "goals belong in the direction doc"),
        (sdlc.product_items, "### O1. A heading\n", "O1 is written as the other kind"),
    ],
)  # fmt: skip
def test_an_id_in_the_wrong_doc_or_form_is_a_problem(parse, text: str, problem: str) -> None:
    out = parse(text)
    assert out["items"] == [] and any(problem in p for p in out["problems"]), out["problems"]


def test_the_default_product_doc_holds_no_outcomes_and_asks_for_them() -> None:
    """Its example is quoted and fenced: copied as it is, it has nothing open to carry."""
    path = ROOT / "defaults" / "PRODUCT.md"
    text = path.read_text(encoding="utf-8")
    assert sdlc.product_items(text) == {"items": [], "problems": [], "next_ids": {"O": "O1"}}
    assert sdlc.is_unfilled(path), "its `<` prompts are what setup fills"


def _product(root: Path, text: str = PRODUCT, evidence: list[str] | None = None) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "PRODUCT.md").write_text(text, encoding="utf-8")
    if evidence is not None:
        (root / ".sdlc").mkdir(exist_ok=True)
        listed = ", ".join(json.dumps(c) for c in evidence)
        (root / ".sdlc" / "config.toml").write_text(f"[retro]\nevidence = [{listed}]\n", "utf-8")


def _serving(name: str, serves: str | None, moves: str = "") -> str:
    nid, slug = name.split("-", 1)
    text = INTENT.format(
        id=nid, slug=slug, tier=1, impact="patch", created="2026-10-01", title=slug
    )
    if serves is not None:
        text = text.replace("idea:\n", f"idea:\nserves: {serves}\n", 1)
    return text.replace("One draft.\n", f"One draft.\n{moves}", 1)


def test_with_no_product_doc_there_is_no_product_block(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-a")
    out = _retro(root)
    assert out["product"] is None
    assert out["changes"][0]["serves"] is None and out["changes"][0]["moves"] == []


def test_each_change_says_what_it_serves_and_what_should_move(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _product(root)
    _close(root, "001-a", intent=_serving("001-a", "[O1, O3]", "- **Moves O1, O3:** setups up\n"))
    _close(root, "002-b", intent=_serving("002-b", None))
    _close(root, "003-c", intent=_serving("003-c", "none"))
    out = _retro(root)
    a = out["changes"][0]
    assert a["serves"] == ["O1", "O3"]
    assert a["moves"] == [{"ids": ["O1", "O3"], "text": "setups up"}]
    product = out["product"]
    assert product["outcomes"]["O1"] == {
        "closed": [{"change": "001-a", "release": None, "moves": ["setups up"]}], "open": [],
    }  # fmt: skip
    assert "O2" not in product["outcomes"], "only open outcomes are scored"
    assert product["unlinked"] == ["002-b"] and product["none"] == ["003-c"]
    assert product["unserved"] == []
    assert product["next_ids"] == {"O": "O4"}


def test_an_outcome_nothing_serves_is_unserved(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _product(root)
    _close(root, "001-a", intent=_serving("001-a", "[O1]"))
    assert _retro(root)["product"]["unserved"] == ["O3"]


def test_an_open_change_serving_a_struck_outcome_is_stale(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _product(root)
    folder = root / ".sdlc" / "work" / "004-open"
    folder.mkdir(parents=True)
    text = _serving("004-open", "[O2, O3]").replace("stage: shipped", "stage: build")
    (folder / "intent.md").write_text(text, encoding="utf-8")
    product = _retro(root)["product"]
    assert product["stale"] == [{"change": "004-open", "outcome": "O2"}]
    assert product["outcomes"]["O3"]["open"] == ["004-open"]


COVERAGE = """\
# Direction

## Goals

- G1. Drafts are kept (O1)
- G2. Drafts sync (O2)
- G3. Drafts are fast
- ~~G4. Offline drafts~~ Dropped: nobody asked for it
- G5. Drafts merge (O9)

## Milestones

### M1. Through its goal

Serves: G1

### M2. Cites nothing

Groups: 011

### M3. An unknown goal

Serves: G9

### M4. A struck outcome

Serves: G2, O2

### M5. A goal that cites nothing

Serves: G3
"""


def test_retro_names_goals_and_milestones_that_reach_no_open_outcome(tmp_path: Path) -> None:
    """092 R5: each open goal and milestone whose citations, a milestone's through its goals too,
    reach no open outcome, with why; in the doc's order, never a struck one."""
    root = _repo(tmp_path)
    _product(root)
    (root / ".sdlc" / "DIRECTION.md").write_text(COVERAGE, encoding="utf-8")
    got = [
        (r["id"], r["kind"], r["serves"], r["reaches"], r["why"])
        for r in _retro(root)["product"]["uncited"]
    ]
    assert got == [
        ("G2", "goal", ["O2"], ["O2"], "closed"),
        ("G3", "goal", [], [], "none"),
        ("G5", "goal", ["O9"], ["O9"], "unknown"),
        ("M2", "milestone", [], [], "none"),
        ("M3", "milestone", ["G9"], [], "unknown"),
        ("M4", "milestone", ["G2", "O2"], ["O2"], "closed"),
        ("M5", "milestone", ["G3"], [], "none"),
    ]
    row = _retro(root)["product"]["uncited"][0]
    assert (row["name"], row["title"]) == ("", "Drafts sync (O2)")


def _none_change(root: Path, name: str, seeds: tuple[tuple[str, str | None], ...] = ()) -> None:
    """A change serving no outcome, built from `seeds` (id, theme): they are filed on main first,
    and its ship commit deletes them from the register, as ship does, so only the register at
    its base still holds them."""
    register = root / ".sdlc" / "work" / "inbox.md"
    register.parent.mkdir(parents=True, exist_ok=True)
    text = register.read_text(encoding="utf-8") if register.exists() else "# Inbox\n\n"
    filed = text
    for sid, theme in seeds:
        filed += f"## [{sid}] [idea] Seed {sid}\n\nWhy.\n\n" + (
            f"Theme: {theme}\n\n" if theme else ""
        )
    if seeds:
        register.write_text(filed, encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "seeds")
        register.write_text(text, encoding="utf-8")
    intent = _serving(name, "none")
    if seeds:
        listed = ", ".join(sid for sid, _ in seeds)
        intent = intent.replace("idea:\n", f"idea: [{listed}]\n", 1)
    _close(root, name, intent=intent, based=True)


def test_none_changes_are_grouped_by_their_seeds_themes(tmp_path: Path) -> None:
    """092 R6: each `none` change under every distinct theme its seeds had at its base, once;
    with none of them themed, `(no theme)`. Rows by count, then theme."""
    root = _repo(tmp_path)
    _product(root)
    _none_change(root, "001-a", (("2026-10-01-1", "cleanup"),))
    _none_change(root, "002-b", (("2026-10-01-2", "cost"), ("2026-10-01-3", "cost")))
    _none_change(root, "003-c")
    _none_change(root, "004-d", (("2026-10-01-4", "cost"), ("2026-10-01-5", None)))
    _close(root, "005-e", intent=_serving("005-e", "[O1]"))
    assert "Theme:" not in (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    product = _retro(root)["product"]
    assert product["none"] == ["001-a", "002-b", "003-c", "004-d"]
    assert product["none_themes"] == [
        {"theme": "cost", "changes": ["002-b", "004-d"], "recurring": False},
        {"theme": "(no theme)", "changes": ["003-c"], "recurring": False},
        {"theme": "cleanup", "changes": ["001-a"], "recurring": False},
    ]


@pytest.mark.parametrize(
    "themes, recurring",
    [(("cleanup", "cleanup"), False), (("cleanup",) * 3, True), ((None,) * 3, False)],
)
def test_a_theme_recurs_at_three_none_changes(tmp_path: Path, themes, recurring: bool) -> None:
    """092 R7: three `none` changes under one theme in the window; `(no theme)` never recurs."""
    root = _repo(tmp_path)
    _product(root)
    for n, theme in enumerate(themes, 1):
        _none_change(root, f"00{n}-c{n}", ((f"2026-10-0{n}-1", theme),))
    (row,) = _retro(root)["product"]["none_themes"]
    assert len(row["changes"]) == len(themes) and row["recurring"] is recurring


def test_a_change_carries_the_first_release_that_holds_it(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-a")
    assert _retro(root)["changes"][0]["release"] is None
    _git(root, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
    _close(root, "002-b")
    _git(root, "tag", "-a", "v1.1.0", "-m", "v1.1.0")
    assert [c["release"] for c in _retro(root)["changes"]] == ["v1.0.0", "v1.1.0"]


# ---------------------------------------------------------------- evidence


def test_evidence_is_each_commands_output_and_never_a_raise(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sdlc.retro, "EVIDENCE_LIMIT", 10)
    monkeypatch.setattr(sdlc.retro, "EVIDENCE_TIMEOUT", 0.5)
    rows = sdlc.retro._evidence(
        tmp_path,
        [
            "echo 3 signups",
            "echo nope >&2; exit 3",
            "printf '%020d' 0",
            "sleep 5",
            "printf '\\377'",
        ],
    )
    ok, failed, long, slow, binary = rows
    assert (binary["exit"], binary["output"], binary["error"]) == (0, "�", None)
    assert (ok["exit"], ok["output"], ok["error"]) == (0, "3 signups\n", None)
    assert failed["exit"] == 3 and failed["error"] == "exited 3: nope"
    assert long["output"] == "0" * 10 and long["truncated"] is True
    assert slow["exit"] is None and "timed out after 0.5s" in slow["error"]


def test_retro_runs_evidence_only_with_a_product_doc(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _product(root, evidence=["echo 3 signups"])
    (root / ".sdlc" / "PRODUCT.md").unlink()
    assert _retro(root)["product"] is None
    _product(root)
    (row,) = _retro(root)["product"]["evidence"]
    assert row["output"] == "3 signups\n"


def test_nothing_but_retro_runs_evidence(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _product(root, evidence=["touch ran-evidence"])
    monkeypatch.chdir(root)
    for command in ("check", "status", "config", "readiness"):
        monkeypatch.setattr("sys.argv", ["sdlc.py", command])
        sdlc.main()
        assert not (root / "ran-evidence").exists(), f"{command} ran the evidence"
    capsys.readouterr()
    _retro(root)
    assert (root / "ran-evidence").exists()


# ---------------------------------------------------------------- test times (130)


def _junit(path: Path, seconds: list[float | None], skipped: int = 0) -> Path:
    """A JUnit XML report with a case per entry of `seconds` (None: no `time`), and `skipped`
    skipped ones, neutral ids."""
    rows = [
        f'<testcase classname="tests.test_drafts" name="test_{n}" file="tests/test_drafts.py"'
        + ("" if s is None else f' time="{s}"')
        + "/>"
        for n, s in enumerate(seconds)
    ]
    rows += [
        f'<testcase classname="tests.test_sync" name="test_skip_{n}" time="0.2">'
        "<skipped/></testcase>"
        for n in range(skipped)
    ]
    path.write_text(
        '<?xml version="1.0"?>\n<testsuites><testsuite name="t">\n'
        + "\n".join(rows)
        + "\n</testsuite></testsuites>\n",
        encoding="utf-8",
    )
    return path


def test_test_times_get_their_own_limits(tmp_path: Path, monkeypatch) -> None:
    """R3: a suite's report runs to megabytes and minutes; the evidence limits never cut it."""
    monkeypatch.setattr(sdlc.retro, "EVIDENCE_LIMIT", 10)
    monkeypatch.setattr(sdlc.retro, "EVIDENCE_TIMEOUT", 0.2)
    monkeypatch.setattr(sdlc.retro, "TIMES_LIMIT", 100_000)
    monkeypatch.setattr(sdlc.retro, "TIMES_TIMEOUT", 10)
    _junit(tmp_path / "junit.xml", [0.5, 0.25])
    times = sdlc.retro._times(tmp_path, ["sleep 0.5; cat junit.xml"])
    (row,) = times["commands"]
    assert (row["error"], row["truncated"], row["cases"]) == (None, False, 2), row
    assert times["state"] == "ok"
    (row,) = sdlc.retro._evidence(tmp_path, ["sleep 0.5; cat junit.xml"])
    assert "timed out after 0.2s" in row["error"], "evidence keeps its own limits"


def test_times_unset_failed_and_ok(tmp_path: Path) -> None:
    """R5: no commands is `unset`; no command giving a case is `failed`, each row saying why; one
    that gives cases is `ok`, a failing one beside it still listed."""
    assert sdlc.retro._times(tmp_path, []) == {"state": "unset", "commands": []}
    (tmp_path / "bad.xml").write_text("not xml", encoding="utf-8")
    _junit(tmp_path / "junit.xml", [2.0, 1.0, None], skipped=2)
    failed = sdlc.retro._times(tmp_path, ["exit 4", "cat bad.xml"])
    assert failed["state"] == "failed"
    assert [r["error"].split(":")[0] for r in failed["commands"]] == ["exited 4", "not JUnit XML"]
    ok = sdlc.retro._times(tmp_path, ["exit 4", "cat junit.xml"])
    assert ok["state"] == "ok"
    assert [r["cases"] for r in ok["commands"]] == [None, 5]
    assert (ok["tests"], ok["skipped"], ok["untimed"]) == (5, 2, 1)
    assert (ok["seconds"], ok["median"]) == (3.0, 1.5)
    assert ok["slowest"][0] == {
        "test": "tests.test_drafts::test_0", "file": "tests/test_drafts.py", "seconds": 2.0,
        "share": 0.667,
    }  # fmt: skip
    assert [r["test"] for r in ok["slowest"]] == ["tests.test_drafts::test_0",
                                                  "tests.test_drafts::test_1"]  # fmt: skip


def test_a_truncated_report_is_a_failure_not_a_partial_read(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sdlc.retro, "TIMES_LIMIT", 200)
    _junit(tmp_path / "junit.xml", [1.0] * 20)
    times = sdlc.retro._times(tmp_path, ["cat junit.xml"])
    (row,) = times["commands"]
    assert times["state"] == "failed" and row["truncated"] is True and row["cases"] is None
    assert "truncated" in row["error"]


@pytest.mark.parametrize(
    ("slowest", "named"),
    [(4.0, True), (3.9, False), (0.9, False)],
)
def test_slow_needs_ten_times_the_median_and_a_second(tmp_path, slowest, named) -> None:
    """R5: `slow` is a slowest row at least `SLOW_OVER` times the median and `SLOW_LEAST` seconds;
    twenty cases at 0.4 s and 0.09 s set the median."""
    rest = [0.4] * 20 if slowest > 1 else [0.09] * 20
    _junit(tmp_path / "junit.xml", [slowest, *rest])
    times = sdlc.retro._times(tmp_path, ["cat junit.xml"])
    assert [r["seconds"] for r in times["slow"]] == ([slowest] if named else [])
    assert times["slowest"][0]["seconds"] == slowest


def test_the_tests_block_stays_small_however_large_the_suite(tmp_path: Path) -> None:
    """R6: 5,000 cases, and the block holds aggregates, at most `TOP` rows and no raw output."""
    root = _repo(tmp_path)
    _junit(root / "junit.xml", [round(0.001 * n, 3) for n in range(1, 5001)])
    _config(root, '[retro]\ntest_times = ["cat junit.xml"]\n')
    out = _retro(root)
    assert out["tests"]["times"]["tests"] == 5000
    assert "output" not in out["tests"]["times"]["commands"][0]
    assert len(json.dumps(out["tests"])) < 8000


def _drifting(root: Path, test: str = "tests/test_drafts.py") -> None:
    """A test closed beside its code, then three changes that move the code without it."""
    _close(root, "001-reopen-drafts", files=(test, "src/drafts.py"))
    for n, slug in enumerate(("draft-titles", "draft-sync", "keep-one-draft"), 2):
        _close(root, f"00{n}-{slug}", files=("src/drafts.py",))


def test_drift_follows_the_hosts_test_paths(tmp_path: Path) -> None:
    """R8: kinds are told the host's way, from the lookback the architecture pass reads."""
    root = _repo(tmp_path)
    _drifting(root, "checks/drafts.sh")
    assert _retro(root)["tests"]["drifted"] == []
    _config(root, '[retro]\ntest_paths = ["checks/"]\n')
    assert _retro(root)["tests"]["drifted"] == [
        {"file": "checks/drafts.sh", "last_change": "001-reopen-drafts",
         "code": ["src/drafts.py"], "later": 3},
    ]  # fmt: skip


def test_no_base_branch_means_no_drift(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _drifting(root)
    cfg = sdlc.load_config(root)[0]
    cfg["git"]["base"] = None
    assert sdlc.retro._tests(root, cfg, None)["drifted"] is None


def test_due_is_slow_or_drifted(tmp_path: Path) -> None:
    """R9: a pruning pass is due exactly when a test is slow or drifted."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("tests/test_drafts.py", "src/drafts.py"))
    assert _retro(root)["tests"]["due"] is False
    _junit(root / "junit.xml", [5.0, *[0.1] * 20])
    _config(root, '[retro]\ntest_times = ["cat junit.xml"]\n')
    tests = _retro(root)["tests"]
    assert (tests["due"], tests["drifted"], len(tests["times"]["slow"])) == (True, [], 1)
    _config(root, "")
    for n, slug in enumerate(("draft-titles", "draft-sync", "keep-one-draft"), 2):
        _close(root, f"00{n}-{slug}", files=("src/drafts.py",))
    tests = _retro(root)["tests"]
    assert (tests["due"], tests["times"]["state"], len(tests["drifted"])) == (True, "unset", 1)


def test_the_unmeasured_test_signals_are_listed(tmp_path: Path) -> None:
    signals = [u["signal"] for u in _retro(_repo(tmp_path))["unmeasured"]]
    assert "a test a newer one repeats" in signals
    assert "a test that passes for the wrong reason" in signals


def test_retro_with_test_times_writes_nothing(tmp_path: Path, capsys) -> None:
    """R10: the retrospective runs the host's report and leaves the tree as it found it."""
    root = _repo(tmp_path)
    _junit(root / "junit.xml", [5.0, *[0.1] * 20])
    _config(root, '[retro]\ntest_times = ["cat junit.xml"]\n')
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a report")
    _drifting(root)
    before = _state(root)
    assert sdlc.retro.cmd_retro(root) == 0
    tests = json.loads(capsys.readouterr().out)["tests"]
    assert tests["due"] and tests["times"]["state"] == "ok" and tests["drifted"]
    assert _state(root) == before


def test_retro_commit_refuses_a_changed_test_file(tmp_path: Path, capsys) -> None:
    """R10: a test edited beside the direction doc is a stray path, refused before anything."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("tests/test_drafts.py", "src/drafts.py"))
    _direction(root)
    (root / "tests" / "test_drafts.py").write_text("pruned\n", encoding="utf-8")
    before = _state(root)
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert any("also changed: tests/test_drafts.py" in r for r in refusals), refusals
    assert _state(root) == before


def test_reference_names_test_times_and_its_format() -> None:
    """R12: the sample, the commands `sdlc.py` runs, and *Retrospectives*' contract."""
    text = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    sample = text.split("[retro]\n")[1].split("\n[")[0]
    assert "test_times = [" in sample
    runs = " ".join(text.split("The commands `sdlc.py` runs itself")[1].split(")")[0].split())
    assert "`retro.test_times`" in runs
    retros = " ".join(text.split("## Retrospectives")[1].split("\n## ")[0].split())
    for needed in ("`retro.test_times`", "JUnit XML", "`<testcase>`", "600", "5,000,000",
                   "`tests`", "`drifted`", "`slow`", "`due`", "pruning pass"):  # fmt: skip
        assert needed in retros, needed


def test_nothing_but_retro_runs_test_times(tmp_path: Path, capsys, monkeypatch) -> None:
    """R2: `check`, `status`, `config`, `readiness` and `retro --report` never run it."""
    root = _repo(tmp_path)
    _config(root, '[retro]\ntest_times = ["touch ran-times"]\n')
    monkeypatch.chdir(root)
    for argv in (["check"], ["status"], ["config"], ["readiness"], ["retro", "--report"]):
        monkeypatch.setattr("sys.argv", ["sdlc.py", *argv])
        sdlc.main()
        assert not (root / "ran-times").exists(), f"{argv} ran test_times"
    capsys.readouterr()
    _retro(root)
    assert (root / "ran-times").exists()


# ---------------------------------------------------------------- architecture


def _config(root: Path, text: str) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(text, encoding="utf-8")


def test_each_change_is_sized_by_kind(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/a.py", "tests/test_a.py", "docs/a.md"))
    (rec,) = _retro(root)["changes"]
    assert rec["files"] == 4  # the intent too, as before
    assert (rec["added"] + rec["deleted"], rec["deleted"]) == (rec["lines"], 0)
    assert rec["by_kind"]["code"] == {"files": 1, "added": 1, "deleted": 0}
    assert rec["by_kind"]["tests"]["files"] == 1
    assert rec["by_kind"]["docs"]["files"] == 2


def test_the_hosts_paths_replace_the_conventions(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _config(root, '[retro]\ntest_paths = ["checks/"]\ndoc_paths = ["*.txt"]\n')
    _close(root, "001-reopen-drafts", files=("checks/a.sh", "tests/test_a.py", "notes.txt"))
    out = _retro(root)
    by_kind = out["changes"][0]["by_kind"]
    assert by_kind["tests"]["files"] == 1
    assert by_kind["docs"]["files"] == 1
    # tests/test_a.py, the intent (a .md, no longer docs) and the config the change commits
    assert by_kind["code"]["files"] == 3
    assert out["architecture"]["kinds"] == {"tests": ["checks/"], "docs": ["*.txt"]}


def test_a_non_ascii_hotspot_on_the_base_branch_is_not_gone(tmp_path) -> None:
    """F1: the hotspots' paths come from numstat, quoted by git's default; the path listing that
    says `gone` must quote the same way, or a file still there reads as deleted."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/café.py",))
    _close(root, "002-draft-titles", files=("src/café.py",))
    hot = _retro(root)["architecture"]["hotspots"]
    assert hot[0]["changes"] == 2 and hot[0]["gone"] is False, hot[0]


def test_hotspots_look_back_past_the_retrospective_while_size_stays_in_it(tmp_path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/a.py",))
    _record(root)
    _close(root, "002-draft-titles", files=("src/a.py", "src/b.py"))
    arch = _retro(root)["architecture"]
    assert arch["lookback"] == {
        "changes": 2,
        "first": "001-reopen-drafts",
        "last": "002-draft-titles",
    }
    assert arch["hotspots"][0] == {
        "file": "src/a.py", "changes": 2, "lines_changed": 2, "lines": 2, "gone": False,
    }  # fmt: skip
    assert not any(h["file"].startswith(".sdlc/work/") for h in arch["hotspots"])
    assert arch["size"]["1"]["changes"] == 1


def test_growth_is_against_the_last_retrospective_and_null_without_one(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("src/a.py",))
    arch = _retro(root)["architecture"]
    assert arch["totals"]["then"] is None
    assert all(r["growth"] is None for r in arch["largest"])
    _record(root)
    _close(root, "002-draft-titles", files=("src/a.py",))
    arch = _retro(root)["architecture"]
    (row,) = [r for r in arch["largest"] if r["file"] == "src/a.py"]
    assert (row["lines"], row["then"], row["growth"]) == (2, 1, 1)
    assert arch["totals"]["now"]["code"] == {"files": 1, "lines": 2}
    assert arch["totals"]["then"]["code"] == {"files": 1, "lines": 1}


def test_the_hosts_indicators_run_without_a_product_doc(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _retro(root)["architecture"]["host"] == []
    _config(root, '[retro]\nindicators = ["echo 7 cycles"]\n')
    (row,) = _retro(root)["architecture"]["host"]
    assert (row["output"], row["error"]) == ("7 cycles\n", None)
    assert _retro(root)["product"] is None


def test_the_architecture_block_stays_small_however_large_the_repo(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    for n in range(200):
        path = root / "src" / f"m{n:03d}.py"
        path.parent.mkdir(exist_ok=True)
        path.write_text("x\n" * (n + 1), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "many files")
    for n in range(40):
        files = tuple(f"src/m{(n * 5 + k) % 200:03d}.py" for k in range(5))
        _close(root, f"{n + 1:03d}-change-{n}", files=files)
    arch = _retro(root)["architecture"]
    assert arch["lookback"]["changes"] == sdlc.retro.ARCH_LOOKBACK
    assert len(json.dumps(arch)) < 8000


def test_no_base_branch_means_no_architecture(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    cfg = sdlc.load_config(root)[0]
    cfg["git"]["base"] = None
    assert sdlc.retro._architecture(root, cfg, None, [], sdlc.retro._kind(cfg)) is None


# ---------------------------------------------------------------- retro-commit and outcomes


def test_retro_commit_takes_the_product_doc_too(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _product(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "product doc")
    _direction(root)
    text = PRODUCT.replace(
        "- O1. **Unaided setup.** A new user finishes setup unaided", "- ~~O1. Setup~~ Done: 001"
    )
    (root / ".sdlc" / "PRODUCT.md").write_text(text, encoding="utf-8")
    code = sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24))
    assert code == 0, capsys.readouterr().out
    assert sorted(_git(root, "show", "--name-only", "--format=", "HEAD").splitlines()) == [
        ".sdlc/DIRECTION.md", ".sdlc/PRODUCT.md", ".sdlc/retros/2026-10-24.md",
        ".sdlc/work/inbox.md",
    ]  # fmt: skip


def test_retro_commit_refuses_a_product_doc_that_drops_an_open_outcome(tmp_path, capsys) -> None:
    root = _repo(tmp_path)
    _product(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "product doc")
    _product(
        root, PRODUCT.replace("- O1. **Unaided setup.** A new user finishes setup unaided\n", "")
    )
    before = _git(root, "rev-parse", "HEAD")
    assert sdlc.retro.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert any("O1 was open and the new product doc drops it" in r for r in refusals), refusals
    assert _git(root, "rev-parse", "HEAD") == before


def test_retro_compares_tool_prompts_only_where_close_recorded_them(tmp_path: Path) -> None:
    """A `Close` commit from before prompts were named carries `permission=`, which counted
    questions and plan approvals: it is unrecorded for prompts, never zero, and never summed in."""
    root = _repo(tmp_path)
    _measured(root, "001-keep-one-draft", 10, 6)  # old: permission=1, no prompts=
    _close(root, "002-draft-titles", tier=2)
    close = _git(root, "log", "-1", "--format=%B")
    _git(root, "commit", "-q", "--amend", "-m", close + "\n\n" + "\n".join([
        "Sdlc-Mode: manual",
        "Sdlc-Coverage: transcripts=1 stages=design,ship",
        "Sdlc-Totals: elapsed=60 agent=20 response=5 away=0 blocked=0 stops=6 required=5 "
        "target=6 allowance=1 prompts=3 prompt_modes=default ship_runs=1 reenter=0 in=1 "
        "cache_read=100 out=10",
        "Sdlc-Prompt: Bash:git:push asked=2 rejected=1",
        "Sdlc-Prompt: Edit asked=1 rejected=0",
    ]))  # fmt: skip
    m = _retro(root)["metrics"]
    assert m["groups"]["tier 2, manual"]["median"]["prompts"] == 3, "the old commit isn't 0"
    assert m["prompts"] == {
        "recorded": 1,
        "names": {
            "Bash:git:push": {"asked": 2, "rejected": 1, "changes": 1},
            "Edit": {"asked": 1, "rejected": 0, "changes": 1},
        },
        "modes": {"default": 1},
    }


def test_retro_reads_extra_stop_kinds_only_where_close_classified_them(tmp_path: Path) -> None:
    """An older `Close` commit counted harness entries and other commands as `extra`, with no
    kinds: it is unrecorded here, never none. A newer one's `Sdlc-Extra` lines add up by kind."""
    root = _repo(tmp_path)
    _measured(root, "001-keep-one-draft", 10, 6)  # old: no harness= on Sdlc-Totals
    _close(root, "002-draft-titles", tier=2)
    close = _git(root, "log", "-1", "--format=%B")
    _git(root, "commit", "-q", "--amend", "-m", close + "\n\n" + "\n".join([
        "Sdlc-Mode: manual",
        "Sdlc-Coverage: transcripts=1 stages=design,ship",
        "Sdlc-Totals: elapsed=60 agent=20 response=5 away=0 blocked=0 stops=8 required=5 "
        "target=6 allowance=1 prompts=0 prompt_modes=auto harness=3 command=1 ship_runs=1 "
        "reenter=0 in=1 cache_read=100 out=10",
        "Sdlc-Extra: design after_gate=1 revise=0 asked=1 unprompted=0 interrupt=0 harness=1 "
        "command=1",
        "Sdlc-Extra: ship after_gate=0 revise=1 asked=0 unprompted=0 interrupt=0 harness=2 "
        "command=0",
    ]))  # fmt: skip
    extra = _retro(root)["metrics"]["extra"]
    assert (extra["recorded"], extra["harness"], extra["command"]) == (1, 3, 1)
    assert extra["kinds"] == {
        "after_gate": {"count": 1, "changes": 1},
        "revise": {"count": 1, "changes": 1},
        "asked": {"count": 1, "changes": 1},
        "unprompted": {"count": 0, "changes": 0},
        "interrupt": {"count": 0, "changes": 0},
        "fix": {"count": 0, "changes": 0},  # the lines predate `fix`: read as 0
    }


# ---------------------------------------------------------------- the process views and report

TOTALS = "Sdlc-Totals: elapsed={elapsed} agent={agent} response=10 away=0 blocked=0 stops=3"


def _rec(name: str, tier: int, closed: str, at: str | None, elapsed: int | None) -> dict:
    """A closed change's record as `closed_changes` gives it, measured when `elapsed` is set."""
    totals = {"elapsed": elapsed, "agent": (elapsed or 0) // 2, "response": 10, "away": 5,
              "blocked": 0}  # fmt: skip
    return {
        "name": name, "tier": tier, "close_date": closed, "days_open": 0,
        "close_at": f"{closed}T{at}:00+00:00" if at else "",
        "metrics": {"totals": totals} if elapsed is not None else None,
    }  # fmt: skip


BUGS = {
    "reported": {"high": 1}, "fixed": {"high": 1}, "days_to_fix": {"median": 2},
    "rate": {"window": {"rate": 0.25}, "previous": {"rate": 0.0}, "trend": "up"},
}  # fmt: skip


def _views(changes: list[dict]) -> dict:
    rework = [{"change": "003-c", "reworks": "001-a", "via": ["reworks"], "days": 1}]
    since = {"sha": "x", "date": "2026-10-01"}
    return sdlc.retro.process_views(changes, [], rework, [{}, {}], BUGS, since, date(2026, 10, 24))


def test_the_process_views_count_cycle_throughput_time_and_load() -> None:
    """R1: a and b overlap each other, c runs alone, and d, a week on, is unmeasured."""
    out = _views([
        _rec("001-a", 1, "2026-10-05", "12:00", 120),   # 10:00 to 12:00
        _rec("002-b", 2, "2026-10-05", "11:00", 60),    # 10:00 to 11:00
        _rec("003-c", 2, "2026-10-07", "12:00", 30),
        _rec("004-d", 1, "2026-10-13", None, None),
    ])  # fmt: skip
    assert out["window"] == {
        "since": "2026-10-01", "today": "2026-10-24", "closed": 4, "tiers": {"1": 2, "2": 2},
        "dropped": 0, "measured": 3, "unmeasured": 1,
    }  # fmt: skip
    assert out["throughput"] == [
        {"week": "2026-10-05", "tiers": {"1": 1, "2": 2}, "total": 3},
        {"week": "2026-10-12", "tiers": {"1": 1}, "total": 1},
    ]
    assert out["cycle"]["1"] == {"n": 1, "elapsed": 120, "max": 120, "agent": 60, "days_open": 0}
    assert out["cycle"]["2"]["n"] == 2 and out["cycle"]["2"]["elapsed"] == 45
    assert out["time"]["sums"] == {"agent": 105, "response": 30, "away": 15, "blocked": 0}
    assert out["time"]["agent_share"] == 0.7
    assert out["wip"] == {"spans": 3, "median": 2, "max": 2}
    assert {k: r["n"] for k, r in out["capacity"].items()} == {"1": 1, "2": 2, "3+": 0}
    assert out["capacity"]["2"]["elapsed"] == 90
    assert out["rework"] == {"links": 1, "reworked": 1, "per_change": 0.25, "questions": 2}
    assert out["escapes"] == {"reported": 1, "fixed": 1, "days_to_fix": 2, "rate": 0.25,
                              "previous": 0.0, "trend": "up"}  # fmt: skip


def test_with_nothing_measured_the_timed_views_say_so_never_zero() -> None:
    """R2: unmeasured changes are counted where they can be, never as zeros where they can't."""
    out = _views([_rec("001-a", 1, "2026-10-05", None, None)])
    assert out["window"]["measured"] == 0 and out["throughput"][0]["total"] == 1
    assert [out[k] for k in ("cycle", "time", "wip", "capacity")] == [None] * 4
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    text = sdlc.retro.render_report(template, out)
    assert text.count("Not measured: none of the 1 changes closed has its numbers.") == 3
    assert "0m" not in text


def test_no_figure_folds_speed_and_stability_into_one() -> None:
    """R3: no velocity, no score, in the template or what it renders."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    text = sdlc.retro.render_report(template, _views([_rec("001-a", 1, "2026-10-05", "12:00", 60)]))
    for word in ("velocity", "score"):
        assert word not in template.lower() and word not in text.lower()
    assert "{{" not in text


def test_retro_and_its_report_show_the_same_figures(tmp_path: Path, capsys) -> None:
    """R1, R5: `retro`'s `process` and `--report` come from one function over one window, and the
    report runs none of the host's commands."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", tier=2, trailers=(TOTALS.format(elapsed=76, agent=40),))
    _close(root, "002-draft-sync", closed="2026-10-03")
    out = _retro(root)
    assert out["report"] == ".sdlc/retros/2026-10-24.md"
    assert out["changes"][0]["close_at"].startswith("2026-10-02T12:00:00")
    cycle = out["process"]["cycle"]["2"]
    assert (cycle["elapsed"], cycle["agent"]) == (76, 40)
    assert out["process"]["window"]["unmeasured"] == 1
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(
        '[retro]\nevidence = ["touch ran"]\nindicators = ["touch ran"]\n', "utf-8"
    )
    assert sdlc.retro.retro(root, sdlc.load_config(root)[0])["architecture"]["host"], "it would run"
    (root / "ran").unlink()
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert not (root / "ran").exists(), "the report runs none of the host's commands"
    assert "| 2 | 1 | 1h 16m | 1h 16m | 40m | 1 |" in text
    assert "1 of them were measured" in text and "1 weren't" in text
    # 168 R10: the Value band's figures, from the same function as the JSON's.
    mix, ttu = out["work_mix"], out["time_to_users"]
    assert f"debt {mix['classes']['debt']} (100%), of {mix['n']} classed changes" in text
    assert f"{ttu['why']['unreleased']} not yet released" in text
    assert f"{ttu['releases']} releases in the window" in text
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    assert capsys.readouterr().out.startswith("# Retrospective report\n")
    assert not (root / "ran").exists()


# ---------------------------------------------------------------- spend (118)

SPENT = (
    "Sdlc-Mode: manual",
    "Sdlc-Totals: elapsed=10 out=500 words=12 tools=7",
    "Sdlc-Stage: build words=9 out=400",
    "Sdlc-Stage: ship words=3 out=100",
    "Sdlc-Tool: Read calls=5 errors=0 build=5",
    "Sdlc-Tool: Bash:make calls=2 errors=1 build=1 ship=1",
)


def _spent(root: Path) -> None:
    _close(root, "001-reopen-drafts", trailers=SPENT, texts={
        "src/a.py": "# why\nx = 1\n# and why\ny = 2\n",
        "tests/test_a.py": "# a test's comment is not the code's\n",
        "docs/a.md": "# a heading\n",
    })  # fmt: skip
    _close(root, "002-draft-titles", closed="2026-10-03", texts={"src/b.py": "z = 3\n"},
           trailers=("Sdlc-Coverage: none: metrics.transcripts is off",
                     "Sdlc-Totals: elapsed=10"))  # fmt: skip
    _close(root, "003-keep-one-draft", closed="2026-10-04", texts={"src/c.ts": "// c\n"})


def test_spend_lists_each_change_and_says_what_is_unrecorded(tmp_path: Path, capsys) -> None:
    """R5, R8: each change's code and comment lines from its diff, its tokens, words and calls
    from its `Close` commit; one without `tools=` and `words=` is `recorded: false`, says why, and
    is in no token or call figure. Its rows print only with `--metrics`."""
    root = _repo(tmp_path)
    _spent(root)
    spend = _retro(root)["spend"]
    first, second, third = spend["changes"]
    assert first == {
        "change": "001-reopen-drafts", "tier": 1, "code_added": 4, "comment_lines": 2,
        "comment_base": 4, "out": 500, "words": {"build": 9, "ship": 3}, "tools": 7, "errors": 1,
        "by_tool": {"Read": {"calls": 5, "errors": 0}, "Bash:make": {"calls": 2, "errors": 1}},
        "recorded": True, "why": None,
    }  # fmt: skip
    assert (second["recorded"], second["tools"], second["words"]) == (False, None, None)
    assert second["why"] == "metrics.transcripts is off"
    assert (third["comment_lines"], third["why"]) == (1, "not measured at close")
    assert (spend["recorded"], spend["unrecorded"]) == (1, 2)
    assert spend["why"] == {"metrics.transcripts is off": 1, "not measured at close": 1}
    assert spend["tools"]["most_called"][0] == {
        "name": "Read", "calls": 5, "errors": 0, "error_share": 0.0, "changes": 1,
    }  # fmt: skip
    assert spend["tiers"]["1"]["changes"] == 3
    assert sdlc.retro.cmd_retro(root) == 0
    lean = json.loads(capsys.readouterr().out)["spend"]
    assert "changes" not in lean and lean["recorded"] == 1
    assert sdlc.retro.cmd_retro(root, metrics=True) == 0
    assert len(json.loads(capsys.readouterr().out)["spend"]["changes"]) == 3


def test_the_report_renders_spend(tmp_path: Path) -> None:
    """R9: `## Spend` in the report: what was left out and why, outliers, the top tools."""
    root = _repo(tmp_path)
    _spent(root)
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "## Spend" in text and "{{spend}}" not in text
    assert "1 of the 3 changes closed recorded" in text
    assert "metrics.transcripts is off: 1" in text
    assert "| Read | 5 | 0 | 0 | 1 |" in text
    assert "No change is over twice its tier's median" in text
    # A host's override from before is reported as breaking, the section and its placeholder.
    old = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8").split("## Spend")[0]
    assert sdlc._template_misses("retro.md", old) == [
        "the `## Spend` heading",
        "the `{{spend}}` placeholder",
    ]


def _section(n: int, rank: str, disposition: str, by: str | None = None) -> str:
    reason = "Reason: said so\n" if disposition in ("wrong", "minor") else ""
    return (
        f"\n## F{n}. [{rank}] [correctness] Finding {n}\n\nEvidence: src/a.py:{n}\nClass: c\n"
        f"Disposition: {disposition}\n{reason}" + (f"By: {by}\n" if by else "")
    )


def _caught(n: int, rank: str, where: str, disposition: str, by: str | None = "code") -> str:
    """A findings.md section whose `Class:` names the round that raised it, `where`."""
    reason = "Reason: said so\n" if disposition in ("wrong", "minor") else ""
    return (
        f"\n## F{n}. [{rank}] [correctness] Finding {n}\n\nEvidence: src/a.py:{n}\n"
        f"Class: {by or 'ship'} review, {where}\nDisposition: {disposition}\n{reason}"
        + (f"By: {by}\n" if by else "")
    )


def test_retro_counts_a_landing_catch_once_per_change(tmp_path: Path) -> None:
    """136 R8: of the window's changes a factory role reviewed, those whose landing kept an
    important finding, fixed or recorded, each counted once however many it kept; a build round's
    finding, a landing nit and one answered wrong never count, nor a change no agent reviewed."""
    root = _repo(tmp_path)
    head = "# Findings\n\n> Note.\n"
    texts = {
        "001-hand": head + _caught(1, "important", "landing round 1", "fixed", None),
        "002-twice": head + _caught(1, "important", "landing round 1", "fixed")
        + _caught(2, "important", "landing round 2", "recorded", "behaviour"),
        "003-built": head + _caught(1, "important", "round 1", "fixed")
        + _caught(2, "nit", "landing round 1", "recorded"),
        "004-wrong": head + _caught(1, "important", "landing round 1", "wrong", "ui"),
    }  # fmt: skip
    for name, text in texts.items():
        _close(root, name, texts={f".sdlc/work/{name}/findings.md": text})
    out = sdlc.retro.retro(root, sdlc.load_config(root)[0], date(2026, 10, 25))
    assert out["bugs"]["landing_catches"] == {"caught": 1, "reviewed": 3}
    report = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 25))
    assert "Landing catches: 1 of 3 factory-reviewed changes" in report, report


def test_review_sources_split_ship_from_the_agents(tmp_path: Path) -> None:
    """114 R12: each change's findings.md counted by who raised each finding, ship's own apart from
    the fresh reviewer's and each factory role's, with how many changes each reviewed; a change
    with no file is unknown, never a review that found nothing."""
    root = _repo(tmp_path)
    hand = "# Findings\n\n> Note.\n" + _section(1, "important", "fixed") + _section(
        2, "nit", "recorded") + _section(3, "important", "wrong", "fresh") + _section(
        4, "important", "fixed", "ship-security")  # fmt: skip
    built = "# Findings\n\n> Note.\n" + "".join([
        _section(1, "important", "fixed", "code"), _section(2, "important", "wrong", "security"),
        _section(3, "pre-existing", "recorded", "test"), _section(4, "nit", "minor", "test"),
    ])  # fmt: skip
    _close(root, "001-hand", texts={".sdlc/work/001-hand/findings.md": hand})
    _close(root, "002-built", texts={".sdlc/work/002-built/findings.md": built})
    _close(root, "003-old")
    out = sdlc.retro.retro(root, sdlc.load_config(root)[0], date(2026, 10, 25))["bugs"]
    row = lambda c, i, n, p, w: {"changes": c, "important": i, "nit": n, "preexisting": p,  # noqa: E731
                                 "wrong": w}  # fmt: skip
    assert out["review_sources"] == {
        "ship": row(1, 1, 1, 0, 0), "fresh": row(1, 1, 0, 0, 1),
        "ship-security": row(1, 1, 0, 0, 0), "code": row(1, 1, 0, 0, 0),
        "security": row(1, 1, 0, 0, 1), "test": row(1, 0, 1, 1, 0),
    }  # fmt: skip
    assert list(out["review_sources"]) == [
        "ship",
        "fresh",
        "ship-security",
        "code",
        "security",
        "test",
    ], "ship's passes before the factory's roles"
    assert out["review_unknown"] == 1
    assert [(i["change"], i["id"], i["by"]) for i in out["important"]] == [
        ("001-hand", "F1", None), ("001-hand", "F3", "fresh"), ("001-hand", "F4", "ship-security"),
        ("002-built", "F1", "code"), ("002-built", "F2", "security"),
    ]  # fmt: skip
    report = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 25))
    for source in ("ship", "fresh", "code", "security", "test"):
        assert re.search(rf"^\| {source} \| 1 \|", report, re.M), report


# ---------------------------------------------------------------- how factory agents worked (146)

AGENT_COUNTS = "edits={} shell_edits={} bg={} tool_errors=0 test_runs=4 broke={}"


def _agent_closed(root: Path, name: str, closed: str, *roles: str) -> None:
    """A factory change closed with the given `Sdlc-Role` lines."""
    _close(root, name, tier=2, closed=closed, trailers=(
        "Sdlc-Mode: factory",
        "Sdlc-Coverage: transcripts=2 stages=build,ship",
        "Sdlc-Totals: elapsed=60 agent=40 tools=20 words=3 out=10",
        *(f"Sdlc-Role: {r}" for r in roles),
    ))  # fmt: skip


def test_retro_compares_agents_by_model(tmp_path: Path) -> None:
    """146 R13: recorded role lines grouped by role and model, with each count's per-change
    median, in the JSON and the report."""
    root = _repo(tmp_path)
    _agent_closed(
        root,
        "001-reopen-drafts",
        "2026-10-02",
        "builder runs=1 agent=30 model=model-a " + AGENT_COUNTS.format(0, 28, 2, 1),
        "code runs=2 agent=5 model=model-a " + AGENT_COUNTS.format(0, 0, 0, 0),
    )
    _agent_closed(
        root,
        "002-draft-titles",
        "2026-10-03",
        "builder runs=1 agent=20 model=model-b " + AGENT_COUNTS.format(9, 0, 0, 0),
    )
    _agent_closed(
        root,
        "003-draft-sync",
        "2026-10-04",
        "builder runs=2 agent=20 model=model-b " + AGENT_COUNTS.format(5, 2, 0, 0),
    )
    agents = _retro(root)["spend"]["agents"]
    groups = {(g["role"], g["model"]): g for g in agents["groups"]}
    assert set(groups) == {("builder", "model-a"), ("builder", "model-b"), ("code", "model-a")}
    a, b = groups[("builder", "model-a")], groups[("builder", "model-b")]
    assert (a["changes"], a["runs"], a["median"]["shell_edits"], a["median"]["bg"]) == (1, 1, 28, 2)
    assert (b["changes"], b["runs"], b["median"]["edits"], b["median"]["shell_edits"]) == (
        2,
        3,
        7,
        1,
    )
    assert agents["unrecorded"] == 0
    report = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "Agents by role and model" in report
    assert "| builder | model-a | 1 | 1 | 0 | 28 | 2 | 0 | 4 | 1 |" in report
    assert "| builder | model-b | 2 | 3 | 7 | 1 | 0 | 0 | 4 | 0 |" in report


def test_retro_leaves_agents_from_before_behaviours_out(tmp_path: Path) -> None:
    """146 R14: a role line without `edits=` is unrecorded, never zero; a recorded one without a
    model groups under `unknown`."""
    root = _repo(tmp_path)
    _agent_closed(root, "001-reopen-drafts", "2026-10-02", "builder runs=1 agent=30 out=4")
    _agent_closed(
        root,
        "002-draft-titles",
        "2026-10-03",
        "builder runs=1 agent=20 " + AGENT_COUNTS.format(3, 1, 0, 0),
    )
    agents = _retro(root)["spend"]["agents"]
    assert [(g["role"], g["model"], g["changes"]) for g in agents["groups"]] == [
        ("builder", "unknown", 1)
    ]
    assert agents["unrecorded"] == 1
    assert agents["groups"][0]["median"]["edits"] == 3


def test_retro_prints_a_change_s_agent_counts_only_with_metrics(tmp_path: Path, capsys) -> None:
    """146 R15: each change's own role counts, in close order, only with `--metrics`."""
    root = _repo(tmp_path)
    _agent_closed(
        root,
        "001-reopen-drafts",
        "2026-10-02",
        "builder runs=1 agent=30 model=model-a " + AGENT_COUNTS.format(1, 0, 2, 0),
    )
    _agent_closed(
        root,
        "002-draft-titles",
        "2026-10-03",
        "builder runs=1 agent=20 model=model-a " + AGENT_COUNTS.format(1, 0, 0, 0),
    )
    assert sdlc.retro.cmd_retro(root) == 0
    lean = json.loads(capsys.readouterr().out)["spend"]["agents"]
    assert "changes" not in lean and lean["groups"]
    assert sdlc.retro.cmd_retro(root, metrics=True) == 0
    rows = json.loads(capsys.readouterr().out)["spend"]["agents"]["changes"]
    assert [(r["change"], r["role"], r["model"], r["bg"]) for r in rows] == [
        ("001-reopen-drafts", "builder", "model-a", 2),
        ("002-draft-titles", "builder", "model-a", 0),
    ]


# ---------------------------------------------------------------- lead time (162)


def _led(name: str, tier: int, mode: str, lead: dict | None, elapsed: int | None = None) -> dict:
    """A record with `Sdlc-Mode` and, when `lead` is set, an `Sdlc-Lead` line's fields."""
    rec = _rec(name, tier, "2026-10-05", "12:00", elapsed)
    metrics = rec["metrics"] or {}
    metrics["mode"] = mode
    if lead is not None:
        metrics["lead"] = {**lead, "source": "runs"}
    rec["metrics"] = metrics
    return rec


def test_lead_time_by_tier_and_way_with_unmeasured_counted_apart() -> None:
    """162 R13, R14: median and nearest-rank p85 per tier and way; a change without the line
    moves no figure and is counted as unmeasured; computed with no `elapsed` anywhere."""
    changes = [_led(f"0{i:02d}-a", 2, "factory", {"lead": 10 * i}) for i in range(1, 11)]
    changes += [
        _led("020-b", 1, "manual", {"lead": 100, "ready_wait": 60}),
        _led("021-c", 1, "manual", {"lead": 50, "queued": 5, "agents": 20, "idle": 5,
                                    "ready_wait": 20}),
        _led("022-d", 1, "manual", None),
    ]  # fmt: skip
    out = _views(changes)
    lead = out["lead"]
    assert (lead["measured"], lead["unmeasured"]) == (12, 1)
    assert lead["groups"] == [
        {"tier": "1", "way": "manual", "n": 2, "median": 75, "p85": 100},
        {"tier": "2", "way": "factory", "n": 10, "median": 55, "p85": 90},
    ]
    assert lead["shares"]["ready_wait"] == {"share": 0.53, "changes": 2}
    assert lead["shares"]["agents"] == {"share": 0.4, "changes": 1}
    assert "landing" not in lead["shares"], "no change recorded it: never 0"
    assert out["cycle"] is None, "no elapsed: the timed views are unmeasured, as before"


def test_without_a_lead_line_every_other_figure_is_as_it_was() -> None:
    """162 R14: the existing views don't see the new line."""
    plain = [
        _rec("001-a", 1, "2026-10-05", "12:00", 120),
        _rec("002-b", 2, "2026-10-05", "11:00", 60),
    ]
    led = [dict(r, metrics={**r["metrics"], "lead": {"lead": 999, "source": "git"}}) for r in plain]
    a, b = _views(plain), _views(led)
    for key in ("window", "cycle", "time", "wip", "capacity"):
        assert a[key] == b[key], key
    assert a["lead"] == {"measured": 0, "unmeasured": 2, "groups": [], "shares": {}}


def test_the_report_shows_lead_time_under_cycle_time() -> None:
    """162 R15: the lead table and the shares under the elapsed table, or alone."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    both = [_led("001-a", 2, "factory", {"lead": 250, "ready_wait": 100}, elapsed=60),
            _led("002-b", 2, "factory", None, elapsed=30)]  # fmt: skip
    text = sdlc.retro.render_report(template, _views(both))
    assert "| Tier | Changes | Median elapsed |" in text
    assert "| Tier | Way | Changes | Median lead | 85th percentile |" in text
    assert "| 2 | factory | 1 | 4h 10m | 4h 10m |" in text
    assert "ready and waiting 40% (of 1)" in text and "1 change has no lead time" in text
    alone = sdlc.retro.render_report(template, _views([_led("001-a", 1, "manual", {"lead": 30})]))
    assert "| 1 | manual | 1 | 30m | 30m |" in alone and "Median elapsed" not in alone


# ---------------------------------------------------------------- the Value band (168)


def _filed(root: Path, text: str) -> None:
    """The register on the base branch, committed as `inbox-commit` would."""
    register = root / ".sdlc" / "work" / "inbox.md"
    register.parent.mkdir(parents=True, exist_ok=True)
    register.write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "File seeds")


SEEDS = (
    "# Inbox\n\n"
    "## [2026-10-01-1] [bug] Drafts vanish\n\nWhat happens.\n\nSeverity: high\n\n"
    "## [2026-10-01-2] [nit] A small thing\n\nTheme: style\nCost: S\nValue: low\n\n"
    "## [2026-10-01-3] [idea] Tidy the drafts code\n\nWhy.\n\nTheme: refactor\n\n"
)


def test_work_mix_classes_each_change_by_its_first_signal(tmp_path: Path) -> None:
    """168 R1: fix, capability, process, debt, the first rule that applies; the rest in `also`."""
    root = _repo(tmp_path)
    _filed(root, SEEDS)
    _close(root, "001-fix-by-fixes", fixes="2026-10-01-1")
    _close(root, "002-new-thing", impact="minor")
    _close(root, "003-rework-it", reworks="002")
    _close(root, "004-bug-seed", idea="2026-10-01-1")
    _close(root, "005-process", files=(".sdlc/SDLC.md",))
    _close(root, "006-nit-seed", idea="2026-10-01-2")
    _close(root, "007-theme-seed", idea="2026-10-01-3", impact="none")
    _close(root, "008-small", impact="patch")
    _close(root, "009-mixed", fixes="2026-10-01-1", impact="minor")
    work = {c["name"]: c["work"] for c in _retro(root)["changes"]}
    assert {n: w["class"] for n, w in work.items()} == {
        "001-fix-by-fixes": "fix", "002-new-thing": "capability", "003-rework-it": "fix",
        "004-bug-seed": "fix", "005-process": "process", "006-nit-seed": "debt",
        "007-theme-seed": "debt", "008-small": "debt", "009-mixed": "fix",
    }  # fmt: skip
    assert {n: w["by"] for n, w in work.items()} == {
        "001-fix-by-fixes": "fixes", "002-new-thing": "impact: minor", "003-rework-it": "reworks",
        "004-bug-seed": "bug seed", "005-process": "process paths", "006-nit-seed": "nit seed",
        "007-theme-seed": "theme: refactor", "008-small": "impact: patch", "009-mixed": "fixes",
    }  # fmt: skip
    assert work["009-mixed"]["also"] == ["capability"]
    assert work["005-process"]["also"] == ["debt"]
    assert work["002-new-thing"]["also"] == []


def test_work_mix_counts_an_unreadable_impact_as_unmeasured_never_a_class(tmp_path) -> None:
    """168 R2: classed changes in `n` and the shares; an unreadable impact with nothing else
    is `unmeasured`, in no class and no share."""
    root = _repo(tmp_path)
    _close(root, "001-new-thing", impact="minor")
    _close(root, "002-small", impact="patch")
    _close(root, "003-mixed", impact="minor", fixes="2026-10-01-1")
    _close(root, "004-unknown", impact="sometime")
    out = _retro(root)
    assert out["changes"][3]["work"] == {"class": None, "by": None, "also": []}
    assert out["work_mix"] == {
        "n": 3, "unmeasured": 1, "mixed": 1,
        "classes": {"fix": 1, "capability": 1, "process": 0, "debt": 1},
        "shares": {"fix": 0.33, "capability": 0.33, "process": 0.0, "debt": 0.33},
    }  # fmt: skip


def test_work_mix_shares_are_null_with_nothing_classed(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-unknown", impact="sometime")
    mix = _retro(root)["work_mix"]
    assert (mix["n"], mix["unmeasured"], mix["shares"]) == (0, 1, None)


def test_a_change_touching_only_the_process_is_process_work(tmp_path: Path) -> None:
    """168 R3: git's quoted path for a non-ASCII process doc is unquoted before it is compared,
    and a change touching only its own folder is not process work."""
    root = _repo(tmp_path)
    _config(root, '[docs]\nprocess = "docs/Prozeß.md"\n')
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "config")
    _close(root, "001-host-dir", files=(".sdlc/SDLC.md",))
    _close(root, "002-named-doc", files=("docs/Prozeß.md",))
    _close(root, "003-own-folder", files=(".sdlc/work/003-own-folder/notes.md",))
    work = {c["name"]: c["work"]["class"] for c in _retro(root)["changes"]}
    assert work == {"001-host-dir": "process", "002-named-doc": "process",
                    "003-own-folder": "debt"}  # fmt: skip


def _released(root: Path, tag: str, when: str) -> None:
    _git(root, "tag", "-a", tag, "-m", tag, when=when)


def test_time_to_users_is_the_median_from_close_to_the_first_release(tmp_path: Path) -> None:
    """168 R5: from each `Close` to the first release tag holding it, in days to one place."""
    root = _repo(tmp_path)
    _released(root, "v0.9.0", "2026-09-01T12:00:00")
    _record(root, "2026-09-30")
    _close(root, "001-reopen-drafts", closed="2026-10-02")
    _close(root, "002-draft-sync", closed="2026-10-03")
    _released(root, "v1.0.0", "2026-10-04T12:00:00")
    _close(root, "003-draft-titles", closed="2026-10-05")
    _released(root, "v1.1.0", "2026-10-06T00:00:00")
    assert _retro(root)["time_to_users"] == {
        "n": 3, "median_days": 1.0, "unmeasured": 0, "why": {}, "releases": 2,
    }  # fmt: skip


def test_an_unreleased_change_is_counted_apart_from_time_to_users(tmp_path: Path) -> None:
    """168 R6: in `unmeasured` under `why`, never read as zero days."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", closed="2026-10-02")
    released = _retro(root)["time_to_users"]
    assert (released["n"], released["median_days"]) == (0, None)
    assert released["why"] == {"unreleased": 1} and released["unmeasured"] == 1
    _released(root, "v1.0.0", "2026-10-05T12:00:00")
    _close(root, "002-draft-sync", closed="2026-10-06")
    ttu = _retro(root)["time_to_users"]
    assert (ttu["n"], ttu["median_days"], ttu["unmeasured"]) == (1, 3.0, 1)
    assert ttu["why"] == {"unreleased": 1} and ttu["releases"] == 1


def _retrospective(root: Path, day: str, direction: str, register: str | None = None) -> None:
    """A `Retrospective` commit holding the direction doc and, when given, the register, as
    `retro-commit` writes them."""
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(direction, encoding="utf-8")
    if register is not None:
        (root / ".sdlc" / "work").mkdir(parents=True, exist_ok=True)
        (root / ".sdlc" / "work" / "inbox.md").write_text(register, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Retrospective {day}")


def _seed(sid: str, title: str) -> str:
    return f"## [{sid}] [idea] {title}\n\nWhy.\n\n"


def test_follow_through_scores_the_last_retrospective_s_seeds(tmp_path: Path) -> None:
    """168 R7: the seeds the last retrospective added, each done, dropped, carried or vanished;
    never one already in the register before it."""
    root = _repo(tmp_path)
    _filed(root, "# Inbox\n\n" + _seed("2026-09-01-1", "Already here"))
    titles = ("Built", "Retired", "Still open", "Deleted by hand")
    added = "".join(_seed(f"2026-10-10-{n}", t) for n, t in enumerate(titles, 1))
    _retrospective(root, "2026-10-10", "# Direction\n",
                   "# Inbox\n\n" + _seed("2026-09-01-1", "Already here") + added)  # fmt: skip
    _close(root, "001-reopen-drafts", idea="2026-10-10-1", closed="2026-10-12")
    register = root / ".sdlc" / "work" / "inbox.md"
    text = register.read_text(encoding="utf-8")
    register.write_text(text.replace(_seed("2026-10-10-2", "Retired"), ""), encoding="utf-8")
    _git(root, "commit", "-q", "-am", "File 2026-10-13-1; Retire 2026-10-10-2",
         "-m", "Reason 2026-10-10-2: duplicate")  # fmt: skip
    text = register.read_text(encoding="utf-8")
    register.write_text(text.replace(_seed("2026-10-10-4", "Deleted by hand"), ""), "utf-8")
    _git(root, "commit", "-q", "-am", "tidy the register")
    ft = _retro(root)["follow_through"]
    assert ft["since"] == "2026-10-10"
    seeds = ft["seeds"]
    assert seeds["rows"] == [
        {"id": "2026-10-10-1", "verdict": "done", "change": "001-reopen-drafts"},
        {"id": "2026-10-10-2", "verdict": "dropped"},
        {"id": "2026-10-10-3", "verdict": "carried"},
        {"id": "2026-10-10-4", "verdict": "vanished"},
    ]
    assert {k: seeds[k] for k in ("n", "done", "dropped", "carried", "vanished")} == {
        "n": 4, "done": 1, "dropped": 1, "carried": 1, "vanished": 1,
    }  # fmt: skip
    assert ft["milestones"]["n"] == 0
    assert (ft["n"], ft["share"], ft["unmeasured"]) == (4, 0.5, 0)
    assert any("intent titles" in m for m in ft["missing"])


DIRECTION_THEN = """\
# Direction

## Milestones

### ~~M0. Long done~~ Done: before

### M1. Finished

### M2. Given up

### M3. Rethought

### M4. Forgotten

### M5. Built

Groups: 001, "Reopen drafts"

### M6. Lost track

Groups: 099

### M7. Under way

Groups: 001, "Still waiting"
"""

DIRECTION_NOW = """\
# Direction

## Milestones

### ~~M0. Long done~~ Done: before

### ~~M1. Finished~~ Done: shipped

### ~~M2. Given up~~ Dropped: not worth it

### ~~M3. Rethought~~ Revised → M8: smaller

### M5. Built

Groups: 001, "Reopen drafts"

### M6. Lost track

Groups: 099

### M7. Under way

Groups: 001, "Still waiting"

### M8. Smaller
"""


def test_follow_through_scores_the_milestones_open_at_the_last_retrospective(tmp_path) -> None:
    """168 R8: struck Done is done, Dropped or Revised dropped, missing vanished; every grouped
    row closed or shipped is done; an unknown change is unmeasured; the rest carried."""
    root = _repo(tmp_path)
    _retrospective(root, "2026-10-10", DIRECTION_THEN,
                   "# Inbox\n\n" + _seed("2026-10-09-1", "Still waiting"))  # fmt: skip
    _close(root, "001-reopen-drafts", idea="Reopen drafts", closed="2026-10-12")
    (root / ".sdlc" / "DIRECTION.md").write_text(DIRECTION_NOW, encoding="utf-8")
    _git(root, "commit", "-q", "-am", "Strike the milestones")
    ft = _retro(root)["follow_through"]
    milestones = ft["milestones"]
    assert [(r["id"], r["verdict"]) for r in milestones["rows"]] == [
        ("M1", "done"), ("M2", "dropped"), ("M3", "dropped"), ("M4", "vanished"),
        ("M5", "done"), ("M6", "unmeasured"), ("M7", "carried"),
    ]  # fmt: skip
    assert {k: milestones[k] for k in ("n", "done", "dropped", "carried", "vanished")} == {
        "n": 6, "done": 2, "dropped": 2, "carried": 1, "vanished": 1,
    }  # fmt: skip
    assert ft["unmeasured"] == 1
    assert ft["seeds"]["rows"] == [{"id": "2026-10-09-1", "verdict": "carried"}]
    assert (ft["n"], ft["share"]) == (7, 0.57), "six milestones and one seed; 4 kept"


def test_without_an_earlier_retrospective_follow_through_is_unmeasured_not_zero(tmp_path) -> None:
    """168 R9: nothing to follow through on is null, never a zero share."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    ft = _retro(root)["follow_through"]
    assert ft["since"] is None and ft["n"] == 0
    assert ft["share"] is None and ft["seeds"] is None and ft["milestones"] is None
    assert any("no earlier retrospective" in m for m in ft["missing"])


def test_the_report_shows_the_value_figures_in_its_window(tmp_path: Path) -> None:
    """168 R10: one sentence each for work mix, time to users and follow-through, after the
    window paragraph, each with its `n` and what it left out."""
    root = _repo(tmp_path)
    _retrospective(root, "2026-10-01", "# Direction\n\n## Milestones\n\n### M1. Drafts\n",
                   "# Inbox\n\n" + _seed("2026-09-30-1", "Reopen drafts"))  # fmt: skip
    _close(root, "001-reopen-drafts", impact="minor", idea="2026-09-30-1", closed="2026-10-02")
    _close(root, "002-draft-sync", closed="2026-10-03")
    _released(root, "v1.0.0", "2026-10-04T12:00:00")
    _close(root, "003-draft-titles", impact="sometime", closed="2026-10-05")
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    window = text.split("## Window\n", 1)[1].split("\n## ", 1)[0]
    assert window.index("From 2026-10-01 to 2026-10-24") < window.index("Work mix:")
    assert (
        "Work mix: capability 1 (50%), debt 1 (50%), of 2 classed changes; 1 not classed." in window
    )
    assert (
        "Time to users: a median 1.5 days from landing to release, over 2 changes; 1 not yet "
        "released. 1 releases in the window." in window
    )
    assert (
        "Follow-through on the retrospective of 2026-10-01: 1 of 2 done or dropped (50%), seeds 1 "
        "of 1 and milestones 0 of 1; intent titles aren't recorded." in window
    )


def test_without_a_value_band_the_window_is_as_before() -> None:
    process = _views([])
    text = sdlc.retro.render_report("{{window}}", process)
    assert "Work mix" not in text and "Time to users" not in text
