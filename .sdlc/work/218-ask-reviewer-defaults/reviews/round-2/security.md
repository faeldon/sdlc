VERDICT: PASS

## Notes

This is the first round I've reviewed, so I read the whole change: the diff to `factory.py`, `autopilot.py`, the builder agent, the decide and autopilot skills, the README and three test files. I found nothing Critical or High.

**Trust boundaries and STRIDE.** Untrusted text enters in two places:
- **Builder reports** (`build/round-<R>.md`). These are model output, and they now carry `- BUILT: D<n>` lines.
- **The `decisions.md` ledger.** Each line's `source` is set by the script itself: `builder round N` at `factory.py:1990`, `approver round N` at `:2237`, and `reviewer-<role>` at `:4282`. A reviewer cannot make its own line look like the builder's, which would get past the `startswith("builder")` check.

STRIDE results:
- **Tampering/spoofing:** the main risk is a builder that writes `- BUILT: D8` without building it. Medium, see below.
- **Information disclosure:** none. `ask` adds an `unbuilt` list built only from ledger fields that are already shown.
- **Denial of service:** none. The change reads a bounded set of local files.
- **Elevation of privilege:** none. No new write path, command execution, or tool permission is added.

**Fails safe.** Both new checks make things harder to land, never easier:
- `cmd_ask()` now says `rebuild` in more cases.
- `hold_causes()` now holds a change in more cases.

The autopilot hold also closes a real hole. `finish()` answers every open line as autopilot. Before this change, a reviewer's security default (like 216's D8/D9) could be answered and landed with no person ever seeing it. Now that change is held.

**Medium: a `- BUILT:` line is the builder's word, and nothing checks it against the code.** If a builder claims it built a reviewer's default and didn't, `ask` says `ship`, and autopilot doesn't hold the change. Two things limit this:
- The line only counts from a round later than the one that raised the default (`unbuilt_defaults()` compares round numbers). That round is reviewed in turn, so a reviewer whose default was skipped can raise it again.
- This design is the settled answer to D1, so it isn't a CHANGE.

A possible later hardening: have the reviewer who raised the default confirm it in the next round, rather than relying on the builder's line alone. I'm not filing it, since it reopens a settled decision.

**Low: round numbering after a restart.** A default raised before a restart keeps its old round number. Rounds after a restart continue the count (`restart_state()`), so a later `- BUILT:` still has the higher number and the comparison holds.

**What I checked:**
- **Report filenames:** `unbuilt_defaults()` keeps only names matching `round-(\d+)\.md`, so `round-N.gate.md`, `.restart.md` and `.files` are never read for `- BUILT:` lines.
- **Ledger parsing:** `read_ledger()` reads `source` through `LEDGER_RE` as `[^,)]+`.
- **Lines with no round:** a supervisor's line has no round number, so it counts as round 0 and any later `- BUILT:` clears it. That is a reasonable choice for a role that has no round.
- **Safety:** no secrets, dependencies, shell calls, subprocesses or destructive operations are added. `ask` still writes nothing.
- **Tests:** `round-2.gate.md` shows `./check.sh` passed (exit 0). I ran the new and related tests in the foreground: `pytest -q tests/test_factory_decisions.py tests/test_autopilot.py -k "unbuilt or built or reviewer_default or hold"` gave 11 passed.

**Done well:**
- A single function, `unbuilt_defaults()`, serves both `cmd_ask()` and autopilot's `hold_causes()`, so the two can't drift apart.
- `builder.md` tells the builder to write `- BUILT:` only for what the code now does.

- NIT: plugins/factory/scripts/factory.py:2296: `BUILT_RE` matches a `- BUILT:` line anywhere in a builder report, including one quoted inside a code fence; skipping fenced blocks would stop a quoted line from counting as built {robustness S low}
