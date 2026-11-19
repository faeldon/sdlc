"""What the retrospective's architecture pass reads: where changes land, what they touch together,
and what grows, counted from git's own output for any repo.

Loaded by path from `sdlc.py`, like `metrics.py`: `uv run --script` and the tests put different
directories on sys.path. Pure functions only, no subprocess and no import of `sdlc.py`: the script
runs git and hands the text here.

    classify(path, is_tests, is_docs)         -> "tests" | "docs" | "code"
    numstat_rows(text)                        -> [(path, added, deleted)]   `git diff --numstat`
    change_size(rows, kind)                   -> {added, deleted, by_kind}
    size_by_tier(changes)                     -> {tier: medians}
    grep_counts(text, ref)                    -> {path: lines}              `git grep -I -c ''`
    hotspots(lookback, now, skip)             -> [row]
    co_change(lookback, skip)                 -> [row]
    largest(now, then, skip)                  -> [row]
    totals(counts, kind, skip)                -> {kind: {files, lines}}
    removed_ranges(text)                      -> {path: [(start, count)]}   `git diff -U0`
    blame_commits(text)                       -> [sha]                      `git blame --porcelain`
    comment_lines(text, include)              -> {added, comment_lines, unknown_lines}  `-U0`
    spend(rows)                               -> {tiers, outliers, tools, recorded, unrecorded}
    junit_times(text)                         -> {cases, error}             a JUnit XML report
    drifted_tests(lookback, kind, skip, present) -> [row]
    host_rows(output)                         -> (rows, None) | (None, reason)  `retro.indicators`
    report_rows(text)                         -> {(name, unit): value | None}   a report's tables
    cell(text), number(value), signed(change) -> str                            a table's cells

A kind is told by path alone, so no language is assumed: a host whose layout the conventions
misread names its own (`retro.test_paths`, `retro.doc_paths`).

A comment is told by line alone, the same for every host: an added line whose stripped text starts
with its file's line-comment marker (`COMMENT_MARKERS`, by suffix). No parser: a docstring or block
comment is code here, and a line inside a string that starts with the marker is a comment. Prose
(`PROSE_SUFFIXES`) is never counted, and a suffix with no marker is counted as `unknown_lines`,
never guessed at.
"""

from __future__ import annotations

import itertools
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Callable
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from statistics import median

KINDS = ("code", "tests", "docs")
# The conventions: a path is tests when a directory in it, or its name, says so; docs when its
# suffix or a directory does; code otherwise.
TEST_DIRS = frozenset({"test", "tests", "spec", "__tests__"})
TEST_NAMES = ("test_*", "*_test.*", "*.test.*", "*.spec.*")
DOC_DIRS = frozenset({"docs"})
DOC_SUFFIXES = (".md", ".rst", ".adoc", ".txt")
# How many rows each list keeps, and how many changes must share a pair before it is coupling.
TOP = 10
PAIR_LEAST = 3
# A change touching more files than this (a mass rename, a reformat) is left out of the pairs: it
# would couple everything to everything, and its pairs grow with the square of its size.
PAIR_FILES_MAX = 50
# How many later changes must touch a test's code, without the test, before the test is drifted.
DRIFT_LEAST = 3
# How many of a drifted test's code files its row names.
DRIFT_CODE_MAX = 5

Row = tuple[str, int | None, int | None]

# Each suffix's line-comment marker, for `comment_lines()`.
COMMENT_MARKERS = {
    **dict.fromkeys((".py", ".sh", ".toml", ".yaml", ".yml", ".rb"), "#"),
    **dict.fromkeys(
        (".js", ".ts", ".go", ".rs", ".java", ".c", ".h", ".cpp", ".swift", ".kt"), "//"
    ),
    **dict.fromkeys((".sql", ".lua"), "--"),
    ".html": "<!--",
}
# Prose, whose lines are never comments, nor code a comment could sit in.
PROSE_SUFFIXES = (*DOC_SUFFIXES, ".markdown")
# Fewer changes than this in a tier with a measure, and the tier gives no median for it.
SPEND_LEAST = 3
# How far over its tier's median a change is named.
SPEND_OVER = 2
SPEND_MEASURES = ("comment_share", "out_per_line", "tools_per_line")


def is_test(path: str) -> bool:
    p = PurePosixPath(path)
    return any(d in TEST_DIRS for d in p.parts[:-1]) or any(
        fnmatchcase(p.name, pat) for pat in TEST_NAMES
    )


def is_doc(path: str) -> bool:
    p = PurePosixPath(path)
    return p.suffix.lower() in DOC_SUFFIXES or any(d in DOC_DIRS for d in p.parts[:-1])


