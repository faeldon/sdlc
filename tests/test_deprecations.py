"""The shim registry: `release.deprecations` lists the code kept working for something older and the
version that removes it, so a release can't carry an overdue shim and status says what's due.

Each repo here is built the way close leaves one, as in test_release.py: a tagged version, then a
change's own commit and its `Close` commit.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_shims", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

PKG = '{\n  "name": "demo",\n  "version": "{v}"\n}\n'
CONFIG = '[release]\nversion_files = ["pkg.json"]\n'
INTENT = """\
---
id: {id}
slug: {slug}
tier: 1
impact: {impact}
stage: shipped
created: 2026-10-01
updated: 2026-10-02
idea:
---

# {id} — {slug}

## Problem

Real prose.
"""
SHIM = '[[shim]]\nname = "old-flag"\nremove_in = "{v}"\nwhere = "scripts/x.py"\n'


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, version: str = "1.0.0", config: str = CONFIG) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pkg.json").write_text(PKG.replace("{v}", version), encoding="utf-8")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "tag", "-a", f"v{version}", "-m", f"v{version}")
    return root


def _close(root: Path, name: str = "001-reopen-drafts", impact: str = "patch") -> None:
    nid, slug = name.split("-", 1)
    folder = root / ".sdlc" / "work" / name
    folder.mkdir(parents=True)
    text = INTENT.format(id=nid, slug=slug, impact=impact)
    (folder / "intent.md").write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Ship {name}")
    _git(root, "rm", "-r", "-q", f".sdlc/work/{name}")
    _git(root, "commit", "-q", "-m", f"Close {name}")


def _registry(root: Path, text: str) -> None:
    (root / ".sdlc" / "deprecations.toml").write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "registry")


def _read(root: Path) -> dict:
    return sdlc.deprecations(root, sdlc.load_config(root)[0])


def _unreleased(root: Path) -> dict:
    return sdlc.unreleased(root, sdlc.load_config(root)[0])


def _release(capsys, root: Path, **kw) -> tuple[int, dict]:
    code = sdlc.cmd_release(root, **kw)
    return code, json.loads(capsys.readouterr().out)


def _state(root: Path) -> tuple[str, str, str]:
    return _git(root, "status", "--porcelain"), _git(root, "tag"), _git(root, "rev-parse", "HEAD")


def _main(monkeypatch, capsys, root: Path, *argv: str) -> tuple[int, str]:
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", *argv])
    code = sdlc.main()
    return code, capsys.readouterr().out


# ---------------------------------------------------------------- R1: the key


def test_without_a_registry_nothing_changes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root)
    reg = _read(root)
    assert reg == {"path": ".sdlc/deprecations.toml", "exists": False, "shims": [], "problems": []}
    u = _unreleased(root)
    assert u["deprecations"] == {"overdue": [], "due": [], "unversioned": []}
    assert u["next"] == "1.0.1" and not u["problems"]


def test_config_prints_the_deprecations_key(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _repo(tmp_path, config=CONFIG + 'deprecations = "ops/shims.toml"\n')
    code, out = _main(monkeypatch, capsys, root, "config")
    assert code == 0
    assert json.loads(out)["release"]["deprecations"] == "ops/shims.toml"
    assert sdlc.CONFIG_KEYS["release"]["deprecations"] == ".sdlc/deprecations.toml"


# ---------------------------------------------------------------- R2: the format


@pytest.mark.parametrize(
    ("text", "why"),
    [
        ("[[shim\n", "won't parse"),
        ('[other]\nx = "y"\n', "may hold only [[shim]] tables"),
        ('shim = ["old-flag"]\n', "shim 1 isn't a table"),
        ('[[shim]]\nname = "old-flag"\nwhere = "x"\n', "remove_in is missing"),
        (SHIM.format(v="2.0.0") + 'owner = "ana"\n', "owner isn't a key a shim has"),
        (SHIM.format(v="2.0.0") + "test = 3\n", "test must be a string"),
        (SHIM.format(v="2.0.0") * 2, "its name is used twice"),
        (SHIM.format(v="2.0"), "remove_in '2.0' isn't X.Y.Z"),
        ('[[shim]]\nname = "old-flag"\nremove_in = 1.10\nwhere = "x"\n', "quoted X.Y.Z"),
    ],
    ids=[
        "parse",
        "top-level",
        "not-a-table",
        "missing",
        "unknown",
        "not-a-string",
        "duplicate",
        "bad-version",
        "unquoted",
    ],
)
def test_registry_problem(tmp_path: Path, text: str, why: str) -> None:
    root = _repo(tmp_path)
    _registry(root, text)
    reg = _read(root)
    assert any(why in p for p in reg["problems"]), reg["problems"]
    names = [s["name"] for s in reg["shims"]]
    assert names in ([], ["old-flag"]), "a bad entry is left out, a good one kept"


def test_an_empty_registry_has_no_shims(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _registry(root, "# nothing yet\n")
    assert _read(root) | {"path": None} == {
        "path": None,
        "exists": True,
        "shims": [],
        "problems": [],
    }


# ---------------------------------------------------------------- R3: due and overdue


def test_overdue_and_due_compare_as_versions() -> None:
    def shim(name: str, v: str) -> dict:
        return {"name": name, "remove_in": v, "where": "x", "test": None}

    shims = [shim("a", "1.9.0"), shim("b", "1.10.0"), shim("c", "1.11.0"), shim("d", "2.0.0")]
    overdue, due = sdlc.shims_due(shims, "1.9.0", "1.10.0")
    assert [s["name"] for s in overdue] == ["a"]
    assert [s["name"] for s in due] == ["b"], "1.10.0 comes after 1.9.0, not before it"
    assert sdlc.shims_due(shims, None, None) == ([], [])


def test_nothing_is_due_with_nothing_to_release(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _registry(root, SHIM.format(v="1.0.1"))
    u = _unreleased(root)
    assert u["next"] is None and u["deprecations"]["due"] == []
    _close(root)
    assert [s["name"] for s in _unreleased(root)["deprecations"]["due"]] == ["old-flag"]


def test_a_shim_the_current_version_still_carries_is_overdue(tmp_path: Path) -> None:
    root = _repo(tmp_path, version="1.2.0")
    _registry(root, SHIM.format(v="1.2.0"))
    d = _unreleased(root)["deprecations"]
    assert [s["name"] for s in d["overdue"]] == ["old-flag"] and d["due"] == []


def test_without_version_files_shims_are_unversioned(tmp_path: Path) -> None:
    root = _repo(tmp_path, config="")
    _registry(root, SHIM.format(v="1.0.1"))
    d = _unreleased(root)["deprecations"]
    assert d["overdue"] == [] and d["due"] == []
    assert [s["name"] for s in d["unversioned"]] == ["old-flag"]


def test_a_bad_registry_blocks_the_bump(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root)
    _registry(root, SHIM.format(v="soon"))
    u = _unreleased(root)
    assert u["next"] is None
    assert any("isn't X.Y.Z" in p for p in u["problems"])


# ---------------------------------------------------------------- R4: release refuses


def test_release_refuses_a_due_shim_before_writing(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root)
    _registry(root, SHIM.format(v="1.0.1") + 'test = "tests/test_x.py::test_old_flag"\n')
    before = _state(root)
    code, report = _release(capsys, root)
    assert code == 1
    assert any(
        "shim old-flag is due by 1.0.1" in r and "scripts/x.py" in r and "test_old_flag" in r
        for r in report["refusals"]
    ), report["refusals"]
    assert _state(root) == before


def test_check_refuses_it_too(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root)
    _registry(root, SHIM.format(v="1.0.1"))
    code, report = _release(capsys, root, check_only=True)
    assert code == 1 and any("old-flag" in r for r in report["refusals"])


def test_a_version_past_remove_in_refuses(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root)
    _registry(root, SHIM.format(v="1.5.0"))
    assert _release(capsys, root, check_only=True)[0] == 0, "1.0.1 doesn't reach 1.5.0"
    code, report = _release(capsys, root, check_only=True, version="2.0.0")
    assert code == 1 and any("due by 2.0.0" in r for r in report["refusals"])


def test_a_later_shim_does_not_refuse(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    _close(root)
    _registry(root, SHIM.format(v="1.1.0"))
    code, report = _release(capsys, root)
    assert code == 0 and report["done"][-1] == "tag"


# ---------------------------------------------------------------- R5: status warns, never gates


def test_status_is_unchanged_without_a_registry(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _repo(tmp_path)
    _close(root)
    _, before = _main(monkeypatch, capsys, root, "status")
    monkeypatch.setattr(sdlc, "deprecations", lambda home, cfg: {"shims": [], "problems": []})
    _, without = _main(monkeypatch, capsys, root, "status")
    assert before == without
    assert "shim" not in before


def test_status_lists_due_and_overdue_shims(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _repo(tmp_path, version="1.2.0")
    _close(root)
    _registry(root, SHIM.format(v="1.2.0") + SHIM.format(v="1.2.1").replace("old-flag", "older"))
    _, out = _main(monkeypatch, capsys, root, "status")
    unreleased = out.split("■ Unreleased")[1].split("■ ")[0]
    assert "⚠  shim old-flag is overdue: remove in 1.2.0 (scripts/x.py)" in unreleased
    assert "⚠  shim older: remove in 1.2.1 (scripts/x.py)" in unreleased


def test_check_strict_ignores_shims(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _repo(tmp_path, version="1.2.0")
    _registry(root, SHIM.format(v="1.0.0"))
    assert _unreleased(root)["deprecations"]["overdue"], "there is an overdue shim"
    code, _ = _main(monkeypatch, capsys, root, "check", "--strict")
    assert code == 0


# ---------------------------------------------------------------- R6: this repo's own registry


def _registry_faults(reg: dict, version: str | None, tests: Path) -> list[str]:
    """What keeps a repo's registry from passing its own gate: a problem, a shim the version
    already released still carries, or a `test` naming nothing."""
    faults = list(reg["problems"])
    overdue, _ = sdlc.shims_due(reg["shims"], version, None)
    faults += [f"{s['name']} is overdue: remove_in {s['remove_in']}" for s in overdue]
    for s in reg["shims"]:
        if s["test"]:
            file, _, func = s["test"].partition("::")
            path = tests.parent / file
            found = path.is_file() and f"def {func}(" in path.read_text(encoding="utf-8")
            if not found:
                faults.append(f"{s['name']}: no test {s['test']}")
    return faults


def test_this_repos_shims_are_well_formed_and_not_overdue() -> None:
    reg = sdlc.deprecations(ROOT, sdlc.load_config(ROOT)[0])
    assert reg["exists"], "this repo keeps the registry it asks hosts to keep"
    assert _registry_faults(reg, sdlc.plugin_version(), ROOT / "tests") == []


def test_this_repos_check_fails_on_an_overdue_shim_or_a_missing_test(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_old_flag():\n    pass\n")
    _registry(root, SHIM.format(v="1.0.0") + 'test = "tests/test_x.py::test_gone"\n')
    faults = _registry_faults(_read(root), "1.0.0", root / "tests")
    assert faults == [
        "old-flag is overdue: remove_in 1.0.0",
        "old-flag: no test tests/test_x.py::test_gone",
    ]


def test_a_registry_that_isnt_utf8_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc" / "deprecations.toml").write_bytes(b"\xff\xfe[[shim]]\n")
    reg = _read(root)
    assert any("won't parse" in p for p in reg["problems"]), reg["problems"]
    assert reg["shims"] == []
