DECISION: READY

**Why.** Each change in a retrospective now gets one `git diff -U0` instead of two, and both `_rework()` and `_spend()` use it. The one round had a single reviewer (code), who returned `VERDICT: PASS` with no CHANGE items. The builder's evidence shows the new test failing first (two diffs per change), then 122 retro tests passing and `./check.sh` passing. On this repo's own 48-change window, `retro_report()` gave the same report before and after, with `-U0` calls dropping from 96 to 48. The folder has no `notes.md`, no `decisions.md` and no `plan.md` (Tier 1). Nothing in the change touches a secret, a destructive operation or a published interface.

**Open items**
- None. The reviewer's notes ask for no change. Two are worth knowing: the intent calls the helper `_change_diff()` but the code calls it `_diffs()`, and `_diffs()` now holds every change's diff in memory at once instead of one at a time.

**Decisions to confirm**
- None. There is no `decisions.md`.

**For the person at ship**
- Look at `_diffs()` in `scripts/retro.py` first, then its two callers (around line 747 in `retro_report()` and line 896 in `retro()`), then the `bases` → `diffs` parameter swap in `_spend()`.
- `_rework()` still skips a change with no base (around line 833), so the extra `diff-tree` diffs that `_diffs()` now reads for those changes go only to `_spend()`, which already read them. Behaviour is the same.
- The builder compared reports byte for byte only for `retro_report()`, not the full `retro()`, because `retro()` runs this repo's `retro.evidence`. The code only changes where rework and spend get their diffs, so I don't count that gap as a risk.
- Check the new test, `test_a_retrospective_reads_each_change_s_diff_once` in `tests/test_retro.py`. It pins one diff per change for both entry points.

- IMPACT: patch — a retrospective makes half the `-U0` git calls, and nothing in what it reports changes.

**Undone items:** none. There is no `notes.md`, so there are no unticked items.

**How to recover:** the prompt names no irreversible paths.
