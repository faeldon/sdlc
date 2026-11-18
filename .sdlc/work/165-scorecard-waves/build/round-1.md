I've built change 165, Tier 1, and left it uncommitted. Only `docs/RETRO-SCORECARD.md` changed, plus a new `checks.md` in the change folder. The change touches one file, so there is no `plan.md`.

**What changed in the doc**
- **Waves replaces Suggested order.** The new section opens with a short paragraph: each change's intent names its register entries, landing the change retires them, and any entry's text and state stay in `.sdlc/work/inbox.md`. Then come waves 0 to 6 as the intent's Approach lays them out:
  - Waves 0 and 1 are marked done, each seed or refactor beside its change (R1 = 160, S7 = 161, S1 = 162, R4 = 163, R2 = 164).
  - Wave 1½ is the two bug fixes, each with its idea.
  - Waves 2 to 5 list each change and the entries it takes in.
  - Wave 6 is the backlog outside the scorecard.
- **Full ids throughout.** I wrote every id in full (`2026-11-18-95`), not as the intent's `-95` shorthand, so a search for an id finds its wave. That is also what makes the acceptance check below possible.
- **Data table.** S17 (comment health, `2026-11-19-9`, Pillar "Quality, Cost", after S8) is a new row, and S5's row now names the feature map `2026-10-25-3` as its list.
- **Nothing else changed.** The rest of the doc is as it was, including the *Already filed* table. My new prose stays within 100 columns; the table row is long, like the rows around it.

**Coverage of the register:** `main`'s `inbox.md` (the same commit as this branch) has 60 open entries, and the Approach's plan names all of them exactly once, with none missing and no ids that aren't open. `2026-11-18-94` (S1) is already gone from the register, so it isn't listed. Before ship, this still needs checking again against `main`'s register for any nits filed in the meantime.

**Tests and checks**
- **No suite test.** No code or test reads this doc, so there's nothing for a suite test to cover.
- **Two acceptance checks in `checks.md`:**
  - Every one of the 60 ids appears exactly once in *Waves*.
  - *Suggested order* is gone, and the S17 row, S5's feature-map mention and the Wave 6 heading are present.
- **Both checks pass on the new doc.** They fail (exit 1) on the doc as it was before this change and on a copy with an id named twice, so they do catch the failures they're meant to.
- **`tests/test_nothing_local.py`:** 8 passed (no machine paths or forbidden project mentions).

**Left in `notes.md`:** nothing.

- DECISION: [default] Put 2026-11-19-1 and -2 (nits restating decisions D3 and D1 of 162) under R6, to be retired as answered? Going ahead with putting them under R6, as the Approach does, unless told otherwise.
  - OPTION: under R6 — every open entry has a place, and the nits leave the register when R6 lands; R6 lands two entries it doesn't build
  - OPTION: leave them out of the plan — the plan holds only work; two entries stay open with no wave, breaking "every entry named once"
  - WHY: the intent's outcome needs every open entry named in exactly one wave, and the Approach puts them under R6

## Evidence

$ sh /tmp/165-chk00   # check 1: every open id once in Waves
exit: 0

$ sh /tmp/165-chk01   # check 2: Suggested order gone, S17 row, S5 feature map, Wave 6
exit: 0

$ (both checks against git show HEAD:docs/RETRO-SCORECARD.md)
exit: 1
exit: 1

$ (check 1 against a copy naming 2026-11-18-95 twice)
2026-11-18-95 named        2 times
exit: 1

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 1.04s
exit: 0
