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
    assert rows[0] == {"file": "a.py", "changes": 3, "lines_changed": 3, "lines": 5, "gone": None}
    assert rows[2]["lines"] is None


def test_a_hotspot_with_no_lines_says_whether_it_is_gone() -> None:
    """R10 (nit 2026-11-12-1): `git grep -I -c` counts no binary or empty file, so `lines: None`
    alone can't tell one from a deleted file; the base branch's paths can."""
    lookback = [[("logo.png", 0, 0), ("empty.py", 0, 0), ("gone.py", 0, 7)]]
    rows = indicators.hotspots(lookback, {}, _none, present={"logo.png", "empty.py", "keep.py"})
    by = {r["file"]: (r["lines"], r["gone"]) for r in rows}
    assert by == {"logo.png": (None, False), "empty.py": (None, False), "gone.py": (None, True)}


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


def test_removed_ranges_read_only_what_a_diff_took_away() -> None:
    """Appending removes nothing and a new file has no old side; a quoted path reads as itself."""
    text = (
        "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n"
        "@@ -3,2 +3,2 @@\n-x\n-y\n+X\n+Y\n@@ -7 +7 @@\n--- a SQL comment\n+-- kept\n"
        "@@ -10 +10 @@\n-z\n+Z\n@@ -20,0 +21,4 @@\n+appended\n"
        "diff --git a/new.py b/new.py\nnew file mode 100644\n--- /dev/null\n+++ b/new.py\n"
        "@@ -0,0 +1 @@\n+fresh\n"
        'diff --git "a/caf\\303\\251.py" "b/caf\\303\\251.py"\n--- "a/caf\\303\\251.py"\n'
        '+++ "b/caf\\303\\251.py"\n@@ -1 +1 @@\n-old\n+new\n'
    )
    assert indicators.removed_ranges(text) == {
        "src/a.py": [(3, 2), (7, 1), (10, 1)],
        "café.py": [(1, 1)],
    }, "a removed `-- comment` line is no file header"


def test_blame_commits_take_each_line_s_sha_from_the_porcelain() -> None:
    a, b = "a" * 40, "b" * 40
    text = (
        f"{a} 3 3 2\nauthor x\nsummary first\nfilename src/a.py\n\tx\n"
        f"{a} 4 4\n\ty\n{b} 10 10 1\nauthor y\nfilename src/a.py\n\tz\n"
    )
    assert indicators.blame_commits(text) == [a, a, b]


# ---------------------------------------------------------------- spend (118)

DIFF_U0 = """\
diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,0 +2,4 @@
+# a comment
+x = 1  # trailing, not a comment line
+    # indented comment
+print(x)
diff --git a/src/b.py b/src/b.py
--- a/src/b.py
+++ b/src/b.py
@@ -3,0 +4,3 @@
+DOC = \"\"\"
+# a heading in a string, counted by design
+\"\"\"
diff --git a/web/c.ts b/web/c.ts
new file mode 100644
--- /dev/null
+++ b/web/c.ts
@@ -0,0 +1,2 @@
+// says what
+const c = 1;
diff --git a/db/q.sql b/db/q.sql
--- a/db/q.sql
+++ b/db/q.sql
@@ -1 +1,2 @@
-select 1;
+-- why
+++ select 2;
diff --git a/page.HTML b/page.HTML
--- a/page.HTML
+++ b/page.HTML
@@ -1,0 +1 @@
+<!-- a note -->
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,0 +1,2 @@
+# A heading, not a comment
+text
diff --git a/Makefile b/Makefile
--- a/Makefile
+++ b/Makefile
@@ -1,0 +1,2 @@
+# can't tell
+all:
diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-# gone
-y = 2
"""


def test_comment_lines_by_suffix() -> None:
    """R4: a line comment by its file's suffix, per line, not parsed: the `#` line inside a
    Python string counts by design. Prose is never comments; an unknown suffix is never guessed."""
    out = indicators.comment_lines(DIFF_U0)
    # `added` is the lines a marker could be read in; README's are counted nowhere.
    assert out == {"added": 4 + 3 + 2 + 2 + 1, "comment_lines": 6, "unknown_lines": 2}
    only_a = indicators.comment_lines(DIFF_U0, include=lambda p: p == "src/a.py")
    assert only_a == {"added": 4, "comment_lines": 2, "unknown_lines": 0}
    assert indicators.COMMENT_MARKERS[".py"] == "#"


