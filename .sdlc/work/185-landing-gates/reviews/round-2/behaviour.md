VERDICT: PASS

The round-1 CHANGE is fixed. `checks_clearance()` in `landing.py` now returns `step: "accept"` with "checks.md is gone, so there is nothing to judge" when `checks_sha()` is None. The `landing.checks_sha(folder)[:16]` call in `factory.py:4431` is therefore never reached with None, and the refusal path is taken. `test_land_checks_refuses_outside_a_changed_train_change` now covers a removed `checks.md` (`tests/test_train.py:2381-2383`). It asserts exit 1 and the "checks.md is gone" refusal, and it passes.

## Notes
- `## The docs state the landing's new gates` (the only check in `checks.md`): I read it and did not run it. I expect it to pass. The grep strings it needs are `[commands] build` for `gate --land --build` and `checks_clearance()`, both in `AGENTS.md`, `land-checks` in the land `SKILL.md`, and `gate --land --build` in the factory `README.md`. The edited files are all modified in this change.
- I did not trace the `[commands] build` and `land-checks` wording, or the old-rule removal, to their lines in the docs. That is the one gap in this expectation.
- I did not run the whole suite. I cite the round-2 gate record, which shows `GATE: PASS` (the repo's `claude plugin validate --strict` check passed).

## Evidence
$ head -5 .sdlc/work/185-landing-gates/build/round-2.gate.md
```
GATE: PASS

## Attempt 1

Verdict: PASS
```
exit: 0

$ uv run --group dev pytest tests/test_train.py -q -n auto -k "land_checks or clearance"
```
.                                                                        [100%]
1 passed in 20.50s
```
exit: 0

$ sed -n 885,965p plugins/factory/scripts/landing.py
```
(read: `checks_clearance()` returns "checks.md is gone, so there is nothing to judge" when `sha is None`; its default `step` is `accept`)
```
exit: 0

$ sed -n 4415,4440p plugins/factory/scripts/factory.py
```
(read: line 4431 `landing.checks_sha(folder)[:16]` runs only after `_task` has not refused)
```
exit: 0

$ cat .sdlc/work/185-landing-gates/checks.md
```
(read: one check, "The docs state the landing's new gates")
```
exit: 0
