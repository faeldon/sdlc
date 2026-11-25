"""The retrospective's host figures (208): what `retro` reads from the host repos the person lists
in `.sdlc/hosts.local`, only in the plugin's own repo, as counts and fixed words alone.

"This repo" is a fixture holding the `sdlc` manifest and `scripts/sdlc.py`, so `_own_repo()`
holds. Each host is a fixture repo built the way close and drop leave one, as in
`test_retro.py`. `claude plugin list` is stubbed in every test, so nothing reads the machine's
own installs.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_hosts", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()
TODAY = date(2026, 11, 21)

INTENT = """\
---
id: {id}
slug: {slug}
tier: {tier}
impact: patch
stage: {stage}
created: 2026-10-01
updated: 2026-10-01
{extra}---

# {id} — {title}

## Problem

Something in {title}.
"""

# The names a host could leak, each planted in a fixture: none may reach any output.
SECRET_DIR = "zebracorp-ledger"
SECRET_BRANCH = "zebracorp-payroll-branch"
SECRET_TITLE = "Zebracorp payroll export"
SECRET_REASON = "Zebracorp legal said no"
SECRET_ORIGIN = "a zebracorp customer call"
SECRET_PROGRAM = "zebractl"
SECRETS = (SECRET_DIR, SECRET_BRANCH, SECRET_TITLE, SECRET_REASON, SECRET_ORIGIN, SECRET_PROGRAM)


def _git(root: Path, *args: str, when: str | None = None) -> str:
    env = os.environ | ({"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when} if when else {})
    out = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        encoding="utf-8",
        check=True,
        env=env,
    )
    return out.stdout.strip()


def _repo(path: Path, files: dict[str, str] | None = None) -> Path:
    path.mkdir(parents=True)
    for rel, text in {"README.md": "a repo\n", **(files or {})}.items():
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        (path / rel).write_text(text, encoding="utf-8", newline="\n")
    _git(path, "init", "-q", "-b", "main")
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "init", when="2026-09-01T12:00:00")
    return path


def _own(tmp_path: Path, hosts: str | None = None) -> Path:
    """This repo: the plugin's own, with a `Retrospective` commit on 2026-11-10 and, given
    `hosts`, its `.sdlc/hosts.local` (never committed)."""
    manifest = json.dumps({"name": "sdlc", "version": "1.11.0"})
    root = _repo(
        tmp_path / "plugin",
        {".claude-plugin/plugin.json": manifest, "scripts/sdlc.py": "# the script\n"},
    )
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "DIRECTION.md").write_text("# Direction\n", encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Retrospective 2026-11-10", when="2026-11-10T12:00:00")
    (root / ".git" / "info" / "exclude").write_text(".sdlc/hosts.local\n", encoding="utf-8")
    if hosts is not None:
        (root / ".sdlc" / "hosts.local").write_text(hosts, encoding="utf-8", newline="\n")
    return root


def _close(
    root: Path,
    name: str,
    *,
    tier: int = 1,
    when: str,
    trailers: tuple[str, ...] = (),
    title: str = "",
    extra: str = "",
    folder: str = ".sdlc/work",
) -> None:
    nid, slug = name.split("-", 1)
    path = root / folder / name
    path.mkdir(parents=True)
    text = INTENT.format(
        id=nid, slug=slug, tier=tier, stage="shipped", extra=extra, title=title or slug
    )
    (path / "intent.md").write_text(text, encoding="utf-8", newline="\n")
    (root / f"{slug}.txt").write_text(name + "\n", encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}", when=when)
    _git(root, "rm", "-r", "-q", f"{folder}/{name}")
    said = ["-m", "\n".join(trailers)] if trailers else []
    _git(root, "commit", "-q", "-m", f"Close {name}", *said, when=when)


def _drop(root: Path, name: str, *, at: str, when: str, reason: str) -> None:
    nid, slug = name.split("-", 1)
    _git(root, "checkout", "-q", "-b", name)
    path = root / ".sdlc" / "work" / name
    path.mkdir(parents=True)
    text = INTENT.format(id=nid, slug=slug, tier=2, stage="dropped", extra=f"dropped_at: {at}\n",
                         title=slug)  # fmt: skip
    (path / "intent.md").write_text(text + f"\n## Dropped\n\n{reason}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"Record why {name} was dropped", when=when)
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "-q", "-s", "ours", "--no-ff", "-m", f"Drop {name}", name, when=when)
    _git(root, "branch", "-q", "-D", name)


def _host_a(tmp_path: Path) -> Path:
    """Two closed changes (one by hand before the window, one by the factory in it) and one drop
    in the window; a config, a setup record at 1.4.0 and two templates; every planted name."""
    config = '[commands]\ncheck = "make zebracorp"\n\n[zebracorp]\nsecret = 1\n'
    setup = json.dumps({"version": "1.4.0"})
    root = _repo(
        tmp_path / SECRET_DIR,
        {
            ".sdlc/config.toml": config,
            ".sdlc/setup.json": setup,
            ".sdlc/templates/retro.md": "# Retrospective report\n",
            ".sdlc/templates/zebracorp-own.md": "# Zebracorp\n",
        },
    )
    _close(
        root, "001-reopen-drafts", tier=1, when="2026-11-01T12:00:00", title=SECRET_TITLE,
        trailers=(
            "Sdlc-Mode: manual",
            "Sdlc-Totals: stops=10 elapsed=100 agent=20 prompts=3",
            "Sdlc-Stage: build elapsed=50 agent=10",
            "Sdlc-Stage: zebrastage elapsed=5",
            f"Sdlc-Prompt: Bash:{SECRET_PROGRAM} asked=3 rejected=1",
            f"Sdlc-Origin: {SECRET_ORIGIN}",
            f"Sdlc-Base: {SECRET_BRANCH}",
            "Sdlc-Role: zebra-reviewer runs=1 agent=3",
            "Sdlc-Skill: sdlc:ship runs=2",
            "Sdlc-Skill: zebracorp:deploy runs=9",
            "Sdlc-Tool: Bash:sdlc.py:ship calls=4",
            f"Sdlc-Tool: Bash:{SECRET_PROGRAM} calls=7",
            "Sdlc-Fixes: 2026-10-30-01 severity=high",
            "Sdlc-Coverage: none: no transcript under /home/zebracorp-ledger",
        ),
    )  # fmt: skip
    _close(
        root, "002-draft-sync", tier=2, when="2026-11-12T12:00:00", extra="reworks: 001\n",
        trailers=("Sdlc-Mode: factory", "Sdlc-Totals: stops=4 elapsed=60 agent=30 prompts=1"),
    )  # fmt: skip
    _drop(root, "003-draft-export", at="build", when="2026-11-13T12:00:00", reason=SECRET_REASON)
    _git(root, "branch", SECRET_BRANCH)
    return root


def _host_b(tmp_path: Path) -> Path:
    """Three closed changes: an old one under the old `work/` with no trailers, before the
    window, and two by hand in it; a setup record at the plugin's own version."""
    setup = json.dumps({"version": sdlc.plugin_version()})
    root = _repo(tmp_path / "second", {".sdlc/setup.json": setup})
    _close(root, "001-old-change", when="2026-10-01T12:00:00", folder="work")
    _close(
        root, "002-draft-list", tier=1, when="2026-11-15T12:00:00",
        trailers=("Sdlc-Mode: manual", "Sdlc-Totals: stops=20 elapsed=200 agent=50"),
    )  # fmt: skip
    _close(
        root, "003-draft-sort", tier=1, when="2026-11-16T12:00:00",
        trailers=("Sdlc-Mode: manual", "Sdlc-Totals: stops=6 elapsed=40 agent=10"),
    )  # fmt: skip
    return root


