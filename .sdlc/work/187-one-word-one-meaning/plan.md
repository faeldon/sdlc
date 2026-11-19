---
id: 187
slug: one-word-one-meaning
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 187 — One meaning per word, and sdlc.py check becomes sdlc.py vet · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `cli_check` → `cli_vet` (`@command("vet", …)`), `HELP_ORDER`, `READ_ONLY`
  (so `ALLOW_RULES` follows), the module docstring (drop `check --json`), the `status` nudge
  comment, the `CONFIG_KEYS`/readiness comments for `commands.build` ("the slow gate").
- `skills/{status,ship,spec,setup,health}/SKILL.md`: bash blocks and `Bash(...)` rules to `vet`.
- `.claude/settings.json`, `evals/fixtures/{set-up,product}/change/.claude/settings.json`: the
  `vet` allow rule.
- `plugins/factory/agents/verifier.md` → `agents/arbiter.md` (`git mv`), `prompts/verify.md` →
  `prompts/arbitrate.md`, `prompts/land-verify.md` → `prompts/land-arbitrate.md` (`git mv`).
- `plugins/factory/scripts/factory.py`: `ROLES`, `FIXED_MODELS`, `--role` choices, `TASKS`,
  `TASK_STEP`, `ROUND_PURPOSE`, `PROMPT_PARTS`/`TASK_PROMPTS`, `LAND_STEPS`, the mend's `arbitrate`
  part, `start`'s summary, a new `RENAMED` map applied in `read_mended()`, the session-role reader,
  and the step readers. Writers write only the new words.
- `plugins/factory/scripts/landing.py`: `RUN_STEPS` key `verify` → `arbitrate`, `--task
  land-arbitrate`, `land-verdicts`' `next`, mendable role `arbiter`; the landing question's
  "accepted as shown" → "approved as shown".
- `plugins/factory/scripts/run_state.py`: `next` `verify` → `arbitrate`, mendable role `arbiter`.
- `scripts/factory_records.py`: `LAND_STEPS`, the `RENAMED` copy, gate record `command` and tail
  (`read_gate_attempts()`), and reading old words through `RENAMED`.
