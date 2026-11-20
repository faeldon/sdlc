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
import shutil
import subprocess
import sys
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
    own: tuple[str, ...] = (),
) -> None:
    """A change's own commit, with its intent and the files it touches, then its `Close`. `later`
    is a second commit on the change, touching those files, before it closes; `before` a first
    one, without its folder. `based` writes where the change started on the `Close`, as close
    does. Each file gets the change's name appended, but those in `rewrite`, which it replaces
    whole. `reworks` is the intent's line; `trailers` go on the `Close`; `texts` are files the
    change's own commit writes whole, beside the rest. `fixes` is the intent's `fixes:` line;
    `own` are trailers on that commit."""
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
    _git(root, "commit", "-q", "-m", f"ship {name}", *(["-m", "\n".join(own)] if own else []),
         when=when)  # fmt: skip
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
    texts: dict[str, str] | None = None,
) -> None:
    """What drop and close leave: the branch's commit, then `Drop NNN-slug`, a merge that keeps
    main's tree and ends with what close measured, and the branch gone. `texts` are files the
    branch's commit writes whole, `{rel: text}`."""
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
    for rel, body in (texts or {}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
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
    assert "changes" not in lean["cost"] and "changes" in full["cost"]
    full["cost"].pop("changes")  # 174 R7: each change's own cost
    assert "changes" not in lean["pipeline"] and "changes" in full["pipeline"]
    full["pipeline"].pop("changes")  # 175 R11: each change's own pipeline figures
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


def test_escape_rate_is_split_by_the_introducing_change_s_way(tmp_path: Path) -> None:
    """176 R7: each escape carries its introducer's way, `unknown` when history doesn't hold it;
    the window's rate is split by way over each way's closed changes, null with none, and the
    split's escapes sum to the window's."""
    root = _repo(tmp_path)
    _filed(root, "# Inbox\n\n## [2026-10-07-1] [bug] Drafts lose titles\n\nWhat happens.\n\n"
                 "Severity: low\nIntroduced by: 099\n\n")  # fmt: skip
    _close(root, "001-reopen-drafts", trailers=("Sdlc-Mode: factory",))
    _close(root, "002-draft-titles", trailers=("Sdlc-Mode: manual",))
    fixes = (
        "Sdlc-Mode: manual",
        "Sdlc-Fixes: 2026-10-05-1 severity=high reported=2026-10-05 introduced_by=001",
        "Sdlc-Fixes: 2026-10-06-1 severity=low reported=2026-10-06 introduced_by=002-draft-titles",
    )
    _close(root, "003-keep-one-draft", closed="2026-10-08", trailers=fixes)
    out = _retro(root)
    bugs = out["bugs"]
    assert {r["change"]: r["way"] for r in bugs["escapes"]} == {
        "001-reopen-drafts": "factory", "002-draft-titles": "manual", "099": "unknown",
    }  # fmt: skip
    window = bugs["rate"]["window"]
    assert window["by_way"] == {
        "factory": {"escapes": 1, "changes": 1, "rate": 1.0},
        "manual": {"escapes": 1, "changes": 2, "rate": 0.5},
        "unknown": {"escapes": 1, "changes": 0, "rate": None},
    }
    assert sum(w["escapes"] for w in window["by_way"].values()) == window["escapes"] == 3


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
    # 180 R13: a hand edit on a change's own branch has no shape history can tell apart.
    assert any(u["signal"] == "a change's own records edited by hand before it landed"
               for u in out["unmeasured"])  # fmt: skip


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


def test_prose_counts_each_of_the_plugins_skills(tmp_path: Path, monkeypatch) -> None:
    root = _repo(tmp_path)
    prose = _retro(root)["prose"]
    assert set(prose["skills"]) == {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    retro = prose["skills"]["retro"]
    assert retro["est_tokens"] == retro["bytes"] // 4 and retro["script_calls"] >= 3
    # A skill's size is what every run reads; the files beside it are its branches.
    ship = prose["skills"]["ship"]
    skill = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    assert ship["lines"] == len(skill.splitlines())
    beside = {p.name for p in (ROOT / "skills" / "ship").glob("*.md")} - {"SKILL.md"}
    # 170: a host never reads the skills' cases' branch, which only this repo's ship names.
    assert set(ship["branches"]) == beside - {"cases.md"}
    assert set(retro["branches"]) == {"insights.md"}, "189: the insights are retro's branch"
    monkeypatch.setattr(sdlc, "_own_repo", lambda home: True)
    assert set(_retro(root)["prose"]["skills"]["ship"]["branches"]) == beside
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


def test_retro_commit_writes_the_report_it_would_print(tmp_path: Path) -> None:
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
    for command in ("vet", "status", "config", "readiness"):
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


# A test's text that loads `src/drafts.py`, as the base branch holds it.
LOADS_DRAFTS = "# checks src/drafts.py\n"


def _drifting(root: Path, test: str = "tests/test_drafts.py") -> None:
    """A test closed beside its code, which it loads, then three changes that move the code
    without it."""
    _close(root, "001-reopen-drafts", files=("src/drafts.py",), texts={test: LOADS_DRAFTS})
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


def test_drift_reads_the_test_at_the_base_branch(tmp_path: Path) -> None:
    """200: a test's code is what it loads on the base branch: edited beside code it doesn't
    load it never drifts with that code, a golden never drifts, and the working tree's copy of a
    test is never what's read."""
    root = _repo(tmp_path)
    _close(
        root, "001-reopen-drafts", files=("src/drafts.py", "src/big.py"),
        texts={"tests/test_drafts.py": "from src import drafts\n",
               "tests/fixtures/out.json": '{"loads": "src/drafts.py"}\n'},
    )  # fmt: skip
    for n, slug in enumerate(("big-one", "big-two", "big-three"), 2):
        _close(root, f"00{n}-{slug}", files=("src/big.py",))
    assert _retro(root)["tests"]["drifted"] == []
    for n, slug in enumerate(("draft-titles", "draft-sync", "keep-one-draft"), 5):
        _close(root, f"00{n}-{slug}", files=("src/drafts.py",))
    (root / "tests" / "test_drafts.py").write_text("nothing loaded\n", encoding="utf-8")
    drifted = _retro(root)["tests"]["drifted"]
    assert [(r["file"], r["code"], r["later"]) for r in drifted] == [
        ("tests/test_drafts.py", ["src/drafts.py"], 3)
    ]


def test_no_base_branch_means_no_drift(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _drifting(root)
    cfg = sdlc.load_config(root)[0]
    cfg["git"]["base"] = None
    assert sdlc.retro._tests(root, cfg, None)["drifted"] is None


def test_due_is_slow_or_drifted(tmp_path: Path) -> None:
    """R9: a pruning pass is due exactly when a test is slow or drifted."""
    root = _repo(tmp_path)
    _close(
        root, "001-reopen-drafts", files=("src/drafts.py",),
        texts={"tests/test_drafts.py": LOADS_DRAFTS},
    )  # fmt: skip
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
    """R2: `vet`, `status`, `config`, `readiness` and `retro --report` never run it."""
    root = _repo(tmp_path)
    _config(root, '[retro]\ntest_times = ["touch ran-times"]\n')
    monkeypatch.chdir(root)
    for argv in (["vet"], ["status"], ["config"], ["readiness"], ["retro", "--report"]):
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


ROWS = (
    '{"name": "src/drafts.py::save", "value": 5, "unit": "commits", "band": "high"}\n'
    '{"name": "src/drafts.py::save", "value": 40, "unit": "lines"}\n'
    '{"name": "cycles", "value": 2}\n'
    '{"name": "new one", "value": 1}\n'
)


def _rows_indicator(root: Path, text: str = ROWS) -> None:
    """An indicator that prints `text`, from a file the tree leaves untracked."""
    (root / "rows.jsonl").write_text(text, encoding="utf-8", newline="\n")
    _config(root, '[retro]\nindicators = ["cat rows.jsonl"]\n')


def test_indicator_rows_reach_the_architecture_block(tmp_path: Path) -> None:
    """177 R3: rows read, in the command's order, `output` null so the blob holds one copy."""
    root = _repo(tmp_path)
    _rows_indicator(root)
    (row,) = _retro(root)["architecture"]["host"]
    assert (row["output"], row["not_rows"], row["error"], row["exit"]) == (None, None, None, 0)
    assert [(r["name"], r["unit"], r["value"]) for r in row["rows"]] == [
        ("src/drafts.py::save", "commits", 5),
        ("src/drafts.py::save", "lines", 40),
        ("cycles", "", 2),
        ("new one", "", 1),
    ]
    assert row["rows"][0]["extra"] == {"band": "high"}
    assert all(r["last"] is None and r["change"] is None for r in row["rows"])


def test_a_failed_or_cut_indicator_passes_through_with_its_reason(tmp_path: Path) -> None:
    """177 R2: plain text, a non-zero exit, a timeout and a cut output keep `output`, `exit`,
    `error` and `truncated` as before, with `rows: null` and why."""
    root = _repo(tmp_path)
    _config(root, '[retro]\nindicators = ["echo 7 cycles", "echo oops >&2; exit 3"]\n')
    plain, failed = _retro(root)["architecture"]["host"]
    assert (plain["rows"], plain["not_rows"], plain["output"]) == (
        None, "line 1 isn't a JSON object", "7 cycles\n"
    )  # fmt: skip
    assert (failed["rows"], failed["not_rows"], failed["exit"]) == (None, "failed: exited 3", 3)
    assert failed["error"] == "exited 3: oops"
    ran = sdlc.retro._evidence(root, ['echo \'{"name": "a", "value": 1}\''], limit=5)
    (cut,) = sdlc.retro._indicator_rows(root, None, ran)
    assert (cut["rows"], cut["truncated"], cut["output"]) == (None, True, '{"nam')
    assert cut["not_rows"] == "truncated at 5 characters"
    ran = sdlc.retro._evidence(root, ["sleep 5"], timeout=0.1)
    (slow,) = sdlc.retro._indicator_rows(root, None, ran)
    assert (slow["rows"], slow["not_rows"]) == (None, "timed out")


def test_an_indicator_that_cannot_start_is_a_failure_not_rows(tmp_path: Path, monkeypatch) -> None:
    """Nit 2026-11-19-40, 177 R2: a command the shell can't start (an OSError, as with no `sh`)
    has no exit, and is `failed: could not start`, never a timeout and never rows."""
    root = _repo(tmp_path)
    monkeypatch.setattr(sdlc, "_sh", lambda command: [str(tmp_path / "no-such-shell"), command])
    ran = sdlc.retro._evidence(root, ['echo \'{"name": "a", "value": 1}\''])
    (row,) = sdlc.retro._indicator_rows(root, None, ran)
    assert row["exit"] is None and "no-such-shell" in row["error"], row
    assert (row["rows"], row["not_rows"]) == (None, "failed: could not start")


def _retro_report_at(root: Path, day: str, report: str) -> None:
    """A `Retrospective` commit holding `report` as that day's report."""
    path = root / ".sdlc" / "retros" / f"{day}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Retrospective {day}")


LAST = """\
## Indicators

`cat rows.jsonl`

| Indicator | Unit | Value | Last retrospective | Change |
|---|---|---|---|---|
| src/drafts.py::save | commits | 7 | — | — |
| src/drafts.py::save | lines | 40 | — | — |
| cycles | — | 1 | — | — |
| cycles | — | 4 | — | — |
"""


def test_an_indicator_is_compared_with_the_last_retrospectives_report(tmp_path: Path) -> None:
    """177 R4: `last` from the newest `Retrospective` commit's report alone, null (never 0) where
    there is none, no such row, or the row twice; `change` is `value − last`."""
    root = _repo(tmp_path)
    # An older retrospective, and a report in the tree, are neither of them the last report.
    _retro_report_at(root, "2026-10-01", LAST.replace("| 7 |", "| 1 |").replace("| 40 |", "| 9 |"))
    _retro_report_at(root, "2026-10-10", LAST)
    in_tree = root / ".sdlc" / "retros" / "2026-10-10.md"
    in_tree.write_text(LAST.replace("| 7 |", "| 99 |"), encoding="utf-8", newline="\n")
    _rows_indicator(root)
    (row,) = _retro(root)["architecture"]["host"]
    got = {(r["name"], r["unit"]): (r["last"], r["change"]) for r in row["rows"]}
    assert got == {
        ("src/drafts.py::save", "commits"): (7, -2),
        ("src/drafts.py::save", "lines"): (40, 0),
        ("cycles", ""): (None, None),
        ("new one", ""): (None, None),
    }
    # A retrospective whose commit holds no report gives no comparison.
    _record(root, "2026-10-20")
    (row,) = _retro(root)["architecture"]["host"]
    assert all(r["last"] is None and r["change"] is None for r in row["rows"])


def _indicators_section(text: str) -> str:
    return text.split("## Indicators\n", 1)[1].split("\n## ", 1)[0]


def test_the_report_renders_indicator_rows_as_a_table(tmp_path: Path) -> None:
    """177 R5: each command in config order, by name; rows as a table against the last report,
    anything else as one sentence. No raw output or stderr reaches the report."""
    root = _repo(tmp_path)
    _retro_report_at(root, "2026-10-10", LAST)
    (root / "rows.jsonl").write_text(
        ROWS + '{"name": "a | b", "value": 0.5, "unit": "x"}\n', encoding="utf-8", newline="\n"
    )
    (root / "plain.txt").write_text("secret-output\n", encoding="utf-8", newline="\n")
    (root / "fail.sh").write_text(
        "cat plain.txt; echo secret-stderr >&2; exit 3\n", encoding="utf-8", newline="\n"
    )
    _config(root, '[retro]\nindicators = ["cat rows.jsonl", "cat plain.txt", "sh fail.sh"]\n')
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    section = _indicators_section(text)
    assert "{{indicators}}" not in text
    assert section.index("`cat rows.jsonl`") < section.index("`cat plain.txt`")
    assert "| Indicator | Unit | Value | Last retrospective | Change |" in section
    assert "| src/drafts.py::save | commits | 5 | 7 | −2 |" in section
    assert "| src/drafts.py::save | lines | 40 | 40 | 0 |" in section
    assert "| cycles | — | 2 | — | — |" in section
    assert "| a \\| b | x | 0.5 | — | — |" in section
    assert "output isn't indicator rows (line 1 isn't a JSON object), so it is in" in section
    assert "failed: exited 3" in section
    assert "secret-output" not in text and "secret-stderr" not in text and "band" not in section
    ran = sdlc.retro._evidence(root, ["sleep 5"], timeout=0.1)
    host = sdlc.retro._indicator_rows(root, None, ran)
    assert "timed out" in sdlc.retro._indicators_text(host)


def test_the_report_says_no_indicators_set(tmp_path: Path) -> None:
    """177 R6."""
    root = _repo(tmp_path)
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert _indicators_section(text).strip() == (
        "No indicators set: name commands in retro.indicators (.sdlc/config.toml) to see them here."
    )


def test_indicator_rows_round_trip_through_the_report() -> None:
    """177 R8: what the table shows is what the next retrospective reads back."""
    rows = [
        {"name": "a | b", "unit": "", "value": 2.0},
        {"name": "back\\slash|", "unit": "u|v", "value": 0.1},
        {"name": "neg", "unit": "lines", "value": -3},
        {"name": "big", "unit": "", "value": 12345.678},
    ]
    host = [{"command": "x", "error": None, "exit": 0, "not_rows": None,
             "rows": [{**r, "last": 1, "change": round(r["value"] - 1, 3), "extra": {}}
                      for r in rows]}]  # fmt: skip
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    text = sdlc.retro.render_report(template, {"process": _views([])}, indicators=host)
    assert sdlc.retro.indicators.report_rows(text) == {
        (r["name"], r["unit"]): r["value"] for r in rows
    }


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


def _classified(root: Path, name: str, design: int, ship: int, named: tuple = ()) -> None:
    """A change whose `Close` commit classified its extra stops, with `design` and `ship`
    `after_gate` stops and the `Sdlc-AfterGate` lines in `named`."""
    _close(root, name, tier=2)
    close = _git(root, "log", "-1", "--format=%B")
    _git(root, "commit", "-q", "--amend", "-m", close + "\n\n" + "\n".join([
        "Sdlc-Mode: manual",
        "Sdlc-Totals: elapsed=60 agent=20 response=5 away=0 blocked=0 stops=8 required=5 "
        "target=6 allowance=1 prompts=0 prompt_modes=auto harness=0 command=0",
        f"Sdlc-Extra: design after_gate={design} revise=0 asked=0 unprompted=0 interrupt=0 fix=0 "
        "harness=0 command=0",
        f"Sdlc-Extra: ship after_gate={ship} revise=0 asked=0 unprompted=0 interrupt=0 fix=0 "
        "harness=0 command=0",
        *named,
    ]))  # fmt: skip


def test_retro_names_the_skill_an_after_gate_stop_followed(tmp_path: Path) -> None:
    """169 R12: each skill's after-gate stops add up from the `Sdlc-AfterGate` lines; a commit
    closed before them keeps its stops in the kinds, unnamed, never under a skill."""
    root = _repo(tmp_path)
    _classified(root, "001-keep-one-draft", 1, 2)  # before the lines
    _classified(
        root,
        "002-draft-titles",
        1,
        1,
        ("Sdlc-AfterGate: sdlc:ship stops=1", "Sdlc-AfterGate: sdlc:spec stops=1"),
    )
    _classified(root, "003-draft-dates", 0, 3, ("Sdlc-AfterGate: sdlc:ship stops=3",))
    extra = _retro(root)["metrics"]["extra"]
    assert extra["kinds"]["after_gate"] == {"count": 8, "changes": 3}
    assert extra["after_gate_by"] == {
        "sdlc:ship": {"count": 4, "changes": 2}, "sdlc:spec": {"count": 1, "changes": 1},
    }  # fmt: skip
    assert extra["after_gate_unnamed"] == 3


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
        "dropped": 0, "measured": 3, "unmeasured": 1, "factory": 0, "mode_unknown": 4,
    }  # fmt: skip
    assert [{k: r[k] for k in ("week", "tiers", "total")} for r in out["throughput"]] == [
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
                              "previous": 0.0, "trend": "up",
                              "coverage": {"measured": 4, "of": 4, "greyed": False},
                              "missing_because": {}}  # fmt: skip


def test_with_nothing_measured_the_timed_views_say_so_never_zero() -> None:
    """R2: unmeasured changes are counted where they can be, never as zeros where they can't."""
    out = _views([_rec("001-a", 1, "2026-10-05", None, None)])
    assert out["window"]["measured"] == 0 and out["throughput"][0]["total"] == 1
    assert [out[k] for k in ("cycle", "time", "wip", "capacity")] == [None] * 4
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    text = sdlc.retro.render_report(template, {"process": out})
    assert text.count("Not measured: none of the 1 changes closed has its numbers.") == 3
    assert "0m" not in text


def test_no_figure_folds_speed_and_stability_into_one() -> None:
    """R3: no velocity, no score, in the template or what it renders."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    text = sdlc.retro.render_report(
        template, {"process": _views([_rec("001-a", 1, "2026-10-05", "12:00", 60)])}
    )
    # 184: the `Scorecard` heading holds the letters, never the word.
    for word in (r"\bvelocity\b", r"\bscores?\b"):
        assert not re.search(word, template.lower()) and not re.search(word, text.lower())
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
        '[retro]\nevidence = ["touch ran-evidence"]\nindicators = ["touch ran-indicator"]\n'
        'test_times = ["touch ran-times"]\n', "utf-8"
    )  # fmt: skip
    assert sdlc.retro.retro(root, sdlc.load_config(root)[0])["architecture"]["host"], "it would run"
    # `retro` runs the evidence only with a product doc; the other two run either way.
    assert (root / "ran-indicator").exists() and (root / "ran-times").exists()
    for name in ("ran-evidence", "ran-indicator", "ran-times"):
        (root / name).unlink(missing_ok=True)
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    # 177 R7: the report runs `retro.indicators`, and none of the host's other commands.
    assert not (root / "ran-evidence").exists() and not (root / "ran-times").exists()
    assert (root / "ran-indicator").exists(), "the report runs the indicators"
    (root / "ran-indicator").unlink()
    assert "| 2 | 1 | 1h 16m | 1h 16m | 40m | 1 |" in text
    assert "1 of them were measured" in text and "1 weren't" in text
    # 168 R10: the Value band's figures, from the same function as the JSON's.
    mix, ttu = out["work_mix"], out["time_to_users"]
    assert f"debt {mix['classes']['debt']} (100%), of {mix['n']} classed changes" in text
    assert f"{ttu['why']['unreleased']} not yet released" in text
    assert f"{ttu['releases']} releases in the window" in text
    # Nit 2026-11-19-17: follow-through too, which has nothing to follow here on either side.
    assert out["follow_through"]["since"] is None and out["follow_through"]["n"] == 0
    assert "Follow-through: no earlier retrospective to follow through on." in text
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    assert capsys.readouterr().out.startswith("# Retrospective report\n")
    assert not (root / "ran-evidence").exists() and not (root / "ran-times").exists()


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
    # A host's override without it is reported as breaking, the section and its placeholder
    # (184 R11: `## Spend` now follows `## Indicators`).
    old = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8").split("## Spend")[0]
    assert sdlc._template_misses("retro.md", old) == [
        "the `## Spend` heading",
        "the `{{spend}}` placeholder",
    ]
    # 177 R9: one cut before the indicators misses their section, and what follows it.
    old = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8").split("## Indicators")[0]
    assert sdlc._template_misses("retro.md", old) == [
        "the `## Spend` heading",
        "the `## Indicators` heading",
        "the `{{spend}}` placeholder",
        "the `{{indicators}}` placeholder",
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
        # 170 R10: the catches are counted only in a window holding a factory change.
        mode = ("Sdlc-Mode: manual",) if name == "001-hand" else ("Sdlc-Mode: factory",)
        _close(root, name, texts={f".sdlc/work/{name}/findings.md": text}, trailers=mode)
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


def test_agents_by_role_groups_verifier_with_arbiter(tmp_path: Path) -> None:
    """187 R14: a `Close` commit from before the rename names the arbiter `verifier`; the retro
    groups it with the arbiter's, and a `runs/verifier.sessions` file is the arbiter's sessions."""
    root = _repo(tmp_path)
    _agent_closed(
        root, "001-reopen-drafts", "2026-10-02",
        "verifier runs=1 agent=5 model=model-a " + AGENT_COUNTS.format(0, 0, 0, 0),
    )  # fmt: skip
    _agent_closed(
        root, "002-draft-titles", "2026-10-03",
        "arbiter runs=2 agent=5 model=model-a " + AGENT_COUNTS.format(0, 0, 0, 0),
    )  # fmt: skip
    agents = _retro(root)["spend"]["agents"]
    assert [(g["role"], g["model"], g["changes"], g["runs"]) for g in agents["groups"]] == [
        ("arbiter", "model-a", 2, 3)
    ]
    files = {"runs/verifier.sessions": "s-1\n", "runs/arbiter.sessions": "s-2\n"}
    roles = sdlc.factory_records.session_roles(files.get, lambda _: "\n".join(files))
    assert roles == {"s-1": "arbiter", "s-2": "arbiter"}


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


def test_lead_time_is_given_by_way_across_tiers() -> None:
    """176 R2: per way, over every tier, the count, median and nearest-rank p85; a way with no
    measured change is n 0 and null figures; the per-tier groups are as they were."""
    changes = [
        _led("001-a", 1, "factory", {"lead": 10}),
        _led("002-b", 2, "factory", {"lead": 30}),
        _led("003-c", 2, "factory", {"lead": 20}),
        _led("004-d", 1, "manual", {"lead": 40}),
        _led("005-e", 1, "manual", None),
    ]
    lead = _views(changes)["lead"]
    assert lead["ways"] == {
        "factory": {"n": 3, "median": 20, "p85": 30},
        "manual": {"n": 1, "median": 40, "p85": 40},
        "unknown": {"n": 0, "median": None, "p85": None},
    }
    assert [(g["tier"], g["way"], g["n"]) for g in lead["groups"]] == [
        ("1", "factory", 1), ("1", "manual", 1), ("2", "factory", 2),
    ]  # fmt: skip


def test_throughput_counts_each_week_by_way_and_by_work_class() -> None:
    """176 R3: each week's row counts its changes by way and by work class, every key there with
    its 0, and each of the two sums to the row's total."""
    a = _led("001-a", 1, "factory", None)
    b = _led("002-b", 2, "manual", None)
    c = _rec("003-c", 2, "2026-10-13", None, None)
    a["work"], b["work"] = {"class": "fix"}, {"class": "process"}
    rows = _views([a, b, c])["throughput"]
    assert rows == [
        {"week": "2026-10-05", "tiers": {"1": 1, "2": 1}, "total": 2,
         "ways": {"factory": 1, "manual": 1, "unknown": 0},
         "classes": {"fix": 1, "capability": 0, "process": 1, "debt": 0, "unclassed": 0}},
        {"week": "2026-10-12", "tiers": {"2": 1}, "total": 1,
         "ways": {"factory": 0, "manual": 0, "unknown": 1},
         "classes": {"fix": 0, "capability": 0, "process": 0, "debt": 0, "unclassed": 1}},
    ]  # fmt: skip
    for row in rows:
        assert sum(row["ways"].values()) == sum(row["classes"].values()) == row["total"]


def test_the_report_s_throughput_shows_work_classes(tmp_path: Path) -> None:
    """176 R4: the report classes each change before it counts the weeks, so a `fix` change reads
    `fix` in the throughput table, as in `retro`'s JSON, never `unclassed`."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", reworks="000", closed="2026-10-05",
           trailers=("Sdlc-Mode: manual",))  # fmt: skip
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "| Week of | Tiers | Ways | Classes | Closed |" in text
    assert "| 2026-10-05 | 1: 1 | manual: 1 | fix: 1 | 1 |" in text, text
    week = _retro(root)["process"]["throughput"][0]
    assert week["classes"]["fix"] == 1 and week["ways"]["manual"] == 1


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
    assert a["lead"] == {
        "measured": 0, "unmeasured": 2, "groups": [], "shares": {},
        "ways": {w: {"n": 0, "median": None, "p85": None} for w in WAYS},
        "coverage": {"measured": 0, "of": 2, "greyed": True},
        "missing_because": {"closed before lead time was recorded": 2},
    }  # fmt: skip


def test_the_report_shows_lead_time_under_cycle_time() -> None:
    """162 R15: the lead table and the shares under the elapsed table, or alone."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    both = [_led("001-a", 2, "factory", {"lead": 250, "ready_wait": 100}, elapsed=60),
            _led("002-b", 2, "factory", None, elapsed=30)]  # fmt: skip
    text = sdlc.retro.render_report(template, {"process": _views(both)})
    assert "| Tier | Changes | Median elapsed |" in text
    assert "| Tier | Way | Changes | Median lead | 85th percentile |" in text
    assert "| 2 | factory | 1 | 4h 10m | 4h 10m |" in text
    assert "ready and waiting 40% (of 1)" in text and "1 change has no lead time" in text
    alone = sdlc.retro.render_report(
        template, {"process": _views([_led("001-a", 1, "manual", {"lead": 30})])}
    )
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


