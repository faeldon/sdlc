"""Setup's life after the first run: `record`, `drift`, `reset` and `uninstall`.

A host owns the docs setup copied, so a newer plugin proposes rather than overwrites: `drift`
compares each block of a host doc three ways (the default now, the hash `record` kept of the
default as copied, the host's text) to tell what the plugin changed from what the host did.
`uninstall` takes setup back out, and refuses while any change is live. Each test runs against a
small fake plugin (its defaults and templates swapped in), so a change to the real defaults can't
move what these assert.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_lifecycle", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

REVIEW = """# Review

> What the review reads.

## Pass 1

Look for these.

- **An error swallowed.** A bare except.
- **A test that can't fail.** It asserts nothing.

## Pass 2

The contract.
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


@pytest.fixture
def plugin(tmp_path: Path, monkeypatch) -> Path:
    """A fake plugin: its defaults and templates, at version 1.1.0."""
    where = tmp_path / "plugin"
    (where / "defaults").mkdir(parents=True)
    (where / "templates").mkdir()
    (where / "defaults" / "REVIEW.md").write_text(REVIEW, encoding="utf-8")
    for name in ("intent.md", "issue.md"):
        text = (ROOT / "templates" / name).read_text(encoding="utf-8")
        (where / "templates" / name).write_text(text, encoding="utf-8")
    monkeypatch.setattr(sdlc, "DEFAULTS_DIR", where / "defaults")
    monkeypatch.setattr(sdlc, "TEMPLATE_DIR", where / "templates")
    monkeypatch.setattr(sdlc, "plugin_version", lambda: "1.1.0")
    return where


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A host set up with a review copied from the fake plugin's default, committed."""
    root = tmp_path / "repo"
    (root / ".sdlc").mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    (root / ".sdlc" / "REVIEW.md").write_text(REVIEW, encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _default(plugin: Path, text: str) -> None:
    (plugin / "defaults" / "REVIEW.md").write_text(text, encoding="utf-8")


def _host(repo: Path, text: str) -> None:
    (repo / ".sdlc" / "REVIEW.md").write_text(text, encoding="utf-8")


def _classes(repo: Path) -> dict[str, list[str]]:
    return sdlc.drift(repo)["docs"]["review"]["classes"]


def _record(repo: Path, *created: str, line: bool = False) -> dict:
    assert sdlc.cmd_record(repo, list(created), line) == 0
    return json.loads((repo / ".sdlc" / "setup.json").read_text(encoding="utf-8"))


BULLET_A = "## Pass 1 > - **An error swallowed.**"
BULLET_B = "## Pass 1 > - **A test that can't fail.**"


# ── R1: the manifest ────────────────────────────────────────────────────────────────────────


def test_record_writes_the_manifest_shape(repo: Path, plugin: Path) -> None:
    manifest = _record(repo)
    assert set(manifest) == {
        "version", "config_keys", "docs", "templates", "created", "gitignore_line"
    }  # fmt: skip
    assert manifest["version"] == "1.1.0"
    assert "commands.check" in manifest["config_keys"]
    review = manifest["docs"]["review"]
    assert review["path"] == ".sdlc/REVIEW.md" and review["default"] == "REVIEW.md"
    assert list(review["units"]) == ["#", "## Pass 1", BULLET_A, BULLET_B, "## Pass 2"]
    assert set(manifest["templates"]) == {"intent.md", "issue.md"}
    assert "process" not in manifest["docs"], "a doc the host doesn't have has no base"


def test_record_twice_is_identical(repo: Path, plugin: Path) -> None:
    first = (_record(repo), (repo / ".sdlc" / "setup.json").read_text(encoding="utf-8"))
    second = (_record(repo), (repo / ".sdlc" / "setup.json").read_text(encoding="utf-8"))
    assert first == second


def test_record_keeps_created_and_ignore_line(repo: Path, plugin: Path) -> None:
    _record(repo, ".sdlc/config.toml", line=True)
    manifest = _record(repo, ".sdlc/REVIEW.md")
    assert manifest["created"] == [".sdlc/REVIEW.md", ".sdlc/config.toml"]
    assert manifest["gitignore_line"] is True


def test_record_refuses_without_a_config_or_with_a_path_outside(repo: Path, plugin) -> None:
    assert sdlc.cmd_record(repo, ["../elsewhere"], False) == 1
    (repo / ".sdlc" / "config.toml").unlink()
    assert sdlc.cmd_record(repo, [], False) == 1
    assert not (repo / ".sdlc" / "setup.json").exists()


# ── R2: three ways, block by block ──────────────────────────────────────────────────────────


def test_drift_current(repo: Path, plugin: Path) -> None:
    _record(repo)
    found = sdlc.drift(repo)
    assert set(_classes(repo)) == {"current"}
    assert found["refresh"] == [] and found["breaking"] == []


def test_drift_added(repo: Path, plugin: Path) -> None:
    _record(repo)
    _default(plugin, REVIEW.replace("\n## Pass 2", "- **Works only here.** A path.\n\n## Pass 2"))
    assert _classes(repo)["added"] == ["## Pass 1 > - **Works only here.**"]
    (refresh,) = sdlc.drift(repo)["refresh"]
    assert refresh["units"][0]["anchor"] == BULLET_B
    assert refresh["proposed"] == (plugin / "defaults" / "REVIEW.md").read_text(encoding="utf-8")


def test_drift_refreshed(repo: Path, plugin: Path) -> None:
    _record(repo)
    _default(plugin, REVIEW.replace("It asserts nothing.", "It asserts nothing real."))
    assert _classes(repo)["refreshed"] == [BULLET_B]
    (refresh,) = sdlc.drift(repo)["refresh"]
    assert "It asserts nothing real." in refresh["proposed"]


def test_drift_removed(repo: Path, plugin: Path) -> None:
    _record(repo)
    _default(plugin, REVIEW.replace("- **An error swallowed.** A bare except.\n", ""))
    assert _classes(repo)["removed"] == [BULLET_A]
    (refresh,) = sdlc.drift(repo)["refresh"]
    assert "An error swallowed" not in refresh["proposed"]
    assert "A test that can't fail" in refresh["proposed"]


def test_drift_conflict_both(repo: Path, plugin: Path) -> None:
    _record(repo)
    _host(repo, REVIEW.replace("A bare except.", "A bare except, or a pass."))
    _default(plugin, REVIEW.replace("A bare except.", "An except that hides it."))
    assert _classes(repo)["conflict"] == [BULLET_A]
    found = sdlc.drift(repo)
    assert found["refresh"] == []
    (conflict,) = [r for r in found["report"] if r["class"] == "conflict"]
    assert "or a pass" in conflict["host"] and "hides it" in conflict["default"]


def test_drift_conflict_removed_but_edited(repo: Path, plugin: Path) -> None:
    _record(repo)
    _host(repo, REVIEW.replace("A bare except.", "A bare except, or a pass."))
    _default(plugin, REVIEW.replace("- **An error swallowed.** A bare except.\n", ""))
    assert _classes(repo)["conflict"] == [BULLET_A]


def test_drift_own(repo: Path, plugin: Path) -> None:
    _record(repo)
    _host(repo, REVIEW + "\n## Pass 9 — Ours\n\nOnly here.\n")
    assert _classes(repo)["own"] == ["## Pass 9 — Ours"]
    assert sdlc.drift(repo)["refresh"] == []


def test_drift_host_removed(repo: Path, plugin: Path) -> None:
    _record(repo)
    _host(repo, REVIEW.replace("- **An error swallowed.** A bare except.\n", ""))
    assert _classes(repo)["host-removed"] == [BULLET_A]
    assert sdlc.drift(repo)["refresh"] == [], "a block the host took out stays out"


def test_drift_edited_is_left_alone(repo: Path, plugin: Path) -> None:
    _record(repo)
    _host(repo, REVIEW.replace("The contract.", "Our contract, in AGENTS.md."))
    assert _classes(repo)["edited"] == ["## Pass 2"]
    assert sdlc.drift(repo)["refresh"] == [] and sdlc.drift(repo)["report"] == []


def test_a_refresh_keeps_every_other_block_as_written(repo: Path, plugin: Path) -> None:
    _record(repo)
    host = REVIEW.replace("The contract.", "Our contract.") + "\n## Ours\n\nMine.\n"
    _host(repo, host)
    _default(plugin, REVIEW.replace("It asserts nothing.", "It asserts nothing real."))
    (refresh,) = sdlc.drift(repo)["refresh"]
    assert refresh["proposed"] == host.replace("It asserts nothing.", "It asserts nothing real.")


def test_whitespace_alone_is_not_drift(repo: Path, plugin: Path) -> None:
    _record(repo)
    _host(repo, REVIEW.replace("Look for these.\n", "Look for these.   \n\n\n"))
    assert set(_classes(repo)) == {"current"}


# ── R3: no manifest ─────────────────────────────────────────────────────────────────────────


def test_drift_without_manifest_is_two_way(repo: Path, plugin: Path) -> None:
    _host(repo, REVIEW.replace("The contract.", "Ours.") + "\n## Ours\n\nMine.\n")
    _default(plugin, REVIEW + "\n## Pass 3\n\nNew.\n")
    found = sdlc.drift(repo)
    assert found["base"] == "none" and found["version"]["manifest"] is None
    classes = _classes(repo)
    assert classes["differs"] == ["## Pass 2"]
    assert classes["added"] == ["## Pass 3"]
    assert classes["own"] == ["## Ours"]
    assert [r["unit"] for r in found["report"] if r["class"] == "differs"] == ["## Pass 2"]


def test_a_downgrade_proposes_nothing(repo: Path, plugin: Path, monkeypatch) -> None:
    _record(repo)
    _default(plugin, REVIEW + "\n## Pass 3\n\nNew.\n")
    monkeypatch.setattr(sdlc, "plugin_version", lambda: "1.0.0")
    found = sdlc.drift(repo)
    assert found["refresh"] == []
    assert [r["class"] for r in found["report"]] == ["downgrade"]


# ── R4: config ──────────────────────────────────────────────────────────────────────────────


def test_retired_key_is_breaking(repo: Path, plugin: Path, monkeypatch) -> None:
    retired = {"commands.gate": {"now": "commands.check", "since": "1.1.0", "do": "rename it"}}
    monkeypatch.setattr(sdlc, "RETIRED_KEYS", retired)
    (repo / ".sdlc" / "config.toml").write_text('[commands]\ngate = "true"\n', encoding="utf-8")
    (breaking,) = sdlc.drift(repo)["breaking"]
    assert breaking["where"] == "commands.gate" and breaking["now"] == "commands.check"
    assert breaking["fix"] == "rename it"


def test_unknown_key_is_reported(repo: Path, plugin: Path) -> None:
    (repo / ".sdlc" / "config.toml").write_text('[commands]\nbuld = "make"\n', encoding="utf-8")
    found = sdlc.drift(repo)
    assert found["breaking"] == []
    assert [(r["where"], r["class"]) for r in found["report"]] == [("commands.buld", "unknown")]


def test_new_keys_listed(repo: Path, plugin: Path) -> None:
    manifest = _record(repo)
    manifest["config_keys"].remove("metrics.stop_allowance")
    (repo / ".sdlc" / "setup.json").write_text(json.dumps(manifest), encoding="utf-8")
    (new,) = [r for r in sdlc.drift(repo)["report"] if r["class"] == "new"]
    assert new["where"] == "metrics.stop_allowance" and new["default"] == 1


def test_a_host_still_setting_target_stops_is_told(repo: Path, plugin: Path) -> None:
    """The flat target was retired for each change's own gates plus an allowance: a host's old
    setting is read by nothing now, so setup's drift says so, with what replaced it."""
    config = repo / ".sdlc" / "config.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n[metrics]\ntarget_stops = 2\n")
    assert "unknown key metrics.target_stops" in sdlc.load_config(repo)[1]
    (found,) = [b for b in sdlc.drift(repo)["breaking"] if b["where"] == "metrics.target_stops"]
    assert found["now"] == "metrics.stop_allowance" and "Delete it" in found["fix"]


