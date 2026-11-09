"""Where landed work reaches the remote: close and release push when `git.push` names them, each
behind the question it already asks; publish pushes what they couldn't; and status says what the
base branch holds that the remote doesn't. The remote is a bare repository on disk, so it all runs
offline."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_push", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, config: str = "", remote: bool = True) -> Path:
    """A repo that ignores its change worktrees, with `origin` a bare repo holding its `main`."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    if remote:
        _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(tmp_path / "remote.git"))
        _git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))
        _git(root, "push", "-q", "origin", "main")
    return root


def _opened(root: Path, slug: str = "thing") -> tuple[Path, str]:
    assert sdlc.cmd_new(root, slug, 1, None, worktree=True) == 0
    branch = next(b for _, b in sdlc.worktrees(root) if b.endswith(f"-{slug}"))
    return root / ".claude" / "worktrees" / branch, branch


def _shipped(root: Path, slug: str = "thing") -> tuple[Path, str]:
    """A change opened in its worktree, shipped and committed there, as /sdlc:ship leaves it."""
    tree, branch = _opened(root, slug)
    intent = tree / ".sdlc" / "work" / branch / "intent.md"
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    assert sdlc.cmd_ship(root, branch[:3]) == 0
    (tree / f"{slug}.txt").write_text("the change\n", encoding="utf-8")
    _git(tree, "add", f"{slug}.txt", ".sdlc")
    _git(tree, "commit", "-q", "-m", f"ship {branch}")
    return tree, branch


def _close(where: Path, capsys, monkeypatch, check_only: bool = False) -> tuple[int, dict]:
    """Close 001 from `where`: the main checkout, or its worktree, which close keeps (exit 3)."""
    monkeypatch.chdir(where)
    capsys.readouterr()
    code = sdlc.cmd_close(where, "001", check_only)
    return code, json.loads(capsys.readouterr().out)


def _landed(root: Path, name: str, body: str = "") -> None:
    """What close leaves on main without pushing: a `Close NNN-slug` commit, its issue line."""
    _git(root, "commit", "-q", "--allow-empty", "-m", f"Close {name}", *(["-m", body] * bool(body)))


def _status(root: Path, capsys, monkeypatch) -> str:
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    capsys.readouterr()
    sdlc.main()
    return capsys.readouterr().out


PUSH_CLOSE = '[git]\npush = ["close"]\n'
# GitHub as the tracker, for its `Closes #N` reader; nothing here closes or archives, so `gh`
# never runs, and its default push is turned off where a test doesn't want one.
GITHUB = '[archive]\ntarget = "github"\n'


# ---------------------------------------------------------------- close


def test_close_check_lists_what_the_push_would_send(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, PUSH_CLOSE)
    _landed(root, "000-earlier")
    _, branch = _shipped(root)
    code, out = _close(root, capsys, monkeypatch, check_only=True)
    assert code == 0 and out["push"]["on"] and out["push"]["remote"] == "origin"
    ahead = out["push"]["unpushed"]["ahead"]
    assert ahead[0] == f"(new) Close {branch}"
    assert ahead[1].endswith(f"ship {branch}") and ahead[-1].endswith("Close 000-earlier")
    assert _git(tmp_path / "remote.git", "rev-parse", "main") != _git(root, "rev-parse", "main")


def test_close_pushes_main_as_its_last_step(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, PUSH_CLOSE)
    tree, branch = _shipped(root)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["done"][-2:] == ["delete branch", "push"], out
    assert _git(tmp_path / "remote.git", "rev-parse", "main") == _git(root, "rev-parse", "main")
    assert _git(root, "log", "-1", "--format=%s", "origin/main") == f"Close {branch}"
    assert out["push"]["closed"] == [] and "push_failed" not in out
    assert "unpushed" not in out


