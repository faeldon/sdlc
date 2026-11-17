DECISION: ESCALATE

**Why.** The build looks complete. The code reviewer passed round 1 with no Critical or Required findings and found code and tests for all 16 requirements. The gate is green: 2018 tests passed and both validations passed. I'm escalating because the builder made three calls on its own (D1–D3) that you haven't confirmed, and one of them (D2) changes the order the spec's Design set out. The change also extends published interfaces: the `Sdlc-Landed` and `Sdlc-Totals` trailers, a new `[land] moves` config key, and the land skill's question, which now has four answers.

**Open items**
- notes.md, from the builder, about R8 as the spec wrote it: `land-fix --ask "<words>"` passes your free text as a shell argument, so a quote or `$(` in it breaks the command or runs. Everywhere else your words reach an agent through `decisions.md`. Because this item is unticked, `land-check` will leave 104 out of a batch, so 104 itself ships by hand.
- From the code reviewer, Optional: in the land skill, `current` and `pass` still say "go to 4", and the step they now reach says "else go to 5". The flow is correct but easy to misread.
- From the code reviewer, Optional: the skill doesn't say whether the fix is asked for again after a `moved` return sends the change back to step 1.
- From the code reviewer, Optional: `land-fix --commit` doesn't check that the builder's reply, `build/land-<n>.md`, exists before it amends. A builder that crashed partway through its edits could be committed without a report.
- From the code reviewer, Optional: two lines in `plugins/factory/README.md` run well past the file's wrapping width.
- From the code reviewer, Nit: `.sdlc/work/inbox.md` is modified on this branch, with both seeds marked `[building]`. AGENTS.md says only `inbox-commit` commits the register, always on the base branch. It isn't in `build/round-1.files`, so check whether it would ride on this commit.

**Decisions to confirm**
- D1: the `_ready()` test fixture now leaves one reviewed, snapshotted build round, so R13's "no snapshot" signal stays as the spec wrote it. One 097 test now passes `reviewed=False`.
- D2: in `land --close`, 097's `by=auto` check runs before the move check, not after it as the spec's Design orders. The builder kept 097's code untouched and says the amend still carries the move (R2).
- D3: a commit with `unreviewed=unknown` says "No snapshot of its last review." in its body.

**For the person at ship**
1. `cmd_land_close()` in `plugins/factory/scripts/factory.py`. Check the order (D2): the auto check, then `_behind()` and `_record_move()`, then the single `_amend_record()`, then close, then the recount after a refused close. Confirm that no path amends twice and that the bound is read from the base branch.
2. `_amend_record(..., also=)` and `cmd_land_fix --commit`. With the default `also=()`, 097's behaviour should be unchanged. With `also` set, the amend takes in paths outside the change folder.
3. The `## Step 2 — WAIT` question in the land skill and the new steps for `moved` and the fix.
4. `land_message()` and `metrics.landed_unreviewed()`. `by=` must stay the first word of `Sdlc-Landed`, and file paths must stay in the commit body, never in a trailer.
5. Whether `.sdlc/work/inbox.md` would go into the commit.

- IMPACT: minor — factory users can newly set `[land] moves`, answer `yes, with a fix` at landing, and have a landing follow a moved base branch on its own. `Sdlc-Landed` and `Sdlc-Totals` gain an optional `unreviewed=` field, and nothing existing is redefined.
