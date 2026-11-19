VERDICT: PASS

I ran `sdlc.py retro` from the worktree and the JSON now has a `pipeline` key that matches the spec. This change has no `checks.md`, so there were no acceptance checks to read.

## Notes
- **Gates (R2):** the round and landing gates each give `seconds` as `{n, median, p85}` for the window and for `previous`. `wait` shows `n: 0` with null median and p85, because history predates the `Waited:` line. That is missing, not zero, as the spec requires.
- **Red-gate rate (R4):** 1 red build out of 28, rate 0.04.
- **Landing (R5):**
  - Coverage is 24 of 25, with `built by hand: 1` as the missing reason.
  - Gates total 20 (0.83 per change), ejections 0, bisections 3, base moves 0, accept stops 16 across 8 changes, conflicts 11 at landing and 0 at ship.
- **Depth (R7):** `n: 0` and `share: null`, with `depth not recorded: 24` as the missing reason. That fits older runs that have no `DEPTH:` line.
- **Unreviewed (R8):** `n: 0` and every count 0, with `unreviewed not recorded: 24` as the missing reason. This is a null result, not a failure.
- **Tests:** the 18 `tests/test_retro.py` tests matching `pipeline`, `none_reason` or `autonomy` pass.
- **Gate record:** `build/round-1.gate.md` reads `GATE: PASS`. I did not rerun the gate or the whole suite.
- **Not run:** I did not run the `factory.py gate` and `sdlc.py gate` writers for the `Waited:` line (R3), or `cmd_retro()` without `--metrics` for R11. I relied on the green gate record, which includes those tests.

## Evidence
$ cat .sdlc/work/175-pipeline-figures/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c "...print(json.dumps(d['pipeline']))"
(the `pipeline` JSON summarised above: gates, red_gate, landing, depth and unreviewed, as printed)
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "pipeline or none_reason or autonomy"
18 passed, 180 deselected in 155.92s (0:02:35)
exit: 0
