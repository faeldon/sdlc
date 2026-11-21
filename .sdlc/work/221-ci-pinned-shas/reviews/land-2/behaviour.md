VERDICT: PASS

The workflows pin both actions to full SHAs with version comments. `dependabot.yml` is added, and the three tests in `tests/test_ci.py` pass. The gate record ends in `Validation passed`. I did not check the pinned SHAs against the upstream tags (that needs the network), and CI's run on the pushed commit is outside what I can see.

## Notes
- The spec names no end-to-end command, so I used the closest path the change's own tests exercise: `tests/test_ci.py`. I ran only that file and did not rerun the suite.
- The Dependabot check in `checks.md` (`## Dependabot proposes bumps to the pinned actions`) should pass. It looks for `version: 2$`, `package-ecosystem: github-actions` and `directory: /$`, and the file has all three lines. I did not run it.
- Decision D1 (are the pins and weekly Dependabot PRs wanted) is answered `seen`, so it is settled.

## Evidence
$ cat .sdlc/work/221-ci-pinned-shas/build/round-2.gate.md | tail -8
      ❯ .claude-plugin/plugin.json icon: No icon (ICON_MISSING). ...
    ✔ Validation passed
exit: 0

$ git diff 10562a3cffaff7a8d940a6b99c0b0eee1e00e975...HEAD -- .github
(`dependabot.yml` added with `version: 2`, `package-ecosystem: github-actions`, `directory: /`, a weekly schedule. `check.yml`'s four `uses:` lines now name `actions/checkout@11d5960a…` `# v4.4.0` and `astral-sh/setup-uv@d0cc045d…` `# v6.8.0`.)
exit: 0

$ uv run --group dev pytest tests/test_ci.py -q
...  [100%]
3 passed in 17.68s
exit: 0

$ cat .sdlc/work/221-ci-pinned-shas/checks.md .sdlc/work/221-ci-pinned-shas/decisions.md
(read; the contents are summarised in Notes)
exit: 0
