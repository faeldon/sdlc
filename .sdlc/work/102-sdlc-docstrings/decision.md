DECISION: ESCALATE

**Why:** The work looks done and clean. Round 1's code review is `VERDICT: PASS` with nothing Critical or Required, the gate is green (1998 tests), and all three acceptance checks failed before the edit and pass after it. I'm escalating only because D1 in `decisions.md` is still unticked. The build assumed an answer to the intent's open question (cut the subcommand list or keep it), and you haven't confirmed it. The question is also still unstruck in `intent.md`.

**Open items**
- Six `#` comments in `scripts/sdlc.py` still call the change folder `work/`, near lines 102, 134, 296, 621, 801 and 4904 (from the code reviewer; also in `notes.md` as left undone). They are comments, not docstrings, so they fall outside the stated outcome. The reviewer says fixing them here would be cheap. Line 3300's `→ work/` is the old heading format that `_seed_title()` parses, so it must stay.

**Decisions to confirm**
- D1: the build assumed **cut**, as the intent's Approach says. The module docstring now states the module's purpose and points at `sdlc.py -h`, not a subcommand list kept complete and pinned by a test. The cost is that some per-subcommand detail is gone from the module docstring, such as `close`'s measure step and its `Drop` split. That detail is still in each function's docstring. Once you answer, strike the question in `intent.md`.

**For the person at ship**
- Read the new module docstring at the top of `scripts/sdlc.py`. Check that nothing you relied on in the old table is now missing.
- Check `_drop_record()`'s finished sentence: "Returns why it failed, or None once the commit is made; a failure aborts the merge…". The reviewer checked it against the function body.
- `stamp_shipped()`'s docstring was also edited, though the seed didn't name it. The edit is to the docstring only; the function's code is untouched.
- `.sdlc/work/inbox.md` arrived already modified (entry `[building]`). Make sure only the intended status line goes into the commit.
- Decide whether the six stale comments go in this change or become a seed.
- There's no `plan.md`, which is fine because `intent.md` says `tier: 1`. The builder's report mentions a Tier 2 prompt, but the intent's Approach covers it.

- IMPACT: none — only docstrings changed; nobody using the plugin sees any difference in behaviour, commands or files.
