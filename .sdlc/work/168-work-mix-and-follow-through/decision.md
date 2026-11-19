DECISION: READY

**Why.** All three reviewers passed in round 1 and the gate is green on the build as it stands (`./check.sh`: 3087 passed, 28 skipped). The test reviewer found a test for each of R1–R13; R14 (the docs) was meant to be checked by review only. The behaviour check ran `sdlc.py retro` on this repo, which printed the three new keys with their `n` and unmeasured counts, and left the tree unchanged. Nothing in the rounds suggests the spec was wrong, and `templates/retro.md` (the one irreversible path) was not touched: the figures go in through `{{window}}`, as the spec says.

**Open items.** There are no unresolved CHANGEs. Five nits are recorded in `findings.md`:
- F1 (code): `_is_process` also skips `.sdlc/setup.json`, which the spec doesn't list.
- F2 (code): a milestone whose seed was retired reads `carried`, while the same seed scored on its own reads `dropped`. This is also `notes.md` item 2.
- F3 (code): no test pins that a `&` inside a URL counts as `bg`.
- F4 (test): the same-figures test has no assertion on the follow-through sentence.
- F5 (test): no test checks the R14 docs.

**Decisions to confirm.** None. There is no blocking decision and no open default.

**For the person at ship:**
- **The report sentences:** check `scripts/retro.py`'s `value_band()` and `render_report(..., value=)`. Both `retro()` and `retro_report()` should call the one function, and the sentences should go only into `values["window"]`.
- **The process rule:** check `_is_process` and the `setup.json` skip (F1). Either accept it or ask for one spec line covering it.
- **Follow-through:** check `_retired_ids()`, which splits each `Retire` subject on `"; "`, and `_follow_through()`'s handling of `missing`.
- **The `bg` regex:** in `scripts/metrics.py`, check the regex and the docstring line saying `bg=` counts can be higher from 168 on.

- IMPACT: minor — `sdlc.py retro` gains three new figures (`work_mix`, `follow_through`, `time_to_users`), shown in the report's Window section. Closed-change records gain `fixes` and `work`. The metrics nit fixes only make `bg=` and the check detection catch more shapes.

**Undone items:**
- UNDONE: `docs/RETRO-SCORECARD.md` *Supporting: throughput* still says "by impact S2": the work classes now exist, but throughput isn't broken down by them. A later change (S14's report, or its own) can add `process.throughput` by `work` class. → seed: Break retro throughput down by work class
- UNDONE: Follow-through's milestone `done` by grouped rows reads `_milestone_verdicts()` against the current register, so a grouped seed retired with `inbox-commit` reads `vanished` there (and the milestone `carried`), while the same seed scored as a seed reads `dropped`. Teaching `_milestone_verdicts()` about `Retire` subjects would change what `direction.milestones` reports, which the spec's boundaries say asks first. → seed: Teach _milestone_verdicts() that a seed retired by inbox-commit is dropped, not vanished
