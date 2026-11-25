"""`sdlc.py update` and the SessionStart hook that runs it (206): whether a newer release is out,
the one line a session and `status` show, and the exact steps a host runs to take it.

The check is one `git ls-remote` on the running manifest's `repository` and one
`claude plugin list --json`, cached a day in the git common dir. Here the repository is a bare
repo in `tmp_path` and `claude` is a fake on PATH printing `fixtures/plugin-list.json`, the shape
Claude Code printed when it was recorded, so nothing reaches the network.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uv_run import uv_script  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "plugin-list.json"


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_update", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

LINE = "sdlc 1.11.0 is out (this session runs 1.10.0): /sdlc:update"
STEPS = [
    "claude plugin marketplace update sdlc",
    "claude plugin update sdlc@sdlc --scope user",
    "claude plugin update sdlc@sdlc --scope project",
    "claude plugin update sdlc-factory@sdlc --scope project",
    "restart Claude Code",
    "/sdlc:setup",
    "commit what setup names",
]


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _rows(repo: Path, other: Path) -> list[dict]:
    """The recorded rows, their neutral paths made this test's."""
    text = FIXTURE.read_text(encoding="utf-8")
    for key, value in (("@REPO@", repo), ("@OTHER@", other), ("@HOME@", other.parent / "home")):
        text = text.replace(key, value.resolve().as_posix())
    return json.loads(text)["rows"]


