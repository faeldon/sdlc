"""The skills' invariants: their frontmatter, their gates, and how they reach the script.

They are about the plugins themselves, not about any repo that installs them: `sdlc`, at the
root, and the optional `sdlc-factory`, under `plugins/factory/`. Two skills can share a folder name
across the plugins (both have a `spec`), so each is known by its full name, `<plugin>:<skill>`.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import frontmatter
import pytest

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "plugins" / "factory"
# Each plugin's root, and the one script its skills run.
PLUGINS = {"sdlc": ROOT, "sdlc-factory": FACTORY}
SCRIPTS = {"sdlc": "sdlc.py", "sdlc-factory": "factory.py"}
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md")) + sorted(
    (FACTORY / "skills").glob("*/SKILL.md")
)


def _plugin(skill: Path) -> str:
    return "sdlc-factory" if skill.is_relative_to(FACTORY) else "sdlc"


def _id(skill: Path) -> str:
    return f"{_plugin(skill)}:{skill.parent.name}"


BY_ID = {_id(s): s for s in SKILLS}


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_under_test", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()

# The skills that write something real, and therefore owe a human gate.
GATED = {
    *(
        f"sdlc:{n}"
        for n in (
            "intent",
            "spec",
            "ship",
            "close",
            "drop",
            "setup",
            "release",
            "publish",
            "retro",
            "uninstall",
        )  # fmt: skip
    ),
    "sdlc-factory:spec",
    "sdlc-factory:build",
}

# Every config key a skill reads, by skill. A skill that stops naming its key has gone back to
# guessing the host's tools, which is what `sdlc.py config` (and `factory.py config`) exists to
# stop.
READS_CONFIG = {
    "sdlc:intent": [
        "docs.process",
        "commands.worktree_setup",
        "archive.ids_from",
        "docs.project",
        "docs.product",
        "git.base",
    ],
    "sdlc:spec": [
        "docs.policy",
        "docs.read_before_design",
        "docs.review",
        "docs.explore",
        "docs.product",
        "docs.process",
    ],
    "sdlc:ship": [
        "docs.process",
        "commands.check",
        "commands.build",
        "commands.build_when",
        "docs.review",
        "docs.context",
        "git.base",
    ],
    "sdlc:close": ["commands.close_list", "commands.close_cleanup", "archive.target", "git.base"],
    "sdlc:drop": ["archive.target", "git.base"],
    "sdlc:uninstall": ["archive.target", "docs.policy", "docs.context"],
    "sdlc:release": [
        "release.version_files",
        "release.tag",
        "release.changelog",
        "release.after_bump",
        "release.prepare",
        "git.base",
    ],
    "sdlc:publish": ["release.remote", "release.publish", "release.prepare", "git.base"],
    "sdlc:health": ["commands.scan", "docs.health"],
    "sdlc:retro": [
        "docs.process",
        "docs.policy",
        "docs.direction",
        "docs.context",
        "docs.product",
        "retro.evidence",
    ],
    "sdlc:setup": [
        "commands.check",
        "commands.build",
        "commands.build_when",
        "commands.scan",
        "commands.worktree_setup",
        "docs.process",
        "docs.review",
        "docs.policy",
        "docs.context",
        "archive.target",
        "docs.project",
        "docs.product",
        "retro.evidence",
        "git.base",
    ],
    "sdlc-factory:spec": ["factory.models"],
    "sdlc-factory:build": ["factory.reviewers", "factory.rounds", "factory.models"],
}


def test_skills_were_found() -> None:
    """A glob that matches nothing makes every test below vacuously pass."""
    names = {"intent", "spec", "ship", "close", "status", "health", "setup", "release"}
    assert {f"sdlc:{n}" for n in names | {"publish", "retro", "drop", "uninstall"}} | {
        "sdlc-factory:spec", "sdlc-factory:build"
    } == set(BY_ID)  # fmt: skip


@pytest.mark.parametrize("skill", SKILLS, ids=_id)
def test_skill_frontmatter(skill: Path) -> None:
    post = frontmatter.load(skill)
    assert post.get("name") == skill.parent.name, "the directory is what the invocation uses"
    desc = post.get("description")
    assert desc and len(desc) > 80, "say when to use it AND when not to"
    # Each is a budget or a gate, and letting the model trigger one on its own defeats the point
    # of the stage boundary.
    assert post.get("disable-model-invocation") is True
    assert post.get("allowed-tools"), "a read-only skill that can Write is not read-only"


@pytest.mark.parametrize("name", sorted(GATED))
def test_writing_skills_carry_exactly_one_wait_gate(name: str) -> None:
    """One, not zero: approval is per-invocation and never standing. One, not several: a skill
    with two gates has an unclear boundary, and in practice the second gets skipped."""
    text = BY_ID[name].read_text(encoding="utf-8")
    waits = [ln for ln in text.splitlines() if ln.startswith("#") and "WAIT" in ln]
    assert len(waits) == 1, f"{name}: expected 1 WAIT heading, found {waits}"


@pytest.mark.parametrize("skill", SKILLS, ids=_id)
def test_skills_run_the_script_through_uv(skill: Path) -> None:
    """The script declares its own dependencies, so every call goes through `uv run --script`,
    whatever the host has or lacks. A call through a host's interpreter works only in a host that
    happens to have the libraries, which is how the plugin first failed to be portable. Each
    plugin's skills run its own script: the factory's installed copy has no `sdlc.py` beside it."""
    text = skill.read_text(encoding="utf-8")
    script = SCRIPTS[_plugin(skill)]
    calls = [ln for ln in text.splitlines() if f"scripts/{script}" in ln]
    assert calls, f"{_id(skill)}: never runs {script}"
    for ln in calls:
        assert f'uv run --quiet --script "${{CLAUDE_PLUGIN_ROOT}}"/scripts/{script}' in ln, ln
    other = SCRIPTS["sdlc" if _plugin(skill) == "sdlc-factory" else "sdlc-factory"]
    assert f"scripts/{other}" not in text, f"{_id(skill)} reaches the other plugin's script"
    assert "/bin/python" not in text


@pytest.mark.parametrize("name", sorted(READS_CONFIG))
def test_skills_read_host_specifics_from_config(name: str) -> None:
    text = BY_ID[name].read_text(encoding="utf-8")
    script = SCRIPTS[name.split(":")[0]]
    assert f"{script} config" in text, f"{name}: run `{script} config` in Step 0"
    for key in READS_CONFIG[name]:
        short = key.split(".", 1)[1]
        assert key in text or f"`{short}`" in text, f"{name}: never reads {key}"


def test_intent_asks_with_a_number_the_tool_just_gave() -> None:
    """The draft for one change showed a number another session's worktree had already taken."""
    text = (ROOT / "skills" / "intent" / "SKILL.md").read_text(encoding="utf-8")
    step4 = text.split("## Step 4")[1].split("## Step 5")[0]
    assert "sdlc.py next" in step4
    assert "if still free when created" in step4


