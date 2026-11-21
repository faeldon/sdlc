DECISION: READY

**Why:** Every requirement R1 to R11 has code and a named test by the reviewers' account. The gate passed (`./check.sh`, 3895 passed) and all four round-1 reviews are `VERDICT: PASS`. The build matches the approved spec. The one policy edit, a second state cache beside the update cache, is named under the spec's *Contracts touched*, and AGENTS.md, `READ_ONLY`'s comment and `cmd_preflight()`'s docstring were updated together.

**Open items**
- None. The only findings are three test NITs and one refactor NIT, all low severity and not blocking. There is no `notes.md`, so nothing was carried over from the rounds.

**Decisions to confirm**
- There is no `decisions.md`, so no blocking decision and no open default.

**For the person at ship**
- Look first at `scripts/sdlc.py`: `base_ci()`, `ci_problem()`, `_write_ci_cache` and the `cli_status()` entry. Then `scripts/trackers/github.py`: `ci()` and `ci_state()`. Last, `plugins/factory/scripts/landing.py`: `land_signals()`.
- The AGENTS.md change to the "one write" claim, which now names both caches, is a policy edit. The spec's *Contracts touched* flags it, so it was shown at spec approval.
- Nothing live was run against GitHub; the tracker is covered through the `gh` fake only.
- Failure to read CI is silent (`unknown`) by design, so an unreachable `gh` leaves the red signal off and auto-landing can still approve itself. The intent states this outright.

**Release impact**
- IMPACT: minor — someone holding the previous release newly sees a red CI on the base branch under `status` Problems, in ship's question and as a landing signal. Nothing existing changes for a host with no GitHub tracker.

**Undone items**
- None: `notes.md` doesn't exist, so there is no `- [ ]` item to place.
