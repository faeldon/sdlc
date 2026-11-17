VERDICT: PASS

The end-to-end path does what the spec says, and the change has no `checks.md`, so there was nothing to read there.

## Notes
- **`checks.md`:** none exists in the change folder, so there are no acceptance checks to read.
- **End-to-end path (R13):** `tests/test_land.py` passes, 26 tests. It includes the batch of three changes landing through `factory.py` alone.
- **Registered commands (R4, R5):** `factory.py accept <NNN>` and `factory.py cases <NNN>` are both registered.
- **No prompt-free grant (R6):** the land skill's `allowed-tools` lists no `accept` or `cases` rule. `check.sh` and CI don't mention either command. The skill text names them only as steps behind the harness's prompt.
- **Skills and factory tests:** `tests/test_skills.py` and `tests/test_factory.py` pass, 503 tests together.
- **Not run:** the full gate, which the script ran before this review. Its record, `build/round-1.gate.md`, says `GATE: PASS`. I did not run `run-cases`, because it is a paid run and `_cases_report()` is unavailable outside this repo.
- **Not run:** `land` against a real change. The tests cover it with a scratch repo.

## Evidence
$ head -5 .sdlc/work/103-landing-does-what-ship-does/build/round-1.gate.md
GATE: PASS
## Attempt 1
Verdict: PASS
exit: 0

$ uv run --group dev pytest tests/test_land.py -q -n auto
26 passed in 7.38s
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py accept --help
positional arguments:
  id
options:
  -h, --help  show this help message and exit
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py cases --help
positional arguments:
  id
options:
  -h, --help  show this help message and exit
exit: 0

$ grep -n "factory.py accept\|factory.py cases" check.sh .github/workflows/*.yml plugins/factory/skills/*/SKILL.md
plugins/factory/skills/land/SKILL.md:107: (accept step)
plugins/factory/skills/land/SKILL.md:110: (cases step)
plugins/factory/skills/land/SKILL.md:218: (behind the harness's prompt)
exit: 0

$ grep -n "allowed-tools" -A12 plugins/factory/skills/land/SKILL.md
lists Read, AskUserQuestion and factory.py config, sdlc-path, land-check, land, resolve, agent, gate and land-verdicts rules; no accept or cases rule
exit: 0

$ uv run --group dev pytest tests/test_skills.py tests/test_factory.py -q -n auto
503 passed in 4.23s
exit: 0