def test_retired_keys_point_at_live_keys() -> None:
    live = {f"{s}.{k}" for s, keys in sdlc.CONFIG_KEYS.items() for k in keys}
    for old, entry in sdlc.RETIRED_KEYS.items():
        assert old not in live, f"{old} is retired but still read"
        assert entry.get("now") is None or entry["now"] in live, f"{old} → {entry['now']}"
        assert entry.get("since") and entry.get("do"), f"{old} says when and what to do"


# ── R5: template overrides ──────────────────────────────────────────────────────────────────


def test_override_missing_a_read_is_breaking(repo: Path, plugin: Path) -> None:
    (repo / ".sdlc" / "templates").mkdir()
    text = (ROOT / "templates" / "intent.md").read_text(encoding="utf-8")
    (repo / ".sdlc" / "templates" / "intent.md").write_text(
        text.replace("## Open questions", "## Questions"), encoding="utf-8"
    )
    (breaking,) = sdlc.drift(repo)["breaking"]
    assert breaking["where"] == ".sdlc/templates/intent.md"
    assert "## Open questions" in breaking["detail"]


def test_changed_template_is_reported(repo: Path, plugin: Path) -> None:
    (repo / ".sdlc" / "templates").mkdir()
    text = (ROOT / "templates" / "intent.md").read_text(encoding="utf-8")
    (repo / ".sdlc" / "templates" / "intent.md").write_text(text, encoding="utf-8")
    _record(repo)
    (plugin / "templates" / "intent.md").write_text(text + "\n## Risks\n\n<Risks.>\n")
    found = sdlc.drift(repo)
    assert [(r["where"], r["class"]) for r in found["report"]] == [
        (".sdlc/templates/intent.md", "changed")
    ]


