"""The release loop: what has landed since the last release, the version it adds up to, the local
release commit and tag, and the one step that pushes.

History is the source. Each repo here is built the way close leaves one: a change's own commit
holding its shipped intent.md, then a `Close NNN-slug` commit removing the folder. The remote is a
bare repository on disk, so publishing runs offline.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_release", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

PKG = '{\n  "name": "demo",\n  "version": "{v}",\n  "private": true\n}\n'
PYPROJECT = '[project]\nname = "demo"\nversion = "{v}"\n\n[tool.ruff]\ntarget-version = "py311"\n'
CONFIG = '[release]\nversion_files = ["pkg.json", "pyproject.toml"]\n'
INTENT = """\
---
id: {id}
slug: {slug}
tier: 1
{impact}stage: shipped
created: 2026-10-01
updated: 2026-10-02
idea:
---

# {id} — {title}

## Problem

Real prose.
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, version: str = "0.4.2", config: str = CONFIG, tag: bool = True) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pkg.json").write_text(PKG.replace("{v}", version), encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT.replace("{v}", version), encoding="utf-8")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    if tag:
        _git(root, "tag", "-a", f"v{version}", "-m", f"v{version}")
    return root


def _ship(root: Path, name: str, impact: str | None = "patch", title: str = "") -> None:
    """The change's own commit: its folder, shipped, and the code it carries."""
    nid, slug = name.split("-", 1)
    folder = root / "work" / name
    folder.mkdir(parents=True)
    line = f"impact: {impact}\n" if impact is not None else ""
    text = INTENT.format(id=nid, slug=slug, impact=line, title=title or slug.replace("-", " "))
    (folder / "intent.md").write_text(text, encoding="utf-8")
    (root / f"{slug}.txt").write_text("the change\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}")


def _close(root: Path, name: str, impact: str | None = "patch", title: str = "") -> None:
    """What close leaves: the change's commit, then `Close NNN-slug` removing its folder."""
    _ship(root, name, impact, title)
    _git(root, "rm", "-r", "-q", f"work/{name}")
    _git(root, "commit", "-q", "-m", f"Close {name}", "-m", "Its artifacts are in x.")


def _unreleased(root: Path) -> dict:
    return sdlc.unreleased(root, sdlc.load_config(root)[0])


def _run(capsys, fn, *args) -> tuple[int, dict]:
    code = fn(*args)
    return code, json.loads(capsys.readouterr().out)


def _state(root: Path) -> tuple[str, str, str]:
    return _git(root, "status", "--porcelain"), _git(root, "tag"), _git(root, "rev-parse", "HEAD")


# ---------------------------------------------------------------- the listing


def test_it_lists_the_changes_closed_since_the_tag_and_not_before(tmp_path: Path) -> None:
    root = _repo(tmp_path, tag=False)
    _close(root, "001-before-the-release", "major")
    _git(root, "tag", "-a", "v0.4.2", "-m", "v0.4.2")
    _close(root, "002-reopen-drafts", "patch", "Reopen saved drafts")
    _close(root, "003-export-totals", "minor")
    u = _unreleased(root)
    assert [(c["id"], c["impact"]) for c in u["changes"]] == [("002", "patch"), ("003", "minor")]
    assert u["changes"][0]["title"] == "Reopen saved drafts", "the H1 without its id"
    assert u["changes"][0]["sha"] == _git(root, "rev-parse", "--short", "HEAD~3")
    assert (u["since"], u["version"], u["bump"], u["next"]) == ("v0.4.2", "0.4.2", "minor", "0.5.0")
    assert _git(root, "status", "--porcelain") == ""