@pytest.fixture(autouse=True)
def installs(monkeypatch) -> list:
    """`claude plugin list` stubbed: no installs, and each call recorded."""
    calls: list = []

    def stub(home):
        calls.append(home)
        return [], None

    monkeypatch.setattr(sdlc, "plugin_installs", stub)
    return calls


def _retro(root: Path) -> dict:
    return sdlc.retro.retro(root, sdlc.load_config(root)[0], TODAY)


def _dumped(value) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


# ---------------------------------------------------------------- the list (R3)


@pytest.mark.portable
def test_the_host_list_format(tmp_path: Path) -> None:
    """R3: one path a line, `~` expanded; blanks and `#` lines ignored; `!` excludes."""
    text = "\n".join([
        "# my hosts", "", f"{tmp_path / 'a'}", "  ", "~/b", f"!{tmp_path / 'c'}", "# !~/d",
    ])  # fmt: skip
    paths, excluded = sdlc.retro.host_list(text)
    home = Path("~").expanduser()
    assert paths == [(tmp_path / "a").resolve(), (home / "b").resolve()]
    assert excluded == [(tmp_path / "c").resolve()]
    assert sdlc.retro.host_list("") == ([], [])


# ---------------------------------------------------------------- where it reads (R1, R2)


def test_a_host_repo_never_reads_hosts(tmp_path: Path, installs) -> None:
    """R1: a repo that isn't the plugin's own reads no list, whatever it holds."""
    host = _host_b(tmp_path)
    root = _repo(tmp_path / "not-the-plugin")
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "hosts.local").write_text(f"{host}\n", encoding="utf-8")
    out = _retro(root)
    assert out["hosts"] == {"state": "unmeasured", "why": "read only in the plugin's own repo"}
    assert installs == []