def _row(name, tier, code, comments, out, tools, recorded=True, errors=0):
    return {
        "change": name, "tier": tier, "code_added": code, "comment_lines": comments,
        "out": out if recorded else None, "words": 5 if recorded else None,
        "tools": tools if recorded else None, "errors": errors if recorded else None,
        "by_tool": {} if not recorded else {"Read": {"calls": tools, "errors": errors}},
        "recorded": recorded,
    }  # fmt: skip


def test_spend_names_a_change_twice_its_tier_median() -> None:
    """R6: per tier the median comment share, out tokens and calls per added code line, and each
    change over twice its tier's median on any, with by how much."""
    rows = [
        _row("001-a", 2, 100, 10, 1000, 50),
        _row("002-b", 2, 100, 10, 1000, 50),
        _row("003-c", 2, 100, 30, 1000, 120),  # comments 3x, calls 2.4x
        _row("004-d", 2, 100, 10, 2000, 50),  # tokens exactly 2x: not more than twice
    ]
    out = indicators.spend(rows)
    assert out["tiers"]["2"] == {
        "changes": 4, "comment_share": 0.1, "out_per_line": 10.0, "tools_per_line": 0.5,
    }  # fmt: skip
    assert out["outliers"] == [
        {"change": "003-c", "tier": 2, "measure": "comment_share", "value": 0.3, "median": 0.1,
         "times": 3.0},
        {"change": "003-c", "tier": 2, "measure": "tools_per_line", "value": 1.2, "median": 0.5,
         "times": 2.4},
    ]  # fmt: skip


def test_a_tier_with_two_changes_names_no_outlier() -> None:
    """R6, R8: under 3 changes a tier gives no median; an unrecorded change is in the comment
    median alone (git says it), and in neither token nor call median."""
    rows = [_row("001-a", 1, 10, 0, 100, 5), _row("002-b", 1, 10, 9, 9000, 90)]
    out = indicators.spend(rows)
    assert out["tiers"]["1"] == {
        "changes": 2, "comment_share": None, "out_per_line": None, "tools_per_line": None,
    }  # fmt: skip
    assert out["outliers"] == []
    rows += [_row("003-c", 1, 10, 1, None, None, recorded=False)]
    tier = indicators.spend(rows)["tiers"]["1"]
    assert tier["comment_share"] == 0.1 and tier["out_per_line"] is None
    assert indicators.spend(rows)["recorded"] == 2


def test_spend_ranks_the_tools() -> None:
    """R7: across the window, each name's calls, errors, error share and changes."""
    rows = [_row("001-a", 1, 10, 0, 1, 0), _row("002-b", 1, 10, 0, 1, 0)]
    rows[0]["by_tool"] = {"Bash:make": {"calls": 4, "errors": 3}, "Read": {"calls": 9, "errors": 0}}
    rows[1]["by_tool"] = {"Bash:make": {"calls": 2, "errors": 0}}
    tools = indicators.spend(rows)["tools"]
    assert tools["most_called"] == [
        {"name": "Read", "calls": 9, "errors": 0, "error_share": 0.0, "changes": 1},
        {"name": "Bash:make", "calls": 6, "errors": 3, "error_share": 0.5, "changes": 2},
    ]
    assert [t["name"] for t in tools["most_errors"]] == ["Bash:make"]


# ---------------------------------------------------------------- the pruning pass (130)