def test_a_dropped_change_is_never_released(tmp_path: Path) -> None:
    """`Drop` keeps main's tree and has no impact: the release reads `Close` commits only."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", impact="patch")
    _git(root, "checkout", "-q", "-b", "002-draft-sync")
    (root / "sync.txt").write_text("never landed\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "work")
    _git(root, "checkout", "-q", "main")
    _git(
        root, "merge", "-q", "-s", "ours", "--no-ff", "-m", "Drop 002-draft-sync", "002-draft-sync"
    )
    out = _unreleased(root)
    assert [c["name"] for c in out["changes"]] == ["001-reopen-drafts"]
    assert out["problems"] == [] and out["next"] == "0.4.3"


def test_a_change_without_an_impact_is_a_problem_and_blocks_the_version(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", None)
    _close(root, "003-export-totals", "sideways")
    u = _unreleased(root)
    assert len(u["problems"]) == 2 and "002-reopen-drafts" in u["problems"][0]
    assert "'sideways'" in u["problems"][1]
    assert u["next"] is None


@pytest.mark.parametrize(
    "version, impacts, bump, nxt",
    [
        ("0.4.2", ["patch"], "patch", "0.4.3"),
        ("0.4.2", ["patch", "minor", "none"], "minor", "0.5.0"),
        ("0.4.2", ["major"], "minor", "0.5.0"),
        ("1.2.3", ["minor", "major"], "major", "2.0.0"),
        ("1.2.3", ["none", "none"], None, None),
        ("1.2.3", [], None, None),
    ],
)
def test_the_highest_impact_decides_and_major_stays_minor_below_1(version, impacts, bump, nxt):
    assert sdlc.next_version(version, impacts) == (bump, nxt)


def test_only_none_is_nothing_to_release(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "none")
    u = _unreleased(root)
    assert u["nothing"] is True and u["next"] is None
    assert [c["impact"] for c in u["changes"]] == ["none"], "listed, never counted"


def test_a_landed_folder_counts_and_an_open_change_does_not(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _ship(root, "002-reopen-drafts", "minor")  # merged, but close stopped before its Close commit
    _git(root, "worktree", "add", "-q", "-b", "003-export-totals", str(tmp_path / "wt"))
    wt = tmp_path / "wt" / "work" / "003-export-totals"
    wt.mkdir(parents=True)
    (wt / "intent.md").write_text(
        INTENT.format(id="003", slug="export-totals", impact="", title="t").replace(
            "stage: shipped", "stage: build"
        ),
        encoding="utf-8",
    )
    u = _unreleased(root)
    assert [(c["id"], c["closed"]) for c in u["changes"]] == [("002", False)]
    assert u["changes"][0]["sha"] == _git(root, "rev-parse", "--short", "HEAD"), "what shipped it"
    assert u["open"] == ["003-export-totals"]
    assert u["next"] == "0.5.0"


def test_closed_changes_carries_what_both_outer_loops_read(tmp_path: Path) -> None:
    """One walk for the release loop and the retrospective: each closed change with its intent's
    fields, the change's own commit, and the Close commit's sha and date."""
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "minor", "Reopen saved drafts")
    [rec] = sdlc.closed_changes(root, "v0.4.2")
    assert {k: rec[k] for k in ("id", "slug", "name", "title", "tier", "impact", "created")} == {
        "id": "002",
        "slug": "reopen-drafts",
        "name": "002-reopen-drafts",
        "title": "Reopen saved drafts",
        "tier": 1,
        "impact": "minor",
        "created": "2026-10-01",
    }
    assert rec["sha"] == _git(root, "rev-parse", "--short", "HEAD~1")
    assert rec["close_sha"] == _git(root, "rev-parse", "--short", "HEAD")
    assert rec["close_date"] == _git(root, "log", "-1", "--format=%cs")
    assert rec["problems"] == [] and rec["closed"] is True
    assert sdlc.closed_changes(root, "HEAD") == []


def test_an_unparseable_intent_is_a_problem_not_a_raise(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    folder = root / "work" / "002-reopen-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text("---\nid: [unclosed\n---\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "ship")
    _git(root, "rm", "-r", "-q", "work")
    _git(root, "commit", "-q", "-m", "Close 002-reopen-drafts")
    [rec] = sdlc.closed_changes(root, None)
    assert "no readable work/002-reopen-drafts/intent.md" in rec["problems"][0]


def test_without_reading_it_lists_by_name_only(tmp_path: Path) -> None:
    root = _repo(tmp_path, config="")
    _close(root, "002-reopen-drafts", None)
    [rec] = sdlc.closed_changes(root, None, read=False)
    assert (rec["id"], rec["impact"], rec["problems"]) == ("002", "", [])


def test_with_nothing_configured_it_still_lists_and_says_what_to_set(tmp_path: Path) -> None:
    root = _repo(tmp_path, config="")
    _close(root, "002-reopen-drafts", "patch")
    u = _unreleased(root)
    assert u["configure"] == "release.version_files"
    assert [c["id"] for c in u["changes"]] == ["002"] and u["next"] is None


def test_a_missing_tag_names_the_command_that_would_make_it(tmp_path: Path) -> None:
    root = _repo(tmp_path, tag=False)
    _close(root, "002-reopen-drafts", "patch")
    u = _unreleased(root)
    first = _git(root, "rev-list", "--max-parents=0", "--abbrev-commit", "HEAD")
    assert u["missing"] == {"tag": "v0.4.2", "hint": f'git tag -a v0.4.2 -m "v0.4.2" {first}'}
    assert u["next"] is None
    assert _git(root, "tag") == ""


def test_version_files_that_disagree_or_hold_two_lines_are_problems(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "pkg.json").write_text(PKG.replace("{v}", "0.4.3"), encoding="utf-8")
    assert "disagree" in _unreleased(root)["problems"][0]
    (root / "pkg.json").write_text('"version": "1"\n"version": "2"\n', encoding="utf-8")
    assert "2 version lines" in _unreleased(root)["problems"][0]


# ---------------------------------------------------------------- release


@pytest.mark.parametrize(
    "spoil, why",
    [
        (lambda r: (r / "pkg.json").write_text("{}\n", encoding="utf-8"), "uncommitted"),
        (lambda r: _git(r, "checkout", "-q", "-b", "side"), "isn't on main"),
        (lambda r: (r / ".sdlc" / "config.toml").write_text("", encoding="utf-8"), "version_files"),
        (lambda r: _git(r, "tag", "-d", "v0.4.2"), "no tag v0.4.2"),
        (lambda r: _close(r, "003-export-totals", None), "impact must be one of"),
        (lambda r: _git(r, "tag", "-a", "v0.4.3", "-m", "x"), "already exists"),
    ],
)
def test_release_refuses_before_writing_anything(tmp_path: Path, capsys, spoil, why) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "patch")
    if why == "version_files":
        _git(root, "commit", "-q", "--allow-empty", "-m", "noop")
    spoil(root)
    if why == "version_files":
        _git(root, "commit", "-q", "-am", "drop the release config")
    before = _state(root)
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 1 and any(why in r for r in out["refusals"]), out["refusals"]
    assert _state(root) == before and out["done"] == []


def test_release_refuses_from_a_change_worktree(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "patch")
    _git(root, "worktree", "add", "-q", "-b", "003-x", str(tmp_path / "wt"))
    code, out = _run(capsys, sdlc.cmd_release, tmp_path / "wt")
    assert code == 1 and "main checkout" in out["refusals"][0]
    assert _git(root, "tag") == "v0.4.2"


def test_only_none_refuses_as_nothing_to_release(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "none")
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 1 and "nothing to release" in out["refusals"][0]


def test_release_edits_only_the_version_and_commits_only_those_files(tmp_path: Path, capsys):
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "minor", "Reopen saved drafts")
    (root / "untracked.txt").write_text("not mine\n", encoding="utf-8")
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 0, out["refusals"]
    assert out["done"] == ["version files", "commit", "tag"]
    assert (root / "pkg.json").read_text(encoding="utf-8") == PKG.replace("{v}", "0.5.0")
    assert (root / "pyproject.toml").read_text(encoding="utf-8") == PYPROJECT.replace(
        "{v}", "0.5.0"
    ), "target-version is not a version line"
    assert _git(root, "log", "-1", "--format=%s") == "Release 0.5.0"
    changed = _git(root, "show", "--name-only", "--format=", "HEAD").splitlines()
    assert sorted(changed) == ["pkg.json", "pyproject.toml"]
    assert _git(root, "rev-parse", "v0.5.0^{commit}") == _git(root, "rev-parse", "HEAD")
    assert out["undo"] == "git tag -d v0.5.0 && git reset --keep HEAD~1"
    assert _unreleased(root)["since"] == "v0.5.0" and _unreleased(root)["changes"] == []


def test_a_crlf_file_keeps_its_line_endings(tmp_path: Path) -> None:
    text = '{\r\n  "version": "0.4.2",\r\n  "x": 1\r\n}\r\n'
    assert sdlc.write_version(text, "0.5.0") == text.replace("0.4.2", "0.5.0")


def test_the_notes_are_the_same_in_the_tag_the_commit_and_the_changelog(tmp_path: Path, capsys):
    config = CONFIG + 'changelog = "CHANGELOG.md"\n\n[archive]\ntarget = "github"\n'
    root = _repo(tmp_path, config=config)
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## 0.4.2 — 2026-10-01\n\n- old\n")
    _git(root, "add", "CHANGELOG.md")
    _git(root, "commit", "-q", "-m", "a changelog")
    _close(root, "002-reopen-drafts", "patch", "Reopen saved drafts")
    _close(root, "013-export-totals", "minor", "Export the totals")
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 0, out["refusals"]
    notes = "- 002 Reopen saved drafts (patch) #2\n- 013 Export the totals (minor) #13"
    assert out["notes"] == notes
    assert _git(root, "tag", "-l", "--format=%(contents)", "v0.5.0") == f"v0.5.0\n\n{notes}"
    assert _git(root, "log", "-1", "--format=%b") == notes
    log = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    assert log.startswith("# Changelog\n\n## 0.5.0 — ") and log.endswith("- old\n")
    assert notes in log and log.index("0.5.0") < log.index("0.4.2")
    assert "CHANGELOG.md" in _git(root, "show", "--name-only", "--format=", "HEAD")


def test_check_writes_nothing_and_version_overrides_upward_only(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "patch")
    before = _state(root)
    code, out = _run(capsys, sdlc.cmd_release, root, True)
    assert code == 0 and out["next"] == "0.4.3" and _state(root) == before
    assert out["skipped"] == ["version files (--check)", "commit (--check)", "tag (--check)"]
    code, out = _run(capsys, sdlc.cmd_release, root, False, "0.4.2")
    assert code == 1 and "isn't greater" in out["refusals"][0] and _state(root) == before
    code, out = _run(capsys, sdlc.cmd_release, root, False, "1.0.0")
    assert code == 0 and _git(root, "tag", "-l", "v1.0.0") == "v1.0.0"


# ---------------------------------------------------------------- publish


def _released(tmp_path: Path, capsys, publish: str | None = None) -> tuple[Path, Path]:
    config = CONFIG + (f"publish = {json.dumps(publish)}\n" if publish else "")
    root = _repo(tmp_path, config=config)
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "origin", "main", "v0.4.2")
    _close(root, "002-reopen-drafts", "patch")
    assert sdlc.cmd_release(root) == 0
    capsys.readouterr()
    return root, remote


def test_publish_pushes_main_then_the_tag_then_runs_the_command(tmp_path: Path, capsys) -> None:
    root, remote = _released(tmp_path, capsys, "echo {version} {tag} >> published.log")
    code, out = _run(capsys, sdlc.cmd_publish, root, True)
    assert code == 0 and _git(remote, "tag") == "v0.4.2", "--check pushes nothing"
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 0, out["refusals"]
    assert out["done"] == ["push main", "push tag", "publish command"]
    assert _git(remote, "rev-parse", "main") == _git(root, "rev-parse", "main")
    assert _git(remote, "rev-parse", "v0.4.3") == _git(root, "rev-parse", "v0.4.3")
    assert (root / "published.log").read_text() == "0.4.3 v0.4.3\n"
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 0 and out["done"] == [], "a rerun after success does nothing"
    assert (root / "published.log").read_text() == "0.4.3 v0.4.3\n"


def test_a_remote_that_has_moved_is_refused_before_the_command(tmp_path: Path, capsys) -> None:
    root, remote = _released(tmp_path, capsys, "touch published")
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(remote), str(other))
    (other / "theirs.txt").write_text("x\n")
    _git(other, "add", "-A")
    _git(other, "-c", "user.name=o", "-c", "user.email=o@o", "commit", "-q", "-m", "theirs")
    _git(other, "push", "-q", "origin", "main")
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 1 and out["refusals"][0].startswith("push main failed")
    assert out["skipped"] == ["push main", "push tag", "publish command"]
    assert not (root / "published").exists() and _git(remote, "tag") == "v0.4.2"


def test_a_failed_command_is_rerun_alone(tmp_path: Path, capsys) -> None:
    root, remote = _released(tmp_path, capsys, "test -f go && echo ran >> published.log")
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 1 and out["done"] == ["push main", "push tag"]
    assert "release.publish exited 1" in out["refusals"][0]
    (root / "go").write_text("")
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 0 and out["done"] == ["publish command"]
    assert out["skipped"] == ["push main (already done)", "push tag (already done)"]
    assert (root / "published.log").read_text() == "ran\n"


def test_a_bad_tag_template_is_refused_not_raised(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, config=CONFIG + 'tag = "v{ver}"\n')
    _close(root, "002-reopen-drafts", "patch")
    assert "may hold only {version}" in _unreleased(root)["problems"][0]
    for fn in (sdlc.cmd_release, sdlc.cmd_publish):
        code, out = _run(capsys, fn, root)
        assert code == 1 and any("may hold only {version}" in r for r in out["refusals"])


def test_publish_refuses_when_main_has_moved_past_the_release(tmp_path: Path, capsys) -> None:
    root, remote = _released(tmp_path, capsys)
    _close(root, "003-export-totals", "patch")
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 1 and "main has moved past v0.4.3" in out["refusals"][0]
    assert _git(remote, "tag") == "v0.4.2"


# ---------------------------------------------------------------- status


def _status(root: Path, capsys, monkeypatch) -> str:
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    sdlc.main()
    return capsys.readouterr().out


def test_status_shows_what_is_unreleased(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "minor")
    out = _status(root, capsys, monkeypatch)
    assert "■ Unreleased: 1\n    since v0.4.2 → 0.5.0 (minor)  /sdlc:release" in out
    assert "002  reopen-drafts" in out


def test_status_leaves_the_section_out_where_releasing_isnt_set_up(tmp_path, capsys, monkeypatch):
    root = _repo(tmp_path, config="")
    assert "Unreleased" not in _status(root, capsys, monkeypatch)
    _close(root, "002-reopen-drafts", "minor")
    out = _status(root, capsys, monkeypatch)
    assert "■ Unreleased: 1\n    set release.version_files" in out


def test_the_release_that_makes_a_retrospective_due_says_so(tmp_path, capsys, monkeypatch) -> None:
    """The repo starts tagged v0.4.2: one release, so nothing is due. The second makes two since
    the start, which both `release`'s report and `status` say, and neither runs anything."""
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "minor")
    assert "Retro due" not in _status(root, capsys, monkeypatch)
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 0, out["refusals"]
    assert out["retro_due"]["due"] and out["retro_due"]["releases"] == ["v0.4.2", "v0.5.0"]
    status = _status(root, capsys, monkeypatch)
    assert "■ Retro due: 2 releases since the start, with none yet (v0.4.2, v0.5.0)" in status
    assert "/sdlc:retro" in status


def test_release_check_leaves_the_due_state_out(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root, "002-reopen-drafts", "minor")
    code, out = _run(capsys, sdlc.cmd_release, root, True)
    assert code == 0 and "retro_due" not in out
