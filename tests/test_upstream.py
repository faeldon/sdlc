"""Filing a bug in the plugin upstream (209): `sdlc.py upstream` reads the plugin's repo from its
manifest, renders the issue from an allowlist with the host's specifics cut, and files it through
the GitHub tracker under the person's own login, once."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REAL_WHICH = shutil.which


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_upstream", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _hide(monkeypatch, *names: str) -> None:
    """`shutil.which` finds none of `names`, wherever the test runs."""

    def which(cmd, *a, **k):
        return None if Path(str(cmd)).name in names else REAL_WHICH(cmd, *a, **k)

    monkeypatch.setattr(shutil, "which", which)


@pytest.fixture(autouse=True)
def plugin(tmp_path: Path, monkeypatch) -> Path:
    """A copy of the plugin's manifest, pointing at a repo of the test's, and no `claude` or `uv`
    on PATH, so no test reads the machine's installs."""
    folder = tmp_path / "plugin"
    (folder / ".claude-plugin").mkdir(parents=True)
    _manifest(folder, "https://github.com/someone/upstream")
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", folder)
    _hide(monkeypatch, "claude", "uv")
    return folder


def _manifest(folder: Path, repository: str | None) -> None:
    data = {"name": "sdlc", "version": "9.9.9"}
    if repository is not None:
        data["repository"] = repository
    (folder / ".claude-plugin" / "plugin.json").write_text(json.dumps(data), encoding="utf-8")