def test_a_change_touching_only_setup_s_record_is_process_work(tmp_path: Path) -> None:
    """176 R12 (nit 2026-11-19-15): setup's record is a `.sdlc/` path like any other, so a
    change whose only edit outside its folder is `.sdlc/setup.json` is process work."""
    root = _repo(tmp_path)
    _close(root, "001-setup-record", files=(".sdlc/setup.json",))
    (change,) = _retro(root)["changes"]
    assert change["work"]["class"] == "process", change["work"]


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


def _retire(root: Path, subject: str, *gone: str) -> None:
    """Remove `gone` (whole entries) from the register in one commit with `subject`, as
    `inbox-commit` does."""
    register = root / ".sdlc" / "work" / "inbox.md"
    text = register.read_text(encoding="utf-8")
    for entry in gone:
        text = text.replace(entry, "")
    register.write_text(text, encoding="utf-8")
    _git(root, "commit", "-q", "-am", subject)


RETIRED_DIRECTION = """\
# Direction

## Milestones

### M1. Given up seed by seed

Groups: 2026-10-09-1, "Second seed"

### M2. Partly built

Groups: 001, 2026-10-09-3

### M3. Lost

Groups: "Deleted by hand"
"""


def test_a_grouped_seed_retired_by_inbox_commit_reads_dropped(tmp_path: Path) -> None:
    """176 R9, R10: a grouped seed gone from the register, which a `Retire` subject names, is
    `dropped`, whether the milestone groups it by id or by its quoted title; one gone without a
    `Retire` is still `vanished`. `retired_entries()` gives each retired entry's title from the
    register before its commit."""
    root = _repo(tmp_path)
    seeds = [_seed("2026-10-09-1", "First seed"), _seed("2026-10-09-2", "Second seed"),
             _seed("2026-10-09-4", "Deleted by hand")]  # fmt: skip
    _filed(root, "# Inbox\n\n" + "".join(seeds))
    _retire(root, "File 2026-10-10-1; Retire 2026-10-09-1, 2026-10-09-2", *seeds[:2])
    _retire(root, "tidy the register", seeds[2])
    assert sdlc.retired_entries(root, "main") == [
        {"id": "2026-10-09-1", "title": "First seed"},
        {"id": "2026-10-09-2", "title": "Second seed"},
    ]
    items = sdlc.direction_items(RETIRED_DIRECTION)["items"]
    verdicts = sdlc._milestone_verdicts(root, items, [], "main")
    assert [(r["entry"], r["verdict"]) for r in verdicts["M1"]] == [
        ("2026-10-09-1", "dropped"), ("Second seed", "dropped"),
    ]  # fmt: skip
    assert [r["verdict"] for r in verdicts["M3"]] == ["vanished"]
    assert not hasattr(sdlc.retro, "_retired_ids"), "one reader of Retire subjects"


def test_a_milestone_whose_grouped_seeds_were_retired_follows_through_as_dropped(tmp_path) -> None:
    """176 R11: every grouped row dropped is a `dropped` milestone; closed or shipped beside
    dropped is `done`; never `carried`."""
    root = _repo(tmp_path)
    seeds = [_seed("2026-10-09-1", "First seed"), _seed("2026-10-09-2", "Second seed"),
             _seed("2026-10-09-3", "Third seed")]  # fmt: skip
    _retrospective(root, "2026-10-10", RETIRED_DIRECTION.split("### M3")[0],
                   "# Inbox\n\n" + "".join(seeds))  # fmt: skip
    _close(root, "001-reopen-drafts", closed="2026-10-12")
    _retire(root, "Retire 2026-10-09-1, 2026-10-09-2, 2026-10-09-3", *seeds)
    milestones = _retro(root)["follow_through"]["milestones"]
    assert [(r["id"], r["verdict"]) for r in milestones["rows"]] == [
        ("M1", "dropped"), ("M2", "done"),
    ]  # fmt: skip


def test_without_an_earlier_retrospective_follow_through_is_unmeasured_not_zero(tmp_path) -> None:
    """168 R9: nothing to follow through on is null, never a zero share."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    ft = _retro(root)["follow_through"]
    assert ft["since"] is None and ft["n"] == 0
    assert ft["share"] is None and ft["seeds"] is None and ft["milestones"] is None
    assert any("no earlier retrospective" in m for m in ft["missing"])


def test_the_report_shows_the_value_figures_in_its_window(tmp_path: Path) -> None:
    """168 R10: one sentence each for work mix, time to users and follow-through, each with its
    `n` and what it left out; since 184 R2, opening the scorecard after the window's sentence."""
    root = _repo(tmp_path)
    _retrospective(root, "2026-10-01", "# Direction\n\n## Milestones\n\n### M1. Drafts\n",
                   "# Inbox\n\n" + _seed("2026-09-30-1", "Reopen drafts"))  # fmt: skip
    _close(root, "001-reopen-drafts", impact="minor", idea="2026-09-30-1", closed="2026-10-02")
    _close(root, "002-draft-sync", closed="2026-10-03")
    _released(root, "v1.0.0", "2026-10-04T12:00:00")
    _close(root, "003-draft-titles", impact="sometime", closed="2026-10-05")
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "From 2026-10-01 to 2026-10-24" in _part(text, "Window")
    window = _part(text, "Scorecard")
    assert window.startswith("\nWork mix:")
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
    # Nit 2026-11-19-17: the sentence's figures are `retro`'s own.
    ft = _retro(root)["follow_through"]
    seeds, milestones = ft["seeds"], ft["milestones"]
    assert (ft["since"], ft["n"], ft["share"]) == ("2026-10-01", 2, 0.5)
    assert (seeds["n"], seeds["done"] + seeds["dropped"]) == (1, 1)
    assert (milestones["n"], milestones["done"] + milestones["dropped"]) == (1, 0)


def test_without_a_value_band_the_window_is_as_before() -> None:
    process = _views([])
    text = sdlc.retro.render_report("{{window}}", {"process": process})
    assert "Work mix" not in text and "Time to users" not in text


# ---------------------------------------------------------------- how often the factory asked (169)

READY = "DECISION: READY\n\nThe build holds.\n"
ESCALATE = "DECISION: ESCALATE\n\n- ESCALATED: D1: the retention call\n"


def _run(files: dict[str, str]):
    """`show` and `listing` over a change folder held as `{rel: text}`, as retro's are at a
    change's own commit."""

    def show(rel: str) -> str | None:
        return files.get(rel)

    def listing(rel: str) -> str:
        prefix = f"{rel}/" if rel else ""
        return "\n".join(sorted(p for p in files if p.startswith(prefix)))

    return show, listing


def test_autonomy_counts_are_none_for_a_change_built_by_hand() -> None:
    """169 R1: no decision file is a change built by hand: None, never a dict of zeros."""
    hand = {"intent.md": "# 001\n", "findings.md": "# Findings\n"}
    assert sdlc.factory_records.autonomy_counts(*_run(hand)) is None
    counts = sdlc.factory_records.autonomy_counts(*_run({**hand, "decision.md": READY}))
    assert isinstance(counts, dict) and counts["escalations"] == 0


def test_autonomy_counts_every_escalation_current_and_archived() -> None:
    """169 R2: each archived `decision-<n>.md` is a past escalation, read as the current one is."""
    files = {"decision.md": READY, "decision-1.md": ESCALATE, "decision-2.md": ESCALATE,
             "reviews/round-1/decision-3.md": ESCALATE}  # fmt: skip
    counts = sdlc.factory_records.autonomy_counts(*_run(files))
    assert counts["escalations"] == 2 and counts["unread"] == []
    alone = sdlc.factory_records.autonomy_counts(*_run({"decision.md": ESCALATE}))
    assert alone["escalations"] == 1


LEDGER = """\
# Decisions

- [x] D1 (builder round 1, default): Page at 50? → decided: the assumed default, confirmed
  - OPTION: 50 — one screen
- [x] D2 (builder round 1, default): Keep 30 days? → decided: the assumed default, confirmed when landing
- [x] D3 (builder round 1, default): Sort by date? → decided: by title, as the list reads
- [x] D4 (builder round 2, default): Badge? → settled by the approver: the spec's R3 says so
- [x] D5 (builder round 1, default): Old badge? → superseded by D6
- [ ] D6 (builder round 2, default): New badge?
- [x] D7 (builder round 1, blocking): Forever or 30 days? → decided: 30 days
- [ ] D8 (builder round 2, blocking): Upgrade?
- [x] D9 (approver round 1, look): the screenshot → decided: seen
- [x] D10 (approver round 1, look): the copy → decided: read every label
- [ ] D11 (approver round 2, look): the colours
- [x] R1 (person, restart): start over
not a ledger line
"""  # noqa: E501


