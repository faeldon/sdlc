"""The host's cleanup after a close: `commands.close_cleanup`, handed to the human as it always
was, or, with `commands.close_cleanup_runs`, run by close itself as its last step, once the change
has landed and its worktree and branch are gone, behind the question that names it. Read from the
base branch's config before the merge, so a change can't turn on its own."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_cleanup", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, config: str) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _opened(root: Path, slug: str) -> tuple[Path, str]:
    assert sdlc.cmd_new(root, slug, 1, None, worktree=True) == 0
    branch = next(b for _, b in sdlc.worktrees(root) if b.endswith(f"-{slug}"))
    return root / ".claude" / "worktrees" / branch, branch


def _shipped(root: Path, slug: str = "thing", config: str | None = None) -> tuple[Path, str]:
    """A change shipped and committed in its worktree; `config` is a config.toml it changes."""
    tree, branch = _opened(root, slug)
    intent = tree / ".sdlc" / "work" / branch / "intent.md"
    intent.write_text(intent.read_text().replace("impact:\n", "impact: none\n", 1))
    assert sdlc.cmd_ship(root, branch[:3]) == 0
    (tree / f"{slug}.txt").write_text("the change\n", encoding="utf-8")
    if config is not None:
        (tree / ".sdlc" / "config.toml").write_text(config, encoding="utf-8")
    _git(tree, "add", f"{slug}.txt", ".sdlc")
    _git(tree, "commit", "-q", "-m", f"ship {branch}")
    return tree, branch


def _close(root: Path, capsys, monkeypatch, ident="001", check_only=False) -> tuple[int, dict]:
    monkeypatch.chdir(root)
    capsys.readouterr()
    code = sdlc.cmd_close(root, ident, check_only)
    return code, json.loads(capsys.readouterr().out)


def _cleanup(command: str, runs: bool | None = True) -> str:
    """A [commands] table: the cleanup as a TOML literal string, and the switch when given."""
    switch = "" if runs is None else f"close_cleanup_runs = {str(runs).lower()}\n"
    return f"[commands]\nclose_cleanup = '{command}'\n{switch}"


def _marker(tmp_path: Path) -> str:
    """A cleanup that leaves `ran-<id>` beside the repo, holding where it ran."""
    return f'pwd > "{tmp_path}/ran-{{id}}"'


def test_off_by_default_hands_over_and_runs_nothing(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, _cleanup(_marker(tmp_path), runs=None))
    _shipped(root)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0, out
    assert out["cleanup"] == {"command": f'pwd > "{tmp_path}/ran-001"', "runs": False}
    assert "cleanup" not in out["done"] and "cleanup_failed" not in out
    assert not (tmp_path / "ran-001").exists()


def test_check_names_the_command_and_runs_nothing(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, _cleanup(f"!  {_marker(tmp_path)}"))
    _shipped(root)
    code, checked = _close(root, capsys, monkeypatch, check_only=True)
    assert code == 0 and checked["cleanup"]["runs"] is True
    assert checked["cleanup"]["command"] == f'pwd > "{tmp_path}/ran-001"'
    assert "cleanup (--check)" in checked["skipped"]
    assert not (tmp_path / "ran-001").exists()
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["cleanup"] == checked["cleanup"]


def test_runs_last_after_the_worktree_and_branch_are_gone(tmp_path, capsys, monkeypatch) -> None:
    remote = tmp_path / "remote.git"
    seen = (
        f'git branch --list "{{id}}-*" > "{tmp_path}/branches"; '
        f'ls .claude/worktrees > "{tmp_path}/trees"; {_marker(tmp_path)}'
    )
    root = _repo(tmp_path, _cleanup(seen) + '[git]\npush = ["close"]\n')
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "origin", "main")
    tree, _ = _shipped(root)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0, out
    assert out["done"][-2:] == ["push", "cleanup"]
    assert (tmp_path / "branches").read_text() == "" and (tmp_path / "trees").read_text() == ""
    assert Path((tmp_path / "ran-001").read_text().strip()).resolve() == root.resolve()
    assert not tree.exists()


def test_a_leading_bang_is_stripped(tmp_path, capsys, monkeypatch) -> None:
    """`sh -c "! false"` exits 0: left in, the prompt's prefix would turn a failure into a pass."""
    root = _repo(tmp_path, _cleanup("! false"))
    _shipped(root)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["cleanup"]["command"] == "false"
    assert out["cleanup_failed"].startswith("exited 1")
    assert "cleanup" not in out["done"]