def test_intent_moves_the_session_and_close_brings_it_back() -> None:
    intent = frontmatter.load(ROOT / "skills" / "intent" / "SKILL.md")
    close = frontmatter.load(ROOT / "skills" / "close" / "SKILL.md")
    assert "EnterWorktree" in intent["allowed-tools"] and "EnterWorktree" in intent.content
    assert "ExitWorktree" in close["allowed-tools"]
    assert '"keep"' in close.content
    # A `cd` in the host's setup would move the session first, and close would have nothing to exit.
    step5 = intent.content.split("## Step 5")[1].split("## Step 6")[0]
    assert "subshell, `(<command>)`" in step5
    assert step5.index("worktree_setup") < step5.index("`EnterWorktree` with")
    drop = (ROOT / "skills" / "drop" / "SKILL.md").read_text(encoding="utf-8")
    for text in (close.content, drop):
        assert "No-op: there is no active EnterWorktree session" in " ".join(text.split())
    # The cleanup is handed over, never run: close may not hold the tool that would run it.
    assert "close_cleanup" in close.content
    assert any(t.startswith("Bash(") for t in close["allowed-tools"])
    assert "Never run it from this session" in close.content
    ship = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    assert "/sdlc:close" in ship


def test_ship_checks_the_context_docs_inside_its_one_gate() -> None:
    """The context update rides the review: weighed in Step 3, shown in Step 4, approved by the
    one WAIT and landed in the same commit. Close can't do it: it has no Edit, and refuses a dirty
    worktree."""
    text = (ROOT / "skills" / "ship" / "SKILL.md").read_text(encoding="utf-8")
    step3 = text.split("## Step 3")[1].split("## Step 4")[0]
    assert "sdlc.py context" in step3 and "**Context**" in step3
    wait = text.split("## Step 5")[1].split("## Step 6")[0]
    assert "context update" in wait
    close = frontmatter.load(ROOT / "skills" / "close" / "SKILL.md")
    assert "Edit" not in close["allowed-tools"]


