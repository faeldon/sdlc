DECISION: ESCALATE

**Why**: All four round-1 reviews are `VERDICT: PASS`, and the gate record reads `GATE: PASS` (3635 passed). I found no requirement without code or a test, and no open Critical or High finding. The decision is ESCALATE only because D1 is a scope default that I may not settle. I read the files and ran nothing myself.

**Open items**
- NIT, code reviewer: `docs/REFERENCE.md:508` has a line over 100 characters and needs a rewrap.
- NIT, code reviewer: `skills/intent/batch.md:34` has two lines that run past the wrapping width.
- NIT, test reviewer: `test_idea_and_bug_offer_an_origin_line` only checks that `Origin: self` is absent, so it would miss the skills saying "self" in other words.
- NIT, security reviewer: `origin_trailer()` at `scripts/closing.py:558` catches every `Exception`. A coding error there would quietly make origins unknown on every close. `fix_trailers()` does the same.

**Decisions to confirm**
- ESCALATED: D1: masking `plugin=<version>` in `tests/fixtures/close-output.json` is an unrelated test edit riding on this change, which is a scope call. The person should choose between that and fixing the fixture in its own Tier 0 change.
  - OPTION: mask the version in this change — the gate goes green and later releases won't break the fixture again, but an unrelated test edit rides on this change.
  - OPTION: revert it and fix it in its own Tier 0 change on the base branch — this change stays narrow, but its gate stays red until that lands.
  - WHY: the gate runs the whole suite, and the fixture fault is on the base branch itself, not in this change's code.
- SETTLED: D2: `spec.md` says origins are never guessed or backfilled, and a missing `origin:` line reads as unknown (R2, R3). The reviewers confirmed that leaving 207's own intent unset is what the spec intends.

**Every other reason you escalate for**
- ESCALATED: look: `scripts/closing.py: origin_trailer()` — this is a sensitive path, so the person should look at it before it lands. It is the only new code in close. It writes a trailer only from the two fixed words, never raises, and is called only from `_step_remove_folder()`.

**For the person at ship**
- Look first at `origin_trailer()` and its call at `scripts/closing.py:1149`.
- Then look at the `_change_record()` and `_origins()` changes in `scripts/sdlc.py` and `scripts/retro.py`, and at the one clause added to Step 4's question in `skills/intent/SKILL.md`.
- Last, look at the D1 fixture change in `tests/fixtures/close-output.json`.
- The spec's *Contracts touched* names no published interface the person approved. `templates/` is untouched, and so is the metrics trailer contract beyond one new key.

- IMPACT: minor — someone holding the previous release can now set `origin:` on an intent, which close records as `Sdlc-Origin`, and the retrospective counts changes by it.

**Each undone item's disposition**: `notes.md` does not exist, so there are no unticked items.
