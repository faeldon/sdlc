"""The architecture pass's counts, from git's output text: each path's kind, a change's size, the
medians per tier, hotspots, co-change, the largest files and each kind's totals. No repo needed;
`test_retro.py` runs them through `sdlc.py retro`."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "indicators.py"
_spec = importlib.util.spec_from_file_location("sdlc_indicators_test", SOURCE)
indicators = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(indicators)


def _none(path: str) -> bool:
    return False


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("tests/test_drafts.py", "tests"),
        ("pkg/test/helpers.py", "tests"),
        ("spec/drafts_spec.rb", "tests"),
        ("src/__tests__/drafts.js", "tests"),
        ("test_drafts.py", "tests"),
        ("drafts_test.go", "tests"),
        ("src/drafts.test.ts", "tests"),
        ("src/drafts.spec.ts", "tests"),
        ("docs/test_guide.md", "tests"),
        ("README.md", "docs"),
        ("guide/process.rst", "docs"),
        ("notes/usage.adoc", "docs"),
        ("LICENSE.txt", "docs"),
        ("docs/diagram.svg", "docs"),
        ("src/drafts.py", "code"),
        ("contest/entries.py", "code"),
        ("specs.py", "code"),
    ],
)
def test_the_conventions_tell_each_kind_by_path(path: str, kind: str) -> None:
    assert indicators.classify(path) == kind


def test_a_host_rule_replaces_the_convention_for_its_kind() -> None:
    def checks(path: str) -> bool:
        return path.startswith("checks/")

    assert indicators.classify("checks/drafts.sh", checks, indicators.is_doc) == "tests"
    assert indicators.classify("tests/test_drafts.py", checks, indicators.is_doc) == "code"
    assert indicators.classify("README.md", checks, _none) == "code"


def test_numstat_rows_keep_a_binary_file_without_counts() -> None:
    text = "3\t1\tsrc/a.py\n-\t-\tlogo.png\nnot a row\n"
    assert indicators.numstat_rows(text) == [("src/a.py", 3, 1), ("logo.png", None, None)]


def test_a_changes_size_is_split_by_kind() -> None:
    rows = [
        ("src/a.py", 10, 2),
        ("tests/test_a.py", 5, 0),
        ("docs/a.md", 1, 1),
        ("x.png", None, None),
    ]
    size = indicators.change_size(rows, indicators.classify)
    assert (size["added"], size["deleted"]) == (16, 3)
    assert size["by_kind"] == {
        "code": {"files": 2, "added": 10, "deleted": 2},
        "tests": {"files": 1, "added": 5, "deleted": 0},
        "docs": {"files": 1, "added": 1, "deleted": 1},
    }


def _sized(tier: int, added: int, files: int = 1) -> dict:
    rows = [(f"src/{tier}-{added}-{n}.py", added if n == 0 else 0, 0) for n in range(files)]
    return {"tier": tier, **indicators.change_size(rows, indicators.classify)}


def test_size_by_tier_takes_medians_and_skips_the_unsized() -> None:
    changes = [_sized(1, 10), _sized(1, 30, files=3), _sized(2, 100), {"tier": 2, "added": None}]
    size = indicators.size_by_tier(changes)
    assert size["1"]["changes"] == 2 and size["1"]["added"] == 20 and size["1"]["files"] == 2
    assert size["2"]["changes"] == 1 and size["2"]["added"] == 100
    assert size["1"]["by_kind"]["code"]["added"] == 20
    assert size["1"]["by_kind"]["tests"]["files"] == 0


def test_grep_counts_reads_a_path_holding_a_colon() -> None:
    text = "abc123:src/a.py:12\nabc123:odd:name.txt:3\nother:b.py:1\n"
    assert indicators.grep_counts(text, "abc123") == {"src/a.py": 12, "odd:name.txt": 3}


def test_hotspots_rank_by_changes_then_churn_and_skip_the_change_folders() -> None:
    lookback = [
        [("a.py", 1, 0), ("b.py", 50, 0), (".sdlc/work/001-x/intent.md", 9, 0)],
        [("a.py", 1, 0), ("b.py", 1, 0), ("gone.py", 0, 7)],
        [("a.py", 1, 0), (".sdlc/work/001-x/intent.md", 9, 0)],
    ]
    rows = indicators.hotspots(lookback, {"a.py": 5, "b.py": 80}, lambda p: p.startswith(".sdlc/"))
    assert [r["file"] for r in rows] == ["a.py", "b.py", "gone.py"]
    assert rows[0] == {"file": "a.py", "changes": 3, "lines_changed": 3, "lines": 5}
    assert rows[2]["lines"] is None


def test_co_change_lists_a_pair_only_from_three_changes_together() -> None:
    pair = [("a.py", 1, 0), ("b.py", 1, 0)]
    assert indicators.co_change([pair, pair], _none) == []
    rows = indicators.co_change([pair, pair, pair, [("a.py", 1, 0)]], _none)
    assert rows == [{"files": ["a.py", "b.py"], "together": 3, "changes": [4, 3]}]


def test_co_change_leaves_a_huge_change_out_of_the_pairs() -> None:
    huge = [(f"f{n}.py", 1, 0) for n in range(indicators.PAIR_FILES_MAX + 1)]
    assert indicators.co_change([huge, huge, huge], _none) == []


def test_largest_says_growth_only_against_a_then() -> None:
    now = {"a.py": 100, "b.py": 40, "new.py": 60, ".sdlc/work/inbox.md": 900}
    skip = lambda p: p.startswith(".sdlc/work/")  # noqa: E731
    rows = indicators.largest(now, {"a.py": 70, "b.py": 40}, skip)
    assert [r["file"] for r in rows] == ["a.py", "new.py", "b.py"]
    assert rows[0]["growth"] == 30 and rows[1] == {
        "file": "new.py", "lines": 60, "then": None, "growth": None,
    }  # fmt: skip
    assert all(
        r["then"] is None and r["growth"] is None for r in indicators.largest(now, None, skip)
    )


def test_totals_count_files_and_lines_per_kind() -> None:
    counts = {"src/a.py": 10, "tests/test_a.py": 4, "README.md": 2, ".sdlc/work/inbox.md": 9}
    out = indicators.totals(counts, indicators.classify, lambda p: p.startswith(".sdlc/work/"))
    assert out == {
        "code": {"files": 1, "lines": 10},
        "tests": {"files": 1, "lines": 4},
        "docs": {"files": 1, "lines": 2},
    }


def test_it_runs_nothing_and_never_imports_the_script() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    assert not names & {"subprocess", "sdlc", "os"}
