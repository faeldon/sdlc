"""134: the register never rides a change's branch. Ship and a landing hold what they file and
retire in the change's `entries.md`; close lands it in the `Close` commit, under the lock
`inbox-commit` takes. Each test builds a real repo and runs the real ship and close."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_register_lands", ROOT / "scripts" / "sdlc.py")

REGISTER = (
    "# Inbox\n\n> The register.\n\n"
    "## [2026-10-01-1] [idea] Keep drafts\n\nThe first.\n\n"
    "## [2026-10-01-2] [idea] Reopen drafts\n\nThe one A takes.\n\n"
    "## [2026-10-01-3] [idea] Share drafts\n\nThe one B takes.\n\n"
    "## [2026-10-01-4] [nit] Terse wording\n\nSay more.\n"
)
INBOX = ".sdlc/work/inbox.md"


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    return out.stdout.strip()


def _repo(tmp_path: Path, register: str = REGISTER) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / INBOX).write_text(register, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "user.email", "t@t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _open(root: Path, slug: str, idea: str = "", extra: str = "") -> tuple[Path, Path]:
    """A change opened in its worktree, its impact set and its `idea:` naming `idea`."""
    assert sdlc.cmd_new(root, slug, 1, None, worktree=True) == 0
    branch = next(b for _, b in sdlc.worktrees(root) if b.endswith(f"-{slug}"))
    tree = root / ".claude" / "worktrees" / branch
    folder = tree / ".sdlc" / "work" / branch
    intent = folder / "intent.md"
    text = intent.read_text(encoding="utf-8").replace("impact:\n", "impact: none\n", 1)
    text = text.replace("idea:\n", f"idea: {idea}\n", 1) if idea else text
    intent.write_text(text.replace("depends_on:\n", f"depends_on:\n{extra}", 1), "utf-8")
    return tree, folder


def _held(folder: Path, *entries: str, retire: tuple[str, ...] = ()) -> None:
    lines = [f"# {folder.name} — entries", ""]
    lines += [f"Retire {i}: taken in by {folder.name}" for i in retire]
    text = "\n".join(lines) + ("\n\n" if retire else "\n")
    (folder / sdlc.ENTRIES).write_text(text + "\n".join(entries), encoding="utf-8")


def _entry(entry_id: str, title: str, tag: str = "idea") -> str:
    return f"## [{entry_id}] [{tag}] {title}\n\nCarried forward.\n"


def _ship(root: Path, tree: Path, folder: Path, capsys=None) -> None:
    (tree / f"{folder.name}.txt").write_text("the change\n", encoding="utf-8")
    assert sdlc.cmd_ship(tree, folder.name[:3]) == 0
    _git(tree, "commit", "-q", "-m", f"ship {folder.name}")


def _close(root: Path, ident: str, capsys, check: bool = False) -> tuple[int, dict]:
    capsys.readouterr()
    code = sdlc.cmd_close(root, ident, check)
    return code, json.loads(capsys.readouterr().out)


def _register(root: Path) -> str:
    return (root / INBOX).read_text(encoding="utf-8")


def test_ship_leaves_the_register_as_the_base_has_it(tmp_path, capsys, monkeypatch) -> None:
    """R1: the change's commit names no register path, whatever it took and holds."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen", "2026-10-01-2")
    _held(folder, _entry("2026-10-02-1", "Page the drafts"), retire=("2026-10-01-4",))
    _ship(root, tree, folder)
    assert INBOX not in _git(tree, "show", "--name-only", "--format=", "HEAD").splitlines()
    assert _git(tree, "show", f"HEAD:{INBOX}") == REGISTER.rstrip("\n")


