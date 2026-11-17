I fixed the one kept change: the docs paragraph now says close marks issues even when a tracker has no `intake()`. The full gate passes (2191 tests passed, 9 skipped).

**Kept change:**
- `docs/CONTRIBUTING.md:193`: I rewrote the paragraph above the intake list. It now names the commands `_intake_tracker()` refuses for a tracker without `intake()`: `intake` (`intake()`, `dangling()`), `closes` and ship's `preflight` (`titles()`), `needs-info` (`needs_info()`), and `mark-triaged` and `sync` (`mark()`, `open_marks()`, `open_numbers()`). It then says close is the exception: once a change has landed, its record step calls `mark()`, `open_marks()` and `open_numbers()` whenever the tracker has `mark()`, whether or not it has `intake()`. I also noted that `closed_by()` is used whenever the tracker has it. Close's behaviour is unchanged.

**`plan.md`:** the CONTRIBUTING line now describes the commands `intake()` gates and close's exception, with a mention of this review round.

**`notes.md`:** unchanged; it still holds the item about `unmark()` in `recorded_issues()`'s docstring.

I raised no new decisions this round. The earlier `[default]` on how to document `unmark()` still stands until the person confirms it.

## Evidence

$ uv run --quiet --script scripts/sdlc.py accept 116 | grep -E '"passed"'
      "passed": true,
      "passed": true,
  "passed": true,
exit: 0

$ ./check.sh
All checks passed!
2191 passed, 9 skipped in 90.19s (0:01:30)
✔ Validation passed
✔ Validation passed
exit: 0