def test_autonomy_counts_read_each_ledger_answer_by_its_mark() -> None:
    """169 R3: a landing's blanket yes is never a kept default (`KEPT_ANSWER` is a prefix of
    `CONFIRMED`), and an approver's settled or superseded line is never the person's answer."""
    fr = sdlc.factory_records
    assert fr.CONFIRMED.startswith(fr.KEPT_ANSWER)
    counts = fr.autonomy_counts(*_run({"decision.md": READY, "decisions.md": LEDGER}))
    assert counts["defaults"] == {
        "kept": 1, "confirmed": 1, "changed": 1, "settled": 1, "superseded": 1, "open": 1,
    }  # fmt: skip
    assert counts["blocking"] == {"answered": 1, "open": 1}
    assert counts["looks"] == {"seen": 1, "checked": 1, "open": 1}


def test_autonomy_counts_tell_a_landing_mend_from_a_build_mend() -> None:
    """169 R4: `runs/mended` holds `<role> <n>` for a build's mend and `<role> land-<n>` for a
    landing's; a line of neither shape is skipped."""
    mended = "builder 1\napprover 2\ncode land-1\nbuilder\nreviewer round-2\n\nverifier land-x\n"
    files = {"decision.md": READY, "runs/mended": mended}
    assert sdlc.factory_records.autonomy_counts(*_run(files))["mends"] == {"build": 2, "landing": 1}
    plain = sdlc.factory_records.autonomy_counts(*_run({"decision.md": READY}))
    assert plain["mends"] == {"build": 0, "landing": 0}


def _factory(root: Path, name: str, files: dict[str, str], **kw) -> None:
    """A factory change closed with `files` in its folder, `{rel: text}`, as its run left them."""
    _close(root, name, tier=2, texts={f".sdlc/work/{name}/{r}": t for r, t in files.items()}, **kw)


def _autonomy(root: Path) -> dict:
    return _retro(root)["autonomy"]


def test_retro_autonomy_leaves_hand_built_changes_out(tmp_path: Path) -> None:
    """169 R6: a window of changes built by hand has no factory figure: every `n` 0 and every rate
    or per-change figure null, never 0."""
    root = _repo(tmp_path)
    _close(root, "001-keep-one-draft")
    _close(root, "002-draft-titles", texts={".sdlc/work/002-draft-titles/findings.md": "# F\n"})
    out = _autonomy(root)
    assert (out["factory"], out["by_hand"]) == (0, 2)
    figures = [v for v in out.values() if isinstance(v, dict)]
    assert figures and all(f["n"] == 0 for f in figures), out
    nulls = ("per_change", "rate", "share", "seen_share")
    assert all(f[k] is None for f in figures for k in nulls if k in f), out
    assert out["overturned"]["count"] is None


def test_retro_autonomy_counts_auto_landed_from_the_change_commit(tmp_path: Path) -> None:
    """169 R7, R16: `Sdlc-Landed` on the change's own commit says who landed it; one on the
    `Close` commit alone is a change shipped by hand. Escalations, asks and mends add up over the
    factory changes only, and retro writes nothing."""
    root = _repo(tmp_path)
    _factory(root, "001-keep-one-draft", {"decision.md": READY}, own=("Sdlc-Landed: by=auto",))
    _factory(root, "002-draft-titles", {"decision.md": ESCALATE, "decision-1.md": ESCALATE,
             "decisions.md": LEDGER, "runs/mended": "builder 1\ncode land-1\n"},
             own=("Sdlc-Landed: by=person unreviewed=0",))  # fmt: skip
    _factory(root, "003-draft-dates", {"decision.md": READY}, trailers=("Sdlc-Landed: by=auto",))
    _close(root, "004-by-hand")
    before = _state(root)
    out = _autonomy(root)
    assert _state(root) == before
    assert (out["factory"], out["by_hand"]) == (3, 1)
    assert out["auto_landed"] == {"auto": 1, "person": 1, "shipped": 1, "share": 0.33, "n": 3}
    assert out["escalations"] == {"total": 2, "changes": 1, "per_change": 0.67, "n": 3}
    assert out["spurious_stops"] == {
        "build": 1, "landing": 1, "changes": 1, "per_change": 0.67, "n": 3,
    }  # fmt: skip
    assert out["asked"] == {"blocking": 1, "default": 2, "look": 2, "per_change": 1.67, "n": 3,
                            "missing_because": {"built by hand": 1}}  # fmt: skip
    assert out["looks"] == {"seen": 1, "checked": 1, "open": 1, "seen_share": 0.5, "n": 2}


def test_retro_autonomy_rates_kept_defaults_without_the_landings_yes(tmp_path: Path) -> None:
    """169 R8 (R3 through `retro()`): the kept-default rate is kept over kept and changed; the
    landing's confirmation and the approver's settled calls sit beside it."""
    root = _repo(tmp_path)
    _factory(root, "001-keep-one-draft", {"decision.md": READY, "decisions.md": LEDGER})
    kept = _autonomy(root)["kept_default"]
    assert kept == {"kept": 1, "changed": 1, "rate": 0.5, "n": 2, "confirmed": 1, "settled": 1}
    # Nit 2026-11-19-20: with confirmed and settled lines outnumbering the rest, the rate's
    # denominator is still kept and changed alone: 2 of 3, never 2 of 8 or 2 of 5.
    _factory(root, "002-draft-titles", {"decision.md": READY, "decisions.md": MORE_CONFIRMED})
    kept = _autonomy(root)["kept_default"]
    assert kept == {"kept": 2, "changed": 1, "rate": 0.67, "n": 3, "confirmed": 3, "settled": 2}


MORE_CONFIRMED = """\
# Decisions

- [x] D1 (builder round 1, default): Page at 50? → decided: the assumed default, confirmed
- [x] D2 (builder round 1, default): Keep 30 days? → decided: the assumed default, confirmed when landing
- [x] D3 (builder round 1, default): Sort by date? → decided: the assumed default, confirmed when landing
- [x] D4 (builder round 2, default): Badge? → settled by the approver: the spec's R3 says so
"""  # noqa: E501


def test_retro_autonomy_says_a_decision_it_cannot_read(tmp_path: Path) -> None:
    """169 R5, R16: a decision with no answer the script reads leaves its change out of the
    escalations' `n`, and is a problem naming the change and the file, never zero escalations."""
    root = _repo(tmp_path)
    _factory(root, "001-keep-one-draft", {"decision.md": ESCALATE})
    _factory(root, "002-draft-titles", {"decision.md": READY, "decision-1.md": "no answer\n"})
    before = _state(root)
    out = _retro(root)
    assert _state(root) == before
    assert out["autonomy"]["escalations"] == {"total": 1, "changes": 1, "per_change": 1.0, "n": 1}
    said = [p for p in out["problems"] if "002-draft-titles" in p]
    assert said and "decision-1.md" in said[0], out["problems"]


def test_retro_says_what_autonomy_cannot_count(tmp_path: Path) -> None:
    """169 R9: an overturned settled call and a stop that cleared by itself leave no record, so
    both are listed as unmeasured with what would record them, and `overturned` has no count."""
    root = _repo(tmp_path)
    _factory(root, "001-keep-one-draft", {"decision.md": READY, "decisions.md": LEDGER})
    out = _retro(root)
    signals = {u["signal"]: u for u in out["unmeasured"]}
    for signal in ("an approver's settled call the person overturned",
                   "a factory stop that cleared with nothing changed"):  # fmt: skip
        assert signal in signals and signals[signal]["needs"], signals
    over = out["autonomy"]["overturned"]
    assert over["count"] is None and over["n"] == 0 and over["unmeasured"]


# ---------------------------------------------------------------- the trust band (170)

FULL_TOTALS = "Sdlc-Totals: elapsed=10 agent=5 response=2 away=0 blocked=0 stops=1 tools=3 words=4"
OLD_TOTALS = "Sdlc-Totals: elapsed=10 agent=5 response=2 away=0 blocked=0 stops=1"


def _trust_window(root: Path) -> None:
    """Six changes, each missing something else: fully measured; history-only with failed
    timing; `lead=none`; closed before `Sdlc-Lead` (and before tool calls); no trailers at all;
    history-only with an unreadable `opened:`."""
    _close(root, "001-full", trailers=(
        "Sdlc-Mode: manual", "Sdlc-Coverage: transcripts=1 stages=ship", FULL_TOTALS,
        "Sdlc-Lead: lead=30 source=git",
    ))  # fmt: skip
    _close(root, "002-history", closed="2026-10-03", trailers=(
        "Sdlc-Mode: manual", "Sdlc-Coverage: none: metrics.transcripts is off lead=failed",
        "Sdlc-Totals: elapsed=10",
    ))  # fmt: skip
    _close(root, "003-no-opened", closed="2026-10-04", trailers=(
        "Sdlc-Mode: manual", "Sdlc-Coverage: transcripts=1 stages=ship lead=none", FULL_TOTALS,
    ))  # fmt: skip
    _close(root, "004-before-lead", closed="2026-10-05", trailers=(
        "Sdlc-Mode: manual", "Sdlc-Coverage: transcripts=1 stages=ship", OLD_TOTALS,
    ))  # fmt: skip
    _close(root, "005-bare", closed="2026-10-06")
    _close(root, "006-bad-opened", closed="2026-10-07", trailers=(
        "Sdlc-Coverage: none: no transcripts for this repo lead=bad-opened runtime=failed",
        "Sdlc-Totals: elapsed=10",
    ))  # fmt: skip


def test_every_headline_says_its_coverage_and_why_the_rest_is_missing(tmp_path: Path) -> None:
    """170 R4, R5: each of the four headlines carries `coverage` and `missing_because`, read from
    what each commit carries, and the reasons add up to what isn't measured."""
    root = _repo(tmp_path)
    _trust_window(root)
    out = _retro(root)
    blocks = {
        "lead": out["process"]["lead"], "escapes": out["process"]["escapes"],
        "metrics": out["metrics"], "spend": out["spend"],
    }  # fmt: skip
    for name, block in blocks.items():
        cov, why = block["coverage"], block["missing_because"]
        assert cov["of"] == 6, name
        assert sum(why.values()) == cov["of"] - cov["measured"], name
    assert blocks["lead"]["coverage"] == {"measured": 1, "of": 6, "greyed": True}
    assert blocks["lead"]["missing_because"] == {
        "timing failed": 1, "no opened: line": 1, "closed before lead time was recorded": 1,
        "not measured at close": 1, "opened: unreadable": 1,
    }  # fmt: skip
    assert blocks["metrics"]["coverage"] == {"measured": 3, "of": 6, "greyed": False}
    assert blocks["metrics"]["missing_because"] == {
        "metrics.transcripts is off": 1, "not measured at close": 1,
        "no transcripts for this repo": 1,
    }  # fmt: skip
    assert blocks["spend"]["coverage"] == {"measured": 2, "of": 6, "greyed": True}
    assert blocks["spend"]["missing_because"] == {
        "metrics.transcripts is off": 1, "closed before tool calls and words were counted": 1,
        "not measured at close": 1, "no transcripts for this repo": 1,
    }  # fmt: skip
    assert blocks["spend"]["missing_because"] == blocks["spend"]["why"], "one reading, not two"
    assert blocks["escapes"]["coverage"] == {"measured": 6, "of": 6, "greyed": False}
    assert blocks["escapes"]["missing_because"] == {}


@pytest.mark.parametrize(
    ("measured", "of", "greyed"), [(4, 10, True), (5, 10, False), (0, 0, False)]
)
def test_a_headline_under_half_its_changes_is_greyed(measured: int, of: int, greyed: bool) -> None:
    """170 R6: greyed exactly when fewer than half the window's changes are measured."""
    changes = [{"n": n} for n in range(of)]
    got = sdlc.retro._coverage(changes, lambda c: c["n"] < measured, lambda c: "a reason")
    assert got["coverage"] == {"measured": measured, "of": of, "greyed": greyed}
    assert got["missing_because"] == ({"a reason": of - measured} if of > measured else {})


def _window_section(text: str) -> str:
    """The Trust band's place: `## Scorecard` since 184 R2, `## Window` before."""
    return text.split("## Scorecard", 1)[1].split("\n## ", 1)[0]


def test_the_report_greys_a_thin_headline(tmp_path: Path) -> None:
    """170 R7: a *Coverage* line per headline after the window's sentence, in italics and
    marked a hint under half its changes; the template is left as it is."""
    root = _repo(tmp_path)
    _trust_window(root)
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    lines = {ln.split(":", 1)[0].strip("-* "): ln for ln in _window_section(text).splitlines()
             if "Coverage, " in ln}  # fmt: skip
    assert set(lines) == {"Coverage, lead time", "Coverage, escape rate",
                          "Coverage, the person's minutes", "Coverage, spend",
                          "Coverage, cost per landed change", "Coverage, waste share"}  # fmt: skip
    lead, spend = lines["Coverage, lead time"], lines["Coverage, spend"]
    for thin in (lead, spend):
        assert thin.startswith("- *") and thin.endswith("a hint: under half the changes*"), thin
    assert "1 of 6 changes" in lead and "timing failed 1" in lead and "opened: unreadable 1" in lead
    for full in (lines["Coverage, escape rate"], lines["Coverage, the person's minutes"]):
        assert not full.startswith("- *") and "a hint" not in full, full
    assert "6 of 6 changes" in lines["Coverage, escape rate"]
    minutes = lines["Coverage, the person's minutes"]
    assert "3 of 6 changes" in minutes and "metrics.transcripts is off 1" in minutes
    assert "{{" not in text
    # Without the metrics block, its line says so; with no change closed there is no line.
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    views = _views([_rec("001-a", 1, "2026-10-05", "12:00", 60)])
    alone = sdlc.retro.render_report(template, {"process": views})
    assert "- Coverage, the person's minutes: not given." in alone
    empty = sdlc.retro.render_report(template, {"process": _views([])})
    assert "Coverage, " not in empty


def _ran(runtime: str) -> tuple[str, ...]:
    return ("Sdlc-Mode: manual", f"Sdlc-Runtime: {runtime}")


def _underneath_repo(tmp_path: Path) -> Path:
    """Two retrospectives: 002 and 003 in the last window (003 from before `Sdlc-Runtime`, with a
    role's model), 004 and 005 in this one (005 with nothing)."""
    root = _repo(tmp_path)
    _close(root, "001-oldest", trailers=_ran("claude=1.0.0 models=model-z plugin=0.0.9"))
    _record(root, "2026-10-01")
    _close(root, "002-a", closed="2026-10-03",
           trailers=_ran("claude=1.0.0 models=model-a plugin=0.1.0"))  # fmt: skip
    _close(root, "003-b", closed="2026-10-04", trailers=(
        "Sdlc-Mode: factory", "Sdlc-Role: builder runs=1 agent=3 model=model-a",
    ))  # fmt: skip
    _record(root, "2026-10-10")
    _close(root, "004-c", closed="2026-10-12",
           trailers=_ran("claude=1.0.1 models=model-a plugin=0.1.0"))  # fmt: skip
    _close(root, "005-d", closed="2026-10-13")
    return root


def test_what_changed_underneath_compares_with_the_last_window(tmp_path: Path) -> None:
    """170 R8: each dimension's values in this window and the last, how many changes recorded
    them, and what changed: null, never false, when a side recorded none."""
    under = _retro(_underneath_repo(tmp_path))["process"]["underneath"]
    assert under["window"] == {
        "claude": {"1.0.1": 1}, "models": {"model-a": 1}, "plugin": {"0.1.0": 1},
        "recorded": 1, "unrecorded": 1,
    }  # fmt: skip
    assert under["previous"] == {
        "claude": {"1.0.0": 1}, "models": {"model-a": 2}, "plugin": {"0.1.0": 1},
        "recorded": 1, "unrecorded": 1,
    }  # fmt: skip
    assert under["changed"] == {"claude": True, "models": False, "plugin": False}

    old = sdlc.retro._underneath_side
    rec = lambda m: {"metrics": m}  # noqa: E731
    now = [rec({"runtime": {"claude": "1.0.1,1.0.2", "models": "m", "plugin": "0.2.0"}})]
    before = [rec({"roles": {"builder": {"model": "m"}}}), rec(None)]
    got = sdlc.retro.underneath(now, before)
    assert got["window"]["claude"] == {"1.0.1": 1, "1.0.2": 1}
    assert got["changed"] == {"claude": None, "models": False, "plugin": None}
    assert got["previous"] == old(before) and got["previous"]["unrecorded"] == 2
    first = sdlc.retro.underneath(now, None)
    assert first["previous"] is None
    assert first["changed"] == {"claude": None, "models": None, "plugin": None}


def test_the_last_window_runs_from_the_start_with_one_retrospective(tmp_path: Path) -> None:
    """170 R8: with one retrospective the last window is all history before it; with none there
    is no last window."""
    root = _repo(tmp_path)
    _close(root, "001-a", trailers=_ran("claude=1.0.0 plugin=0.1.0"))
    assert _retro(root)["process"]["underneath"]["previous"] is None
    _record(root, "2026-10-01")
    _close(root, "002-b", closed="2026-10-03", trailers=_ran("claude=1.0.0 plugin=0.1.1"))
    under = _retro(root)["process"]["underneath"]
    assert under["previous"]["plugin"] == {"0.1.0": 1}
    assert under["changed"] == {"claude": False, "models": None, "plugin": True}


def test_the_report_says_what_changed_underneath(tmp_path: Path) -> None:
    """170 R9: one line after the coverage lines, each dimension against the last window, what
    changed and how many recorded none; never a path, whatever a trailer says."""
    root = _underneath_repo(tmp_path)
    _close(root, "006-e", closed="2026-10-14",
           trailers=_ran("claude=made/up/1.0.2 plugin=~/0.1.0"))  # fmt: skip
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    window = _window_section(text)
    [line] = [ln for ln in window.splitlines() if "What changed underneath" in ln]
    assert window.index("Coverage, spend") < window.index(line)
    assert "/" not in line and "~" not in line, line
    assert "Claude Code" in line and "changed" in line and "1.0.0" in line
    assert "1 of 3 changes in this window recorded none" in line, line
    (tmp_path / "first").mkdir()
    root2 = _repo(tmp_path / "first")
    _close(root2, "001-a", trailers=_ran("claude=1.0.0 plugin=0.1.0"))
    first = sdlc.retro.retro_report(root2, sdlc.load_config(root2)[0], date(2026, 10, 24))
    [line] = [ln for ln in first.splitlines() if "What changed underneath" in ln]
    assert "no earlier window to compare" in line


