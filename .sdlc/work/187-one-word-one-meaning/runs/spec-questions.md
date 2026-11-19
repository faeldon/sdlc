**Settled by your answers**
- The command is `sdlc.py vet` (and `vet --strict`), and its glossary entry is `vet` (R1–R6).
- The release impact is `minor` (R23).
- `[models] verifier` is dropped with no shim and becomes an unknown role (R16).
- The agent and its prompts are renamed with `git mv` (R12).
- The guide heading becomes "The gate and the slow gate" (R9).
- `.sdlc/DIRECTION.md` stays out of the term test (R10).
- With `validate` gone, the clash with "validation" is gone too.

**Resolved from the code (unchanged)**
- *Does `drift` or setup propose the `sdlc.py vet *` permission rule on update?* Yes, through
  readiness, not drift. `permissions_status()` compares `ALLOW_RULES` with the shared settings. A
  host without the new rule reads `permissions: missing` and `complete: false`, so setup's next run
  drafts the rule from `permissions.missing` (`cmd_readiness()`, `scripts/sdlc.py`). The old
  `check *` rule stays, and it is harmless. R3 pins this.
- *What does `.sdlc/deprecations.toml` say?* Nothing. It holds only shims, and this change keeps
  none, neither for `check` nor for `[models] verifier`. The removals are said by `impact: minor`,
  the changelog line and REFERENCE.md's *After an update* (R23).
- *"How many passed" on the card:* no record holds per-check results. The card shows `passed` or
  `failed` from the landing's last acceptance run (R18).

**Left for you**
- `intent.md` still says `validate` in its title, Problem and Outcome. Its title becomes the
  changelog line (R23), so update it to say `vet` before ship.
