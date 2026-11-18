VERDICT: CHANGES

- CHANGE: tests/test_factory.py: the landing rebase added one behaviour, and no test covers it. `agent_findings()` weighs nits from build rounds only. "Raised again" and `reworked_round()` also read build rounds only. A nit raised only in a `reviews/land-<n>/` round is `minor` and never filed. The builder checked this by hand and wrote no test (`build/land-1.md`). Land rounds restart their numbers at 1, so the rule exists to stop a land-1 nit colliding with build round 1. Add a test that builds a change with build rounds 1–3 plus a `land-1` round. In that round, re-raise a handed cheap nit and add a new `{… low S}`-style nit, then assert that `findings.md` and the filed set are unchanged and the new nit is `minor`. Without it, deleting the build-only filter still passes the suite.

## Notes
- **Run:** `uv run --group dev pytest -q -n auto` gave 2374 passed, 13 skipped. That matches the builder's `./check.sh` count.
- **Well covered:**
  - The plan's R1–R13 each map to a named test. The suite diff adds about 374 lines across `test_factory.py`, `test_land.py` and `test_skills.py`.
  - The weighing, the cap of 5, the handed-on and not-raised-again cases, and the file-once rerun are all covered.
- **Check in `checks.md`:** the one section greps for the wording in `guide/review.md`, `guide/process.md` and `templates/inbox.md`. It fails if the change is reverted, it doesn't write to the tree, and it has no unquoted-quote problem. I didn't run it. I expect it to exit 0 against the current text.
- **Merge note:** the dropped stale `[2026-11-18-7]` heading in `inbox.md` is a reasonable resolution, since the base retired that seed. It is not a test matter.