def test_no_host_list_is_unmeasured(tmp_path: Path, monkeypatch, installs) -> None:
    """R2: no list, no count, no subprocess at all, and `claude plugin list` never runs."""
    root = _own(tmp_path)
    assert _retro(root)["hosts"] == {"state": "unmeasured", "why": "no host list"}
    ran: list = []
    real = subprocess.run
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: ran.append(a) or real(*a, **k))
    assert sdlc.retro.hosts_figures(root, None) == {"state": "unmeasured", "why": "no host list"}
    assert ran == [] and installs == []


# ---------------------------------------------------------------- reading a host (R4, R5)


def test_host_reads_are_log_and_show_only(tmp_path: Path, monkeypatch) -> None:
    """R4: reading a host runs git alone, and only the subcommands that read."""
    host = _host_a(tmp_path)
    ran: list = []
    real = subprocess.run

    def record(argv, *a, **k):
        ran.append(list(argv))
        return real(argv, *a, **k)

    monkeypatch.setattr(subprocess, "run", record)
    got = sdlc.retro.read_host(host)
    assert isinstance(got, dict) and len(got["closed"]) == 2
    allowed = {"log", "show", "rev-parse", "symbolic-ref", "for-each-ref"}
    assert ran
    for argv in ran:
        assert argv[0] == "git" and argv[1] == "-C", argv
        assert Path(argv[2]).resolve() == host.resolve(), argv
        assert argv[3] in allowed, argv


