"""A conflict with the base branch, resolved inside ship and landed.

074's shape, through `uv run --script` as the skills run it: a change whose uncommitted work, its
own untracked folder included, edits two files the base branch also changed, one of them the
register. `base` refuses it as resolvable, `resolve` stops on both files, the merge is scripted
here as the agent would write it, and the change ships and closes with the resolution recorded
and its refs gone.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sdlc.py"
GIT_ID = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}

pytestmark = [
    pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do"),
    pytest.mark.portable,
]

INBOX = """# Inbox

> Every change request, one entry each.

## [2026-11-01-1] [idea] The first idea

Kept by both sides.
"""


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | GIT_ID
    return subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SCRIPT), *args],
        cwd=cwd, capture_output=True, encoding="utf-8", env=env,
    )  # fmt: skip


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True, encoding="utf-8", check=True, env=os.environ | GIT_ID,
    )  # fmt: skip
    return out.stdout.strip()


def _json(done: subprocess.CompletedProcess) -> dict:
    assert done.stdout, done.stderr
    return json.loads(done.stdout)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_a_conflict_with_the_base_is_resolved_shipped_and_closed(tmp_path: Path) -> None:
    root = tmp_path / "host"
    _write(root / "README.md", "one\ntwo\nthree\n")
    _write(root / ".gitignore", ".claude/worktrees/\n")
    _write(root / ".sdlc" / "work" / "inbox.md", INBOX)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")

    made = _run(root, "new", "thing", "--tier", "1", "--worktree")
    assert made.returncode == 0, made.stdout + made.stderr
    tree = root / ".claude" / "worktrees" / "001-thing"
    folder = tree / ".sdlc" / "work" / "001-thing"
    intent = folder / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8").replace("impact:\n", "impact: none\n"),
                      encoding="utf-8")  # fmt: skip
    _write(tree / "README.md", "one, as the change says\ntwo\nthree\n")
    _write(tree / ".sdlc" / "work" / "inbox.md",
           INBOX + "\n## [2026-11-02-1] [idea] The change's idea\n\nOurs.\n")  # fmt: skip

    _write(root / "README.md", "one, as main says\ntwo\nthree\n")
    _write(root / ".sdlc" / "work" / "inbox.md",
           INBOX + "\n## [2026-11-02-2] [idea] Main's idea\n\nTheirs.\n")  # fmt: skip
    _git(root, "commit", "-q", "-am", "main moves")

    based = _run(tree, "base", "001")
    assert based.returncode == 1 and _json(based)["resolvable"] is True, based.stdout

    started = _json(_run(tree, "resolve", "001"))
    assert started["state"] == "conflict", started
    assert set(started["conflicted"]) == {"README.md", ".sdlc/work/inbox.md"}
    assert _git(tree, "rev-parse", "--verify", "refs/sdlc/aside/001-thing")

    _write(tree / "README.md", "one, as main says and as the change says\ntwo\nthree\n")
    _write(tree / ".sdlc" / "work" / "inbox.md",
           INBOX + "\n## [2026-11-02-2] [idea] Main's idea\n\nTheirs.\n"
           "\n## [2026-11-02-1] [idea] The change's idea\n\nOurs, quoting a marker: "
           + "<" * 7 + " mid-line.\n")  # fmt: skip
    done = _json(_run(tree, "resolve", "001", "--continue"))
    assert done["state"] == "clean", done
    assert set(done["resolved"]) == {"README.md", ".sdlc/work/inbox.md"}
    assert _git(tree, "rev-parse", "HEAD") == _git(root, "rev-parse", "main"), "nothing committed"
    assert intent.is_file() and "?? .sdlc/work/001-thing/" in _git(tree, "status", "--porcelain")
    record = (folder / "conflicts.md").read_text(encoding="utf-8")
    assert "- README.md" in record and "- .sdlc/work/inbox.md" in record

    asked = _run(tree, "preflight", "001", "--question")
    assert "with the conflicts in" in asked.stdout and "README.md" in asked.stdout, asked.stderr

    shipped = _run(tree, "ship", "001")
    assert shipped.returncode == 0, shipped.stdout + shipped.stderr
    _git(tree, "commit", "-q", "-m", "ship 001")
    closed = _run(root, "close", "001")
    assert closed.returncode == 0, closed.stdout + closed.stderr
    assert (root / "README.md").read_text(encoding="utf-8").startswith("one, as main says and as")
    register = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert "Main's idea" in register and "The change's idea" in register
    refs = _git(root, "for-each-ref", "--format=%(refname)", "refs/sdlc/")
    assert "001-thing" not in refs, refs


def test_an_inbox_commit_on_the_base_never_stops_an_open_change_s_rebase(tmp_path: Path) -> None:
    """100 R2: intent edits no register, so an entry filed on the base branch while a change is
    open, right after the change's own seed, brings the change up to date with no conflict. The
    control is the tag edit intent used to make, which stops `base` on that same commit."""
    root = tmp_path / "host"
    seed = "\n## [2026-11-02-1] [idea] The change's seed\n\nWhy it's worth doing.\n"
    _write(root / ".gitignore", ".claude/worktrees/\n")
    _write(root / ".sdlc" / "work" / "inbox.md", INBOX + seed)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")

    trees = {}
    for n, slug in (("001", "seeded"), ("002", "tagged")):
        made = _run(root, "new", slug, "--tier", "1", "--worktree")
        assert made.returncode == 0, made.stdout + made.stderr
        tree = root / ".claude" / "worktrees" / f"{n}-{slug}"
        intent = tree / ".sdlc" / "work" / f"{n}-{slug}" / "intent.md"
        text = intent.read_text(encoding="utf-8").replace("idea:\n", "idea: 2026-11-02-1\n")
        _write(intent, text)
        trees[n] = tree
    # The control: what intent wrote before 100, on the change's branch.
    tagged = seed.replace("[idea]", "[building]").replace(
        "\n\nWhy", "\n\nBuilding in .sdlc/work/002-tagged/.\nWhy"
    )
    _write(trees["002"] / ".sdlc" / "work" / "inbox.md", INBOX + tagged)

    _write(root / ".sdlc" / "work" / "inbox.md",
           INBOX + seed + "\n## [2026-11-03-1] [idea] Filed later\n\nOn main.\n")  # fmt: skip
    filed = _run(root, "inbox-commit")
    assert filed.returncode == 0, filed.stdout + filed.stderr
    assert _git(root, "log", "-1", "--format=%s") == "File 2026-11-03-1"

    based = _run(trees["001"], "base", "001")
    assert based.returncode == 0, based.stdout
    assert _json(based)["action"] != "refused"
    on_main = (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    assert (trees["001"] / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8") == on_main
    assert _git(trees["001"], "rev-parse", "HEAD") == _git(root, "rev-parse", "main")

    control = _run(trees["002"], "base", "002")
    assert control.returncode == 1 and _json(control)["resolvable"] is True, control.stdout