SUITES = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="4">
<testcase classname="tests.test_drafts" name="test_reopen" file="tests/test_drafts.py" time="1.25"/>
<testcase classname="tests.test_drafts" name="test_save" time="nope"/>
<testcase name="test_titles" file="tests/test_titles.py" time="0.5"/>
<testsuite name="nested"><testcase classname="tests.test_sync" name="test_sync" time="0.1">
<skipped message="not on this platform"/></testcase></testsuite>
</testsuite></testsuites>
"""


def test_junit_times_reads_every_testcase() -> None:
    """130 R4: every `<testcase>` at any depth, under `<testsuites>` or a bare `<testsuite>`; an
    id from `classname`, else `file`; a missing or bad `time` is None, never 0."""
    out = indicators.junit_times(SUITES)
    assert out["error"] is None
    assert out["cases"] == [
        {"test": "tests.test_drafts::test_reopen", "file": "tests/test_drafts.py",
         "seconds": 1.25, "skipped": False},
        {"test": "tests.test_drafts::test_save", "file": None, "seconds": None, "skipped": False},
        {"test": "tests/test_titles.py::test_titles", "file": "tests/test_titles.py",
         "seconds": 0.5, "skipped": False},
        {"test": "tests.test_sync::test_sync", "file": None, "seconds": 0.1, "skipped": True},
    ]  # fmt: skip
    bare = (
        '<testsuite><testcase classname="a" name="b"/>'
        '<testcase classname="a" name="c" time="0"/></testsuite>'
    )
    cases = indicators.junit_times(bare)["cases"]
    assert [(c["test"], c["seconds"]) for c in cases] == [("a::b", None), ("a::c", None)]


@pytest.mark.parametrize("text", ["", "not xml", "<testsuite>", "<testsuites/>", "<a><b/></a>"])
def test_junit_that_does_not_parse_is_an_error_not_a_raise(text: str) -> None:
    out = indicators.junit_times(text)
    assert out["cases"] == [] and out["error"], out


def _change(*paths: str) -> list:
    return [(p, 1, 0) for p in paths]


TESTED = {"tests/test_drafts.py", "src/drafts.py", "src/store.py", "src/sync.py"}
# What each test file says, at the base branch: test_drafts.py loads drafts and store.
TEXTS = {
    "tests/test_drafts.py": "from src.drafts import reopen\nfrom src.store import Store\n",
    "tests/test_gone.py": "import drafts\n",
}


def _read(texts: dict[str, str] = TEXTS):
    return texts.get


def _drifted(lookback, present, skip=_none, texts=TEXTS) -> list[dict]:
    return indicators.drifted_tests(lookback, indicators.classify, skip, present, _read(texts))


def test_a_test_whose_code_moved_without_it_is_drifted() -> None:
    """130 R7: the code beside a test's last touch changed in three later changes without it."""
    lookback = [
        ("001-reopen-drafts", _change("tests/test_drafts.py", "src/drafts.py", "src/store.py")),
        ("002-a", _change("src/drafts.py")),
        ("003-b", _change("src/store.py", "src/sync.py")),
        ("004-c", _change("src/drafts.py", "src/store.py")),
    ]
    rows = _drifted(lookback, TESTED)
    assert rows == [
        {"file": "tests/test_drafts.py", "last_change": "001-reopen-drafts",
         "code": ["src/drafts.py", "src/store.py"], "later": 3},
    ]  # fmt: skip
    assert _drifted(lookback[:3], TESTED) == []


def test_a_test_moved_with_its_code_is_not_drifted() -> None:
    lookback = [
        ("001-a", _change("tests/test_drafts.py", "src/drafts.py")),
        ("002-b", _change("src/drafts.py")),
        ("003-c", _change("src/drafts.py")),
        ("004-d", _change("src/drafts.py", "tests/test_drafts.py")),
        ("005-e", _change("src/drafts.py")),
    ]
    assert _drifted(lookback, TESTED) == []


def test_a_deleted_test_is_never_drifted() -> None:
    lookback = [("001-a", _change("tests/test_gone.py", "src/drafts.py"))]
    lookback += [(f"00{n}-x", _change("src/drafts.py")) for n in range(2, 6)]
    assert _drifted(lookback, TESTED) == []
    rows = _drifted(lookback, TESTED | {"tests/test_gone.py"})
    assert [r["file"] for r in rows] == ["tests/test_gone.py"]