def _repo(tmp_path: Path, name: str = "repo") -> Path:
    root = tmp_path / name
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "work" / "inbox.md").write_text("# Inbox\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _input(root: Path, **sections: str) -> Path:
    """The scratch file the skill writes, each keyword a `## ` section (underscores as spaces)."""
    path = sdlc._ledger_dir(root) / sdlc.UPSTREAM_INPUT
    text = "".join(f"## {k.replace('_', ' ')}\n\n{v}\n\n" for k, v in sections.items())
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


BUG = {
    "Title": "close refuses a clean branch",
    "What_happens": "close says the branch carries another change.",
    "What_should_happen": "close lands it.",
    "How_to_see_it": "Run /sdlc:close on a change with one commit.",
    "Command": 'uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close 031',
    "Exit": "1",
    "Output": "refused: the branch carries another change's commits",
}


# R1. The upstream repo comes from the manifest.


@pytest.mark.portable
def test_upstream_repo_comes_from_the_manifest(tmp_path: Path, plugin: Path, gh) -> None:
    root = _repo(tmp_path)
    _git(root, "remote", "add", "origin", "https://github.com/hostowner/hostrepo.git")
    info = sdlc.upstream_info(root)
    assert info["repo"] == "someone/upstream" and info["available"], info
    assert info["new_issue_url"] == "https://github.com/someone/upstream/issues/new"
    assert info["login"] == "me" and info["own_repo"] is False
    _manifest(plugin, "https://github.com/afork/sdlc.git")
    assert sdlc.upstream_info(root)["repo"] == "afork/sdlc"
    for bad in ("https://gitlab.com/someone/upstream", None, "https://github.com/someone"):
        _manifest(plugin, bad)
        info = sdlc.upstream_info(root)
        assert info["available"] is False and info["repo"] is None, bad
        assert "repository" in info["why"], bad


# R2. The plugin's own repo files locally.


@pytest.mark.portable
def test_upstream_is_unavailable_in_the_plugins_own_repo(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text('{"name": "sdlc"}', encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    info = sdlc.upstream_info(root)
    assert info["own_repo"] is True and info["available"] is False
    assert "own repo" in info["why"]


# R11. With no gh or no login, nothing is filed and the bug still ends cleanly.


def test_upstream_without_gh_files_nothing(tmp_path: Path, monkeypatch, gh, capsys) -> None:
    root = _repo(tmp_path)
    _input(root, **BUG)
    _hide(monkeypatch, "claude", "uv", "gh")
    info = sdlc.upstream_info(root)
    assert info["available"] is False and info["why"] == "gh isn't installed"
    key = sdlc.upstream_render(root)["key"]
    out, code = sdlc.upstream_send(root, key)
    assert code == 0 and out["filed"] is None and out["why"] == "gh isn't installed"
    assert out["new_issue_url"] == "https://github.com/someone/upstream/issues/new"
    assert gh()["calls"] == []
    args = argparse.Namespace(render=False, send=True, key=key)
    assert sdlc.cli_upstream(root, root, args) == 0
    assert json.loads(capsys.readouterr().out)["filed"] is None


def test_upstream_without_a_login_files_nothing(tmp_path: Path, monkeypatch, gh) -> None:
    root = _repo(tmp_path)
    _input(root, **BUG)
    monkeypatch.setenv("FAKE_GH_NOAUTH", "1")
    info = sdlc.upstream_info(root)
    assert info["available"] is False and info["why"] == "run `gh auth login`"
    out, code = sdlc.upstream_send(root, sdlc.upstream_render(root)["key"])
    assert code == 0 and out["filed"] is None
    assert not [c for c in gh()["calls"] if c[:2] == ["issue", "create"]]


# R4. Only allowlisted fields reach the body.

SENTINELS = (
    "zqfolder", "zqowner", "zqremote", "Zq Username", "zq@zqmail.example", "zqslug",
    "Zqchangetitle", "Zqentrytitle", "zqbranch", "zqconfigvalue", "zqtrailervalue",
    "zqfilecontent", "2026-10-02-7",
)  # fmt: skip


def _sentinel_host(tmp_path: Path) -> Path:
    """A host whose every specific is a sentinel of its own."""
    root = _repo(tmp_path, "zqfolder")
    _git(root, "config", "user.name", "Zq Username")
    _git(root, "config", "user.email", "zq@zqmail.example")
    _git(root, "remote", "add", "origin", "git@github.com:zqowner/zqremote.git")
    (root / ".sdlc" / "config.toml").write_text(
        '[commands]\ncheck = "./zqconfigvalue.sh"\n', encoding="utf-8"
    )
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n## [2026-10-02-7] [idea] Zqentrytitle\n\nWhat it asks.\n", encoding="utf-8"
    )
    folder = root / ".sdlc" / "work" / "031-zqslug"
    folder.mkdir()
    (folder / "intent.md").write_text(
        "---\nid: 031\nslug: zqslug\ntier: 1\nstage: build\n---\n\n# 031 — Zqchangetitle\n",
        encoding="utf-8",
    )
    (root / "zqfile.txt").write_text("zqfilecontent\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "x\n\nSdlc-Size: zqtrailervalue")
    _git(root, "branch", "zqbranch")
    return root


@pytest.mark.portable
def test_upstream_body_holds_only_the_allowlist(tmp_path: Path, gh) -> None:
    root = _sentinel_host(tmp_path)
    sha = _git(root, "rev-parse", "HEAD")
    every = (
        f"{root}/src/app.py zqfolder zqowner/zqremote git@github.com:zqowner/zqremote.git "
        "Zq Username zq@zqmail.example 031-zqslug zqslug Zqchangetitle Zqentrytitle "
        f"2026-10-02-7 zqbranch ./zqconfigvalue.sh Sdlc-Size: zqtrailervalue {sha} #12"
    )
    _input(
        root,
        Title=f"close fails in {root.name}",
        What_happens=every,
        What_should_happen=every,
        How_to_see_it=every,
        Command=f"cd {root} && git switch zqbranch",
        Exit="1",
        Output=every + "\n" + every,
        Files="zqfilecontent",
    )
    shown = sdlc.upstream_render(root)
    text = (shown["title"] + "\n" + shown["body"]).casefold()
    assert [s for s in (*SENTINELS, sha[:7], "#12") if s.casefold() in text] == []
    assert shown["left_out"] == ["Files"]
    assert "### What happens" in shown["body"] and "### Diagnostics" in shown["body"]


# R5. The diagnostic block is versions and key names.


def _tool(bin_dir: Path, name: str, script: str) -> None:
    path = bin_dir / name
    path.write_text(f"#!/usr/bin/env python3\nimport sys\n{script}\n", encoding="utf-8")
    path.chmod(0o755)


def test_upstream_diagnostics_name_keys_never_values(tmp_path: Path, monkeypatch) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc" / "config.toml").write_text(
        '[git]\nbase = "trunkvalue"\n[commands]\ncheck = "./checkvalue.sh"\n'
        '[made]\nup = "madevalue"\n',
        encoding="utf-8",
    )
    lines = sdlc.upstream_diagnostics(root)
    text = "\n".join(lines)
    assert "Claude Code: unknown" in text and "uv: unknown" in text
    assert "sdlc-factory: unknown" in text
    assert "Config keys set: commands.check, git.base (and 1 not the plugin's)" in text
    assert not [v for v in ("trunkvalue", "checkvalue", "madevalue", "made.up") if v in text]
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    rows = [
        {"id": "sdlc@sdlc", "scope": "user", "version": "9.9.9"},
        {"id": "sdlc-factory@sdlc", "scope": "project", "version": "9.9.8",
         "projectPath": str(root)},
    ]  # fmt: skip
    _tool(
        bin_dir,
        "claude",
        "print('2.1.3 (Claude Code)') if sys.argv[1:] == ['--version'] else "
        f"print({json.dumps(json.dumps(rows))})",
    )
    _tool(bin_dir, "uv", "print('uv 0.9.9 (abc 2026-01-01)')")
    monkeypatch.setattr(shutil, "which", REAL_WHICH)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    text = "\n".join(sdlc.upstream_diagnostics(root))
    assert "- sdlc: 9.9.9 (user scope)" in text
    assert "- sdlc-factory: 9.9.8 (project scope)" in text
    assert "Claude Code: 2.1.3" in text and "uv: 0.9.9" in text
    rows.pop()
    _tool(bin_dir, "claude", f"print({json.dumps(json.dumps(rows))})")
    assert "- sdlc-factory: not installed" in sdlc.upstream_diagnostics(root)


# R6. Host specifics are cut, and text that stays unsafe is left out.


@pytest.mark.portable
def test_upstream_cut_places_paths_by_where_they_are(tmp_path: Path, plugin: Path) -> None:
    root = _repo(tmp_path)
    (plugin / "scripts").mkdir()
    (plugin / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    specifics = sdlc.host_specifics(root)
    cut = lambda t: sdlc._cut_host(t, specifics)[0]  # noqa: E731
    assert cut(f"{plugin.as_posix()}/scripts/sdlc.py") == "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc.py"
    assert cut(f"{root.as_posix()}/.sdlc/work/031-keep-drafts/intent.md") == (
        "<repo>/.sdlc/work/<change>/intent.md"
    )
    assert cut(f"{root.as_posix()}/src/drafts.py") == "<repo>/<path>"
    assert cut(".claude/worktrees/031-keep-drafts") == ".claude/worktrees/<change>"
    assert cut("src/drafts.py and scripts/sdlc.py") == "<path> and scripts/sdlc.py"
    assert cut("/etc/elsewhere/file") == "<path>"
    assert cut('"${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close') == (
        '"${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close'
    )
    assert cut("run /sdlc:close, see https://example.test/x") == "run /sdlc:close, see <url>"
    assert cut(r"C:\Users\someone\repo\x.py") == "<path>"


@pytest.mark.portable
def test_upstream_cut_leaves_out_what_it_cannot_make_safe(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _git(root, "branch", "keepdrafts")
    _input(
        root,
        Title="branch trouble",
        What_happens="the keepdraftsx branch is refused",
        Output="\n".join(f"line {n}" for n in range(1, 61)),
    )
    shown = sdlc.upstream_render(root)
    assert "keepdrafts" not in shown["body"]
    assert "*Left out: it named the host.*" in shown["body"]
    assert "What happens: it named the host" in shown["left_out"]
    assert "line 21\n" in shown["body"] and "line 20\n" not in shown["body"]
    assert "Kept the last 40 lines of 60" in shown["body"]
    title_cut = sdlc._cut_host("the keepdrafts branch", sdlc.host_specifics(root))
    assert title_cut == ("the <branch> branch", True)


# R7. The body sent is the body shown.


def test_upstream_send_refuses_a_body_not_previewed(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    _input(root, **BUG)
    old = sdlc.upstream_render(root)["key"]
    _input(root, **{**BUG, "What_happens": "something else"})
    out, code = sdlc.upstream_send(root, old)
    assert code == 1 and out["refusals"]
    assert not [c for c in gh()["calls"] if c[:2] == ["issue", "create"]]
    shown = sdlc.upstream_render(root)
    assert shown["key"] != old and shown["body"].startswith(
        f"<!-- sdlc:host-bug:{shown['key']} -->"
    )


# R9. Filed under the person's own login, with nothing GitHub would drop.


def test_github_file_issue_names_the_repo_and_sets_nothing_else(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    number, url, why = sdlc.upstream_tracker(root).file_issue("someone/upstream", "t", "b")
    assert why is None and number == 1 and url.endswith("/issues/1")
    (create,) = [c for c in gh()["calls"] if c[:2] == ["issue", "create"]]
    assert create == [
        "issue", "create", "--repo", "someone/upstream", "--title", "t", "--body-file", "-"
    ]  # fmt: skip
    assert gh()["issues"][0]["body"] == "b"


# R10. A rerun never files twice.


def test_upstream_send_never_files_twice(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    path = _input(root, **BUG)
    shown = sdlc.upstream_render(root)
    out, code = sdlc.upstream_send(root, shown["key"])
    assert code == 0 and out["filed"] == 1 and out["already"] is False
    assert not path.exists()
    _input(root, **BUG)
    again = sdlc.upstream_render(root)
    assert again["key"] == shown["key"] and again["already"]["number"] == 1
    out, code = sdlc.upstream_send(root, shown["key"])
    assert code == 0 and out["filed"] == 1 and out["already"] is True
    assert len([c for c in gh()["calls"] if c[:2] == ["issue", "create"]]) == 1
    record = json.loads((sdlc._ledger_dir(root) / "sdlc-upstream.json").read_text("utf-8"))
    assert record[shown["key"]]["state"] == "filed"
    assert record[shown["key"]]["repo"] == "someone/upstream"


def test_upstream_send_after_a_stopped_send_finds_the_issue_first(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    _input(root, **BUG)
    shown = sdlc.upstream_render(root)
    # A send that died after GitHub made the issue: the record says `sending`, the issue is there.
    record = sdlc._ledger_dir(root) / "sdlc-upstream.json"
    record.write_text(
        json.dumps({shown["key"]: {"repo": "someone/upstream", "state": "sending"}}),
        encoding="utf-8",
    )
    sdlc.upstream_tracker(root).file_issue("someone/upstream", shown["title"], shown["body"])
    out, code = sdlc.upstream_send(root, shown["key"])
    assert code == 0 and out["filed"] == 1
    assert len([c for c in gh()["calls"] if c[:2] == ["issue", "create"]]) == 1
    (listed,) = [c for c in gh()["calls"] if c[:2] == ["issue", "list"]]
    assert listed[2:4] == ["--repo", "someone/upstream"] and "@me" in listed
    assert json.loads(record.read_text("utf-8"))[shown["key"]]["state"] == "filed"


def test_a_stopped_send_with_no_issue_files_it(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    _input(root, **BUG)
    shown = sdlc.upstream_render(root)
    record = sdlc._ledger_dir(root) / "sdlc-upstream.json"
    record.write_text(
        json.dumps({shown["key"]: {"repo": "someone/upstream", "state": "sending"}}),
        encoding="utf-8",
    )
    out, code = sdlc.upstream_send(root, shown["key"])
    assert code == 0 and out["filed"] == 1 and out["already"] is False


# R13. The upstream number never enters the host's issue records.


def test_an_upstream_send_changes_nothing_recorded_issues_reads(tmp_path: Path, gh) -> None:
    root = _repo(tmp_path)
    (root / ".sdlc" / "work" / "inbox.md").write_text(
        "# Inbox\n\n## [2026-10-01-1] [idea] Keep drafts\n\nWhat it asks.\n\nIssue: #3\n",
        encoding="utf-8",
    )
    _git(root, "commit", "-qam", "File 2026-10-01-1")
    before = sdlc.recorded_issues(root)
    _input(root, **BUG)
    out, code = sdlc.upstream_send(root, sdlc.upstream_render(root)["key"])
    assert code == 0 and out["filed"]
    assert sdlc.recorded_issues(root) == before
    assert _git(root, "status", "--porcelain") == ""


@pytest.mark.portable
def test_upstream_cut_places_a_path_after_a_colon_and_an_scp_remote(tmp_path: Path) -> None:
    """Round 1, C1: a path after `:` and a `user@host:path` remote no configured remote names
    are cut too, never sent as they are."""
    root = _repo(tmp_path)
    specifics = sdlc.host_specifics(root)
    assert sdlc._cut_host("host:/srv/drafts/x/y", specifics) == ("host:<path>", True)
    assert sdlc._cut_host("cloned git@example.test:me/secret.git", specifics) == (
        "cloned <remote>",
        True,
    )
    assert sdlc._cut_host("see https://example.test/a/b", specifics) == ("see <url>", True)
    assert sdlc._cut_host("run /sdlc:close now", specifics) == ("run /sdlc:close now", True)
    assert sdlc._cut_host(r"at C:\Users\someone\x.py", specifics) == ("at <path>", True)


@pytest.mark.portable
def test_upstream_body_pings_no_one(tmp_path: Path) -> None:
    """Round 1 nit: an `@name` in the person's words would notify that GitHub user when the issue
    is filed, so the prose holds it in backticks; an email is left alone."""
    root = _repo(tmp_path)
    _input(root, Title="ask @someone", What_happens="I asked @someone-else, and a@b.example.")
    body = sdlc.upstream_render(root)["body"]
    assert "I asked `@someone-else`, and a@b.example." in body


@pytest.mark.portable
def test_upstream_cut_places_short_and_common_names_the_host_holds(tmp_path: Path) -> None:
    """Land fix (security Medium): a two-letter folder, owner or user is cut as a whole word, and
    a common word is cut where it is the host's own name rather than a branch every repo has."""
    root = _repo(tmp_path, "qz")
    _git(root, "remote", "add", "origin", "git@example.test:xo/origin.git")
    _git(root, "config", "user.name", "jb")
    specifics = sdlc.host_specifics(root)
    assert sdlc._cut_host("qz by jb, from xo/origin", specifics) == (
        "<repo> by <user>, from <path>",
        True,
    )
    assert sdlc._cut_host("xo and origin", specifics) == ("<owner> and <repo>", True)
    # A short name is never matched inside a longer word, and never leaves that word out.
    assert sdlc._cut_host("quiz the jobs", specifics) == ("quiz the jobs", True)
    assert sdlc._cut_host("on main", specifics) == ("on main", True), "a branch every repo has"


@pytest.mark.portable
def test_upstream_cut_never_keeps_a_relative_path_that_climbs(tmp_path: Path, plugin) -> None:
    """Land fix (security Medium): a relative path is kept as written only when it names a file in
    the plugin's own copy, never through a `..` that climbs out of it."""
    root = _repo(tmp_path)
    (plugin / "scripts").mkdir()
    (plugin / "scripts" / "sdlc.py").write_text("", encoding="utf-8")
    (tmp_path / "secret").mkdir()
    (tmp_path / "secret" / "notes.txt").write_text("", encoding="utf-8")
    specifics = sdlc.host_specifics(root)
    assert sdlc._cut_host("scripts/../../secret/notes.txt", specifics) == ("<path>", True)
    assert sdlc._cut_host("scripts/sdlc.py", specifics) == ("scripts/sdlc.py", True)
