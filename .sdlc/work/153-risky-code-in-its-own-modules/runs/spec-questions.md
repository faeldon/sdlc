Resolved:
- **How this change's own run gets full depth.** A one-line listing of both new paths in
  `[review] sensitive`, committed on the base branch before the build starts (R10, R11). The paths
  don't exist on the base yet, so listing them early changes nothing for any other change. Because
  this change's diff creates both files, `depth()` sees them and runs full, using only existing
  code. A "please review deeply" flag would be a new feature, against "a move only". The module
  names (`scripts/closing.py`, `plugins/factory/scripts/landing.py`) are fixed by this spec because
  that commit spells them out.
- **Where the line falls.** By a rule a test holds (R3): the named entries move, a helper moves when
  only moved code calls it, and anything else the script still calls stays and is reached as
  `sdlc.<name>`/`factory.<name>`. The intent's "cmd_land, cmd_train, cmd_resolve and theirs" is
  read to include `land --close`, `land-fix`, `land-check` (its risk signals decide `by=auto`) and
  `land-verdicts`. `agent`, `_run_check`, `gate --land` and the landing-step records stay in
  `factory.py`, so its single-place invariants and the board's pins don't move.
- **One module per script, or more.** One per script (`closing.py`, `landing.py`). The parts call
  each other, and one list entry per script is all the review needs. A finer split later is a move
  of its own.
- **How a test's stand-in still reaches moved code.** Moved code reads shared names through the
  live binding, as `retro.py` does. Tests reach moved names on the module (`sdlc.closing.X`,
  `factory.landing.X`), with no re-exports. This is answered from `_load_retro()` and
  `retro.py`'s docstring.

Left for the person:
- **Does the change wait for the release, as the seed says?** If yes: the move ships alone in the
  next version, after 147, 149, 150, 151, 154 and 156 have landed and been released, so a
  regression in close or the landing traces to one release that changed nothing else there. If no:
  it can land as soon as its `depends_on` close, and the next release carries both the move and
  whatever those changes did to the same code, which is harder to pull apart if a host's close
  breaks.
- **Approve the precursor listing.** Who commits the `[review] sensitive` lines to the base branch
  before the build, and in what form (a Tier 0 commit, or a change of its own), is your call. This
  spec only requires that it is there before the first `verdicts`.