def test_ship_refuses_an_uncommitted_register_edit(tmp_path, capsys) -> None:
    """R11: an entry appended the old way is refused before anything is stamped."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen")
    (tree / INBOX).write_text(REGISTER + "\n" + _entry("2026-10-02-1", "Old way"), "utf-8")
    before = (folder / "intent.md").read_text(encoding="utf-8")
    capsys.readouterr()
    assert sdlc.cmd_ship(tree, folder.name[:3]) == 1
    err = capsys.readouterr().err
    assert "never edits the register" in err and sdlc.ENTRIES in err and "/sdlc:idea" in err
    assert (folder / "intent.md").read_text(encoding="utf-8") == before


def test_close_files_and_retires_in_the_close_commit(tmp_path, capsys, monkeypatch) -> None:
    """R4: the seed `idea:` names, the bug `fixes:` names and the retired nit leave, the held
    entries arrive, all in the one `Close` commit, whose parent is the change's commit."""
    register = REGISTER + "\n## [2026-10-01-5] [bug] Drafts vanish\n\nThey do.\n\nSeverity: low\n"
    root = _repo(tmp_path, register)
    tree, folder = _open(root, "reopen", "2026-10-01-2", "fixes: [2026-10-01-5]\n")
    _held(folder, _entry("2026-10-02-1", "Page the drafts"), retire=("2026-10-01-4",))
    _ship(root, tree, folder)
    tip = _git(tree, "rev-parse", "HEAD")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys, check=True)
    assert code == 0, out
    assert out["register"] == {
        "file": ["2026-10-02-1"],
        "retire": ["2026-10-01-2", "2026-10-01-5", "2026-10-01-4"],
        "gone": [],
    }
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert _git(root, "rev-parse", "main~1") == tip, "the Close commit's parent is the change"
    assert _git(root, "log", "-1", "--format=%s", "main") == f"Close {folder.name}"
    names = _git(root, "show", "--name-only", "--format=", "main").splitlines()
    assert INBOX in names
    assert _git(root, "status", "--porcelain") == ""
    text = _register(root)
    assert "2026-10-01-2" not in text and "2026-10-01-5" not in text and "2026-10-01-4" not in text
    assert text.endswith("The one B takes.\n\n" + _entry("2026-10-02-1", "Page the drafts"))
    assert "Sdlc-Fixes: 2026-10-01-5 severity=low" in _git(root, "log", "-1", "--format=%B")


def test_close_refuses_a_held_id_the_base_holds_otherwise_before_merging(
    tmp_path, capsys, monkeypatch
) -> None:
    """R6: refused with the other preconditions, so the merge never runs."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen")
    _held(folder, _entry("2026-10-01-1", "Someone else's"))
    _ship(root, tree, folder)
    before = _git(root, "rev-parse", "main")
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 1 and "2026-10-01-1" in " ".join(out["refusals"]), out
    assert out["done"] == [] and _git(root, "rev-parse", "main") == before


def test_close_refuses_a_held_file_it_cant_read(tmp_path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen")
    (folder / sdlc.ENTRIES).write_text("# held\n\nfile this one too\n", encoding="utf-8")
    _ship(root, tree, folder)
    monkeypatch.chdir(root)
    code, out = _close(root, "001", capsys)
    assert code == 1 and any("line 3" in r for r in out["refusals"]), out
    assert out["done"] == []


def test_a_close_rerun_files_each_entry_once(tmp_path, capsys, monkeypatch) -> None:
    """R6: a close that stopped after its `Close` commit resumes without filing twice, and one
    the base caught up with word for word skips the entry."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen", "2026-10-01-2")
    entry = _entry("2026-10-02-1", "Page the drafts")
    _held(folder, entry)
    _ship(root, tree, folder)
    monkeypatch.chdir(root)
    real = sdlc._git_err
    calls = {"n": 0}

    def flaky(where, *args):
        if args[:2] == ("worktree", "remove") and not calls["n"]:
            calls["n"] += 1
            return "a stand-in failure"
        return real(where, *args)

    monkeypatch.setattr(sdlc, "_git_err", flaky)
    code, out = _close(root, "001", capsys)
    assert code == 1 and "remove folder" in out["done"], out
    code, out = _close(root, "001", capsys)
    assert code == 0, out
    assert _register(root).count("[2026-10-02-1]") == 1
    assert "Reopen drafts" not in _register(root)
    plan = sdlc.register_plan(_register(root), "", sdlc.held_entries(f"# t\n\n{entry}"))
    assert plan["skipped"] == ["2026-10-02-1"] and plan["file"] == []


