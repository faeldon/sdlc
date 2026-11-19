"""The retrospective's surface (179): every skill, script command and config key, built from the
code, with its use in the window, the share used, retire candidates, setup's footprint and the
surface's growth per release.

Each repo is built the way close leaves one, as in `test_retro.py`: a change's own commit holding
its intent, then a `Close NNN-slug` commit carrying the trailers close would have written.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_surface", ROOT / "scripts" / "sdlc.py")

INTENT = """\
---
id: {id}
slug: {slug}
tier: 1
impact: {impact}
stage: shipped
created: 2026-10-01
updated: 2026-10-01
idea:
---

# {id} — {slug}

## Problem

x
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True, env=os.environ
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, config: str = "") -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    if config:
        (root / ".sdlc").mkdir()
        (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _close(root: Path, name: str, *trailers: str, impact: str = "patch") -> None:
    nid, slug = name.split("-", 1)
    folder = root / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        INTENT.format(id=nid, slug=slug, impact=impact), encoding="utf-8"
    )
    (root / f"{slug}.txt").write_text(name, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}")
    _git(root, "rm", "-r", "-q", f".sdlc/work/{name}")
    said = ["-m", "\n".join(trailers)] if trailers else []
    _git(root, "commit", "-q", "-m", f"Close {name}", *said)


def _record(root: Path, day: str) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "DIRECTION.md").write_text(f"# Direction\n\n{day}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Retrospective {day}")


@pytest.fixture(autouse=True)
def no_factory(monkeypatch) -> None:
    """A scratch repo is no plugin repo, and the machine's settings never decide a test."""
    monkeypatch.setattr(sdlc, "factory_enabled", lambda home: (False, None))


def _surface(root: Path) -> dict:
    """The surface as `retro()` computes it, without the rest of the retrospective."""
    cfg = sdlc.load_config(root)[0]
    since = sdlc.last_retrospective(root, cfg["git"]["base"])
    changes = sdlc.closed_changes(root, since["sha"] if since else None, cfg["git"]["base"])
    return sdlc.retro.surface(root, cfg, changes, since)


def _item(surface: dict, kind: str, name: str) -> dict:
    return next(i for i in surface["items"] if (i["kind"], i["name"]) == (kind, name))


SKILLS = "Sdlc-Skill: sdlc:spec runs=1"
TOOLS = "Sdlc-Tool: Bash:sdlc.py:ship calls=1 errors=0"


# ---------------------------------------------------------------- R2, R3: the inventory


def test_the_surface_is_the_code(tmp_path: Path, monkeypatch) -> None:
    """R2: every skill folder, registered command and config key is listed, read when retro runs:
    one added to the code is there with no list to edit."""
    plugin = tmp_path / "plugin"
    shutil.copytree(ROOT / "skills", plugin / "skills")
    (plugin / "skills" / "made-up").mkdir()
    (plugin / "skills" / "made-up" / "SKILL.md").write_text("# Made up\n", encoding="utf-8")
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", plugin)
    monkeypatch.setitem(sdlc.COMMANDS, "made-up", None)
    monkeypatch.setitem(sdlc.CONFIG_KEYS, "made", {"up": None})
    names = {(i["kind"], i["name"]) for i in _surface(_repo(tmp_path))["items"]}
    skills = {p.parent.name for p in (plugin / "skills").glob("*/SKILL.md")}
    assert {("skill", f"sdlc:{s}") for s in skills} <= names and ("skill", "sdlc:made-up") in names
    own = {("command", f"sdlc.py:{c}") for c in sdlc.retro.OWN_REPO_COMMANDS}
    assert {("command", f"sdlc.py:{c}") for c in sdlc.COMMANDS} - own <= names
    assert ("command", "sdlc.py:made-up") in names and ("key", "made.up") in names
    keys = {f"{s}.{k}" for s, ks in sdlc.CONFIG_KEYS.items() for k in ks}
    assert {n for k, n in names if k == "key"} == keys


def test_the_factory_command_regex_finds_every_command() -> None:
    """R3: the copy of the registry `retro.py` reads from each script's text finds what each
    script registers, so a new decorator shape fails here."""
    factory = ROOT / "plugins" / "factory" / "scripts" / "factory.py"
    loaded = _load("factory_surface", factory)
    found = sdlc.retro.COMMAND_RE.findall(factory.read_text(encoding="utf-8"))
    assert sorted(found) == sorted(loaded.COMMANDS)
    core = sdlc.retro.COMMAND_RE.findall((ROOT / "scripts" / "sdlc.py").read_text("utf-8"))
    assert sorted(core) == sorted(sdlc.COMMANDS)