- `scripts/board.py`, `scripts/board.html`: `TRACK`/`AT`/`LAND_TRACK`/`LAND_AT`/`LAND_TIMED`
  labels, `step_samples()` through `RENAMED`, the round chip text, the card's `acceptance: N`
  (with the last `land-accept.md` verdict), and the gate badge's command and summary
  (`hand_gate()` and the factory's gate reading).
- `scripts/retro.py`: the *Agents by role and model* grouping through `RENAMED`.
- `plugins/factory/scripts/factory.py`'s `read_gate_file()`: `command` and `tail`, pinned with
  core's copy.
- Docs and prose: `docs/FEATURES.md` (*Vocabulary* entries), `docs/REFERENCE.md` (*After an
  update*, the slow gate, `vet`), `docs/CONTRIBUTING.md`, `docs/PROCESS.md`, `AGENTS.md` (vet,
  approval, 100 columns), README.md, `guide/process.md` and `guide/review.md`, `defaults/SDLC.md`,
  `.sdlc/SDLC.md`, `templates/findings.md`, `skills/**`, `agents/*.md`, the factory README,
  agents, prompts and skills, the three manifests' descriptions. `sdlc.py record` rerun.
- Tests: `tests/test_feature_map.py` (two term tests, vocabulary entries, AGENTS.md width),
  `test_sdlc.py`, `test_adoption.py`, `test_evals.py`, `test_acceptance.py`,
  `test_config_resolution.py`, `test_deprecations.py`, `test_next_up.py`, `test_retro.py`
  (`vet`), `test_readiness.py` (missing vet rule), `test_factory.py`, `test_prompts.py` and
  `tests/prompts/*verifier*`/`*verify*` (regenerated), `test_skills.py`, `test_board.py`,
  `test_modules.py`, `test_land.py`, `test_train.py`, `train_driver.py`; nits in `test_metrics.py`
  and `test_skills.py`.

## Work order

1. **The command (R1–R5).** Tests first: `test_vet_strict_fails_on_a_problem`,
   `test_check_is_no_longer_a_command`, `test_a_host_with_only_the_check_rule_is_missing_the_vet_rule`.
   Then the rename and every caller (skills, settings, fixtures, tests that ran `check --strict`).
2. **The arbiter (R12–R16).** Tests first: `test_the_verifier_role_and_task_are_gone`,
   `test_models_verifier_is_an_unknown_role`, `test_the_arbiter_writes_verified_md`, the old-record
   tests. Then `git mv` the agent and prompts, rename roles/tasks/steps, add `RENAMED` in both
   modules, regenerate the prompt snapshots, update every test table.
3. **The board (R17–R19).** Tests first on the state JSON and `board.html`'s text, the card's
   acceptance count, and the gate badge. Then the tables, `card_reading()`, `read_gate_attempts()`
   / `read_gate_file()` and `hand_gate()`.
4. **The words (R6–R11).** Tests first: the vocabulary entries, the two term tests with their
   fixture. Then reword the prose set until both pass; the guide heading in three places, and
   `sdlc.py record`.
5. **Nits and release (R20–R23).** AGENTS.md width test, the two test comments, REFERENCE.md's
   *After an update*, `impact: minor` in the intent.

## Tests

- R1: `test_vet_strict_fails_on_a_problem`; the existing `check --strict` tests moved to `vet`.
- R2: `test_check_is_no_longer_a_command`.
- R3: `test_a_host_with_only_the_check_rule_is_missing_the_vet_rule`.
- R4: `test_skills.py`'s rule tests; R11's term test; `test_the_set_up_fixture_is_complete`.
- R5: R11's term test (`check --strict` in the docstring).
- R6: `test_every_vocabulary_term_has_an_entry`.
- R7–R10: `test_no_doc_uses_a_retired_phrasing`, with its fixture proving each pattern.
- R11: `test_no_file_names_a_retired_name`.
- R12: `test_the_verifier_role_and_task_are_gone`, `test_skills.py`'s agent tables,
  `test_prompts.py`, `test_modules.py`'s `LAND_STEPS` pin.
- R13: `test_the_arbiter_writes_verified_md`.
- R14: `test_an_old_verifier_row_counts_as_arbitrate`, `test_an_old_verify_step_sits_at_arbitrate`,
  `test_an_old_verifier_mend_counts_for_its_round`, `test_agents_by_role_groups_verifier_with_arbiter`,
  `RENAMED` pinned by `test_every_shared_name_is_the_factorys`.
- R15: the asserts on `start`'s summary in `test_skills.py` and `test_factory.py`.
- R16: `test_models_verifier_is_an_unknown_role`.
- R17: `test_board.py`'s track and chip asserts.
- R18: `test_a_card_counts_acceptance_and_its_last_run`.
- R19: `test_the_gate_badge_names_its_command_and_result`; `test_modules.py`'s shared cases.
- R20: `test_agents_md_fits_100_columns`. R21, R22: the spec's greps, as acceptance checks.
- R23: an acceptance check on REFERENCE.md's *After an update* and the intent's `impact: minor`.

## Rollback

`git revert` undoes all of it. Nothing outside the repo is written. A host that took setup's new
`sdlc.py vet *` rule keeps it after a revert (harmless; it allows a command that would no longer
exist) and would need `sdlc.py check *` back, which setup proposes again. A run whose records were
written with `arbiter`/`arbitrate` would not read under a revert: finish or restart it first.

## As built

Where the build departed from the plan above:

- **R11 and R23 collide.** R23 has REFERENCE.md's *After an update* name `sdlc.py check` to say
  it is gone; R11's retired-names test bans the name in every prose file. The test exempts that
  one paragraph (`RENAME_NOTE`, the lines from its bold lead to the next blank line) and fails if
  the paragraph disappears, so the exemption can't outlive it. The spec's own verification grep
  therefore still prints those lines, and the `[models] verifier` line R23 asks for.
- **`RENAMED` is read in more places than the spec listed**: `landing()` (whether a landing is in
  flight) and the landing's `land_mended()`, besides `mended()`, `session_roles()`, the board's
  two step readers, `step_samples()` and the retro's grouping.
- **`test_modules.py`'s shared-name pin now compares dicts**, so `RENAMED` is pinned by the same
  test as the other shared names, and `TAIL_RE` is shared too. The two gate readers are pinned by a
  new table of records (`test_both_gate_readers_read_the_command_and_tail_alike`).
- **The card's acceptance verdict** comes from a new `factory_records.accept_verdict()`, read in
  `card_reading()`, so only a factory card carries `accept`; a hand-built card shows the count.
- **More "gate" meaning a person's yes** was reworded than R7 lists (the land skill's "the gate
  passes itself", REFERENCE.md's metrics and `auto_landed` lines, the retro, intent and health
  skills, the factory README's *The gates* bullet, now *The approvals*), and "build check" became
  "the slow gate" in ship's steps, the setup drafts, README.md and the landing question.
- **The landing prompt `land-checks.md`** now says "acceptance checks" and backticks `checks.md`,
  so its snapshot was regenerated with the arbiter's.
- **AGENTS.md's factory paragraph** was rewrapped whole, not three lines, to keep it under 100
  columns without breaking an inline code span.
- **A resumed arbiter reads `runs/verifier.sessions`** when no `arbiter.sessions` exists, so a
  run in flight across the update can still mend its arbiter
  (`test_an_old_verifier_session_is_resumed_as_the_arbiter`). New sessions are written only as
  `arbiter.sessions`.