def test_a_change_too_large_to_pair_drifts_nothing() -> None:
    huge = [f"src/m{n}.py" for n in range(indicators.PAIR_FILES_MAX)]
    lookback = [("001-reformat", _change("tests/test_drafts.py", *huge))]
    lookback += [(f"00{n}-x", _change(*huge)) for n in range(2, 6)]
    texts = {"tests/test_drafts.py": "".join(f"import m{n}\n" for n in range(len(huge)))}
    assert _drifted(lookback, TESTED | set(huge), texts=texts) == []


def test_a_test_touched_by_a_change_too_large_to_pair_starts_again() -> None:
    """200: a test a large change touched was looked at there, so the changes before it never
    drift it; the large change gives it no code, so nothing after it does either."""
    huge = [f"src/m{n}.py" for n in range(indicators.PAIR_FILES_MAX)]
    lookback = [("001-a", _change("tests/test_drafts.py", "src/drafts.py"))]
    lookback += [(f"00{n}-x", _change("src/drafts.py")) for n in range(2, 6)]
    assert [r["file"] for r in _drifted(lookback, TESTED)] == ["tests/test_drafts.py"]
    lookback += [("006-reformat", _change("tests/test_drafts.py", *huge))]
    lookback += [(f"00{n}-y", _change("src/drafts.py")) for n in range(7, 10)]
    assert _drifted(lookback, TESTED | set(huge)) == []


def test_drift_skips_what_skip_says_and_reads_only_tests() -> None:
    lookback = [("001-a", _change("tests/test_drafts.py", "README.md", ".sdlc/x.py"))]
    lookback += [(f"00{n}-x", _change("README.md", ".sdlc/x.py")) for n in range(2, 6)]
    skip = lambda p: p.startswith(".sdlc/")  # noqa: E731
    present = TESTED | {"README.md", ".sdlc/x.py"}
    texts = {"tests/test_drafts.py": "import x\n# README.md\n"}
    assert _drifted(lookback, present, skip, texts) == []


def test_a_test_drifts_only_with_the_code_it_loads() -> None:
    """200: a test edited beside code it doesn't load never drifts with that code; the code it
    loads still drifts it, and its row names only that code."""
    lookback = [("001-a", _change("tests/test_drafts.py", "src/drafts.py", "src/big.py"))]
    lookback += [(f"00{n}-x", _change("src/big.py")) for n in range(2, 6)]
    texts = {"tests/test_drafts.py": "from src.drafts import reopen\n"}
    present = TESTED | {"src/big.py"}
    assert _drifted(lookback, present, texts=texts) == []
    lookback += [(f"00{n}-y", _change("src/big.py", "src/drafts.py")) for n in range(6, 9)]
    rows = _drifted(lookback, present, texts=texts)
    assert [(r["file"], r["code"], r["later"]) for r in rows] == [
        ("tests/test_drafts.py", ["src/drafts.py"], 3)
    ]
    assert _drifted(lookback, present, texts={}) == [], "a test with no text loads nothing"


def test_a_golden_never_drifts() -> None:
    """200: a fixture or a prompt an exact test compares against loads nothing, whatever it names,
    and is never read."""
    goldens = ["tests/fixtures/close-output.json", "tests/prompts/land-fix.txt"]
    lookback = [("001-a", _change(*goldens, "src/drafts.py"))]
    lookback += [(f"00{n}-x", _change("src/drafts.py")) for n in range(2, 6)]
    asked: list[str] = []

    def read(path: str) -> str:
        asked.append(path)
        return "drafts.py\nimport drafts\n"

    rows = indicators.drifted_tests(
        lookback, indicators.classify, _none, TESTED | set(goldens), read
    )
    assert rows == [] and asked == []