def test_underneath_reads_history_alone(tmp_path: Path, monkeypatch) -> None:
    """170 R12: no transcript, no `claude`, no plugin manifest: only git runs."""
    root = _underneath_repo(tmp_path)
    real = subprocess.run

    def only_git(args, *a, **kw):
        if not args or Path(str(args[0])).name != "git":
            raise AssertionError(f"retro ran {args[0] if args else args}")
        return real(args, *a, **kw)

    def refuse(*_a, **_kw):
        raise AssertionError("retro reached outside history")

    monkeypatch.setattr(subprocess, "run", only_git)
    monkeypatch.setattr(sdlc.shutil, "which", lambda name, *a, **kw: refuse() if "claude" in
                        str(name) else None)  # fmt: skip
    for name in ("plugin_version", "_project_dirs"):
        monkeypatch.setattr(sdlc, name, refuse)
    monkeypatch.setattr(sdlc.metrics, "read_events", refuse)
    out = _retro(root)
    assert out["process"]["underneath"]["changed"]["claude"] is True
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "What changed underneath" in text


def test_a_window_with_no_factory_changes_says_so(tmp_path: Path) -> None:
    """170 R10: with no `Sdlc-Mode: factory` in the window, no landing-catches figure, a sentence
    in its place, and the changes with no way recorded named."""
    root = _repo(tmp_path)
    _close(root, "001-a", trailers=("Sdlc-Mode: manual",))
    _close(root, "002-b", closed="2026-10-03")
    process = _retro(root)["process"]
    assert (process["window"]["factory"], process["window"]["mode_unknown"]) == (0, 1)
    assert process["landing_catches"] is None
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "No factory changes in this window." in text
    assert "1 change records no way of building" in text
    assert "Landing catches: 0 of 0" not in text
    _close(root, "003-c", closed="2026-10-04", trailers=("Sdlc-Mode: factory",))
    process = _retro(root)["process"]
    assert process["window"]["factory"] == 1 and process["landing_catches"] is not None
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "No factory changes" not in text


def test_a_hosts_retrospective_never_mentions_the_cases(tmp_path: Path, capsys) -> None:
    """170 R11: the skills' cases are this plugin's own; a host's retro and report say nothing of
    them. `tests.times` counts JUnit test cases, which are the host's."""
    root = _underneath_repo(tmp_path)
    _trust_window(root)
    assert not sdlc._own_repo(root)
    assert sdlc.retro.cmd_retro(root, metrics=True) == 0
    out = capsys.readouterr().out
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    report = capsys.readouterr().out

    def keys(value: object, path: tuple = ()) -> list[tuple]:
        if isinstance(value, dict):
            return [p for k, v in value.items() for p in [(*path, k), *keys(v, (*path, k))]]
        if isinstance(value, list):
            return [p for v in value for p in keys(v, path)]
        return []

    named = [p for p in keys(json.loads(out)) if "cases" in str(p[-1]).lower()]
    assert all(p[:2] == ("tests", "times") for p in named), named
    for text in (out, report):
        for said in ("skills' cases", "Skill evals", "run-cases"):
            assert said.lower() not in text.lower(), said


# ---------------------------------------------------------------- what a change cost (174)


def _row(session: str, cost: float | None, purpose: str | None = "build", **kw) -> str:
    """One `costs.jsonl` row as `factory.py agent` writes it: `cost` the session's running total."""
    row = {
        "session": session,
        "role": kw.pop("role", "builder"),
        "model": kw.pop("model", "opus"),
        "duration_ms": kw.pop("ms", 60000),
        **({"purpose": purpose} if purpose else {}),
        **kw,
    }
    return json.dumps(row if cost is None else {**row, "cost_usd": cost})  # fmt: skip


RESUMED = "\n".join([
    _row("b", 0.5, task="build", round=1),
    _row("b", 0.75, "rework", task="rework", round=1),
    _row("b", None, "mend", task="mend", round=2),
    _row("b", 1.25, "rework", task="rework", round=2),
    _row("r1", 0.2, role="code", model="sonnet", task="review", round=1),
    _row("r2", 0.3, "rework", role="code", model="sonnet", task="review", round=2),
]) + "\n"  # fmt: skip


@pytest.mark.portable
def test_row_dollars_sum_to_the_changes_cost(tmp_path: Path) -> None:
    """174 R5: each row's dollars are the change in its session's running total, so a builder
    resumed three times is counted once; a row with no cost is unknown, and the next carries it."""
    fr = sdlc.factory_records
    folder = tmp_path / "008-reopen-drafts"
    (folder / "runs").mkdir(parents=True)
    (folder / "runs" / "costs.jsonl").write_text(RESUMED, encoding="utf-8")
    spent = fr.spend_rows(_run({"runs/costs.jsonl": RESUMED})[0])
    assert [r["usd"] for r in spent["rows"]] == [0.5, 0.25, None, 0.5, 0.2, 0.3]
    assert spent["unknown"] == 1 and spent["untagged"] == 0
    total = sum(r["usd"] or 0 for r in spent["rows"])
    assert round(total, 4) == fr.cost(folder)["usd"] == 1.75
    assert [r["minutes"] for r in spent["rows"]] == [1.0] * 6
    assert {(r["role"], r["model"]) for r in spent["rows"]} == {
        ("builder", "opus"), ("code", "sonnet"),
    }  # fmt: skip
    # A total that falls floors at 0, and never takes back what was counted.
    fell = _row("b", 0.5) + "\n" + _row("b", 0.25) + "\n"
    assert [r["usd"] for r in fr.spend_rows(_run({"runs/costs.jsonl": fell})[0])["rows"]] == [
        0.5, 0.0,
    ]  # fmt: skip
    assert fr.spend_rows(_run({})[0]) == {"rows": [], "unknown": 0, "untagged": 0}


@pytest.mark.portable
def test_each_row_counts_in_one_part() -> None:
    """174 R6: untagged first, then a dropped change's every row, then a landing's runs that ended
    by an ejection, then the row's own purpose; the parts sum to the total, and an untagged row of
    a dropped change is never waste."""
    fr = sdlc.factory_records
    costs = "\n".join([
        _row("b", 1.0, task="build", round=1),
        _row("g", 0.5, "gate-fix", task="fix", round=1),
        _row("c", 0.25, "rerun", role="code", task="review", round=1),
        _row("l1", 0.4, "land", role="code", task="land-review", land=1,
             ended="2026-11-01T10:00:00Z"),
        _row("l2", 0.6, "land", role="code", task="land-review", land=2,
             ended="2026-11-02T10:00:00Z"),
        _row("old", 0.1, None),
    ]) + "\n"  # fmt: skip
    ejected = json.dumps({"at": "2026-11-01T10:00:00Z", "land": 1, "cause": "gate"}) + "\n"
    files = {"runs/costs.jsonl": costs, "runs/ejections.jsonl": ejected}
    spent = fr.spend_rows(_run(files)[0])
    parts = [r["part"] for r in spent["rows"]]
    assert parts == ["build", "gate-fix", "rerun", "ejected", "land", "untagged"], parts
    assert set(parts) <= set(fr.PARTS) and spent["untagged"] == 1
    by_part = Counter()
    for r in spent["rows"]:
        by_part[r["part"]] += r["usd"]
    assert round(sum(by_part.values()), 4) == 2.85
    assert "untagged" not in fr.WASTE and {"ejected", "dropped"} <= set(fr.WASTE)
    gone = fr.spend_rows(_run(files)[0], dropped=True)
    assert [r["part"] for r in gone["rows"]] == ["dropped"] * 5 + ["untagged"]


FACTORY = ("Sdlc-Mode: factory",)


def _cost_window(root: Path) -> None:
    """The window R7's test reads, each change's rows a minute each:

    - 001 (tier 2, landed): build 1.00, review 0.50, rework 0.50 (its builder resumed to 1.50),
      mend 0.25: 2.25 and 4 minutes, 0.75 and 2 minutes of it waste.
    - 002 (tier 2, ejected once, then landed): build 1.00, the ejected landing's review 0.40, the
      next landing's 0.60: 2.00 and 3 minutes, 0.40 and 1 minute waste.
    - 003 (dropped): build 0.30, 1 minute, all of it waste.
    - 004 (tier 1, by hand): no rows. 005 (tier 1, factory, before purposes): 0.80 untagged, and
      an untagged row with no cost. 006 (tier 1, factory): no rows. 007 (tier 1, factory): one
      row with no cost.
    """
    ejected = "2026-10-01T10:00:00Z"
    _factory(root, "001-reopen-drafts", {"runs/costs.jsonl": "\n".join([
        _row("b", 1.0, task="build", round=1),
        _row("r", 0.5, role="code", model="sonnet", task="review", round=1),
        _row("b", 1.5, "rework", task="rework", round=1),
        _row("m", 0.25, "mend", role="code", model="sonnet", task="mend", round=2),
    ]) + "\n"}, trailers=FACTORY)  # fmt: skip
    _factory(root, "002-draft-titles", {"runs/costs.jsonl": "\n".join([
        _row("b2", 1.0, task="build", round=1),
        _row("l1", 0.4, "land", role="code", model="sonnet", task="land-review", land=1,
             ended=ejected),
        _row("l2", 0.6, "land", role="code", model="sonnet", task="land-review", land=2,
             ended="2026-10-01T12:00:00Z"),
    ]) + "\n", "runs/ejections.jsonl": json.dumps({"at": ejected, "land": 1, "cause": "gate"})
        + "\n"}, trailers=FACTORY)  # fmt: skip
    _drop(root, "003-draft-sync", trailers=FACTORY, texts={
        ".sdlc/work/003-draft-sync/runs/costs.jsonl": _row("b3", 0.3, task="build", round=1) + "\n",
    })  # fmt: skip
    _close(root, "004-by-hand")
    _close(root, "005-draft-dates", trailers=FACTORY, texts={
        ".sdlc/work/005-draft-dates/runs/costs.jsonl": _row("e", 0.8, None) + "\n"
        + _row("e2", None, None) + "\n",
    })  # fmt: skip
    _close(root, "006-draft-export", trailers=FACTORY)
    _close(root, "007-draft-colours", trailers=FACTORY, texts={
        ".sdlc/work/007-draft-colours/runs/costs.jsonl": _row("g", None, task="build", round=1)
        + "\n",
    })  # fmt: skip


def test_retro_reports_cost_per_landed_change_and_waste(tmp_path: Path) -> None:
    """174 R7, R8: dollars and minutes per landed change by tier, the waste share and its parts,
    spend by role and model, each with its `n`; a change with no dollars is missing, never $0;
    each change's own rows only with `--metrics`; and retro writes nothing."""
    root = _repo(tmp_path)
    _cost_window(root)
    before = _state(root)
    cost = _retro(root)["cost"]
    assert _state(root) == before
    assert cost["per_change"] == {
        "2": {"n": 2, "usd": {"median": 2.125, "total": 4.25},
              "minutes": {"median": 3.5, "total": 7.0}},
        "1": {"n": 1, "usd": {"median": 0.8, "total": 0.8},
              "minutes": {"median": 2.0, "total": 2.0}},
    }  # fmt: skip
    assert cost["coverage"] == {"measured": 3, "of": 6, "greyed": False}
    assert cost["missing_because"] == {
        "built by hand": 1, "no agent runs recorded": 1, "no cost reported": 1,
    }  # fmt: skip
    waste = cost["waste"]
    assert (waste["usd"], waste["of_usd"], waste["share"]) == (1.45, 4.55, 0.32), waste
    assert (waste["minutes"], waste["of_minutes"], waste["minutes_share"]) == (4.0, 8.0, 0.5)
    assert waste["n"] == 3
    assert waste["parts"]["rework"] == {"usd": 0.5, "minutes": 1.0, "runs": 1}
    assert waste["parts"]["mend"] == {"usd": 0.25, "minutes": 1.0, "runs": 1}
    assert waste["parts"]["ejected"] == {"usd": 0.4, "minutes": 1.0, "runs": 1}
    assert waste["parts"]["dropped"] == {"usd": 0.3, "minutes": 1.0, "runs": 1}
    assert waste["parts"]["build"] == {"usd": 2.5, "minutes": 3.0, "runs": 3}
    assert waste["parts"]["land"] == {"usd": 0.6, "minutes": 1.0, "runs": 1}
    assert waste["parts"]["untagged"] == {"usd": 0.0, "minutes": 0.0, "runs": 0}
    assert waste["coverage"] == {"measured": 3, "of": 7, "greyed": True}, "under half"
    assert waste["missing_because"] == {
        "built by hand": 1, "runs recorded before purposes": 1, "no agent runs recorded": 1,
        "no cost reported": 1,
    }  # fmt: skip
    assert cost["by_role"] == {
        "builder": {"usd": 3.6, "minutes": 7.0, "runs": 7, "changes": 5},
        "code": {"usd": 1.75, "minutes": 4.0, "runs": 4, "changes": 2},
    }  # fmt: skip
    assert cost["by_model"] == {
        "opus": {"usd": 3.6, "minutes": 7.0, "runs": 7, "changes": 5},
        "sonnet": {"usd": 1.75, "minutes": 4.0, "runs": 4, "changes": 2},
    }  # fmt: skip
    assert cost["unknown"] == 2
    assert cost["untagged"] == {"runs": 2, "usd": 0.8, "changes": 1}
    named = {c["name"]: c for c in cost["changes"]}
    assert set(named) == {"001-reopen-drafts", "002-draft-titles", "003-draft-sync",
                          "005-draft-dates", "007-draft-colours"}  # fmt: skip
    assert named["001-reopen-drafts"]["usd"] == 2.25 and named["007-draft-colours"]["usd"] is None
    assert named["003-draft-sync"]["state"] == "dropped"


def test_retro_prints_each_changes_cost_only_with_metrics(tmp_path: Path, capsys) -> None:
    """174 R7: `cost.changes` is each change's own figures, printed only with `--metrics`."""
    root = _repo(tmp_path)
    _cost_window(root)
    sdlc.retro.cmd_retro(root)
    lean = json.loads(capsys.readouterr().out)["cost"]
    assert "changes" not in lean and lean["waste"]["n"] == 3
    sdlc.retro.cmd_retro(root, metrics=True)
    assert len(json.loads(capsys.readouterr().out)["cost"]["changes"]) == 5


# ---------------------------------------------------------------- by way of building (176)

WAYS = ("factory", "manual", "unknown")


def _by_hand(root: Path, name: str, tokens: tuple[int, int, int], **kw) -> None:
    """A change built by hand whose close read its transcripts: `in`, `cache_read`, `out`."""
    i, c, o = tokens
    _close(root, name, trailers=("Sdlc-Mode: manual",
                                 f"Sdlc-Totals: elapsed=10 in={i} cache_read={c} out={o}"),
           **kw)  # fmt: skip


def test_a_change_with_no_sdlc_mode_counts_as_unknown_way(tmp_path: Path) -> None:
    """176 R1: the way is `Sdlc-Mode` alone; a `Close` with no `Sdlc-*` lines is `unknown`, even
    when the change's folder held a `decision.md`."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts",
           texts={".sdlc/work/001-reopen-drafts/decision.md": "DECISION: READY\n"})  # fmt: skip
    out = _retro(root)
    assert out["by_way"]["changes"] == {"factory": 0, "manual": 0, "unknown": 1}
    assert out["process"]["throughput"][0]["ways"] == {"factory": 0, "manual": 0, "unknown": 1}


def test_by_way_gives_every_figure_for_each_way_with_its_n(tmp_path: Path) -> None:
    """176 R5: every part names every way, and `changes` sums to the window's closed count;
    throughput is per week over the window's span, which runs from the first close with no
    retrospective."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", closed="2026-10-03", trailers=FACTORY)
    _by_hand(root, "002-draft-titles", (100, 50, 10), closed="2026-10-10")
    out = _retro(root)
    by_way = out["by_way"]
    assert set(by_way) == {"changes", "lead", "throughput", "cost", "escapes"}
    for part in by_way.values():
        assert set(part) == set(WAYS), part
    assert sum(by_way["changes"].values()) == out["process"]["window"]["closed"] == 2
    assert by_way["throughput"]["factory"] == {
        "closed": 1, "weeks": 3.0, "per_week": 0.33, "why": None,
    }  # fmt: skip
    assert by_way["throughput"]["unknown"] == {
        "closed": 0, "weeks": 3.0, "per_week": 0.0, "why": None,
    }  # fmt: skip
    assert by_way["lead"] == out["process"]["lead"]["ways"]
    lean = {w: {k: v for k, v in e.items() if k != "missing_because"}
            for w, e in by_way["escapes"].items()}  # fmt: skip
    assert lean == out["bugs"]["rate"]["window"]["by_way"]
    assert by_way["escapes"]["unknown"]["missing_because"] == {"no unknown change in the window": 0}
    assert "_landed" not in out["cost"]


