# 119 — Plan

> How the change is built, written after reading the code: the files it touches, the order of its
> slices, the test each requirement gets, and what a revert wouldn't undo.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `shots(root, folder, label, ui)` gains `role`: its folder becomes
    `.sdlc/reports/shots/<change>/<label>/<role>/`, so the role's PNGs, `shots.json`,
    `serve.log` and `fixture/` copy are its own. `_fixture_copy()` and `_serve()` are reused
    unchanged: they already work inside whatever `where` they are handed.
  - `cmd_agent()` passes the role it runs (`ui` or `ux`) for both `round-<n>` and `land-<n>`.
  - `cmd_shots()` and its parser take `--role` (`ui` or `ux`, `UI_REVIEWERS`), required, since a
    round's shots no longer exist apart from a role.
- `tests/test_factory.py`: the new test, and every existing `factory.shots(...)` call given a role
  and its expected folder.
- `plugins/factory/README.md`: the two places that name the shots folder.

The reviewer prompts (`agents/reviewer-ui.md`, `reviewer-ux.md`) name no folder: each is handed
its screenshots' paths in the prompt by `cmd_agent()`, so they need no edit. Nor does `serve.sh`
or `build.sh`: the host's `serve` is unchanged, it is handed a different `{fixture}`.

## Work order

1. **Each role its own folder** (one slice: the function, its one caller, the CLI, the docs).
   Red: the test below, run before any code change. Green: the `role` parameter and its callers.
   Then the existing tests' paths, the README, and the gate.

## Tests

- `test_the_ui_and_ux_reviews_of_a_round_run_at_once` (Outcome 1 and 2): starts `cmd_agent` for
  `ui` and `ux` in two threads, held at a barrier until both have copied their fixture, with a
  `serve` stub that refuses a fixture already holding `drafts/` (as `build.sh` does). Both must
  exit 0 and write their review, each handed only screenshots under its own `round-1/<role>/`.
  While the folder is shared, the second serve finds the first's `drafts/` and that review is
  refused.
- `test_a_ui_review_never_runs_blind` gains the assertion that ux's screenshots are under
  `round-1/ux/`.

## Rollback

Nothing outside the tree: shots go under `.sdlc/reports/`, which ignores itself. A `git revert`
undoes all of it; any `round-<n>/<role>/` folders left in a host's reports are ignored files.