def test_close_without_push_leaves_the_remote_and_nudges(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    before = _git(tmp_path / "remote.git", "rev-parse", "main")
    code, out = _close_after_ship(root, capsys, monkeypatch)
    assert code == 0 and "push" not in out["done"]
    assert out["push"] == {
        "on": False,
        "remote": "origin",
        "branch": "main",
        "off_because": "git.push doesn't name close",
    }
    assert _git(tmp_path / "remote.git", "rev-parse", "main") == before
    assert out["unpushed"]["changes"] == 1


def test_a_dropped_change_s_plan_lists_what_main_holds_past_its_branch(
    tmp_path, capsys, monkeypatch
):
    """A dropped branch may be behind main: the push sends main, so the plan lists main's own
    unpushed commits too, not only the branch's."""
    root = _repo(tmp_path, PUSH_CLOSE)
    tree, branch = _opened(root)
    _landed(root, "000-earlier")
    intent = tree / ".sdlc" / "work" / branch / "intent.md"
    intent.write_text(
        intent.read_text().replace("stage: plan\n", "stage: dropped\n", 1) + "\n## Dropped\n\nNo.\n"
    )
    assert sdlc.cmd_drop(tree, None) == 0
    code, out = _close(root, capsys, monkeypatch, check_only=True)
    ahead = out["push"]["unpushed"]["ahead"]
    assert code == 0 and ahead[0] == f"(new) Drop {branch}"
    assert ahead[-1].endswith("Close 000-earlier"), ahead
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["done"][-1] == "push", out
    assert _git(tmp_path / "remote.git", "rev-parse", "main") == _git(root, "rev-parse", "main")


def test_a_rerun_never_calls_a_written_close_commit_new(tmp_path, capsys, monkeypatch) -> None:
    """Exit 3 leaves the change landed and its Close commit written; the rerun's plan lists it as
    the commit it is, and everything main holds past the branch."""
    root = _repo(tmp_path, PUSH_CLOSE)
    tree, branch = _shipped(root)
    code, out = _close(tree, capsys, monkeypatch)
    assert code == 3, out
    _git(root, "commit", "-q", "--allow-empty", "-m", "File 2026-10-01-1")
    code, out = _close(root, capsys, monkeypatch, check_only=True)
    ahead = out["push"]["unpushed"]["ahead"]
    assert not any(a.startswith("(new)") for a in ahead)
    assert ahead[0].endswith("File 2026-10-01-1") and ahead[1].endswith(f"Close {branch}")


def _close_after_ship(root: Path, capsys, monkeypatch) -> tuple[int, dict]:
    _shipped(root)
    return _close(root, capsys, monkeypatch)


def test_close_with_no_remote_says_why_it_doesnt_push(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, PUSH_CLOSE, remote=False)
    code, out = _close_after_ship(root, capsys, monkeypatch)
    assert code == 0 and "push" not in out["done"]
    assert out["push"]["off_because"] == "no remote 'origin': set release.remote"


def test_a_refused_push_never_fails_the_close(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, PUSH_CLOSE)
    tree, branch = _shipped(root)
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(other))
    _git(other, "commit", "-q", "--allow-empty", "-m", "theirs")
    _git(other, "push", "-q", "origin", "main")
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["refusals"] == [] and out["done"][-1] == "delete branch"
    assert "push" not in out["done"] and "closed" not in out["push"]
    assert "/sdlc:publish pushes it" in out["push_failed"]
    assert not tree.exists() and branch not in _git(root, "branch", "--list")
    assert _git(other, "log", "-1", "--format=%s") == "theirs"


@pytest.mark.parametrize("config, want", [(GITHUB, [7]), ("", [])])
def test_only_the_tracker_reads_which_issues_a_push_closes(tmp_path, config, want) -> None:
    """GitHub's closing keyword is the GitHub tracker's to read: with no tracker, a `Closes #N`
    line is only text, and the count of changes is all there is."""
    root = _repo(tmp_path, config)
    _landed(root, "000-earlier", "Its artifacts are in abc.\nCloses #7")
    found = sdlc._unpushed(root, sdlc.load_config(root)[0])
    assert found["changes"] == 1 and found["closes"] == want


# ---------------------------------------------------------------- release and publish

RELEASE = '[release]\nversion_files = ["pkg.json"]\n'
PKG = '{\n  "name": "demo",\n  "version": "0.4.2"\n}\n'


def _released_repo(tmp_path: Path, config: str) -> Path:
    root = _repo(tmp_path, RELEASE + config)
    (root / "pkg.json").write_text(PKG, encoding="utf-8")
    _git(root, "add", "pkg.json")
    _git(root, "commit", "-q", "-m", "pkg")
    _git(root, "tag", "-a", "v0.4.2", "-m", "v0.4.2")
    _git(root, "push", "-q", "origin", "main", "v0.4.2")
    folder = root / ".sdlc" / "work" / "002-reopen-drafts"
    folder.mkdir(parents=True)
    (folder / "intent.md").write_text(
        "---\nid: 002\nslug: reopen-drafts\ntier: 1\nimpact: patch\nstage: shipped\n---\n\n"
        "# 002 — Reopen drafts\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Reopen drafts")
    _git(root, "rm", "-r", "-q", ".sdlc/work/002-reopen-drafts")
    _git(root, "commit", "-q", "-m", "Close 002-reopen-drafts")
    return root


def _run(capsys, fn, *args) -> tuple[int, dict]:
    capsys.readouterr()
    code = fn(*args)
    return code, json.loads(capsys.readouterr().out)