def test_close_lands_mirrors_and_removes_through_the_script_and_never_by_hand() -> None:
    """Land, mirror, remove: one command, so the removal can't run without the other two."""
    text = (ROOT / "skills" / "close" / "SKILL.md").read_text(encoding="utf-8")
    assert "sdlc.py close <NNN> --check" in text and "sdlc.py close <NNN>\n" in text
    assert "rm -" not in text
    wait = text.split("## Step 2")[1].split("## Step 3")[0]
    assert "archive it to" in wait and '"Close NNN-slug"' in wait, (
        "the one approval covers the mirror and the commit that removes the folder"
    )


def test_only_publish_pushes() -> None:
    """The production gate: ship and close stop at a commit, release at a local tag. Publish is
    the one skill, and `cmd_publish` the one function, that pushes, behind its own approval."""
    for skill in SKILLS:
        rules = [r for r in _bash_rules(skill) if "push" in r]
        pushes = [c for c in _block_commands(skill.read_text(encoding="utf-8")) if "git push" in c]
        assert not rules and not pushes, f"{_id(skill)} pushes: {rules or pushes}"
    publish = frontmatter.load(ROOT / "skills" / "publish" / "SKILL.md")
    assert "sdlc.py publish" in publish.content
    source = (ROOT / "scripts" / "sdlc.py").read_text(encoding="utf-8")
    body = source.split("\ndef cmd_publish(")[1].split("\ndef ")[0]
    assert source.count('"push"') == body.count('"push"') > 0, "a push outside cmd_publish"


def test_retro_counts_through_the_script_and_records_after_its_gate() -> None:
    """The retrospective audits prose doing a script's work, so it keeps that rule itself: history
    comes from `sdlc.py retro`, never `git log`, and the one write
    after the WAIT goes through `retro-commit`."""
    skill = ROOT / "skills" / "retro" / "SKILL.md"
    text = frontmatter.load(skill).content
    commands = _block_commands(text)
    assert not any(c.startswith("git ") for c in commands)
    assert not any("git" in r for r in _bash_rules(skill))
    before, after = text.split("WAIT for explicit approval")
    assert "sdlc.py retro-commit" not in before and "sdlc.py retro-commit" in after
    assert (
        "never for editing code, skills or the process doc"
        in frontmatter.load(skill)["description"]
    )


