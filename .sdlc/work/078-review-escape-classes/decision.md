DECISION: ESCALATE

**Why.** The text change is small and the full gate passed: `./check.sh` ran 1848 tests and the gate ran on round 1. Both bullets are in place, and the verifier rightly dropped the one CHANGE the reviewer raised. But D1 is still unticked. That means the first bullet's main claim, that the review requires a test built from a real transcript, rests on an assumption you haven't confirmed. The reviewer also found that the two tests the bullet cites don't follow that rule themselves.

**Open items**
- None of the reviewer's CHANGEs is still open. The one it raised (credit the tests on line 50 to different changes) was dropped by the verifier. The `Sdlc-Fixes` trailers on `Close 050` and `Close 052` show the bullet credits the escapes correctly as written.
- These are notes from the code reviewer, not CHANGEs, and nothing addresses them:
  - **Rule vs. its own tests.** The first bullet requires "a test built from a real transcript's entries". The two tests it names are built from hand-written events, made up under a fake path according to the `tests/test_metrics.py` docstring. Either the rule should say "the shape of a real transcript's entries", or it should name a fixture that really was recorded.
  - **Second bullet claims more than its tests cover.** It names "git's quoted path against its `-z` output". `test_a_non_ascii_hotspot_on_the_base_branch_is_not_gone` covers only the quoted numstat path against `ls-tree`.
  - **One test only bites on Windows.** `test_paths_shown_are_posix` passes trivially on darwin and only catches anything in CI's Windows job.

**Decisions to confirm**
- **D1:** is the first bullet's "carries a test built from a real transcript's entries" a rule the review enforces, or only a question it asks? The build assumed it is a rule, as the seed words it.

**For the person at ship**
- Read `.sdlc/REVIEW.md`, lines 42–53; the diff is that and nothing else.
- Settle D1 first. If you keep the rule, decide whether "real transcript" should become "the shape of a real transcript" so the cited tests don't break it on day one. As written, the next review would hold every change to a standard no test in `tests/test_metrics.py` meets yet. A recorded-transcript fixture could become a seed of its own.
- Then decide whether the second bullet should drop the `-z` clause, or say that nothing pins it yet.

- IMPACT: none — only this repo's own review answers (`.sdlc/REVIEW.md`) change; no host reads them, and nothing in `defaults/`, `guide/`, `scripts/` or the skills changes.
