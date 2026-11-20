DECISION: ESCALATE

**Why.** Round 2 passed on all three reviewers. Round 1's one kept change, a test for "a failed git step leaves the draft", is done. The round-2 gate is green (`./check.sh`, 3464 passed), and every requirement from R1 to R14 has its named test by the reviewers' account. The one thing left is D2. It is a scope call: R11 says a row reads `none in the window` only when the window closed no change. The lead-time-by-way rows still break that rule, and only you can say whether this change has to fix them.

## Open items

- None. The one CHANGE (test, round 1: no test for a failed git step leaving the draft) was fixed in round 2 with `test_a_failed_commit_leaves_the_insights_draft_for_a_rerun`, which uses a real failing pre-commit hook. The nits left are F1 (the Step 6 line in `skills/retro/SKILL.md` runs past 100 columns, marked minor) and F4 (a weak "off while it doesn't exist" check in `test_config_reports_the_insights_doc`, recorded).

## Decisions to confirm

- SETTLED: D1: `plan.md` *Departures from the spec* explains it. `time` is None when no change was measured, which is exactly the window R11's test builds, so a reason stored in `time.tiers[t]` could never be read. The spec's Design says "The plan settles the exact key names against `retro()`'s return". `process.response` is a new block and leaves `time.tiers` as it was. The code review in round 1 checked it and passed it, and the behaviour check in round 1 found no requirement it broke.
- SETTLED: D3: this is the same question as D1, raised again by the code reviewer in round 1, who recommended keeping `process.response`. It is settled for the same reason as D1 (`plan.md` *Departures*, the round-1 code review).
- ESCALATED: D2: this decides how far the change reaches. R11 lists four blocks, but it also says "A row's note is `none in the window` only when the window closed no change". The lead-time-by-way rows (`process.lead`'s ways) still read `none in the window` when the window closed changes but none of that way. Whether R11's general sentence covers them, or they wait for a later change, is a scope call for you.
  - OPTION: leave the rows as built and carry the gap forward as a seed — no rebuild and the change lands now; but one kind of scorecard row still names the wrong reason, against R11's own general sentence.
  - OPTION: send it back to give the lead-time-by-way rows `no <way> change in the window`, matching the escape rate's rows — the rows then follow R11's sentence everywhere; but it costs another build round, and `test_a_figure_with_no_data_reads_a_dash_with_its_reason` must change.
  - OPTION: change R11 to name the four blocks only — the spec then matches what was built with no code change; but it writes down a known gap in the reasons as intended.
  - WHY: R11 lists four blocks, and `process.lead`'s ways is not one of them. So the builder stayed inside the listed scope and wrote the gap into `notes.md` instead of widening the change.

## For the person at ship

- **Look first at `scripts/retro.py`'s `cmd_retro_commit()`.** Check that it finds every problem in the draft before writing anything, that the draft stays out of the commit's `paths`, and that it removes the draft only after the commit succeeds.
- **Then `retro --insights`.** It empties all three host command lists, which is what keeps R4's promise that no host command runs.
- **Then `templates/retro.md`.** It gains `## Insights` and `{{insights}}`. Check that `TEMPLATE_READS` has not changed, so a host's own template override without the placeholder still renders.
- **Published interfaces you already approved in `spec.md`, *Contracts touched*:**
  - The policy edit to the *Retrospectives* paragraph in AGENTS.md: `retro-commit` now reads and deletes an untracked draft, and still commits only its four files. The spec's Boundaries mark this "Ask first … approved with this spec".
  - `{{insights}}` is an optional placeholder in the template override contract.
  - The new config key `[docs] insights`.
  - The new core agent `sdlc:insight` (tools `Read, Grep, Glob`).
- **The draft's shape, fixed by the script.** `INSIGHT_FIELDS` and the disposition kinds are constants in `retro.py`, so a host can't reword them.

## Release impact

- IMPACT: minor — hosts can newly get an `## Insights` section in their retrospective, extend the questions through `[docs] insights`, and use the new `sdlc:insight` agent. A template override without the placeholder still renders, so no host has to do anything.

## Undone items

- UNDONE: The scorecard's lead-time rows by way still say `none in the window` when the window closed changes but none of that way (`test_a_figure_with_no_data_reads_a_dash_with_its_reason` pins it): R11 named four blocks, not `process.lead`'s ways. `no <way> change in the window` would match the escape rate's. → seed: Lead-time-by-way scorecard rows name their real reason

## How to recover

- RECOVER: templates/retro.md: `git revert` of the change's commit restores the plugin's template, then run `sdlc.py record` so `.sdlc/setup.json` holds the old hash again. A revert can't undo two things:
  - Reports hosts have already committed keep their `## Insights` section as history. The next retrospective reads back only the scorecard table, so nothing is misread.
  - A host that copied the new template into `.sdlc/templates/` keeps its copy. Fix forward: a follow-up change that drops the `## Insights` section from the template, and `drift` would point those hosts to it.
