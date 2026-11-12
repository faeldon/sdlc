---
id: 052
slug: skill-tool-counts-as-stage
tier: 1
impact: patch
stage: shipped
created: 2026-11-12
updated: 2026-11-12
shipped: 2026-11-12
idea:
depends_on:
fixes: [2026-11-12-5]
serves: [O3]
---

# 052 — A skill started through the Skill tool counts as its stage

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Bug 2026-11-12-5: close's measure step missed 051's ship stage. The `Close` commit 54bec13 reads
`Sdlc-Coverage: transcripts=36 stages=intent,build,close`, with `ship_runs=0` and `Sdlc-Happy:
ship=unknown`, though `/sdlc:ship` ran in that session and committed 18160df. Ship's edits, checks
and stops were counted under build (`gate=2`, `reply=approve,approve`, `edits=…,doc:7`).

`SKILL_RE` (`scripts/metrics.py:75`) finds a stage only in the `<command-name>/sdlc:…</command-name>`
line the harness writes when the person types the command. The ship prompt reached the session as
plain text (` /sdlc:ship`, with a leading space), so the session started the skill with the Skill
tool, which leaves an assistant `tool_use` (`name: "Skill"`, `input.skill: "sdlc:ship"`) and a meta
user message holding the skill's text, and `metrics.py:505` skips meta messages. No `skill` event
is recorded, so the stage spans, `ship_runs`, `Sdlc-Happy` and the stops O3's measure reads are all
off for that change.

## Outcome

- A skill the session starts with the Skill tool counts as its stage, as one the person types does:
  a transcript like 051's gives `stages=…,ship,…`, `ship_runs=1`, and ship's stops and edits under
  ship.
- A typed command that also yields a Skill tool call is counted once, not twice.
- A test in `tests/test_metrics.py` builds both transcript shapes and asserts the same stage spans;
  it fails on today's `metrics.py`.
- **Moves O3:** the stops close records per change are counted against the stage that made them,
  so a ship run started by the session no longer adds its stops to build, and the stops-over-target
  figure says where the stops were.

## Affected

- **Area:** close's `measure` step, transcript reading in `scripts/metrics.py`.
- **Files & components:** `scripts/metrics.py` (event extraction near line 505, `SKILL_RE`);
  `tests/test_metrics.py`.
- **Downstream:** the `Sdlc-*` trailers on every later `Close` commit, which `/sdlc:retro` and
  `metrics_summary()` read. Past commits keep the numbers they were written with.
- **Contracts:** "The event list and trailer format are a contract: extend them, never redefine"
  (AGENTS.md, Metrics). This extends what produces a `skill` event; no trailer's format changes.
  `metrics.py` stays pure functions, no import of `sdlc.py`.

## Constraints

- Measuring never refuses: an entry of an unexpected shape is skipped, never raised.
- Numbers and names only: the skill's name, never its text.
- Runs on Windows like the rest (`portable` where the test can be).

## Open questions

- ~~Does the stage start at the assistant's `tool_use` or at the meta message after it? Their
  timestamps differ, and a span's first stop depends on which.~~ Resolved: at the person's message
  when it names the skill (` /sdlc:ship`), as a typed command's does; at the `tool_use` when it
  names none.
- ~~Should the person's plain-text ` /sdlc:ship` reply count as a command reply (`command=True`), as
  a typed slash command does, or stay an ordinary human reply?~~ Resolved: a command, so no stop,
  as typed.
- ~~Should a Skill tool call for a skill outside `sdlc`/`sdlc-factory` be ignored, as `SKILL_RE`'s
  pattern ignores it now?~~ Resolved: ignored; both read one `PLUGIN_SKILL` pattern.

## Approach

Where `metrics.py` reads assistant entries, record a `skill` event for a `tool_use` named `Skill`
whose `input.skill` matches `sdlc(-factory)?:…`, unless a typed `<command-name>` for the same skill
came just before it. Add a test in `tests/test_metrics.py` with both shapes.