def test_the_factory_is_listed_only_when_in_play(tmp_path: Path, monkeypatch) -> None:
    """R3: the factory's skills and commands, tagged as its, when it is enabled or the repo is the
    plugin's own; left out otherwise."""
    root = _repo(tmp_path)
    assert not [i for i in _surface(root)["items"] if i["plugin"] == "sdlc-factory"]
    monkeypatch.setattr(sdlc, "factory_enabled", lambda home: (True, "project"))
    listed = {i["name"] for i in _surface(root)["items"] if i["plugin"] == "sdlc-factory"}
    assert {"sdlc-factory:build", "factory.py:land", "factory.py:check"} <= listed
    monkeypatch.setattr(sdlc, "factory_enabled", lambda home: (False, None))
    monkeypatch.setattr(sdlc, "_own_repo", lambda home: True)
    assert "sdlc-factory:build" in {i["name"] for i in _surface(root)["items"]}


def test_a_host_never_lists_the_skills_cases(tmp_path: Path, monkeypatch) -> None:
    """The skills' cases are this plugin's own (170): a host's surface lists neither `cases` nor
    `run-cases`, and the plugin's own repo lists both."""
    root = _repo(tmp_path)
    names = {i["name"] for i in _surface(root)["items"]}
    assert not {"sdlc.py:cases", "sdlc.py:run-cases"} & names
    monkeypatch.setattr(sdlc, "_own_repo", lambda home: True)
    names = {i["name"] for i in _surface(root)["items"]}
    assert {"sdlc.py:cases", "sdlc.py:run-cases"} <= names


# ---------------------------------------------------------------- R4, R5, R6: use and state


def test_a_call_counts_once(tmp_path: Path) -> None:
    """R4: a command's use is its `Sdlc-Tool` calls; `Sdlc-Calls` splits the same calls by role
    and is never added on top. A skill's is its `Sdlc-Skill` runs, summed across changes."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", "Sdlc-Skill: sdlc:ship runs=2",
           "Sdlc-Tool: Bash:sdlc.py:preflight calls=3 errors=0",
           "Sdlc-Calls: reviewer Bash:sdlc.py:preflight=3")  # fmt: skip
    _close(root, "002-keep-one-draft", "Sdlc-Skill: sdlc:ship runs=1",
           "Sdlc-Tool: Bash:sdlc.py:preflight calls=1 errors=0")  # fmt: skip
    s = sdlc.retro.retro(root, sdlc.load_config(root)[0], date(2026, 10, 24))["surface"]
    assert s == _surface(root), "retro reports the surface"
    assert _item(s, "command", "sdlc.py:preflight")["uses"] == 4
    assert _item(s, "skill", "sdlc:ship")["uses"] == 3
    assert _item(s, "command", "sdlc.py:ship")["state"] == "unused"


def test_a_key_is_used_when_the_config_sets_it(tmp_path: Path) -> None:
    """R4: a key is used when the base branch's config sets it, never by its default."""
    root = _repo(tmp_path, '[git]\nbase = "main"\n')
    s = _surface(root)
    assert _item(s, "key", "git.base")["state"] == "used"
    assert _item(s, "key", "docs.process")["state"] == "unused", "a default is not a setting"


def test_an_unrecorded_item_is_never_unused(tmp_path: Path, monkeypatch) -> None:
    """R5: a skill run outside a change, a command no skill runs, and anything no change in the
    window recorded are `unmeasured`, each with why; never `unused`."""
    monkeypatch.setitem(sdlc.COMMANDS, "made-up", None)
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    s = _surface(root)
    assert _item(s, "skill", "sdlc:ship") | {} == {
        "kind": "skill", "name": "sdlc:ship", "plugin": "sdlc", "uses": 0,
        "state": "unmeasured", "why": "no change recorded it",
    }  # fmt: skip
    assert _item(s, "command", "sdlc.py:ship")["why"] == "no change recorded it"
    _close(root, "002-keep-one-draft", SKILLS, TOOLS)
    s = _surface(root)
    assert _item(s, "skill", "sdlc:ship")["state"] == "unused", "a record could have shown it"
    assert _item(s, "skill", "sdlc:idea")["why"] == "runs outside a change's sessions"
    assert _item(s, "command", "sdlc.py:made-up")["why"] == "no skill runs it"
    assert _item(s, "command", "sdlc.py:publish")["why"] == "runs outside a change's sessions"
    assert not [i for i in s["items"] if i["state"] == "unused" and i.get("why")]


