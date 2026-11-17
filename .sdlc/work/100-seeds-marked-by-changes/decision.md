DECISION: ESCALATE

**Why.** The build looks complete and clean. The only reviewer (code) gave `VERDICT: PASS` in round 1 and found code and a test that can fail for every requirement, R1 to R9. The gate passed with 2009 tests and a clean `drift`, and the run ended with no decisions raised and no open CHANGE. I'm escalating anyway because the change touches a published interface. `templates/inbox.md` sits under `[review] irreversible`. `guide/process.md` and `docs/REFERENCE.md` change what a host's `[building]` tag means. The JSON from `status`, `bugs`, `nits` and `preflight` gains a new `building` key. Two skills change behaviour (`intent` and `batch.md`). Those are the kinds of edits a person should see before they reach `main`, even when every review is green.

**Open items.**
- No unresolved CHANGE. Two minor items are carried in `notes.md`:
  - `/sdlc:idea --themes` still skips only tagged `[building]` seeds, not seeds an open change's `idea:` names. Raised by the builder; the reviewer didn't flag it.
  - Plain `status` hides `■ Next up` when every seed is being built, so the `N being built` line doesn't show then. Raised by the builder.
- The code reviewer's notes are optional only: one over-long line in intent's Step 0, and `next_up`'s map of claimed entries is keyed by title.

**Decisions to confirm.** None. There is no `decisions.md`, and the intent's two open questions are marked as settled by the person.

**For the person at ship.**
1. **`templates/inbox.md` and `guide/process.md`.** Confirm the new wording keeps `[building]` as a tag that is still read but no longer written, and that a host's existing register only goes stale, with nothing misread.
2. **`scripts/sdlc.py`.** Look at the new `_claimed_by()` and the `building` list in `next_up()`. The builder took the change's name from the open-change records `next_up` already receives, not from a second `_open_claims()` call. `plan.md` and the build report both explain this as the same data from a different source; check you're happy with it.
3. **`skills/intent/SKILL.md` and `batch.md`.** Step 5 should no longer edit the register at all. Step 0 now names `work.register`, which `READS_CONFIG` requires now that the removed lines were its only mention.
4. **`tests/test_resolve.py`.** Look at the R2 rebase test and its control branch, which carries the old tag edit and must conflict.
5. **`.sdlc/work/inbox.md` on this branch.** The builder says it reverted this change's own seed tag to `main`'s text, and the file is absent from `round-1.files`, which fits. Confirm the branch shows no register diff.

- IMPACT: minor — intent no longer tags seeds `[building]` in the register, and `status`, `status --all`, `bugs`, `nits` and `preflight` now show which open change is building each seed (a new `building` key and status line); older tags still read as before.
