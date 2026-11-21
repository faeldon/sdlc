# Decisions

- [x] D1 (builder round 1, default): Leave nit 2026-11-20-47 (`intent_closes()` from the fork point) out of this change. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: leave it out, keep the follow-up in notes.md — no change to the bar; a build can still remove its own `closes:` line
  - OPTION: read the fork point and the working copy together — never loosens anything, but in a factory run the fork point never holds `intent.md`, so it does nothing
  - OPTION: record the approved `closes:` in the records ledger at `start` — actually fixes it; new mechanism, more than an S nit
  - WHY: the change's folder isn't tracked until ship commits it, so a read at the fork point finds no `closes:`. Using that alone would let every change carry a `- CONFIRM:` default to the landing, even one its intent says may not.
