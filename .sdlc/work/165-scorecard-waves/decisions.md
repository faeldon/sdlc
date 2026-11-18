# Decisions

- [x] D1 (builder round 1, default): Put 2026-11-19-1 and -2 (nits restating decisions D3 and D1 of 162) under R6, to be retired as answered? Going ahead with putting them under R6, as the Approach does, unless told otherwise. → settled by the approver: the intent settles it. Its Outcome requires "every register entry open when this lands is named in exactly one wave", and its Approach says "R6 takes 2026-11-19-1 to -4 and -100". The doc only lists the two nits under R6. Whether they are actually retired is up to R6's own intent and landing, so this change neither builds nor retires anything. Both reviewers (code.md, behaviour.md) confirmed the doc follows this default.
  - OPTION: under R6 — every open entry has a place, and the nits leave the register when R6 lands; R6 lands two entries it doesn't build
  - OPTION: leave them out of the plan — the plan holds only work; two entries stay open with no wave, breaking "every entry named once"
  - WHY: the intent's outcome needs every open entry named in exactly one wave, and the Approach puts them under R6