def classify(
    path: str, is_tests: Callable[[str], bool] = is_test, is_docs: Callable[[str], bool] = is_doc
) -> str:
    """A path's kind, tests checked first: `docs/test_guide.md` is a test's."""
    if is_tests(path):
        return "tests"
    if is_docs(path):
        return "docs"
    return "code"


def numstat_rows(text: str) -> list[Row]:
    """`git diff --numstat` as rows; a binary file's counts (`-`) are None."""
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added, deleted, path = parts
            rows.append(
                (path, int(added) if added.isdigit() else None,
                 int(deleted) if deleted.isdigit() else None)
            )  # fmt: skip
    return rows


def _unquote(path: str) -> str:
    """A path as git prints it in a diff header, C-quoted when it holds anything unusual, back to
    the path itself: what `git blame` is handed."""
    if not (path.startswith('"') and path.endswith('"')):
        return path
    raw = path[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape")
    return raw.encode("latin-1").decode("utf-8", "replace")


def removed_ranges(text: str) -> dict[str, list[tuple[int, int]]]:
    """The old side of `git diff -U0`: each file's runs of lines the diff removed or replaced, as
    (first line, count). A run that only adds lines removes none, so appending is never here, and a
    file the diff creates has no old side. A file's header runs from its `diff --git` line to its
    first `@@`: past that, a removed line reading `-- x` prints as `--- x`, and is no header."""
    out: dict[str, list[tuple[int, int]]] = {}
    path = None
    header = False
    for line in text.splitlines():
        if line.startswith("diff --git "):
            header, path = True, None
        elif header and line.startswith("--- "):
            name = _unquote(line[4:])
            path = None if name == "/dev/null" else name.removeprefix("a/")
        elif line.startswith("@@ "):
            header = False
            if not path:
                continue
            old = line.split()[1].removeprefix("-")
            start, _, count = old.partition(",")
            n = int(count) if count else 1
            if n > 0:
                out.setdefault(path, []).append((int(start), n))
    return out


def blame_commits(text: str) -> list[str]:
    """The commit each line came from, in order, from `git blame --porcelain`: every line's group
    opens with its sha (40 hex, or 64 in a SHA-256 repo) and line numbers."""
    shas = []
    for line in text.splitlines():
        head = line.split(" ", 1)[0]
        if len(head) in (40, 64) and all(c in "0123456789abcdef" for c in head) and " " in line:
            shas.append(head)
    return shas


def change_size(rows: list[Row], kind: Callable[[str], str]) -> dict:
    """A change's lines added and deleted, overall and by kind, with the files of each kind."""
    by_kind = {k: {"files": 0, "added": 0, "deleted": 0} for k in KINDS}
    for path, added, deleted in rows:
        k = by_kind[kind(path)]
        k["files"] += 1
        k["added"] += added or 0
        k["deleted"] += deleted or 0
    return {
        "added": sum(k["added"] for k in by_kind.values()),
        "deleted": sum(k["deleted"] for k in by_kind.values()),
        "by_kind": by_kind,
    }


def size_by_tier(changes: list[dict]) -> dict:
    """Per tier, the changes sized and the median of each count, overall and by kind. A change with
    no size (`added` None) is left out of the medians, not counted as zero."""
    tiers: dict[str, list[dict]] = {}
    for c in changes:
        if c.get("added") is not None:
            tiers.setdefault(str(c.get("tier")), []).append(c)
    out = {}
    for tier, rows in sorted(tiers.items()):
        out[tier] = {
            "changes": len(rows),
            "added": median(r["added"] for r in rows),
            "deleted": median(r["deleted"] for r in rows),
            "files": median(sum(k["files"] for k in r["by_kind"].values()) for r in rows),
            "by_kind": {
                k: {
                    f: median(r["by_kind"][k][f] for r in rows)
                    for f in ("files", "added", "deleted")
                }
                for k in KINDS
            },
        }
    return out


def grep_counts(text: str, ref: str) -> dict[str, int]:
    """`git grep -I -c '' <ref>`, each line `<ref>:<path>:<lines>`, as lines per path. Binary files
    are already left out by `-I`; an empty file has no line here."""
    counts = {}
    prefix = f"{ref}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            path, _, n = line[len(prefix) :].rpartition(":")
            if path and n.isdigit():
                counts[path] = int(n)
    return counts


def _files(rows: list[Row], skip: Callable[[str], bool]) -> set[str]:
    return {path for path, _, _ in rows if not skip(path)}


def hotspots(
    lookback: list[list[Row]],
    now: dict[str, int],
    skip: Callable[[str], bool],
    top: int = TOP,
    present: set[str] | None = None,
) -> list[dict]:
    """The files the most changes touched, ties to the more lines changed. `lines` is the file's
    size on the base branch now, None when it has none to count: a binary or empty file, or one
    that is gone. `gone` says which, from `present` (every path on the base branch), and is None
    without it."""
    changes: Counter = Counter()
    churn: Counter = Counter()
    for rows in lookback:
        for path in _files(rows, skip):
            changes[path] += 1
        for path, added, deleted in rows:
            if not skip(path):
                churn[path] += (added or 0) + (deleted or 0)
    ranked = sorted(changes, key=lambda p: (-changes[p], -churn[p], p))[:top]
    return [
        {
            "file": p,
            "changes": changes[p],
            "lines_changed": churn[p],
            "lines": now.get(p),
            "gone": None if present is None else p not in present,
        }
        for p in ranked
    ]


def co_change(
    lookback: list[list[Row]],
    skip: Callable[[str], bool],
    least: int = PAIR_LEAST,
    top: int = TOP,
) -> list[dict]:
    """Pairs of files `least` or more changes touched together, the most first, then the pair whose
    rarer file nearly always brings the other. Empty when no pair reaches `least`."""
    alone: Counter = Counter()
    together: Counter = Counter()
    for rows in lookback:
        files = _files(rows, skip)
        alone.update(files)
        if len(files) <= PAIR_FILES_MAX:
            together.update(itertools.combinations(sorted(files), 2))
    pairs = [p for p, n in together.items() if n >= least]
    pairs.sort(key=lambda p: (-together[p], -together[p] / min(alone[p[0]], alone[p[1]]), p))
    return [
        {"files": list(p), "together": together[p], "changes": [alone[p[0]], alone[p[1]]]}
        for p in pairs[:top]
    ]


def largest(
    now: dict[str, int],
    then: dict[str, int] | None,
    skip: Callable[[str], bool],
    top: int = TOP,
) -> list[dict]:
    """The largest files by lines, each with its lines at `then` and how much it grew; both None
    when there is no `then` or the file wasn't there."""
    ranked = sorted((p for p in now if not skip(p)), key=lambda p: (-now[p], p))[:top]
    rows = []
    for p in ranked:
        before = then.get(p) if then is not None else None
        rows.append(
            {"file": p, "lines": now[p], "then": before,
             "growth": None if before is None else now[p] - before}
        )  # fmt: skip
    return rows


def totals(counts: dict[str, int], kind: Callable[[str], str], skip: Callable[[str], bool]) -> dict:
    """Files and lines of each kind."""
    out = {k: {"files": 0, "lines": 0} for k in KINDS}
    for path, n in counts.items():
        if not skip(path):
            k = out[kind(path)]
            k["files"] += 1
            k["lines"] += n
    return out


def comment_lines(text: str, include: Callable[[str], bool] | None = None) -> dict:
    """The added lines of `git diff -U0` in files a marker can be read in (`added`), those that are
    line comments (`comment_lines`), and the added lines of files whose suffix has no marker
    (`unknown_lines`). Prose is in none. `include`, when given, keeps only the paths it says."""
    out = {"added": 0, "comment_lines": 0, "unknown_lines": 0}
    path: str | None = None
    header = False
    for line in text.splitlines():
        if line.startswith("diff --git "):
            header, path = True, None
        elif header and line.startswith("+++ "):
            name = _unquote(line[4:])
            path = None if name == "/dev/null" else name.removeprefix("b/")
        elif line.startswith("@@ "):
            header = False
        elif not header and path and line.startswith("+"):
            suffix = PurePosixPath(path).suffix.lower()
            if suffix in PROSE_SUFFIXES or (include is not None and not include(path)):
                continue
            marker = COMMENT_MARKERS.get(suffix)
            if marker is None:
                out["unknown_lines"] += 1
                continue
            out["added"] += 1
            out["comment_lines"] += 1 if line[1:].strip().startswith(marker) else 0
    return out


def _measures(row: dict) -> dict:
    """A change's three spend measures, None where a count is missing or it added no code."""
    code = row.get("code_added")
    base = row.get("comment_base", code)
    per_line = lambda n: n / code if isinstance(n, int) and code else None  # noqa: E731
    comments = row.get("comment_lines")
    return {
        "comment_share": comments / base if isinstance(comments, int) and base else None,
        "out_per_line": per_line(row.get("out")),
        "tools_per_line": per_line(row.get("tools")),
    }


def spend(rows: list[dict]) -> dict:
    """What each change spent beside its size. `rows` are the window's changes, each with `change`,
    `tier`, `code_added`, `comment_lines` (and `comment_base`, the lines a marker could be read
    in, when it isn't `code_added`), `out`, `tools` and `by_tool` (`{name: {calls, errors}}`), and
    `recorded`. Per tier, the median of each measure over the changes that have it, None under
    `SPEND_LEAST`; each change more than `SPEND_OVER` times its tier's median on any measure; and
    across the recorded changes, the tools most called and with the most errors. A missing count
    is left out of a median, never read as zero."""
    measured = [(r, _measures(r)) for r in rows]
    tiers: dict[str, dict] = {}
    for tier in sorted({str(r["tier"]) for r in rows}):
        mine = [m for r, m in measured if str(r["tier"]) == tier]
        row: dict = {"changes": len(mine)}
        for k in SPEND_MEASURES:
            values = [m[k] for m in mine if m[k] is not None]
            row[k] = round(median(values), 3) if len(values) >= SPEND_LEAST else None
        tiers[tier] = row
    outliers = []
    for r, m in measured:
        for k in SPEND_MEASURES:
            mid = tiers[str(r["tier"])][k]
            if m[k] is not None and mid and m[k] > SPEND_OVER * mid:
                outliers.append(
                    {"change": r["change"], "tier": r["tier"], "measure": k,
                     "value": round(m[k], 3), "median": mid, "times": round(m[k] / mid, 1)}
                )  # fmt: skip
    names: dict[str, dict] = {}
    for r in rows:
        if not r.get("recorded"):
            continue
        for name, t in (r.get("by_tool") or {}).items():
            row = names.setdefault(name, {"name": name, "calls": 0, "errors": 0, "changes": 0})
            row["calls"] += t.get("calls") or 0
            row["errors"] += t.get("errors") or 0
            row["changes"] += 1
    for row in names.values():
        row["error_share"] = round(row["errors"] / row["calls"], 2) if row["calls"] else None
    ranked = [
        {k: row[k] for k in ("name", "calls", "errors", "error_share", "changes")}
        for row in names.values()
    ]
    recorded = sum(1 for r in rows if r.get("recorded"))
    return {
        "recorded": recorded,
        "unrecorded": len(rows) - recorded,
        "tiers": tiers,
        "outliers": outliers,
        "tools": {
            "most_called": sorted(ranked, key=lambda t: (-t["calls"], t["name"]))[:TOP],
            "most_errors": sorted(
                (t for t in ranked if t["errors"]),
                key=lambda t: (-t["errors"], -(t["error_share"] or 0), t["name"]),
            )[:TOP],
        },
    }


def _seconds(value: str | None) -> float | None:
    """A `time` attribute as seconds: None when missing, not a number, or not above 0, since a
    runner that didn't time a case may write 0."""
    try:
        seconds = float(value) if value is not None else None
    except ValueError:
        return None
    return seconds if seconds is not None and math.isfinite(seconds) and seconds > 0 else None


def junit_times(text: str) -> dict:
    """Every `<testcase>` of a JUnit XML report, at any depth, with its id (`classname::name`, or
    `file::name` without a classname), `file`, `seconds` and whether it was `skipped`. Text that
    isn't XML, or holds no test case, is an `error`, never a raise."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return {"cases": [], "error": f"not JUnit XML: {e}"}
    cases = []
    for case in root.iter("testcase"):
        name = case.get("name") or ""
        owner = case.get("classname") or case.get("file")
        cases.append(
            {
                "test": f"{owner}::{name}" if owner else name,
                "file": case.get("file"),
                "seconds": _seconds(case.get("time")),
                "skipped": case.find("skipped") is not None,
            }
        )
    if not cases:
        return {"cases": [], "error": "no <testcase> in the report"}
    return {"cases": cases, "error": None}


def drifted_tests(
    lookback: list[tuple[str, list[Row]]],
    kind: Callable[[str], str],
    skip: Callable[[str], bool],
    present: set[str] | None,
    top: int = TOP,
) -> list[dict]:
    """The tests whose code moved without them. `lookback` is `[(change, rows)]`, oldest first; a
    change of more than `PAIR_FILES_MAX` files is left out, as in `co_change()`. For each test
    file still in `present` (every path when None), its code is the code files its last change
    touched, and `later` the changes after that touching any of them: drifted at `DRIFT_LEAST`,
    with the code touched since (at most `DRIFT_CODE_MAX`), the most `later` first."""
    changes = []
    for name, rows in lookback:
        files = _files(rows, skip)
        if len(files) <= PAIR_FILES_MAX:
            changes.append((name, files))
    last: dict[str, int] = {}
    for i, (_, files) in enumerate(changes):
        for path in files:
            if kind(path) == "tests" and (present is None or path in present):
                last[path] = i
    rows = []
    for test, i in last.items():
        code = {p for p in changes[i][1] if kind(p) == "code"}
        since = [files & code for _, files in changes[i + 1 :]]
        later = sum(1 for moved in since if moved)
        if later >= DRIFT_LEAST:
            moved = sorted(set().union(*since))[:DRIFT_CODE_MAX]
            rows.append({"file": test, "last_change": changes[i][0], "code": moved, "later": later})
    rows.sort(key=lambda r: (-r["later"], r["file"]))
    return rows[:top]


# ---------------------------------------------------------------- the host's indicator rows

# The table a report shows a host's indicator rows under, and reads back by: its header line.
INDICATOR_HEAD = ("Indicator", "Unit", "Value", "Last retrospective", "Change")
HEADER = "| " + " | ".join(INDICATOR_HEAD) + " |"
# The longest `name` and `unit` a row may carry.
NAME_MAX = 200
UNIT_MAX = 40


def _finite(value: float) -> bool:
    """A finite number, as a float can hold it: an integer too large for one is not."""
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _one_line(value: object, most: int) -> bool:
    return isinstance(value, str) and "\n" not in value and "\r" not in value and len(value) <= most


def host_rows(output: str) -> tuple[list[dict] | None, str | None]:
    """An indicator command's stdout as rows, `(rows, None)`, when every non-blank line is a JSON
    object with a `name` (a non-empty string on one line, at most `NAME_MAX`), a `value` (a finite
    number, never a boolean) and maybe a `unit` (a string on one line, at most `UNIT_MAX`, or null),
    no `(name, unit)` twice; other keys are kept as `extra`. Anything else is `(None, reason)`."""
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    lines = [(n, line) for n, line in enumerate(output.splitlines(), 1) if line.strip()]
    if not lines:
        return None, "no rows"
    for n, line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            obj = None
        if not isinstance(obj, dict):
            return None, f"line {n} isn't a JSON object"
        name, value, unit = obj.get("name"), obj.get("value"), obj.get("unit")
        if not _one_line(name, NAME_MAX) or not name:
            return None, f"line {n} has no name"
        is_number = isinstance(value, int | float) and type(value) is not bool
        if not is_number or not _finite(value):
            return None, f"line {n}'s value isn't a number"
        if unit is not None and not _one_line(unit, UNIT_MAX):
            return None, f"line {n}'s unit isn't a short string"
        key = (name, unit or "")
        if key in seen:
            return None, f"line {n} repeats " + ", ".join(k for k in key if k)
        seen.add(key)
        extra = {k: v for k, v in obj.items() if k not in ("name", "value", "unit")}
        rows.append({"name": name, "unit": key[1], "value": value, "extra": extra})
    return rows, None


def cell(text: str) -> str:
    """Text as a table cell: `\\` and `|` escaped, so the row splits where the table does."""
    return text.replace("\\", "\\\\").replace("|", "\\|")


def number(value: float) -> str:
    """A value as the report writes it: an integral float without its `.0`."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def signed(change: float | None) -> str:
    """A change as `+3`, `−2` (a minus sign) or `0`; `—` for none."""
    if change is None:
        return "—"
    if change > 0:
        return "+" + number(change)
    if change < 0:
        return "−" + number(-change)
    return "0"


def _cells(line: str) -> list[str]:
    """A table row's cells, split on the `|` no backslash escapes, each unescaped and stripped."""
    out, cur, chars = [], [], iter(line.strip().removeprefix("|"))
    for ch in chars:
        if ch == "\\":
            cur.append(next(chars, ""))
        elif ch == "|":
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return out


def _parsed(text: str) -> float | None:
    for kind in (int, float):
        try:
            value = kind(text)
        except ValueError:
            continue
        return value if _finite(value) else None
    return None


def report_rows(text: str) -> dict[tuple[str, str], float | None]:
    """Each `(name, unit)` a report's indicator tables show (those under `HEADER` exactly), with
    its value; a key shown twice, or a value that doesn't read, is None. A unit of `—` is ""."""
    found: dict[tuple[str, str], float | None] = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() != HEADER:
            continue
        for row in itertools.takewhile(lambda r: r.lstrip().startswith("|"), lines[i + 2 :]):
            cells = _cells(row)
            if len(cells) != len(INDICATOR_HEAD):
                continue
            key = (cells[0], "" if cells[1] == "—" else cells[1])
            found[key] = None if key in found else _parsed(cells[2])
    return found