def test_loads_follows_a_helper_the_test_imports() -> None:
    """200: the code a test helper loads is the test's, as the helper is: `test_train.py` loads
    `factory.py` through `train_driver.py`; a cycle between helpers ends, and a test file only
    named, never imported, is no helper."""
    texts = {
        "tests/test_train.py": 'from train_driver import drive_train\nOTHER = "test_other.py"\n',
        "tests/test_other.py": 'SDLC = "sdlc.py"\n',
        "tests/train_driver.py": 'import helpers\nFACTORY = "factory.py"\n',
        "tests/helpers.py": "import train_driver\n",
    }
    paths = {*texts, "scripts/factory.py", "scripts/sdlc.py"}
    found = indicators.loads("tests/test_train.py", texts.get, paths, indicators.classify)
    assert found == {"scripts/factory.py"}


@pytest.mark.parametrize(
    ("text", "loaded"),
    [
        ('SCRIPT = ROOT / "scripts" / "sdlc.py"\n', {"scripts/sdlc.py"}),
        ("run('scripts/sdlc.py')\n", {"scripts/sdlc.py"}),
        ("from src.drafts import reopen\n", {"src/drafts.py"}),
        ("from src import drafts, store\n", {"src/drafts.py", "src/store.py"}),
        ("import src.store as s\n", {"src/store.py"}),
        ("const s = require('../src/store');\n", {"src/store.py"}),
        ("import { open } from './drafts.js';\n", {"src/drafts.py"}),
        ('#include "store.h"\n', {"src/store.py"}),
        ("use crate::drafts::open;\n", {"src/drafts.py"}),
        ("# the drafts are reopened from the store\n", set()),
        ("my_drafts.py and drafts.pyc\n", set()),
        ("# checks src/drafts.py\n", {"src/drafts.py"}),
        ('run("./src/drafts.py") and run("../src/store.py")\n', {"src/drafts.py", "src/store.py"}),
        ('"""`scripts/sdlc.py` reads it, as `sdlc.py retro` says."""\n', set()),
        ("load('evals/base/drafts.py')\n", set()),
        ("the branch and the main\n", set()),
        ('open("src/config.json")\n', set()),
    ],
)
def test_loads_reads_names_and_imports(text: str, loaded: set[str]) -> None:
    """200: a test loads a file it names in a string or by a path, or one whose stem a load line
    names; a word in prose or in backticks, a longer name, another file of the same name, a file
    with no suffix, or a data file loads nothing."""
    paths = {"tests/test_drafts.py", "src/drafts.py", "src/store.py", "scripts/sdlc.py",
             "src/config.json", "branch", "src/main"}  # fmt: skip
    read = {"tests/test_drafts.py": text}.get
    assert indicators.loads("tests/test_drafts.py", read, paths, indicators.classify) == loaded


# ---------------------------------------------------------------- the host's indicator rows (177)


def test_indicator_rows_are_read_from_json_lines() -> None:
    """R1: JSON Lines, each with a `name`, a numeric `value` and an optional `unit`; other keys
    kept as `extra`, a missing or null unit read as ""."""
    text = (
        '{"name": "src/drafts.py::save", "value": 3, "unit": "commits", "band": "high"}\n'
        "\n"
        '{"name": "cycles", "value": 1.5}\n'
        '{"name": "cycles2", "value": -2, "unit": null}\n'
    )
    rows, why = indicators.host_rows(text)
    assert why is None
    assert rows == [
        {"name": "src/drafts.py::save", "unit": "commits", "value": 3, "extra": {"band": "high"}},
        {"name": "cycles", "unit": "", "value": 1.5, "extra": {}},
        {"name": "cycles2", "unit": "", "value": -2, "extra": {}},
    ]


