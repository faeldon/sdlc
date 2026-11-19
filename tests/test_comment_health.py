"""This repo's comment health for the retrospective's Quality pillar: comment density per file and
its band, docstring coverage of long and hot functions, the share of comments that narrate their
line, and comments' share of what agents read, read from a scratch repo's base branch.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".sdlc" / "comment-health.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


health = _load("sdlc_comment_health_test", SCRIPT)
retro = _load("sdlc_retro_comment_health_test", ROOT / "scripts" / "retro.py")
indicators = _load("sdlc_indicators_comment_health_test", ROOT / "scripts" / "indicators.py")

pytestmark = pytest.mark.portable

DENSITY = '''\
# /// script
# dependencies = []
# ///
"""Module doc."""  # and a note

import os  # noqa: F401

# a comment
x = 1  # trailing
"""not a docstring, an expression"""


def f():
    """Doc
    on two lines."""
    return "# not a comment"
'''


def _git(repo: Path, *args: str) -> str:
    ran = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", check=True
    )
    return ran.stdout


def _write(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    _git(repo, "add", path)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)


def _run(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=repo, capture_output=True, encoding="utf-8"
    )


def _parsed(text: str) -> dict[tuple[str, str], float]:
    return {(r["name"], r["unit"]): r["value"] for r in map(json.loads, text.splitlines())}


def _m(nonblank=100, marked=20, comment_lines=10, narration_lines=0, comment_bytes=0,
       size=1000, long=()):  # fmt: skip
    return {
        "nonblank": nonblank, "marked": marked, "comment_lines": comment_lines,
        "narration_lines": narration_lines, "comment_bytes": comment_bytes, "bytes": size,
        "long": list(long),
    }  # fmt: skip


def _long_source() -> str:
    body = "".join(f"    x{i} = {i}\n" for i in range(28))
    method = "".join(f"        y{i} = {i}\n" for i in range(28))
    return (
        "def short():\n    return 1\n\n\n"
        f'def long_one():\n    """Doc."""\n{body}\n\n'
        f"class Box:\n    def long_method(self):\n{method}        return 0\n\n"
        "    def tiny(self):\n        pass\n\n\n"
        f"def outer():\n    def inner():\n{method}        return 0\n    return inner\n"
    )


@pytest.fixture
def repo(tmp_path: Path, git_identity) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _write(tmp_path, "scripts/a.py", DENSITY)
    _write(tmp_path, "plugins/factory/scripts/b.py", _long_source())
    _write(tmp_path, "scripts/notes.md", "# not python\n")
    _commit(tmp_path, "first")
    return tmp_path


def test_density_counts_comment_and_docstring_lines_once():
    """R2: 12 non-blank lines, 5 of them comment or docstring lines (line 4 is both); the PEP 723
    block, the `# noqa` and the `#` inside a string are not comments."""
    m = health.measure(DENSITY)
    assert (m["nonblank"], m["marked"]) == (12, 5)
    assert m["comment_lines"] == 3
    assert _parsed(health.rows({"a.py": m}, []))[("a.py", "comment density")] == 0.417


def test_the_band_counts_files_below_and_above():
    """R3: 0.05 and 0.45 are outside the band; 0.10 and 0.40, its edges, are inside."""
    measured = {f"f{n}.py": _m(marked=n) for n in (5, 10, 20, 40, 45)}
    rows = _parsed(health.rows(measured, []))
    assert rows[("all scripts", "files outside 0.10-0.40")] == 2
    assert rows[("all scripts", "comment density")] == 0.24


def test_long_function_coverage_counts_methods_and_skips_short_ones():
    """R5: a top-level function and a top-level class's method of 30 lines count; a short one
    doesn't, and a function nested in another counts only as the one that holds it."""
    m = health.measure(_long_source())
    assert m["long"] == [("long_one", True), ("Box.long_method", False), ("outer", False)]
    rows = _parsed(health.rows({"b.py": m}, []))
    assert rows[("long functions (30+ lines)", "functions")] == 3
    assert rows[("long functions (30+ lines)", "share with a docstring")] == 0.333


