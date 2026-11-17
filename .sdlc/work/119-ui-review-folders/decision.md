DECISION: READY

**Why.** The one reviewer, code, passed round 1. Both outcomes are built: each role now gets its own shots folder, fixture copy and server under `round-<n>/<role>/`. They are pinned by a new test that runs the ui and ux reviews at once against a serve stub that refuses an existing `drafts/`. The builder shows the test failing before the fix with the same error seen on 110. The gate passes (`./check.sh`, 2246 passed, tree unchanged). Nothing touches a secret or a destructive operation, and the build follows `plan.md` as written.

**Open items**
- None. The code reviewer left two notes, not changes:
  - Confirm the new threaded test isn't flaky when run repeatedly under `-n auto`. A lost port would call the fixture copy again and could break the barrier.
  - `factory.py shots` now requires `--role`. No skill, agent or doc calls it, but an outside script calling `shots --round N` would need the flag.

**Decisions to confirm**
- None. The change has no `decisions.md`. The intent's one open question (should both roles share one set of screenshots?) is still unstruck, but the intent's own Approach answers it (separate folders), and the build followed that.

**For the person at ship**
- `shots()` and its call in `cmd_agent()` in `plugins/factory/scripts/factory.py`: check that the role reaches both the `round-<n>` and `land-<n>` labels.
- The `shots` parser's `--role ... required=True`.
- Then `test_the_ui_and_ux_reviews_of_a_round_run_at_once` in `tests/test_factory.py`: check the barrier's placement and its 20-second timeout, given the flakiness note.
- Consider running that test a few times in a row before landing.

- IMPACT: patch — the factory's ui and ux reviewers of a round can now run together as the build skill already says they should. The only visible change is that the internal `factory.py shots` command needs `--role`, and nothing in the plugins calls it.

**Undone items**
- None. The change has no `notes.md`, so there are no unticked items.

**How to recover**
- Not needed: the prompt names no irreversible paths, and every shot goes under `.sdlc/reports/`, which git ignores. A `git revert` undoes all of it.
