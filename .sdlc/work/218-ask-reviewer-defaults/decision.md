DECISION: READY

**Why:** Round 2 is all `VERDICT: PASS`, with a green gate (`./check.sh`, exit 0). Round 1's requirements are covered by tests. Those cover a reviewer's default confirmed with no later build giving `rebuild`, the builder's own default giving `ship`, and a later `- BUILT: D<n>` clearing the default. D2's answer, that autopilot holds such a change, is built in `hold_causes()` and tested. Nothing in the reviews suggests the spec was wrong, and no Critical or High finding is open.

**Open items:**
- NIT (code reviewer): `tests/test_autopilot.py:~984` has a backslash-continued f-string that is hard to read.
- NIT (test reviewer): the `cmd_ask()` docstring in `factory.py` wraps short.
- NIT (security reviewer): `BUILT_RE` also matches a `- BUILT:` line quoted inside a code fence.
- Medium (security reviewer): a `- BUILT:` line is the builder's word and nothing checks it against the code. D1 settled that design, and the line only counts from a later, reviewed round, so it is not a change request.

**Decisions to confirm:**
- D1 and D2 are both ticked, so no blocking decision is open. D1 was settled by the approver. D2 was decided by the person ("autopilot holds such a change"), and the build follows it.
- No default is still open.

**For the person at ship:**
- Look first at `unbuilt_defaults()` and `BUILT_RE` in `plugins/factory/scripts/factory.py`, then at `hold_causes()` in `plugins/factory/scripts/autopilot.py`. `cmd_ask()` and autopilot share that one rule.
- No published interface is touched. `ask`'s `next` values are unchanged, only when each is given.
- The change touches no destructive operation or secret.

- IMPACT: patch — `ask` says `rebuild` in more cases and autopilot holds more changes. Nothing new is offered and nothing is asked of someone upgrading.

**Undone items:** `notes.md` doesn't exist, so there are no unticked `- [ ]` items to dispose of.
