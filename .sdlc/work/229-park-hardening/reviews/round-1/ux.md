VERDICT: PASS

## Notes
- **Read:** both screenshots (1280x800 and 390x844), and `scripts/board.py` (the park read and the gate-track label) and `scripts/sdlc.py` (`park_line`, `_park_deadline_at`, the `needs_of` park branch). I did not read `factory.py` or the tests.
- **Screenshots:** neither shows a parked card. They show the board's other cards. At 390px the columns collapse to a single list and the Needs You column leads, so the task still works on a phone.
- **Parked states I couldn't see:** I judged them from the code.
  - A park inside its deadline puts the gate track on a "parked" step. Its label is `park_line`: "parked on X, held by Y; retry …, deadline …". It names the resource, the holder, the next retry and the cutoff.
  - A park past its deadline becomes a need: "parked past its deadline: free X". The next step reads "free what it waits on and rerun". That says what happened and what to do.
- **Consistency:** the board and `status` use the same `park_line`, so the wording is identical in both. The deadline is read from the base branch's config in both, so they agree with the run.
- **Smaller finding:** `park_line` prints the raw deadline and retry values. If they are ISO timestamps, a relative form such as "in 12 min" would be easier to read. This is minor.
- **Done well:** a park is read only while the change is at `build`. A park left over from earlier can't mislead the card.