def test_hand_built_cost_compares_in_tokens_and_is_missing_in_dollars(tmp_path: Path) -> None:
    """176 R6: tokens on both sides from `Sdlc-Totals`, over the changes whose totals came from
    transcripts; dollars only where recorded, a hand-built change missing as `built by hand`,
    never $0; a median with n 0 is null."""
    root = _repo(tmp_path)
    _cost_window(root)
    _by_hand(root, "008-hand-tokens", (100, 50, 10))
    _by_hand(root, "009-hand-more", (200, 100, 20))
    cost = _retro(root)["by_way"]["cost"]
    manual = cost["manual"]
    assert manual["tokens"] == {"n": 2, "median": 240, "missing_because": {}}
    assert manual["usd"] == {"n": 0, "median": None, "missing_because": {"built by hand": 2}}
    factory = cost["factory"]
    assert (factory["usd"]["n"], factory["usd"]["median"]) == (3, 2.0)
    assert factory["usd"]["missing_because"] == {
        "no agent runs recorded": 1, "no cost reported": 1,
    }  # fmt: skip
    assert factory["tokens"] == {
        "n": 0, "median": None, "missing_because": {"not measured at close": 5},
    }  # fmt: skip
    assert cost["unknown"]["usd"]["missing_because"] == {"built by hand": 1}


def test_the_report_compares_the_ways_of_building(tmp_path: Path) -> None:
    """176 R8: the window ends with the *By way of building* table, after the value sentences,
    every figure with its `n` and `–` for a null, never 0; throughput gains its two columns."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", closed="2026-10-03", trailers=FACTORY)
    _by_hand(root, "002-draft-titles", (1000, 500, 100), closed="2026-10-10")
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    # 184 R2: the table is Speed's now, and the Window's sentence stands alone.
    window = _part(text, "Speed")
    assert "By way of building" not in _part(text, "Window")
    rows = {line.split(" | ")[0].strip("| "): line for line in window.splitlines()
            if line.startswith("| ")}  # fmt: skip
    assert rows["By way of building"] == "| By way of building | Factory | By hand | Unknown |"
    assert rows["Changes"] == "| Changes | 1 | 1 | 0 |"
    assert rows["Median lead"] == "| Median lead | – (0) | – (0) | – (0) |"
    assert rows["85th percentile lead"] == "| 85th percentile lead | – (0) | – (0) | – (0) |"
    assert rows["Closed per week"] == "| Closed per week | 0.33 (1) | 0.33 (1) | 0 (0) |"
    assert rows["Median tokens"] == "| Median tokens | – (0) | 1,600 (1) | – (0) |"
    assert rows["Median dollars"] == "| Median dollars | – (0) | – (0) | – (0) |"
    assert rows["Escape rate"] == "| Escape rate | 0 (1) | 0 (1) | – (0) |"
    assert "| Week of | Tiers | Ways | Classes | Closed |" in text
    assert "By way of building" not in sdlc.retro.render_report(
        "{{window}}", {"process": _views([])}
    )


def test_the_report_says_how_far_cost_and_waste_rest(tmp_path: Path) -> None:
    """174 R9: the report's *Coverage* lines say how far the cost per landed change and the waste
    share rest, the waste line naming the runs recorded before purposes, greyed under half."""
    root = _repo(tmp_path)
    _cost_window(root)
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    lines = {line.split(":")[0].strip("-* "): line for line in text.splitlines()}
    cost = lines["Coverage, cost per landed change"]
    assert cost.startswith("- Coverage, cost per landed change: 3 of 6 changes; missing: "), cost
    assert "built by hand 1" in cost and "no cost reported 1" in cost
    waste = lines["Coverage, waste share"]
    assert waste.startswith("- *Coverage, waste share: 3 of 7 changes"), waste
    assert "runs recorded before purposes 1" in waste and "2 runs untagged" in waste, waste
    assert waste.endswith("a hint: under half the changes*"), waste


# ---------------------------------------------------------------- the pipeline's figures (175)


@pytest.mark.portable
def test_none_reason_strips_close_s_words_as_before() -> None:
    """175 R13: the reason loses the `key=value` words close appends, and nothing else."""
    said = "none: no transcripts lead=failed runtime=failed"
    assert sdlc.retro._none_reason(said) == "no transcripts"
    assert sdlc.retro._none_reason("none: no transcripts") == "no transcripts"
    assert sdlc.retro._none_reason("full") is None


@pytest.mark.portable
def test_none_reason_returns_quickly_on_many_equals_tokens() -> None:
    """175 R13 (nit 2026-11-19-21): a hand-written coverage of many `a=b=c=d` tokens and a last
    token without `=` returns within a second. It runs in a child process with a timeout, so a
    regression fails rather than hangs: `re` holds the GIL, so no thread's join could stop it."""
    child = (
        "import importlib.util, sys, time\n"
        "spec = importlib.util.spec_from_file_location('sdlc_nit', sys.argv[1])\n"
        "mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\n"
        "said = 'none: by hand' + ' a=b=c=d' * 40 + ' plain'\n"
        "start = time.monotonic(); got = mod.retro._none_reason(said)\n"
        "assert got == said.removeprefix('none:').strip(), got\n"
        "print(time.monotonic() - start)\n"
    )
    try:
        done = subprocess.run(
            [sys.executable, "-c", child, str(ROOT / "scripts" / "sdlc.py")],
            capture_output=True, encoding="utf-8", timeout=60,
        )  # fmt: skip
    except subprocess.TimeoutExpired:
        pytest.fail("_none_reason backtracked for a minute")
    assert done.returncode == 0, done.stderr
    assert float(done.stdout) < 1.0, done.stdout


def _gate_file(*attempts: tuple) -> str:
    """A gate record as `factory.py gate` writes it: each attempt `(verdict, seconds, waited)`,
    `waited` None for one from before the `Waited:` line."""
    sections = []
    for i, (verdict, seconds, waited) in enumerate(attempts, 1):
        wait = "" if waited is None else f"Waited: {waited}\n"
        sections.append(
            f"## Attempt {i}\n\nVerdict: {verdict}\nCommand: true\nBuild: abc123\nExit: 0\n"
            f"Seconds: {seconds}\n{wait}Tree: unchanged\n\nLast 40 lines of its output:\n\n"
            f"    Seconds: 999\n"
        )
    return f"GATE: {attempts[-1][0]}\n\n" + "\n".join(sections)


def _land_step(moves: int = 0) -> str:
    return f"STEP: close\nROUND: 1\nMOVES: {moves}\nLIMIT: 3\nSINCE: 2026-10-01T10:00:00Z\n"


def _pipeline(root: Path) -> dict:
    return _retro(root)["pipeline"]


def _nulls_and_ns(value, path=()) -> list[tuple]:
    """Every `(path, key, value)` under `value` whose key is `n` or a rate, share, median, p85 or
    per-change figure."""
    found = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k in ("n", "rate", "share", "median", "p85", "per_change"):
                found.append((path, k, v))
            found += _nulls_and_ns(v, (*path, k))
    return found


def test_pipeline_is_null_with_no_factory_change(tmp_path: Path) -> None:
    """175 R1, R12: a window of changes built by hand: every `n` 0 and every rate, share, median
    or percentile null, never 0; no `mends`, which `autonomy.spurious_stops` counts."""
    root = _repo(tmp_path)
    _close(root, "001-keep-one-draft")
    _close(root, "002-draft-titles", own=("Sdlc-Landed: by=person",))
    out = _pipeline(root)
    assert (out["factory"], out["by_hand"]) == (0, 2)
    for key in ("gates", "red_gate", "landing", "depth", "unreviewed"):
        assert key in out, key
    assert "mends" not in out
    assert out["gates"]["previous"] is None, "no retrospective before this window"
    found = _nulls_and_ns(out)
    assert any(k == "median" for _, k, _ in found) and any(k == "rate" for _, k, _ in found)
    wrong = [(p, k, v) for p, k, v in found if (v != 0 if k == "n" else v is not None)]
    assert not wrong, wrong


def test_pipeline_gates_by_window(tmp_path: Path) -> None:
    """175 R2: the round and landing gates' seconds and slot waits, median and nearest-rank 85th
    percentile, this window and the one before; an attempt without `Waited:` counts in
    `seconds.n` and not `wait.n`; the hand gate's record is in neither."""
    root = _repo(tmp_path)
    _factory(root, "001-old-run", {"decision.md": READY,
             "build/round-1.gate.md": _gate_file(("PASS", 5.0, 0.0))})  # fmt: skip
    _retrospective(root, "2026-10-05", "# Direction\n")
    _factory(root, "002-reopen-drafts", {
        "decision.md": READY,
        "build/round-1.gate.md": _gate_file(("FAIL", 10.0, 1.0), ("PASS", 20.0, 2.0)),
        "build/land-1.gate.md": _gate_file(("PASS", 50.0, 5.0)),
        "build/gate.md": _gate_file(("PASS", 999.0, 999.0)),
    }, closed="2026-10-06")  # fmt: skip
    _factory(root, "003-draft-titles", {
        "decision.md": READY,
        "build/round-1.gate.md": _gate_file(("PASS", 30.0, 3.0)),
        "build/round-2.gate.md": _gate_file(("PASS", 40.0, None)),
    }, closed="2026-10-07")  # fmt: skip
    gates = _pipeline(root)["gates"]
    assert gates["window"]["round"]["seconds"] == {"n": 4, "median": 25.0, "p85": 40.0}
    assert gates["window"]["round"]["wait"] == {"n": 3, "median": 2.0, "p85": 3.0}
    assert gates["window"]["land"]["seconds"] == {"n": 1, "median": 50.0, "p85": 50.0}
    assert gates["window"]["land"]["wait"] == {"n": 1, "median": 5.0, "p85": 5.0}
    assert gates["previous"]["round"]["seconds"] == {"n": 1, "median": 5.0, "p85": 5.0}
    assert gates["previous"]["land"]["seconds"] == {"n": 0, "median": None, "p85": None}


def test_pipeline_red_gate_rate(tmp_path: Path) -> None:
    """175 R4: a build is red when any attempt of its round gate failed: one red-then-green build
    and one green build is a rate of 0.5."""
    root = _repo(tmp_path)
    _factory(root, "001-reopen-drafts", {"decision.md": READY,
             "build/round-1.gate.md": _gate_file(("FAIL", 1, 0), ("PASS", 1, 0))})  # fmt: skip
    _factory(root, "002-draft-titles", {"decision.md": READY,
             "build/round-1.gate.md": _gate_file(("PASS", 1, 0))})  # fmt: skip
    _close(root, "003-by-hand")
    assert _pipeline(root)["red_gate"] == {"builds": 2, "red": 1, "rate": 0.5, "n": 2}


def _train_record(name: str, k: int, *gates: str) -> str:
    return f"# {name} — landing train\n\nTRAIN: {k} of 2\nSTACKED ON: main\n" + "".join(
        f"{g}\n" for g in gates
    )


def test_pipeline_landing_train_figures(tmp_path: Path) -> None:
    """175 R5: the landing's gates, ejections by cause, bisections (a red gate over a prefix
    above 1, counted once though two changes' records name it), base moves, accept stops and
    conflicts, over the factory changes with a landing record; one without is missing."""
    root = _repo(tmp_path)
    red = "GATE: 2 FAIL abcdef012345 002-draft-titles/build/land-1.gate.md"
    one = "GATE: 1 PASS 0123456789ab 001-reopen-drafts/build/land-1.gate.md"
    tip = "GATE: 2 PASS fedcba987654 002-draft-titles/build/land-2.gate.md"
    ejected = json.dumps({"at": "2026-10-01T10:00:00Z", "land": 1, "cause": "gate"}) + "\n"
    _factory(root, "001-reopen-drafts", {
        "decision.md": READY, "runs/land-step.md": _land_step(2),
        "runs/land-train.md": _train_record("001-reopen-drafts", 1, red, one),
        "build/land-1.gate.md": _gate_file(("PASS", 1, 0)),
        "build/land-accept.md": _gate_file(("FAIL", 1, 0), ("PASS", 1, 0)),
        "runs/land-times.jsonl": json.dumps({"step": "resolve", "round": 1, "seconds": 4.0})
        + "\n" + json.dumps({"step": "gate", "round": 1, "seconds": 9.0}) + "\n",
        "conflicts.md": "# Conflicts\n\n## Resolved\n\n- a.py\n- b.py\n- a.py\n",
    })  # fmt: skip
    _factory(root, "002-draft-titles", {
        "decision.md": READY, "runs/land-step.md": _land_step(2),
        "runs/land-train.md": _train_record("002-draft-titles", 2, red, tip),
        "build/land-1.gate.md": _gate_file(("FAIL", 1, 0)),
        "build/land-2.gate.md": _gate_file(("PASS", 1, 0)),
        "runs/ejections.jsonl": ejected,
    })  # fmt: skip
    _factory(root, "003-shipped-by-hand", {"decision.md": READY})
    _close(root, "004-by-hand")
    landing = _pipeline(root)["landing"]
    assert landing["n"] == 2
    assert landing["coverage"] == {"measured": 2, "of": 4, "greyed": False}
    assert landing["missing_because"] == {"built by hand": 1, "no landing record": 1}
    assert landing["gates"] == {"total": 3, "per_change": 1.5}
    assert landing["ejections"]["gate"] == 1 and landing["ejections"]["review"] == 0
    assert (landing["ejections"]["total"], landing["ejections"]["changes"]) == (1, 1)
    assert landing["bisections"] == {"total": 1, "per_change": 0.5}
    assert landing["base_moves"] == {"total": 4, "per_change": 2.0, "changes": 2}
    assert landing["accept_stops"] == {"total": 2, "changes": 1, "per_change": 1.0}
    assert landing["conflicts"] == {"landing": 1, "ship": 2}
    assert sdlc.CONFLICTS == sdlc.factory_records.CONFLICTS, "one name for the record"


def test_pipeline_depth_share(tmp_path: Path) -> None:
    """175 R7: the share of factory runs whose last step record says `DEPTH: full`; a run from
    before the line is missing, never light."""
    root = _repo(tmp_path)
    step = "STEP: approve\nROUND: 1\nLIMIT: 3\nREVIEWERS: code\nSINCE: 2026-10-01T10:00:00Z\n"
    _factory(root, "001-full", {"decision.md": READY, "runs/step.md": step + "DEPTH: full\n"})
    _factory(root, "002-light", {"decision.md": READY, "runs/step.md": step + "DEPTH: light\n"})
    _factory(root, "003-older", {"decision.md": READY, "runs/step.md": step})
    _close(root, "004-by-hand")
    depth = _pipeline(root)["depth"]
    assert (depth["full"], depth["light"], depth["share"], depth["n"]) == (1, 1, 0.5, 2)
    assert depth["coverage"] == {"measured": 2, "of": 3, "greyed": False}
    assert depth["missing_because"] == {"depth not recorded": 1}


def test_pipeline_unreviewed_landings(tmp_path: Path) -> None:
    """175 R8: the landings `Sdlc-Landed` says left paths no review read, by its `unreviewed=`:
    a count above 0, `unknown`, or 0; a landing from before the field is missing."""
    root = _repo(tmp_path)
    for i, landed in enumerate(("by=auto unreviewed=3", "by=person unreviewed=unknown",
                                "by=auto unreviewed=0", "by=person"), 1):  # fmt: skip
        _factory(root, f"00{i}-landing", {"decision.md": READY}, own=(f"Sdlc-Landed: {landed}",))
    _close(root, "005-by-hand")
    out = _pipeline(root)["unreviewed"]
    assert {k: out[k] for k in ("with_paths", "paths", "unknown", "none", "n")} == {
        "with_paths": 1, "paths": 3, "unknown": 1, "none": 1, "n": 3,
    }  # fmt: skip
    assert out["missing_because"] == {"unreviewed not recorded": 1}


def test_retro_prints_each_changes_pipeline_only_with_metrics(tmp_path: Path, capsys) -> None:
    """175 R11: `pipeline.changes` is each change's own figures, printed only with `--metrics`."""
    root = _repo(tmp_path)
    _factory(root, "001-reopen-drafts", {"decision.md": READY,
             "build/round-1.gate.md": _gate_file(("PASS", 1, 0))})  # fmt: skip
    sdlc.retro.cmd_retro(root)
    lean = json.loads(capsys.readouterr().out)["pipeline"]
    assert "changes" not in lean and lean["red_gate"]["builds"] == 1
    sdlc.retro.cmd_retro(root, metrics=True)
    changes = json.loads(capsys.readouterr().out)["pipeline"]["changes"]
    assert [c["name"] for c in changes] == ["001-reopen-drafts"]


# ---------------------------------------------------------------- workarounds (180)


def _hand(root: Path, subject: str, files: dict[str, str]) -> str:
    """A commit on the base branch as a person or a command would make it: `files` written whole,
    `{rel: text}`, under `subject`. Its short sha."""
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject)
    return _git(root, "rev-parse", "--short", "HEAD")


INBOX_PATH = ".sdlc/work/inbox.md"


def _register(*ids: str) -> str:
    return "# Inbox\n" + "".join(f"\n## [{i}] [idea] Entry {i}\n" for i in ids)


def _workarounds(root: Path) -> dict:
    return _retro(root)["simplicity"]["workarounds"]


@pytest.mark.parametrize("hand", [True, False])
def test_a_hand_commit_on_the_base_is_outside_the_loop(tmp_path: Path, hand: bool) -> None:
    """180 R1: a commit on the base branch that no change, register commit, release, setup or
    drop made counts as outside the loop; each command's own commit counts 0."""
    root = _repo(tmp_path)
    _record(root)
    _close(root, "001-reopen-drafts", based=True)
    _hand(root, "File 2026-10-02-1", {INBOX_PATH: _register("2026-10-02-1")})
    _hand(root, "File 2026-10-02-2; Triage #4",
          {INBOX_PATH: _register("2026-10-02-1", "2026-10-02-2")})  # fmt: skip
    _hand(root, "Release 1.2.0", {"VERSION": "1.2.0\n"})
    _hand(root, "Refresh the sdlc setup for 1.2.0", {".sdlc/setup.json": "{}\n"})
    sha = _hand(root, "tidy the readme", {"README.md": "tidied\n"}) if hand else None
    _drop(root, "002-draft-sync")
    _close(root, "003-draft-titles", based=True)
    before = _state(root)
    out = _workarounds(root)
    assert _state(root) == before, "read-only (R8)"
    outside = out["outside"]
    assert outside["count"] == (1 if hand else 0), outside
    assert outside["rows"] == ([{"sha": sha, "subject": "tidy the readme"}] if hand else [])
    assert outside["n"] == (10 if hand else 9), "every first-parent commit in the window"
    assert out["hand_record"]["count"] == 0 and out["hand_record"]["n"] == outside["n"]
    assert out["unknown"]["count"] == 0


