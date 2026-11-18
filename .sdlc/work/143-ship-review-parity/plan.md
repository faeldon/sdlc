---
id: 143
slug: ship-review-parity
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 143 — Ship reviews a hand-built change as deeply as the factory reviews its own · plan

> Written by the builder after reading `cmd_preflight()`, `SHIP_BRANCHES`, `findings_entries()`,
> `_findings_from_text()`, `findings_trailer()`, `cmd_ship()`, `ship_question()`, `_gate_jobs_at()`
> and `factory.py`'s `_ui_table()`, `ui_complete()`, `_page_name()` and `shots()`.

## Files to change

- `scripts/sdlc.py`:
  - `_passes_report(root, path, risk)` (new), which joins `cmd_preflight()`'s parts as `passes`. It
    reuses `_risk_report()`, `load_change()`, `is_unfilled()`, `changed_paths()`, `risk_paths()`
    and `factory_enabled()`.
  - `_ui_at(home, trunk)` (new), which reads `[ui]` from `refs/heads/<trunk>` the way
    `_gate_jobs_at()` does. With it go `UI_DEFAULTS`, `_ui_complete()` and `_page_name()`, copies
    of `factory.py`'s.
  - `_current_shots(checkout, change, ui, changed)` (new).
  - `SHIP_BRANCHES` gains `security.md`, `behaviour.md` and `ui.md` after `fresh.md`.
  - `SHIP_PASSES` (new), and `FINDING_BY` and `ship_findings()` take it in.
  - `findings_trailer()` gains `passes=` and `passes_wrong=` after `agents=`.
  - Four note regexes (new). `findings_entries()` gains `passes` and `evidence`.
  - `_findings_from_text()` skips a `## Evidence` section. `findings_evidence()` (new) pairs its
    `$` and `exit:` lines.
  - `cmd_ship()` refuses an applying pass whose note line is missing.
  - `ship_question()` and `cmd_ship_question()` name the passes.
- `scripts/retro.py`: `_review_sources()` orders its sources `ship`, `fresh`, `SHIP_PASSES`, then
  `AGENT_ROLES`.
- `agents/security.md`, `agents/ui.md`, `agents/ux.md` (new): read-only core agents.
- `NOTICE` (new, repo root): the MIT notice for `agents/security.md`, which adapts
  `reviewer-security`'s text, so the notice is reachable from the core plugin.
- `skills/ship/security.md`, `skills/ship/behaviour.md`, `skills/ship/ui.md` (new): the branch
  files.
- `skills/ship/SKILL.md`: Step 0's list of branches, Step 3 naming the three files, and Step 7's
  report. No net line added.
- `templates/findings.md`, with `plugins/factory/scripts/factory.py`'s `FINDINGS_HEAD` kept equal
  to its title and note (`test_findings_head_is_the_template`).
- `guide/review.md`'s *Review dimensions*, then `sdlc.py record`, so `.sdlc/setup.json` matches.
- `docs/REFERENCE.md`: *Risky paths*, the `findings.md` paragraph and the trailer paragraph.
- `AGENTS.md`: the *Ship* paragraph (no longer one core agent) and the factory paragraph (what
  `sdlc` reads of the factory's files).
- `evals/ship-behaviour/` (new case) and `evals/fixtures/built-tier2/` (new fixture).
- Tests:
  - `tests/test_preflight.py`: passes, branch rows, the base-branch `[ui]` and stale shots.
  - `tests/test_findings.py`: `By:`, the trailer, note lines, evidence, ship's refusals and the
    question.
  - `tests/test_hand_gate.py`: the `[ui]` copies' pin.
  - `tests/test_skills.py`: the agents, the notice, each side file's `subagent_type` and the
    behaviour check.
  - `tests/test_retro.py`: source order.
  - `tests/test_evals.py`: the new stop case.

## Work order

1. **Security and behaviour passes.** `_passes_report()` with `security` and `behaviour`,
   `passes` in preflight, two `SHIP_BRANCHES` rows, and `security.md` and `behaviour.md`, so the
   branch-files test holds. Tests: R1–R3, R7, R19.
2. **The UI pass.** `_ui_at()`, the copies, `_current_shots()`, `passes.ui`, the `ui.md` row and
   file. Tests: R4–R6, the pin.
3. **Findings.** `SHIP_PASSES`, `FINDING_BY`, `ship_findings()`, the trailer keys, the note lines,
   evidence parsing. Tests: R9, R10, R13.
4. **Ship's refusal and question.** `cmd_ship()` and `ship_question()`. Tests: R11, R12, R14.
5. **The agents.** Three agent files and the root `NOTICE`. Tests: R8, R16.
6. **Prose and the rest.** `SKILL.md`, retro, the template and `FINDINGS_HEAD`, the guide and
   `record`, REFERENCE.md, AGENTS.md, then the eval case and fixture. Tests: R15, R17, R18,
   R20–R23.

## Tests

- R1/R2: `test_preflight_passes_security`, on a deep or shallow change and a factory run.
- R1/R3: `test_preflight_passes_behaviour`, on Tier 1, an unfilled spec, a filled spec and a
  factory run.
- R1/R4: `test_preflight_passes_ui`, on no `[ui]`, an incomplete one, a complete one, a touched or
  untouched path, and a factory run.
- R4: `test_ui_is_read_from_the_base_branch`.
- R5: `test_the_ui_copies_are_the_factorys` (`tests/test_hand_gate.py`).
- R6: `test_stale_shots_are_not_current`, plus a test for a set with a problem or a missing PNG.
- R7: new rows in `test_ship_branches_condition`. `test_ship_branches_are_the_files_beside_ship`
  is unchanged.
- R8: `test_ship_s_agents_read_and_nothing_more`, and `test_adapted_agents_keep_the_notice`
  extended.
- R9: `test_the_trailer_never_counts_an_agent_finding` extended.
  `test_finding_by_names_every_factory_reviewer` is updated for the new `FINDING_BY`.
- R10: `test_an_old_findings_file_keeps_its_trailer`.
- R11: `test_ship_refuses_a_{security_pass,behaviour_check,ui_review,ux_review}_unsaid`.
- R12: `test_a_skipped_ui_review_still_ships`.
- R13: `test_behaviour_evidence_is_read_not_counted`.
- R14: `test_the_question_names_the_passes`. The existing `ship_question` tests are unchanged.
- R15: `test_behaviour_check_never_runs_checks`. The existing rule-coverage tests are unchanged.
- R16: `test_ship_s_pass_files_spawn_their_agents`.
- R17: the budget test, unchanged at 475, and the reviewer test's phrase.
- R18: `test_review_sources_split_ship_from_the_agents` extended.
- R19: `test_preflight_names_the_branches_that_apply`, with `decision.md` on a deep, Tier 2,
  `[ui]`-touching change.
- R20: `test_every_review_dimension_names_both_ways`, and `drift` clean through the gate.
- R21: `tests/test_defaults.py`.
- R22: no test. Read by the review.
- R23: `tests/test_evals.py` (fixture check, stop case).
- R24: no test. Read by the review.

## Rollback

`git revert` of the change's commit undoes all of it. It writes no data outside the repo, and the
trailer's new keys are additive: a `Close` commit that already carries `passes=` keeps it, and
retro reads unknown keys as fields, so nothing downstream needs undoing.
