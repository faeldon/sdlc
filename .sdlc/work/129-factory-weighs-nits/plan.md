---
id: 129
slug: factory-weighs-nits
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 129 — The factory weighs its agents' nits and files them as [nit] entries · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - `NIT_WEIGHT_RE`, `NIT_COSTS`/`NIT_VALUES` (copies of `sdlc.py`'s), the reason strings.
  - `read_rounds()`: each nit a dict `{text, theme, cost, value}`, weights stripped.
  - `_rounds_at_depth()`: mark each round that starts a run (`r["start"]`, restart or upgrade).
  - `handed_nits(rounds, n)` (new): the `fix` nits of round `n` a rework handed on.
  - `agent_findings()`: the weights → disposition, `fixed` for a handed nit not raised again, the
    no-path rule and the cap of 5 last; `filed` nits carry title, paths, pass, theme, cost, value.
  - `cmd_carry()`: `high` and `L` nits join `wanted` as `<role>: <text>`.
  - `finding_section()`: `Theme:`/`Cost:`/`Value:` after `Disposition:` on a filed nit.
  - `loop_state()`: `handed`, round N's `fix` nits, for the rework prompt and the next review.
  - `_task()`: the rework lists `handed`; round N+1's review names what it was handed.
  - `land_parts(folder, pre, root, cfg)`: a `nits` part from `agent_findings()`; its callers
    (`land_signals()`, `cmd_land_check()`, `_dispose()`) pass the worktree and config.
  - `land_signals()`: `nits to file: <n>[, <m> past the cap of 5]`.
  - `land_question()`: the `its agents' nits filed as shown` clause.
  - `_dispose()`: one `next-entry` for seeds, bugs and nits; nits appended; a rerun skips one
    already filed (`filed_nit()`, new). It now returns `(filed ids, why)`, and `cmd_land()`
    reports the ids as `filed_nits`.
  - `land_parts()` takes `root` and `cfg` as optional arguments: the tests that call it on a bare
    folder, with no repo, keep working, and get an empty `nits`.
- `plugins/factory/agents/reviewer-{code,security,test}.md`: end each `- NIT:` with
  `{<theme> <cost> <value>}`, by the process doc's rubric.
- `plugins/factory/skills/land/SKILL.md`: Step 0/1 show `nits`, Step 2's fullest question,
  Step 3's `filed_nits`, the description.
- `plugins/factory/README.md`: the reviewers weigh nits; the landing files them.
- `docs/REFERENCE.md`: the register's `[nit]` entries also come from the factory's landing.
- `skills/ship/factory.md`: Step 4 proposes the agents' filed nits as `[nit]` entries.
- `guide/review.md` (nits row), `guide/process.md` (register table), `templates/inbox.md` (note),
  then `scripts/sdlc.py record` for `.sdlc/setup.json`.
- Tests: `tests/test_factory.py` (R1–R7), `tests/test_land.py` (R8–R11), `tests/test_skills.py`
  (R12, R13's land skill text).

Reused, not re-derived: `LEAD_RE` and `first_sentence()` for title and paths (as
`finding_section()` uses them), `finding_pass()` for the pass, `NIT_RE` for the register's
`[nit]` headings, `_sdlc(["next-entry", "--count", …])` for ids, `read_restarts()`/
`read_upgrade()` (through `_rounds_at_depth()`) for the run's first rounds.

## Work order

1. **Weights read** (R1): `NIT_WEIGHT_RE`, nit dicts in `read_rounds()`, `agent_findings()` reading
   `nit["text"]`; existing nit test moved to the dict shape. Nothing changes disposition yet.
2. **Disposition** (R2, R3, R5, R6, R7): `agent_findings()` weighs; `finding_section()` writes the
   weights; `cmd_carry()` carries `high`/`L`. Handed nits read from rounds (`handed_nits()`).
3. **Hand-off** (R4): `loop_state()`'s `handed`; the rework and review prompts.
4. **Landing shows** (R8, R9): `land_parts()`'s `nits`, the signal, the question clause.
5. **Landing files** (R10, R11): `_dispose()` and `cmd_land()`'s `filed_nits`.
6. **Words** (R12, R13): reviewers' prompts, the land skill, ship's side file, README, guides,
   template, `record`.

"Handed" is read from the rounds alone: round N's `fix` nits were handed when round N's verifier
kept a change (so a rework ran, R4) and round N+1 has a build that isn't a restart's or an
upgrade's first round. A build answering a blocking decision in place of the rework is counted as
handed too: it is the build the rework would have been, and its reviewer is still asked to raise
the nit again if it wasn't made.

## Tests

- R1: `test_a_nit_is_read_with_its_weights`; `test_nit_words_are_sdlcs` pins the copies.
- R2: `test_carry_disposes_each_nit_by_its_weights`.
- R3: `test_carry_never_leaves_a_fix_for_ship_to_refuse`.
- R4: `test_rework_hands_the_builder_its_cheap_nits`, `test_a_round_with_only_nits_is_never_reworked`.
- R5: `test_a_nit_not_raised_again_is_still_filed`.
- R6: `test_carry_caps_the_nits_it_files_at_five`.
- R7: `test_carry_writes_each_agent_finding_once_by_its_role`, extended.
- R8: `test_land_check_shows_the_nits_it_would_file`, `test_land_question_names_the_nits`.
- R9: `test_nits_to_file_keep_the_gate_the_persons`.
- R10: `test_a_landing_files_the_nits_sdlc_reads`.
- R11: `test_a_landing_rerun_files_each_nit_once`.
- R1's prompts: `test_the_factory_reviewers_weigh_their_nits` (`tests/test_skills.py`).
- R12: `test_ship_files_the_agents_recorded_nits`, which also checks the land skill's text (R13).
- R13: `checks.md`'s acceptance check for the guides' and the template's wording;
  `test_every_review_dimension_names_both_ways` (unchanged); `sdlc.py drift` in the gate.

## Rollback

`git revert` undoes the code and docs. Not undone: `[nit]` entries a landing already filed in a
host's register, which are ordinary entries: retire each by a ship that fixes it, or delete its
section from `.sdlc/work/inbox.md` by hand. Findings already written keep their extra
`Theme:`/`Cost:`/`Value:` lines, which `sdlc.py` ignores.
