# Decisions

- [x] D1 (builder round 1, default): Is a look "covered" when the spec names the interface under *Contracts touched* (at Tier 1, the intent's *Affected* contracts or its Approach) **or** when a person's `→ decided:` answer settles it? Going ahead with either one, but never a settled or assumed default. → decided: the assumed default, confirmed
  - OPTION: either the spec's contracts or the person's answer — both are the person's own approval; it moves the most stops that were never needed
  - OPTION: only the spec's *Contracts touched* — simplest to check; misses an interface the person approved in a decision
  - OPTION: only the person's words in `decisions.md` — clearest record of consent; 177's looks, approved in its spec, would still stop
  - WHY: the intent's Constraints say "the approved spec or the person's answers"
- [x] D2 (builder round 1, default): Give a look a fixed `<target> — <why>` form inside the reason text, without a new parsed field? Going ahead with the fixed prose form. → settled by the approver: The intent answers it. Its Constraints say "No change to how `factory.py` parses decisions or ledgers", and its *Affected* Contracts say the `- ESCALATED: <kind>: <why>` line "stays as `REASON_RE` reads it". That rules out a parsed field. Its Approach says "each look's reason starts with what to look at", which is the target-first prose form that was built (`approver.md:100-103`, `docs/REFERENCE.md:543-545`). Both round-2 reviews confirmed that `REASON_RE` still reads it whole.
  - OPTION: target-first prose, split at ` — ` — no parser change, so `REASON_RE` and the "no factory.py change" constraint hold; an approver that forgets the form still yields a readable question, just with the whole reason
  - OPTION: a parsed target field — decide could quote it exactly; changes `REASON_RE` and its pinned copy, which the intent rules out
  - WHY: the intent's constraint that how `factory.py` parses decisions doesn't change