def test_an_unreadable_host_is_counted_not_fatal(tmp_path: Path, monkeypatch, capsys) -> None:
    """R5: a missing path, a folder that isn't a repo, a repo with no base branch and one that
    raises are each counted by their word, never a failed retro or a zero."""
    plain = tmp_path / "plain"
    plain.mkdir()
    nobase = tmp_path / "nobase"
    nobase.mkdir()
    _git(nobase, "init", "-q", "-b", "trunk")
    (nobase / "x").write_text("x\n", encoding="utf-8")
    _git(nobase, "add", "-A")
    _git(nobase, "commit", "-q", "-m", "init")
    broken = _host_b(tmp_path)
    listed = [tmp_path / "missing", plain, nobase, broken]
    root = _own(tmp_path, "".join(f"{p}\n" for p in listed))
    real = sdlc.closed_changes

    def raising(home, *a, **k):
        if Path(home).resolve() == broken.resolve():
            raise RuntimeError("boom")
        return real(home, *a, **k)

    monkeypatch.setattr(sdlc, "closed_changes", raising)
    read = _retro(root)["hosts"]["read"]
    assert read["listed"] == 4 and read["read"] == 0
    assert read["unreadable"] == {"missing": 1, "not-a-repo": 1, "no-base": 1, "failed": 1}
    assert sdlc.retro.hosts_figures(root, None)["all"]["closed"] is None
    assert sdlc.retro.cmd_retro(root) == 0
    assert "boom" not in capsys.readouterr().out


# ---------------------------------------------------------------- the figures (R6, R8)


def _listed(tmp_path: Path) -> tuple[Path, Path, Path]:
    a, b = _host_a(tmp_path), _host_b(tmp_path)
    own = tmp_path / "plugin"
    worktree = own / ".claude" / "worktrees" / "001-reopen-drafts"
    lines = [f"{a}", f"{b}", f"{own}", f"{worktree}", f"{a}/", f"{tmp_path / 'gone'}",
             f"!{tmp_path / 'never'}"]  # fmt: skip
    return _own(tmp_path, "\n".join(lines) + "\n"), a, b


def test_two_fixture_hosts_give_known_counts(tmp_path: Path) -> None:
    """R6: every count, over two hosts with known `Close`/`Drop` commits and trailers. 235 R14:
    a path under this repo's `.claude/worktrees/` is `own`, as the main checkout is."""
    root, _, _ = _listed(tmp_path)
    h = _retro(root)["hosts"]
    assert h["state"] == "read"
    read = h["read"]
    assert {k: read[k] for k in ("listed", "read", "own", "repeated", "excluded")} == {
        "listed": 6, "read": 2, "own": 2, "repeated": 1, "excluded": 1,
    }  # fmt: skip
    assert read["unreadable"] == {"missing": 1}
    assert read["unlisted"] == 0 and read["discovery"] == "read"
    assert read["note"] == sdlc.retro.HOST_NOTE
    assert read["unmeasured"] and all(isinstance(u["signal"], str) for u in read["unmeasured"])
    w = h["window"]
    assert (w["closed"], w["dropped"]) == (3, 1)
    assert w["by_way"] == {"factory": 1, "manual": 2, "unknown": 0}
    assert w["tiers"] == {"1": 2, "2": 1}
    assert w["dropped_at"] == {"build": 1}
    assert w["escapes"] == {"fixes": 0, "reworks": 1}
    assert w["prompts"] == 1
    groups = w["metrics"]["groups"]
    assert groups["tier 2, factory"]["median"]["stops"] == 4
    assert groups["tier 1, manual"]["changes"] == 2
    assert groups["tier 1, manual"]["median"]["stops"] == 13
    a = h["all"]
    assert (a["closed"], a["dropped"]) == (5, 1)
    assert a["by_way"] == {"factory": 1, "manual": 3, "unknown": 1}
    assert a["tiers"] == {"1": 3, "2": 1, "unknown": 1}
    assert a["escapes"] == {"fixes": 1, "reworks": 1}
    assert a["prompts"] == 4
    assert a["drop_share"] == 0.17
    assert a["metrics"]["groups"]["tier 1, manual"]["median"]["stops"] == 10
    assert h["busiest"] == {
        "closed": 3,
        "by_way": {
            "factory": {"n": 0, "stops": None, "elapsed": None},
            "manual": {"n": 2, "stops": 13, "elapsed": 120},
            "unknown": {"n": 0, "stops": None, "elapsed": None},
        },
    }
    assert h["versions"]["hosts"] == {"1.4.0": 1, sdlc.plugin_version(): 1}
    assert h["versions"]["behind"] == 1
    s = h["surface"]
    assert s["skills"] == {"sdlc:ship": {"hosts": 1, "runs": 2}}
    assert s["commands"] == {"sdlc.py:ship": 4}
    assert s["keys"] == {"commands.check": 1}
    assert s["templates"] == {"retro.md": 1}