def test_close_and_inbox_commit_keep_both_entries(tmp_path, capsys, monkeypatch) -> None:
    """R7: close writes the register under `_main_lock()`, rereading it there, so an idea filed
    between close's check and its write is kept beside what close files."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen", "2026-10-01-2")
    _held(folder, _entry("2026-10-02-1", "Page the drafts"))
    _ship(root, tree, folder)
    monkeypatch.chdir(root)
    real = sdlc.fix_trailers

    def file_an_idea(main, branch):
        # What /sdlc:idea does in another session while this close is between its steps.
        (root / INBOX).write_text(_register(root) + "\n" + _entry("2026-10-03-1", "Late"), "utf-8")
        assert sdlc.cmd_inbox_commit(root) == 0
        assert json.loads(capsys.readouterr().out)["refusals"] == []
        return real(main, branch)

    monkeypatch.setattr(sdlc, "fix_trailers", file_an_idea)
    capsys.readouterr()
    code = sdlc.cmd_close(root, "001")
    out = capsys.readouterr().out
    assert code == 0, out
    text = _register(root)
    assert text.count("[2026-10-03-1] [idea] Late") == 1
    assert text.count("[2026-10-02-1] [idea] Page the drafts") == 1
    assert "Reopen drafts" not in text


def test_drop_refuses_while_the_change_holds_entries(tmp_path, capsys) -> None:
    """R12: a `Drop` commit keeps the base's tree, so held entries would never be filed."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen")
    intent = folder / "intent.md"
    intent.write_text(
        intent.read_text(encoding="utf-8") + "\n## Dropped\n\nNot needed.\n", encoding="utf-8"
    )
    _held(folder, _entry("2026-10-02-1", "Page the drafts"))
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "wip")
    capsys.readouterr()
    assert sdlc.cmd_drop(tree, folder.name[:3]) == 1
    out = json.loads(capsys.readouterr().out)
    assert any(sdlc.ENTRIES in r for r in out["refusals"]), out
    assert "stage: dropped" not in intent.read_text(encoding="utf-8")


def test_next_entry_counts_the_ids_a_change_holds(tmp_path) -> None:
    """R8: an id held on a branch, on disk or only in a commit, is never handed out again."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen")
    _held(folder, _entry("2026-10-01-7", "Held on disk"))
    assert sdlc.next_entry_ids(root, "2026-10-01") == ["2026-10-01-8"]
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", "wip")
    _held(folder, _entry("2026-10-01-2", "Rewritten"))
    assert sdlc.next_entry_ids(root, "2026-10-01") == ["2026-10-01-8"], "the commit still counts"


def test_a_held_split_seed_records_its_issue(tmp_path) -> None:
    """R9: between ship and close, a seed split off an issue is that issue's record."""
    root = _repo(tmp_path)
    tree, folder = _open(root, "reopen")
    _held(folder, _entry("2026-10-02-1", "Split off").replace(
        "Carried forward.\n", "Split from 001-reopen: the rest.\n\nIssue: #41\n"
    ))  # fmt: skip
    found = sdlc.recorded_issues(root)
    assert found[41]["filed"] == "2026-10-02-1", found
    assert 41 not in sdlc.recorded_issues(root, committed_only=True)


def test_two_landings_and_an_idea_never_conflict_on_the_register(
    tmp_path, capsys, monkeypatch
) -> None:
    """R5, by hand: A and B start from one base, each takes a seed and carries one forward. A
    ships and closes, an idea is filed on the base, then B comes up to date and closes. Nothing
    conflicts, each new entry is there once, and neither taken seed is."""
    root = _repo(tmp_path)
    a_tree, a = _open(root, "reopen", "2026-10-01-2")
    b_tree, b = _open(root, "share", "2026-10-01-3")
    _held(a, _entry("2026-10-02-1", "Page the drafts"))
    _held(b, _entry("2026-10-02-2", "Search the drafts"))
    for tree in (a_tree, b_tree):
        (tree / ".sdlc" / "last-id").unlink()  # its own conflict, which `resolve` settles
        _ship(root, tree, tree / ".sdlc" / "work" / tree.name)
    monkeypatch.chdir(root)
    assert _close(root, "001", capsys)[0] == 0
    (root / INBOX).write_text(_register(root) + "\n" + _entry("2026-10-02-3", "Late"), "utf-8")
    capsys.readouterr()
    assert sdlc.cmd_inbox_commit(root) == 0
    capsys.readouterr()
    assert sdlc.cmd_base(b_tree, "002") == 0
    based = json.loads(capsys.readouterr().out)
    assert based["action"] == "rebased", based
    code, out = _close(root, "002", capsys)
    assert code == 0, out
    text = _register(root)
    for title in ("Page the drafts", "Search the drafts", "Late"):
        assert text.count(f"] [idea] {title}\n") == 1, (title, text)
    assert "Reopen drafts" not in text and "Share drafts" not in text
    assert "Keep drafts" in text and "Terse wording" in text
