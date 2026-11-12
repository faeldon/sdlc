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

A kind is told by path alone, so no language is assumed: a host whose layout the conventions
misread names its own (`retro.test_paths`, `retro.doc_paths`).
"""

from __future__ import annotations

import itertools
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

Row = tuple[str, int | None, int | None]


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
    lookback: list[list[Row]], now: dict[str, int], skip: Callable[[str], bool], top: int = TOP
) -> list[dict]:
    """The files the most changes touched, ties to the more lines changed. `lines` is the file's
    size on the base branch now, None once it is gone."""
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
        {"file": p, "changes": changes[p], "lines_changed": churn[p], "lines": now.get(p)}
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
