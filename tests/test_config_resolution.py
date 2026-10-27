"""`sdlc.py config` and templates: what a host sets, and what it gets when it sets nothing.

A host's specifics reach the skills only through `config`, so its two failure modes are the ones to
pin: a setting silently ignored (a typo'd key), and a default silently standing in for a host file
that should have been there.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "sdlc_config_under_test", ROOT / "scripts" / "sdlc.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()


def _config(root: Path, capsys) -> tuple[int, dict]:
    code = sdlc.cmd_config(root)
    return code, json.loads(capsys.readouterr().out)


def test_a_host_with_nothing_gets_null_commands_and_the_plugins_files(tmp_path: Path, capsys):
    code, out = _config(tmp_path, capsys)
    assert code == 0
    assert out["config_file"] is None
    assert set(out["commands"]) == set(sdlc.CONFIG_KEYS["commands"])
    assert all(v is None for v in out["commands"].values())
    assert {t["source"] for t in out["templates"].values()} == {"plugin"}
    assert out["docs"]["review"]["source"] == "plugin"
    assert Path(out["docs"]["review"]["path"]) == sdlc.GUIDE_DIR / "review.md"
    assert Path(out["docs"]["review"]["path"]).is_file()
    assert out["docs"]["review"]["guide"] is None, "the guide alone, read once"
    process = out["docs"]["process"]
    assert (process["exists"], process["layout"]) == (False, "answers")
    assert Path(process["guide"]) == sdlc.GUIDE_DIR / "process.md", "the guide with no answers"


def test_a_missing_policy_doc_is_reported_not_defaulted(tmp_path: Path, capsys):
    _, out = _config(tmp_path, capsys)
    assert out["docs"]["policy"] == {"path": "CLAUDE.md", "exists": False, "source": "host"}
    assert [d["path"] for d in out["docs"]["context"]] == [
        "CLAUDE.md",
        ".claude/CLAUDE.md",
        "AGENTS.md",
    ]
    assert not any("docs.context" in w for w in out["warnings"]), "a repo has one, not all"
    assert "docs.policy: CLAUDE.md doesn't exist" in out["warnings"]


def test_the_process_docs_default_to_sdlc(tmp_path: Path, capsys):
    _, out = _config(tmp_path, capsys)
    for key, name in (
        ("process", "SDLC"),
        ("direction", "DIRECTION"),
        ("project", "PROJECT"),
        ("product", "PRODUCT"),
    ):
        assert out["docs"][key]["path"] == f".sdlc/{name}.md", key
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "REVIEW.md").write_text("# review\n", encoding="utf-8")
    _, out = _config(tmp_path, capsys)
    assert out["docs"]["review"] == {
        "path": ".sdlc/REVIEW.md",
        "exists": True,
        "source": "host",
        "layout": "full",
        "guide": None,
    }


def test_the_policy_is_agents_md_only_without_a_claude_md(tmp_path: Path, capsys):
    (tmp_path / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    cfg, _, _ = sdlc.load_config(tmp_path)
    assert cfg["docs"]["policy"] == "AGENTS.md"
    _, out = _config(tmp_path, capsys)
    assert not any("docs.policy" in w for w in out["warnings"])

    (tmp_path / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    cfg, _, _ = sdlc.load_config(tmp_path)
    assert cfg["docs"]["policy"] == "CLAUDE.md", "a host with a CLAUDE.md resolves as before"

    (tmp_path / "CLAUDE.md").unlink()
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "config.toml").write_text(
        '[docs]\npolicy = "CLAUDE.md"\n', encoding="utf-8"
    )
    cfg, _, _ = sdlc.load_config(tmp_path)
    assert cfg["docs"]["policy"] == "CLAUDE.md", "named by the host, so reported missing"


def test_host_settings_and_files_win(tmp_path: Path, capsys):
    host = tmp_path / ".sdlc"
    (host / "templates").mkdir(parents=True)
    (host / "templates" / "intent.md").write_text("---\nid: NNN\n---\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (host / "REVIEW.md").write_text("# review\n", encoding="utf-8")
    (tmp_path / "docs" / "conventions.md").write_text("# conventions\n", encoding="utf-8")
    (host / "config.toml").write_text(
        '[commands]\ncheck = "make check"\nbuild_when = "^src/"\n'
        '[docs]\nread_before_design = ["docs/conventions.md"]\nexplore = "/db:explore"\n'
        'context = ["docs/conventions.md"]\n',
        encoding="utf-8",
    )
    code, out = _config(tmp_path, capsys)
    assert code == 0
    assert out["config_file"] == ".sdlc/config.toml"
    assert out["commands"]["check"] == "make check"
    assert out["commands"]["build_when"] == "^src/"
    assert out["commands"]["scan"] is None
    assert out["docs"]["explore"] == "/db:explore"
    assert out["docs"]["review"] == {
        "path": ".sdlc/REVIEW.md",
        "exists": True,
        "source": "host",
        "layout": "full",
        "guide": None,
    }
    assert out["docs"]["read_before_design"] == [
        {"path": "docs/conventions.md", "exists": True, "source": "host"}
    ]
    assert out["docs"]["context"] == [
        {"path": "docs/conventions.md", "exists": True, "source": "host"}
    ]
    assert out["templates"]["intent.md"]["source"] == "host"
    assert out["templates"]["spec.md"]["source"] == "plugin"


def test_the_direction_doc_resolves_and_isnt_missed_before_the_first_retro(tmp_path: Path, capsys):
    _, out = _config(tmp_path, capsys)
    assert out["docs"]["direction"] == {
        "path": ".sdlc/DIRECTION.md",
        "exists": False,
        "source": "host",
    }
    assert not any("docs.direction" in w for w in out["warnings"])
    assert out["templates"]["direction.md"]["source"] == "plugin"
    assert Path(out["templates"]["direction.md"]["path"]).is_file()

    host = tmp_path / ".sdlc"
    (host / "templates").mkdir(parents=True)
    (host / "templates" / "direction.md").write_text("# Where we're going\n", encoding="utf-8")
    (host / "config.toml").write_text('[docs]\ndirection = "ROADMAP.md"\n', encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
    _, out = _config(tmp_path, capsys)
    assert out["docs"]["direction"] == {"path": "ROADMAP.md", "exists": True, "source": "host"}
    assert out["templates"]["direction.md"]["source"] == "host"


def test_retro_after_releases_is_a_whole_number(tmp_path: Path, capsys):
    _, out = _config(tmp_path, capsys)
    assert out["retro"] == {"after_releases": 2, "evidence": []}
    host = tmp_path / ".sdlc"
    host.mkdir()
    (host / "config.toml").write_text("[retro]\nafter_releases = 3\n", encoding="utf-8")
    _, out = _config(tmp_path, capsys)
    assert out["retro"]["after_releases"] == 3
    assert not any("retro" in w for w in out["warnings"])
    for bad in ('"3"', "-1", "true", "2.5"):
        (host / "config.toml").write_text(f"[retro]\nafter_releases = {bad}\n", encoding="utf-8")
        _, out = _config(tmp_path, capsys)
        assert out["retro"]["after_releases"] == 2, bad
        assert "retro.after_releases must be a whole number, 0 or more" in out["warnings"], bad


def test_metrics_reads_transcripts_by_default_and_a_host_can_turn_it_off(tmp_path: Path, capsys):
    _, out = _config(tmp_path, capsys)
    assert out["metrics"] == {"transcripts": True, "idle_minutes": 30, "stop_allowance": 1}
    host = tmp_path / ".sdlc"
    host.mkdir()
    toml = host / "config.toml"
    toml.write_text("[metrics]\ntranscripts = false\nidle_minutes = 45\nstop_allowance = 0\n")
    _, out = _config(tmp_path, capsys)
    assert out["metrics"] == {"transcripts": False, "idle_minutes": 45, "stop_allowance": 0}
    assert not any("metrics" in w for w in out["warnings"])
    toml.write_text('[metrics]\ntranscripts = "no"\nidle_minutes = 0\nstop_allowance = -1\n')
    _, out = _config(tmp_path, capsys)
    assert out["metrics"]["transcripts"] is True and out["metrics"]["idle_minutes"] == 30
    assert out["metrics"]["stop_allowance"] == 1
    assert "metrics.stop_allowance must be a whole number, 0 or more" in out["warnings"]
    assert "metrics.transcripts must be true or false" in out["warnings"]
    assert "metrics.idle_minutes must be a whole number, 1 or more" in out["warnings"]


def test_a_review_in_work_is_read_in_the_checkout_it_runs_in(tmp_path: Path, capsys):
    """.sdlc/work/ is committed, so a review kept there (the default until it moved to docs/) is in
    every checkout, and a worktree reads its own copy, at a path relative to it."""
    root = tmp_path / "repo"
    (root / ".sdlc" / "work").mkdir(parents=True)
    (root / ".sdlc" / "work" / "REVIEW.md").write_text("# review\n", encoding="utf-8")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[docs]\nreview = ".sdlc/work/REVIEW.md"\n')
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "init"], check=True)
    tree = tmp_path / "side"
    subprocess.run([*git, "worktree", "add", "-q", "-b", "side", str(tree)], check=True)

    code, out = _config(tree, capsys)
    assert code == 0
    assert out["docs"]["review"] == {
        "path": ".sdlc/work/REVIEW.md",
        "exists": True,
        "source": "host",
        "layout": "full",
        "guide": None,
    }
    assert out["work"] == {
        "dir": str(tree / ".sdlc" / "work"),
        "rel": ".sdlc/work",
        "ignored": False,
        "register": str(tree / ".sdlc" / "work" / "inbox.md"),
    }


def test_an_unknown_key_or_wrong_type_is_a_warning(tmp_path: Path, capsys):
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "config.toml").write_text(
        '[commands]\nbuld = "make build"\nscan = 3\n[extras]\nx = 1\n'
        '[docs]\nread_before_design = "docs/one.md"\n',
        encoding="utf-8",
    )
    code, out = _config(tmp_path, capsys)
    assert code == 0
    assert "unknown key commands.buld" in out["warnings"]
    assert "commands.scan must be a string" in out["warnings"]
    assert "unknown section [extras]" in out["warnings"]
    assert "docs.read_before_design must be a list of paths" in out["warnings"]
    assert out["commands"]["build"] is None and out["commands"]["scan"] is None


def test_the_release_section_resolves_with_its_defaults(tmp_path: Path, capsys):
    code, out = _config(tmp_path, capsys)
    assert code == 0
    assert out["release"] == {
        "version_files": [],
        "tag": "v{version}",
        "changelog": None,
        "after_bump": None,
        "prepare": None,
        "remote": "origin",
        "publish": None,
        "deprecations": ".sdlc/deprecations.toml",
    }
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "config.toml").write_text(
        '[release]\nversion_files = ["pkg.json"]\npublish = "make upload V={version}"\n',
        encoding="utf-8",
    )
    out = _config(tmp_path, capsys)[1]
    assert out["release"]["version_files"] == ["pkg.json"]
    assert out["release"]["publish"] == "make upload V={version}"
    (tmp_path / ".sdlc" / "config.toml").write_text(
        '[release]\nversion_files = "pkg.json"\n', encoding="utf-8"
    )
    out = _config(tmp_path, capsys)[1]
    assert "release.version_files must be a list of paths" in out["warnings"]
    assert out["release"]["version_files"] == []


def test_a_config_that_wont_parse_exits_1(tmp_path: Path, capsys):
    (tmp_path / ".sdlc").mkdir(exist_ok=True)
    (tmp_path / ".sdlc" / "config.toml").write_text("[commands\n", encoding="utf-8")
    code, out = _config(tmp_path, capsys)
    assert code == 1
    assert any("won't parse" in w for w in out["warnings"])


def test_new_scaffolds_from_the_host_template(tmp_path: Path, capsys, monkeypatch):
    (tmp_path / ".sdlc" / "templates").mkdir(parents=True)
    (tmp_path / ".sdlc" / "templates" / "intent.md").write_text(
        "---\nid: NNN\nslug: SLUG\ntier: 1\nstage: plan\ncreated: YYYY-MM-DD\n"
        "updated: YYYY-MM-DD\n---\n\n# NNN — TITLE\n\nHOST PROMPT\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sdlc, "_used", lambda root: [])
    assert sdlc.cmd_new(tmp_path, "thing", 1, None) == 0
    written = (tmp_path / ".sdlc" / "work" / "001-thing" / "intent.md").read_text(encoding="utf-8")
    assert "HOST PROMPT" in written and "# 001 — thing" in written
    assert "(host template)" in capsys.readouterr().out


def test_new_falls_back_to_the_plugin_template(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(sdlc, "_used", lambda root: [])
    assert sdlc.cmd_new(tmp_path, "thing", 2, None) == 0
    for name in ("intent.md", "spec.md", "plan.md"):
        assert (tmp_path / ".sdlc" / "work" / "001-thing" / name).is_file()
    assert "(plugin template)" in capsys.readouterr().out


def test_the_plugin_intent_keeps_the_sections_hosts_mirror():
    """A host may copy the intent's section list into tools of its own, so the default template
    keeps the five sections plus Approach, in order."""
    text = (sdlc.TEMPLATE_DIR / "intent.md").read_text(encoding="utf-8")
    headings = [ln[3:] for ln in text.splitlines() if ln.startswith("## ")]
    assert headings == [
        "Problem",
        "Outcome",
        "Affected",
        "Constraints",
        "Open questions",
        "Approach",
    ]


# ── 018: the base branch ─────────────────────────────────────────────────────────────────────


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _repo_on(root: Path, branch: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", branch)
    _git(root, "commit", "-q", "--allow-empty", "-m", "init")
    return root


def _with_origin(tmp_path: Path, branch: str) -> Path:
    """A clone of a repo whose only branch is `branch`, so `origin/HEAD` names it."""
    _repo_on(tmp_path / "upstream", branch)
    _git(tmp_path, "clone", "-q", str(tmp_path / "upstream"), str(tmp_path / "repo"))
    return tmp_path / "repo"


def test_the_base_is_main_when_there_is_one(tmp_path: Path, capsys):
    _, out = _config(_repo_on(tmp_path, "main"), capsys)
    assert out["git"] == {"base": "main", "base_source": "detected"}


def test_with_no_main_the_base_is_the_branch_origin_head_names(tmp_path: Path, capsys):
    _, out = _config(_with_origin(tmp_path, "master"), capsys)
    assert out["git"] == {"base": "master", "base_source": "detected"}


def test_with_no_main_and_no_origin_the_base_is_unset(tmp_path: Path, capsys):
    root = _repo_on(tmp_path, "master")
    _, out = _config(root, capsys)
    assert out["git"] == {"base": None, "base_source": "unset"}
    assert "no base branch" in sdlc.trunk_refusal(root, None)
    assert any(w.startswith("git.base: no base branch") for w in out["warnings"])


def test_status_reports_a_missing_base_and_check_doesnt(tmp_path: Path, capsys, monkeypatch):
    """Status says so, since every change would refuse to start; `check` is a gate, and stays
    green for a repo that simply has no commit on `main` yet."""
    import sys

    root = _repo_on(tmp_path, "master")
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "status"])
    capsys.readouterr()
    sdlc.main()
    assert "git.base: no base branch" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["sdlc.py", "check", "--strict"])
    assert sdlc.main() == 0
    assert "no base branch" not in capsys.readouterr().out


def test_the_configured_base_wins_over_one_detected(tmp_path: Path, capsys):
    root = _repo_on(tmp_path, "main")
    _git(root, "branch", "trunk")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[git]\nbase = "trunk"\n', encoding="utf-8")
    _, out = _config(root, capsys)
    assert out["git"] == {"base": "trunk", "base_source": "config"}
    assert sdlc.trunk_refusal(root, "trunk") is None
    assert "'gone' doesn't exist here" in sdlc.trunk_refusal(root, "gone")


def test_a_base_that_isnt_a_string_is_a_warning(tmp_path: Path, capsys):
    root = _repo_on(tmp_path, "main")
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text("[git]\nbase = 1\n", encoding="utf-8")
    _, out = _config(root, capsys)
    assert "git.base must be a string" in out["warnings"]
    assert out["git"]["base"] == "main"


def test_an_answers_doc_names_the_guide_to_read_before_it(tmp_path: Path, capsys):
    """Setup's record decides the layout, never the doc's text: recorded as answers, a host doc
    comes with the guide's path; without a record, it is a full copy read alone."""
    host = tmp_path / ".sdlc"
    host.mkdir()
    (host / "SDLC.md").write_text("# Process\n", encoding="utf-8")
    _, out = _config(tmp_path, capsys)
    assert (out["docs"]["process"]["layout"], out["docs"]["process"]["guide"]) == ("full", None)
    record = {"docs": {"process": {"path": ".sdlc/SDLC.md", "layout": "answers"}}}
    (host / "setup.json").write_text(json.dumps(record), encoding="utf-8")
    _, out = _config(tmp_path, capsys)
    assert out["docs"]["process"]["layout"] == "answers"
    assert Path(out["docs"]["process"]["guide"]) == sdlc.GUIDE_DIR / "process.md"