def test_older_trailers_are_unmeasured_not_zero(tmp_path: Path) -> None:
    """R8: a `Close` with no trailers counts in `closed` and as `unknown`, never in a median; an
    intent under the old `work/` is tier `unknown`."""
    b = _host_b(tmp_path)
    root = _own(tmp_path, f"{b}\n")
    a = _retro(root)["hosts"]["all"]
    assert a["closed"] == 3 and a["by_way"]["unknown"] == 1
    assert a["tiers"] == {"1": 2, "unknown": 1}
    assert a["metrics"]["captured"] == 2 and a["metrics"]["uncaptured"] == 1
    assert a["metrics"]["groups"]["tier 1, manual"]["median"]["stops"] == 13


def test_an_empty_list_reads_no_host_and_shows_no_zero(tmp_path: Path) -> None:
    """A list of comments alone is read, with no host, and every figure null, never 0."""
    root = _own(tmp_path, "# none yet\n")
    h = _retro(root)["hosts"]
    assert h["state"] == "read" and h["read"]["listed"] == 0 and h["read"]["read"] == 0
    assert h["all"]["closed"] is None and h["window"]["closed"] is None
    assert h["busiest"] is None


# ---------------------------------------------------------------- nothing names a host (R7, R12)


def test_no_host_name_or_path_reaches_the_output(tmp_path: Path) -> None:
    """R7: no planted name, and no part of the tmp path, reaches `retro`'s JSON, the insights'
    JSON or the report."""
    root, _, _ = _listed(tmp_path)
    cfg = sdlc.load_config(root)[0]
    out = _dumped(sdlc.retro._lean_out(_retro(root), False)["hosts"])
    insights = _dumped(sdlc.retro.retro_insights(root, cfg, TODAY))
    report = sdlc.retro.retro_report(root, cfg, TODAY)
    for text in (out, insights, report):
        for secret in (*SECRETS, str(tmp_path), tmp_path.name):
            assert secret not in text, secret
    h = _retro(root)["hosts"]
    assert h["read"]["dropped_names"] == 0  # filtered before summing, never left to the guard


def test_the_last_guard_drops_a_name_the_filter_missed() -> None:
    """R7: a leaf string outside the vocabulary is dropped and counted, never shown."""
    words = {"build", "manual"}
    figures = {"a": ["build", SECRET_DIR], "b": {"c": "manual", "d": SECRET_TITLE, "e": 3}}
    kept, dropped = sdlc.retro._scrub(figures, words)
    assert kept == {"a": ["build"], "b": {"c": "manual", "e": 3}}
    assert dropped == 2


def test_host_figures_never_move_this_repos_figures(tmp_path: Path) -> None:
    """R12: everything outside `hosts` is the same with a list as without one, the report's
    `## Indicators` block included (235 R16), which holds rows here, not the no-rows sentence."""
    root, _, _ = _listed(tmp_path)
    (root / "rows.jsonl").write_text(
        '{"name": "cycles", "value": 2}\n', encoding="utf-8", newline="\n"
    )
    (root / ".sdlc" / "config.toml").write_text(
        '[retro]\nindicators = ["cat rows.jsonl"]\n', encoding="utf-8", newline="\n"
    )

    def indicators() -> str:
        report = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], TODAY)
        return report.split("## Indicators\n", 1)[1].split("\n## ", 1)[0]

    with_list, with_block = _retro(root), indicators()
    (root / ".sdlc" / "hosts.local").unlink()
    without, without_block = _retro(root), indicators()
    assert with_list.pop("hosts")["state"] == "read"
    assert without.pop("hosts")["state"] == "unmeasured"
    assert _dumped(with_list) == _dumped(without)
    assert "| cycles | — | 2 |" in with_block and sdlc.retro.NO_INDICATORS not in with_block
    assert with_block == without_block


