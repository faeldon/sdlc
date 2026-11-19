VERDICT: PASS

The spec-writer's agent file and the spec prompt now both carry the `Nits taken in:` rule, worded like `skills/spec/SKILL.md:76-79`. The extended marker test passes.

The Tier 1 change has no spec, so there is no end-to-end command to run. The closest path is the test that pins the marker.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- The rule is added to `plugins/factory/agents/spec-writer.md`. It names only the nits the intent or the person asks for, which matches the Constraint "never unasked". It also says an id written anywhere else retires nothing.
- `plugins/factory/prompts/spec.md` carries the same rule. Both built fixtures, `tests/prompts/spec.txt` and `spec-upgraded.txt`, were re-recorded to match.
- `tests/test_skills.py`: `test_every_place_that_takes_a_nit_in_names_the_marker` now lists the spec-writer file and the spec prompt.
- The gate record `build/round-1.gate.md` reads `GATE: PASS`, exit 0.

## Evidence
$ git diff 910657a749c30ddc000f60bcefd9c6fbee75108a...HEAD -- plugins tests
(diff as read above: the spec-writer rule, the prompt rule, the two re-recorded fixtures, the two files added to the test's list)
exit: 0

$ head -20 .sdlc/work/183-spec-writer-nits-marker/build/round-1.gate.md
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ uv run --group dev pytest tests/test_skills.py -q -k nit
4 passed, 415 deselected in 0.05s
exit: 0

$ sed -n 74,80p skills/spec/SKILL.md
(the reference wording: "Each one taken becomes a requirement, and its id goes on the section's `Nits taken in: <id>, <id>` line; an id written anywhere else is never taken in.")
exit: 0

$ cat .sdlc/work/183-spec-writer-nits-marker/checks.md
No such file or directory
exit: 1