def test_a_supervised_skills_calls_are_unmeasured(tmp_path: Path, monkeypatch) -> None:
    """The factory's supervisor keeps a change's typed command, never its calls: a command only
    `/sdlc-factory:build` or `land` runs is unmeasured, and the skill itself is measured."""
    monkeypatch.setattr(sdlc, "factory_enabled", lambda home: (True, "project"))
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", SKILLS, TOOLS)
    s = _surface(root)
    assert _item(s, "command", "factory.py:train")["why"] == "runs outside a change's sessions"
    assert _item(s, "skill", "sdlc-factory:build")["state"] == "unused"


def test_every_skill_says_where_it_runs() -> None:
    """R6: each skill, core or factory, opens a stage (`metrics.SKILL_STAGE`) or is classed in
    `SKILL_RUNS`; the class names nothing that isn't a skill."""
    folders = {f"sdlc:{p.parent.name}" for p in (ROOT / "skills").glob("*/SKILL.md")} | {
        f"sdlc-factory:{p.parent.name}"
        for p in (ROOT / "plugins" / "factory" / "skills").glob("*/SKILL.md")
    }
    runs = sdlc.retro.SKILL_RUNS
    assert folders - set(sdlc.metrics.SKILL_STAGE) - set(runs) == set()
    assert set(runs) <= folders and set(sdlc.metrics.SKILL_STAGE) <= folders
    assert set(runs.values()) <= {"inside", "outside", "supervised"}


# ---------------------------------------------------------------- R7: the share


