---
id: 072
slug: factory-land
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 072 — Land a batch of ready factory changes with one stop, or none when nothing is risky · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `sdlc-path` (its own version's `sdlc.py`, clone or cache,
  refused on a version mismatch) and `_sdlc()` (runs it, env cleaned of `SDLC_CLOSE_RAN`,
  `SDLC_OWN_SCRIPT`, `VIRTUAL_ENV`); `land-check` (signals, exclusions, `clear`); `land-message`;
  `land <NNN> --by` (impact, `sdlc.py ship`, the commit, `sdlc.py base`) and `land <NNN> --close`
  (`sdlc.py close` from the main checkout); `resolve` / `resolve --continue`; `agent --task
  resolve | land-review | land-verify`; `land-verdicts`; `land.auto` (base branch) and
  `land.batch`.
- `plugins/factory/skills/land/SKILL.md` (new): the batch, its one WAIT passing itself when clear,
  each change landed in order, the report.
- `plugins/factory/agents/approver.md` (`- IMPACT:` line), `builder.md` (the resolve task),
  `build/SKILL.md`, reviewers (the land review reads the rebased or resolved diff).
- `scripts/metrics.py`: `GATES`/`SKILL_STAGE` for land, `_supervised` keeps a typed land naming
  the change, `summarize(..., landed=)` (`REQUIRED` with `land`, `auto` outside `stops`),
  `happy()`'s `auto` marks.
- `scripts/sdlc.py`: `measure_change()` reads `Sdlc-Landed` from the branch tip.
- Tests: `tests/test_factory.py`, `tests/test_metrics.py`, `tests/test_skills.py`.
- Docs: `AGENTS.md`, the factory README, `docs/REFERENCE.md`.

## Work order

1. `factory.py`: `sdlc-path`, `_sdlc()`, the `land` config; tests.
2. `factory.py`: `land-check`, `land-message`; tests.
3. `factory.py`: `land --by`, `land --close`, `resolve`, the new agent tasks, `land-verdicts`; an
   end-to-end scratch batch with a conflict; tests.
4. `metrics.py` and `measure_change()`; tests.
5. The land skill, the agents' and build's text; skills tests.
6. Docs; `./check.sh`.

## Tests

- R1: `sdlc_path` for a clone, a cache layout in a tmp dir, and a version mismatch.
- R2–R4: `land-check` for each signal and exclusion, `clear`, `land.batch`, `land.auto` from the
  base branch.
- R5–R7: an end-to-end batch in a scratch repo (`archive.target` none, no push): two changes on
  one file, the second's rebase conflicting, resolved by a fake `claude`, reviewed, both closed,
  `Sdlc-Landed: by=auto` on each; a batch stopped by a refusal; the deep-diff note line.
- R8: `REQUIRED` with `land`, `auto=` round-trip, `happy`'s `auto`, a typed land naming two changes.
- R9: the skills tests with `land` in `GATED`, `READS_CONFIG` and the skill list; the docs read.
- R10: `./check.sh`.
- Manual (paid): two ready scratch factory changes, `/sdlc-factory:land` from a fresh session.

## Rollback

`git revert <sha>`. Not covered: changes a real batch already landed and pushed, which stay landed,
each with its own `Close` commit.