def test_a_failed_cleanup_never_fails_the_close(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, _cleanup("echo gone wrong >&2; exit 3"))
    tree, branch = _shipped(root)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["refusals"] == []
    assert out["cleanup_failed"] == "exited 3: gone wrong"
    assert out["done"][-1] == "delete branch" and not tree.exists()
    assert _git(root, "log", "-1", "--format=%s", "main") == f"Close {branch}"


def test_a_hung_cleanup_times_out_and_the_close_stands(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, _cleanup("sleep 5"))
    _shipped(root)
    monkeypatch.setattr(sdlc, "CLEANUP_TIMEOUT", 1)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["cleanup_failed"] == "timed out after 1s"


def test_a_failed_step_never_reaches_the_cleanup(tmp_path, capsys, monkeypatch) -> None:
    config = _cleanup(_marker(tmp_path)) + '[archive]\ntarget = "command"\ncommand = "exit 1"\n'
    root = _repo(tmp_path, config)
    _shipped(root)
    code, out = _close(root, capsys, monkeypatch)
    assert code == 1 and any(r.startswith("archive failed") for r in out["refusals"]), out
    assert "cleanup" not in out["done"] and "cleanup_failed" not in out
    assert not (tmp_path / "ran-001").exists()


def test_a_close_that_keeps_its_worktree_never_reaches_it(tmp_path, capsys, monkeypatch) -> None:
    """Exit 3 stops before the worktree goes; the rerun from the main checkout runs it."""
    root = _repo(tmp_path, _cleanup(_marker(tmp_path)))
    tree, _ = _shipped(root)
    code, out = _close(tree, capsys, monkeypatch)
    assert code == 3 and not (tmp_path / "ran-001").exists()
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["done"][-1] == "cleanup", out
    assert (tmp_path / "ran-001").exists()


def test_a_dropped_change_runs_it_too(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path, _cleanup(_marker(tmp_path)))
    tree, branch = _opened(root, "thing")
    intent = tree / ".sdlc" / "work" / branch / "intent.md"
    intent.write_text(
        intent.read_text().replace("stage: plan\n", "stage: dropped\n", 1) + "\n## Dropped\n\nNo.\n"
    )
    assert sdlc.cmd_drop(tree, None) == 0
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["done"][-1] == "cleanup", out
    assert (tmp_path / "ran-001").exists()


def test_a_change_cannot_turn_on_its_own_cleanup(tmp_path, capsys, monkeypatch) -> None:
    """The switch the change itself brings counts from the next close, never its own."""
    off = _cleanup(_marker(tmp_path), runs=False)
    root = _repo(tmp_path, off)
    _shipped(root, "first", config=off.replace("= false", "= true"))
    code, out = _close(root, capsys, monkeypatch)
    assert code == 0 and out["cleanup"]["runs"] is False, out
    assert not (tmp_path / "ran-001").exists()
    _shipped(root, "second")
    code, out = _close(root, capsys, monkeypatch, ident="002")
    assert code == 0 and out["done"][-1] == "cleanup", out
    assert (tmp_path / "ran-002").exists()


def test_after_the_merge_only_the_start_ref_s_config_counts(tmp_path, capsys, monkeypatch) -> None:
    """A rerun once main has the change reads the base from the start ref; with that ref gone,
    nothing runs and the command is handed over."""
    root = _repo(tmp_path, _cleanup(_marker(tmp_path), runs=False))
    _, branch = _shipped(root, config=_cleanup(_marker(tmp_path)))
    _git(root, "merge", "--ff-only", "-q", branch)
    code, out = _close(root, capsys, monkeypatch, check_only=True)
    assert out["cleanup"]["runs"] is False
    assert "can't be read" in out["cleanup"]["because"]


def test_config_warns_on_a_switch_with_no_command_or_a_word_for_it(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir()
    path = tmp_path / ".sdlc" / "config.toml"
    path.write_text("[commands]\nclose_cleanup_runs = true\n", encoding="utf-8")
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert any("close_cleanup_runs is on with no close_cleanup" in w for w in warnings)
    path.write_text('[commands]\nclose_cleanup = "x"\nclose_cleanup_runs = "yes"\n', "utf-8")
    cfg, warnings, _ = sdlc.load_config(tmp_path)
    assert "commands.close_cleanup_runs must be true or false" in warnings
    assert cfg["commands"]["close_cleanup_runs"] is False
