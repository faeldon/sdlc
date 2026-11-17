
**What this revision changes, as you asked:**
- **Retired nits:** R13 now also drops the nits the landing retired. The resolution finds them with `named_nits()`, the rule the landing used to retire them, applied to the register as the builder resolved it. It reports their ids in `dropped`, next to the `idea:` and `fixes:` entries. A new test, `test_a_landing_resolution_never_keeps_the_nits_it_retired`, pins it.
- **Ids only:** register entries are matched by id alone. A title-valued `idea:` is skipped, and this is now a stated rule in Contracts touched and Boundaries.
- **Policy widening:** the mend's wider reach (the approver, the verifier, landing rounds) is marked approved in Contracts touched; AGENTS.md's paragraph is updated at ship.

**Already resolved, unchanged:**
- *Is a read-only command's missing exit a mend, or no stop at all?* A mend (R1), and for any command, not only reads. The intent's Outcome already says "a mend, not a stop". The script can't reliably tell a read from a write, and treating it as no stop would let a claim stand on evidence no one saw finish.
- *Does a landing mend count against the same "once per role" as a build round's?* No: once per role per landing round, recorded as `<role> land-<n>` in `runs/mended`. `mended()` already skips non-numeric rounds, so neither loop uses up the other's allowance (R3).
- *What counts as a verifier's "preamble"?* 2026-11-17-77's case was `- **KEPT:**`, a problem of shape, so the verifier is mended whenever `read_verified()` reports a problem with its reply (R10).

**Left for you:** nothing open.
