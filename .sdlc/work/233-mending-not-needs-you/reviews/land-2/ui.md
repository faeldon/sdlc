VERDICT: PASS

The two requested additions are in `docs/REFERENCE.md`, and both screenshots render cleanly.

## Notes
- I read `index-1280x800.png` and `index-390x844.png`. Neither shows a mending card. The board content in both is the existing Needs-you, Building and Landing cards. I could not confirm the mending look (the `mending` label and the `→ the factory is mending the <role>` line) from them.
- `docs/REFERENCE.md` lines 658–661: the mend text is there. A mending stop reads `mending`, has no `⚠` lines, shows `→ the factory is mending the <role>: wait for it`, and stays off Needs you until the mend replies or times out.
- `docs/REFERENCE.md` lines 677–678: the timed-out text, `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it`, is in the Needs-you list.
- Minor: line 678 runs far past the wrapped width of the lines around it, so the paragraph reflows unevenly. Rewrap it to match.
- At 1280×800 the columns line up, and the red Needs-you cards stand out. At 390×844 the cards stack into one column with no sideways overflow, and the monospace `next:` lines wrap inside their cards.
- I did not review the Python and HTML changes (`board.html`, `board.py`, `factory.py`, `sdlc.py` and the other changed paths) for styling. I only checked the screenshots and the docs.
