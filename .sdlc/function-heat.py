# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""This repo's function-level hotspots for `/sdlc:retro`'s architecture pass.

Named in `.sdlc/config.toml` under `retro.indicators`, so only `sdlc.py retro` in this repo runs
it: a host's cached copy of the plugin carries the file, but no host's config names it. For each
top-level function in the four scripts below, it counts the commits since the last retrospective
that rewrote some of its lines and gives its size, ranked by commits then size, and prints the top
of each file as a plain-text table.

"Since the last retrospective" is the newest `Retrospective YYYY-MM-DD` commit on the base
branch's first-parent line, the boundary `sdlc.py retro` reads (`retrospectives()`); with none,
the whole history. A commit counts when `git blame` still gives it some of a function's lines, so
one whose lines a later commit rewrote again is not counted. Everything is read as of the base
branch (`[git] base`, else `main`, else the branch `origin/HEAD` names), so any checkout gives the
same answer, and nothing is written. It prints function names and numbers only.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path

FILES = [
    "scripts/sdlc.py",
    "scripts/closing.py",
    "plugins/factory/scripts/factory.py",
    "plugins/factory/scripts/landing.py",
]
TOP = 15
DEFAULT_BASE = "main"
RETRO_RE = re.compile(r"^Retrospective (\d{4}-\d{2}-\d{2})$")
# A `--line-porcelain` header: the commit, its line in that commit, and the line in the file.
HEADER_RE = re.compile(r"^([0-9a-f]{40}) \d+ (\d+)")


def _git(root: Path, *args: str) -> str | None:
    """stdout of a git command run in `root`, or None when it fails."""
    try:
        ran = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8",
            errors="replace", check=True,
        )  # fmt: skip
    except (subprocess.CalledProcessError, OSError):
        return None
    return ran.stdout


def base_branch(root: Path) -> str | None:
    """`[git] base` from the checkout's config, else `main` when it exists, else the local branch
    `origin/HEAD` names: `_resolve_trunk()`'s order."""
    config = root / ".sdlc" / "config.toml"
    if config.is_file():
        try:
            given = tomllib.loads(config.read_text(encoding="utf-8")).get("git", {}).get("base")
        except tomllib.TOMLDecodeError:
            given = None
        if given:
            return given
    if _git(root, "rev-parse", "--verify", "-q", f"refs/heads/{DEFAULT_BASE}") is not None:
        return DEFAULT_BASE
    remote = (_git(root, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD") or "").strip()
    name = remote.removeprefix("origin/")
    named = remote.startswith("origin/") and name
    if named and _git(root, "rev-parse", "--verify", "-q", f"refs/heads/{name}") is not None:
        return name
    return None


def last_retrospective(root: Path, base: str) -> dict | None:
    """The newest `Retrospective YYYY-MM-DD` commit on the base branch's first-parent line."""
    log = _git(root, "log", "--first-parent", "--format=%h%x00%s", base) or ""
    for line in log.splitlines():
        sha, _, subject = line.partition("\x00")
        m = RETRO_RE.match(subject)
        if m:
            return {"sha": sha, "date": m.group(1)}
    return None


def functions(source: str) -> list[tuple[str, int, int]]:
    """Each module-level function, sync or async, with its first and last line, in file order.
    Methods and nested functions belong to what holds them."""
    tree = ast.parse(source)
    return [
        (node.name, node.lineno, node.end_lineno or node.lineno)
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def blamed(porcelain: str) -> dict[int, str]:
    """Each line's commit from `git blame --line-porcelain`, leaving out the lines blame stopped
    at the boundary, which no commit in the range wrote."""
    by_line: dict[int, str] = {}
    sha, line, boundary = None, 0, False
    for row in porcelain.splitlines():
        m = HEADER_RE.match(row)
        if m and sha is None:
            sha, line, boundary = m.group(1), int(m.group(2)), False
        elif row == "boundary":
            boundary = True
        elif row.startswith("\t") and sha is not None:
            if not boundary:
                by_line[line] = sha
            sha = None
    return by_line


def heat(root: Path, base: str, files: list[str]) -> dict[str, list[dict]]:
    """Each file's functions as of `base`, with the commits since the last retrospective that
    blame gives some of its lines to, and its size in lines. A file missing on `base` has none."""
    since = last_retrospective(root, base)
    span = f"{since['sha']}..{base}" if since else base
    out: dict[str, list[dict]] = {}
    for path in files:
        source = _git(root, "show", f"{base}:{path}")
        # A file added after `since` has no boundary lines, `--root` or not: every line is blamed
        # in the range, and the commit that added the whole file counts as one, as it should.
        porcelain = _git(root, "blame", "--root", "--line-porcelain", span, "--", path)
        if source is None or porcelain is None:
            out[path] = []
            continue
        lines = blamed(porcelain)
        out[path] = [
            {
                "name": name,
                "commits": len({lines[n] for n in range(start, end + 1) if n in lines}),
                "lines": end - start + 1,
            }
            for name, start, end in functions(source)
        ]
    return out


def rank(rows: list[dict], top: int = TOP) -> list[dict]:
    """Most commits first, the larger function first among equals, cut to `top`."""
    return sorted(rows, key=lambda r: (-r["commits"], -r["lines"], r["name"]))[:top]


def render(by_file: dict[str, list[dict]], since: dict | None) -> str:
    when = f"since the retrospective at {since['sha']} ({since['date']})" if since else "ever"
    out = [f"Function hotspots: commits that rewrote some of each top-level function {when}."]
    for path, rows in by_file.items():
        out += ["", path]
        if not rows:
            out.append("  (no functions read)")
            continue
        out.append(f"  {'commits':>7}  {'lines':>5}  function")
        out += [f"  {r['commits']:>7}  {r['lines']:>5}  {r['name']}" for r in rank(rows)]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    root = Path.cwd()
    base = base_branch(root)
    if base is None:
        print("function-heat: no base branch found", file=sys.stderr)
        return 1
    files = argv or FILES
    print(render(heat(root, base, files), last_retrospective(root, base)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
