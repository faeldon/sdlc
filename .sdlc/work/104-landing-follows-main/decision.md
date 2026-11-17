DECISION: ESCALATE

**Why.** The build is complete and converged. Both review rounds passed with no Critical or Required findings. All 16 requirements have code and tests, and the round-2 gate is green (2020 passed, both validations passed). You confirmed D1–D3, and round 2 did what your R2 asked. I'm escalating for two narrow reasons, so this should be a short look. First, the builder rewrote `spec.md`'s R8 and the Design's `--ask` bullet itself, and the reviewer then checked the build against that edited spec. Second, the change extends published interfaces: the `Sdlc-Landed` and `Sdlc-Totals` trailers, a new `[land] moves` key, and the land skill's WAIT, which now has four answers and covers more.

**Open items**
None of these was marked as a required change; all are Optional or Nit from the code reviewer:
- Optional (rounds 1 and 2): `cmd_land_fix --commit` amends without checking that `build/land-<n>.md` exists, so a builder that crashed partway could be committed with no report.
- Optional (rounds 1 and 2): the land skill's fix step says "once" but never says whether the fix is asked for again after `moved` sends the change back to step 1.
- Optional (round 2): `FIX_WORDS_RE` reads the fix words from one line only, so a multi-line fix is cut at its first line. The skill should say "on one line".
- Optional (round 1): in `SKILL.md`, `current` and `pass` still say "go to 4" where step 4 starts "else go to 5". The flow is right, but it is easy to misread.
- Optional (round 2): two lines in `SKILL.md` run past the wrapping width. The README's long lines were reflowed in round 2.
- Nit (round 2): `read_fix_words` takes the first match when an id appears twice. This is harmless, because the skill picks one past the highest `R`.

**Decisions to confirm**
None. R1, R2 and D1–D3 are all ticked and decided.

**For the person at ship**
1. The `spec.md` diff for R8 and the Design's `--ask` bullet. Check that the builder's wording says what you meant in R2 and nothing more.
2. `cmd_land_close()` in `plugins/factory/scripts/factory.py`. The steps should run in this order: the `by=auto` check (D2), then `_behind()` and `_record_move()`, then exactly one `_amend_record()`, then close, then the recount after a refused close. `moves` must be read from the base branch.
3. `_amend_record(..., also=)` and `cmd_land_fix`. With the default `also=()`, 097's behaviour should be unchanged. `--ask` should accept only the id of a ticked `(person, fix)` line.
4. `land_message()` and `metrics.landed_unreviewed()`. `by=` must stay the first word of `Sdlc-Landed`, paths must go only in the commit body, and `unreviewed=` should appear on `Sdlc-Totals` only for a landed change.
5. The land skill's `## Step 2 — WAIT` question and its new steps for `moved` and the fix.

- IMPACT: minor — factory users can now set `[land] moves`, answer `yes, with a fix` at landing, and have a landing follow a moved base branch without a hand `base` and regate. `Sdlc-Landed` and `Sdlc-Totals` gain an optional `unreviewed=` field, and nothing existing is redefined.

There are no `- UNDONE:` lines: `notes.md`'s only item is ticked, since round 2 resolved it. There are no `- RECOVER:` lines either, because the prompt names no irreversible paths.