def test_no_long_functions_prints_no_share():
    """R5, R6: a share of none isn't a number, so only the counts print."""
    rows = _parsed(health.rows({"a.py": health.measure(DENSITY)}, []))
    assert rows[("long functions (30+ lines)", "functions")] == 0
    assert rows[("hot functions", "functions")] == 0
    assert ("long functions (30+ lines)", "share with a docstring") not in rows
    assert ("hot functions", "share with a docstring") not in rows


def test_narration_is_told_from_explanation():
    """R7: a comment restating its line is narration; one saying why is not; a 3-line block is
    never narration; a trailing comment is read against its own line."""
    narrates = "retry_count = 0\n# increment the retry count\nretry_count += 1\n"
    explains = "# A rerun resumes here, so the push never repeats\n_push(home)\n"
    long_block = "# increment the retry count\n" * 3 + "retry_count += 1\n"
    trailing = "retry_count += 1  # increment retry count\n"
    no_words = "# --\nretry_count += 1\n"
    found = {
        name: (m["comment_lines"], m["narration_lines"])
        for name, m in (
            ("narrates", health.measure(narrates)),
            ("explains", health.measure(explains)),
            ("long_block", health.measure(long_block)),
            ("trailing", health.measure(trailing)),
            ("no_words", health.measure(no_words)),
        )
    }
    assert found == {
        "narrates": (1, 1),
        "explains": (1, 0),
        "long_block": (3, 0),
        "trailing": (1, 1),
        "no_words": (1, 0),
    }
    rows = _parsed(health.rows({"n.py": health.measure(narrates + explains)}, []))
    assert rows[("n.py", "narration share")] == 0.5
    assert rows[("all scripts", "narration share")] == 0.5


def test_words_split_identifiers_and_drop_short_and_stopwords():
    assert health.words("retryCount the_max_RETRY x  of ab") == {"retry", "count", "max"}


def test_token_share_is_comment_and_docstring_bytes_over_all_bytes():
    """R8: `\"\"\"doc\"\"\"` (9 bytes) and `# ab` (4) of 36 bytes; the `# noqa` is a directive."""
    source = '"""doc"""\nx = 1  # ab\ny = 2  # noqa\n'
    m = health.measure(source)
    assert (m["comment_bytes"], m["bytes"]) == (13, 36)
    rows = _parsed(health.rows({"t.py": m}, []))
    assert rows[("all scripts", "comment token share")] == 0.361
    assert rows[("all scripts", "comment est. tokens")] == 3


def test_rows_carry_no_source_text():
    """R11: names and numbers only."""
    marker = "zqxmarkerzqx"
    source = f'"""{marker}"""\n# {marker}\nx = 1  # {marker}\n\n\ndef {marker}_fn():\n    pass\n'
    text = health.rows({"m.py": health.measure(source)}, [])
    assert marker not in text


def test_a_file_that_does_not_parse_is_skipped_not_raised(repo: Path):
    """R10: its rows go, everyone else's stay."""
    assert health.measure("def (:\n") is None
    assert health.measure('"""never closed\n') is None
    _write(repo, "scripts/bad.py", "def (:\n")
    _commit(repo, "bad")
    ran = _run(repo)
    assert ran.returncode == 0, ran.stderr
    names = {name for name, _ in _parsed(ran.stdout)}
    assert "scripts/bad.py" not in names
    assert {"scripts/a.py", "plugins/factory/scripts/b.py"} <= names


def test_no_base_branch_exits_one(tmp_path: Path, git_identity):
    _git(tmp_path, "init", "-q", "-b", "trunk")
    _commit(tmp_path, "first")
    ran = _run(tmp_path)
    assert ran.returncode == 1
    assert len(ran.stderr.strip().splitlines()) == 1
    assert ran.stdout == ""


def test_its_output_reads_as_indicator_rows(repo: Path):
    """R1: 177's row shape, with no `(name, unit)` twice; a non-Python file is not measured."""
    ran = _run(repo)
    assert ran.returncode == 0, ran.stderr
    rows, reason = indicators.host_rows(ran.stdout)
    assert reason is None
    names = {r["name"] for r in rows}
    assert "scripts/notes.md" not in names
    assert {"scripts/a.py", "plugins/factory/scripts/b.py", "all scripts"} <= names


