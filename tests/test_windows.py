"""The plugin's scripts run on Windows as they do elsewhere: no Unix-only import, a lock on a file
that every worktree shares and no `git status` shows, UTF-8 out and in, one shell for a host's
commands, and LF in every file written. The Windows CI job runs every test marked `portable`, these
among them; the AST checks keep a later edit from undoing any of it on a platform nobody runs."""

from __future__ import annotations

import ast
import errno
import importlib.util
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

pytestmark = pytest.mark.portable

REPO = Path(__file__).resolve().parents[1]
SDLC_PY = REPO / "scripts" / "sdlc.py"
SCRIPTS = [
    SDLC_PY,
    REPO / "scripts" / "metrics.py",
    REPO / "scripts" / "indicators.py",
    *sorted((REPO / "scripts" / "trackers").glob("*.py")),
    REPO / "plugins" / "factory" / "scripts" / "factory.py",
]
GIT_ID = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def _load(name: str = "sdlc_windows"):
    spec = importlib.util.spec_from_file_location(name, SDLC_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        encoding="utf-8",
        check=True,
        env=os.environ | GIT_ID,
    ).stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("# r\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


class _FakeMsvcrt:
    """`msvcrt.locking` as Windows does it, for a test on another platform: a byte held by one
    descriptor raises OSError for every other, until it is unlocked."""

    LK_NBLCK, LK_UNLCK = 2, 0

    def __init__(self) -> None:
        self.guard = threading.Lock()
        self.held: dict[tuple[int, int], int] = {}
        self.waited = 0

    def locking(self, fd: int, mode: int, nbytes: int) -> None:
        st = os.fstat(fd)
        key = (st.st_dev, st.st_ino)
        with self.guard:
            if mode == self.LK_UNLCK:
                self.held.pop(key, None)
            elif key in self.held:
                self.waited += 1
                raise OSError(errno.EACCES, "locked")
            else:
                self.held[key] = fd


def test_the_script_loads_and_claims_without_fcntl(tmp_path: Path, monkeypatch) -> None:
    """R1, R2: with `fcntl` gone, the script still loads, and two claims at once through the
    Windows pair take turns by its retry and get distinct numbers. The pair is set by hand, since
    a module loaded with `os.name` faked can't build its `Path` constants here."""
    fake = _FakeMsvcrt()
    monkeypatch.setitem(sys.modules, "fcntl", None)
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    mod = _load("sdlc_without_fcntl")
    monkeypatch.setattr(mod, "_lock", mod._msvcrt_lock)
    monkeypatch.setattr(mod, "_unlock", mod._msvcrt_unlock)
    real = mod.next_id

    def slow(home: Path) -> str:
        nid = real(home)
        threading.Event().wait(0.1)  # hold the lock long enough for the other claim to wait
        return nid

    monkeypatch.setattr(mod, "next_id", slow)
    start = threading.Barrier(2)
    made: list[Path | None] = []

    def one(slug: str) -> None:
        start.wait()
        made.append(mod.claim(tmp_path, slug)[0])

    threads = [threading.Thread(target=one, args=(s,)) for s in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert sorted(p.name[:3] for p in made if p) == ["001", "002"]
    assert fake.waited > 0 and not fake.held


def test_a_lock_that_fails_for_another_reason_raises_rather_than_waits(
    tmp_path: Path, monkeypatch
) -> None:
    """Only a held lock is waited for: any other failure raises, as `flock` would."""

    class Broken(_FakeMsvcrt):
        def locking(self, fd: int, mode: int, nbytes: int) -> None:
            raise OSError(errno.EBADF, "bad descriptor")

    monkeypatch.setitem(sys.modules, "msvcrt", Broken())
    fd = os.open(tmp_path / "lock", os.O_RDWR | os.O_CREAT)
    try:
        with pytest.raises(OSError, match="bad descriptor"):
            sdlc._msvcrt_lock(fd)
    finally:
        os.close(fd)


def test_the_lock_is_a_file_in_the_git_dir_that_git_status_never_shows(tmp_path: Path) -> None:
    """R2, R4: inside git the lock is `sdlc.lock` beside the objects; outside, `.sdlc/lock`."""
    root = _repo(tmp_path)
    with sdlc._main_lock(root):
        pass
    assert (root / ".git" / "sdlc.lock").is_file()
    assert _git(root, "status", "--porcelain") == ""
    bare = tmp_path / "bare"
    bare.mkdir()
    assert sdlc._lock_path(bare) == bare / ".sdlc" / "lock"


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv, as the skills do")
def test_status_prints_utf8_under_a_code_page_without_its_marks(tmp_path: Path) -> None:
    """R5: a console in cp1252 has no `■`; the script writes UTF-8 anyway, and exits 0."""
    root = _repo(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    ran = subprocess.run(
        ["uv", "run", "--quiet", "--script", str(SDLC_PY), "status"],
        cwd=root,
        capture_output=True,
        env=env | {"PYTHONIOENCODING": "cp1252"},
    )
    assert ran.returncode == 0, ran.stderr.decode("utf-8", "replace")
    assert "■" in ran.stdout.decode("utf-8")


def _calls(path: Path, name: str) -> list[ast.Call]:
    """Every call in `path` to a function or method named `name`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Attribute) and node.func.attr == name)
            or (isinstance(node.func, ast.Name) and node.func.id == name)
        )
    ]


def _keywords(call: ast.Call) -> set[str]:
    return {k.arg for k in call.keywords if k.arg}


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_every_text_subprocess_names_its_encoding(script: Path) -> None:
    """R6: text mode without `encoding=` decodes with the locale's code page, cp1252 on Windows."""
    bad = [
        c.lineno
        for c in _calls(script, "run")
        if {"text", "universal_newlines"} & _keywords(c) and "encoding" not in _keywords(c)
    ]
    assert bad == [], f"{script.name}: text-mode subprocess.run without encoding at {bad}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_no_shell_true_anywhere(script: Path) -> None:
    """R7: a host's commands go through `_sh()`, never `shell=True`, which is `cmd.exe` there."""
    bad = [c.lineno for c in _calls(script, "run") if "shell" in _keywords(c)]
    assert bad == [], f"{script.name}: shell= at {bad}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_every_file_written_is_lf(script: Path) -> None:
    """R8: without `newline=`, a write on Windows turns every `\\n` into `\\r\\n`."""
    bad = [c.lineno for c in _calls(script, "write_text") if "newline" not in _keywords(c)]
    assert bad == [], f"{script.name}: write_text without newline= at {bad}"


def test_no_script_imports_a_one_platform_module_at_the_top() -> None:
    """R1: `fcntl` and `msvcrt` exist on one platform each, so only a branch may import them."""
    for script in SCRIPTS:
        tree = ast.parse(script.read_text(encoding="utf-8"))
        top = [
            alias.name
            for node in tree.body
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        ] + [node.module for node in tree.body if isinstance(node, ast.ImportFrom) and node.module]
        assert not {"fcntl", "msvcrt", "termios", "pwd", "grp", "resource"} & set(top), script.name


def test_the_shell_is_bin_sh_here_and_git_s_sh_on_windows(monkeypatch) -> None:
    """R7: `/bin/sh -c` as `shell=True` used; on Windows the `sh` on PATH, or a refusal."""
    if os.name != "nt":
        assert sdlc._sh("echo hi") == ["/bin/sh", "-c", "echo hi"]
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(shutil, "which", lambda name: r"C:\Git\usr\bin\sh.exe")
    assert sdlc._sh("echo hi") == [r"C:\Git\usr\bin\sh.exe", "-c", "echo hi"]
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(OSError, match="Git for Windows"):
        sdlc._sh("echo hi")


def test_evidence_with_no_sh_is_a_row_saying_so(tmp_path: Path, monkeypatch) -> None:
    """R7: the refusal goes out through the call site's own error path, never a traceback."""
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(shutil, "which", lambda name: None)
    rows = sdlc._evidence(tmp_path, ["echo hi"])
    assert rows[0]["exit"] is None and "Git for Windows" in rows[0]["error"]


def test_the_command_tracker_s_shell_is_sdlc_s() -> None:
    """R7: `trackers/command.py` can't import `sdlc.py`, so it keeps a copy, pinned here."""

    def source(path: Path) -> str:
        """The function without its docstring, so each copy can say which one it is."""
        tree = ast.parse(path.read_text(encoding="utf-8"))
        (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_sh"]
        if ast.get_docstring(fn) is not None:
            fn.body = fn.body[1:]
        return ast.unparse(fn)

    assert source(REPO / "scripts" / "trackers" / "command.py") == source(SDLC_PY)


def test_paths_shown_are_posix(tmp_path: Path) -> None:
    """R9: a repo path is what git prints, forward slashes, whatever the platform's separator."""
    root = tmp_path / "r"
    assert sdlc._shown(root / "scripts" / "ci.sh", root) == "scripts/ci.sh"
