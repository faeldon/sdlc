I resolved all three conflicted files and the gate passes again: 2374 passed, 13 skipped. I edited only those three files and ran no git command.

**`.sdlc/work/inbox.md`**
- **Base:** I kept its new `[2026-11-18-11] findings.md template note names the landing as a writer` entry, with 127's carried-forward note under it.
- **This change's side:** `[2026-11-18-6]` stays deleted, as the landing asked. I also dropped this side's stale `[2026-11-18-7] Landing review rounds in findings.md` heading, because the base had already retired that seed (127 took it in).

**`plugins/factory/README.md`**
I merged the two versions of the `findings.md` row into one. It keeps the base's "the landing's too" and this change's "a nit to file with its Theme:, Cost: and Value:".

**`plugins/factory/scripts/factory.py`**
- **Kept from base:** the `kind` argument on `_no_verdict()`, landing rounds in `agent_findings()` (their docstring, and the `kind` on each finding), and its `carried` logic.
- **Kept from this change:** `read_nit()`, the nit weighing, and the `file` and `note` fields on each finding. The docstring now covers both.
- **One code change beyond merging text:** nits are now weighed from build rounds only. Since 127, a landing round can be passed in, but only when `land-close` rewrites `findings.md`, which is after the yes has already filed the nits. A landing round's numbers also start again from 1 (land-1 after build round 3), and my nit logic compared round numbers. Without this, a landing round could make a nit look raised again or handed on, or appear as one to file that was never filed. Now:
  - the "raised again" check and `reworked_round()` read build rounds only;
  - a nit raised only in a landing round is `minor` and is never filed;
  - so `findings.md` matches what the landing actually filed.

I checked this by hand: adding a landing round, which re-raises a handed cheap nit and adds a new one, leaves the filed set the same, and the new nit is `minor`. There's no test for it, because I was only to edit the conflicted files.

## Evidence

$ ./check.sh 2>&1 | grep -E "passed|failed|FAILED|All checks|already formatted|would be"
All checks passed!
259 files already formatted
2374 passed, 13 skipped in 86.59s (0:01:26)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift
{'breaking': [], 'refresh': [], 'report': []}
exit: 0

$ grep -n '^<<<<<<<\|^=======$\|^>>>>>>>' .sdlc/work/inbox.md plugins/factory/README.md plugins/factory/scripts/factory.py
none-left
exit: 0

$ grep -c "2026-11-18-6\|2026-11-18-7\]" .sdlc/work/inbox.md
0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0

$ uv run --group dev python -I - (agent_findings on build rounds, then with a landing round added)
[('round', 'src/a.py:1: cheap', 'fixed', False), ('round', 'src/b.py:2: later', 'recorded', True)]
[('round', 'src/a.py:1: cheap', 'fixed', False), ('round', 'src/b.py:2: later', 'recorded', True), ('land', 'src/c.py:3: new', 'minor', False)]
exit: 0
