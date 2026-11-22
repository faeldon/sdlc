
**I resolved these open questions from the intent and the code:**
- **How is "the same nit, reworded" told apart?** By neither path:line nor a reviewer's mark. A
  role's nits are filed from its last complete build round only (R1), and each later reviewer is
  asked to raise its earlier nits again, word for word (R4). An earlier finding's path is used
  only to label it `fixed` or `minor` (repeat) in `findings.md` (R3).
- **Is `stale` a reason of its own?** Yes. The intent's Outcome names all three reasons, and the
  retro can then tell "moved on" from "not worth it" (R7).
- **Does the guide's nits rubric state the filing bar?** No. Its "nits cap at 5" is ship's, so
  `guide/` isn't edited and no `sdlc.py record` is needed. The factory's bar goes in its README
  (R11).
- **Nits taken in:** none. The intent names 2026-11-21-55 only as an example of a stale nit. It is
  for retiring after this lands, not for this change to build. Taking it in would record "taken in
  by 230", which is false.

**Left for you:**
- **How does a landing file fewer: a value floor, a lower cap, or both?** The draft keeps
  `NIT_CAP = 5` and adds a `med` floor (R5).
  - **Floor alone (the draft):** 55 of today's 64 nits are `low`, so the floor would cut roughly
    6 in 7. The cap would rarely bind, and it stays the guide's 5.
  - **Cap 3 alone:** `low` nits keep being filed, just fewer per change. The factory's cap and
    ship's 5 would then differ.
  - **Both:** the fewest nits filed, with the cap mostly redundant.
- **Does `/sdlc:ship` follow the same bar?** The draft says no (R12): ship's person approves each
  nit. Yes would mean editing ship's `SKILL.md`, and probably `guide/process.md` (with
  `sdlc.py record`), and would put an irreversible-path question into this change.
- **Today's duplicates and stale nits (for example 2026-11-21-10 and -11, both on the fake
  `claude`'s encoding, and the stale 2026-11-21-55).** The draft leaves these to `/sdlc:idea`
  after landing, one WAIT each. If you'd rather this change carry them, its ship would hold
  `Retire` lines in `entries.md`, which stretches the rule that held `Retire` lines are for nits a
  diff fixes.