def test_the_window_starts_after_the_repo_took_the_plugin_up(tmp_path: Path) -> None:
    """180 R1: with no retrospective, the window runs from the adoption commit, and nothing before
    it, the adoption included, is a workaround."""
    root = _repo(tmp_path)
    _hand(root, "an early commit", {"src/drafts.py": "early\n"})
    _hand(root, "Set the repo up for the sdlc plugin", {".sdlc/config.toml": ""})
    sha = _hand(root, "tidy the readme", {"README.md": "tidied\n"})
    _close(root, "001-reopen-drafts", based=True)
    out = _workarounds(root)
    assert out["outside"]["rows"] == [{"sha": sha, "subject": "tidy the readme"}]
    assert out["outside"]["n"] == 3


def test_a_hand_commit_to_a_record_is_told_from_one_to_code(tmp_path: Path) -> None:
    """180 R2: an outside commit touching a record counts as `hand_record`; one touching only code
    as `outside`."""
    root = _repo(tmp_path)
    _record(root)
    _close(root, "001-reopen-drafts", based=True)
    fixed = _hand(root, "put the entry back", {INBOX_PATH: _register("2026-10-02-1")})
    code = _hand(root, "quick fix", {"src/drafts.py": "fixed\n"})
    out = _workarounds(root)
    assert out["hand_record"]["rows"] == [{"sha": fixed, "subject": "put the entry back"}]
    assert out["outside"]["rows"] == [{"sha": code, "subject": "quick fix"}]
    assert out["hand_record"]["count"] == out["outside"]["count"] == 1


def test_an_entry_filed_again_after_it_was_retired_is_restored(tmp_path: Path) -> None:
    """180 R3: the register gaining an id it held before, from before the window too, is a
    restoration; a new id is not."""
    root = _repo(tmp_path)
    _hand(root, "File 2026-10-02-1", {INBOX_PATH: _register("2026-10-02-1")})
    _record(root)
    _close(root, "001-reopen-drafts", based=True, texts={INBOX_PATH: _register()})
    again = _hand(root, "File 2026-10-02-1", {INBOX_PATH: _register("2026-10-02-1")})
    _hand(root, "File 2026-10-03-1", {INBOX_PATH: _register("2026-10-02-1", "2026-10-03-1")})
    _hand(root, "Update 2026-10-03-1",
          {INBOX_PATH: _register("2026-10-02-1").replace("Entry", "An entry") +
           "\n## [2026-10-03-1] [idea] Renamed\n"})  # fmt: skip
    before = _state(root)
    out = _workarounds(root)["restored"]
    assert _state(root) == before
    assert out == {
        "count": 1, "n": 2,
        "rows": [{"id": "2026-10-02-1", "sha": again, "subject": "File 2026-10-02-1"}],
        "missing_because": {},
    }  # fmt: skip


def test_a_change_with_no_start_leaves_its_commits_unknown(tmp_path: Path, monkeypatch) -> None:
    """180 R7: with no start, a change claims only its own last commit; the commits before it are
    unknown, never outside, and a problem names the change."""
    root = _repo(tmp_path)
    _record(root)
    _close(root, "001-reopen-drafts", later=("src/drafts.py",))
    monkeypatch.setattr(sdlc, "_change_base", lambda *a: None)
    out = _retro(root)
    found = out["simplicity"]["workarounds"]
    assert found["outside"]["count"] == 0 and found["hand_record"]["count"] == 0
    assert found["unknown"]["count"] == 1
    # Seed 2026-11-20-15: the unknown block carries its `n`, as each other count does.
    assert found["unknown"]["n"] == found["outside"]["n"] > 0
    assert [r["subject"] for r in found["unknown"]["rows"]] == ["ship 001-reopen-drafts"]
    # Nit 2026-11-19-56: each unknown commit names the change whose start couldn't be found.
    assert [r["change"] for r in found["unknown"]["rows"]] == ["001-reopen-drafts"]
    assert any(p.startswith("001-reopen-drafts: its start is unknown") for p in out["problems"])


def test_with_no_factory_change_the_overrides_are_null(tmp_path: Path) -> None:
    """180 R7: no change in the window was the factory's, so no override count is 0: each is
    null over an `n` of 0."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", based=True)
    over = _workarounds(root)["overrides"]
    assert over == {
        "ejections": {"count": None, "by_cause": {}, "n": 0},
        "stops": {"count": None, "n": 0},
        "fixes": {"count": None, "n": 0},
    }


def _factory_texts(name: str, rows: list[dict], asks: int = 0, garbled: bool = False) -> dict:
    """A factory change's records as its own commit holds them: a decision, its ejection rows and
    `asks` fixes asked at landing."""
    folder = f".sdlc/work/{name}"
    lines = [json.dumps(r) for r in rows] + (["not a row"] if garbled else [])
    texts = {f"{folder}/decision.md": "DECISION: READY\n"}
    if lines:
        texts[f"{folder}/runs/ejections.jsonl"] = "\n".join(lines) + "\n"
    for k in range(1, asks + 1):
        texts[f"{folder}/build/land-{k}.ask.md"] = "Name the drafts by date.\n"
    return texts


def test_overrides_are_read_from_each_factory_changes_commit(tmp_path: Path) -> None:
    """180 R6: ejections by cause, stops by train (a row with no train once per change), and the
    fixes asked at landing, over the factory changes, a dropped one's tip included; a line that
    doesn't parse is passed over, and a change built by hand isn't in `n`."""
    root = _repo(tmp_path)
    t1, t2 = "2026-10-02T09:00:00Z", "2026-10-02T11:00:00Z"
    row = lambda cause, train=None: {"at": t2, "land": 1, "cause": cause,  # noqa: E731
                                     **({"train": train} if train else {})}  # fmt: skip
    landed = {
        "001-reopen-drafts": ([row("gate", t1), row("stop", t2)], 2),
        "002-keep-one-draft": ([row("stop", t2), row("review", t2)], 0),
        "003-draft-titles": ([row("stop")], 0),
        "004-draft-dates": ([row("stop")], 0),
    }
    for name, (rows, asks) in landed.items():
        texts = _factory_texts(name, rows, asks=asks, garbled=asks > 0)
        _close(root, name, based=True, texts=texts)
    _close(root, "005-draft-colours", based=True)
    _drop(root, "006-draft-sync", texts=_factory_texts("006-draft-sync", [row("refusal", t1)]))
    before = _state(root)
    over = _workarounds(root)["overrides"]
    assert _state(root) == before
    assert over["ejections"] == {
        "count": 3, "by_cause": {"gate": 1, "refusal": 1, "review": 1}, "n": 5,
    }  # fmt: skip
    assert over["stops"] == {"count": 3, "n": 5}, "train t2 once, and 003 and 004 each once"
    assert over["fixes"] == {"count": 2, "n": 5}


# ---------------------------------------------------------------- the scorecard report (184)


def test_by_way_throughput_is_null_under_a_week(tmp_path: Path) -> None:
    """184 R13: a retrospective a day after the last gives no rate per week, with why, and still
    its closed count and weeks; the report's cell reads `–`."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", closed="2026-10-03", trailers=FACTORY)
    _record(root, "2026-10-23")
    _close(root, "002-draft-titles", closed="2026-10-23", trailers=FACTORY)
    tput = _retro(root)["by_way"]["throughput"]["factory"]
    assert tput == {"closed": 1, "weeks": 0.1, "per_week": None, "why": "window under a week"}
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert "| Closed per week | – (1) |" in text


def test_bisections_and_accept_stops_carry_per_change_null_over_none(tmp_path: Path) -> None:
    """184 R18: with no factory landing, `per_change` is null on both, never 0."""
    root = _repo(tmp_path)
    _close(root, "001-by-hand")
    landing = _pipeline(root)["landing"]
    assert landing["bisections"] == {"total": 0, "per_change": None}
    assert landing["accept_stops"] == {"total": 0, "changes": 0, "per_change": None}


def _bugs_from_one_change(root: Path, bugs: int) -> None:
    _close(root, "001-reopen-drafts", trailers=("Sdlc-Mode: manual",))
    _close(root, "002-draft-titles", trailers=("Sdlc-Mode: factory",))
    _filed(root, "# Inbox\n\n" + "".join(
        f"## [2026-10-0{i}-1] [bug] Drafts break {i}\n\nWhat happens.\n\nSeverity: low\n"
        "Introduced by: 001\n\n"
        for i in range(1, bugs + 1)
    ))  # fmt: skip


def test_introducers_are_resolved_once_whatever_the_bugs(tmp_path: Path, monkeypatch) -> None:
    """184 R19: each distinct `Introduced by:` is resolved to its change once, so the calls don't
    grow with the bugs or the ways; the rate keeps its numbers."""
    counts = []
    for bugs in (1, 3):
        (tmp_path / str(bugs)).mkdir()
        root = _repo(tmp_path / str(bugs))
        _bugs_from_one_change(root, bugs)
        cfg = sdlc.load_config(root)[0]
        changes = sdlc.closed_changes(root, None, "main")
        calls = []
        real = sdlc.names_change
        monkeypatch.setattr(
            sdlc, "names_change", lambda *a, seen=calls, real=real: seen.append(a) or real(*a)
        )
        out = sdlc.retro.bugs_retro(root, cfg, None, changes, date(2026, 10, 24))
        monkeypatch.setattr(sdlc, "names_change", real)
        assert out["rate"]["window"]["by_way"]["manual"] == {
            "escapes": bugs, "changes": 1, "rate": float(bugs),
        }  # fmt: skip
        counts.append(len(calls))
    assert counts[0] == counts[1], counts


def test_report_figures_runs_cost_once(tmp_path: Path, monkeypatch) -> None:
    """184 R12: `retro()` and `retro_report()` get their figures from `report_figures()`, the one
    place `_cost` runs, once each."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", trailers=FACTORY)
    calls = []
    real = sdlc.retro._cost
    monkeypatch.setattr(sdlc.retro, "_cost", lambda *a: calls.append(a) or real(*a))
    _retro(root)
    assert len(calls) == 1
    sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert len(calls) == 2
    source = (ROOT / "scripts" / "retro.py").read_text(encoding="utf-8")
    callers = [
        f.split("(", 1)[0]
        for f in re.split(r"\ndef ", source)[1:]
        if re.search(r"(?<![\w.`])_cost\(", f.split("\n", 1)[1])
    ]
    assert callers == ["report_figures"]


HOST_ROWS = [
    ("Speed", "headline", "Median lead time, factory"),
    ("Speed", "headline", "Median lead time, by hand"),
    ("Speed", "guardrail", "Rework links per closed change"),
    ("Quality", "headline", "Escape rate"),
    ("Autonomy", "headline", "Median response, tier 1"),
    ("Autonomy", "headline", "Median response, tier 2"),
    ("Autonomy", "headline", "Questions answered per factory change"),
    ("Autonomy", "guardrail", "Escape rate, factory"),
    ("Autonomy", "guardrail", "Escape rate, by hand"),
    ("Cost", "headline", "Median dollars per landed change, tier 1"),
    ("Cost", "headline", "Median dollars per landed change, tier 2"),
    ("Simplicity", "headline", "Commits outside the loop"),
    ("Simplicity", "headline", "Records edited by hand"),
    ("Simplicity", "headline", "Register entries restored"),
]
SURFACE_ROW = ("Simplicity", "headline", "Share of the surface used")


def _card(out: dict, own: bool = False, last: dict | None = None) -> dict:
    return sdlc.retro.scorecard(
        out["process"], out["autonomy"], out["by_way"], out["cost"],
        out["simplicity"]["workarounds"], out["surface"] if own else None, last or {},
    )  # fmt: skip


def _keys(card: dict) -> list[tuple]:
    return [(r["pillar"], r["role"], r["figure"]) for r in card["rows"]]


def test_scorecard_rows_for_a_host_and_for_the_plugin(tmp_path: Path) -> None:
    """184 R3, R4: one row a way or tier present, the surface's share only in the plugin's own
    repo, and `retro()`'s JSON holds the same rows; with no tier, one `—` row each."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", tier=1, trailers=FACTORY)
    _close(root, "002-draft-titles", tier=2, trailers=("Sdlc-Mode: manual",))
    out = _retro(root)
    assert _keys(_card(out)) == HOST_ROWS
    assert _keys(_card(out, own=True)) == [*HOST_ROWS[:11], SURFACE_ROW, *HOST_ROWS[11:]]
    assert out["scorecard"]["rows"] == _card(out)["rows"], "a test repo is a host"
    assert out["scorecard"]["since"] is None
    row = out["scorecard"]["rows"][0]
    assert set(row) == {"pillar", "role", "figure", "unit", "value", "n", "last", "trend", "note"}
    (tmp_path / "empty").mkdir()
    empty = _card(_retro(_repo(tmp_path / "empty")))
    figures = [r["figure"] for r in empty["rows"]]
    assert "Median response" in figures and "Median dollars per landed change" in figures
    assert all(r["value"] is None for r in empty["rows"] if r["figure"].startswith("Median"))


def _card_row(text: str, figure: str) -> list[str]:
    line = next(line for line in text.splitlines() if f"| {figure} |" in line)
    return sdlc.retro.indicators._cells(line)


def test_a_figure_with_no_data_reads_a_dash_with_its_reason(tmp_path: Path) -> None:
    """184 R5: with no factory change, the factory lead time reads `—` with a reason, never 0:
    the escape rate's, `no factory change in the window` (seed 2026-11-20-24)."""
    root = _repo(tmp_path)
    _close(
        root, "001-reopen-drafts", trailers=("Sdlc-Mode: manual", "Sdlc-Lead: lead=30 source=git")
    )
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    cells = _card_row(text, "Median lead time, factory")
    assert cells[4] == "—" and cells[8], cells
    assert cells[8] == "no factory change in the window"
    row = next(r for r in _retro(root)["scorecard"]["rows"] if r["figure"] == cells[2])
    assert (row["value"], row["n"], row["note"]) == (None, 0, "no factory change in the window")
    escape = next(
        r for r in _retro(root)["scorecard"]["rows"] if r["figure"] == "Escape rate, factory"
    )
    assert escape["note"] == row["note"], "the two rows give one reason"


def test_a_greyed_lead_time_is_marked_a_hint(tmp_path: Path) -> None:
    """184 R6: one of three changes with a lead time is under half: its Note says it's a hint."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", trailers=(*FACTORY, "Sdlc-Lead: lead=30 source=git"))
    _close(root, "002-draft-titles", trailers=FACTORY)
    _close(root, "003-keep-one-draft", trailers=FACTORY)
    rows = {r["figure"]: r for r in _retro(root)["scorecard"]["rows"]}
    assert rows["Median lead time, factory"]["value"] == 30
    assert "a hint: under half the changes" in rows["Median lead time, factory"]["note"]


def test_a_first_scorecard_has_no_last_and_no_trend(tmp_path: Path) -> None:
    """184 R7: no retrospective before: every `last` null and every trend `unknown`."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", trailers=FACTORY)
    rows = _retro(root)["scorecard"]["rows"]
    assert {(r["last"], r["trend"]) for r in rows if r["figure"] != "Escape rate"} == {
        (None, "unknown")
    }


def _by_hand_led(root: Path, k: int, lead: int, closed: str) -> None:
    for i in range(k):
        _close(root, f"0{lead}{i}-draft-{lead}-{i}", closed=closed,
               trailers=("Sdlc-Mode: manual", f"Sdlc-Lead: lead={lead} source=git"))  # fmt: skip


def test_a_second_retrospective_carries_the_first_s_values_as_last(tmp_path: Path) -> None:
    """184 R4, R7: the first report's table reads back as the JSON's rows, value and `n`; the
    second's rows carry those values as `last`, and a trend only where both sides' `n` is 5 or
    more; the escape rate keeps its own previous and trend."""
    root = _repo(tmp_path)
    _by_hand_led(root, 5, 40, "2026-10-02")
    _close(root, "001-reopen-drafts", trailers=FACTORY)
    cfg = sdlc.load_config(root)[0]
    first = sdlc.retro.retro_report(root, cfg, date(2026, 10, 10))
    rows = sdlc.retro.retro(root, cfg, date(2026, 10, 10))["scorecard"]["rows"]
    head = sdlc.retro.SCORECARD_HEAD
    read = sdlc.retro.indicators.report_rows
    for col, field in ((4, "value"), (5, "n")):
        back = read(first, head, keys=(0, 2), value=col)
        assert back == {(r["pillar"], r["figure"]): r[field] for r in rows}, field
    _retro_report_at(root, "2026-10-10", first)
    _by_hand_led(root, 5, 20, "2026-10-12")
    _close(root, "002-draft-titles", closed="2026-10-12", trailers=FACTORY)
    now = {r["figure"]: r for r in _retro(root)["scorecard"]["rows"]}
    before = {r["figure"]: r for r in rows}
    for figure, r in now.items():
        if figure != "Escape rate":
            assert r["last"] == before[figure]["value"], figure
    hand = now["Median lead time, by hand"]
    assert (hand["value"], hand["n"], hand["last"], hand["trend"]) == (20, 5, 40, "down")
    # One factory change each side: n under five gets no trend.
    assert now["Median lead time, factory"]["trend"] == "unknown"
    assert now["Rework links per closed change"]["trend"] == "flat"
    escape = now["Escape rate"]
    process = _retro(root)["process"]["escapes"]
    assert (escape["last"], escape["trend"]) == (process["previous"], process["trend"])


