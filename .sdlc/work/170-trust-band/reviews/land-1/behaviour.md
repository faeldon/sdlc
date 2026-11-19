VERDICT: PASS

## Notes
- No `checks.md` exists for this change, so there are no acceptance checks to read.
- **End-to-end path.** I started `sdlc.py retro` on this repo and it hadn't finished after 120 s. The harness moved it to the background and I didn't wait for it, so I haven't seen its report. The closest path I did run is the retro tests that cover the change: coverage and `missing_because`, the *What changed underneath* line, the host view, the factory window, and the merged value band. All 10 selected tests pass.
- **Landing resolution.** Both 168's value-band lines and 170's coverage lines are kept. `render_report(template, process, spend, value, metrics)` is consistent with the way `retro_report` calls it, and the full `tests/test_retro.py` run in `land-1.md` reports 178 passed.
- **Gate.** `build/land-1.gate.md` reports `GATE: PASS`, from `./check.sh` with exit 0 on this build. I did not run the gate again.
- **Not checked.** The landing note says it didn't check how 169's report lines would sit beside these tests. 169 isn't part of this diff, so that isn't a finding here.

## Evidence
$ ls .sdlc/work/170-trust-band/ .sdlc/work/170-trust-band/build
(listing: `build/land-1.gate.md`, `build/land-1.md`, `build/round-1.gate.md`, `decision.md`, `spec.md` and others; no `checks.md`)
exit: 0

$ head -12 .sdlc/work/170-trust-band/build/land-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: d447770e2710f206
Exit: 0
Seconds: 309.4
Tree: unchanged
exit: 0

$ git diff --stat 9c35272b9024efc337d8878ff6cf60cebc526983...HEAD | tail -15
 40 files changed, 1847 insertions(+), 38 deletions(-)
(touches `scripts/retro.py`, `scripts/metrics.py`, `scripts/closing.py`, `docs/REFERENCE.md`, `tests/test_retro.py` and others)
exit: 0

$ ls .sdlc/work/170-trust-band/checks.md
ls: .sdlc/work/170-trust-band/checks.md: No such file or directory
exit: 1

$ uv run --quiet --script scripts/sdlc.py retro
(no output read: the command passed 120 s and was moved to the background; I did not wait for it)
exit: not observed

$ uv run --group dev pytest -q tests/test_retro.py -k "trust or coverage or underneath or value or factory_window or host"
..........                                                               [100%]
10 passed, 168 deselected in 94.78s (0:01:34)
exit: 0
