VERDICT: PASS

All three kept or required changes are in the code, and I found no state that leaves the person stuck or misled.

- **Rebasing before the stage check (kept, `board.py:606-611`):** a rebasing card now returns the rebase line before the missing-stage and problem checks, so a rebasing card with an unreadable `intent.md` gets the resolve/abort line first.
- **Problems at any stage (`board.py:612-616`):** a card with a problem reads "fix what its problems name" at every stage, and only a missing stage gets the frontmatter line. `PRECEDENCE` in `tests/test_board.py:979-1027` pins every pair of states.
- **Rebasing next line (`board.py:606-611`):** it says the rebase is stopped and names `sdlc.py resolve <id> --continue` or `--abort`. `skills/ship/conflict.md` names those same forms, so the person is told the command the skills already use.
- **Settled:** the reload notice (`board.py:729-732`) now says the board serves the code it had until the file loads. I did not re-raise it.

## Notes

**Read:** both round-3 screenshots (1280x800 and 390x844), `intent.md`, `scripts/board.py` 560-760 (`next_action`, `column`, `file_at`, `route`, `_Live.current`, `_handler`), the card renderer in `scripts/board.html` 235-316 (the flags, the `rebasing` badge, the `next` line and the stale status), the `PRECEDENCE` table and the rebasing and reload tests in `tests/test_board.py`, and `skills/ship/conflict.md`. There is no `spec.md`: this is Tier 1, so the intent's Approach stands in for it.

**States I could not see:** no screenshot shows a rebasing card, a problem at intent, spec, build or test, or the stale page. I judged them from the code and the precedence tests. The 098 card's own `next` line is cut off at the bottom of both screenshots, so I could not check it on screen.

**Smaller findings:**
- The 099 card under Needs you shows "fix what its problems name" as its next line, while its flag reads "the approver escalated it to you". The person sees both, and the next line names only the first. That is acceptable, but a card could name both steps.
- The rebasing line's "resolve its conflicts" is vague about which files. The conflicted files are in the worktree, so the person can find them, but the card does not point there.

**What the change does well:** the card's one next step now sits directly under its flags, and a rebasing card's line names the exact commands the skills use, so the person never has to guess how to finish a stopped rebase.
