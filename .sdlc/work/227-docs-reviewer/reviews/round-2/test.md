VERDICT: PASS

The kept change from round 1 is done. `skills/ship/docs.md:28` now reads "refuses, when the change has a `findings.md`, a diff this applies to whose note says neither". That matches `cmd_ship` at sdlc.py:4187, which asks for the `Docs review:` line only when `found["exists"]` is true. `docs/REFERENCE.md:161-162` says the same, that the docs pass is "asked of a `findings.md` that exists, never of a change with none". `skills/ship/SKILL.md` and `plugins/factory/README.md` make no unconditional claim about the refusal. A test pins the conditional: `tests/test_findings.py:700` has "never of a change with none, which predates the file".

## Notes
- The gate's record, `build/round-2.gate.md`, reads `GATE: PASS` (`./check.sh`, exit 0, 615 s, plugin validation passed). I did not run the suite myself.
- `tests/test_factory_docs.py` covers the rules for joining a run, the keys `REFERENCE.md` names, the factory README's reviewer rows, and the build skill. These are the requirements I mapped. I did not re-review anything the round-1 pass already accepted.
- `decisions.md` still holds D1 open for the person, as the prompt says. If it is answered the other way, `ship/docs.md:28` and `REFERENCE.md:161` must change with it.
- `checks.md` does not exist, so there is no check to judge.
- I ran no named tests.
