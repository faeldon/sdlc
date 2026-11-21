VERDICT: PASS

## Notes
- checks.md has one check, "Dependabot proposes bumps to the pinned actions". I expect it to pass. `.github/dependabot.yml` has `version: 2`, `package-ecosystem: github-actions` and `directory: /`, which are the three greps. I did not run it.
- Both actions in `check.yml` (4 `uses:` lines across the 2 jobs) are pinned to a 40-hex SHA with a `# vX.Y.Z` comment, as the Outcome requires.
- `tests/test_ci.py` reads `.yml` and `.yaml` workflows. Its 3 tests pass: the check refuses tag, branch and short-SHA pins and a SHA with no version comment, the `.yml`/`.yaml` file filter, and the real workflows.
- The round 2 gate record is `GATE: PASS`.
- I did not check that each SHA is the commit its tag points at. That needs the network, and the intent leaves CI's run to after ship.

## Evidence
$ git status --short
 M .github/workflows/check.yml
?? .github/dependabot.yml
?? .sdlc/work/221-ci-pinned-shas/
?? tests/test_ci.py
exit: 0

$ grep -n uses .github/workflows/*
.github/workflows/check.yml:24:      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
.github/workflows/check.yml:25:      - uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0
.github/workflows/check.yml:39:      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
.github/workflows/check.yml:40:      - uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0
exit: 0

$ cat .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
exit: 0

$ uv run --group dev pytest tests/test_ci.py -q
...                                                                      [100%]
3 passed in 33.32s
exit: 0

$ head -5 .sdlc/work/221-ci-pinned-shas/build/round-2.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ tail -3 .sdlc/work/221-ci-pinned-shas/build/round-2.gate.md
    The directory also runs a safety scan and a policy review that this command does not.
    
    ✔ Validation passed
exit: 0