def test_retro_closes_its_own_loop_and_release_says_when_one_is_due() -> None:
    """Each run scores what the last one left open before it sets anything new, and its one WAIT
    names the status changes it approves. Release passes the nudge on; nothing runs a retro."""
    text = frontmatter.load(ROOT / "skills" / "retro" / "SKILL.md").content
    step0 = text.split("## Step 0")[1].split("## Step 1")[0]
    assert "`direction`" in step0 and "`next_ids`" in step0 and "`vanished`" in step0
    direction = text.split("5. **Direction.**")[1].split("## Step 3")[0]
    assert "Since the last retrospective" in " ".join(direction.split())
    assert direction.index("close the loop") < direction.index("propose up to three open goals")
    wait = text.split("## Step 5")[1].split("## Step 6")[0]
    assert "status changes" in wait
    release = (ROOT / "skills" / "release" / "SKILL.md").read_text(encoding="utf-8")
    step4 = release.split("## Step 4")[1].split("## Out of scope")[0]
    assert "`retro_due.due`" in step4 and "/sdlc:retro" in step4 and "Don't run" in step4


def test_ship_records_its_findings_and_close_and_retro_name_the_numbers() -> None:
    """Ship's findings are counts in its own commit, written after its WAIT; close says what it
    measured and why not; retro reads the numbers and says what they rest on."""
    ship = frontmatter.load(ROOT / "skills" / "ship" / "SKILL.md").content
    before, after = ship.split("WAIT for explicit approval")
    assert "Sdlc-Findings: important=<n> nit=<n>" in before, "drafted in Step 4, for approval"
    assert "git commit" in after and "git commit" not in before
    close = frontmatter.load(ROOT / "skills" / "close" / "SKILL.md").content
    report = close.split("## Step 4")[1]
    assert "`measure`" in report and "`coverage`" in report and "never stops a close" in report
    assert "`ran`" in report and "`merged code`" in report, "which code ran the close"
    retro = frontmatter.load(ROOT / "skills" / "retro" / "SKILL.md").content
    step0 = retro.split("## Step 0")[1].split("## Step 1")[0]
    assert "`metrics`" in step0 and "`uncaptured`" in step0
    process = retro.split("3. **Process.**")[1].split("4. **Direction.**")[0]
    assert "`metrics`" in process and "`required`" in process and "`target`" in process
    # Rework within a change is read beside its cost, and never confused with follow-up rework.
    assert "`in_change`" in step0 and "`in_change`" in process
    assert "follow-up `rework`" in step0


def test_nits_are_offered_early_recorded_at_ship_and_counted_by_retro() -> None:
    """A nit approved unfixed goes to work/inbox.md, as a `[nit]` entry with an id, behind ship's
    one approval; intent and spec offer the open ones a change touches; retro weighs them and never
    edits the register."""
    text = {
        s: (ROOT / "skills" / s / "SKILL.md").read_text(encoding="utf-8")
        for s in ("ship", "intent", "spec", "retro")
    }
    ship = text["ship"]
    step0 = ship.split("## Step 0")[1].split("## Step 1")[0]
    assert "sdlc.py nits --change <NNN>" in step0
    wait = ship.split("## Step 5")[1].split("## Step 6")[0]
    assert "the nits shown recorded in work/inbox.md" in wait
    present = ship.split("## Step 4")[1].split("## Step 5")[0]
    assert "sdlc.py next-entry --count <N>" in present and "[nit]" in present
    land = ship.split("## Step 6")[1].split("## Step 7")[0]
    assert 'templates["inbox.md"]' in land
    assert "`work/inbox.md` when Step 6" in " ".join(land.split())
    assert "Retired nits:" in ship
    for name in ("intent", "spec"):
        assert "sdlc.py nits --touching" in text[name], name
        assert "Never take one in unasked" in " ".join(text[name].split()), name
    assert "`nits`" in text["retro"]
    assert "never this skill's" in " ".join(text["retro"].split())


