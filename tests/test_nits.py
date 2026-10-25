"""work/nits.md: the nits ship approved unfixed. `nits` lists them, `check` audits them, `retro`
counts them by theme and age, and release and publish never look."""

from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_nits", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

GOOD = """\
# Nits

> The note.

## 003-1 [robustness] A registry that isn't UTF-8 crashes status
- **raised:** 2026-10-04 by 003-test-lifetimes (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** med

What's wrong.

## 005-2 [robustness] Timed-out output kept as bytes
- **raised:** 2026-10-10 by 005-acceptance-checks (correctness)
- **paths:** scripts/
- **cost:** S  **value:** low

## 009-1 [style] An idiom
- **raised:** 2026-10-20 by 009-drift-message (cost)
- **paths:** tests/test_defaults.py, docs/
- **cost:** M  **value:** low
"""

INTENT = """\
---
id: 001
slug: reopen-drafts
tier: 1
impact:
stage: plan
created: 2026-10-01
updated: 2026-10-01
idea:
depends_on:
---

# 001 — Reopen drafts
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, nits: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "work").mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    if nits is not None:
        (root / "work" / "nits.md").write_text(nits, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _nits(root: Path, capsys, *args: str) -> tuple[int, dict]:
    touching = list(args[args.index("--touching") + 1 :]) if "--touching" in args else None
    change = args[args.index("--change") + 1] if "--change" in args else None
    code = sdlc.cmd_nits(root, touching, change)
    return code, json.loads(capsys.readouterr().out)


def test_a_register_reads_as_its_entries(tmp_path: Path) -> None:
    root = _repo(tmp_path, GOOD)
    nits, problems = sdlc.nit_entries(root)
    assert problems == []
    assert [n["id"] for n in nits] == ["003-1", "005-2", "009-1"]
    first = nits[0]
    assert first["theme"] == "robustness" and first["by"] == "003-test-lifetimes"
    assert first["raised"] == "2026-10-04" and first["pass"] == "correctness"
    assert first["paths"] == ["scripts/sdlc.py"] and first["text"] == "What's wrong."
    assert (first["cost"], first["value"]) == ("S", "med")
    assert nits[2]["paths"] == ["tests/test_defaults.py", "docs/"]


def test_no_register_is_no_nits_and_no_problem(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    assert sdlc.nit_entries(root) == ([], [])
    code, out = _nits(root, capsys)
    assert code == 0 and out["nits"] == [] and out["problems"] == []
    assert not any(p["kind"] == "nits" for p in sdlc.analyze(root)["problems"])


def test_the_template_alone_holds_no_entry(tmp_path: Path) -> None:
    root = _repo(tmp_path, (ROOT / "templates" / "nits.md").read_text(encoding="utf-8"))
    assert sdlc.nit_entries(root) == ([], [])


def test_each_malformed_entry_is_a_problem_check_reports(tmp_path: Path) -> None:
    bad = GOOD + (
        "\n## not a nit heading\n"
        "\n## 003-1 [robustness] Twice\n"
        "- **raised:** 2026-10-04 by 003-test-lifetimes (correctness)\n"
        "- **paths:** a\n- **cost:** S  **value:** med\n"
        "\n## 011-1 [docs] Missing and wrong\n"
        "- **raised:** yesterday by 011-x\n- **cost:** L  **value:** high\n"
    )
    root = _repo(tmp_path, bad)
    problems = sdlc.nit_entries(root)[1]
    assert any("'## not a nit heading'" in p for p in problems)
    assert "003-1 is used twice" in problems
    assert any("011-1: raised 'yesterday'" in p for p in problems)
    assert "011-1 has no `- **paths:**`" in problems
    assert any(p.startswith("011-1: cost must be one of S|M") for p in problems)
    assert any(p.startswith("011-1: value must be one of med|low") for p in problems)
    found = [p for p in sdlc.analyze(root)["problems"] if p["kind"] == "nits"]
    assert len(found) == len(problems) and all(p["dir"] == "work/nits.md" for p in found)


def test_a_register_that_isnt_utf8_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "work" / "nits.md").write_bytes(b"# Nits\n\n\xff\xfe\n")
    nits, problems = sdlc.nit_entries(root)
    assert nits == [] and problems and problems[0].startswith("can't be read")


def test_touching_keeps_the_nits_on_those_paths(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, GOOD)
    code, out = _nits(root, capsys, "--touching", "scripts/sdlc.py")
    # 005-2 names the folder, so a file inside it touches it too.
    assert code == 0 and [n["id"] for n in out["nits"]] == ["003-1", "005-2"]
    code, out = _nits(root, capsys, "--touching", "docs/REFERENCE.md")
    assert [n["id"] for n in out["nits"]] == ["009-1"]
    assert all(isinstance(n["age_days"], int) for n in out["nits"])


def test_change_keeps_the_nits_its_diff_touches(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, GOOD)
    _git(root, "checkout", "-q", "-b", "001-reopen-drafts")
    folder = root / "work" / "001-reopen-drafts"
    folder.mkdir()
    (folder / "intent.md").write_text(INTENT, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_defaults.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "work")
    code, out = _nits(root, capsys, "--change", "001")
    assert code == 0 and [n["id"] for n in out["nits"]] == ["009-1"]


def test_retro_counts_open_nits_by_theme_and_age(tmp_path: Path) -> None:
    root = _repo(tmp_path, GOOD)
    got = sdlc.nits_summary(sdlc.nit_entries(root)[0], date(2026, 10, 24))
    assert got == {
        "open": 3,
        "themes": {
            "robustness": {"count": 2, "oldest": "2026-10-04", "age_days": 20},
            "style": {"count": 1, "oldest": "2026-10-20", "age_days": 4},
        },
    }
    out = sdlc.retro(root, sdlc.load_config(root)[0], date(2026, 10, 24))
    assert out["nits"] == got
    empty = _repo(tmp_path / "empty")
    assert sdlc.retro(empty, sdlc.load_config(empty)[0])["nits"] == {"open": 0, "themes": {}}


def test_a_malformed_raised_date_is_never_a_themes_oldest() -> None:
    nits = [{"theme": "x", "raised": "2026-00-01"}, {"theme": "x", "raised": "2026-10-04"}]
    got = sdlc.nits_summary(nits, date(2026, 10, 24))
    assert got["themes"]["x"] == {"count": 2, "oldest": "2026-10-04", "age_days": 20}


def test_this_repos_register_reads_clean() -> None:
    nits, problems = sdlc.nit_entries(ROOT)
    assert problems == []
    assert all(n["by"] and n["raised"] for n in nits)


def test_release_and_publish_never_read_the_register() -> None:
    """The release cycle is for shipping: the in-change and retro loops pay nits down."""
    for skill in ("release", "publish"):
        text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "nits" not in text, skill
    for fn in (sdlc.cmd_release, sdlc.cmd_publish):
        source = inspect.getsource(fn)
        assert "nits" not in source and "nit_" not in source, fn.__name__