def test_an_excluded_host_is_never_read(tmp_path: Path) -> None:
    """235 R15: of two real hosts listed, the one a `!` line excludes is counted `excluded` and
    never read: the figures are the other's alone."""
    a, b = _host_a(tmp_path), _host_b(tmp_path)
    root = _own(tmp_path, f"{a}\n{b}\n!{b}\n")
    h = _retro(root)["hosts"]
    assert (h["read"]["read"], h["read"]["excluded"]) == (1, 1), h["read"]
    (root / ".sdlc" / "hosts.local").write_text(f"{a}\n", encoding="utf-8", newline="\n")
    alone = _retro(root)["hosts"]
    assert alone["read"]["read"] == 1
    assert _dumped(h["window"]) == _dumped(alone["window"])
    assert _dumped(h["all"]) == _dumped(alone["all"])


# ---------------------------------------------------------------- discovery (R9)


def test_discovery_counts_unlisted_installs(tmp_path: Path, monkeypatch) -> None:
    """R9: `sdlc` installs at project or local scope, less this repo, its worktrees, the listed
    and the excluded, counted; a failed discovery is `unmeasured`, its reason never shown."""
    root, a, _ = _listed(tmp_path)
    secret = tmp_path / "zebracorp-unlisted"

    def row(project, scope="project", plugin="sdlc"):
        return {"plugin": plugin, "scope": scope, "version": "1.4.0",
                "project": Path(project).resolve().as_posix(), "local_source": False,
                "applies": False}  # fmt: skip

    rows = [
        row(secret), row(secret, "local"), row(tmp_path / "other", "local"), row(a),
        row(root), row(root / ".claude" / "worktrees" / "208-x"), row(tmp_path / "never"),
        row(tmp_path / "third", "user"), row(tmp_path / "fourth", plugin="sdlc-factory"),
    ]  # fmt: skip
    monkeypatch.setattr(sdlc, "plugin_installs", lambda home: (rows, None))
    h = _retro(root)["hosts"]
    assert h["read"]["unlisted"] == 2 and h["read"]["discovery"] == "read"
    assert str(secret) not in _dumped(h) and "zebracorp-unlisted" not in _dumped(h)
    why = f"claude plugin list failed: {secret}"
    monkeypatch.setattr(sdlc, "plugin_installs", lambda home: ([], why))
    h = _retro(root)["hosts"]
    assert h["read"]["unlisted"] is None and h["read"]["discovery"] == "unmeasured"
    assert "zebracorp-unlisted" not in _dumped(h)


# ---------------------------------------------------------------- the command (R10)


def test_hosts_command_prints_paths_and_writes_nothing(tmp_path: Path, monkeypatch, capsys):
    """R10: each listed host's state and each unlisted install's path with its two lines to
    append; nothing in this repo or a host changes."""
    root, a, b = _listed(tmp_path)
    unlisted = (tmp_path / "zebracorp-unlisted").resolve().as_posix()
    rows = [{"plugin": "sdlc", "scope": "project", "version": "1.4.0", "project": unlisted,
             "local_source": False, "applies": False}]  # fmt: skip
    monkeypatch.setattr(sdlc, "plugin_installs", lambda home: (rows, None))
    before = [_git(p, "status", "--porcelain") + _git(p, "rev-parse", "HEAD") for p in (root, a, b)]
    assert sdlc.retro.cmd_hosts(root) == 0
    out = capsys.readouterr().out
    assert f"read: {a.resolve().as_posix()}" in out
    assert f"read: {b.resolve().as_posix()}" in out
    assert f"missing: {(tmp_path / 'gone').resolve().as_posix()}" in out
    assert f"unlisted: {unlisted}" in out
    assert f"\n    {unlisted}\n" in out and f"\n    !{unlisted}\n" in out
    after = [_git(p, "status", "--porcelain") + _git(p, "rev-parse", "HEAD") for p in (root, a, b)]
    assert after == before