def test_release_pushes_main_and_the_tag_when_named(tmp_path, capsys) -> None:
    root = _released_repo(tmp_path, '[git]\npush = ["release"]\n')
    code, out = _run(capsys, sdlc.cmd_release, root, True)
    assert code == 0 and out["push"]["on"] and "push" not in out["done"]
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 0 and out["done"][-1] == "push", out
    remote = tmp_path / "remote.git"
    assert _git(remote, "rev-parse", "main") == _git(root, "rev-parse", "main")
    assert _git(remote, "rev-parse", "v0.4.3") == _git(root, "rev-parse", "v0.4.3")


def test_a_publish_command_release_left_is_named_with_the_push(tmp_path, capsys) -> None:
    """Release pushed the tag, the publish command never ran, and a change landed since: the yes
    must cover the command too, so it is in `will_run`."""
    root = _released_repo(tmp_path, 'publish = "true"\n[git]\npush = ["release"]\n')
    assert sdlc.cmd_release(root) == 0
    _landed(root, "003-export-totals")
    code, out = _run(capsys, sdlc.cmd_publish, root, True)
    assert code == 0 and out["will_run"] == ["push main", "publish command"], out


def test_release_without_push_stays_local(tmp_path, capsys) -> None:
    root = _released_repo(tmp_path, "")
    code, out = _run(capsys, sdlc.cmd_release, root)
    assert code == 0 and "push" not in out["done"]
    assert out["push"]["off_because"] == "git.push doesn't name release"
    assert _git(tmp_path / "remote.git", "tag") == "v0.4.2"


def test_publish_pushes_main_alone_once_the_tag_is_out(tmp_path, capsys) -> None:
    """The retry for a push close couldn't make, and the nudge's command: the release is on the
    remote, so what landed since goes alone."""
    root = _released_repo(tmp_path, GITHUB.replace("[archive]", "[git]\npush = []\n[archive]"))
    assert sdlc.cmd_release(root) == 0
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 0 and out["done"] == ["push main", "push tag"]
    code, out = _run(capsys, sdlc.cmd_publish, root, True)
    assert code == 0 and out["will_run"] == [], "nothing to publish"
    _landed(root, "003-export-totals", "Closes #9")
    code, out = _run(capsys, sdlc.cmd_publish, root, True)
    assert code == 0 and out["refusals"] == [] and out["unpushed"]["closes"] == [9]
    assert out["will_run"] == ["push main"]
    assert out["already"] == ["push tag", "publish command"]
    code, out = _run(capsys, sdlc.cmd_publish, root)
    assert code == 0 and out["done"] == ["push main"]
    assert out["skipped"][0] == "push tag (already done)"
    assert _git(tmp_path / "remote.git", "rev-parse", "main") == _git(root, "rev-parse", "main")


# ---------------------------------------------------------------- status


def test_status_says_what_waits_for_a_push(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, GITHUB)
    _landed(root, "001-reopen-drafts", "Closes #4")
    _git(root, "commit", "-q", "--allow-empty", "-m", "File 2026-10-01-1")
    _landed(root, "002-keep-drafts", "Closes #5\nCloses #6")
    out = _status(root, capsys, monkeypatch)
    assert (
        "■ Unpushed: 2 closed changes not on origin/main, oldest 0d (3 commits); a push closes "
        "#4, #5, #6  /sdlc:publish"
    ) in out


@pytest.mark.parametrize("config", ["[git]\nnudge_after_changes = 2\n",
                                    "[git]\nnudge_after_changes = 0\n"])  # fmt: skip
def test_status_says_nothing_below_the_threshold(tmp_path, capsys, monkeypatch, config) -> None:
    root = _repo(tmp_path, config)
    _landed(root, "001-reopen-drafts")
    assert "Unpushed" not in _status(root, capsys, monkeypatch)


def test_status_says_nothing_without_a_tracking_ref(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, remote=False)
    _landed(root, "001-reopen-drafts")
    assert "Unpushed" not in _status(root, capsys, monkeypatch)


def test_status_never_counts_a_commit_that_only_looks_like_a_close(tmp_path, capsys, monkeypatch):
    root = _repo(tmp_path)
    _git(root, "commit", "-q", "--allow-empty", "-m", "Close the gap in the docs")
    assert "Unpushed" not in _status(root, capsys, monkeypatch)


def test_a_push_never_waits_on_a_prompt(tmp_path, monkeypatch) -> None:
    """Close and release push by default on GitHub hosts: a remote wanting a password fails at
    once and is reported, never asks a session that can't answer."""
    seen: dict = {}

    def run(args, **kwargs):
        seen.update(kwargs, args=args)
        return subprocess.CompletedProcess(args, 128, "", "could not read Username")

    monkeypatch.setattr(sdlc.subprocess, "run", run)
    assert sdlc._push(tmp_path, "origin", "refs/heads/main") == "could not read Username"
    assert seen["stdin"] is subprocess.DEVNULL and seen["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert "--force" not in seen["args"]
