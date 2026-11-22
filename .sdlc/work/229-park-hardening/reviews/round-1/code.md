VERDICT: PASS

## Notes
- NIT: docs/REFERENCE.md:249: the line "holder is `unknown`, and an `UNTIL` that won't read is noted and ignored. The factory then parks the change: its gate records no" is now well past the wrap used in the rest of the paragraph. Rewrap it. {docs S low}
- NIT: scripts/sdlc.py:11036: `_park_deadline_at()` runs a `git show` for each build-stage change inside the status loop. Read it once before the loop, as `_gate_jobs_at()` is. {refactor S low}
- Well done:
  - Each of the five rough edges has a named test.
  - `capped_park` is copied into `factory_records.py` and pinned to the factory's original, so `needs_of()` stays the one rule.
  - The `park --clear` change is limited to records the ledger never vouched for.
  - The 0/1 refusal is made in `_park()`, where every other bad `[park]` value is handled.
- I read the gate record (`build/round-1.gate.md`: PASS) and the full diff. I ran no tests and did not read the new tests, so I did not check them.
