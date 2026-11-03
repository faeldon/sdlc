---
id: 039
slug: factory-evidence-and-replay
kind: plan
created: 2026-11-04
updated: 2026-11-04
---

# 039 — The factory proves its builds, replays its reviewers, and reviews old code · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

Builds seed 2026-11-03-12 only (split at the spec). The code is as 038 left it: `factory.py`'s
`REVIEWERS`, `ROLES`, `DEFAULTS`, `read_rounds`, `cmd_verdicts`; the build skill; the reviewers'
shared "Later rounds" section; `tests/test_factory.py`'s `_build_report`, `_review` and `_round`
helpers and the tests pinning three default reviewers and `max_runs` 17.

- `plugins/factory/scripts/factory.py`: `behaviour` in `ROLES`, `REVIEWERS` and the default
  `reviewers` (R3, R5); `EVIDENCE`, `EXIT_RE`, `read_evidence(text, where)` (R2); `cmd_verdicts`
  checks `build/round-<built>.md` and every `behaviour.md` (R2, R4).
- `plugins/factory/agents/builder.md`: the `## Evidence` format (R1).
- `plugins/factory/agents/reviewer-behaviour.md` (new) (R3, R4).
- `plugins/factory/skills/build/SKILL.md`: Steps 0 and 1 (R5).
- `skills/ship/SKILL.md` Step 0 (R6).
- `plugins/factory/README.md`, `AGENTS.md` (R7).
- `.sdlc/work/inbox.md` at ship: seeds -13, -14 (R8).
- Tests: `tests/test_factory.py`, `tests/test_skills.py`.

## Work order

1. `factory.py` evidence check and role; test helpers write valid evidence; pinned defaults (four
   reviewers, `max_runs` 20); evidence tests.
2. Agents; skill tests (`AGENT_TOOLS`, the never-run rule, the evidence format).
3. Build skill, ship Step 0, README, AGENTS.md; skill tests for R6.
4. `./check.sh` with its exit code read directly.

## Tests

- R2: a good report passes; missing section, empty section, a `$ ` without `exit:` stop, naming
  the file.
- R3: `reviewer-behaviour.md` tools exactly Read/Grep/Glob/Bash; it says it never runs
  `checks.md`.
- R4: a `behaviour.md` without evidence stops, naming it.
- R5: four defaults; a host's own `reviewers` kept; `max_runs` 20.
- R6: ship Step 0 names `## Evidence` and `behaviour.md`.
- R1, R7, R8: read at ship.

## Rollback

`git revert` of the ship commit. Nothing outside the repo. A host mid-run when it upgrades stops
on its next `verdicts` if the builder's last report lacks evidence; resuming the builder for a
report with it continues the run.