def test_hosts_command_outside_the_plugin_reads_nothing(tmp_path: Path, capsys, installs):
    root = _repo(tmp_path / "not-the-plugin")
    assert sdlc.retro.cmd_hosts(root) == 0
    assert "only in the plugin's own repo" in capsys.readouterr().out
    assert installs == []


@pytest.mark.portable
def test_hosts_is_not_read_only() -> None:
    """R10: a command no model runs unprompted: in neither `READ_ONLY` nor `ALLOW_RULES`."""
    assert "hosts" in sdlc.COMMANDS
    assert "hosts" not in sdlc.READ_ONLY
    assert not [r for r in sdlc.ALLOW_RULES if " hosts " in r]


# ---------------------------------------------------------------- the report (R11)


def test_the_report_has_a_hosts_section(tmp_path: Path) -> None:
    """R11: the counts, the note and the tables in the plugin's own repo; one line elsewhere."""
    root, _, _ = _listed(tmp_path)
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], TODAY)
    section = text.split("## Hosts\n", 1)[1]
    assert "2 host repos read of 6 listed" in section
    assert "1 couldn't be read" in section and "0 installed repos not in the host list" in section
    assert sdlc.retro.HOST_NOTE in section
    assert "| By hand |" in section and "| Factory |" in section
    assert "Factory-built changes, all time: 1." in section
    assert "| 1.4.0 | 1 |" in section
    host = _repo(tmp_path / "a-host")
    text = sdlc.retro.retro_report(host, sdlc.load_config(host)[0], TODAY)
    assert text.split("## Hosts\n", 1)[1].strip() == sdlc.retro.HOSTS_ELSEWHERE


def test_a_template_without_hosts_renders_as_before(tmp_path: Path) -> None:
    """R11: an override without `{{hosts}}` renders as it did, and `{{hosts}}` is no template
    read, so it isn't breaking."""
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    old = template.replace("\n\n## Hosts\n\n{{hosts}}", "")
    assert old != template and "{{hosts}}" not in old
    root = _repo(tmp_path / "a-host", {".sdlc/templates/retro.md": old})
    text = sdlc.retro.retro_report(root, sdlc.load_config(root)[0], TODAY)
    assert "## Hosts" not in text and "{{" not in text
    assert "{{hosts}}" not in sdlc.TEMPLATE_READS["retro.md"].get("placeholders", ())


# ---------------------------------------------------------------- the insights (R13)

SLICES = {
    "Value": {"all", "versions"},
    "Speed": {"window", "busiest"},
    "Quality": {"window"},
    "Autonomy": {"window"},
    "Cost": {"window"},
    "Simplicity": {"surface"},
    "Tradeoffs": {"all"},
}
WINDOW_SLICES = {
    "Speed": {"by_way", "metrics"},
    "Quality": {"escapes", "dropped_at"},
    "Autonomy": {"prompts"},
    "Cost": {"metrics"},
}


def test_insight_bundles_carry_host_slices(tmp_path: Path) -> None:
    """R13: every bundle carries `hosts.read`, and each pillar its own slices and no other's."""
    root, _, _ = _listed(tmp_path)
    got = sdlc.retro.retro_insights(root, sdlc.load_config(root)[0], TODAY)
    seen = set()
    for q in got["questions"]:
        hosts = q["data"]["hosts"]
        assert hosts["state"] == "read" and hosts["read"]["read"] == 2, q["title"]
        assert set(hosts) - {"state", "read"} == SLICES[q["pillar"]], q["title"]
        if q["pillar"] in WINDOW_SLICES:
            assert set(hosts["window"]) == WINDOW_SLICES[q["pillar"]], q["title"]
        seen.add(q["pillar"])
    assert seen == set(SLICES)
