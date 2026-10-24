"""The default process doc still captures the core of Anthropic's AI-native SDLC playbook.

defaults/SDLC.md is what /sdlc:setup gives a repo, and it says it is adapted from the playbook.
This holds it to that: every core prescription below must still be in it, in substance. The doc
may add to the playbook freely; what it may not do is drop a prescription without this file
saying so, as a deliberate scope-out with its reason.

Source: https://claude.com/blog/the-ai-native-sdlc-playbook, read 2026-10-23. The prescriptions
are recorded in substance, and the phrases matched are the doc's own, so the test checks the doc
rather than the wording of a page it can't fetch offline. When the playbook changes, re-read it
and update PRESCRIPTIONS and SCOPED_OUT here first; then the doc follows.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "defaults" / "SDLC.md"
PLAYBOOK_URL = "https://claude.com/blog/the-ai-native-sdlc-playbook"

# The playbook's plays, in its order. Deploy is split between Ship (review, approval) and the
# release loop (authorization): /sdlc:release prepares a release locally, and /sdlc:publish, behind
# its own approval, is the one step that pushes.
PLAYS = ("Loop", "Plan", "Design", "Build", "Test", "Deploy", "Maintain")

# (play, what the playbook prescribes, phrases the doc must contain to capture it). Each phrase is
# a regex, matched case-insensitively against the doc with its line breaks folded into spaces.
PRESCRIPTIONS = [
    (
        "Loop",
        "Each stage commits an artifact the next stage reads: intent, spec, plan",
        [
            r"\*\*1 Plan\*\*.*`intent\.md`",
            r"\*\*2 Design\*\*.*`spec\.md`",
            r"\*\*3 Build\*\*.*`plan\.md`",
        ],
    ),
    (
        "Loop",
        "The process is a loop: what maintenance finds re-enters as a new intent",
        [r"\*\*6 Maintain\*\*.*a new `intent\.md`", r"This is the loop closing"],
    ),
    (
        "Loop",
        "Humans stay accountable for every judgment call: gates, never standing approval",
        [
            r"Confirm before write",
            r"per-invocation, never standing",
            r"exactly one step headed \*\*WAIT\*\*",
        ],
    ),
    (
        "Plan",
        "Capture what is wanted, why, and the constraints as intent.md, before any design",
        [r"`intent\.md`: why", r"Problem · Outcome · Affected · Constraints · Open questions"],
    ),
    (
        "Plan",
        "Repeated processes are encoded as skills",
        [r"The process is a plugin", r"/sdlc:intent"],
    ),
    (
        "Design",
        "Claude turns the accepted intent into spec.md, inside the organisation's policies",
        [
            r"/sdlc:spec",
            r"inside the invariants in the policy doc",
            r"Requirements · Design · Contracts touched",
        ],
    ),
    (
        "Design",
        "A human decides whether the spec proceeds",
        [r"drafts `spec\.md`, gates"],
    ),
    (
        "Build",
        "Nothing is implemented without an accepted plan, made in plan mode, saved as plan.md",
        [
            r"Nothing is implemented without an accepted plan",
            r"plan mode already \*is\* this stage",
            r"save it as `plan\.md`",
        ],
    ),
    (
        "Build",
        "When implementation departs from the plan, plan.md is updated in the same commit",
        [r"departs from the plan, update `plan\.md` in the same commit"],
    ),
    (
        "Build",
        "CLAUDE.md is under a page, in git, and a mistake made twice becomes a correction in it",
        [r"under a page, checked into git", r"same mistake twice, the correction goes into it"],
    ),
    (
        "Build",
        "A skill is an advisory control; a rule that must always hold needs a hook or check",
        [r"A skill is a control, but an advisory one", r"needs a hook or a test"],
    ),
    (
        "Build",
        "One git worktree per session working in parallel",
        [r"one worktree per change", r"`\.claude/worktrees/NNN-slug`"],
    ),
    (
        "Test",
        "Always give Claude a way to verify its own work: one command that fails on error",
        [
            r"Always give Claude a way to verify its own work",
            r"\*\*The gate\*\* \(`commands\.check`\)",
        ],
    ),
    (
        "Test",
        "Healthy outputs are listed in CLAUDE.md",
        [r"the policy doc says what healthy output"],
    ),
    (
        "Test",
        "A bug is fixed by committing a failing test first, then fixing without editing it",
        [r"A bug fix starts with a failing test", r"without editing the test"],
    ),
    (
        "Test",
        "Each incident becomes a permanent check",
        [r"Every near-miss becomes a test"],
    ),
    (
        "Deploy",
        "Review policy lives in REVIEW.md, in passes, with a rule for Important versus nit",
        [r"`\.sdlc/REVIEW\.md`", r"Important or Nit", r"nits cap at 5"],
    ),
    (
        "Deploy",
        "Review findings don't approve a change on their own; a person does",
        [r"\*\*one approval\*\*"],
    ),
    (
        "Deploy",
        "The agent may act up to the production gate and cannot pass it",
        [r"never pushes and never deploys"],
    ),
    (
        "Deploy",
        "In production, the agent prepares the release and the release manager authorizes it",
        [
            r"The agent prepares the release and a person authorizes it",
            r"`/sdlc:release`.*All local",
            r"`/sdlc:publish`.*the one step that sends anything anywhere",
        ],
    ),
    (
        "Maintain",
        "Detection stays deterministic, before a model is asked anything",
        [r"Deterministic detection before a model is asked anything"],
    ),
    (
        "Maintain",
        "Findings are tiered: log, diagnose, propose; larger ones become an intent",
        [r"\*\*Report\*\*", r"\*\*Fix inline\*\*", r"\*\*Write an intent\*\*"],
    ),
    (
        "Maintain",
        "Dismissing a finding requires a reason",
        [r"why it needs nothing more"],
    ),
    (
        "Maintain",
        "Name one source of truth for every artifact",
        [r"Each artifact has one source of truth"],
    ),
    (
        "Maintain",
        "Measure the loop: time in stages, rework, failures found late",
        [r"Signals worth watching", r"\*\*Rework\.\*\*", r"\*\*Age of open intents\.\*\*"],
    ),
]

# What the playbook prescribes that this plugin deliberately doesn't carry, and why. Each is a
# decision, not an oversight; take one out of here only by adding it to PRESCRIPTIONS.
SCOPED_OUT = [
    ("Design", "Front-end mocks in Claude Design", "a product, not a process step a repo adopts"),
    ("Build", "Auto mode for routine work", "a session setting each person chooses"),
    ("Build", "Subagents in .claude/agents/", "how a session works, not a stage's output"),
    ("Build", "Formatter and protected-path hooks", "the repo's own hooks; setup leaves them be"),
    (
        "Test",
        "Continuous evals in CI on 20-50 real tasks",
        "needs CI, which the plugin doesn't run",
    ),
    ("Test", "Visual check loops for UI", "specific to front-end repos"),
    ("Deploy", "Claude reviewing PRs and @claude comments", "the plugin reviews before the commit"),
    ("Deploy", "Hooks as approval gates, managed settings", "org policy, outside a repo's plugin"),
    ("Deploy", "CI/CD with claude -p, MCP per environment", "CI runs outside the repo's sessions"),
    ("Deploy", "Gate wait times from OpenTelemetry, DORA", "needs telemetry the plugin can't see"),
    ("Maintain", "Control bands (1σ/2σ/3σ) in bands.yaml", "a monitoring system's job"),
    ("Maintain", "Claude Tag in incident channels", "a chat integration, not a repo process"),
]


def _doc() -> str:
    """The doc with its line breaks folded, so a phrase can wrap without failing the match."""
    return re.sub(r"\s+", " ", DOC.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "play, prescription, phrases", PRESCRIPTIONS, ids=[p[1][:60] for p in PRESCRIPTIONS]
)
def test_the_doc_captures_the_prescription(play: str, prescription: str, phrases: list[str]):
    doc = _doc()
    missing = [p for p in phrases if not re.search(p, doc, re.IGNORECASE)]
    assert not missing, f"[{play}] {prescription}: defaults/SDLC.md lacks {missing}"


def test_every_play_is_accounted_for() -> None:
    """Each play has a prescription the doc captures, so none can fall out of it entirely."""
    assert {p[0] for p in PRESCRIPTIONS} == set(PLAYS)
    assert {s[0] for s in SCOPED_OUT} <= set(PLAYS)


def test_every_scope_out_says_why() -> None:
    assert all(len(reason) > 10 for _, _, reason in SCOPED_OUT)


def test_the_doc_names_its_source_and_all_six_stages() -> None:
    doc = _doc()
    assert PLAYBOOK_URL in doc
    for n, stage in enumerate(("Plan", "Design", "Build", "Test", "Ship", "Maintain"), start=1):
        assert f"**{n} {stage}**" in doc
        assert re.search(rf"### Stage {n} — {stage}", doc)


def test_the_doc_describes_three_loops() -> None:
    """The plugin's own addition, not a prescription: the playbook describes one loop, and the
    doc nests two slower ones around it. Kept apart from PRESCRIPTIONS, which holds only what the
    playbook itself says, and with the map of where it is thin, so that stays said."""
    doc = _doc()
    loops = doc.split("## Three loops")[1].split("\n## ")[0] if "## Three loops" in doc else ""
    assert loops, "defaults/SDLC.md has no Three loops section"
    for skill in ("/sdlc:release", "/sdlc:publish", "/sdlc:retro"):
        assert skill in loops
    for phrase in (
        r"seeds become intents",
        r"No loop reaches past the one inside it",
        r"never edits code or skills",
        r"`/sdlc:health` belongs to the change loop",
        r"### Where the playbook fits",
    ):
        assert re.search(phrase, loops, re.IGNORECASE), phrase
    assert doc.index("## The six stages") < doc.index("## Three loops") < doc.index("## Tiers")


def test_a_dropped_prescription_fails(tmp_path: Path, monkeypatch) -> None:
    """The check can fail: the doc without its plan rule no longer passes."""
    text = DOC.read_text(encoding="utf-8").replace("Nothing is implemented", "Little is built")
    (tmp_path / "SDLC.md").write_text(text, encoding="utf-8")
    monkeypatch.setattr(f"{__name__}.DOC", tmp_path / "SDLC.md")
    play, prescription, phrases = next(p for p in PRESCRIPTIONS if "accepted plan" in p[1])
    with pytest.raises(AssertionError):
        test_the_doc_captures_the_prescription(play, prescription, phrases)
