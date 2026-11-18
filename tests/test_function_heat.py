"""This repo's function-level hotspots for the retrospective's architecture pass: which top-level
functions the commits since the last retrospective rewrote, and how big each is, read from a
scratch repo's base branch.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".sdlc" / "function-heat.py"
_spec = importlib.util.spec_from_file_location("sdlc_function_heat_test", SCRIPT)
heat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(heat)

pytestmark = pytest.mark.portable

ONE = """\
def small():
    return 1


def big(x):
    y = x
    y += 1
    return y


class Box:
    def method(self):
        return 2
"""


def _git(repo: Path, *args: str) -> str:
    ran = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", check=True
    )
    return ran.stdout


def _commit(repo: Path, message: str, text: str | None = None) -> None:
    if text is not None:
        (repo / "mod.py").write_text(text, encoding="utf-8", newline="\n")
        _git(repo, "add", "mod.py")
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)


@pytest.fixture
def repo(tmp_path: Path, git_identity) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _commit(tmp_path, "first", ONE)
    return tmp_path


def _rows(repo: Path) -> dict[str, dict]:
    return {r["name"]: r for r in heat.heat(repo, "main", ["mod.py"])["mod.py"]}


def test_only_top_level_functions_are_read_with_their_line_ranges():
    assert heat.functions(ONE) == [("small", 1, 2), ("big", 5, 8)]


def test_with_no_retrospective_the_whole_history_counts(repo: Path):
    _commit(repo, "second", ONE.replace("y += 1", "y += 2"))
    rows = _rows(repo)
    assert rows["big"] == {"name": "big", "commits": 2, "lines": 4}
    assert rows["small"]["commits"] == 1
    assert "method" not in rows and "Box" not in rows


def test_only_commits_after_the_last_retrospective_count(repo: Path):
    _commit(repo, "Retrospective 2026-01-01")
    _commit(repo, "touch big", ONE.replace("y += 1", "y += 2"))
    rows = _rows(repo)
    assert rows["big"]["commits"] == 1
    assert rows["small"]["commits"] == 0


def test_ranked_by_commits_then_size_and_cut_to_the_top():
    rows = [
        {"name": "a", "commits": 1, "lines": 50},
        {"name": "b", "commits": 3, "lines": 5},
        {"name": "c", "commits": 1, "lines": 90},
        {"name": "d", "commits": 0, "lines": 900},
    ]
    assert [r["name"] for r in heat.rank(rows, top=3)] == ["b", "c", "a"]


def test_the_table_names_each_file_and_function_with_its_numbers():
    text = heat.render(
        {"mod.py": [{"name": "big", "commits": 2, "lines": 4}]}, {"sha": "abc1234", "date": "x"}
    )
    assert "mod.py" in text
    assert "big" in text and "2" in text and "4" in text
    assert "abc1234" in text


def test_it_reads_the_base_branch_and_writes_nothing(repo: Path):
    _git(repo, "checkout", "-q", "-b", "side")
    _commit(repo, "on the side", ONE.replace("return 1", "return 9"))
    (repo / "mod.py").write_text("def other():\n    pass\n", encoding="utf-8", newline="\n")
    before = _git(repo, "status", "--porcelain")
    ran = subprocess.run(
        [sys.executable, str(SCRIPT), "mod.py"],
        cwd=repo, capture_output=True, encoding="utf-8",
    )  # fmt: skip
    assert ran.returncode == 0, ran.stderr
    assert "small" in ran.stdout and "big" in ran.stdout
    assert "other" not in ran.stdout
    assert _git(repo, "status", "--porcelain") == before


def test_a_file_missing_on_the_base_is_said_not_raised(repo: Path):
    result = heat.heat(repo, "main", ["gone.py"])
    assert result["gone.py"] == []
