VERDICT: PASS

No screenshot shows a mending card. The sample board has no mend stop, so I judged the mend states from `board.py`, `board.html` and `needs_of()` in `sdlc.py`. I ran nothing.

## Notes

- **Read:** both screenshots (1280×800 and 390×844), `intent.md`, `board.py` (`_mend_progress`, the "next" text), `board.html` (the flag wording), and `sdlc.py` (`mend_running`, `needs_of`, `FACTORY_STOP_NEEDS`).
- **Mend under way:** the card stays in Building. Its track shows the step labelled `mending <role>`, with the elapsed time. The flag reads "mending: …" instead of "stopped: …". The next line reads "the factory is mending the <role>: wait for it, or /sdlc-factory:build N if its session ended". That tells the person to wait, and what to do if nothing is running.
- **Mend left past its timeout:** Needs you says "stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build N if no session runs it". This is clear and gives the command.
- **Mend used up:** the stop's way becomes `rerun`, so it goes to Needs you at once with the existing wording. The intent requires this and I did not check the test for it.
- **Smaller points, none blocking:**
  - The "since" time in the needs text is cut with `[11:16]`, so it is UTC with no zone label. The board's own times are local, for example 11:55:20 AM. A person comparing the two may be off by their UTC offset. Consider adding "UTC", or showing a local time.
  - In the timeout text, "stopped: mending…" mixes two ideas. "mend unanswered" would read more plainly.
  - On the 390px layout the track and chips wrap as they do for other cards, so I saw nothing that stops the task there.
- **Done well:** the mend flag and the "next" line change wording together, and the "wait, or rerun if the session ended" wording applies to both the mending and the timed-out case. Needs you stays reserved for stops that really are the person's.
