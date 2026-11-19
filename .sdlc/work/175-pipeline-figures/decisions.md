# Decisions

- [x] R1 (person, revise): add a line `Nits taken in: 2026-11-19-19, 2026-11-19-21` to the Requirements, so the landing retires them
- [x] D1 (builder round 1, default): For `unreviewed`, a factory landing whose `Sdlc-Landed` has no `unreviewed=` field is counted as missing (`unreviewed not recorded`) and left out of `n`, not counted as `none`. Going ahead with this unless told otherwise. → settled by the approver: the intent's Constraints already answer it ("A figure a record doesn't hold for an older change is missing, counted in the trust band, never zero"), and so does the spec's R1/*Contracts touched* rule "missing, never zero". The security reviewer agreed in round 1, since counting such a landing as `none` would claim a review no record shows. The behaviour run on this repo confirms it: `unreviewed not recorded: 24`, with `n: 0`.
  - OPTION: missing — follows the intent's rule that a figure the records don't hold is missing, never zero; `n` is smaller.
  - OPTION: count it as `none` — larger `n`, but it claims every path was reviewed when nothing recorded that.
  - WHY: the intent's constraint that an older change's absent figure is missing, never zero.
