VERDICT: PASS

No Critical or Required findings. I reviewed `main...HEAD` (the change's own commit), not a plain `git diff main`. `main` has since gained 2 commits, including `Close 100-seeds-marked-by-changes`. A plain diff would show that work as reverted, and it isn't this change's.

## Notes

- **Main moved again after the rebase.** `HEAD` is 2 commits behind `main`. That is the case this change handles. `land --close` will return `moved`, and the skill sends the landing back to its rebase. This is not a defect in the change.
- **Optional: a repeated `land-fix --ask`.** It refuses while the fix round it opened hasn't passed, because `land_verdict` for that round isn't `pass`. That is probably the intent. A rerun after the ask was written but before the builder ran gets a refusal that says "hasn't passed" rather than being idempotent. Worth a line in the README if someone hits it.
- **Optional: `Write` and `Edit` in the land skill's `allowed-tools`.** They are broader than the other grants. `test_the_land_skill_passes_a_fixs_id_never_its_words` pins them, and the skill limits them to `decisions.md`. Reasonable, but say so in the skill's prose if you want to be explicit.
- **Nit: `cmd_land_fix --commit`.** It computes the dirty paths outside the folder itself, and `_amend_record()` computes them again. The duplication is small, and `also` keeps 097's amend as the one commit path.
- **Done well:**
  - `_behind()` is the factory's own `rev-list` count, with no import of `sdlc.py` and no `main` literal.
  - A move is recorded in `runs/land-moves` before the amend, so the commit it was found on carries it.
  - The bound comes from the base branch's `[land] moves`, so a change can't raise its own.
  - The racing-close path reads the base, not close's refusal text.
  - The fix's words travel through `decisions.md` and never reach a command line.
  - `Sdlc-Landed … unreviewed=` keeps `by=` first, and file paths stay in the body, not the trailer.
  - `landed_unreviewed()` leaves the field out when it is missing or unreadable, so measuring never refuses.
- **Ran:** `./check.sh`: ruff check and format clean, 2137 passed and 9 skipped, `claude plugin validate --strict` passed. I did not run the new `test_land.py` tests on their own.
- **Not checked:** I did not re-read each new test's body for a case that can't fail. I relied on the builder's recorded red-then-green evidence in `build/round-<R>.md`.
