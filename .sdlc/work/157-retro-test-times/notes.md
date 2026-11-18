# Notes

- [x] The intent's Outcome writes the report to `.sdlc/reports/junit.xml`. Built instead with a
  `mktemp` file that the command removes after printing it. `.sdlc/reports/` is ignored only by a
  `.gitignore` the script writes when it first makes a report (`sdlc.py`, beside `REPORTS`), never a
  committed one. So in a fresh worktree or clone, `junit.xml` showed as untracked, which
  `retro-commit` refuses. Run from this worktree, the command printed the XML alone: 2,877 tests
  (28 skipped), 159 s in all against retro's 600 s limit, exit 0, and `git status` unchanged. The
  slowest five are all in `tests/test_train.py`, 46–91 s each.
