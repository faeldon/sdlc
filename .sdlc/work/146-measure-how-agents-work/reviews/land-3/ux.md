VERDICT: PASS

## Notes

I read both screenshots, `scripts/board.html` (landmarks, buttons and the drawer's ARIA), and the changed-paths list. I could not open `decisions.md`; it isn't in the change folder, so I treated no decisions as answered. I did not read the Python diffs, so I can't judge empty, loading or error states from the code. Of those states the screenshots show only the factory error cards.

- **Task and states:** The board is the person's view of this change. Each card names its state and its next step. Examples are 006 "stopped: rerun to ask an agent again" and 007 "decide D1 in the session running…". The error and needs-you cards each say what happened and what to do now, not a raw error.
- **Words:** "verifier: kept 1 · dropped 0" is clear. The "was ESCALATE" and "was READY" tags are slightly terse but understandable.
- **Reach:** The drawer has `role=dialog` and `aria-modal`, a Tab cycle inside it, and labelled Close and Raw buttons, with Raw using `aria-pressed`. The file list uses `aria-current`. Scrollable code and table regions are focusable and labelled. The columns are labelled sections.
- **Phone width (390px):** The columns stack, the needs-you column comes first, and each card stays readable.
- **Small point:** At 390px, a stacked card such as 008 shows the B1 and B2 rows of chips, which makes it tall. This doesn't block the task.
- **Done well:** The "next:" line on every card, the verifier-kept counts shown beside each round, and the red "needs you" text at the top of the stack on a phone.
