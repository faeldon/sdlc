# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Build

- `read_verified()` gained a `where` argument so a landing round's problems name
  `reviews/land-<n>/verified.md`, not `reviews/round-<n>/` (the verifier's mend prompt quotes them).
- `drop_entries()` ends an entry at the next level-one or level-two heading, where `retire_nits()`
  ended it at any heading: a `###` inside a retired nit is now deleted with it.
- `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make` became
  `test_a_hand_shipped_change_is_not_committed_again` (R9): with R8, a `HEAD` whose `intent.md`
  isn't shipped reads as a landing whose commit failed, so the hand-shipped case now commits its
  `intent.md` too.
- [x] `_resolve()`'s problems still say "round <n>" for a landing round's answer ("C3, which no → seed: 2026-11-17-80
  change of round 1 is"); only the file named before them says which kind of round it is.
