VERDICT: PASS

I read the diff against R1–R15. The gate record at `build/round-1.gate.md` is green. I did not run any test myself.

## Notes
- NIT: scripts/retro.py:2425: `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`. A `None` rating relies on `_table` rendering it as `—`. A test pins this, but the `—` spelling is implicit. {tests S low}
- NIT: scripts/retro.py:2467: `_last_experience` does `int(rating)` on the table cell. A hand-edited report with a non-numeric cell would raise instead of reading back as no rating. Guard it, or catch `ValueError`. {robustness S low}
- Done well:
  - Each requirement has code and a named test, including the metrics case for the two-question dialog.
  - The experience draft is read before any write, so a malformed draft is refused cleanly (R7).
  - The draft stays outside the commit's paths and is removed only after the commit succeeds (R8).
  - `{{experience}}` is not a template read, so an older override still renders.
  - `AGENTS.md` and `docs/PROCESS.md` were updated to match the new behaviour.
- Tests and commands run: none. I read `build/round-1.gate.md` for the gate result.