def test_template_reads_exist_in_the_plugins_templates() -> None:
    for name in sdlc.TEMPLATE_READS:
        text = (ROOT / "templates" / name).read_text(encoding="utf-8")
        assert sdlc._template_misses(name, text) == [], f"TEMPLATE_READS names what {name} lacks"


# ── R6: kept apart ──────────────────────────────────────────────────────────────────────────


def test_drift_keeps_breaking_refresh_and_report_apart(repo: Path, plugin: Path) -> None:
    _record(repo)
    _default(plugin, REVIEW.replace("It asserts nothing.", "It asserts nothing real."))
    (repo / ".sdlc" / "config.toml").write_text('[commands]\nbuld = "make"\n', encoding="utf-8")
    (repo / ".sdlc" / "templates").mkdir()
    (repo / ".sdlc" / "templates" / "issue.md").write_text("No artifacts here.\n")
    found = sdlc.drift(repo)
    assert [b["where"] for b in found["breaking"]] == [".sdlc/templates/issue.md"]
    assert [r["path"] for r in found["refresh"]] == [".sdlc/REVIEW.md"]
    assert [r["where"] for r in found["report"]] == ["commands.buld"]


# ── R8: reset ───────────────────────────────────────────────────────────────────────────────


def test_reset_deletes_only_an_override(repo: Path, plugin: Path) -> None:
    (repo / ".sdlc" / "templates").mkdir()
    (repo / ".sdlc" / "templates" / "intent.md").write_text("ours\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "override")
    assert sdlc.cmd_reset(repo, "intent.md", check_only=True) == 0
    assert (repo / ".sdlc" / "templates" / "intent.md").exists()
    assert sdlc.cmd_reset(repo, "intent.md") == 0
    assert not (repo / ".sdlc" / "templates" / "intent.md").exists()
    assert (repo / ".sdlc" / "REVIEW.md").exists()


@pytest.mark.parametrize("name", ["../REVIEW.md", "REVIEW.md", "", "..", "sub/intent.md"])
def test_reset_refuses_other_paths(repo: Path, plugin: Path, name: str) -> None:
    assert sdlc.cmd_reset(repo, name) == 1
    assert (repo / ".sdlc" / "REVIEW.md").exists()


def test_reset_refuses_an_uncommitted_override(repo: Path, plugin: Path) -> None:
    (repo / ".sdlc" / "templates").mkdir()
    (repo / ".sdlc" / "templates" / "intent.md").write_text("ours\n", encoding="utf-8")
    assert sdlc.cmd_reset(repo, "intent.md") == 1
    assert (repo / ".sdlc" / "templates" / "intent.md").exists()


# ── R9, R10: uninstall ──────────────────────────────────────────────────────────────────────

INTENT = "---\nid: {id}\nslug: {slug}\ntier: 1\nstage: {stage}\n---\n\n# {id} — x\n"


def _setup(root: Path, settings: dict | None = None, line: bool = True) -> None:
    """What setup writes, committed: its allow rules into the settings, the ignore line."""
    data = settings or {}
    data.setdefault("permissions", {}).setdefault("allow", []).extend(sdlc.ALLOW_RULES)
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "settings.json").write_text(json.dumps(data, indent=2) + "\n")
    assert sdlc.cmd_record(root, [".sdlc/config.toml", ".sdlc/REVIEW.md"], line) == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "setup")