def test_only_close_and_drop_leave_the_worktree() -> None:
    """Every stage before close writes its artifacts in the change's worktree, where the session
    already is, so none of them needs to step out and back. Drop ends a change the way close
    does, after its one approval."""
    for skill in SKILLS:
        if _id(skill) not in ("sdlc:close", "sdlc:drop"):
            assert "ExitWorktree" not in skill.read_text(encoding="utf-8"), _id(skill)


def test_drop_writes_the_reason_then_lands_through_the_script() -> None:
    """The reason is prose, so the skill writes it; the stamp, the commits and the removals are
    the script's, behind the one WAIT."""
    post = frontmatter.load(ROOT / "skills" / "drop" / "SKILL.md")
    assert "Edit" in post["allowed-tools"] and "ExitWorktree" in post["allowed-tools"]
    # Both checks refuse until Step 4 writes the reason, so `&&` would skip `config`.
    step0 = post.content.split("## Step 0")[1].split("## Step 1")[0]
    assert "--check ;" in step0 and "&&" not in step0.split("```bash")[1].split("```")[0]
    wait = post.content.split("## Step 3")[1].split("## Step 4")[0]
    assert '"Drop NNN-slug"' in wait and "not planned" in wait
    land = post.content.split("## Step 4")[1].split("## Step 5")[0]
    assert (
        land.index("sdlc.py drop <NNN>")
        < land.index("ExitWorktree")
        < land.index("sdlc.py close <NNN>")
    )
    assert '"keep"' in land and "-D" not in post.content.split("## Out of scope")[0]
    close = (ROOT / "skills" / "close" / "SKILL.md").read_text(encoding="utf-8")
    assert '"Drop NNN-slug"' in close.split("## Step 2")[1].split("## Step 3")[0]


@pytest.mark.parametrize("name", sorted(BY_ID))
def test_no_skill_writes_the_inbox_heading_itself(name: str) -> None:
    """`work/inbox.md` starts from `templates["inbox.md"]`, which a host can override; a heading
    written inline would skip it."""
    text = BY_ID[name].read_text(encoding="utf-8")
    assert "`# Inbox`" not in text, f'{name}: start inbox.md from templates["inbox.md"]'


@pytest.mark.parametrize("name", ["sdlc:intent", "sdlc:spec", "sdlc:retro", "sdlc:setup"])
def test_skills_show_an_outcome_by_its_name_beside_its_id(name: str) -> None:
    """An id alone (`O3`) means nothing to someone without the product doc open."""
    text = BY_ID[name].read_text(encoding="utf-8")
    assert "`name`" in text and re.search(r"O\d+ \([A-Z][\w ]+\)", text), f"{name}: `O1 (<name>)`"


