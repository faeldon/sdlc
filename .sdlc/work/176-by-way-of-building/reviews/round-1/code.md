VERDICT: PASS

I read the diff against all 13 requirements and found nothing that needs rework. Per `build/round-1.gate.md`, the gate (`./check.sh`) passed. I ran no tests myself, and I did not run the verification command against this repo's own `retro` output.

## Notes

- **Requirements:** each of R1–R13 has code. Each named test exists, in `tests/test_retro.py` or `tests/test_next_up.py`. The R13 doc edits are in `docs/REFERENCE.md`, `docs/RETRO-SCORECARD.md` and `skills/retro/SKILL.md`.
- **Done well:**
  - `by_way()` is pure.
  - `retired_entries()` is the single reader of `Retire` subjects, and `_milestone_verdicts()` walks it only when a grouped seed has gone.
  - The report-before-process ordering fix (R4) is a one-line move.
  - `_landed` is popped by both callers, so it never reaches the JSON.
  - The way comes from `metrics.mode` alone.
- **Escapes:** `bugs_retro()` resolves each escape's introducer through the same `names_change` path for the row and the rate. The per-way escapes therefore sum to the window total, because each attributed bug lands in exactly one way.
- NIT: skills/retro/SKILL.md:~60: the edits left some lines well over the file's wrapping width (the `lead`/`throughput` line, the escapes `rate` line, the `dropped` line); rewrap them {style S low}
- NIT: scripts/retro.py:3222: `introducer_way()` rescans `history` for every attributed bug and every way. This is fine at today's sizes, but a name-to-way dict built once would be simpler {refactor S low}
