I've built 091 and left it uncommitted on its branch, ready for your review at `/sdlc:ship`. `./check.sh` passes with 1,937 tests, the portable set passes, and `plan.md` was written before any code.

**One thing in the spec can't be done as written:** its by-hand Verification steps 1–4 can't run on 091 itself. 091's folder holds `runs/`, so it is a factory run, and R2 says `sdlc.py gate` must refuse those. I ran it: it refused (exit 1) and wrote nothing. Tests on fixture repos cover the same steps instead.

**What was built, one slice at a time (each test seen failing first unless noted):**
1. **The build hash** (`hand_build()`, R6): combines the merge-base with the content of every path the change touched (committed, uncommitted, untracked), leaving out the change folder and `.sdlc/last-id`. Tests: the hash holds when the same work is committed and when only the folder changes. It changes on a code edit, a new file, a deletion and a rebase onto a moved base.
2. **The command** (`sdlc.py gate NNN`, R1–R5, R13, R14):
   - It runs the base branch's check from the change's checkout and refuses in the seven R2 cases, writing nothing.
   - It appends one attempt to `build/gate.md` in the factory's record shape, with machine paths replaced by placeholders.
   - It is in `OWN_SCRIPT_CMDS` and never pre-approved: not in `READ_ONLY`, `ALLOW_RULES` or any skill.
   - The main pin test runs `factory.py gate` and `sdlc.py gate` on the same fixture, red then green. Their records match line for line apart from `Build:` and `Seconds:`.
   - Other tests pin the copied constants and the placeholder function to `factory.py`'s. They also cover each outcome (pass, fail, timeout, couldn't start, tree changed) and check the record has no `\r`.
3. **The reader** (`hand_gate()`, R7): returns nothing without a record. A record counts as current only on the change's own branch and the build it judged. A malformed record comes back as a problem and never raises.
4. **The board** (R8–R10):
   - A current green record puts a hand-built card in Test with `/sdlc:ship` next, at stage `plan` or `build`. An edit outside the change folder sends it back to Build.
   - A current red record keeps it in Build and tells you to read `build/gate.md`, fix it and gate again.
   - Factory cards never read the record.
   - `board.html` shows a `gate green` / `gate red` badge, only while the record is current.
5. **Status** (R11): an open change's line gets `· gate green` or `· gate red` while its record is current, and nothing when the record is missing or stale.
6. **Metrics** (R12): a Bash call running `scripts/sdlc.py gate` counts as a `check` event, failed when it errors, even when `commands.check` is unset. The test that close's factory counts ignore a hand change's red record passed the first time, because nothing reads that file. It pins behaviour that already held.
7. **Docs** (R15): `docs/REFERENCE.md` has a new paragraph on the hand gate, and its board paragraph is updated. I also updated the board sentence in `AGENTS.md`, because it describes how `_seen()` decides a card's column.

**`plan.md`:** updated to match the build: the helper functions added (`_hand_hash`, `_refused`, `_gate_attempts`), the real test names, and the note about the Verification steps.

**`notes.md`:** nothing left there.

- DECISION: [default] The spec's by-hand Verification steps 1–4 name 091, which the spec's own R2 refuses because its folder holds `runs/`. Options: accept the fixture tests as that verification; or try it by hand on a separate test change. Going ahead with the fixture tests (`test_board.py`'s gate/edit/read-again tests and `test_status_marks_a_current_gate_only`), which run the same steps.

## Evidence

$ ./check.sh
All checks passed!
192 files already formatted
1937 passed in 81.77s (0:01:21)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable
207 passed, 1730 deselected in 55.99s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_hand_gate.py tests/test_board.py tests/test_metrics.py tests/test_factory.py
319 passed in 6.46s
exit: 0

$ uv run --quiet --script scripts/sdlc.py gate 091
{
  "refusals": [
    "091-hand-gate-record is a factory run: its gate is `factory.py gate`"
  ]
}
exit: 1
