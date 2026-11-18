DECISION: READY

**Why.** The change adds `"scripts/closing.py"` and `"plugins/factory/scripts/landing.py"` to `.sdlc/config.toml`'s `[review] sensitive` list. They are quoted exactly as 153's spec greps for them, and the comment above the list now says why they're there. That is everything the intent asks for. Both reviewers gave `VERDICT: PASS` in round 1, the gate (`./check.sh`) is green with 2908 passed, and `sdlc.py accept 158` passes the one acceptance check. The edit only adds review depth and loosens nothing. Neither path exists yet, so no open change's depth moves now.

**Open items**
- None. The only finding is a NIT from `code` (F1, `recorded`): the comment at `.sdlc/config.toml:26` is one long sentence.

**Decisions to confirm**
- None. The change has no `decisions.md` and no open defaults.

**For the person at ship**
- Read the `[review]` block in `.sdlc/config.toml`, lines 26–38. Check that the two new entries match 153's R10 and Verification greps character for character. Check that `irreversible` didn't change.
- The behaviour reviewer didn't run `factory.py verdicts`, so "same depth before and after" is inferred, not shown. The builder's evidence backs it up: neither file exists, and no open branch (153 or 158) touches either path.
- One outcome can't be checked until this lands: `git show main:.sdlc/config.toml | grep` finding both lines. Run it once the change is on `main`, before 153's build starts.

- IMPACT: none — this is only the plugin repo's own review list. Nothing a host installs or runs changes.

**Undone items**
- None. The change has no `notes.md`, so it has no unticked items.
