I fixed the one kept change from round 1, and the gate still passes (2,364 passed, 13 skipped). The work is still uncommitted.

- **KEPT C1** (`AGENTS.md:138`): the *Retrospectives* sentence now reads "runs the host's `retro.evidence`, `retro.indicators` and `retro.test_times` (`_evidence()`, the only place they run)". This is the only edit to `AGENTS.md`. The spec had left it for ship, so ship no longer needs to make it.

**What changed in `plan.md`:** its file list now includes `AGENTS.md`, with a note that round 1's review asked for the edit during the build.

**Not done:** nothing goes into `notes.md`, and the line needs no test because it is prose.

No decisions raised.

## Evidence

$ git diff AGENTS.md | grep "^[-+]"
--- a/AGENTS.md
+++ b/AGENTS.md
-`retro.evidence` and `retro.indicators` (`_evidence()`, the only place they run), so `retro` is
+`retro.evidence`, `retro.indicators` and `retro.test_times` (`_evidence()`, the only place they
+run), so `retro` is

$ ./check.sh
All checks passed!
255 files already formatted
2364 passed, 13 skipped in 72.15s (0:01:12)
✔ Validation passed
✔ Validation passed
exit: 0

$ git log --oneline -1
6d8905f Close 114-one-review