def test_a_row_under_five_gets_no_trend(tmp_path: Path) -> None:
    """184 R7: a `last` with `n` 4, against a value with `n` 5 or more, is still `unknown`."""
    root = _repo(tmp_path)
    _by_hand_led(root, 5, 20, "2026-10-12")
    out = _retro(root)
    key = ("Speed", "Median lead time, by hand")
    assert _card(out, last={key: (40, 4)})["rows"][1]["trend"] == "unknown"
    assert _card(out, last={key: (40, 5)})["rows"][1]["trend"] == "down"
    assert _card(out, last={key: (20, 9)})["rows"][1]["trend"] == "flat"


# `templates/retro.md` as it stood before 184, as a host's override of it may still read.
OLD_TEMPLATE = """\
# Retrospective report

> How the process ran from {{since}} to {{today}}, from the numbers `/sdlc:close` recorded on each
> `Close` commit, and the host's own figures from its `retro.indicators`. `sdlc.py retro-commit`
> writes it and commits it with the retrospective; `sdlc.py retro` gives the same figures as its
> `process` and `spend` blocks and its `architecture.host` rows.

## Window

{{window}}

## Cycle time

{{cycle}}

## Throughput

{{throughput}}

## Time

{{time}}

## Work in progress and capacity

{{capacity}}

## Rework

{{rework}}

## Escapes

{{escapes}}

## Spend

{{spend}}

## Indicators

{{indicators}}
"""
SECTIONS = [
    "Window",
    "Scorecard",
    "Insights",
    "Experience",
    "Speed",
    "Quality",
    "Indicators",
    "Autonomy",
    "Cost",
    "Spend",
    "Simplicity",
]


def _part(text: str, heading: str) -> str:
    return text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def _factory_window(root: Path) -> None:
    _factory(root, "001-reopen-drafts", {"decision.md": READY})
    _close(root, "002-draft-titles", trailers=("Sdlc-Mode: manual",))


def _report(root: Path) -> str:
    return sdlc.retro.retro_report(root, sdlc.load_config(root)[0], date(2026, 10, 24))


def test_the_report_s_sections_come_in_order(tmp_path: Path) -> None:
    """184 R1: the template's `##` sections, in order, each with its one placeholder, and none
    left in the report."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    assert re.findall(r"^## (.+)$", template, re.M) == SECTIONS
    for name in SECTIONS:
        assert _part(template, name).strip() == "{{" + name.lower() + "}}", name
    root = _repo(tmp_path)
    _factory_window(root)
    text = _report(root)
    assert re.findall(r"^## (.+)$", text, re.M) == SECTIONS
    assert "{{" not in text


def test_the_scorecard_holds_the_value_band_table_and_trust_band_once(tmp_path: Path) -> None:
    """184 R2: the Value band, then the pillar table, then the Trust band, in `## Scorecard`;
    `## Window` is the window's sentence alone; the by-way table is Speed's."""
    root = _repo(tmp_path)
    _factory_window(root)
    text = _report(root)
    window, card = _part(text, "Window"), _part(text, "Scorecard")
    assert window.strip().startswith("From the start of history to 2026-10-24: 2 changes closed")
    assert "\n" not in window.strip()
    head = "| " + " | ".join(sdlc.retro.SCORECARD_HEAD) + " |"
    order = [
        card.index(s)
        for s in (
            "Work mix:",
            "Follow-through",
            head,
            "Coverage, lead time",
            "What changed underneath",
            "Unmeasured signals:",
        )
    ]
    assert order == sorted(order), order
    for said in ("Work mix:", "Coverage, lead time", "| By way of building |"):
        assert text.count(said) == 1, said
    assert "| By way of building |" in _part(text, "Speed")
    for u in sdlc.retro.UNMEASURED:
        assert u["signal"] in card


def test_the_pillar_sections_show_autonomy_pipeline_and_cost(tmp_path: Path) -> None:
    """184 R8: autonomy's escalations, the landing's figures and the waste share, each in its
    pillar's section."""
    root = _repo(tmp_path)
    _factory_window(root)
    text = _report(root)
    assert "Escalations:" in _part(text, "Autonomy")
    speed = _part(text, "Speed").splitlines()
    # Nit 2026-11-19-67: each figure on its own line of the landing's list, by the line's label.
    for label in ("Landing gates:", "Ejections:", "Bisections:", "Base moves:", "Accept stops:"):
        assert any(line.startswith(f"- {label} ") for line in speed), label
    assert "Waste share:" in _part(text, "Cost")
    assert "Red gates:" in _part(text, "Quality")


def test_a_host_s_simplicity_shows_workarounds_alone(tmp_path: Path) -> None:
    """184 R9: a host's Simplicity is its workarounds, never the plugin's surface."""
    root = _repo(tmp_path)
    _factory_window(root)
    simplicity = _part(_report(root), "Simplicity")
    for said in ("Commits outside the loop", "Records edited by hand",
                 "Register entries restored", "Overrides"):  # fmt: skip
        assert said in simplicity, said
    for word in ("surface", "footprint", "growth"):
        assert word not in simplicity.lower(), word


def test_the_plugin_s_simplicity_shows_its_surface(tmp_path: Path, monkeypatch) -> None:
    """184 R9: in the plugin's own repo, the surface's share, retire candidates, footprint and
    growth follow the workarounds, and the table has the share's row."""
    root = _repo(tmp_path)
    _factory_window(root)
    monkeypatch.setattr(sdlc, "_own_repo", lambda home: True)
    text = _report(root)
    simplicity = _part(text, "Simplicity").lower()
    for word in ("surface", "retire", "footprint", "growth"):
        assert word in simplicity, word
    assert "| Share of the surface used |" in _part(text, "Scorecard")


def test_an_override_from_before_still_renders_every_placeholder(tmp_path: Path) -> None:
    """184 R10: the template as it stood before still renders, every placeholder filled, and its
    `{{window}}` keeps the Value band, the coverage lines and the by-way table."""
    root = _repo(tmp_path)
    _factory_window(root)
    (root / ".sdlc" / "templates").mkdir(parents=True)
    (root / ".sdlc" / "templates" / "retro.md").write_text(OLD_TEMPLATE, encoding="utf-8")
    text = _report(root)
    assert "{{" not in text
    window = _part(text, "Window")
    for said in ("Work mix:", "Coverage, lead time", "| By way of building |"):
        assert said in window, said
    assert "## Scorecard" not in text


def test_an_override_without_the_scorecard_is_breaking() -> None:
    """184 R11: the next retrospective reads the scorecard back, so an override without it is
    misread: its heading and placeholder, and nothing else."""
    assert sdlc._template_misses("retro.md", OLD_TEMPLATE) == [
        "the `## Scorecard` heading",
        "the `{{scorecard}}` placeholder",
    ]


def test_the_retro_skill_s_process_pass_reads_workarounds() -> None:
    """184 R14: Step 0 lists `scorecard`, and Step 2's process pass reads
    `simplicity.workarounds`, turning a recurring `outside` or `restored` row into a seed."""
    text = (ROOT / "skills" / "retro" / "SKILL.md").read_text(encoding="utf-8")
    step0 = text.split("## Step 0", 1)[1].split("\n## ", 1)[0]
    step2 = text.split("## Step 2", 1)[1].split("\n## ", 1)[0]
    assert "- `scorecard`:" in step0
    process = step2.split("3. **Process.**", 1)[1].split("4. **Product**", 1)[0]
    assert "`simplicity.workarounds`" in process and "seed" in process


# ---------------------------------------------------------------- the Insights section (189)


def _written_back(process: dict, values: list) -> dict:
    """Each value written through the scorecard's table and read back by `_last_rows()`'s
    reader, keyed by its figure."""
    rows = [
        {"pillar": "Speed", "role": "headline", "figure": f"F{i}", "unit": "u", "value": v,
         "n": 9, "last": None, "trend": "unknown", "note": ""}
        for i, v in enumerate(values)
    ]  # fmt: skip
    text = sdlc.retro._scorecard_text({"rows": rows}, None, process, None, None, None)
    read = sdlc.retro.indicators.report_rows
    head, keys = sdlc.retro.SCORECARD_HEAD, sdlc.retro.SCORECARD_KEYS
    return {k[1]: v for k, v in read(text, head, keys, sdlc.retro.SCORECARD_VALUE).items()}


def test_a_trend_reads_flat_against_its_own_written_value(tmp_path: Path) -> None:
    """189 R12 (nit 2026-11-19-65): a value read back from the table it was written to trends
    `flat` against itself, and 0.174 against a written 0.17 is `up`: two numbers the person sees."""
    process = _retro(_repo(tmp_path))["process"]
    values = [1 / 3, 0.174, 1.4]
    back = _written_back(process, values)
    for i, v in enumerate(values):
        assert sdlc.retro._trend(v, 9, (back[f"F{i}"], 9)) == "flat", v
    assert sdlc.retro._trend(0.174, 9, (_written_back(process, [0.17])["F0"], 9)) == "up"


def test_minutes_keep_one_decimal() -> None:
    """189 R13 (nit 2026-11-19-66): a median of 1.44 minutes is written 1.4, not 1."""
    assert sdlc.retro._minutes(1.44) == 1.4
    assert sdlc.retro.indicators.number(sdlc.retro._minutes(1.44)) == "1.4"
    assert sdlc.retro._minutes(30.0) == 30 and sdlc.retro._minutes(None) is None


def test_render_report_takes_the_figures_whole() -> None:
    """189 R10 (2026-11-19-63): the figures as one dict, and the host's indicators, the insights
    and (190) the experience beside it, by keyword."""
    import inspect

    params = inspect.signature(sdlc.retro.render_report).parameters
    assert [(p.name, p.kind.name) for p in params.values()] == [
        ("template", "POSITIONAL_OR_KEYWORD"), ("figures", "POSITIONAL_OR_KEYWORD"),
        ("indicators", "KEYWORD_ONLY"), ("insights", "KEYWORD_ONLY"),
        ("experience", "KEYWORD_ONLY"),  # 190
    ]  # fmt: skip


def test_every_null_scorecard_row_names_its_reason(tmp_path: Path) -> None:
    """189 R11 (2026-11-19-64): a window that closed changes, none measured and none built by the
    factory: every null row says why, never `none in the window`."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", tier=1, trailers=("Sdlc-Mode: manual",))
    _close(root, "002-draft-titles", tier=2, trailers=("Sdlc-Mode: manual",))
    rows = _retro(root)["scorecard"]["rows"]
    null = {r["figure"]: r["note"] for r in rows if r["value"] is None}
    assert {"Median response, tier 1", "Questions answered per factory change",
            "Escape rate, factory", "Register entries restored"} <= set(null), null  # fmt: skip
    assert [f for f, note in null.items() if note == sdlc.retro.NONE_NOTE] == []
    assert null["Questions answered per factory change"] == "built by hand"
    assert null["Escape rate, factory"] == "no factory change in the window"
    assert null["Register entries restored"] == "no register entry added in the window"
    assert null["Median response, tier 1"].startswith("not measured at close")
    out = _retro(root)
    ws = out["simplicity"]["workarounds"]
    assert ws["outside"]["missing_because"] == {}, "a window with commits counts them"
    (tmp_path / "quiet").mkdir()
    quiet = _repo(tmp_path / "quiet")
    _record(quiet)  # a retrospective at the tip: nothing on the base branch since
    card = {r["figure"]: r for r in _retro(quiet)["scorecard"]["rows"]}
    for figure in ("Commits outside the loop", "Records edited by hand"):
        assert card[figure]["value"] is None
        assert card[figure]["note"] == "no commit on the base branch in the window", figure
    unknown = _retro(quiet)["simplicity"]["workarounds"]["unknown"]
    assert (unknown["count"], unknown["n"]) == (None, 0), "null, never 0, with no commit"
    assert unknown["missing_because"] == {"no commit on the base branch in the window": 0}


def _scorecard_questions() -> dict[str, str]:
    """The synthesis questions as `docs/RETRO-SCORECARD.md`'s table holds them, by pillar."""
    text = (ROOT / "docs" / "RETRO-SCORECARD.md").read_text(encoding="utf-8")
    table = text.split("## Insights: the synthesis questions", 1)[1].split("\n## ", 1)[0]
    rows = [sdlc.retro.indicators._cells(ln) for ln in table.splitlines() if ln.startswith("| ")]
    return {cells[0]: cells[1] for cells in rows[1:] if cells[0] != "Pillar"}


def test_the_insights_guide_asks_one_question_per_pillar() -> None:
    """189 R1: one `##` section per pillar, in order, each holding that pillar's question."""
    text = (ROOT / "guide" / "insights.md").read_text(encoding="utf-8")
    units = [(k, t) for k, t in sdlc.doc_units(text) if k != "#"]
    assert [k for k, _ in units] == [f"## {p}" for p in sdlc.retro.INSIGHT_PILLARS]
    asked = _scorecard_questions()
    assert list(asked) == list(sdlc.retro.INSIGHT_PILLARS)
    for key, block in units:
        assert block.split("\n", 1)[1].strip() == asked[key.removeprefix("## ")], key
    assert not [ln for ln in text.splitlines() if ln.startswith("<")]


HOST_INSIGHTS = """\
# Insights

> This repo's own questions.

## Speed

Where does the review's time go?

## Quality

### Flaky tests

Which tests fail now and then, and why?

- **Hint**: read the red gates.

### Speed

A title already asked.

## Cost

## Customer churn

Did anything shipped lose a user?
"""


def _questions(root: Path) -> tuple[list[dict], list[str]]:
    return sdlc.retro.insight_questions(root, sdlc.load_config(root)[0])


def test_a_host_insights_doc_replaces_adds_and_places(tmp_path: Path) -> None:
    """189 R2: a pillar's block with text replaces the guide's question; a heading alone places;
    a `###` under a pillar adds one on its figures; any other `##` one on the tradeoffs'; a second
    question with one title is a problem, and dropped."""
    root = _repo(tmp_path)
    guide, problems = _questions(root)
    assert [(q["title"], q["pillar"]) for q in guide] == [
        (p, p) for p in sdlc.retro.INSIGHT_PILLARS
    ]
    assert problems == []
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "INSIGHTS.md").write_text(HOST_INSIGHTS, encoding="utf-8")
    got, problems = _questions(root)
    asked = _scorecard_questions()
    assert [(q["title"], q["pillar"]) for q in got] == [
        ("Value", "Value"), ("Speed", "Speed"), ("Quality", "Quality"),
        ("Flaky tests", "Quality"), ("Autonomy", "Autonomy"), ("Cost", "Cost"),
        ("Simplicity", "Simplicity"), ("Tradeoffs", "Tradeoffs"),
        ("Customer churn", "Tradeoffs"),
    ]  # fmt: skip
    by = {q["title"]: q["question"] for q in got}
    assert by["Speed"] == "Where does the review's time go?", "a block with text replaces"
    assert by["Cost"] == asked["Cost"] and by["Quality"] == asked["Quality"], "a heading places"
    assert (
        by["Flaky tests"].startswith("Which tests fail now and then")
        and "**Hint**" in (by["Flaky tests"])
    )
    assert by["Customer churn"] == "Did anything shipped lose a user?"
    assert len(problems) == 1 and "Speed" in problems[0] and "twice" in problems[0], problems


def test_config_reports_the_insights_doc(tmp_path: Path, capsys) -> None:
    """189 R2: `docs.insights` is `.sdlc/INSIGHTS.md`, off while it doesn't exist, read after the
    guide."""
    root = _repo(tmp_path)
    assert sdlc.cmd_config(root) == 0
    out = json.loads(capsys.readouterr().out)
    got = out["docs"]["insights"]
    assert got["path"] == ".sdlc/INSIGHTS.md" and got["exists"] is False
    assert got["layout"] == "answers" and got["guide"].endswith("guide/insights.md")
    # Off while it doesn't exist (nit 2026-11-20-26): no warning, where the missing process doc
    # does warn, and the questions are the guide's, one a pillar, as with no doc named at all.
    warned = out["warnings"]
    assert any(w.startswith("docs.process:") for w in warned), warned
    assert not any(w.startswith("docs.insights") for w in warned), warned
    cfg = sdlc.load_config(root)[0]
    asked = sdlc.retro.insight_questions(root, cfg)
    unset = sdlc.retro.insight_questions(root, {**cfg, "docs": {**cfg["docs"], "insights": None}})
    assert asked == unset and asked[1] == []
    assert [q["title"] for q in asked[0]] == list(sdlc.retro.INSIGHT_PILLARS)


def _insights_json(root: Path, capsys) -> dict:
    assert sdlc.retro.cmd_retro(root, insights=True) == 0
    return json.loads(capsys.readouterr().out)


def test_each_insight_gets_only_its_pillars_figures(tmp_path: Path, capsys) -> None:
    """189 R3: each question's `data` holds only its pillar's paths, its scorecard rows, the
    window and what changed underneath."""
    root = _repo(tmp_path)
    _factory_window(root)
    out = _insights_json(root, capsys)
    assert out["problems"] == []
    by = {q["title"]: q for q in out["questions"]}
    assert list(by) == list(sdlc.retro.INSIGHT_PILLARS)
    for q in out["questions"]:
        assert set(q) == {"title", "pillar", "question", "data"}
        assert {"window", "underneath"} <= set(q["data"]["process"]), q["title"]
        rows = q["data"]["scorecard"]["rows"]
        if q["pillar"] != "Tradeoffs":
            assert {r["pillar"] for r in rows} <= {q["pillar"]}, q["title"]
    assert "cost" not in by["Speed"]["data"] and "cycle" in by["Speed"]["data"]["process"]
    assert "cost" in by["Cost"]["data"] and "cycle" not in by["Cost"]["data"]["process"]
    assert "host" not in by["Quality"]["data"]["architecture"]
    assert "surface" not in by["Simplicity"]["data"], "a host's Simplicity has no surface"
    assert {r["pillar"] for r in by["Tradeoffs"]["data"]["scorecard"]["rows"]} > {"Speed"}
    assert "changes" not in by["Cost"]["data"]["cost"], "no change's own numbers"


