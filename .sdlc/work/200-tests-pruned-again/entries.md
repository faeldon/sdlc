# 200-tests-pruned-again — entries

## [2026-11-20-50] [idea] The train's reading runs about 1,500 git calls for a driven train of three (723 `rev-parse`, 418 `show`), which is most of each train test's time and of a real landing's bookkeeping.

Left undone by 200-tests-pruned-again, carried forward when it landed: The train's reading runs about 1,500 git calls for a driven train of three (723 `rev-parse`, 418 `show`), which is most of each train test's time and of a real landing's bookkeeping. Caching what doesn't change within one reading would speed both.
See .sdlc/work/200-tests-pruned-again/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-51] [idea] No test fails when the train's readiness refusal (`_land_readiness()`'s `refusal`, in `cmd_train`) is ejected under another cause: mutating its `"refusal"` to `"review"` passed every train and landing test.

Left undone by 200-tests-pruned-again, carried forward when it landed: No test fails when the train's readiness refusal (`_land_readiness()`'s `refusal`, in `cmd_train`) is ejected under another cause: mutating its `"refusal"` to `"review"` passed every train and landing test. The removed `test_every_ejection_names_its_cause` never reached that path either: its stray file is the `failed` path, which `test_train_run_stops_at_a_refusal` covers.
See .sdlc/work/200-tests-pruned-again/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-52] [nit] `_names()` is the one place a string-to-path match is decided, and its docstring wraps mid-sentence and is hard to read.

Raised by the code review of 200-tests-pruned-again, round 1: scripts/indicators.py:478: `_names()` is the one place a string-to-path match is decided, and its docstring wraps mid-sentence and is hard to read. Splitting it into two sentences would help.

Theme: docs
Paths: scripts/indicators.py
Cost: S
Value: low
Raised by: 200-tests-pruned-again (correctness)

## [2026-11-20-53] [nit] the paragraph opens "one is left", then lists several tests under "Kept", and only `test_function_heat.py` still drifts.

Raised by the code review of 200-tests-pruned-again, round 1: .sdlc/work/200-tests-pruned-again/notes.md:8: the paragraph opens "one is left", then lists several tests under "Kept", and only `test_function_heat.py` still drifts. Rewording it to say that would match what follows.

Theme: docs
Paths: .sdlc/work/200-tests-pruned-again/notes.md
Cost: S
Value: low
Raised by: 200-tests-pruned-again (context)
