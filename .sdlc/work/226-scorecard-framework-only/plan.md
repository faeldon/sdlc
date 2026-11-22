# 226 — Plan

> Tier 1, written because the Approach touches three files. The intent's Approach is the spec.

## Files to change

- `docs/RETRO-SCORECARD.md`: delete `## Seeds to build it` through the end of the file; delete
  the opening note's sentence "The last section lists the seeds that build it."; rewrite each
  `**Status:**` line as *captured* or *not captured: <what>*, no S/R id and no change number.
  Everything else stays word for word (the intent's constraint).
- `.sdlc/SDLC.md`: delete `### The release loop → ...` and its one block (lines 83–88). The
  heading holds nothing else, so it goes with the block; the guide's own release rule stands.
- `docs/CONTRIBUTING.md`: the scorecard row drops ", and the seeds that build it".

Reused, not re-derived: the figures `sdlc.py retro --insights` prints (no host command runs), and
`scripts/retro.py`'s own keys, to check each Status line. The full `retro` is not run: its
`retro.test_times` runs the whole suite.

## What each Status line was checked against

`retro --insights` today: `work_mix`, `time_to_users`, `follow_through` (`missing`: the intent
titles), `process.lead` (`shares`), `process.throughput`, `bugs` (`escapes`, `rate`,
`review_sources.security`, `days_to_fix`), `pipeline` (`depth`, `unreviewed`, `gates`, `landing`),
`architecture`, `autonomy` (`escalations`, `kept_default`, `auto_landed`, `spurious_stops`,
`looks`), `by_way`, `cost` (`per_change`, `waste`, `by_role`, `by_model`), `spend.tiers`
(`out_per_line`, no dollars per line), `surface` (`share`, `retire`, `footprint`, `growth`),
`simplicity.workarounds`, `prose`; and in `retro.py`: the experience rating (`_experience_text`),
the indicator rows (`.sdlc/function-heat.py`, `.sdlc/comment-health.py`), and no read of
irreversible paths, the cases' scores or the board's estimates.

Changed verdicts: the structural debt index and function-level design health are captured in
this repo by `function-heat.py`'s indicator rows; decisions escalated, kept defaults, auto-landed
share, spurious stops and looks, and the person's experience are captured; security findings are
captured (`review_sources.security`), irreversible paths still aren't.

## Work order

One slice: the three doc edits, then the tests that read these docs.

## Tests

No new test: every requirement here is a deletion or a rewording only a revert could break, so
each is an acceptance check in `checks.md`. The existing tests that read these files are run by
name: `tests/test_retro.py` (the questions table), `tests/test_defaults.py` (SDLC.md holds only
answers), `tests/test_feature_map.py`, `tests/test_nothing_local.py`.

## Rollback

`git revert` undoes all of it; nothing is written outside the tree.