@pytest.fixture
def host(tmp_path: Path) -> Path:
    root = tmp_path / "host"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    (root / "README.md").write_text("a host\n", encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


@pytest.fixture
def releases(tmp_path: Path) -> Path:
    """A bare repo tagged as the plugin's releases are, and one tag that isn't a version."""
    src, bare = tmp_path / "src", tmp_path / "releases.git"
    src.mkdir()
    _git(src, "init", "-q", "-b", "main")
    _git(src, "commit", "-q", "--allow-empty", "-m", "one")
    for tag in ("v1.10.0", "v1.11.0", "docs-preview"):
        _git(src, "tag", tag)
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(src, "push", "-q", str(bare), "--tags")
    return bare


def _manifest(where: Path, version: str, repository: str) -> None:
    (where / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    data = {"name": "sdlc", "version": version, "repository": repository}
    (where / ".claude-plugin" / "plugin.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def plugin(tmp_path: Path, releases: Path, monkeypatch) -> Path:
    """The running copy: Claude Code's cached copy at 1.10.0, no `.git`."""
    where = tmp_path / "plugin"
    _manifest(where, "1.10.0", str(releases))
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", where)
    return where


FAKE_CLAUDE = r"""#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_CLAUDE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
if sys.argv[1:] != ["plugin", "list", "--json"]:
    sys.exit(2)
print(open(os.environ["FAKE_CLAUDE_ROWS"], encoding="utf-8").read())
"""


@pytest.mark.portable
def test_the_fake_claude_opens_its_files_as_utf8() -> None:
    """235 R13: every `open(` in the fake names its encoding, never the locale's code page."""
    calls = re.findall(r"\bopen\(([^)]*\))", FAKE_CLAUDE)
    assert calls and all('encoding="utf-8"' in c for c in calls), calls


@pytest.fixture
def claude(tmp_path: Path, host: Path, monkeypatch) -> dict:
    """A fake `claude` first on PATH, printing the recorded rows for `host`; its calls logged."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(FAKE_CLAUDE, encoding="utf-8")
    fake.chmod(0o755)
    rows, log = tmp_path / "rows.json", tmp_path / "claude.log"
    rows.write_text(json.dumps(_rows(host, tmp_path / "other")), encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_ROWS", str(rows))
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return {"rows": rows, "log": log, "bin": bin_dir}


def _calls(log: Path) -> list:
    return [json.loads(ln) for ln in log.read_text().splitlines()] if log.is_file() else []


@pytest.fixture
def argvs(monkeypatch) -> list:
    """Every argv the script runs, recorded, and still run."""
    seen: list = []
    real = subprocess.run

    def run(argv, *a, **kw):
        seen.append([str(x) for x in argv])
        return real(argv, *a, **kw)

    monkeypatch.setattr(sdlc.subprocess, "run", run)
    return seen


def _network(argvs: list) -> list:
    """The calls that reach for a release or the installs: `ls-remote`, and `claude` itself."""
    return [a for a in argvs if "ls-remote" in a or Path(a[0]).name.startswith("claude")]


def _hook(host: Path, capsys) -> str:
    assert sdlc.cmd_update(host, sdlc.main_root(host), "hook") == 0
    return capsys.readouterr().out


# ---------------------------------------------------------------- the pure parts (portable)


@pytest.mark.portable
def test_parse_installs_reads_the_recorded_rows(tmp_path: Path) -> None:
    """R6: only sdlc and sdlc-factory from the `sdlc` marketplace, sdlc first, user before
    project before local; applies here at user scope, or a project path that is this repo's."""
    repo, other = tmp_path / "host", tmp_path / "other"
    repo.mkdir()
    found = sdlc.parse_installs(_rows(repo, other), repo)
    got = [(i["plugin"], i["scope"], i["version"], i["applies"], i["local_source"]) for i in found]
    assert got == [
        ("sdlc", "user", "1.10.0", True, False),
        ("sdlc", "project", "1.10.0", True, False),
        ("sdlc", "project", "1.8.0", False, False),  # a worktree of this repo
        ("sdlc", "project", "1.9.0", False, False),  # another repo
        ("sdlc", "local", "1.9.0", False, True),  # another repo, read from a folder
        ("sdlc-factory", "project", "1.10.0", True, False),
    ]
    assert found[1]["project"] == repo.resolve().as_posix()


@pytest.mark.portable
def test_a_project_path_is_compared_resolved_never_as_text(tmp_path: Path) -> None:
    """R6: `host/.` and `host` are one folder."""
    repo = tmp_path / "host"
    repo.mkdir()
    row = {"id": "sdlc@sdlc", "version": "1.0.0", "scope": "project", "projectPath": f"{repo}/."}
    assert sdlc.parse_installs([row], repo)[0]["applies"]
    assert sdlc.parse_installs("not a list", repo) == []


def _data(repo: Path, tmp_path: Path, latest: str | None = "1.11.0", **more) -> dict:
    installs = sdlc.parse_installs(_rows(repo, tmp_path / "other"), repo)
    return {"latest": latest, "installs": installs, "installs_reason": None, **more}


@pytest.mark.portable
def test_the_line_says_the_session_runs_an_older_copy(tmp_path: Path) -> None:
    """R3, the first form, character for character."""
    repo = tmp_path / "host"
    repo.mkdir()
    assert sdlc.update_line("1.10.0", _data(repo, tmp_path)) == LINE


@pytest.mark.portable
def test_the_line_names_each_stale_install_when_the_session_is_current(tmp_path: Path) -> None:
    """R3, the second form: the running copy is current, the installs here aren't."""
    repo = tmp_path / "host"
    repo.mkdir()
    assert sdlc.update_line("1.11.0", _data(repo, tmp_path)) == (
        "sdlc 1.11.0 is out (sdlc 1.10.0 at user scope, sdlc 1.10.0 at project scope, "
        "sdlc-factory 1.10.0 at project scope): /sdlc:update"
    )


@pytest.mark.portable
def test_the_line_is_silent_when_it_can_t_tell(tmp_path: Path) -> None:
    """No release found, no installs read, everything current, a downgrade, or sdlc here read
    from a folder: no line."""
    repo = tmp_path / "host"
    repo.mkdir()
    assert sdlc.update_line("1.10.0", _data(repo, tmp_path, latest=None)) is None
    assert sdlc.update_line("1.10.0", _data(repo, tmp_path, installs_reason="no claude")) is None
    assert sdlc.update_line("1.10.0", _data(repo, tmp_path, latest="1.10.0")) is None
    assert sdlc.update_line("1.12.0", _data(repo, tmp_path, latest="1.9.0")) is None
    local = [{"plugin": "sdlc", "scope": "local", "version": "1.0.0", "project": None,
              "local_source": True, "applies": True}]  # fmt: skip
    assert sdlc.update_line("1.0.0", {"latest": "1.11.0", "installs": local}) is None


@pytest.mark.portable
def test_installed_says_restart_first_over_a_newer_project_install(
    tmp_path: Path, monkeypatch
) -> None:
    """R9: the most specific install here wins; newer than the running copy is `true`."""
    repo = tmp_path / "host"
    repo.mkdir()
    _manifest(tmp_path / "plugin", "1.10.0", "x")
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "plugin")
    user = {"plugin": "sdlc", "scope": "user", "version": "1.10.0", "project": None,
            "local_source": False, "applies": True}  # fmt: skip
    project = user | {"scope": "project", "version": "1.11.0"}
    monkeypatch.setattr(sdlc, "plugin_installs", lambda home: ([user, project], None))
    found = sdlc.installed_check(repo)
    assert found["restart_first"] is True
    assert (found["installed"], found["scope"], found["running"]) == ("1.11.0", "project", "1.10.0")
    monkeypatch.setattr(sdlc, "plugin_installs", lambda home: ([user], None))
    assert sdlc.installed_check(repo)["restart_first"] is False


@pytest.mark.portable
def test_installed_is_null_without_claude(tmp_path: Path, monkeypatch) -> None:
    """R9: no `claude` on PATH can't tell, and says why."""
    repo = tmp_path / "host"
    repo.mkdir()
    _manifest(tmp_path / "plugin", "1.10.0", "x")
    monkeypatch.setattr(sdlc, "PLUGIN_DIR", tmp_path / "plugin")
    monkeypatch.setattr(sdlc.shutil, "which", lambda name: None)
    found = sdlc.installed_check(repo)
    assert found["restart_first"] is None and found["reason"] == "no claude on PATH"


@pytest.mark.portable
def test_update_is_not_read_only() -> None:
    """R10: it writes the cache and reaches the network, so setup never allows it unasked."""
    assert "update" not in sdlc.READ_ONLY
    assert not any(" update " in rule for rule in sdlc.ALLOW_RULES)


# ---------------------------------------------------------------- the check (fakes on PATH)


def test_hook_prints_the_line(host: Path, plugin: Path, claude: dict, capsys) -> None:
    """R2, R3: one JSON object whose `systemMessage` is the one line."""
    assert json.loads(_hook(host, capsys)) == {"systemMessage": LINE}


def test_one_check_a_day(host: Path, plugin: Path, claude: dict, argvs: list, capsys) -> None:
    """R4: the first run checks once and caches in the git common dir; a second the same day
    runs neither `git ls-remote` nor `claude`, and says the same."""
    first = _hook(host, capsys)
    assert len(_network(argvs)) == 2
    cache = Path(_git(host, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    data = json.loads((cache / "sdlc-update.json").read_text(encoding="utf-8"))
    assert data["latest"] == "1.11.0" and data["source"] == str(plugin.parent / "releases.git")
    argvs.clear()
    assert _hook(host, capsys) == first
    assert _network(argvs) == []
    assert _git(host, "status", "--porcelain") == "", "the cache dirties no checkout"


def test_a_stale_cache_is_checked_again(
    host: Path, plugin: Path, claude: dict, argvs: list, capsys
) -> None:
    """R4: a day old, the cache is checked again."""
    _hook(host, capsys)
    path = sdlc._update_cache_path(host)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["checked"] = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
    path.write_text(json.dumps(data), encoding="utf-8")
    argvs.clear()
    _hook(host, capsys)
    assert len(_network(argvs)) == 2


def test_a_failed_check_is_cached_as_null(
    tmp_path: Path, host: Path, plugin: Path, claude: dict, argvs: list, capsys
) -> None:
    """R4: offline is cached as `latest: null` with its reason, and retried tomorrow, not at
    the next session."""
    _manifest(plugin, "1.10.0", str(tmp_path / "nowhere.git"))
    assert _hook(host, capsys) == ""
    data = json.loads(sdlc._update_cache_path(host).read_text(encoding="utf-8"))
    assert data["latest"] is None and data["reason"].startswith("git ls-remote exited")
    argvs.clear()
    assert _hook(host, capsys) == ""
    assert _network(argvs) == []


def test_hook_is_silent_when_it_can_t_tell(
    tmp_path: Path, host: Path, plugin: Path, claude: dict, argvs: list, capsys, monkeypatch
) -> None:
    """R2: no `claude`, a failing `ls-remote`, outside a git repo: exit 0 and nothing printed,
    each time; and a check that raises says nothing either."""
    with monkeypatch.context() as m:
        m.setattr(sdlc.shutil, "which", lambda name: None)
        assert _hook(host, capsys) == ""
    sdlc._update_cache_path(host).unlink()
    with monkeypatch.context() as m:
        _manifest(plugin, "1.10.0", str(tmp_path / "nowhere.git"))
        assert _hook(host, capsys) == ""
    outside = tmp_path / "loose"
    outside.mkdir()
    argvs.clear()
    assert _hook(outside, capsys) == ""
    assert _network(argvs) == [], "outside a repo there is nowhere to cache, so no check"

    def broken(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(sdlc, "check_update", broken)
    assert _hook(host, capsys) == ""


def test_in_place_is_never_told(
    host: Path, plugin: Path, claude: dict, argvs: list, capsys
) -> None:
    """R5: a running copy with `.git` gets no line, no step and no network call, even from a
    fresh cache that would say a release is out."""
    _hook(host, capsys)
    (plugin / ".git").mkdir()
    argvs.clear()
    assert _hook(host, capsys) == ""
    assert sdlc.update_nudge(host) is None
    assert sdlc.cmd_update(host, host, None) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["in_place"] is True and report["steps"] == []
    assert _network(argvs) == []


def test_steps_in_order(tmp_path: Path, host: Path, plugin: Path, claude: dict, capsys) -> None:
    """R8: the marketplace, each stale install here (sdlc first, user before project), the
    restart, setup, the commit; another repo's install in `elsewhere`, never in a step, and this
    repo's worktrees in neither."""
    assert sdlc.cmd_update(host, host, None) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["steps"] == STEPS
    assert report["running"] == "1.10.0" and report["latest"] == "1.11.0"
    assert report["cwd"] == host.as_posix()
    other = (tmp_path / "other").resolve().as_posix()
    assert [(i["plugin"], i["scope"], i["project"]) for i in report["elsewhere"]] == [
        ("sdlc", "project", other)
    ]
    assert not any(other in s for s in report["steps"])
    assert report["restart_first"] is False
    assert len(report["installs"]) == 6


def test_no_steps_when_everything_is_current(
    host: Path, plugin: Path, claude: dict, capsys
) -> None:
    """R8: everything here at the latest release, nothing to run."""
    rows = json.loads(claude["rows"].read_text(encoding="utf-8"))
    for row in rows:
        row["version"] = "1.11.0"
    claude["rows"].write_text(json.dumps(rows), encoding="utf-8")
    _manifest(plugin, "1.11.0", str(plugin.parent / "releases.git"))
    sdlc.cmd_update(host, host, None)
    report = json.loads(capsys.readouterr().out)
    assert report["steps"] == [] and report["elsewhere"] == []


def test_update_refreshes_the_day_s_cache(
    host: Path, plugin: Path, claude: dict, argvs: list, capsys
) -> None:
    """R8: with no flag it checks now, ignoring the day's cache, and writes it."""
    _hook(host, capsys)
    argvs.clear()
    sdlc.cmd_update(host, host, None)
    capsys.readouterr()
    assert len(_network(argvs)) == 2


def test_installed_runs_no_network_and_writes_no_cache(
    host: Path, plugin: Path, claude: dict, argvs: list, capsys
) -> None:
    """R9: `claude plugin list` only."""
    assert sdlc.cmd_update(host, host, "installed") == 0
    found = json.loads(capsys.readouterr().out)
    assert found["restart_first"] is False and found["installed"] == "1.10.0"
    assert [a for a in argvs if "ls-remote" in a] == []
    assert not sdlc._update_cache_path(host).exists()


def test_status_reads_the_cache_alone(
    host: Path, plugin: Path, claude: dict, argvs, capsys
) -> None:
    """R7: status repeats the line from a fresh cache, and runs no `claude` and no
    `ls-remote`; a stale cache, or `latest: null`, shows nothing."""
    _hook(host, capsys)
    argvs.clear()
    assert sdlc.cli_status(host, host, argparse.Namespace(all=False)) == 0
    assert f"■ Update: {LINE}" in capsys.readouterr().out
    assert _network(argvs) == []
    path = sdlc._update_cache_path(host)
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(data | {"latest": None}), encoding="utf-8")
    assert sdlc.update_nudge(host) is None
    old = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    path.write_text(json.dumps(data | {"checked": old}), encoding="utf-8")
    assert sdlc.update_nudge(host) is None
    path.unlink()
    assert sdlc.update_nudge(host) is None


# ---------------------------------------------------------------- setup's line (213)


def _behind(host: Path, plugin: Path, recorded: str, running: str) -> None:
    """`host` set up by a plugin at `recorded`, a config key new since, and `running` now."""
    source = sdlc.release_source()
    (host / ".sdlc").mkdir(exist_ok=True)
    (host / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    _manifest(plugin, recorded, source)
    assert sdlc.cmd_record(host, [], False) == 0
    path = host / ".sdlc" / "setup.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["config_keys"].remove("metrics.stop_allowance")
    path.write_text(json.dumps(record), encoding="utf-8")
    _manifest(plugin, running, source)


def _no_release(host: Path) -> None:
    """The day's check, found no release: no release line to print."""
    data = {
        "checked": datetime.now(UTC).isoformat(),
        "source": sdlc.release_source(),
        "latest": None,
        "reason": "offline",
        "installs": [],
        "installs_reason": None,
    }
    sdlc._update_cache_path(host).write_text(json.dumps(data), encoding="utf-8")


SETUP_LINE = "sdlc setup: set up with 1.9.0, the plugin is 1.10.0  /sdlc:setup"


def test_hook_says_setup_is_behind(host: Path, plugin: Path, claude: dict, capsys) -> None:
    """R6: no release line, and setup behind with something to draft: setup's line."""
    _behind(host, plugin, "1.9.0", "1.10.0")
    _no_release(host)
    capsys.readouterr()
    assert json.loads(_hook(host, capsys)) == {"systemMessage": SETUP_LINE}


def test_hook_prefers_the_release_line(host: Path, plugin: Path, claude: dict, capsys) -> None:
    """R7: both are due: the release line alone, since `/sdlc:update`'s steps run setup."""
    _behind(host, plugin, "1.9.0", "1.10.0")
    capsys.readouterr()
    assert sdlc.setup_nudge(host), "setup is behind"
    assert _hook(host, capsys) == json.dumps({"systemMessage": LINE}) + "\n"


def test_hook_setup_half_never_fails_the_session(
    host: Path, plugin: Path, claude: dict, capsys, monkeypatch
) -> None:
    """R8: a setup half that raises says nothing and exits 0; a repo not set up says nothing."""
    _no_release(host)
    assert _hook(host, capsys) == "", "not set up"

    def broken(root):
        raise RuntimeError("boom")

    _behind(host, plugin, "1.9.0", "1.10.0")
    capsys.readouterr()
    monkeypatch.setattr(sdlc, "setup_nudge", broken)
    assert _hook(host, capsys) == ""


# ---------------------------------------------------------------- end to end, as the hook runs


def test_hook_end_to_end(tmp_path: Path, host: Path, releases: Path, claude: dict) -> None:
    """R13: the script as the hook runs it, from a copy of the plugin at 1.10.0, against the
    fake `claude` and the bare repo: the exact line, then the same line the same day with no
    second check (a tag pushed since is not seen)."""
    copy = tmp_path / "cached-plugin"
    shutil.copytree(
        ROOT / "scripts", copy / "scripts", ignore=shutil.ignore_patterns("__pycache__")
    )
    _manifest(copy, "1.10.0", str(releases))
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    script = copy / "scripts" / "sdlc.py"
    ran = uv_script(script, host, ["update", "--hook"], env, timeout=120)
    assert (ran.returncode, ran.stderr) == (0, "")
    assert json.loads(ran.stdout) == {"systemMessage": LINE}
    assert _calls(claude["log"]) == [["plugin", "list", "--json"]]
    src = tmp_path / "src"
    _git(src, "tag", "v1.12.0")
    _git(src, "push", "-q", str(releases), "--tags")
    again = uv_script(script, host, ["update", "--hook"], env, timeout=120)
    assert (again.returncode, json.loads(again.stdout)) == (0, {"systemMessage": LINE})
    assert len(_calls(claude["log"])) == 1, "the day's cache answered"


# ---------------------------------------------------------------- the docs say the same (R15)


@pytest.mark.portable
@pytest.mark.parametrize(
    ("rel", "heading"),
    [("README.md", "## Updating"), ("docs/REFERENCE.md", "## After an update")],
)
def test_docs_list_the_five_steps_in_order(rel: str, heading: str) -> None:
    """README *Updating* and REFERENCE.md *After an update* give the steps `update` prints, in
    its order, and say what the hook and `status` print."""
    text = (ROOT / rel).read_text(encoding="utf-8")
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    marks = [
        "claude plugin marketplace update sdlc",
        "claude plugin update sdlc@sdlc --scope",
        "restart Claude Code",
        "/sdlc:setup",
        "git commit",
    ]
    at = 0
    for mark in marks:  # each after the one before it: the order `update` prints them in
        at = section.find(mark, at)
        assert at >= 0, f"{mark} missing, or out of order"
    for said in ("/sdlc:update", "sdlc-factory@sdlc", "is out (this session runs", "status"):
        assert said in section, said


@pytest.mark.portable
def test_the_maps_name_the_hook_and_the_command() -> None:
    """R15: the feature map has the hook, the process map the skill's `update` call."""
    features = (ROOT / "docs" / "FEATURES.md").read_text(encoding="utf-8")
    assert "`hooks/hooks.json`" in features and "sdlc.py update" in features
    process = (ROOT / "docs" / "PROCESS.md").read_text(encoding="utf-8")
    assert "calls: config, update" in process and "update --installed" in process


@pytest.mark.portable
def test_reference_says_the_hook_carries_setup_s_line() -> None:
    """213 R11: *After an update* says the hook prints setup's line when there is no release line,
    and that status names the record only when setup has something to draft."""
    text = (ROOT / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    section = text.split("## After an update", 1)[1].split("\n## ", 1)[0]
    assert "sdlc setup: set up with" in section and "no release line" in section
    assert "drift" in section.split("**`.sdlc/setup.json`**", 1)[1].split("\n\n", 1)[0]
