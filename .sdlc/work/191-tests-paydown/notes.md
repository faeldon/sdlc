# Notes

## Nits answered rather than fixed

- **2026-11-18-79** (`test_board_browser.py`, about 49 s). Here the test's call takes 2.9 s and
  its setup 4.8 s (`--durations`, below in the report). `wait_for_function` returns as soon as
  the page's next poll (`POLL_MS = 2000` in `board.html`) rebuilds the cards, and `PATIENT`
  (seed 2026-11-19-45) is only a bound on a hang. The 49 s was a gate under load. A faster poll
  would mean a test-only setting in the page that no host sets, so I left it as it is.
- **2026-11-19-23** and the intent's "drops its long polls". Both kill tests already waited
  120 s, and each poll sleeps 0.05 s and ends the moment the marker file appears, so there was no
  long poll to drop: the 20–27 s each test takes is the train's own landing. The two now share
  one bound, `STARTED_WITHIN`, and its comment says why it is that long.
- **2026-11-19-29** (`.sdlc/work/173-style-paydown/checks.md`, which covers only seven named
  files). That file belongs to a change that has closed: `/sdlc:ship` reruns a change's checks
  only for that change, and close removed the folder from `main`. Editing it now would change
  nothing. The review called it "fine for this scope"; nothing to do.
- **2026-11-18-104** (the spec's four plants in one test). All four exist, beside the guards they
  test: two in `test_sdlc.py`, the literal `work/` in `test_work_folder.py`, and the second push
  in `test_skills.py`. Moving them into one test would split each guard from its own plant. The
  test's docstring now says where the other two are.
- **2026-11-19-11** (`_bare_repo` has no git identity). Every test gets one from conftest's
  autouse `git_identity`, which sets `GIT_AUTHOR_*` and `GIT_COMMITTER_*` in the environment the
  `git` subprocess inherits, so a clean CI box has it too. `repo` relies on the same fixture. The
  docstring now says so.

## Left for later

- [x] `retro.py`'s workarounds block gives `unknown` a `count` and `rows` but no `n`, though → seed: 2026-11-20-15
  `_workarounds()`'s docstring says "each count carries its `n`" (nit 2026-11-19-56). That is a
  code change, and this change is tests-only, so its test pins the row's `change` key and leaves
  `n` alone.
- [x] The intent's open question, whether this change should land after R5's split of → dropped: answered; the change doesn't touch `test_factory.py`, so it can't conflict with R5's split
  `test_factory.py`: this change doesn't touch `test_factory.py`, so the two can't conflict on it.
  The person can strike the question.
