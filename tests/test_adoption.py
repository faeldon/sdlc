"""A repo adopts the plugin unedited.

The mechanism/policy split works only if any repo can adopt the plugin without editing it. So this
one runs the script the way the skills do, `uv run --script`, in a scratch repo with nothing but a
README and a `.gitignore` for the worktrees: no `.sdlc/`, no `work/`, no virtualenv, no tools of
its own. A change goes the whole way from `new` to `close`, and the main checkout is never written
until close lands it.
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

pytestmark = pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")


def _run(cwd: Path, *args: str, path: str | None = None) -> subprocess.CompletedProcess:
    # VIRTUAL_ENV is dropped so uv builds the script's own environment rather than reusing the one
    # these tests run in, which would hide a missing dependency in the script's metadata.
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | GIT_ID
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=True,
        env=os.environ | GIT_ID,
    )
    return out.stdout.strip()


def _track(root: Path, remote: Path, trunk: str) -> None:
    """Give `root` an origin holding `trunk`, with `origin/HEAD` naming it, as a clone has."""
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "origin", trunk)
    _git(root, "remote", "set-head", "origin", trunk)


# A host whose only branch is `master` gets there with no config: `origin/HEAD` names it.
TRUNKS = pytest.mark.parametrize("trunk", ["main", "master"])


def _land(root: Path, number: str, slug: str, rel: str) -> None:
    """A change run from `new` to `close` through the script, its folder asserted under `rel`."""
    made = _run(root, "new", slug, "--tier", "1", "--worktree")
    assert made.returncode == 0, made.stderr
    tree = root / ".claude" / "worktrees" / f"{number}-{slug}"
    intent = tree / rel / f"{number}-{slug}" / "intent.md"
    assert intent.is_file(), made.stdout
    intent.write_text(intent.read_text(encoding="utf-8").replace("impact:\n", "impact: none\n", 1))
    (tree / f"{slug}.txt").write_text("the change itself\n", encoding="utf-8")
    assert _run(tree, "ship", number).returncode == 0
    _git(tree, "commit", "-q", "-m", f"ship {number}")
    closed = _run(root, "close", number)
    assert closed.returncode == 0, closed.stdout + closed.stderr


def test_a_repo_on_the_old_folder_works_there_then_moves_once(tmp_path: Path) -> None:
    """A repo set up before 1.4.0 keeps `work/` and is nudged; `move-work` moves it once, and the
    next change lands under `.sdlc/work/`, numbered on from the last."""
    root = tmp_path / "old"
    (root / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "work" / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")

    assert json.loads(_run(root, "config").stdout)["work"]["rel"] == "work"
    assert "■ Change folder: work/ is the old change folder" in _run(root, "status").stdout
    assert _run(root, "check", "--strict").returncode == 0, "a nudge, never a problem"
    _land(root, "001", "before-the-move", "work")

    moved = _run(root, "move-work")
    assert moved.returncode == 0, moved.stdout + moved.stderr
    assert _git(root, "log", "-1", "--format=%s") == "Move work to .sdlc/work"
    assert not (root / "work").exists() and (root / ".sdlc" / "work" / "inbox.md").is_file()
    assert "Change folder" not in _run(root, "status").stdout

    _land(root, "002", "after-the-move", ".sdlc/work")
    subjects = _git(root, "log", "--format=%s").splitlines()
    assert subjects[0] == "Close 002-after-the-move" and "Close 001-before-the-move" in subjects
    assert _run(root, "next").stdout.strip() == "003"


@TRUNKS
def test_a_bare_repo_runs_a_change_from_new_to_close(tmp_path: Path, trunk: str) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    (root / "README.md").write_text("a repo with nothing set up\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", trunk)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    if trunk != "main":
        _git(tmp_path, "init", "-q", "--bare", "-b", trunk, str(tmp_path / "remote.git"))
        _track(root, tmp_path / "remote.git", trunk)

    cfg = _run(root, "config")
    assert cfg.returncode == 0, cfg.stderr
    out = json.loads(cfg.stdout)
    assert out["config_file"] is None
    assert all(v is None for v in out["commands"].values())
    assert out["docs"]["review"]["source"] == "plugin"
    assert out["work"] == {
        "dir": str(root / ".sdlc" / "work"),
        "rel": ".sdlc/work",
        "ignored": False,
        "register": str(root / ".sdlc" / "work" / "inbox.md"),
    }
    assert out["git"] == {"base": trunk, "base_source": "detected"}

    def main_checkout() -> tuple[str, list[str]]:
        return _git(root, "status", "--porcelain"), sorted(
            p.name for p in root.rglob(".sdlc/work/*")
        )

    before = main_checkout()
    made = _run(root, "new", "first-change", "--tier", "1", "--worktree")
    assert made.returncode == 0, made.stderr
    assert "(plugin template)" in made.stdout
    tree = root / ".claude" / "worktrees" / "001-first-change"
    intent = tree / ".sdlc" / "work" / "001-first-change" / "intent.md"
    assert intent.is_file()

    # From the worktree, `config` points the skills at the worktree's own work/.
    assert json.loads(_run(tree, "config").stdout)["work"]["dir"] == str(tree / ".sdlc" / "work")

    # What /sdlc:intent and /sdlc:ship would have written: the prose, and the approved impact.
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("impact:\n", "impact: none\n", 1),
        encoding="utf-8",
    )
    (tree / "feature.txt").write_text("the change itself\n", encoding="utf-8")

    status = _run(tree, "status")
    assert status.returncode == 0 and "001" in status.stdout, status.stderr
    check = _run(tree, "check", "--strict")
    assert check.returncode == 0, check.stdout + check.stderr

    shipped = _run(tree, "ship", "001")
    assert shipped.returncode == 0, shipped.stderr
    # One commit carries the code, the change's folder and the counter `new` wrote beside it,
    # every one of them staged by `ship` itself.
    staged = set(_git(tree, "diff", "--cached", "--name-only").splitlines())
    assert {"feature.txt", ".sdlc/work/001-first-change/intent.md", ".sdlc/last-id"} <= staged, (
        staged
    )
    _git(tree, "commit", "-q", "-m", "ship 001")
    tip = _git(tree, "rev-parse", "HEAD")
    assert "001" in _run(root, "status").stdout, "the main checkout sees the worktree's change"
    assert main_checkout()[0] == before[0], "new and ship never wrote the main checkout"
    assert not (root / ".sdlc" / "work").exists()

    closed = _run(root, "close", "001")
    assert closed.returncode == 0, closed.stdout + closed.stderr
    assert json.loads(closed.stdout)["done"] == [
        "merge", "verify", "measure", "remove folder", "remove worktree", "delete branch"
    ]  # fmt: skip
    assert _git(root, "rev-parse", f"{trunk}~1") == tip
    assert _git(root, "log", "-1", "--format=%s", trunk) == "Close 001-first-change"
    # No session ever ran in this scratch repo, so close records what history gives, and says so.
    # (HOME stays real: uv's cache lives there, and this repo's path matches no transcript folder.)
    body = _git(root, "log", "-1", "--format=%B", trunk)
    assert "Sdlc-Coverage: none: no transcripts for this repo" in body
    assert "Sdlc-Totals: elapsed=" in body and "Sdlc-Mode: manual" in body
    assert not tree.exists()
    assert "001-first-change" not in _git(root, "branch", "--list")
    assert not (root / ".sdlc" / "work" / "001-first-change").exists()
    assert "stage: shipped" in _git(root, "show", f"{tip}:.sdlc/work/001-first-change/intent.md")
    assert (root / ".sdlc" / "last-id").read_text(encoding="utf-8") == "001\n"
    assert _git(root, "status", "--porcelain") == ""
    nxt = _run(root, "next")
    assert nxt.stdout.strip() == "002", "the committed counter holds 001 with the folder gone"

    # A second change, dropped: what /sdlc:drop runs, then close records it without landing it.
    assert _run(root, "new", "second-try", "--tier", "1", "--worktree").returncode == 0
    tree = root / ".claude" / "worktrees" / "002-second-try"
    intent = tree / ".sdlc" / "work" / "002-second-try" / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8") + "\n## Dropped\n\nThe first change covered it.\n",
        encoding="utf-8",
    )
    dropped = _run(tree, "drop", "002")
    assert dropped.returncode == 0, dropped.stdout + dropped.stderr
    before = _git(root, "rev-parse", trunk)
    closed = _run(root, "close", "002")
    assert closed.returncode == 0, closed.stdout + closed.stderr
    assert json.loads(closed.stdout)["done"] == [
        "verify", "measure", "record", "remove worktree", "delete branch"
    ]  # fmt: skip
    assert _git(root, "log", "-1", "--format=%s", trunk) == "Drop 002-second-try"
    assert _git(root, "rev-parse", f"{trunk}^1") == before
    assert _git(root, "diff", "--name-only", f"{trunk}^1", trunk) == ".sdlc/last-id"
    assert not tree.exists() and not (root / ".sdlc" / "work" / "002-second-try").exists()
    assert _git(root, "status", "--porcelain") == ""
    assert _run(root, "next").stdout.strip() == "003", "a dropped change's number stays spent"


def _bare(tmp_path: Path) -> Path:
    root = tmp_path / "bare"
    root.mkdir()
    (root / "README.md").write_text("a repo with nothing set up\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def test_a_bare_repo_files_a_bug_and_closes_the_change_that_fixes_it(tmp_path: Path) -> None:
    """The fix cycle through the script alone: what /sdlc:bug, /sdlc:intent, /sdlc:ship and
    /sdlc:close run, from filing to the `Sdlc-Fixes:` line retro counts."""
    root = _bare(tmp_path)
    bug_id = _run(root, "next-entry").stdout.strip()
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        f"# Inbox\n\n## [{bug_id}] [bug] The report loses its last row\n\nIt does.\n\n"
        "Severity: high\nPaths: report.txt\n",
        encoding="utf-8",
    )
    filed = _run(root, "bug-commit")
    assert filed.returncode == 0, filed.stdout + filed.stderr
    assert _git(root, "log", "-1", "--format=%s") == f"File {bug_id}"
    assert "■ Bugs: 1 open (high 1)" in _run(root, "status").stdout

    assert _run(root, "new", "fix-report", "--tier", "1", "--worktree").returncode == 0
    tree = root / ".claude" / "worktrees" / "001-fix-report"
    intent = tree / ".sdlc" / "work" / "001-fix-report" / "intent.md"
    text = intent.read_text(encoding="utf-8").replace("impact:\n", "impact: patch\n", 1)
    intent.write_text(text.replace("depends_on:\n", f"depends_on:\nfixes: [{bug_id}]\n", 1))
    (tree / "report.txt").write_text("every row\n", encoding="utf-8")
    check = _run(tree, "check", "--strict")
    assert check.returncode == 0, check.stdout + check.stderr
    assert "■ Bugs" not in _run(tree, "status").stdout, "a bug being fixed isn't counted open"

    shipped = _run(tree, "ship", "001")
    assert shipped.returncode == 0, shipped.stderr
    assert f"removed bug {bug_id}" in shipped.stdout
    assert ".sdlc/work/inbox.md" in _git(tree, "diff", "--cached", "--name-only").splitlines()
    _git(tree, "commit", "-q", "-m", "ship 001")

    closed = _run(root, "close", "001")
    assert closed.returncode == 0, closed.stdout + closed.stderr
    body = _git(root, "log", "-1", "--format=%B")
    today = bug_id.rsplit("-", 1)[0]
    assert f"Sdlc-Fixes: {bug_id} severity=high reported={today} introduced_by=unknown" in body
    assert bug_id not in (root / ".sdlc" / "work" / "inbox.md").read_text(encoding="utf-8")
    bugs = json.loads(_run(root, "retro").stdout)["bugs"]
    assert bugs["fixed"] == {"high": 1} and bugs["open"] == [] and bugs["unattributed"] == 1


@TRUNKS
def test_a_bare_repo_releases_and_publishes_what_it_closed(tmp_path: Path, trunk: str) -> None:
    """The release loop after the change loop: one change closed with `impact: minor`, then a
    release that reads it from history and a publish to a remote, here a bare repo on disk."""
    root = tmp_path / "bare"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "VERSION").write_text('version = "0.1.0"\n', encoding="utf-8")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text(
        '[release]\nversion_files = ["VERSION"]\n', encoding="utf-8"
    )
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", trunk, str(remote))
    _git(root, "init", "-q", "-b", trunk)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    _track(root, remote, trunk)

    assert _run(root, "new", "first-change", "--worktree").returncode == 0
    tree = root / ".claude" / "worktrees" / "001-first-change"
    intent = tree / ".sdlc" / "work" / "001-first-change" / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8").replace("impact:\n", "impact: minor\n", 1),
        encoding="utf-8",
    )
    assert _run(tree, "ship", "001").returncode == 0
    _git(tree, "add", ".sdlc")
    _git(tree, "commit", "-q", "-m", "ship 001")
    assert _run(root, "close", "001").returncode == 0

    listed = json.loads(_run(root, "unreleased").stdout)
    assert [(c["id"], c["impact"]) for c in listed["changes"]] == [("001", "minor")]
    assert (listed["since"], listed["next"]) == ("v0.1.0", "0.2.0")
    released = _run(root, "release")
    assert released.returncode == 0, released.stdout + released.stderr
    assert (root / "VERSION").read_text(encoding="utf-8") == 'version = "0.2.0"\n'
    published = _run(root, "publish")
    assert published.returncode == 0, published.stdout + published.stderr
    assert json.loads(published.stdout)["done"] == [f"push {trunk}", "push tag"]
    assert _git(remote, "rev-parse", trunk) == _git(root, "rev-parse", trunk)
    assert _git(remote, "rev-parse", "v0.2.0^{commit}") == _git(root, "rev-parse", trunk)
    assert _git(root, "status", "--porcelain") == ""

    # The retro loop over both: it counts what closed and released, then records one commit,
    # which the next retrospective starts after.
    looked = json.loads(_run(root, "retro").stdout)
    assert looked["since"] is None
    assert [c["id"] for c in looked["changes"]] == ["001"]
    assert [r["tag"] for r in looked["releases"]] == ["v0.1.0", "v0.2.0"]
    (root / ".sdlc" / "DIRECTION.md").write_text("# Direction\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "inbox.md").write_text("# Ideas\n", encoding="utf-8")
    recorded = _run(root, "retro-commit")
    assert recorded.returncode == 0, recorded.stdout + recorded.stderr
    assert _git(root, "log", "-1", "--format=%s").startswith("Retrospective ")
    again = json.loads(_run(root, "retro").stdout)
    assert again["since"]["sha"] == _git(root, "rev-parse", "--short", "HEAD")
    assert again["changes"] == [] and again["releases"] == []
    assert _git(root, "status", "--porcelain") == ""


def test_before_the_first_change_and_after_the_last_everything_answers(tmp_path: Path) -> None:
    """Close removes each change's folder, so a repo with nothing open is the usual state, not only
    a new one: `check` has nothing to audit and passes, `status` says nothing is open, and `next`
    says the first change will be 001."""
    _git(tmp_path, "init", "-q", "-b", "main")
    check = _run(tmp_path, "check", "--strict")
    assert check.returncode == 0, check.stdout + check.stderr
    assert _run(tmp_path, "status").returncode == 0
    nxt = _run(tmp_path, "next")
    assert nxt.returncode == 0 and nxt.stdout.strip() == "001"


def test_with_no_tracker_a_change_runs_where_gh_doesnt_exist(tmp_path: Path) -> None:
    """A tracker is optional: with `target = "none"` and no `gh` anywhere on PATH, a change still
    goes from `new` to `close`, and `sync` says there is nothing to sync."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("git", "uv", "python3"):
        (bin_dir / tool).symlink_to(shutil.which(tool))
    path = str(bin_dir)
    root = tmp_path / "plain"
    (root / ".sdlc").mkdir(parents=True)
    (root / ".sdlc" / "config.toml").write_text('[archive]\ntarget = "none"\n', encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")

    made = _run(root, "new", "plain", "--worktree", path=path)
    assert made.returncode == 0, made.stderr
    tree = root / ".claude" / "worktrees" / "001-plain"
    intent = tree / ".sdlc" / "work" / "001-plain" / "intent.md"
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    synced = _run(tree, "sync", path=path)
    assert synced.returncode == 0, synced.stderr
    assert json.loads(synced.stdout)["nothing to sync"] == "archive.target is none"
    assert _run(tree, "ship", "001", path=path).returncode == 0
    _git(tree, "add", ".sdlc")
    _git(tree, "commit", "-q", "-m", "ship 001")
    closed = _run(root, "close", "001", path=path)
    assert closed.returncode == 0, closed.stdout + closed.stderr
    assert json.loads(closed.stdout)["archive"]["kept_because"] == "archive.target is none"


# ---------------------------------------------------------------- the plugin closing its own

PLUGIN = Path(__file__).resolve().parents[1]
BLOCKED = '        lines.append(f"Sdlc-Blocked: {_word(dep)} minutes={_minutes(seconds)}")\n'


def _plugin_copy(dest: Path) -> Path:
    """The files the script reads from its plugin: manifest, scripts, templates, defaults."""
    ignore = shutil.ignore_patterns("__pycache__")
    for name in (".claude-plugin", "scripts", "templates", "defaults"):
        shutil.copytree(PLUGIN / name, dest / name, ignore=ignore)
    return dest


def _probe(tree: Path, word: str) -> None:
    """Make the copy's `trailers()` end with a line saying which code wrote it."""
    metrics = tree / "scripts" / "metrics.py"
    text = metrics.read_text(encoding="utf-8")
    assert text.count(BLOCKED) == 1
    probe = f'    lines.append("Sdlc-Probe: {word}")\n'
    metrics.write_text(text.replace(BLOCKED, BLOCKED + probe), encoding="utf-8")


def _by(script: Path, cwd: Path, *args: str, ran: str | None = None):
    """`_run` with a given copy of the script, and the handoff marker set or cleared."""
    dropped = ("VIRTUAL_ENV", "SDLC_CLOSE_RAN", "SDLC_OWN_SCRIPT")
    env = {k: v for k, v in os.environ.items() if k not in dropped}
    env |= GIT_ID | ({"SDLC_CLOSE_RAN": ran} if ran else {})
    return subprocess.run(
        ["uv", "run", "--quiet", "--script", str(script), *args],
        cwd=cwd, capture_output=True, text=True, env=env,
    )  # fmt: skip


def test_the_plugins_own_close_runs_mains_code_then_the_merged_code(tmp_path: Path) -> None:
    """In the plugin's own repo, close runs main's script whatever copy started it, and then the
    code its merge brought: a change to close runs on its own close."""
    root = _plugin_copy(tmp_path / "plugin")
    (root / ".gitignore").write_text(".claude/worktrees/\n__pycache__/\n", encoding="utf-8")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[archive]\ntarget = "none"\n', encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the plugin")
    script = root / "scripts" / "sdlc.py"

    def land(slug: str, edit, ran: str | None = None, by: Path = script) -> tuple[dict, str]:
        made = _by(script, root, "new", slug, "--worktree")
        assert made.returncode == 0, made.stderr
        tree = next((root / ".claude" / "worktrees").glob(f"*-{slug}"))
        intent = tree / ".sdlc" / "work" / tree.name / "intent.md"
        intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
        edit(tree)
        number = tree.name.split("-")[0]
        shipped = _by(script, tree, "ship", number)
        assert shipped.returncode == 0, shipped.stderr
        # A change that edits scripts/ ships on its own code; one that doesn't, on main's.
        edits_scripts = bool(_git(tree, "status", "--porcelain", "--", "scripts"))
        assert ("ran the change's own code" in shipped.stdout) == edits_scripts, shipped.stdout
        _git(tree, "add", "-A")
        _git(tree, "commit", "-q", "-m", f"ship {tree.name}")
        closed = _by(by, root, "close", number, ran=ran)
        assert closed.returncode == 0, closed.stdout + closed.stderr
        assert not tree.exists()
        return json.loads(closed.stdout), _git(root, "log", "-1", "--format=%B", "main")

    # A change to close's measuring: its own Close commit is written by it.
    out, body = land("probe-merged", lambda tree: _probe(tree, "merged"))
    assert out["ran"] == "merged code" and "Sdlc-Probe: merged" in body

    # The same with the handoff already spent: the code loaded before the merge writes it.
    out, body = land("probe-second", lambda tree: _probe(tree, "second"), ran="merged")
    assert "ran" not in out and "Sdlc-Probe: second" not in body and "Sdlc-Probe: merged" in body

    # A stale copy, with no probe at all, starts a close; main's script, with both, finishes it.
    stale = _plugin_copy(tmp_path / "cache") / "scripts" / "sdlc.py"
    out, body = land("plain", lambda tree: (tree / "feature.txt").write_text("x\n"), by=stale)
    assert out["ran"] == "main's code" and "Sdlc-Probe: second" in body
    assert _git(root, "status", "--porcelain") == ""


def test_a_host_hears_what_an_update_changed_and_can_take_setup_out(tmp_path: Path) -> None:
    """The plugin updates under a host that set up from it: `drift`, run the way the skills run
    it, from the new copy, names the one block the update changed, and `uninstall` then leaves
    the repo as it was before setup."""
    plugin = _plugin_copy(tmp_path / "plugin")
    script = plugin / "scripts" / "sdlc.py"
    root = tmp_path / "host"
    root.mkdir()
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    before = sorted(p.name for p in root.iterdir() if p.name != ".git")

    def run(*args: str) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | GIT_ID
        return subprocess.run(
            ["uv", "run", "--quiet", "--script", str(script), *args],
            cwd=root,
            capture_output=True,
            text=True,
            env=env,
        )

    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    shutil.copy(plugin / "defaults" / "REVIEW.md", root / ".sdlc" / "REVIEW.md")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    created = (".sdlc/config.toml", ".sdlc/REVIEW.md", ".gitignore")
    made = run("record", "--created", *created, "--gitignore-line")
    assert made.returncode == 0, made.stderr
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Set the repo up for the sdlc plugin")

    review = plugin / "defaults" / "REVIEW.md"
    text = review.read_text(encoding="utf-8")
    first = next(line for line in text.splitlines() if line.startswith("## "))
    review.write_text(text.replace(first, f"{first}\n\nOne more sentence.", 1), encoding="utf-8")
    found = run("drift")
    assert found.returncode == 0, found.stderr
    drift = json.loads(found.stdout)
    assert drift["breaking"] == [] and drift["base"] == "manifest"
    assert [(u["unit"], u["class"]) for r in drift["refresh"] for u in r["units"]] == [
        (first, "refreshed")
    ]

    gone = run("uninstall")
    assert gone.returncode == 0, gone.stdout + gone.stderr
    after = sorted(p.name for p in root.iterdir() if p.name != ".git")
    assert after == before, "setup's .sdlc/ and the .gitignore it created holding one line are gone"