def test_setup_drafts_from_readiness_and_never_commits() -> None:
    text = (ROOT / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
    assert "sdlc.py readiness" in text.split("## Step 1")[0]
    assert "git commit" not in text.split("## Step 6")[0], "the commit is handed to the human"
    assert "never rewrite it" in text, "an existing CLAUDE.md gets a diff, not a new file"


def test_setup_asks_what_kind_of_repo_first() -> None:
    skill = ROOT / "skills" / "setup" / "SKILL.md"
    step2 = skill.read_text(encoding="utf-8").split("## Step 2")[1].split("## Step 3")[0]
    for question in ("**Kind:**", "**Who runs it:**", "**Where changes are tracked:**"):
        assert question in step2, f"the profile round asks {question}"
    assert 'target = "none"' in step2, "a local repo mirrors nothing"
    # readiness reports an unset slower check as missing on a repo that is set up, so the round is
    # keyed on the config file alone: a rerun never asks again.
    assert "`config` item is `missing`" in step2
    # The profile is guessed from readiness and the repo's files, never from history or the tracker:
    # either would need a rule of its own, and a change to a skill's allowed-tools is Tier 2.
    reads_history = [
        r for r in _bash_rules(skill) if ("git " in r and "rev-parse" not in r) or "gh " in r
    ]
    assert not reads_history, reads_history


# ---------------------------------------------------------------- allowed-tools
#
# A skill's allowed-tools grants each listed tool without a prompt for the turn that runs it; it
# restricts nothing. Plain `Bash` would pre-approve every command, a commit and an issue included,
# so each skill lists the exact commands it runs, and these keep the list and the skill in step.

# The splitter lives in the script, which counts each skill's commands for the retrospective too:
# one definition of what a command is.
_block_commands = sdlc.bash_commands


def _rule_regex(rule: str) -> re.Pattern:
    """A `Bash(...)` rule as a regex: `*` matches anything, and a trailing ` *` the bare command."""
    body = re.escape(rule[len("Bash(") : -1])
    body = re.sub(r"\\ \\\*$", r"(?: .*)?", body).replace(r"\*", ".*")
    return re.compile(rf"^{body}$")


def _bash_rules(skill: Path) -> list[str]:
    return [t for t in frontmatter.load(skill)["allowed-tools"] if t.startswith("Bash")]


@pytest.mark.parametrize("skill", SKILLS, ids=_id)
def test_no_skill_grants_all_of_bash(skill: Path) -> None:
    assert "Bash" not in frontmatter.load(skill)["allowed-tools"]
    assert all(r.startswith("Bash(") and r.endswith(")") for r in _bash_rules(skill))


@pytest.mark.parametrize("skill", SKILLS, ids=_id)
def test_every_command_a_skill_runs_has_a_rule(skill: Path) -> None:
    rules = [_rule_regex(r) for r in _bash_rules(skill)]
    uncovered = [c for c in _block_commands(skill.read_text(encoding="utf-8"))
                 if not any(r.match(c) for r in rules)]  # fmt: skip
    assert not uncovered, f"{_id(skill)}: no allowed-tools rule for {uncovered}"


@pytest.mark.parametrize("skill", SKILLS, ids=_id)
def test_every_rule_is_for_a_command_the_skill_runs(skill: Path) -> None:
    """No stale grants: each rule matches a command in a block or in the skill's prose."""
    text = skill.read_text(encoding="utf-8")
    used = _block_commands(text) + re.findall(r"`([a-z][^`]*)`", text)
    stale = [r for r in _bash_rules(skill) if not any(_rule_regex(r).match(c) for c in used)]
    assert not stale, f"{_id(skill)}: rules for nothing it runs: {stale}"


def test_the_rule_matcher_can_fail() -> None:
    rule = _rule_regex("Bash(git diff *)")
    assert rule.match("git diff") and rule.match("git diff --stat HEAD")
    assert not rule.match("git difftool") and not rule.match("git commit -m x")


def test_manifest_names_the_plugin_and_its_license() -> None:
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert data["name"] == "sdlc", "the manifest name is what namespaces every skill"
    assert re.fullmatch(r"\d+\.\d+\.\d+", data["version"])
    # MIT, and the LICENSE file at the root says so in full.
    assert data["license"] == "MIT"
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_marketplace_lists_both_plugins() -> None:
    data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert data["name"] == "sdlc"
    assert [(p["name"], p["source"]) for p in data["plugins"]] == [
        ("sdlc", "./"),
        ("sdlc-factory", "./plugins/factory"),
    ]


# ---------------------------------------------------------------- the optional factory
#
# `sdlc-factory` is optional by construction: a repo that doesn't want agents doesn't install it,
# and `sdlc` reads nothing of it.


def _manifest(root: Path) -> dict:
    return json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


def test_sdlc_loads_nothing_from_plugins() -> None:
    """`sdlc`'s source is the repo root, so `plugins/factory/` travels in its cached copy. It stays
    unread only while `sdlc` keeps its default scans: skills from `skills/`, and no agents."""
    sdlc = _manifest(ROOT)
    assert not {"skills", "agents", "commands", "hooks"} & set(sdlc), "a manifest key widens a scan"
    assert not (ROOT / "agents").exists() and not (ROOT / "commands").exists()
    assert not (ROOT / "hooks").exists()


def test_the_factory_depends_on_sdlc_and_shares_its_version() -> None:
    factory, sdlc = _manifest(FACTORY), _manifest(ROOT)
    assert factory["name"] == "sdlc-factory" and factory["dependencies"] == ["sdlc"]
    assert factory["version"] == sdlc["version"], "one release carries both"
    assert factory["license"] == "MIT"


# Each agent's tools: only the builder may change files. A reviewer or the approver that could
# Edit or Write would be a second builder nobody asked for, and the spec-writer's draft must reach
# the person before anything is written.
AGENT_TOOLS = {
    "spec-writer": {"Read", "Grep", "Glob"},
    "builder": {"Read", "Grep", "Glob", "Edit", "Write", "Bash"},
    "reviewer-code": {"Read", "Grep", "Glob", "Bash"},
    "reviewer-security": {"Read", "Grep", "Glob", "Bash"},
    "reviewer-test": {"Read", "Grep", "Glob", "Bash"},
    "approver": {"Read", "Grep", "Glob"},
}
ADAPTED = {"spec-writer", "builder", "reviewer-code", "reviewer-security", "reviewer-test"}


def test_agents_have_their_tools_and_nothing_more() -> None:
    agents = {p.stem: frontmatter.load(p) for p in sorted((FACTORY / "agents").glob("*.md"))}
    assert set(agents) == set(AGENT_TOOLS)
    for name, post in agents.items():
        assert post["name"] == name and post.get("model") and len(post["description"]) > 80
        tools = {t.strip() for t in str(post["tools"]).split(",")}
        assert tools == AGENT_TOOLS[name], f"{name}: {sorted(tools)}"
        assert "never" in post.content.lower() and "commit" in post.content, f"{name}: no rule"


def test_adapted_agents_keep_the_notice() -> None:
    """MIT asks for the notice wherever the material goes: the NOTICE file holds it, and each
    adapted agent names its source on the line after its heading."""
    notice = (FACTORY / "NOTICE").read_text(encoding="utf-8")
    assert "MIT License" in notice and "Copyright (c) 2025 Addy Osmani" in notice
    for name in ADAPTED:
        text = (FACTORY / "agents" / f"{name}.md").read_text(encoding="utf-8")
        assert "Adapted from addyosmani/agent-skills (MIT)" in text, name
        assert f"agents/{name}.md" in notice, f"NOTICE doesn't list {name}"


def test_judging_agents_return_text_the_skill_writes() -> None:
    """The spec-writer, reviewers and approver have no Write, so the skill writes what they
    return, and the spec only after its WAIT."""
    spec = BY_ID["sdlc-factory:spec"].read_text(encoding="utf-8")
    after_wait = spec.split("## Step 2 — WAIT")[1]
    assert "Edit" in after_wait and "spec.md" in after_wait
    build = BY_ID["sdlc-factory:build"].read_text(encoding="utf-8")
    assert "reviews/round-<round>/<role>.md" in build and "decision.md" in build
    assert "in one\n     message" in build or "in one message" in build, "reviewers in parallel"


def test_ship_reads_the_agents_verdicts() -> None:
    """When a change was built by agents, ship reads their decision and reviews as evidence for its
    own passes, and shows them; a change without them is reviewed as before."""
    text = BY_ID["sdlc:ship"].read_text(encoding="utf-8")
    step0 = text.split("## Step 0")[1].split("## Step 1")[0]
    assert "decision.md" in step0 and "reviews/round-<N>/" in step0
    step4 = text.split("## Step 4")[1].split("## Step 5")[0]
    assert "**Agent verdicts.**" in step4 and "ESCALATE" in step4
    assert "never stands in" in step4


def test_ship_lists_then_runs_the_changes_checks_under_a_prompt() -> None:
    """After the gate and before the build check: the checks are listed, shown, then run by
    `accept`, which ship names without a rule, so the person answers a prompt with them in view."""
    text = BY_ID["sdlc:ship"].read_text(encoding="utf-8")
    step1 = text.split("## Step 1")[1].split("## Step 2")[0]
    order = ("commands.check", "sdlc.py checks <NNN>", "sdlc.py accept <NNN>")
    gate, listed, run = (step1.find(s) for s in order)
    assert -1 < gate < listed < run, "the gate, then the listing, then the run"
    assert "**A failure stops" in step1 and "no acceptance checks" in step1


@pytest.mark.parametrize("skill", SKILLS, ids=_id)
def test_no_skill_lets_accept_run_unasked(skill: Path) -> None:
    accept = 'uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py accept 005'
    granted = [r for r in _bash_rules(skill) if _rule_regex(r).match(accept)]
    assert not granted, f"{_id(skill)} would run a change's own checks without a prompt"


def test_the_build_session_brings_the_persons_decisions_to_them() -> None:
    """Agents can't talk to the person; the build session can. A blocking decision stops the loop
    (`next: decide`) and is asked, never answered by the session itself; ship and the approver read
    the ledger."""
    build = frontmatter.load(BY_ID["sdlc-factory:build"])
    assert "AskUserQuestion" in build["allowed-tools"] and "Edit" in build["allowed-tools"]
    assert "**`decide`**" in build.content and "decisions.md" in build.content
    assert "Never answer a decision yourself" in build.content
    assert "decisions.md" in BY_ID["sdlc:ship"].read_text(encoding="utf-8").split("## Step 1")[0]
    approver = (FACTORY / "agents" / "approver.md").read_text(encoding="utf-8")
    assert "decisions.md" in approver and "still unticked" in approver
    builder = (FACTORY / "agents" / "builder.md").read_text(encoding="utf-8")
    assert "- DECISION: [blocking]" in builder and "- DECISION: [default]" in builder


def test_the_retro_keeps_evidence_and_the_product_docs_prose_out_of_what_it_writes() -> None:
    """Evidence can hold what a host's users did, and the product doc's prose is the human's: the
    retrospective writes outcome lines only, in its own words."""
    text = BY_ID["sdlc:retro"].read_text(encoding="utf-8")
    out = text.split("## Out of scope")[1]
    assert "Quoting evidence output" in out and "only its outcome lines" in out
    assert "the product pass first of all" in text.split("## Step 2")[1].split("## Step 3")[0]


def test_intent_never_picks_what_a_change_serves() -> None:
    text = BY_ID["sdlc:intent"].read_text(encoding="utf-8")
    step1 = text.split("## Step 1")[1].split("## Step 2")[0]
    assert "**What it serves**" in step1 and "Never pick for the human" in step1
    assert "`none`" in step1 and "**Moves O1:**" in step1


def test_setup_checks_and_records_what_it_offered() -> None:
    """A rerun after a plugin update is how a host hears what changed under its docs, and the
    record is what the next rerun compares against: setup runs `drift` before drafting and
    `record` after writing."""
    text = (ROOT / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
    step0 = text.split("## Step 0")[1].split("## Step 1")[0]
    step5 = text.split("## Step 5")[1].split("## Step 6")[0]
    assert "sdlc.py drift" in step0
    assert "sdlc.py record" in step5 and "sdlc.py reset" in step5
    assert "uninstall" not in " ".join(
        frontmatter.load(ROOT / "skills/setup/SKILL.md")["allowed-tools"]
    )


def test_uninstall_plans_before_its_gate_and_removes_after() -> None:
    text = (ROOT / "skills" / "uninstall" / "SKILL.md").read_text(encoding="utf-8")
    before, after = text.split("WAIT for explicit approval")
    assert "sdlc.py uninstall --check" in before and "sdlc.py uninstall --check" not in after
    assert "sdlc.py uninstall\n" in after
