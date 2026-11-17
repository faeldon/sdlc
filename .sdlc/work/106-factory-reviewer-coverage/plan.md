---
id: 106
slug: factory-reviewer-coverage
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 106 — Factory review reads the tests and sees the new cards · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `_depth_keys()` returns whether it took `reviewers`;
  `load_config()` records it as `light.chosen`; a new `light_reviewers(cfg, tier)`; `depth()`
  takes the tier and uses it for the light depth's reviewers and its "beyond" test;
  `_rounds_at_depth()` reads the tier from `intent.md` with the existing `frontmatter()`;
  `cmd_start()` reports `light.reviewers` for the change's tier. `_ui_table()` takes `fixture`
  (a relative path without `..`) and warns on a `serve` naming `{fixture}` with none set;
  `shots()` checks, removes and copies the fixture, and fills `{fixture}`.
- `tests/test_factory.py`: the R1–R11 tests; the light-depth tests that built a Tier 2 change
  to mean "today's light run" now build a Tier 1 (see the decision raised); the config tests
  expect `light.chosen`.
- `tests/fixtures/board/changes/` (new): one folder per card state, plus `gates`, naming the
  changes whose hand gate is run and whether it passes.
- `tests/fixtures/board/build.sh` (new): builds the scratch repo from a copy of `changes/`.
- `tests/fixtures/board/serve.sh` (new): builds it inside the copy, then serves this checkout's
  own `scripts/sdlc.py board` there.
- `tests/test_board.py`: `test_the_board_fixture_shows_every_card_state` (R13).
- `.sdlc/factory.toml`: `serve` and `fixture` for the board fixture; `paths` gains it (R12).
- `plugins/factory/README.md`: `fixture`, `{fixture}` and the Tier 2 light default (R14).
- `plugins/factory/skills/build/SKILL.md`: the light default's line says the Tier 2 default (R14).

**As built**, where the build departed from the spec's design:

- `build.sh <changes> <dir>` takes the data and the target apart, and refuses a `<dir>` that exists;
  `serve.sh` builds into `<fixture>/drafts`, inside the copy, so `shots()` replacing the copy
  clears the scratch repo too (and the board's header reads `drafts`).
- Which changes get a hand gate, and whether it passes, is data too: `changes/gates`, one
  `<change> pass|fail` line each. The scratch repo's check is `test ! -e RED`, and a failing
  change's branch carries a `RED` file.
- The step record carries no `SINCE:`, so the card shows its track without a time that would grow
  with every day the fixture ages.
- A fixture that is one file is copied into `fixture/`, by its name, and `{fixture}` names the file.
- `{fixture}` is filled only when `fixture` is set: unset, `serve` runs exactly as written.
- `light.chosen` is true only when `[light] reviewers` was set and taken; a list with no known
  reviewer falls back to the default, Tier 2's `test` included.
- The existing tests that built a Tier 2 to mean today's light run now build a Tier 1 (raised as
  a decision): `test_a_diff_touching_no_sensitive_path_runs_light` and
  `test_the_ui_reviewers_join_on_a_ui_path_at_either_depth`. The config tests expect `chosen`;
  `test_a_ui_review_never_runs_blind` writes no `null` for an unset key.

Reused, not re-derived: `frontmatter()` for the tier, `risk_paths()`, `_fill()`, `_reports()`,
`_sh()`, the existing `problem` path that makes `cmd_agent` refuse a blind UI review, and
`sdlc.py gate` itself to write the fixture's current hand-gate records.

## Work order

1. **Light reviewers by tier** (R1–R8): `light_reviewers()`, `light.chosen`, `depth()` and
   `_rounds_at_depth()` with the tier, `cmd_start`. Tests first; the existing light tests move
   to Tier 1. Gate.
2. **`[ui] fixture` in config** (R9, half of R11): `_ui_table()` accepts and checks it, warns on
   `{fixture}` without it. Test first. Gate.
3. **`shots()` serves a fresh copy** (R10, the rest of R11): check, remove, copy, fill. Tests
   first, with a fake server that writes into its copy. Gate.
4. **The board fixture** (R12, R13): `changes/`, `build.sh`, `serve.sh`, the board test, then
   `.sdlc/factory.toml`. Run `serve.sh` once by hand and read `/state.json`. Gate.
5. **Docs** (R14): README and the build skill. Gate.

## Tests

- R1, R2, R3, R7: `test_a_tier_2_light_round_includes_the_test_reviewer` (Tier 2, Tier 1 and
  an unreadable tier; `verdicts`' `missing` and `start`'s `light.reviewers`).
- R8: `test_the_landing_review_judges_a_tier_2_light_run_with_its_test_reviewer`.
- R4, R5: `test_a_set_light_list_is_kept_at_either_tier`.
- R6: `test_the_test_reviewer_never_deepens_a_tier_2_light_run`.
- R2 also: `test_a_diff_touching_no_sensitive_path_runs_light` and its neighbours, at Tier 1.
- R9: `test_ui_fixture_is_checked_like_the_other_keys`.
- R10: `test_shots_serve_a_fresh_copy_of_the_fixture`.
- R11: `test_a_missing_fixture_refuses_the_ui_review`.
- R12, R13: `test_the_board_fixture_shows_every_card_state` (needs `sh`, `git`, `uv`).
- R14: `test_the_build_verifies_before_rework_and_states_its_depths` stays green; the README
  is read by hand.

## Rollback

`git revert` undoes all of it. Nothing is written outside the repo: the fixture's copies and
scratch repos sit under `.sdlc/reports/shots/`, which ignores itself; `rm -rf .sdlc/reports/shots`
clears them. A factory run straddling the revert stops expecting `test` at the light depth, which
is today's behaviour.