def test_retro_insights_runs_no_host_command(tmp_path: Path, capsys) -> None:
    """189 R4: `retro --insights` runs none of the host's evidence, indicator or test-time
    commands, and writes nothing; `retro` itself runs them, so the marker would show."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    (root / ".sdlc").mkdir(exist_ok=True)
    shutil.copy(ROOT / "defaults" / "PRODUCT.md", root / ".sdlc" / "PRODUCT.md")
    (root / ".sdlc" / "config.toml").write_text(
        '[retro]\nevidence = ["touch ran-evidence"]\nindicators = ["touch ran-indicators"]\n'
        'test_times = ["touch ran-times"]\n',
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "set up")
    before = _state(root)
    out = _insights_json(root, capsys)
    assert len(out["questions"]) == len(sdlc.retro.INSIGHT_PILLARS)
    assert _state(root) == before and not list(root.glob("ran-*"))
    assert sdlc.retro.cmd_retro(root) == 0
    capsys.readouterr()
    assert {p.name for p in root.glob("ran-*")} == {"ran-evidence", "ran-indicators", "ran-times"}


def _answer(title: str, **fields: str) -> str:
    said = {
        "Headline": f"{title} held steady.",
        "Evidence": "Median lead time 42 minutes (n 7).",
        "Recommendation": "Nothing.",
        "Disposition": "none: nothing to act on this window",
        **fields,
    }
    return f"## {title}\n\n" + "".join(f"{k}: {v}\n" for k, v in said.items() if v is not None)


def _draft(root: Path, day: date, **by_title: dict) -> Path:
    """An insights draft answering every guide question, `by_title` overriding fields."""
    text = "\n".join(_answer(p, **by_title.get(p, {})) for p in sdlc.retro.INSIGHT_PILLARS)
    path = root / sdlc.retro.insights_rel(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


DAY = date(2026, 10, 24)


def test_retro_commit_refuses_an_insight_missing_a_field(tmp_path: Path, capsys) -> None:
    """189 R6: a field left out, or empty, is a refusal naming the question and the field, found
    before anything is written."""
    root = _repo(tmp_path)
    _direction(root)
    _draft(root, DAY, Speed={"Recommendation": None}, Cost={"Headline": ""})
    before = _state(root)
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert any("'Speed'" in r and "Recommendation" in r for r in refusals), refusals
    assert any("'Cost'" in r and "Headline" in r for r in refusals), refusals
    assert _state(root) == before


@pytest.mark.parametrize(
    "fields, why",
    [
        ({"Disposition": "seed 2026-10-30-9"}, "2026-10-30-9, which the register doesn't hold"),
        ({"Disposition": "maybe later"}, "is none of"),
    ],
)
def test_retro_commit_refuses_a_seed_the_register_lacks(tmp_path, capsys, fields, why) -> None:
    """189 R6: a `seed` names an entry in the register as it stands, and a Disposition is one of
    the kinds; an unknown title is refused too."""
    root = _repo(tmp_path)
    _direction(root)
    path = _draft(root, DAY, Value=fields)
    path.write_text(path.read_text(encoding="utf-8") + _answer("Churn"), encoding="utf-8")
    before = _state(root)
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert any("'Value'" in r and why in r for r in refusals), refusals
    assert any("'Churn'" in r and "not a question" in r for r in refusals), refusals
    assert _state(root) == before


def test_retro_commit_renders_the_insights_and_removes_the_draft(tmp_path, capsys) -> None:
    """189 R6: the answers go into the report's `## Insights`, the commit holds the report and
    never the draft, and the draft is gone once the commit is made."""
    root = _repo(tmp_path)
    _direction(root)
    path = _draft(root, DAY, Speed={"Headline": "Reviews wait on the person.",
                                    "Disposition": "seed 2026-10-24-1"})  # fmt: skip
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    out = json.loads(capsys.readouterr().out)
    draft = sdlc.retro.insights_rel(DAY)
    assert draft not in out["paths"] and not path.exists()
    assert draft not in _git(root, "show", "--name-only", "--format=", "HEAD").splitlines()
    report = (root / ".sdlc" / "retros" / "2026-10-24.md").read_text(encoding="utf-8")
    insights = _part(report, "Insights")
    assert "### Speed: Reviews wait on the person." in insights
    assert "- Disposition: seed 2026-10-24-1" in insights
    assert f"*{_scorecard_questions()['Speed']}*" in insights
    assert _git(root, "status", "--porcelain") == ""


def test_the_insights_say_not_answered_without_a_draft(tmp_path: Path, capsys) -> None:
    """189 R7: with no draft the section is a sentence, never empty; `retro --report` renders a
    draft that is there, and writes nothing."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    assert _part(_report(root), "Insights").strip() == sdlc.retro.NOT_ANSWERED
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    assert _part(capsys.readouterr().out, "Insights").strip() == sdlc.retro.NOT_ANSWERED
    _draft(root, date.today(), Cost={"Headline": "Spend is flat."})
    before = _state(root)
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    assert "### Cost: Spend is flat." in _part(capsys.readouterr().out, "Insights")
    assert _state(root) == before


def test_an_override_without_insights_still_renders(tmp_path: Path, capsys) -> None:
    """189 R8: a host's override from before this change (the 184 template) renders every section
    it has, and `retro-commit` takes a draft with it all the same."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    old = template.replace("## Insights\n\n{{insights}}\n\n", "")
    assert old != template and "{{insights}}" not in old
    root = _repo(tmp_path)
    (root / ".sdlc" / "templates").mkdir(parents=True)
    (root / ".sdlc" / "templates" / "retro.md").write_text(old, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "override")
    text = _report(root)
    assert re.findall(r"^## (.+)$", text, re.M) == [s for s in SECTIONS if s != "Insights"]
    assert "{{" not in text
    _direction(root)
    _draft(root, DAY)
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out


def test_insights_is_not_a_template_read() -> None:
    """189 R8: `{{insights}}` is optional, so an override without it isn't breaking."""
    reads = sdlc.TEMPLATE_READS["retro.md"]
    assert "{{insights}}" not in reads.get("placeholders", ())
    assert "Insights" not in reads.get("headings", ())


def test_a_failed_commit_leaves_the_insights_draft_for_a_rerun(tmp_path, capsys) -> None:
    """189 R6: the draft is removed only once the commit is made; a refused `git commit` (a hook
    that fails) leaves it, and the report, as they were, and the rerun commits and removes it."""
    root = _repo(tmp_path)
    _direction(root)
    path = _draft(root, DAY, Speed={"Headline": "Reviews wait on the person."})
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    head = _git(root, "rev-parse", "HEAD")
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 1
    out = json.loads(capsys.readouterr().out)
    assert any(r.startswith("git commit failed") for r in out["refusals"]), out["refusals"]
    assert path.is_file() and _git(root, "rev-parse", "HEAD") == head
    assert not (root / sdlc.retro.report_rel(DAY)).exists()
    hook.unlink()
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    capsys.readouterr()
    assert not path.exists()
    report = (root / sdlc.retro.report_rel(DAY)).read_text(encoding="utf-8")
    assert "### Speed: Reviews wait on the person." in _part(report, "Insights")


# ---------------------------------------------------------------- the Experience section (190)


@pytest.mark.parametrize(
    "answer, expected",
    [
        ("3 fine", (3, None)),
        ("2 the reviews dragged", (2, "the reviews dragged")),
        ("4 — quick this time", (4, "quick this time")),
        ("1 In the Way", (1, None)),
        ("3, the reviews waited on me", (3, "the reviews waited on me")),
        ("4", (4, None)),
        ("5 great", (None, "5 great")),
        ("12 things", (None, "12 things")),
        ("the builds were slow", (None, "the builds were slow")),
        ("", (None, None)),
        ("   ", (None, None)),
    ],
)
def test_an_experience_answer_reads_its_rating_and_line(answer, expected) -> None:
    """190 R4: a leading 1 to 4 is the rating, the rest the line, the option's own label no line;
    anything else is no rating and all of it the line."""
    assert sdlc.retro.experience_answer(answer) == expected


def _experience(root: Path, day: date, text: str) -> Path:
    """The day's experience draft, holding `text` as the skill writes it."""
    path = root / sdlc.retro.experience_rel(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _felt_row(rating: str, last: str, trend: str) -> str:
    return f"| {sdlc.retro.EXPERIENCE_FIGURE} | {rating} | {last} | {trend} |"


def test_retro_commit_renders_the_rating_and_removes_its_draft(tmp_path, capsys) -> None:
    """190 R5: the rating and the line go into `## Experience`, the commit holds the report and
    never the draft, and the draft is gone once the commit is made."""
    root = _repo(tmp_path)
    _direction(root)
    path = _experience(root, DAY, "Answer: 2 the reviews dragged\n")
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    out = json.loads(capsys.readouterr().out)
    draft = sdlc.retro.experience_rel(DAY)
    assert draft not in out["paths"] and not path.exists()
    assert "experience draft removed" in out["done"]
    assert draft not in _git(root, "show", "--name-only", "--format=", "HEAD").splitlines()
    report = (root / sdlc.retro.report_rel(DAY)).read_text(encoding="utf-8")
    part = _part(report, "Experience")
    assert "| " + " | ".join(sdlc.retro.EXPERIENCE_HEAD) + " |" in part
    assert _felt_row("2", "—", "unknown") in part
    assert "Their line: the reviews dragged" in part
    assert _git(root, "status", "--porcelain") == ""


def test_a_rating_with_no_line_says_so() -> None:
    """190 R5: a rating with no line reads `No line given.`; a line with no rating keeps it."""
    assert sdlc.retro._experience_text("4 smooth", None).endswith(sdlc.retro.NO_LINE)
    text = sdlc.retro._experience_text("the builds | were slow", None)
    assert _felt_row("—", "—", "unknown") in text and "Their line: the builds | were slow" in text


def test_the_experience_says_not_rated_without_a_draft(tmp_path: Path, capsys) -> None:
    """190 R6: with no draft the row's value is `—`, its trend `unknown`, and the line says no
    rating was given, in `retro-commit`'s report and in `retro --report`, which previews a draft
    that is there and writes nothing."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    part = _part(_report(root), "Experience")
    assert _felt_row("—", "—", "unknown") in part and sdlc.retro.NOT_RATED in part
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    part = _part(capsys.readouterr().out, "Experience")
    assert _felt_row("—", "—", "unknown") in part and sdlc.retro.NOT_RATED in part
    _experience(root, date.today(), "Answer: 3 fine\n")
    before = _state(root)
    assert sdlc.retro.cmd_retro(root, report=True) == 0
    part = _part(capsys.readouterr().out, "Experience")
    assert _felt_row("3", "—", "unknown") in part and sdlc.retro.NO_LINE in part
    assert _state(root) == before
    (root / sdlc.retro.experience_rel(date.today())).unlink()
    _direction(root)
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    report = (root / sdlc.retro.report_rel(DAY)).read_text(encoding="utf-8")
    assert sdlc.retro.NOT_RATED in _part(report, "Experience")


def test_retro_commit_refuses_an_experience_draft_without_an_answer(tmp_path, capsys) -> None:
    """190 R7: a draft with no `Answer:` line is refused, found before anything is written."""
    root = _repo(tmp_path)
    _direction(root)
    _experience(root, DAY, "3 fine\n")
    before = _state(root)
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    rel = sdlc.retro.experience_rel(DAY)
    assert f"experience: {rel} has no Answer: line" in refusals, refusals
    assert _state(root) == before


def test_a_failed_commit_leaves_the_experience_draft_for_a_rerun(tmp_path, capsys) -> None:
    """190 R8: a refused `git commit` leaves the draft and removes the report, HEAD unmoved; the
    rerun commits and removes the draft."""
    root = _repo(tmp_path)
    _direction(root)
    path = _experience(root, DAY, "Answer: 4 smooth\n")
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    head = _git(root, "rev-parse", "HEAD")
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 1
    out = json.loads(capsys.readouterr().out)
    assert any(r.startswith("git commit failed") for r in out["refusals"]), out["refusals"]
    assert path.is_file() and _git(root, "rev-parse", "HEAD") == head
    assert not (root / sdlc.retro.report_rel(DAY)).exists()
    hook.unlink()
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    capsys.readouterr()
    assert not path.exists()
    report = (root / sdlc.retro.report_rel(DAY)).read_text(encoding="utf-8")
    assert _felt_row("4", "—", "unknown") in _part(report, "Experience")


def test_the_next_retro_reads_the_last_rating_back(tmp_path: Path, capsys) -> None:
    """190 R9: the second retrospective's row reads the first's rating as its last, with the
    trend; `retro`'s `experience.last` is the newest report's rating and line."""
    root = _repo(tmp_path)
    assert sdlc.retro.retro(root, sdlc.load_config(root)[0], DAY)["experience"] == {"last": None}
    _direction(root)
    _experience(root, DAY, "Answer: 2 the reviews dragged\n")
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    later = date(2026, 10, 25)
    (root / ".sdlc" / "DIRECTION.md").write_text("# Direction\n\nNew goals.\n", encoding="utf-8")
    _experience(root, later, "Answer: 3, quicker now\n")
    assert sdlc.retro.cmd_retro_commit(root, later) == 0, capsys.readouterr().out
    capsys.readouterr()
    report = (root / sdlc.retro.report_rel(later)).read_text(encoding="utf-8")
    assert _felt_row("3", "2", "up") in _part(report, "Experience")
    got = sdlc.retro.retro(root, sdlc.load_config(root)[0], date(2026, 10, 26))["experience"]
    assert got == {"last": {"date": "2026-10-25", "rating": 3, "line": "quicker now"}}


@pytest.mark.parametrize(
    "rating, last, trend",
    [(3, 2, "up"), (2, 3, "down"), (3, 3, "flat"), (None, 3, "unknown"), (3, None, "unknown")],
)
def test_the_experience_trend_needs_both_ratings(rating, last, trend) -> None:
    """190 R9: one person's single answer, so no minimum count: only both sides."""
    assert sdlc.retro._experience_trend(rating, last) == trend


def test_a_report_without_the_table_reads_back_as_no_last(tmp_path: Path) -> None:
    """190 R9: a last report from before this change (no Experience table) gives `last: null`;
    a `—` rating is `rating: null` with its line kept."""
    root = _repo(tmp_path)
    _record(root)
    assert sdlc.retro._last_rows(root, {"sha": "HEAD", "date": "2026-10-10"})["experience"] is None
    rel = sdlc.retro.report_rel(date(2026, 10, 12))
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(
        "# Report\n\n## Experience\n\n" + sdlc.retro._experience_text("slow builds", None) + "\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Retrospective 2026-10-12")
    got = sdlc.retro._last_rows(root, {"sha": "HEAD", "date": "2026-10-12"})["experience"]
    assert got == {"date": "2026-10-12", "rating": None, "line": "slow builds"}


@pytest.mark.parametrize("cell", ["abc", "7", "0", "2.5", "inf", ""])
def test_a_hand_edited_rating_reads_back_as_none(cell) -> None:
    """Nit 2026-11-20-33: a report's rating cell, edited by hand to anything but a whole 1 to 4,
    reads back as no rating, its line kept, never raising or passing on a rating the question
    never offered."""
    text = sdlc.retro._experience_text("3 slow builds", None)
    edited = text.replace(_felt_row("3", "—", "unknown"), _felt_row(cell, "—", "unknown"))
    assert edited != text
    got = sdlc.retro._last_experience("# Report\n\n## Experience\n\n" + edited, "2026-10-12")
    assert got == {"date": "2026-10-12", "rating": None, "line": "slow builds"}
    assert sdlc.retro._last_experience("## Experience\n\n" + text, None)["rating"] == 3


def test_experience_is_not_a_template_read() -> None:
    """190 R10: `{{experience}}` is optional, so an override without it isn't breaking."""
    reads = sdlc.TEMPLATE_READS["retro.md"]
    assert "{{experience}}" not in reads.get("placeholders", ())
    assert "Experience" not in reads.get("headings", ())


def test_an_override_without_experience_still_renders(tmp_path: Path, capsys) -> None:
    """190 R10: the 189 template (no `## Experience`) renders every section it has, and
    `retro-commit` takes a draft with it all the same."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    old = template.replace("## Experience\n\n{{experience}}\n\n", "")
    assert old != template and "{{experience}}" not in old
    root = _repo(tmp_path)
    (root / ".sdlc" / "templates").mkdir(parents=True)
    (root / ".sdlc" / "templates" / "retro.md").write_text(old, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "override")
    text = _report(root)
    assert re.findall(r"^## (.+)$", text, re.M) == [s for s in SECTIONS if s != "Experience"]
    assert "{{" not in text
    _direction(root)
    path = _experience(root, DAY, "Answer: 3 fine\n")
    assert sdlc.retro.cmd_retro_commit(root, DAY) == 0, capsys.readouterr().out
    assert not path.exists()


def test_reference_names_the_rating_and_its_draft() -> None:
    """190 R13: *Retrospectives* names `experience`, the scale, the draft and that it is never
    committed, and still says what `retro-commit` holds."""
    text = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    retros = " ".join(text.split("## Retrospectives")[1].split("\n## ")[0].split())
    for needed in ("`experience`", "1 to 4", "`.sdlc/retros/<date>.experience.md`",
                   "never committed", "retro-commit` commits those files and nothing else",
                   "`{{experience}}`"):  # fmt: skip
        assert needed in retros, needed
    process = (ROOT / "docs" / "PROCESS.md").read_text(encoding="utf-8")
    assert "the experience draft" in process.split('written["writes:')[1].split("\n")[0]


def test_reference_and_step_0_name_the_aim_keys() -> None:
    """190 R14 (nit 2026-11-19-18): the aim keys 168 added are named where a reader looks."""
    text = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    retros = text.split("## Retrospectives")[1].split("\n## ")[0]
    skill = (ROOT / "skills" / "retro" / "SKILL.md").read_text(encoding="utf-8")
    step0 = skill.split("## Step 0")[1].split("\n## Step 1")[0]
    for key in ("`work_mix`", "`time_to_users`", "`follow_through`"):
        assert key in retros, key
        assert key in step0, key
