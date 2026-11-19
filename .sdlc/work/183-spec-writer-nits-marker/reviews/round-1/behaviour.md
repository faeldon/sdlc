VERDICT: PASS

## Notes
- No `checks.md` exists for this change, so there are no acceptance checks to read.
- The spec names no end-to-end command, so I ran the closest path, which is the marker test.
- The change matches the intent. Both `spec-writer.md` and `prompts/spec.md` now say that each nit taken in goes by id on the Requirements `Nits taken in: <id>, <id>` line, and that an id anywhere else is never taken in. This is worded as `skills/spec/SKILL.md` words it.
- `spec-writer.md` also limits the spec-writer to nits the intent names or the person asks for, so it never takes one in unasked. This keeps the intent's constraint.
- 181's marker test now covers both files, so it fails if either stops saying `Nits taken in:`.
- The built prompt fixtures `tests/prompts/spec.txt` and `tests/prompts/spec-upgraded.txt` were updated.
- The gate record shows `GATE: PASS` for round 1.

## Evidence
$ cat .sdlc/work/183-spec-writer-nits-marker/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ git diff HEAD~1 -- plugins tests/test_skills.py
(diff: spec-writer.md gains the "Nits taken in" bullet, prompts/spec.md draft line gains the marker rule, test_skills.py adds both paths to the marker test's list)
exit: 0

$ sed -n 70,82p skills/spec/SKILL.md
(prints the core skill's wording: "its id goes on the section's `Nits taken in: <id>, <id>` line; an id written anywhere else is never taken in")
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k marker
1 passed, 418 deselected in 0.19s
exit: 0
