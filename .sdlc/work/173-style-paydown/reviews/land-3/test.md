VERDICT: PASS

This change rewraps prose and adds two comments. It changes no behaviour, so no new test is needed, and the plan says so. I read the three checks without running them.

## Notes
- **Gate:** `build/land-3.gate.md` is `GATE: PASS` (`./check.sh`, exit 0), with `3156 passed, 29 skipped in 137.88s`. The plan expected 28 skips from the board's pairs of states plus the Chromium-dependent `browser` tests, so 29 is plausible. I did not run any test myself.
- **Check 1, no prose line past 100 columns:**
  - It would fail if a line were rewrapped back out, and it leaves the tree unchanged.
  - It skips fenced blocks, table rows and `description:` lines, which can't wrap.
  - I expect it to pass. The `check.yml` and `check.sh` hunks I read all fit within 100 columns.
- **Check 2, `check.sh` says why the summary counts skips:**
  - It greps for the two phrases the new comment holds, `pytest -rs` names each reason and `skipped` count is expected.
  - Both are in the diff, so I expect it to pass.
  - It could not pass without the comment.
- **Check 3, `heat()` says how a file added after the boundary counts:**
  - It greps for `A file added after` followed by `since` has no boundary lines.
  - The comment's wording is split across the diff's two lines but starts with that phrase, so I expect it to pass.
- **Well covered:** the full suite reads these files in many substring checks, and the green gate shows none of them broke.
- **Commands:** none run by me. I read the gate record only.
