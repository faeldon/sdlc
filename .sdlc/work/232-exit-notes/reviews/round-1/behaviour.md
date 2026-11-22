VERDICT: PASS

The new `exit:` reading works, and the one check in `checks.md` should pass. The change did what the intent asked. Two small points are in the Notes; neither is a failure.

## Notes
- **`checks.md`, "Both prompts say a hook-refused command is no `$ ` line and every exit is a real code"**: I expect it to pass. I ran its three grep conditions by hand, not the block itself, and all three matched. The first two are the "never ran" sentence and `echo "exit: $?"` in `builder.md` and `reviewer-behaviour.md`. The third is the "list it under `## Notes`" sentence in `reviewer-behaviour.md`.
- **Reading change**: `EXIT_RE` is now `^\s*exit:\s*\d+(?:\s.*)?$`.
  - It accepts `exit: 2 (note)` and `exit: 0 # ok`.
  - It still rejects `exit: nonzero`, `exit: not run` and `exit: 2x`, because they carry no code.
  - It is slightly stricter than the intent's Approach, `\d+\b.*`. It needs whitespace after the code, so `exit: 2(note)` would still be flagged. That is fine.
- **Gate**: the record `build/round-1.gate.md` ends in `Validation passed`.
- **Test**: the new parametrised test `test_an_exit_with_a_note_after_its_code_is_an_exit` covers each of those forms. The six cases passed in my run.
- **Decisions**: D1 and D2 are builder defaults, not blocking. Both are reasonable and I raise nothing new.

## Evidence
$ grep -n 'EXIT_RE' plugins/factory/scripts/*.py
plugins/factory/scripts/factory.py:322:EXIT_RE = re.compile(r"^\s*exit:\s*\d+(?:\s.*)?$")
plugins/factory/scripts/factory.py:1750:        elif EXIT_RE.match(line):
exit: 0

$ for f in reviewer-behaviour.md builder.md: tr '\n' ' ' < "$f" | grep -q 'A command a hook refused never ran, so it is no `\$ ` line'; grep -q 'echo "exit: \$?"' "$f"; then tr '\n' ' ' < reviewer-behaviour.md | grep -q "list it under \`## Notes\`"
a 0
b 0
a 0
b 0
c 0
exit: 0

$ uv run --group dev pytest tests/test_factory_depth.py -q -k "exit_with_a_note"
6 passed, 58 deselected, 1 warning in 33.99s
exit: 0

$ tail -3 .sdlc/work/232-exit-notes/build/round-1.gate.md
    ✔ Validation passed
exit: 0

$ sed -n 488,520p tests/test_factory_depth.py
(parametrised cases: the exit lines listed above, then the test body)
exit: 0
