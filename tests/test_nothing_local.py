"""Nothing in this repo names a project, a change by its number, or the machine it was written
on.

The plugin is meant for any host, so a project's name in a comment, docstring or doc couples it to
that one project, and a change cited by its folder number points at history the reader may not
have. The author's own workspace slips in the same way: a clone's path in a command,
`/Users/<name>/...` in an artifact. This scans every doc, script and test for those, and planted
text proves the scan can fail.

The patterns here describe a shape and name nothing, because a name listed here would be the one
mention left in the repo. Specific terms go one regex per line in `.sdlc/terms.local`, which
is gitignored: read when it exists, never scanned, never committed.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A change cited by its folder number with no slug, `work/046`, is how a project's history gets
# quoted; `work/001-x` is an example path and stays fine. A home directory path says how the
# author's machine is laid out; `~/.claude/` is Claude Code's own and stays fine, as do
# placeholders like `/Users/<name>/`.
PATTERNS = [
    r"\bwork/\d{3,}\b(?!-)",
    r"/Users/[\w.-]+/",
    r"/home/[\w.-]+/",
    r"~/[\w-]+/",
]
LOCAL = Path(".sdlc", "terms.local")
SUFFIXES = {".md", ".py", ".json", ".toml", ".sh"}
SKIP_DIRS = {".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__"}
# A change's worktree is a second copy of the repo: scanned from the main checkout, it would report
# every line twice, and a change's work in progress as though it had landed.
WORKTREES = (".claude", "worktrees")


def main_checkout() -> Path:
    """The main checkout, which holds the local file: it's gitignored, so a change's worktree,
    where the change is written, has no copy of its own."""
    try:
        common = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ROOT
    return Path(common).parent


def local_patterns(path: Path) -> list[str]:
    """The local file's patterns, one per line, skipping blank lines and `#` comments; none when
    the file is missing, as on a fresh clone."""
    if not path.is_file():
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def scanned(root: Path) -> list[Path]:
    """Every file the scan reads: docs, scripts, tests and the committed work/, but not this one
    or the local file, which hold the patterns, and not the change worktrees."""
    return [
        p
        for p in sorted(root.rglob("*"))
        if p.is_file()
        and p.suffix in SUFFIXES
        and not SKIP_DIRS & set(p.relative_to(root).parts)
        and p.relative_to(root).parts[:2] != WORKTREES
        and p.relative_to(root) != LOCAL
        and p.name != Path(__file__).name
    ]


def forbidden(root: Path, local: Path | None = None) -> list[str]:
    """Every line that matches a pattern, as `path:line: text`. The line is reported, never the
    pattern it matched."""
    pattern = re.compile("|".join(PATTERNS + local_patterns(local or root / LOCAL)), re.IGNORECASE)
    found = []
    for path in scanned(root):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                found.append(f"{path.relative_to(root)}:{n}: {line.strip()}")
    return found


def test_the_scan_reads_the_plugin() -> None:
    """A walk over nothing finds nothing, and would pass."""
    names = {p.relative_to(ROOT).as_posix() for p in scanned(ROOT)}
    assert {"scripts/sdlc.py", "skills/ship/SKILL.md", "defaults/SDLC.md", "README.md"} <= names


def test_nothing_in_the_repo_is_forbidden() -> None:
    assert forbidden(ROOT, main_checkout() / LOCAL) == []


def test_a_citation_in_a_change_worktree_is_not_read_but_one_in_work_is(tmp_path: Path) -> None:
    copy = tmp_path / ".claude" / "worktrees" / "001-x" / "README.md"
    copy.parent.mkdir(parents=True)
    copy.write_text("Moved here by work/046.\n", encoding="utf-8")
    (tmp_path / "work" / "001-x").mkdir(parents=True)
    (tmp_path / "work" / "001-x" / "intent.md").write_text("See work/046.\n", encoding="utf-8")
    assert forbidden(tmp_path) == ["work/001-x/intent.md:1: See work/046."]


def test_a_planted_citation_is_caught(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Moved here by work/046.\nSee work/001-x/.\n")
    assert forbidden(tmp_path) == ["README.md:1: Moved here by work/046."]


def test_a_planted_home_path_is_caught_but_not_claude_s_own(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "Cloned to /Users/someone/code/x.\n"
        "Cloned to /home/someone/code/x.\n"
        "Cloned to ~/code/x.\n"
        "The cache is ~/.claude/plugins/cache/.\n"
        "Say /Users/<name>/ for the reader's own.\n"
    )
    assert forbidden(tmp_path) == [
        "README.md:1: Cloned to /Users/someone/code/x.",
        "README.md:2: Cloned to /home/someone/code/x.",
        "README.md:3: Cloned to ~/code/x.",
    ]


def test_a_term_in_the_local_file_is_caught_and_the_file_is_not_read(tmp_path: Path) -> None:
    (tmp_path / LOCAL).parent.mkdir()
    (tmp_path / LOCAL).write_text("# terms kept out of the repo\n\n\\breopen drafts\\b\n")
    (tmp_path / "README.md").write_text("It began with reopen drafts.\nIt began.\n")
    assert forbidden(tmp_path) == ["README.md:1: It began with reopen drafts."]


def test_without_the_local_file_only_the_shapes_apply(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("It began with reopen drafts.\nCloned to ~/code/x.\n")
    assert local_patterns(tmp_path / LOCAL) == []
    assert forbidden(tmp_path) == ["README.md:2: Cloned to ~/code/x."]
