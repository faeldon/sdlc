VERDICT: PASS

The move is behaviour-preserving. The two time readers (`timed_rows`, `land_sinces`) now live in `factory_records.py`, and `_lead_marks` reads the same two committed files through them.

- **Same paths:** `LAND_TIMES` and `COSTS` are `runs/land-times.jsonl` and `runs/costs.jsonl`. `_lead_marks` builds `{branch}:{folder}/runs/…`, which matches the old `{runs}/…` reads.
- **Same logic:** the parser bodies moved unchanged, along with the three helpers only they used (`RUN_TIME_FORMAT`, `_run_time`, `_json_rows`).
- **`git show` stays in `closing.py`:** close is still the only place those git reads run.
- **R5:** the only `closing.py` lines that still name `costs.jsonl` are two docstring mentions, which the tests accept. The R5 test passes in `tests/test_modules.py`.
- **Tests:** `tests/test_archive.py` now calls the moved readers with the same inputs and expected values. `tests/test_modules.py` requires `timed_rows` and `land_sinces` in the module and lists the old private names as ones no other file may define.
- **Gate:** the record for this round, `build/land-2.gate.md`, reads `GATE: PASS`. I did not rerun the whole suite.

## Notes
- **Spec path:** the end-to-end path here is the lead-time measurement at close. I ran only the named tests that exercise it, in `tests/test_modules.py` and `tests/test_archive.py`.
- **`checks.md`:** the change has no `checks.md`, so there is nothing to read.
- **Not run:** I did not run a real `close`, since that writes.

## Evidence
$ head -8 .sdlc/work/163-factory-records-reader/build/land-2.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: bbc83e4d480ccc45
Exit: 0
exit: 0

$ grep -n "_lead_marks" -A45 scripts/closing.py
(`_lead_marks` reads `runs/land-times.jsonl` and `runs/costs.jsonl` via `records.LAND_TIMES` and `sdlc.factory_records.COSTS`, then parses with `land_sinces` and `timed_rows`)
exit: 0

$ grep -n "^LAND_TIMES\|^COSTS\|def timed_rows\|def land_sinces" scripts/factory_records.py
115:LAND_TIMES = Path("runs") / "land-times.jsonl"
116:COSTS = Path("runs") / "costs.jsonl"
663:def timed_rows(text: str) -> list[tuple[datetime, datetime, str]]:
675:def land_sinces(text: str) -> list[datetime]:
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_modules.py tests/test_archive.py 2>&1 | tail -3
177 passed in 25.97s
exit: 0
