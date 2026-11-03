---
id: 036
slug: review-depth-by-risk
tier: 2
impact: minor
stage: shipped
created: 2026-11-03
updated: 2026-11-04
shipped: 2026-11-04
idea: 2026-11-03-4
depends_on:
serves: none
---

# 036 — Review depth set by what a change touches

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Ship reviews every change the same way, in the same session that built it, and asks how to undo
it in one place only. The Claude Code team's account of code review (Oct 2026) names all three:

- **Risk isn't set by the change.** The tiers size the paperwork (intent alone, or spec and plan),
  not the risk. A Tier 1 change to a release script, `cmd_close()`'s merge, or a host's CI workflow
  gets the same review as a README fix. The post's rule is "the change sets the tier, not the
  author", with paths that always get a closer look. Nothing in `.sdlc/config.toml` says which
  paths those are, so `preflight` can't tell a diff that touches them.
- **The reviewer is anchored on the builder.** Ship runs in the session that wrote the code, its
  reasoning in context. The post's step before every PR is "a second agent reviews the diff in a
  fresh context". Only the factory's changes get reviewers that didn't write them, and only through
  `sdlc-factory`.
- **How to undo is asked in one place.** `plan.md`'s Rollback covers Tier 2. A Tier 1 change, or
  a Tier 2 whose plan says "git revert", can still touch what a revert doesn't undo: data written
  elsewhere, a published artifact, a host's files setup copied. Ship's commit says nothing of it.

This takes in seeds 2026-11-03-4, -5 and -6 together, as phase 2.

## Outcome

- A host can list sensitive paths in config, and `preflight` reports a `risk` part: the changed
  paths that match, and whether the diff is sensitive.
- On a sensitive diff the build check always runs, an Important finding can't be dismissed (only
  fixed), and ship's WAIT question names the sensitive paths (`ship_question()` renders it, a test
  pins it).
- Ship runs one fresh-context review (a subagent given only the diff, the intent or spec and the
  review docs), always on a sensitive diff. Its findings join `findings.md` marked as the fresh
  reviewer's, and one ship's own passes don't confirm is shown with why.
- When the diff touches what a revert doesn't undo, ship asks for a `How to undo:` paragraph in the
  commit message and shows it before the WAIT; for Tier 2 it is drawn from the plan's Rollback.
- `/sdlc:setup` asks for the sensitive list, and `docs/REFERENCE.md` documents the key.
- Seeds 2026-11-03-4, -5 and -6 all leave the register when this ships.

## Affected

- **Area:** config, `preflight`, ship, setup.
- **Files & components:** `scripts/sdlc.py` (`CONFIG_KEYS`, a `_risk_report()` part in
  `cmd_preflight()`, `ship_question()`), `skills/ship/SKILL.md` (Steps 2–5, `Agent` in
  `allowed-tools`), `skills/setup/SKILL.md`, `guide/review.md` and `guide/process.md`, perhaps
  `templates/plan.md`, `docs/REFERENCE.md`, `AGENTS.md`, tests in `test_preflight.py`,
  `test_config_resolution.py` and `test_skills.py`.
- **Downstream:** every host's ship. A host with no sensitive list must ship exactly as now, apart
  from what the fresh review costs. Hosts that rerun setup get the new question.
- **Contracts:** a new config key, read through `load_config()` and named in `READS_CONFIG` for the
  skills that read it; narrow `allowed-tools` (`Agent` is a tool, not a `Bash` rule); one WAIT in
  ship, its question worded by `preflight --question`; confirm before writing (a reviewing subagent
  writes nothing); only publish pushes.

## Constraints

- With no `[review] sensitive` set, every existing check, test and question behaves as today.
- The fresh reviewer never edits and never commits: it returns text, and ship decides what becomes
  a finding.
- Sensitivity is mechanical, decided in `sdlc.py` from the diff's paths, never by the model.
- `findings.md`'s format from 035 is extended, never redefined.

## Open questions

- ~~Does the fresh review run on every change, or only on a sensitive one? It costs a subagent a
  ship; the seed calls it a cost question.~~ Resolved: sensitive diffs only, the person's call
  (spec R4).
- ~~How is "a revert doesn't undo it" known: a second config list (`[review] irreversible`), the
  same sensitive list, or the process doc's prose?~~ Resolved: a second list, since the two are
  different questions (spec R1, R9).
- ~~How is a fresh-review finding marked in `findings.md` (a `By: fresh` line, or a pass of its
  own), and does the trailer count it apart?~~ Resolved: a `By: fresh` line, counted as `fresh=`
  and `fresh_wrong=` (spec R7).
- ~~Does a sensitive diff also raise the tier (a Tier 1 touching a sensitive path becomes Tier 2),
  or only deepen the review?~~ Resolved: only deepens the review (spec R5).
- ~~Can the fresh review run where the `Agent` tool isn't available, or does ship then say plainly
  it was skipped?~~ Resolved: skipped, said in Step 4, `findings.md` and the WAIT (spec R8).
- ~~Seeds -5 and -6: deleted in this change's commit, as phase 1's were.~~ Resolved: yes, with -7's
  `After:` line (spec R14).
