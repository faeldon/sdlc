"""The change folder is `.sdlc/work/`, whatever an old repo still holds: the old `work/` is read
only from history, for good. Every path the script builds, on disk and in git, comes from
`work_rel()`."""

from __future__ import annotations

import ast
import importlib.util
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


def test_the_old_folder_is_never_the_change_folder(tmp_path: Path) -> None:
    """On disk or only in history, an old `work/` is not where changes live: a repo that hasn't
    moved it moves it by hand."""
    root = _repo(tmp_path)
    _write(root, "work/001-reopen-drafts/intent.md")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Ship 001-reopen-drafts")
    assert sdlc.work_rel(root) == ".sdlc/work"
    _git(root, "rm", "-r", "-q", "work")
    _git(root, "commit", "-q", "-m", "Close 001-reopen-drafts")
    assert sdlc.work_rel(root) == ".sdlc/work"
    tree = tmp_path / "tree"
    _git(root, "worktree", "add", "-q", "-b", "002-keep-one-draft", str(tree))
    assert sdlc.work_dir(tree) == tree / ".sdlc" / "work"


@pytest.mark.parametrize("command", [["move-work"], ["answers", "process"]])
def test_the_shims_commands_are_gone(command: list[str], monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["sdlc.py", *command])
    with pytest.raises(SystemExit) as raised:
        sdlc.main()
    assert raised.value.code != 0


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


# R8. Texts name where the folder is.

TEXTS = sorted(
    {
        *ROOT.glob("skills/*/SKILL.md"),
        *ROOT.glob("plugins/factory/skills/*/SKILL.md"),
        *ROOT.glob("plugins/factory/agents/*.md"),
        *ROOT.glob("defaults/*.md"),
        *ROOT.glob("templates/*.md"),
        ROOT / "README.md",
    }
)
# A line about the move names the old folder on purpose.
MOVE = re.compile(r"old `?work/|`work/` to `\.sdlc/work/`|move-work|Move work|before 1\.4\.0")


@pytest.mark.parametrize("path", TEXTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_text_names_the_old_folder(path: Path) -> None:
    bare = [
        f"{n}: {line.strip()}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"(?<![\w./-])work/", line) and not MOVE.search(line)
    ]
    assert bare == [], "\n".join(bare)


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
