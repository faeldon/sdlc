VERDICT: CHANGES

- CHANGE: scripts/board.py:601-605: the stage-missing check runs before the rebasing check, so a rebasing change whose `intent.md` won't read gets "fix intent.md's frontmatter" and no word that its rebase is stopped. That is the case the comment at 603-604 names ("its conflicted files may be what won't read"), and a conflict in `intent.md` is exactly how it happens. Move the `entry.get("rebasing")` branch above the `problems and stage is None` check so every rebasing card gets the resolve/abort line first.

## Notes

**Read:** both round-2 screenshots (1280x800 and 390x844), `intent.md` (Tier 1, so its Approach stands in for a spec; there is no `spec.md`), `scripts/board.py` 560-820 (`next_action`, `column`, `_Live.current`, `route`, `serve`, `cmd_board`), `scripts/board.html` (the status line and the card's `flags`, `rebasing` badge and `next` rendering), the REFERENCE.md rebasing passage (489-493), and `skills/ship/conflict.md`, which names `sdlc.py resolve <NNN> --continue` and `--abort`.

**Kept changes, checked:**
- Reload message: the code now says "`board.py` changed but won't load (…): the board serves the code it had until the file loads". The page status shows it as `stale · …` in the red `down` style. No restart is asked for. This is fixed.
- Problems at any stage: `next_action()` returns "fix what its problems name" before the close, the stopped, and the stage steps. The 099 card at 1280 reads "next: fix what its problems name" under its red flags. Fixed, except for the frontmatter ordering above.
- Rebasing: the card keeps its rebasing badge and its next line names `resolve --continue` or `--abort`, which is the command the skills name. Only the stage-missing ordering escapes it, as above.

**Not seen:** a loading state (the page renders only after its first fetch), a board with no open changes at all, and a `board.py` that fails at first load (the server never starts). I judged the reload and stale paths from the code and the two screenshots, which show the live state only.

**Notes:**
- A card whose `stopped` record is set and which also has `problems` shows "fix what its problems name", and its own `stopped.next` is hidden. The 099 card shows this. Check that the stopped record's next is not more specific than "fix what its problems name" before it is hidden.
- `test_a_card_with_a_problem_never_names_close` only checks that the card does not name close. Nothing pins the new "fix what its problems name" text at intent, spec, build or test, so a later edit could drop it unseen.
- PREEXISTING: at 390 wide the columns stack in order, so Needs you (the column a person must act on) sits below Plan, Design and Build, about five cards down. A phone user has to scroll past all of it to find the card that needs them. Filed for later, not this change's rework.
- PREEXISTING: an empty column (DESIGN, TEST, READY TO SHIP, READY TO CLOSE in the screenshots) shows a bare "—". It does not say the column is empty or that nothing is waiting there.
- The rebasing line names the change and the command, and says "in its worktree". That tells the person where to run it. Its length wraps cleanly at 390 wide.