@pytest.fixture
def bare(tmp_path: Path) -> Path:
    """A repo before setup: a README, its own settings and an ignore file without the line."""
    root = tmp_path / "bare"
    (root / ".claude").mkdir(parents=True)
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    settings = {"model": "x", "permissions": {"allow": ["Bash(ls *)"], "deny": ["Bash(rm *)"]}}
    (root / ".claude" / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _set_up(root: Path) -> None:
    (root / ".sdlc").mkdir(exist_ok=True)
    (root / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "true"\n', encoding="utf-8")
    (root / ".sdlc" / "REVIEW.md").write_text(REVIEW, encoding="utf-8")
    (root / ".gitignore").write_text("node_modules/\n.claude/worktrees/\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# Guide\n\nRun /sdlc:intent first.\n", encoding="utf-8")
    settings = json.loads((root / ".claude" / "settings.json").read_text())
    _setup(root, settings)


def _files(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): p.read_text(encoding="utf-8")
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def test_uninstall_leaves_the_pre_setup_tree(bare: Path, plugin: Path) -> None:
    before = _files(bare)
    _set_up(bare)
    head = _git(bare, "rev-parse", "HEAD")
    assert sdlc.cmd_uninstall(bare, check_only=True) == 0
    assert (bare / ".sdlc" / "config.toml").exists(), "--check writes nothing"
    assert sdlc.cmd_uninstall(bare) == 0
    after = _files(bare)
    assert after.pop("AGENTS.md").startswith("# Guide"), "the context doc is left"
    assert {k: v for k, v in after.items() if k != ".claude/settings.json"} == {
        k: v for k, v in before.items() if k != ".claude/settings.json"
    }
    assert json.loads(after[".claude/settings.json"]) == json.loads(
        before[".claude/settings.json"]
    ), "unrelated keys and rules kept, the plugin's gone"
    assert _git(bare, "rev-parse", "HEAD") == head, "uninstall commits nothing"


def test_uninstall_lists_the_context_lines_naming_the_plugin(bare: Path, plugin, capsys) -> None:
    _set_up(bare)
    capsys.readouterr()
    sdlc.cmd_uninstall(bare, check_only=True)
    plan = json.loads(capsys.readouterr().out)
    assert plan["mentions"] == [{"path": "AGENTS.md", "line": 3, "text": "Run /sdlc:intent first."}]
    assert sorted(plan["remove"]) == [".sdlc/REVIEW.md", ".sdlc/config.toml", ".sdlc/setup.json"]


def test_uninstall_keeps_a_preexisting_ignore_line(repo: Path, plugin: Path) -> None:
    _setup(repo, line=False)
    assert sdlc.cmd_uninstall(repo) == 0
    assert ".claude/worktrees/" in (repo / ".gitignore").read_text(encoding="utf-8")
    assert not (repo / ".sdlc").exists()


def test_uninstall_without_a_manifest_leaves_the_ignore_line(repo: Path, plugin: Path) -> None:
    """With no record of what setup added, the line may be the host's own: it stays, said so."""
    _setup(repo, line=True)
    _git(repo, "rm", "-q", str(sdlc.MANIFEST))
    _git(repo, "commit", "-q", "-m", "lose the record")
    assert sdlc.cmd_uninstall(repo) == 0
    assert ".claude/worktrees/" in (repo / ".gitignore").read_text(encoding="utf-8")
    assert not (repo / ".sdlc").exists()


def test_uninstall_leaves_what_git_doesnt_hold(repo: Path, plugin: Path) -> None:
    (repo / ".gitignore").write_text(".claude/worktrees/\n.sdlc/terms.local\n")
    (repo / ".sdlc" / "terms.local").write_text("a term\n")
    _setup(repo)
    assert sdlc.cmd_uninstall(repo) == 0
    assert (repo / ".sdlc" / "terms.local").read_text() == "a term\n"
    assert not (repo / ".sdlc" / "config.toml").exists()


def _change(root: Path, ident: str, slug: str, stage: str, worktree: bool) -> None:
    name = f"{ident}-{slug}"
    where = root
    if worktree:
        where = root / ".claude" / "worktrees" / name
        _git(root, "worktree", "add", "-q", "-b", name, str(where))
    (where / ".sdlc" / "work" / name).mkdir(parents=True)
    (where / ".sdlc" / "work" / name / "intent.md").write_text(
        INTENT.format(id=ident, slug=slug, stage=stage), encoding="utf-8"
    )
    _git(where, "add", "-A")
    _git(where, "commit", "-q", "-m", name)


def _refusals(root: Path, capsys) -> list[str]:
    capsys.readouterr()
    assert sdlc.cmd_uninstall(root) == 1
    assert (root / ".sdlc" / "config.toml").exists(), "a refusal removes nothing"
    return json.loads(capsys.readouterr().out)["refused"]


def test_uninstall_refuses_open_change(repo: Path, plugin: Path, capsys) -> None:
    _setup(repo)
    _change(repo, "001", "reopen-drafts", "build", worktree=False)
    (refusal,) = _refusals(repo, capsys)
    assert "001-reopen-drafts is open" in refusal


def test_uninstall_refuses_worktree(repo: Path, plugin: Path, capsys) -> None:
    _setup(repo)
    _git(repo, "worktree", "add", "-q", "-b", "002-stale", str(repo / ".claude/worktrees/x"))
    (refusal,) = _refusals(repo, capsys)
    assert "worktree 002-stale" in refusal


def test_uninstall_refuses_unclosed_shipped(repo: Path, plugin: Path, capsys) -> None:
    _setup(repo)
    _change(repo, "003", "landed", "shipped", worktree=True)
    (refusal,) = _refusals(repo, capsys)
    assert "003-landed is shipped but not closed" in refusal


def test_uninstall_refuses_uncommitted(repo: Path, plugin: Path, capsys) -> None:
    _setup(repo)
    (repo / ".sdlc" / "config.toml").write_text('[commands]\ncheck = "false"\n')
    (refusal,) = _refusals(repo, capsys)
    assert ".sdlc/config.toml has uncommitted changes" in refusal


# ── R12: visible without a rerun ────────────────────────────────────────────────────────────


def _readiness(root: Path, capsys) -> dict:
    capsys.readouterr()
    sdlc.cmd_readiness(root)
    items = json.loads(capsys.readouterr().out)["items"]
    return next(i for i in items if i["name"] == "drift")


def test_readiness_drift_item(repo: Path, plugin: Path, capsys) -> None:
    _record(repo)
    assert _readiness(repo, capsys)["status"] == "ok"
    _default(plugin, REVIEW.replace("It asserts nothing.", "It asserts nothing real."))
    item = _readiness(repo, capsys)
    assert item["status"] == "warn" and "1 doc(s) to refresh" in item["detail"]
    (repo / ".sdlc" / "config.toml").unlink()
    assert _readiness(repo, capsys)["status"] == "n/a"


def test_status_nudges_on_old_manifest(repo: Path, plugin: Path, monkeypatch) -> None:
    assert "no record" in sdlc.setup_nudge(repo)
    _record(repo)
    assert sdlc.setup_nudge(repo) is None
    monkeypatch.setattr(sdlc, "plugin_version", lambda: "1.2.0")
    assert sdlc.setup_nudge(repo) == "set up with 1.1.0, the plugin is 1.2.0  /sdlc:setup"
    (repo / ".sdlc" / "config.toml").unlink()
    assert sdlc.setup_nudge(repo) is None, "a repo not set up gets no nudge"


def test_check_strict_ignores_drift(repo: Path, plugin: Path) -> None:
    _default(plugin, REVIEW + "\n## Pass 3\n\nNew.\n")
    assert sdlc.drift(repo)["refresh"], "there is drift"
    assert sdlc.analyze(repo)["problems"] == [], "and it isn't a problem `check` counts"


# ── Found at review ─────────────────────────────────────────────────────────────────────────


def test_a_repeated_key_is_its_own_block(repo: Path, plugin: Path) -> None:
    """A host that uses a default's bullet lead a second time keeps its own text when the
    default's is refreshed: each block is compared and rewritten on its own."""
    _record(repo)
    ours = "- **An error swallowed.** Ours: a retry that hides the cause.\n"
    _host(repo, REVIEW.replace("\n## Pass 2", f"{ours}\n## Pass 2"))
    _default(plugin, REVIEW.replace("A bare except.", "A bare except, or a pass."))
    assert _classes(repo)["refreshed"] == [BULLET_A]
    assert _classes(repo)["own"] == [f"{BULLET_A} (2)"]
    (refresh,) = sdlc.drift(repo)["refresh"]
    assert refresh["proposed"].count("A bare except, or a pass.") == 1
    assert ours.strip() in refresh["proposed"]


def test_the_shipped_defaults_have_one_block_per_key() -> None:
    paths = sorted((ROOT / "defaults").glob("*.md"))
    assert paths, "the defaults were found"
    for path in paths:
        keys = [k for k, _ in sdlc.doc_units(path.read_text(encoding="utf-8"))]
        assert not [k for k in keys if k.endswith(")") and k.rsplit(" (", 1)[0] in keys], path


def test_a_moved_doc_is_reported(repo: Path, plugin: Path) -> None:
    _record(repo)
    (repo / ".sdlc" / "REVIEW.md").rename(repo / "REVIEW.md")
    (repo / ".sdlc" / "config.toml").write_text('[docs]\nreview = "REVIEW.md"\n')
    (moved,) = [r for r in sdlc.drift(repo)["report"] if r["class"] == "moved"]
    assert moved["where"] == "REVIEW.md" and ".sdlc/REVIEW.md" in moved["detail"]


def test_uninstall_keeps_other_settings_text_as_written(repo: Path, plugin: Path) -> None:
    _setup(repo, {"note": "réglages partagés"})
    assert sdlc.cmd_uninstall(repo) == 0
    text = (repo / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert "réglages partagés" in text and "sdlc.py" not in text


def test_uninstall_removes_the_settings_file_setup_created(repo: Path, plugin: Path) -> None:
    _setup(repo)
    manifest = json.loads((repo / ".sdlc" / "setup.json").read_text())
    manifest["created"].append(".claude/settings.json")
    (repo / ".sdlc" / "setup.json").write_text(json.dumps(manifest))
    _git(repo, "commit", "-qam", "record the settings")
    assert sdlc.cmd_uninstall(repo) == 0
    assert not (repo / ".claude" / "settings.json").exists()
