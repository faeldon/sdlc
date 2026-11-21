---
id: 216
slug: autopilot
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 216 — Autopilot: the factory runs from seed to landing while the person is away · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/autopilot.py` (new): loaded by path like `landing.py` and bound to
  `factory.py`'s globals as `factory`. It holds `cmd_autopilot()` (`--preview`, `--begin`, `--run`,
  `--cancel`, `--summary`), `autopilot_lock()` (only it takes the lock), `AUTOPILOT_CANCEL`,
  `AUTOPILOT_STEPS` and `TRAIN_COMMANDS`, the config (`autopilot_config()`), `candidates()`, the
  planner's and the intent-writer's filing (`plan_wave()`, `read_wave()`, `open_seed()`),
  `change_step()`/`build_step()`, `answer_calls()`, `finish()`, `hold_causes()`, `landing_due()`,
  `land_batch()`, `review_debt()`, `change_risk()`, `run_loop()` and the summary
  (`write_summary()`).
- `plugins/factory/scripts/factory.py`:
  - `AUTOPILOT_RUN_LOCK`, `AUTOPILOT_RUN_ENV` and `AUTOPILOT_STATE` beside the slot code, and
    `autopilot_running()`, which reuses `_slot_dir()`, `_try_lock()` and `_unlock()`;
  - `BY_VALUES = ("auto", "person", "autopilot")`, and `--by autopilot` on `land`, `train`,
    `write-spec` and `answer`, refused by `by_refusal()` unless `autopilot_running()`;
  - `agent_env()` (round 1): every agent session runs without `AUTOPILOT_RUN_ENV` and
    `TRAIN_RUN_ENV`, so `--by autopilot` is the loop's children's alone;
  - `answer` (new, R5), which works out its own answer (`autopilot_answer()`: a default's
    `KEPT_ANSWER`, a look's `LOOK_SEEN`, a blocking line's first option) so no answer text is
    passed on a command line; `DECIDED_AUTOPILOT`, `read_ledger()`'s `decided_by`, and `ask`'s
    `autopilot` list for the decide skill;
  - `agent` gains the change-less tasks `wave` and `intent` (`--seed`, `cmd_autopilot_agent()`),
    run only under the lock, filed in the run's report folder, kept out of `TASKS` so no change's
    purposes count them; `prompts/autopilot.md` holds their prompts;
  - the `## autopilot` prompt part for `spec`, `build` and `approve` (R20);
  - `"autopilot"` in `DEFAULTS`, so `load_config()` doesn't warn on the table;
  - `_load_autopilot()` and the `autopilot` command.
- `plugins/factory/scripts/landing.py`: `--by autopilot` refused without the lock in `cmd_land()`
  and `_train_begin()`; autopilot lands with signals and disposes as `person` does; close's
  resolved/fixed guard read by a regex for `by=auto` and `by=autopilot`; `land_signals()` gives
  each signal's kind (R25) into a `kinds` list, `SIGNAL_KINDS` (with `unread` for a preflight that
  can't be read); `land-check` prints `signal_kinds`.
- `plugins/factory/prompts/{spec,build,approve}.md`: an `## autopilot` part (`${policy}`).
- `plugins/factory/agents/autopilot-planner.md`, `intent-writer.md` (new): `Read, Grep, Glob`.
- `plugins/factory/skills/autopilot/SKILL.md` (new): one WAIT, the rules R7 names.
- `plugins/factory/skills/decide/SKILL.md`: lists autopilot-decided lines under their own heading.
- `scripts/closing.py`, `scripts/metrics.py`, `scripts/retro.py`: `autopilot` a third value of
  `Sdlc-Landed`, kept apart from `auto` and `person` (R3).
- `scripts/sdlc.py`: `status --json` (round 1: R10 assumed it, and none existed), `next_up()`'s
  items for autopilot's candidates; `load_change()` reads `opened_by:` (`OPENED_BY`, only `autopilot`; any other
  value an error), `status`'s change line says `opened by autopilot`.
