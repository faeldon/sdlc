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
import subprocess
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
) -> None:
    """A change's own commit, with its intent and the files it touches, then its `Close`."""
    nid, slug = name.split("-", 1)
    folder = root / "work" / name
    folder.mkdir(parents=True)
    text = intent or INTENT.format(
        id=nid, slug=slug, tier=tier, impact=impact, created=created, title=slug.replace("-", " ")
    )
    if idea:
        text = text.replace("idea:\n", f'idea: "{idea}"\n', 1)
    (folder / "intent.md").write_text(text, encoding="utf-8")
    for rel in files or (f"{slug}.txt",):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{path.read_text() if path.exists() else ''}{name}\n", encoding="utf-8")
    when = f"{closed}T12:00:00"
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}", when=when)
    _git(root, "rm", "-r", "-q", f"work/{name}")
    _git(root, "commit", "-q", "-m", f"Close {name}", when=when)


def _retro(root: Path) -> dict:
    return sdlc.retro(root, sdlc.load_config(root)[0], date(2026, 10, 24))


def _state(root: Path) -> tuple[str, str]:
    return _git(root, "status", "--porcelain"), _git(root, "rev-parse", "HEAD")


def _record(root: Path, day: str = "2026-10-10") -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(f"# Direction\n\n{day}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Retrospective {day}")


# ---------------------------------------------------------------- what retro counts


def test_it_reports_every_key_and_writes_nothing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    before = _state(root)
    assert sdlc.cmd_retro(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out) >= {
        "since", "changes", "dropped", "dropped_at_counts", "problems", "rework", "open",
        "ideas", "tiers", "impacts", "releases", "unmeasured", "prose",
    }  # fmt: skip
    assert "tokens" not in out
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


