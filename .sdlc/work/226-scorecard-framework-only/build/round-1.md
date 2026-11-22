I made all three doc edits, and they're left uncommitted. The four acceptance checks fail before the edits and pass after, and the 435 tests that read these docs pass.

**Slice built (one, Tier 1, with a `plan.md` because the change touches three files):**
- **`docs/RETRO-SCORECARD.md`:**
  - Deleted from *Seeds to build it* to the end of the file, so the doc now ends after *Hosts*.
  - Removed the opening note's "The last section lists the seeds that build it."
  - Rewrote all 36 `**Status:**` lines to read *captured* or *not captured: <what is missing>*, with no seed ids or change numbers. When only part of a metric is captured, the line says what's missing first, then what's captured.
  - Left every other line word for word.
- **What changed after checking against `retro --insights` and `scripts/retro.py`:** I didn't run the full `retro`, because its `retro.test_times` runs the whole suite.
  - Six metrics marked "needs S3/S7/S8/S16" are now captured: structural debt index, function-level design health, decisions escalated and kept defaults, auto-landed share, spurious stops and looks, and the person's experience.
  - Security findings are now captured (`bugs.review_sources.security`).
  - Still missing: changes to irreversible paths, the board's estimates against actual times, the skills' test cases' scores, dollars per line, a measured per-skill-run figure, the intent titles in follow-through, and edits to a change's own records on its branch.
- **`.sdlc/SDLC.md`:** deleted `### The release loop` along with its block, because that block was all the heading held. The guide's *Release due* rule now applies.
- **`docs/CONTRIBUTING.md`:** removed ", and the seeds that build it" from the scorecard row.

**Tests:** no new suite test, because only a deliberate revert could break these outcomes. Instead `checks.md` has four acceptance checks:
- the scorecard ends after *Hosts*;
- every Status line is captured or not captured, with no ids;
- the wave-based release block is gone from `SDLC.md`;
- the CONTRIBUTING row no longer mentions seeds.

**`plan.md`:** written before the edits, and the build follows it.

**`notes.md`:**
- Seed ids outside the Status lines were kept because of the word-for-word constraint. See the first decision below.
- Five lines in the scorecard were already longer than 100 columns, and I didn't touch them.

- DECISION: [default] Keep the seed ids that sit outside the Status lines? The Speed Diagnostics say "captured (S10, 175)" twice, and *Hosts* says "when S14 and S15 build it" and "(S1)". Going ahead with keeping them, as the intent's constraint says, with a follow-up in `notes.md`.
  - OPTION: keep them — follows the word-for-word constraint; four ids still point at nothing
  - OPTION: reword them now — the doc has no dead ids; goes past the constraint and the outcome's list
  - WHY: the constraint is the person's explicit words, and the outcome names only the Status lines
- DECISION: [default] Should this repo have a release rule of its own besides *Release due*? Going ahead with none.
  - OPTION: none — the guide's rule applies, and `SDLC.md` holds no restatement of it; nothing makes a release happen before a retrospective
  - OPTION: "release before each retrospective" — gives `time_to_users` a release to measure; another rule of this repo's own to maintain
  - WHY: the intent's outcome says this repo releases on *Release due*, as the guide says
- DECISION: [default] Should a metric still marked *not captured* get a seed? Going ahead with the Status line saying so and no seeds filed.
  - OPTION: just say so — the scorecard is the record, and nothing is filed without the person
  - OPTION: file a seed for each — seven gaps become visible in the register; the register fills with work nobody has chosen
  - WHY: filing seeds is the person's or the retrospective's call, not this change's

- UNTESTABLE: none

## Evidence

$ uv run --quiet --script scripts/sdlc.py retro --insights > /tmp/226-insights.json; echo "exit: $?"
exit: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 226 (before the edits, summarised)
False 1 The scorecard ends after Hosts
False 1 Every Status line is captured or not captured, with no seed id or change number
False 1 This repo releases on Release due
False 1 The contributor docs no longer list the scorecard's seeds
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 226 (after the edits, summarised)
True 0 The scorecard ends after Hosts
True 0 Every Status line is captured or not captured, with no seed id or change number
True 0 This repo releases on Release due
True 0 The contributor docs no longer list the scorecard's seeds
passed True
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_defaults.py tests/test_feature_map.py tests/test_nothing_local.py
435 passed in 82.15s (0:01:22)
exit: 0

$ grep -n '\*\*Status:\*\*' docs/RETRO-SCORECARD.md | wc -l
36
exit: 0

$ grep -rn --exclude-dir=.git --exclude-dir=work -e 'Seeds to build it' -e 'RETRO-SCORECARD.md`, \*Waves' -e 'follows the waves' .
exit: 1

$ git status --short
 M .sdlc/SDLC.md
 M docs/CONTRIBUTING.md
 M docs/RETRO-SCORECARD.md
?? .sdlc/work/226-scorecard-framework-only/
exit: 0
