---
id: 235
slug: tests-robustness-nits
kind: plan
created: 2026-11-23
updated: 2026-11-23
---

# 235 — tests robustness nits · plan

> Written by the builder after reading the code each requirement names; read by the review.

## Files to change

- `plugins/factory/scripts/run_state.py`: `uncarried()` gains the SETTLED-but-unconfirmed branch (R1).
- `scripts/closing.py`: `fix_trailers()` and `origin_trailer()` catch `(OSError, ValueError)` (R2).
- `scripts/sdlc.py`: `cmd_intake()`'s `from_host` reads the body's opening only (R4);
  `cli_preflight()` refuses the clause flags with `--preview` (R6). The `given` list moves up and
  is reused by both refusals.
- `scripts/retro.py`: `_read_hosts()` skips a listed path a `!` line also excludes (R15). Not in
  the spec's design: R15's test showed the code still read such a host, against 208 R3 ("never
  read"), so the test could only pass with this fix. Raised as a default.
- `plugins/factory/skills/autopilot/SKILL.md`: Step 1 and Step 3 say to single-quote the goal (R7).
- `.sdlc/work/235-tests-robustness-nits/entries.md` (new): one `Retire <id>: <reason>` line per nit.
- Tests: `tests/test_factory_decisions.py` (R1, R9), `tests/test_archive.py` (R2, R4),
  `tests/test_preflight.py` (R6), `tests/test_skills.py` (R7, R12, R18, R20),
  `tests/test_train.py` (R8, R19), `tests/test_suite_shape.py` (R10),
  `tests/test_records_ledger.py` (R11), `tests/test_update.py` (R13),
  `tests/test_retro_hosts.py` (R14–R16), `tests/test_setup_lifecycle.py` (R17),
  `tests/test_hand_gate.py` (R21, R23), `tests/test_factory_ui.py` (R22),
  `tests/test_base_ci.py` (R24, R25), `tests/test_autopilot.py` (R26, R28, R29),
  `tests/test_factory_loop.py` (R27).

Reused, not re-derived: `factory.approver_weighing()` (R1), `_carried()`/`_closing()` in the
decisions tests, `_listed()`/`_own()` in the retro-hosts tests, `_restart()` in the loop tests,
`test_windows.py`'s `_function()` shape for R21's body comparison.

## Work order

Each slice is one requirement: its test first, seen to fail where the requirement fixes code,
then the fix, then the file's tests by name.

1. Code fixes, each with its test: R1, R2, R4, R6, R7.
2. Test-only nits whose test must first fail against a deliberately weakened check: R10 (the
   `kwonlyargs` read), R12, R18, R20 (the whole-word matcher).
3. Test-only nits that pin existing behaviour: R8, R9, R11, R13–R17, R19, R21–R29.
4. `entries.md` with all 31 ids, R3 and R5 with their reasons.

## Tests

- R1: `test_ready_with_an_uncarried_default_is_mended[settled]`.
- R2: `test_archive.py::test_trailer_builders_swallow_only_git_and_read_failures`.
- R4: `test_intake_flags_an_issue_from_a_host` (third issue).
- R6: `test_preflight.py::test_preview_refuses_the_question_s_flags_rather_than_ignoring_them`;
  `test_preflight_preview_lists_findings_paths_and_stamp` drops the clause flags it passed, which
  210 R7 let `--preview` ignore and R6 now refuses.
- R7: `test_skills.py::test_autopilot_single_quotes_the_goal`.
- R8: the `mv` case of `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused`.
- R9: the `closes` case of `test_ready_with_an_uncarried_default_is_mended`.
- R10: `test_the_check_finds_a_fixture_never_used` (`test_three`).
- R11: `test_two_writers_at_once_leave_whole_lines`.
- R12: `test_idea_and_bug_offer_an_origin_line`.
- R13: `test_update.py::test_the_fake_claude_opens_its_files_as_utf8`.
- R14–R16: `test_two_fixture_hosts_give_known_counts`, `test_an_excluded_host_is_never_read`,
  `test_host_figures_never_move_this_repos_figures`.
- R17: `test_a_doc_drift_cannot_read_keeps_the_nudge`.
- R18: `test_skills.py::test_triage_files_a_host_issue_with_origin_host`.
- R19: a `READ_ONLY_REFUSALS` case.
- R20: `test_every_wait_names_its_preview` plus a portable matcher test.
- R21, R23: new tests in `test_hand_gate.py`.
- R22: new portable test in `test_factory_ui.py`.
- R24, R25: new tests in `test_base_ci.py`.
- R26, R28, R29: `test_autopilot.py`.
- R27: `test_a_nit_no_later_round_raises_is_fixed_whatever_its_weights`.
- R30: the gate (`factory.py check 235`).

## Rollback

`git revert` undoes all of it. Nothing outside the repo is written. The register entries retired
at close come back only by re-filing them, from the `Close` commit's parent's `inbox.md`.