def test_it_reads_the_base_branch_and_writes_nothing(repo: Path):
    """R9: a side branch's commit and an uncommitted edit change nothing."""
    before = _run(repo).stdout
    _git(repo, "checkout", "-q", "-b", "side")
    _write(repo, "scripts/a.py", DENSITY + "# more\n# and more\n")
    _commit(repo, "on the side")
    (repo / "scripts" / "a.py").write_text("x = 1\n", encoding="utf-8", newline="\n")
    status = _git(repo, "status", "--porcelain")
    ran = _run(repo)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout == before
    assert _git(repo, "status", "--porcelain") == status


def test_rows_read_back_from_a_report(repo: Path):
    """R4: the trend is the report's own `Last retrospective` and `Change`, so every row must come
    back from the report under its own name and unit with its value."""
    rows, _ = indicators.host_rows(_run(repo).stdout)
    host = [{
        "command": "uv run --quiet --script .sdlc/comment-health.py",
        "rows": [{**r, "last": None, "change": None} for r in rows],
        "not_rows": None,
    }]  # fmt: skip
    back = indicators.report_rows(retro._indicators_text(host))
    assert {(r["name"], r["unit"]): r["value"] for r in rows} == back


HOT = '''\
def small():
    return 1


def big(x):
    """Doc."""
    y = x
    return y


def bare(x):
    return x
'''


def test_hot_functions_are_function_heats_with_a_commit(tmp_path: Path, git_identity):
    """R6: after a `Retrospective` commit, only the functions touched since are hot."""
    _git(tmp_path, "init", "-q", "-b", "main")
    _write(tmp_path, "mod.py", HOT)
    _commit(tmp_path, "first")
    _commit(tmp_path, "Retrospective 2026-01-01")
    _write(tmp_path, "mod.py", HOT.replace("y = x", "y = x + 1").replace("return x", "return 2"))
    _commit(tmp_path, "touch big and bare")
    assert health.hot(tmp_path, "main", ["mod.py"]) == [True, False]
    rows = _parsed(health.rows({}, [True, False]))
    assert rows[("hot functions", "functions")] == 2
    assert rows[("hot functions", "share with a docstring")] == 0.5


def test_hot_reads_function_heat_not_a_copy():
    """R6: the boundary and the ranking are function heat's, never a second copy to drift."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert not defined & {"blamed", "heat", "rank", "functions", "last_retrospective"}
    assert health.HEAT.__file__ == str(ROOT / ".sdlc" / "function-heat.py")


def test_this_repos_rows_stay_under_the_evidence_limit():
    """R12: every script this repo has, at the widest numbers, with every hot function function
    heat could keep, stays under the cut that would read the output as text."""
    paths = [
        p.relative_to(ROOT).as_posix()
        for d in ("scripts", "plugins/factory/scripts")
        for p in sorted((ROOT / d).rglob("*.py"))
    ]
    wide = _m(
        nonblank=10**7, marked=3_333_333, comment_lines=10**7, narration_lines=3_333_333,
        comment_bytes=10**9, size=3 * 10**9, long=[("f", True), ("g", False)] * 2,
    )  # fmt: skip
    hot = [True, False, False] * health.HEAT.TOP * len(health.HEAT.FILES)
    text = health.rows(dict.fromkeys(paths, wide), hot)
    assert len(text.splitlines()) == 2 * len(paths) + 5 + 2 + 2
    assert len(text) + 1 < retro.EVIDENCE_LIMIT


def test_this_repo_runs_comment_health():
    """R13: set in this repo's config, after function heat."""
    config = tomllib.loads((ROOT / ".sdlc" / "config.toml").read_text(encoding="utf-8"))
    commands = config["retro"]["indicators"]
    entry = "uv run --quiet --script .sdlc/comment-health.py"
    assert entry in commands
    assert commands.index(entry) > commands.index("uv run --quiet --script .sdlc/function-heat.py")
