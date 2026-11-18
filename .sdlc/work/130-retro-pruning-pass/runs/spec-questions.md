
**Open questions resolved**

- *Where per-test times come from:* from host commands in a new `[retro] test_times` key. Each prints JUnit XML, which most runners can write, so the plugin learns nothing about the runner. Not pytest's `--durations`, which is runner-specific, and not a file path, which a worktree's gate never leaves in the main checkout. I checked against `_evidence()` and `COMMAND_LISTS` in the code.
- *Is a test-to-code map needed, or are blame and age enough?* Neither. Age alone is noise. The history retro already reads (`_architecture()`'s lookback rows, `co_change()`'s shape) shows a test whose code moved while it didn't. Duplicates and tests that pass for the wrong reason really would need coverage or mutation data, so they're listed as `unmeasured`.
- *A retro proposal, or a seed retro files?* Both, in the retro's existing flow: a finding in the process pass whose disposition is one seed listing every candidate and why. That approved seed, committed in the `Retrospective` commit, is where the evidence is recorded. Pruning itself is a later change through `/sdlc:intent` and ship's review.

**Left for you**

- **Should this repo set its own `retro.test_times`?** Doing that means producing a JUnit report. One way is for `check.sh` to add `--junitxml` (`check.sh` is under `review.sensitive`) and keep the file somewhere the main checkout can read. Another is a command that runs the suite at retro time, which takes about 60 s and fits the 600 s limit. Leaving it unset means this repo's first pruning pass rests on drift alone. The spec leaves it unset.
- **Should the committed report also carry the evidence?** The spec records it only in the approved seed. A `## Tests` section in `templates/retro.md` would make the report self-contained. The cost: it touches the irreversible `templates/`, needs `record`, and means either a host command inside `retro-commit` or a section built from history alone (drift without run times).
- **The thresholds:** `SLOW_OVER` 10× the median and at least 1 s, `DRIFT_LEAST` 3 later changes, `TIMES_TIMEOUT` 600 s. Lower values name more candidates and more noise. Higher values may never trigger on a small suite.
