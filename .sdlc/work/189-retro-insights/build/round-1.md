I've rerun the checks and the full gate now passes: 3463 passed and 29 skipped, ruff is clean, and plugin validation passes. My last report ended on a red gate, a stale prose test I fixed afterwards. It also left out the `exit:` lines for several commands, so this reply has them. Nothing else changed since that report: the build, the tests, the plan and the two decisions stand as I reported them.

## Slices built

1. Two nits:
   - R13: `_minutes()` keeps one decimal.
   - R12: `_trend()` compares the value as the table writes it. Its test passed on the old code too, because `str(float)` reads back exactly, so it pins the behaviour but proves no fix.
2. R10: `render_report(template, figures, *, indicators, insights)` takes the figures dict whole.
3. R11: `missing_because` on the four null-row blocks the spec names (response by tier, questions answered, the workaround counts, escape rate by way).
4. R1, R2: `guide/insights.md`, the `[docs] insights` key, and `insight_questions()`.
5. R3, R4: `retro --insights` gives each question only its pillar's figures. It counts them with all host command lists emptied, so no host command runs.
6. R5: `agents/insight.md`, with Read, Grep and Glob only and the fixed answer shape.
7. R6–R8:
   - The draft is read and checked by `retro-commit`, which refuses a bad draft before writing anything.
   - The answers are rendered into the report. The draft is never committed, and is removed only after the commit succeeds.
   - The template gains `## Insights`, and with no draft the section says "Not answered".
   - An older template override without the section still renders.
8. R9: the retro skill lists `Agent` and has a new side file, `skills/retro/insights.md`. Steps 4–6 and the WAIT question cover the insights.
9. R14: `REFERENCE.md`, `AGENTS.md`, `FEATURES.md` and `PROCESS.md` are updated, and `.sdlc/setup.json` is rerecorded.

**Tests added:** one per requirement, as listed in `plan.md`. `test_prose_counts_each_of_the_plugins_skills` was updated to expect `insights.md` as the retro skill's side file.

**`plan.md`:** a *Departures from the spec, as built* section covers `process.response`, why R12 can't be seen by a test, the prose test update, and the draft reading that `retro --report` and `retro-commit` share.

**`notes.md`:** one unticked line. The lead-time rows by way still say `none in the window` when the window closed changes but none of that way, because R11 named only four blocks.

## Decisions

- DECISION: [default] Keep the per-tier response reasons in a new `process.response` block rather than in `time.tiers[t]` as the spec says? Going ahead with `process.response` unless told otherwise.
  - OPTION: `process.response`: always there, per tier, over every change of that tier; adds a key to `retro`'s JSON
  - OPTION: `time.tiers[t]` as specified: `time` is None when no change was measured, the very window R11's test builds, so the reason could never be read there
  - WHY: only a block that is always present can explain a null median when nothing was measured.
- DECISION: [default] Leave the lead-time-by-way rows at `none in the window` when the window closed changes but none of that way? Going ahead as built, with a `notes.md` line, unless told otherwise.
  - OPTION: leave it: R11 lists four blocks and an existing test pins the wording; R11's general sentence isn't fully met
  - OPTION: give `process.lead`'s ways `no <way> change in the window`: matches the escape rate; widens R11 and changes the 184 test
  - WHY: the spec's list of blocks is explicit, and widening it is a scope call.

- UNTESTABLE: none

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 189
All checks passed!
323 files already formatted
3463 passed, 29 skipped in 184.35s (0:03:04)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro --insights > /tmp/ins189.json
exit: 0

$ python3 -c "import json; d=json.load(open('/tmp/ins189.json')); print(len(d['questions']), [q['title'] for q in d['questions']], d['problems'])"
7 ['Value', 'Speed', 'Quality', 'Autonomy', 'Cost', 'Simplicity', 'Tradeoffs'] []
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro --report > /tmp/rep189.md
exit: 0

$ sed -n '/^## Insights/,/^## Speed/p' /tmp/rep189.md
## Insights

Not answered: this report was written without the retrospective's insights.

## Speed

$ uv run --quiet --script scripts/sdlc.py drift > /tmp/drift189.json
exit: 0

$ python3 -c "import json; d=json.load(open('/tmp/drift189.json')); print(d['breaking'], d['refresh'], d['report'])"
[] [] []
exit: 0

$ git -C <path-to-clone> status --porcelain
exit: 0
