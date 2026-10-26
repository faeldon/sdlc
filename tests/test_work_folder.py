"""The change folder is `.sdlc/work/`. A repo still on the old `work/` keeps working there,
history included, until `/sdlc:setup` moves it (`move-work`); that fallback is a shim, gone in
1.5.0. Every path the script builds, on disk and in git, comes from `work_rel()`."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_work_folder", ROOT / "scripts" / "sdlc.py")
metrics = _load("metrics_work_folder", ROOT / "scripts" / "metrics.py")
factory = _load("factory_work_folder", ROOT / "plugins" / "factory" / "scripts" / "factory.py")


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _write(root: Path, rel: str, text: str = "x\n") -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8")


# R1. One resolver.


def test_a_new_repo_keeps_its_changes_under_sdlc(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert sdlc.work_rel(root) == ".sdlc/work"
    assert sdlc.work_dir(root) == root / ".sdlc" / "work"


def test_a_repo_on_the_old_folder_stays_there_until_it_moves(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "work/inbox.md", "# Inbox\n")
    assert sdlc.work_rel(root) == "work"
    _write(root, ".sdlc/work/inbox.md", "# Inbox\n")
    assert sdlc.work_rel(root) == ".sdlc/work", "the new folder wins once it exists"


def test_an_old_repo_whose_changes_all_closed_is_still_on_the_old_folder(tmp_path: Path) -> None:
    """Close removes each folder, so an old repo can hold no `work/` at all: history decides."""
    root = _repo(tmp_path)
    _write(root, "work/001-reopen-drafts/intent.md")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-reopen-drafts")
    _git(root, "rm", "-r", "-q", "work")
    _git(root, "commit", "-q", "-m", "Close 001-reopen-drafts")
    assert not (root / "work").exists()
    assert sdlc.work_rel(root) == "work"


def test_a_worktree_resolves_as_its_main_checkout_does(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "work/inbox.md", "# Inbox\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "inbox")
    tree = tmp_path / "tree"
    _git(root, "worktree", "add", "-q", "-b", "001-reopen-drafts", str(tree))
    assert sdlc.work_dir(tree) == tree / "work"


def test_no_literal_work_path_in_the_script() -> None:
    """Every path to the change folder comes from `work_rel()`: a literal `work/` in a string the
    code runs is one a moved repo would read in the wrong place. Docstrings describe, and aren't
    read."""
    tree = ast.parse((ROOT / "scripts" / "sdlc.py").read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    # Kept for good: what reads history, which never migrates. Uninstall's search for the plugin's
    # mentions in a host's docs, and the pointer older intent headings carry.
    kept = {sdlc.MENTIONS_RE.pattern, " → work/"}
    found = [
        f"line {node.lineno}: {node.value!r}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        and node.value not in kept
        and re.search(r"(?<![\w./])work/", node.value)
    ]
    assert found == [], "\n".join(found)


# R2. A change's checkout is read from its folder's path.


@pytest.mark.parametrize("rel", [".sdlc/work", "work"])
def test_checkout_of_reads_the_checkout_from_either_folder(tmp_path: Path, rel: str) -> None:
    assert sdlc.checkout_of(tmp_path / rel / "001-reopen-drafts") == tmp_path


# R3. Metrics and the factory follow it.


@pytest.mark.parametrize("rel", [".sdlc/work", "work"])
def test_metrics_reads_a_change_s_own_files_under_either_folder(rel: str) -> None:
    assert metrics.artifact(f"{rel}/001-reopen-drafts/intent.md", "001-reopen-drafts") == "intent"
    absolute = f"/repo/{rel}/001-reopen-drafts/spec.md"
    assert metrics.artifact(absolute, "001-reopen-drafts") == "spec"


@pytest.mark.parametrize("layout", ["new", "old", "both"])
def test_the_factory_finds_the_folder_sdlc_finds(tmp_path: Path, layout: str) -> None:
    root = _repo(tmp_path)
    if layout in ("old", "both"):
        _write(root, "work/inbox.md")
    if layout in ("new", "both"):
        _write(root, ".sdlc/work/inbox.md")
    assert factory.work_rel(root) == sdlc.work_rel(root)


# R7. Register ids never repeat across the move.


def test_an_id_deleted_before_the_move_is_never_handed_out_after_it(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "work/inbox.md", "# Inbox\n\n## [2026-10-26-4] [idea] Keep drafts\n\nx\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "File 2026-10-26-4")
    _write(root, "work/inbox.md", "# Inbox\n")
    _git(root, "commit", "-q", "-am", "Retire 2026-10-26-4")
    (root / ".sdlc").mkdir()
    _git(root, "mv", "work", ".sdlc/work")
    _git(root, "commit", "-q", "-m", "Move work to .sdlc/work")
    assert sdlc.work_rel(root) == ".sdlc/work"
    assert sdlc.next_entry_ids(root, "2026-10-26") == ["2026-10-26-5"]


# R5. Setup moves an old repo's folder once. R6. Until then, it is told and keeps working.


def _old_repo(tmp_path: Path) -> Path:
    """A repo on the old folder: one closed change in history, and its register."""
    root = _repo(tmp_path)
    _write(root, "work/001-reopen-drafts/intent.md")
    _write(root, "work/inbox.md", "# Inbox\n\n## [2026-10-26-1] [idea] Keep drafts\n\nx\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-reopen-drafts")
    _git(root, "rm", "-r", "-q", "work/001-reopen-drafts")
    _git(root, "commit", "-q", "-m", "Close 001-reopen-drafts")
    return root


def _move(root: Path, capsys) -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_move_work(root)
    return code, json.loads(capsys.readouterr().out)


def test_move_work_moves_the_old_folder_in_one_commit(tmp_path: Path, capsys) -> None:
    root = _old_repo(tmp_path)
    before = _git(root, "rev-parse", "HEAD")
    code, out = _move(root, capsys)
    assert code == 0, out
    assert _git(root, "log", "-1", "--format=%s") == "Move work to .sdlc/work"
    assert _git(root, "rev-parse", "HEAD~1") == before, "one commit"
    assert _git(root, "ls-files", "work") == ""
    assert _git(root, "ls-files", ".sdlc/work") == ".sdlc/work/inbox.md"
    assert sdlc.work_rel(root) == ".sdlc/work" and sdlc.old_folder(root) is None
    assert sdlc.next_entry_ids(root, "2026-10-26") == ["2026-10-26-2"]


@pytest.mark.parametrize(
    "setup, refusal",
    [
        ("open", "close or drop every change first"),
        ("dirty", "commit or put back these first: stray.txt"),
        ("there", ".sdlc/work/ already exists"),
        ("ignored", ".sdlc/work/ is gitignored"),
        ("unreleased", "release first: these closed changes aren't released"),
    ],
)
def test_move_work_refuses_before_moving_anything(
    tmp_path: Path, capsys, setup: str, refusal: str
) -> None:
    root = _old_repo(tmp_path)
    if setup == "open":
        _write(root, "work/002-keep-one-draft/intent.md")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "002")
    elif setup == "dirty":
        _write(root, "stray.txt")
    elif setup == "there":
        _write(root, ".sdlc/work/inbox.md")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "half")
    elif setup == "ignored":
        _write(root, ".gitignore", ".claude/worktrees/\n.sdlc/work/\n")
        _git(root, "commit", "-q", "-am", "ignore")
    elif setup == "unreleased":
        _write(root, ".sdlc/config.toml", '[release]\nversion_files = ["VERSION"]\n')
        _write(root, "VERSION", "1.0.0\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "release config")
    head = _git(root, "rev-parse", "HEAD")
    code, out = _move(root, capsys)
    assert code == 1
    assert any(r.startswith(refusal) for r in out["refusals"]), out["refusals"]
    assert _git(root, "rev-parse", "HEAD") == head and (root / "work").is_dir()


def test_move_work_refuses_a_worktree(tmp_path: Path, capsys) -> None:
    root = _old_repo(tmp_path)
    tree = tmp_path / "tree"
    _git(root, "worktree", "add", "-q", "-b", "002-keep-one-draft", str(tree))
    code, out = _move(tree, capsys)
    assert code == 1 and "not a change's worktree" in out["refusals"][0]


def test_an_old_repo_is_nudged_and_keeps_working(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _old_repo(tmp_path)
    nudge = "work/ is the old change folder: run /sdlc:setup to move it to .sdlc/work/"
    assert sdlc.old_folder(root) == nudge
    assert [p for p in sdlc.analyze(root)["problems"] if "old change folder" in p["detail"]] == []
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    capsys.readouterr()
    assert sdlc.main() == 0
    assert f"■ Change folder: {nudge}" in capsys.readouterr().out
    capsys.readouterr()
    sdlc.cmd_readiness(root)
    items = {i["name"]: i for i in json.loads(capsys.readouterr().out)["items"]}
    assert items["work moved"]["status"] == "warn" and items["work moved"]["detail"] == nudge
    assert [c["name"] for c in sdlc.closed_changes(root, None, "main")] == ["001-reopen-drafts"]


def test_a_half_moved_repo_names_both_folders(tmp_path: Path) -> None:
    root = _old_repo(tmp_path)
    _write(root, ".sdlc/work/inbox.md")
    said = sdlc.old_folder(root)
    assert said.startswith("both work/ and .sdlc/work/ exist: half-moved")


# R10. The base branch is resolved once.


def test_the_base_branch_is_resolved_once_per_checkout(tmp_path: Path, monkeypatch) -> None:
    root = _repo(tmp_path)
    calls = []
    real = sdlc._git

    def counting(where, *args):
        if args[:2] == ("rev-parse", "--verify"):
            calls.append(args)
        return real(where, *args)

    monkeypatch.setattr(sdlc, "_git", counting)
    for _ in range(5):
        assert sdlc.load_config(root)[0]["git"]["base"] == "main"
    assert len(calls) == 1
