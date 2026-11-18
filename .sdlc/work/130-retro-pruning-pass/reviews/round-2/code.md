VERDICT: PASS

The kept change is done. `AGENTS.md:138` now reads "runs the host's `retro.evidence`, `retro.indicators` and `retro.test_times` (`_evidence()`, the only place they run)", which is true.

## Notes
- This round I only checked the reworked path, `AGENTS.md`. I did not review the rest of the diff again, since round 1 already passed it.
- Done well: the one-line edit matches the code and leaves the rest of the paragraph alone.
- Ran `grep` on `AGENTS.md` and `git diff --stat`. I did not run the test gate.
