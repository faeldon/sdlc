DECISION: ESCALATE

**Why:** The build looks finished. Round 2 is all `VERDICT: PASS`, the one kept CHANGE from round 1 (code C1, "mend once" enforced by the script) is fixed and tested, and `./check.sh` passed at 1907 tests by the builder's evidence. But `decisions.md` still has three unticked defaults that you haven't confirmed. One of them, D3, knowingly goes against the intent's literal wording in Outcome 3 ("the aside commit … never skipped"), and no test covers that case.

**Open items**
- None open as CHANGE. What's left is optional or a nit from reviewer-code in round 2:
  - A `behaviour` reply missing both its verdict line and `## Evidence` gets only the verdict mend. The leftover evidence problem then stops as `rerun`. That's safe, but the skill doesn't say so (reviewer-code, optional).
  - No test covers the empty aside commit (reviewer-code, optional; linked to D3).
  - `plugins/factory/skills/build/SKILL.md`: the `way` sentence in the `stop` step breaks the line after a dangling "with" (reviewer-code, nit).
  - The changed paragraph in `AGENTS.md` wraps unevenly around the `runs/mended` and `checks.md` lines (reviewer-code, nit).
- There is no `notes.md`, so these aren't carried anywhere yet. File them as nits at ship if you keep them.

**Decisions to confirm**
- D1: only a reply whose verdict comes after a preamble can be mended. A reply with no `VERDICT:` line at all still stops as `rerun`.
- D2: only reviewers get the mend. A verifier's or approver's reply that doesn't open with its line still stops as before.
- D3: an empty aside commit (all the uncommitted work already on the base) is skipped by `git rebase --skip`, not committed and then undone. This departs from Outcome 3's "never skipped". The builder reads that outcome as being about an aside commit that holds work, and that case is tested. The skipped case is reasoned about but not tested.

**For the person at ship**
1. **`_go_on()` in `scripts/sdlc.py`** (inside `cmd_resolve()`). Check that it only runs `git rebase --skip` when nothing is unmerged and both the index and the worktree match `HEAD`. This is the one place the change can drop a commit. Then decide D3, ideally after asking for an empty-aside test.
2. **`mended()` / `mend_round()` and the mend branch of `cmd_agent()` in `plugins/factory/scripts/factory.py`.** `runs/mended` is now the one file a run writes that `verdicts` reads back, which is an exception the AGENTS.md text now states.
3. **`_as_written()` in `_inbox_commit()`**, which is small and well tested by both reviewers.

- IMPACT: patch — fixes two bugs (inbox-commit naming entries it didn't change, and `resolve --continue` stopping on a commit the merge emptied), and makes a reviewer's preamble a stop the run mends instead of a stop someone has to clear by hand; no interface anyone calls changes.
