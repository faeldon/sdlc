VERDICT: PASS

The change does what the intent asks and the tests prove it. I found nothing that needs rework.

- **Parser:** `EXIT_RE` now accepts a space-separated note after the code, so `exit: 2 (note)` and `exit: 0 # ok` count as exits. `exit: nonzero`, `exit: not run` and `exit: 2x` still have no code and still fail.
- **Prompts:** the behaviour reviewer and the builder both say a command that ran records its real code (`; echo "exit: $?"`). Both also say a hook-refused command is no `$ ` line. The reviewer lists it under `## Notes` and the builder says so in its report.
- **Decisions:** D1 and D2 are the builder's open defaults. I reviewed against them and agree with both.
- **Context docs:** nothing in the context docs became false.

## Notes
- NIT: plugins/factory/agents/resolver.md:58: the resolver's *Evidence* paragraph has the same `exit: <n>` wording and no hook-refusal sentence, so it will meet the same stop {docs S med}
- Done well: the plan narrows the regex to a space-separated note, so `exit: 2x` and `exit: 2.5` aren't read as code 2. The parametrized test covers that boundary.
- Ran: `pytest tests/test_factory_depth.py -k "exit_with_a_note or evidence"` (14 passed). I didn't run the gate; its record at `build/round-1.gate.md` shows `claude plugin validate --strict` passing.