- `scripts/factory_records.py`: `DECIDED_AUTOPILOT`, and `autonomy_counts()` counts autopilot's
  lines apart (`autopilot` in each kind's counts), never as asked, kept or changed (R23).
- `.sdlc/config.toml`: `plugins/factory/scripts/autopilot.py` in `[review] sensitive`.
- Tests: `tests/test_autopilot.py` (new); `tests/test_metrics.py`, `tests/test_retro.py`,
  `tests/test_skills.py` (R6, R7, the gated and config tables, the agents' tools table),
  `tests/test_modules.py` (autopilot.py's placement, loading and binding), `tests/test_prompts.py`
  (five golden cases and their recorded copies), `tests/test_factory_decisions.py` (`decided_by` in
  the ledger's record); `tests/test_feature_map.py` follows `docs/FEATURES.md` and
  `docs/PROCESS.md`, and retro's `SKILL_RUNS` classes the skill.
- Docs: `plugins/factory/README.md` (*Autopilot*, the config table, *The approvals*' promise,
  *Mechanism*), `AGENTS.md` (the factory paragraph), `docs/REFERENCE.md` (`[autopilot]`,
  `Sdlc-Landed: by=autopilot`, the retro's counts), `docs/FEATURES.md`, `docs/PROCESS.md`,
  `scripts/metrics.py`'s docstring.

**Departures from the spec**, each a decision in the build report and a line in `notes.md`: the
weight tables are `[autopilot.debt_weights]` and `[autopilot.risk_weights]` (TOML can't hold
`[autopilot.debt]` beside `[autopilot] debt`); the approver isn't rerun after `done` (`agent`
refuses it); a spent debt or risk budget still takes opened changes on to `stage: test`, as the
spec's dry run asks; the `Close` commits are read through `factory.closes()`.

Reused, not re-derived: `run_state.loop_state()` (through `verdicts`) for a build's next step;
`landing._run_one()`/`_run_group()` for subprocesses; `_try_lock()` for the lock; `land_signals()`
for risk; `read_only_command()` for checks; `read_ledger()` for escalations; `run_cost()` for
costs; `_defused()`/`_placeholders()` for the summary; `_base_factory()` for config; `_sdlc()`
and `sdlc_path()` for `new`, `status --json` and the `Close` commits (`git log` on the base).

## Work order

1. **The record of who decided (A: R1–R5, R23).** The lock and `autopilot_running()`;
   `--by autopilot` on `land`, `train`, `write-spec`, and the new `answer`, each refused without
   the lock; `land_message()` writes `by=autopilot`; `read_ledger()`'s `decided_by`; the readers
   in `closing.py`, `metrics.py` and `retro.py`. Tested: the twelve refusal cases, the ledger, the
   metrics and retro values, the three-values grep.
2. **The signals' kinds and the budgets (D: R24–R26).** `SIGNAL_KINDS`, `land_signals()`'s kinds,
   `land-check`'s `signal_kinds`; `review_debt()` and `change_risk()`, pure. Tested by the named
   tests.
3. **Config, preview and begin (B: R8–R10, R28).** `autopilot_config()` from the base branch,
   `--preview` (read-only: question and shown), `--begin`'s refusals and state, `candidates()`.
4. **The loop (B and C: R11–R19, R21, R22, R27).** The planner and intent-writer agents and their
   tasks; opening a seed; the build step table; holds; escalations answered; landing as a train;
   cancel; the summary. The loop's steps go through one function, `run_step()`, which a test
   stands in for, so the loop is driven in process.
5. **The prompts, the skill and the docs (R6, R7, R20).** The `## autopilot` parts; the skill and
   its tests; the decide skill's heading; README, AGENTS.md, REFERENCE.md, FEATURES.md.
6. **Round 4: the person's answers to the escalation (`decision-1.md`).** D1–D7 stand as built.
   - D8: `_default_guards()` adds the base branch's `[review] sensitive` (`factory._sensitive()`)
     after `irreversible`.
   - D9: `sdlc.py`'s `next_up` items carry `issues` (`entry_issues()`, `None` for a line that
     isn't `#N`). `candidates()` takes a seed with any issue only when `--seeds` names it.
     `open_wave()` passes the numbers to `open_seed()`, which writes them as `closes:` through
     `opened_intent()` and holds a seed whose line can't be read before any agent runs.
   - D10: AGENTS.md, the factory README and the skill say `--by autopilot` stops accidental
     inheritance of the marker, not a same-user process that sets it on purpose.

## Tests

- R1 `test_a_second_autopilot_run_is_refused_while_one_holds_the_lock`
- R2 `test_by_autopilot_is_refused_without_the_run_lock` (four commands × three cases)
- R3 `test_landed_by_autopilot_is_its_own_value` (test_metrics), `test_auto_landed_counts_autopilot_apart` (test_retro), `test_land_message_says_by_autopilot`
- R4 `test_landed_values_are_three`
- R5 `test_autopilot_decision_is_ticked_but_never_the_persons`
- R6 `test_only_autopilot_names_by_autopilot` (test_skills)
- R7 `test_autopilot_grants_no_other_skills_writes` (test_skills)
- R8 `test_autopilot_preview_writes_nothing`; the WAIT tests cover the skill
- R9 `test_autopilot_begin_refusals`
- R10 `test_candidates_are_the_ready_group_within_bounds`
- R11 `test_planner_reply_is_checked_by_the_script`, `test_new_agents_have_no_write`
- R12 `test_opened_intent_says_autopilot_opened_it`
- R13 `test_a_change_waits_for_what_it_depends_on`
- R14 `test_build_step_runs_only_the_named_commands`
- R15 `test_landing_waits_for_a_nearly_ready_change`, `test_landing_does_not_wait_past_the_wait`
- R16 `test_cancel_stops_between_steps_and_a_rerun_resumes`
- R17 `test_escalations_are_answered_as_defaults_and_recorded`
- R18 `test_autopilot_never_upgrades`
- R19 `test_held_change_and_its_dependents_never_land`
- R20 `test_prompt_parts_match` (existing) and `test_autopilot_prompt_parts_sent_only_under_the_lock`
- R21 `test_autopilot_runs_no_paid_or_unlisted_command`
- R22 `test_summary_names_every_call_and_no_machine`
- R23 `test_autopilot_records_are_never_the_persons`
- R24 `test_review_debt_is_counted_by_kind`
- R25 `test_every_signal_has_a_kind`
- R26 `test_change_risk_weighs_pushed_and_stacked`
- R27 `test_a_spent_budget_starts_nothing_and_lands_nothing_more`
- R28 `test_autopilot_config_is_read_from_the_base_branch`
- D8 `test_default_guards_hold_the_sensitive_paths`
- D9 `test_a_seed_with_an_issue_is_a_candidate_only_when_named`,
  `test_a_seed_with_an_issue_is_opened_with_closes`, and `test_candidates_come_from_the_real_status_json`
  (the real `status --json` gives `issues`)
- End to end: `test_autopilot_end_to_end` drives the loop in process with a stand-in step runner
  (the train's own tests do the same, since a monkeypatch can't reach subprocesses), so it proves
  the loop's order and records, not a live `claude`.

## Rollback

`git revert` undoes the code. What it does not undo:

- Changes autopilot landed while it ran are commits of their own on the base branch: each is
  reverted by its own `git revert`, found by its `Sdlc-Landed: by=autopilot` trailer
  (`git log --grep 'Sdlc-Landed: by=autopilot'`).
- Pushed landings are on the remote: revert them there the same way.
- Issues `new` opened under GitHub numbering stay open: close them by hand, or `/sdlc:drop` the
  change.
- State in the git common dir (`sdlc-factory-autopilot.json`, `.cancel`, `-run.lock`): remove the
  files, which nothing else reads.
- `.sdlc/reports/autopilot/` is ignored by git: delete the folder.
