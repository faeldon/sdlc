VERDICT: PASS

The two `docs/REFERENCE.md` additions match what the code does.

- The `mending` status text and the `→ the factory is mending the <role>: wait for it` line match `scripts/sdlc.py` at line 11003. A mend in progress is skipped for Needs you, as the first branch at lines 5206–5207 shows.
- The timed-out mend's Needs-you text matches `scripts/sdlc.py` at lines 5211–5212, word for word.
- I did not check the "3-hour timeout" figure. `factory_records.py` line 272 says the deadline is the agent's own timeout past `since`, but I did not look for where the 3-hour value is set.
- I did not run any tests. I relied on the builder's run of the nine test files that read `docs/REFERENCE.md`: 1139 passed.

## Notes
- NIT: docs/REFERENCE.md:678: the Needs-you list sentence now runs far past the wrap width, with `parked past its deadline…` following on the same line as the new text. Rewrapping would read better. {style S low}
- Done well: both doc additions quote the printed strings exactly, and the `stopped` and `mending` cases are kept distinct.