def test_the_share_leaves_out_the_unmeasured(tmp_path: Path) -> None:
    """R7: used / (used + unused) per kind and overall, the unmeasured in neither; and the window's
    changes that recorded skills or calls, with why the rest didn't."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts")
    _close(root, "002-keep-one-draft", SKILLS, TOOLS)
    s = _surface(root)
    skills = [i for i in s["items"] if i["kind"] == "skill"]
    used = sum(i["state"] == "used" for i in skills)
    unused = sum(i["state"] == "unused" for i in skills)
    assert (used, unused) == (1, 3), "spec used; intent, ship, close unused; the rest unmeasured"
    assert s["share"]["skills"] == 0.25
    every = [i for i in s["items"] if i["state"] != "unmeasured"]
    assert s["share"]["overall"] == round(sum(i["state"] == "used" for i in every) / len(every), 2)
    assert s["coverage"] == {"measured": 1, "of": 2, "greyed": False}
    assert s["missing_because"] == {"not measured at close": 1}


# ---------------------------------------------------------------- R8: retire candidates


def _windows(root: Path, *closes: tuple[str, ...]) -> None:
    """One retrospective window a change, oldest first, each `Close` carrying its trailers."""
    for n, trailers in enumerate(closes, 1):
        if n > 1:
            _record(root, f"2026-10-{n:02d}")
        _close(root, f"{n:03d}-change-{n}", *trailers)


def _retire(root: Path) -> tuple[set[str], int]:
    retire = _surface(root)["retire"]
    return {i["name"] for i in retire["items"]}, retire["windows"]


def test_retire_needs_n_unused_windows(tmp_path: Path) -> None:
    """R8: an item unused in each of the last `RETIRE_AFTER` windows that measured it is a
    candidate; a window that couldn't measure it is passed over, neither counting nor breaking
    the run."""
    assert sdlc.retro.RETIRE_AFTER == 3
    root = _repo(tmp_path / "a")
    _windows(root, ("Sdlc-Skill: sdlc:intent runs=1", TOOLS), (SKILLS, TOOLS), (SKILLS, TOOLS))
    names, windows = _retire(root)
    assert windows == 3
    assert "sdlc:close" in names, "unused in all three"
    assert "sdlc:intent" not in names, "used in the oldest"
    assert "sdlc.py:ship" not in names, "used in every one"
    _record(root, "2026-10-20")
    _close(root, "004-old-style", TOOLS)
    names, windows = _retire(root)
    assert "sdlc:close" in names and windows == 4, "the newest measured no skill: passed over"


def test_an_item_unmeasured_in_one_of_n_windows_is_not_named(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _windows(root, (SKILLS, TOOLS), (TOOLS,), (SKILLS, TOOLS))
    names, windows = _retire(root)
    assert "sdlc:close" not in names and windows == 3, "two measured windows of three"


def test_the_walk_stops_where_a_kind_was_not_yet_counted(tmp_path: Path) -> None:
    """A window measured from its transcripts without `Sdlc-Skill` closed before skills were
    counted, and so did every older one: the walk stops there for skills."""
    root = _repo(tmp_path)
    old = ("Sdlc-Totals: elapsed=10 tools=1 words=1", TOOLS)
    _windows(root, (SKILLS, TOOLS), old, (SKILLS, TOOLS), (SKILLS, TOOLS))
    names, _ = _retire(root)
    assert "sdlc:close" not in names
    assert "sdlc.py:status" in names, "commands were counted there: the walk goes on for them"


def test_retire_with_too_few_windows_names_nothing(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", SKILLS, TOOLS)
    _record(root, "2026-10-05")
    _close(root, "002-keep-one-draft", SKILLS, TOOLS)
    retire = _surface(root)["retire"]
    assert retire["items"] == [] and retire["windows"] == 2


# ---------------------------------------------------------------- R9: footprint


def test_footprint_counts_what_setup_left(tmp_path: Path) -> None:
    """R9: setup's `created` paths, the keys the config sets, and the lines under `.sdlc/` but
    the change folders, reports and retrospectives."""
    root = _repo(tmp_path, '[git]\nbase = "main"\npush = false\n')
    s = _surface(root)
    assert s["footprint"] is None
    assert s["why"]["footprint"] == "no .sdlc/setup.json on the base branch"
    manifest = {"version": "1.0.0", "config_keys": [], "created": [".sdlc/SDLC.md", "CLAUDE.md"]}
    (root / ".sdlc" / "setup.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / ".sdlc" / "SDLC.md").write_text("one\ntwo\n", encoding="utf-8")
    for rel in ("work/inbox.md", "retros/2026-10-10.md", "reports/x/out.md"):
        (root / ".sdlc" / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / ".sdlc" / rel).write_text("left\nout\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "setup")
    s = _surface(root)
    assert s["footprint"] == {"created": 2, "keys": 2, "lines": 3 + 1 + 2}
    assert "footprint" not in s["why"]


# ---------------------------------------------------------------- R10: growth


def _release(root: Path, version: str, commands: list[str], skills: list[str], keys: int) -> None:
    (root / "scripts").mkdir(exist_ok=True)
    (root / "scripts" / "sdlc.py").write_text(
        "".join(f'@command("{c}", "about")\ndef f(): ...\n' for c in commands), encoding="utf-8"
    )
    for s in skills:
        (root / "skills" / s).mkdir(parents=True, exist_ok=True)
        (root / "skills" / s / "SKILL.md").write_text(f"# {s}\n", encoding="utf-8")
    (root / ".sdlc").mkdir(exist_ok=True)
    keys_json = json.dumps({"config_keys": [f"k.{n}" for n in range(keys)], "created": []})
    (root / ".sdlc" / "setup.json").write_text(keys_json, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Release {version}")
    _git(root, "tag", "-a", f"v{version}", "-m", f"v{version}")


def test_growth_reads_each_release_tag(tmp_path: Path, monkeypatch) -> None:
    """R10: one row per tag in the window and the tag before the first, each count read at its
    tag with its change since the one before, and the major and minor changes between them; null
    where a count can't be read; and nothing in a host."""
    root = _repo(tmp_path)
    assert _surface(root)["growth"] is None
    assert _surface(root)["why"]["growth"] == "only in the plugin's own repo"
    monkeypatch.setattr(sdlc, "_own_repo", lambda home: True)
    (root / "scripts").mkdir()
    (root / "scripts" / "sdlc.py").write_text("sub.add_parser('status')\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Release 0.9.0")
    _git(root, "tag", "-a", "v0.9.0", "-m", "v0.9.0")
    _release(root, "1.0.0", ["status", "new"], ["intent"], 3)
    _record(root, "2026-10-05")
    _close(root, "001-reopen-drafts", impact="minor")
    _close(root, "002-keep-one-draft", impact="patch")
    _release(root, "1.1.0", ["status", "new", "close"], ["intent", "close"], 4)
    rows = _surface(root)["growth"]
    assert [r["tag"] for r in rows] == ["v1.0.0", "v1.1.0"]
    assert (rows[0]["commands"], rows[0]["skills"], rows[0]["keys"]) == (2, 1, 3)
    assert rows[0]["change"] is None and rows[0]["capability"] is None
    assert rows[1]["change"]["commands"] == 1 and rows[1]["change"]["skills"] == 1
    assert rows[1]["change"]["keys"] == 1 and rows[1]["change"]["doc_lines"] == 1
    assert rows[1]["capability"] == ["001-reopen-drafts"]
    # Before the registry, no command can be counted, and nothing is subtracted from it.
    _git(root, "tag", "-d", "v1.0.0")
    rows = _surface(root)["growth"]
    assert [r["tag"] for r in rows] == ["v0.9.0", "v1.1.0"]
    assert rows[0]["commands"] is None and rows[0]["keys"] is None
    assert rows[1]["change"]["commands"] is None