@pytest.mark.parametrize(
    ("text", "why"),
    [
        ("", "no rows"),
        ("  \n\n", "no rows"),
        ("7 cycles\n", "line 1 isn't a JSON object"),
        ('{"name": "a", "value": 1}\n[1]\n', "line 2 isn't a JSON object"),
        ('{"value": 1}\n', "line 1 has no name"),
        ('{"name": "", "value": 1}\n', "line 1 has no name"),
        ('{"name": "a\\nb", "value": 1}\n', "line 1 has no name"),
        ('{"name": "' + "n" * 201 + '", "value": 1}\n', "line 1 has no name"),
        ('{"name": "a"}\n', "line 1's value isn't a number"),
        ('{"name": "a", "value": "3"}\n', "line 1's value isn't a number"),
        ('{"name": "a", "value": true}\n', "line 1's value isn't a number"),
        ('{"name": "a", "value": NaN}\n', "line 1's value isn't a number"),
        ('{"name": "a", "value": Infinity}\n', "line 1's value isn't a number"),
        ('{"name": "a", "value": ' + "9" * 400 + "}\n", "line 1's value isn't a number"),
        ('{"name": "a", "value": 1, "unit": 3}\n', "line 1's unit isn't a short string"),
        ('{"name": "a", "value": 1, "unit": "' + "u" * 41 + '"}\n',
         "line 1's unit isn't a short string"),
        ('{"name": "a", "value": 1, "unit": "x"}\n{"name": "a", "value": 2, "unit": "x"}\n',
         "line 2 repeats a, x"),
        ('{"name": "a", "value": 1}\n{"name": "a", "value": 2, "unit": null}\n',
         "line 2 repeats a"),
        # 184 R15: a row that would read back from the report as another key.
        ('{"name": "a", "value": 1, "unit": "—"}\n',
         "line 1's unit is —, which the report reads as none"),
        ('{"name": " a", "value": 1}\n', "line 1's name has stray spaces"),
        ('{"name": "a ", "value": 1}\n', "line 1's name has stray spaces"),
        ('{"name": "a", "value": 1, "unit": "x "}\n', "line 1's unit has stray spaces"),
    ],
)  # fmt: skip
def test_output_that_isnt_rows_passes_through_with_its_reason(text: str, why: str) -> None:
    """R2: anything else is no rows, with a short reason."""
    assert indicators.host_rows(text) == (None, why)


TABLE = """\
## Indicators

`./heat`

| Indicator | Unit | Value | Last retrospective | Change |
|---|---|---|---|---|
| src/drafts.py::save | commits | 3 | — | — |
| a \\| b | — | -1.5 | 2 | −3.5 |

Some prose | with a bar.

| Name | Value |
|---|---|
| other | 9 |
"""


def test_the_last_report_s_rows_are_read_back_by_their_header() -> None:
    """R4: only tables under R5's exact header are read, each cell unescaped; a key twice is
    ambiguous, so None."""
    assert indicators.report_rows(TABLE) == {
        ("src/drafts.py::save", "commits"): 3,
        ("a | b", ""): -1.5,
    }
    twice = TABLE + "\n" + "\n".join(TABLE.splitlines()[4:7]) + "\n"
    assert indicators.report_rows(twice)[("src/drafts.py::save", "commits")] is None
    assert indicators.report_rows("no tables here") == {}


def test_a_cell_escapes_what_a_table_would_split_on() -> None:
    assert indicators.cell("a|b\\c") == "a\\|b\\\\c"
    assert [indicators.number(v) for v in (3, 3.0, 0.25, -2)] == ["3", "3", "0.25", "-2"]
    assert [indicators.signed(v) for v in (3, -2, 0, 0.5, None)] == ["+3", "−2", "0", "+0.5", "—"]


def test_report_rows_reads_any_table_by_its_header_and_key_columns() -> None:
    """184 R7: one parser reads the indicator table and the scorecard's, each by its own header,
    keyed by the columns named and reading the column asked for."""
    head = ("Pillar", "Role", "Figure", "Unit", "Value", "n", "Trend")
    text = (
        "| Pillar | Role | Figure | Unit | Value | n | Trend |\n|---|---|---|---|---|---|---|\n"
        "| Speed | headline | Median lead time, factory | minutes | 76 | 6 | unknown |\n"
        "| Cost | headline | Median dollars | USD | — | 0 | unknown |\n\n" + TABLE
    )
    assert indicators.report_rows(text, head, keys=(0, 2), value=4) == {
        ("Speed", "Median lead time, factory"): 76, ("Cost", "Median dollars"): None,
    }  # fmt: skip
    assert indicators.report_rows(text, head, keys=(0, 2), value=5)[("Cost", "Median dollars")] == 0
    assert indicators.report_rows(text) == indicators.report_rows(TABLE)
