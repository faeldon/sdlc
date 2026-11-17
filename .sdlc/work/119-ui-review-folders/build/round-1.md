The ui and ux reviewers of one round can now start together and both run. Each one gets its own screenshots folder, `.sdlc/reports/shots/<change>/<label>/<role>/`, with its own fixture copy, server log and server. The gate passes (2246 passed, 13 skipped), and the work is left uncommitted on the branch.

## Slices built

There was one slice: give each role its own folder (Tier 1, but I wrote a short `plan.md` because the change touches three files).

- **`plugins/factory/scripts/factory.py`:**
  - `shots()` now takes `role` and builds its folder with the role at the end. `_fixture_copy()` and `_serve()` needed no change, because they already work inside whatever folder they're given.
  - `cmd_agent()` passes the role it runs, for both `round-<n>` and `land-<n>`.
  - `cmd_shots()` and `factory.py shots` now require `--role` (`ui` or `ux`), because a round's shots no longer exist without a role. Nothing in the skills calls this command.
- **`plugins/factory/README.md`:** the two places that name the shots folder now include `<role>/`, and it says each reviewer has its own folder, fixture copy and server.
- I left the reviewer prompts, `serve.sh` and `build.sh` alone. `cmd_agent()` passes each reviewer the full paths of its screenshots, and the host's `[ui] serve` is unchanged: it just gets a different `{fixture}`.

## Tests

- **New: `test_the_ui_and_ux_reviews_of_a_round_run_at_once`.** It starts `cmd_agent` for ui and ux in two threads, holds both until each has copied its fixture, and uses a serve stub that refuses a fixture already holding `drafts/`, as `build.sh` does. Both must exit 0, write their review, build their own `round-1/<role>/fixture/drafts`, and be given only their own screenshots.
  - I ran it before the fix and it failed for the same reason as on 110: `FileExistsError: … round-1/fixture/drafts`, and the ui review refused with "doesn't run blind".
- **Extended: `test_a_ui_review_never_runs_blind`.** It now also checks that ux's screenshots come from `round-1/ux/`.
- **Updated:** every existing `factory.shots(...)` call now passes a role, and the expected paths include `"ui"`.

## Gate

`./check.sh` exited 0: 2246 passed, 13 skipped; ruff lint and format clean; plugin validation passed.

## plan.md and notes.md

The build followed `plan.md` as written. There is nothing in `notes.md`.

## Decisions

None raised. The intent's open question, whether the two roles should share one set of screenshots, was settled by its Approach (separate folders), so I built that.

## Evidence

```
$ uv run --group dev pytest -q tests/test_factory.py::test_the_ui_and_ux_reviews_of_a_round_run_at_once   # before the fix
E       "the screenshots failed, so the ui review doesn't run blind: the dev server exited 1 before answering on 54631"
FileExistsError: [Errno 17] File exists: '.sdlc/reports/shots/008-reopen-drafts/round-1/fixture/drafts'
1 failed in 6.23s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py::test_the_ui_and_ux_reviews_of_a_round_run_at_once   # after the fix
1 passed in 0.83s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py -k "shot or ui or ux or fixture or port"
71 passed in 7.06s
exit: 0

$ ./check.sh
246 files already formatted
2246 passed, 13 skipped in 145.76s (0:02:25)
✔ Validation passed
✔ Validation passed
exit: 0
```
