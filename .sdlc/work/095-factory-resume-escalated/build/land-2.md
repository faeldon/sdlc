I've resolved both conflicts, keeping both sides' intent. No conflict markers remain, and the full gate passes: 1986 tests, ruff clean, and both plugin validations green. As asked, I edited only those two files and ran no git command.

**`.sdlc/work/inbox.md`.** Both sides were removing an entry at the same place, so the conflicted section now holds neither entry:
- **Base side:** it retired the 2026-11-17-11 nit ("resolve stops when a merge empties one of the branch's commits"), because 094 shipped that fix.
- **This change:** it deletes its own seed, 2026-11-17-16 ("Resume an escalated factory run"), as shipping a change does with its idea.
- Every other entry stays as base has it, including -10, -19 and -22 to -25.

**`AGENTS.md`, the factory paragraph.**
- **Base side:** 090 rewrote the Architecture section as a short map, each rule said once, with detail pointed elsewhere. This change's side was the old long text with one added restart sentence. I kept base's map whole, including the newer `runs/mended` / `preamble()` wording, and dropped the old long text.
- **This change:** I added its rule to base's paragraph in the map's terser style:
  - only the current `decision.md` is ever a run's decision;
  - an ESCALATE sent back (`restart_state()`, `cmd_restart()`) is kept as `decision-<n>.md` and never written over;
  - the new run counts its rounds from the round its `build/round-<R>.restart.md` names.

  The full description is already in `plugins/factory/README.md`, where base's map points for factory detail.

## Evidence

$ grep -n '^<<<<<<<\|^=======$\|^>>>>>>>' .sdlc/work/inbox.md AGENTS.md
(no output)
exit: 1

$ ./check.sh
All checks passed!
214 files already formatted
1986 passed in 35.83s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
