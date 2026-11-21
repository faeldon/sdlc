VERDICT: PASS

The change does what the intent says. Each `uses:` in `.github/workflows/check.yml` is pinned to a 40-character SHA with a version comment. The new test passes, and the SHAs match what the current tags pointed at.

## Notes
- **Pins match the old tags.** `v4` resolves to `11d5960a…`, the same commit as `v4.4.0`. `v6` is an annotated tag whose commit (`^{}`) is `d0cc045d…`, the same commit as `v6.8.0`. CI's behaviour therefore doesn't change, as the intent's Constraints require.
- **The new test:** `tests/test_ci.py` passes (2 tests: the real workflows, and a case where it refuses tag and branch pins).
- **Dependabot:** `.github/dependabot.yml` exists with the `github-actions` ecosystem, directory `/` and a weekly schedule.
- **Gate:** the round-1 record shows PASS and Exit 0. I did not rerun the suite.
- **Check "Dependabot proposes bumps to the pinned actions":** read, not run. I expect it to pass. The file has `version: 2`, `package-ecosystem: github-actions` and `directory: /`, each on its own line, as the three greps need.
- **CI on the commit:** not run here. The first push will show it.

## Evidence
$ git status --short
 M .github/workflows/check.yml
?? .github/dependabot.yml
?? .sdlc/work/221-ci-pinned-shas/
?? tests/test_ci.py
exit: 0

$ grep -n 'uses:' .github/workflows/check.yml
24:      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
25:      - uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0
39:      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
40:      - uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0
exit: 0

$ cat .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
exit: 0

$ git ls-remote https://github.com/actions/checkout refs/tags/v4.4.0 refs/tags/v4
11d5960a326750d5838078e36cf38b85af677262	refs/tags/v4.4.0
11d5960a326750d5838078e36cf38b85af677262	refs/tags/v4
exit: 0

$ git ls-remote https://github.com/astral-sh/setup-uv refs/tags/v6.8.0 'refs/tags/v6^{}'
d0cc045d04ccac9d8b7881df0226f9e82c39688e	refs/tags/v6.8.0
d0cc045d04ccac9d8b7881df0226f9e82c39688e	refs/tags/v6^{}
exit: 0

$ uv run --group dev pytest tests/test_ci.py -q
..                                                                       [100%]
2 passed in 0.01s
exit: 0

$ head -8 .sdlc/work/221-ci-pinned-shas/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: a6879e5cb9055a27
Exit: 0
exit: 0
