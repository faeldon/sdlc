VERDICT: PASS

## Notes
- The diff covers each spec outcome.
  - `agent --task mend` records `runs/step.md` as a `mend` step with its role, and a failed session puts the old record back (`_record_mend()`, `_unrecord_mend()`).
  - `needs_of()` skips a `mend` stop while `mend_running()` holds, and says "mending … with no reply" once the mend is past its deadline.
  - A mend that is used up has `way: rerun`, so it reaches Needs you at once.
  - The board shows a `mending <role>` step.
  - `status` shows "mending" and a "wait for it" line.
  - `factory_records.py` carries the matching `ROLE_RE` and `mending()`, which `tests/test_modules.py` pins.
- Only files and their times decide. The timeout is the agent's own (`AGENT_TIMEOUT`), which settles the first open question.
- `mending()` never raises. Stamps in one fixed UTC form are compared as text.
- I did not run any tests. The gate record `build/land-1.gate.md` shows PASS, and I did not read it past its first lines.
- NIT: `scripts/sdlc.py` (`needs_of`): a `mend` stop with no step record at all still shows the plain "rerun to ask an agent again" text. That matches the "nobody is mending it" case, but it doesn't say "mending since". {docs S low}
