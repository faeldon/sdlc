# Decisions

- [x] D1 (builder round 1, default): Treat a raise from the same source and of the same kind, with the same options in the same order and the same why, as one already filed, even when its question is worded differently. Going ahead with that. → decided: the assumed default, confirmed
  - OPTION: match on source, kind, options and why — catches a resumed agent's reworded re-raise, as with 187's D1/D4 and D2/D5; two different questions with word-for-word identical alternatives would be filed once
  - OPTION: match identical text only — never merges two questions; does nothing for 187's case, which identical text already covered
  - WHY: the intent's outcome is "a decision raised twice in one reply lands once", and 187's twice-raised decisions were reworded, not identical
