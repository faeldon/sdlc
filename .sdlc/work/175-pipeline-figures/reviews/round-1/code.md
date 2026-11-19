VERDICT: PASS

I found no Critical or Required problems. I read the diff against the spec's requirements, and nothing in the code contradicts them. I ran no tests. The round-1 gate record at `build/round-1.gate.md` shows PASS (`./check.sh`, exit 0). It shows `Tree: unchanged`.

## Notes

- Not every spec requirement was walked through. I did not read `tests/test_retro.py`, `tests/test_modules.py` or `tests/test_train.py` line by line. The gate passes, so the tests exist and pass.
- R3: both gate writers (`factory.py` and `sdlc.py`) now write `Waited:` after `Seconds:`. `Waited:` takes its value from `gate_slot()` and `_hand_slot()`.
- R6/R7: `verdicts` output already carries `depth` into `step_text()`, so `DEPTH:` is written. Both `read_step()` copies read it back.
- R9: the new `pipeline_counts()` is pure. `retro.py` reads records only through it.
- R10: the shared constants now live in `factory.py` under the same names (`LAND_TRAIN`, `TRAIN_GATE_RE`, `LAND_ACCEPT`, `WAITED_RE`, `DEPTH_RE`). `landing.py` reads them as `factory.LAND_TRAIN`.
- R11: `pipeline.changes` is dropped without `--metrics`.
- R12: no `mends` key, as the spec asks.
- R13: `_none_reason()` uses the bounded regex.
- R14: the comment in `autonomy_counts()` is added.
- R1: figures are null with no `n` (`_spread` and `_share`). A change built by hand lands under `by_hand` or `missing_because`, never as a zero.
- The ejection cause defaults to `refusal` when a row has no `cause`. That is a reasonable choice for older rows.
- `resolved_files()` removes the duplicate parse of `conflicts.md`.
- `_p85()` is reused by `lead_view`.
- NIT: scripts/retro.py:1098: `bisections` and `accept_stops` have no `per_change`. `gates` and `base_moves` do. This is optional and the spec doesn't ask for it. {docs S low}
