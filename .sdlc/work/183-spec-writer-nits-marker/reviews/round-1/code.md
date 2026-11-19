VERDICT: PASS

The change meets the intent. Both files carry the marker rule in the wording of `skills/spec/SKILL.md:76-79`.

## Notes
- **Correctness:** `spec-writer.md` and `prompts/spec.md` both name `Nits taken in:` and say an id anywhere else retires nothing. The spec-writer is told to take in only nits the intent names or the person asks for, which matches the Constraints.
- **Tests:** the two files are added to 181's `test_every_place_that_takes_a_nit_in_names_the_marker`, so dropping the line from either now fails the test. The pinned fixtures `tests/prompts/spec.txt` and `spec-upgraded.txt` were re-recorded to match the prompt.
- **Contract:** `factory.py` is untouched. The change is wording only, and it keeps the marker form from 181.
- **Context:** the diff leaves no context doc false, so no `[context]` finding.
- **Not run:** I ran no tests and did not re-run the gate. I read the gate record at `build/round-1.gate.md`, which shows `GATE: PASS`.
- NIT: tests/test_skills.py:1939: the `# 183` comments on the two new `places` entries add nothing, since git blame already says where they came from. {style S low}
