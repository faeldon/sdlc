VERDICT: PASS

The diff is `.sdlc/factory.toml` alone, as the intent's Affected section says.

- **Outcome met:** `gate_jobs` is 1 and `[autopilot] enabled = true` is set. The `[autopilot]` key is the one `autopilot.py` reads for `enabled`, and `guards` and the other keys stay at their defaults.
- **Header comment:** it no longer says "two gates at once". It gives the swap pressure and the 158.5 to 261.5 second round median as the reason for one gate, names M25, and says `gate_jobs = 1` is for that run too.
- **Gate:** `build/round-1.gate.md` shows PASS with exit 0.
- **Tests:** none, because the change is a settings value. The `factory.py config` and `autopilot --preview` checks need the base branch, so the intent defers them to after close.
- **D1:** the default is to leave `enabled = true` after the run. That is fine, since `--begin` still needs the person's WAIT.

## Notes
- NIT: .sdlc/factory.toml:1: The header comment is now seven lines of history (swap, medians, M24's 2026-11-22-38). The reasons for these settings are also in the intent and the commit, so a shorter comment would age better {docs S low}
- What's done well: the change stays inside its one file, and `guards` stays unset, so no guard is loosened.
- Ran: I read the diff and the gate record, and grepped `autopilot.py` for the `enabled` handling. I did not run the gate.
