VERDICT: PASS

The two doc additions the person asked for are in `docs/REFERENCE.md`, and they match what the code prints.

## Notes
- **What I read:** the 1280x800 screenshot, the `REFERENCE.md` passages, the card flag logic in `board.html`, and the mend strings in `board.py` and `sdlc.py`. I did not open the 390x844 screenshot. I did not review the rest of the diff. This round's fix is docs only.
- **Screenshot:** it shows no mending card, so the `mending` flag and the timed-out mend card are unconfirmed from the screenshot. From `board.html`, a mend stop gets a `mending:` flag prefix instead of `stopped:`.
- **Lines 655–661:** these now say a stop being mended reads `mending` with no `⚠` lines. They give the `→ the factory is mending the <role>: wait for it` line and say the card stays off Needs you until the mend replies or times out. That matches `sdlc.py:11003`, the status output.
- **Lines 677–678:** these add the timed-out text `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it` to the Needs-you list. That matches `sdlc.py:5211`.
- **Formatting:** the parenthetical at line 678 runs well past the other lines' wrapping width. It is cosmetic, so reflow it if you touch that paragraph again.
- **Board wording:** the board's own next-step line (`board.py:748`) reads "wait for it, or …", longer than the status line the docs quote. The docs describe the status output, so I'm not raising it.
- **Done well:** the board shows a stop that is being mended as `mending:` with a "wait for it" step, so the person is not told to act on something the factory is already handling. The timed-out case states what to run.
