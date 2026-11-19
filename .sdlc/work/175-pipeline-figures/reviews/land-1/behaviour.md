VERDICT: PASS

The background run finished, and it settles the one check I had left open. `sdlc.py retro --metrics` prints `True` for `'changes' in pipeline`, so the key is there with the flag and absent without it, as R11 says. The earlier run printed only the keys `factory`, `by_hand`, `gates`, `red_gate`, `landing`, `depth` and `unreviewed`.

## Notes
- **End-to-end path:** `sdlc.py retro` on this repo prints the `pipeline` figures the spec names. The only figures with no data yet are `wait`, `depth` and `unreviewed`, and they show `n: 0` and null, with every change under `missing_because`, not zero. The spec's Verification section says they start that way.
- **Tests:** `tests/test_retro.py`, `tests/test_modules.py` and `tests/test_hand_gate.py` give 274 passed, in two runs (21.02s and 25.90s).
- **Gate record:** `build/round-1.gate.md` reads `GATE: PASS`. That is the gate's result, not mine.
- **checks.md:** the change folder has no `checks.md`, so there are no acceptance checks to read.

## Evidence
$ uv run --quiet --script scripts/sdlc.py retro --metrics | python3 -c "...print('changes' in d['pipeline'])"
True
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py tests/test_modules.py tests/test_hand_gate.py -n auto
274 passed in 25.90s
exit: 0

$ tail -8 /private/tmp/claude-501/-Users-<term>-<term>-sdlc--claude-worktrees-175-pipeline-figures/3870909f-f322-49fb-9663-b0a999c7d361/tasks/b2x517h0j.output
(the `True` and the 274-passed lines above, then `[exited with code 0]`)
exit: 0

The earlier `sdlc.py retro` run, the first test run (21.02s, 274 passed) and the `head` of `round-1.gate.md` are in my previous reply's Evidence section.
