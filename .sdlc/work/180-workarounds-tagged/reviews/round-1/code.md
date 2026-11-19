VERDICT: PASS

The change meets all 13 requirements and has a test for each. The gate record `build/round-1.gate.md` is green (`GATE: PASS`, exit 0). I ran no tests myself; I read the diff, the tests and the docs.

## Notes

- NIT: tests/test_train.py: R5's test covers the eject path only. The same `problems.append(f"{name}: {problem}")` branch in `_train_stop` has no failing-append test. {tests S low}
- NIT: scripts/retro.py `_workarounds`: when `trunk` is empty, `_log_blocks` still runs with `"..None"`-style arguments, and the result is then thrown away by `commits if trunk else []`. Guard it before the call. {robustness S low}
- NIT: scripts/retro.py `_workarounds`: `_closing_subject` is defined after its first use. That works, but it reads out of order. {style S low}

Done well:
- **Detection:** `_workarounds` reads history only. `unknown` is kept apart from `outside`.
- **Ejection record:** `_record_ejection` never blocks the eject. It returns a problem that both callers pass on. The new `train` key goes last, so 174's key order stays as it was.
- **Copies:** `LAND_ASK_RE` is pinned to `land_ask_path()`. `SETUP_SUBJECTS` is pinned to the skills' own text.
- **Docs:** I grepped for the names the diff touches (`ejections.jsonl`, the `land` skill, the `retro` skill's field list, `REFERENCE.md`, `RETRO-SCORECARD.md`) and found no stale statement.

Tests run: none by me. I relied on the gate record, which includes the new tests.