def test_an_unparseable_intent_is_a_problem_not_a_raise(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", intent="---\nid: [unclosed\n---\n# x\n")
    out = _retro(root)
    assert any("001-reopen-drafts" in p for p in out["problems"])
    assert "problems" not in out["changes"][0]


def test_rework_is_a_later_change_on_the_same_code_within_a_week(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", closed="2026-10-02", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-09", files=("src/drafts.py",))
    _close(root, "003-draft-titles", closed="2026-10-17", files=("src/drafts.py",))
    pairs = [(r["change"], r["reworks"], r["days"]) for r in _retro(root)["rework"]]
    # 7 days apart is rework; 8 apart (002 → 003) and 15 (001 → 003) are not.
    assert pairs == [("002-keep-one-draft", "001-reopen-drafts", 7)]


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
    folder = root / "work" / name
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


def test_a_change_closed_soon_after_a_drop_on_the_same_code_reworks_it(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _drop(root, "001-draft-sync", dropped="2026-10-03", files=("src/drafts.py",))
    _close(root, "002-keep-one-draft", closed="2026-10-06", files=("src/drafts.py",))
    [pair] = _retro(root)["rework"]
    assert pair == {
        "change": "002-keep-one-draft", "reworks": "001-draft-sync", "days": 3,
        "files": ["src/drafts.py"], "dropped": True,
    }  # fmt: skip


def test_sharing_only_the_docs_every_change_updates_is_not_rework(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", files=("CLAUDE.md", ".sdlc/SDLC.md", "a.py"))
    _close(root, "002-keep-one-draft", files=("CLAUDE.md", ".sdlc/SDLC.md", "b.py"))
    assert _retro(root)["rework"] == []


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
    assert sdlc.cmd_retro(root) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["since"] is None
    assert out["changes"] == out["rework"] == out["releases"] == out["problems"] == []
    assert out["ideas"] == {"seeds": 0, "oldest": None}


def test_open_changes_and_seeds_are_counted(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "work" / "004-open-one").mkdir(parents=True)
    (root / "work" / "004-open-one" / "intent.md").write_text(
        INTENT.format(id="004", slug="open-one", tier=1, impact="", created="2026-10-20",
                      title="open one").replace("stage: shipped", "stage: build"),
        encoding="utf-8",
    )  # fmt: skip
    (root / "work" / "ideas.md").write_text(
        "# Ideas\n\n## [2026-09-01] [seed] Old one\n\nx\n\n## [2026-10-01] [seed] New one\n\nx\n"
        "\n## [2026-10-02] [building] Taken\n\nx\n",
        encoding="utf-8",
    )
    out = _retro(root)
    assert [(o["name"], o["title"], o["age_days"]) for o in out["open"]] == [
        ("004-open-one", "open one", 4)
    ]
    assert out["ideas"] == {"seeds": 2, "oldest": "2026-09-01"}


def test_prose_counts_each_of_the_plugins_skills(tmp_path: Path) -> None:
    prose = _retro(_repo(tmp_path))["prose"]
    assert set(prose["skills"]) == {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    retro = prose["skills"]["retro"]
    assert retro["est_tokens"] == retro["bytes"] // 4 and retro["script_calls"] >= 3
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
    (root / "work").mkdir(exist_ok=True)
    (root / "work" / "ideas.md").write_text("# Ideas\n\n## [2026-10-24] [seed] X\n\nx\n")


def test_it_commits_the_direction_doc_and_the_seeds_and_nothing_else(tmp_path, capsys) -> None:
    root = _repo(tmp_path)
    _direction(root)
    code = sdlc.cmd_retro_commit(root, date(2026, 10, 24))
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out["refusals"]
    assert _git(root, "log", "-1", "--format=%s") == "Retrospective 2026-10-24"
    assert _git(root, "show", "--name-only", "--format=", "HEAD").splitlines() == [
        ".sdlc/DIRECTION.md",
        "work/ideas.md",
    ]
    assert _git(root, "status", "--porcelain") == ""
    assert sdlc.last_retrospective(root)["date"] == "2026-10-24"


def _stray(root: Path) -> None:
    _direction(root)
    (root / "README.md").write_text("edited\n", encoding="utf-8")


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
        (_nothing, "nothing to record"),
        (_today_already, "one a day"),
        (_off_main, "isn't on main"),
    ],
)
def test_it_refuses_before_writing_anything(tmp_path: Path, capsys, spoil, why) -> None:
    root = _repo(tmp_path)
    spoil(root)
    before = _state(root)
    assert sdlc.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    assert any(why in r for r in json.loads(capsys.readouterr().out)["refusals"])
    assert _state(root) == before


def test_it_refuses_from_a_change_worktree(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    tree = tmp_path / "tree"
    _git(root, "worktree", "add", "-q", "-b", "001-x", str(tree))
    _direction(tree)
    before = _state(root), _state(tree)
    assert sdlc.cmd_retro_commit(tree, date(2026, 10, 24)) == 1
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
        "seeds": ["Reopen drafts from the list"],
    }


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


def test_each_grouped_seed_and_change_says_what_it_became(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "work").mkdir()
    (root / "work" / "ideas.md").write_text(
        "# Ideas\n\n## [2026-10-01] [seed] Still waiting\n\nx\n", encoding="utf-8"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _close(root, "011-keep-one-draft", idea="Reopen drafts from the list")
    (root / "work" / "012-open-one").mkdir(parents=True)
    (root / "work" / "012-open-one" / "intent.md").write_text(
        INTENT.format(id="012", slug="open-one", tier=1, impact="", created="2026-10-20",
                      title="open one").replace("stage: shipped", "stage: build"),
        encoding="utf-8",
    )  # fmt: skip
    (root / ".sdlc").mkdir()
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
    code = sdlc.cmd_retro_commit(root, date(2026, 10, 24))
    out = json.loads(capsys.readouterr().out)
    if refused:
        assert code == 1 and any(refused in r for r in out["refusals"]), out["refusals"]
        assert _git(root, "rev-parse", "HEAD") == before
    else:
        # G9 was already struck, so leaving it out is fine.
        assert code == 0, out["refusals"]


def test_the_first_direction_doc_has_nothing_to_carry(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "DIRECTION.md").write_text("## Goals\n\n- G1. Ship\n", encoding="utf-8")
    assert sdlc.cmd_retro_commit(root, date(2026, 10, 24)) == 0, capsys.readouterr().out


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


def _measured(root: Path, name: str, agent: int, stops: int, extra: tuple = ()) -> None:
    """Close a change, then give its `Close` commit the trailers close writes."""
    _close(root, name, tier=2)
    close = _git(root, "log", "-1", "--format=%B")
    _git(root, "commit", "-q", "--amend", "-m", close + "\n\n" + "\n".join([
        "Sdlc-Mode: manual",
        "Sdlc-Coverage: transcripts=2 stages=design,ship",
        f"Sdlc-Totals: elapsed=90 agent={agent} response=10 away=0 blocked=0 stops={stops} "
        "required=5 target=2 permission=1 ship_runs=1 reenter=0 in=1 cache_read=100 out=10",
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
    assert group["target"] == 2
    assert group["stages"]["design"]["agent"] == 15
    assert group["roles"]["builder"] == {"runs": 2, "agent": 30, "cache_read": 40, "out": 10}


def test_ship_findings_are_read_from_the_changes_own_commit(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    nid, slug = "004", "found-things"
    folder = root / "work" / f"{nid}-{slug}"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        INTENT.format(id=nid, slug=slug, tier=2, impact="patch", created="2026-10-01",
                      title="found things"), encoding="utf-8",
    )  # fmt: skip
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship it", "-m", "Sdlc-Findings: important=1 nit=3 cost=2")
    _git(root, "rm", "-r", "-q", f"work/{nid}-{slug}")
    _git(root, "commit", "-q", "-m", f"Close {nid}-{slug}", "-m",
         "Sdlc-Mode: manual\nSdlc-Totals: agent=5 stops=5 required=5 target=2")  # fmt: skip
    [rec] = sdlc.closed_changes(root, None)
    assert rec["findings"] == {"important": 1, "nit": 3, "cost": 2}
    group = sdlc.metrics_summary([rec])["groups"]["tier 2, manual"]
    assert group["findings"] == {"important": 1, "nit": 3}


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
    folder = root / "work" / "004-open"
    folder.mkdir(parents=True)
    text = _serving("004-open", "[O2, O3]").replace("stage: shipped", "stage: build")
    (folder / "intent.md").write_text(text, encoding="utf-8")
    product = _retro(root)["product"]
    assert product["stale"] == [{"change": "004-open", "outcome": "O2"}]
    assert product["outcomes"]["O3"]["open"] == ["004-open"]


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
    monkeypatch.setattr(sdlc, "EVIDENCE_LIMIT", 10)
    monkeypatch.setattr(sdlc, "EVIDENCE_TIMEOUT", 0.5)
    rows = sdlc._evidence(
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
    code = sdlc.cmd_retro_commit(root, date(2026, 10, 24))
    assert code == 0, capsys.readouterr().out
    assert sorted(_git(root, "show", "--name-only", "--format=", "HEAD").splitlines()) == [
        ".sdlc/DIRECTION.md", ".sdlc/PRODUCT.md", "work/ideas.md",
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
    assert sdlc.cmd_retro_commit(root, date(2026, 10, 24)) == 1
    refusals = json.loads(capsys.readouterr().out)["refusals"]
    assert any("O1 was open and the new product doc drops it" in r for r in refusals), refusals
    assert _git(root, "rev-parse", "HEAD") == before
