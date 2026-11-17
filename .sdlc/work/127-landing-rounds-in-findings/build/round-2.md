I fixed the one kept change: `AGENTS.md` now names `land --close` as a third writer of `findings.md`. The gate still passes (2337 passed, 13 skipped).

- **KEPT code C1** (`AGENTS.md:195`): the Ship paragraph now reads "Ship, the factory's `carry`, and its `land --close` write `findings.md`, and `sdlc.py` only reads it (`findings_entries()`)". I used the reviewer's wording. The longer line pushed the rest of the paragraph past the file's width, so I rewrapped the paragraph to its end ("*Risky paths*."). Only the line breaks changed there.

`plan.md` and `notes.md` are unchanged this round. `notes.md` still holds its one unticked line: the note at the top of `templates/findings.md` names only `carry` as a writer.

No new decisions this round. Round 0's three defaults still stand: the landing writes at `land --close`; a finding raised in both a build round and a landing round counts once; a change kept in the last landing round with no later round is `recorded`.

## Evidence

$ git diff AGENTS.md
-run stay in `SKILL.md`. Ship, and the factory's `carry`, write `findings.md`, and `sdlc.py` only
-reads it (`findings_entries()`); `fix` never reaches a commit. `[review] sensitive` and
+run stay in `SKILL.md`. Ship, the factory's `carry`, and its `land --close` write `findings.md`,
+and `sdlc.py` only reads it (`findings_entries()`); `fix` never reaches a commit. `[review]

$ ./check.sh
All checks passed!
2337 passed, 13 skipped in 189.43s (0:03:09)
✔ Validation passed
✔ Validation passed
exit: 0
