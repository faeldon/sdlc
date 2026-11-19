VERDICT: PASS

Kept change done: both kill tests now wait up to 120 s, polled every 0.05 s. `test_a_killed_train_run_resumes` passed when I ran it alone, in 62 s. That is inside the new deadline, but over the 60 s the old deadline allowed, which shows the margin was needed.

## Notes
- NIT: .sdlc/work/171-factory-run-state/spec.md:42: R14 still says "a `time.monotonic()` deadline of 60 s", but the test and its sibling `_killed_at_its_gate` now use 120 s. Change R14 to 120 s, since startup here takes about 60 s. {docs S med}
- Done well: the comment on the deadline gives the reason for 120 s. The wait still ends the moment `.started` appears, so a fast machine pays nothing for the margin. The loop also stops waiting if the process exits.
- Ran: `tests/test_train.py::test_a_killed_train_run_resumes`, alone and in the foreground (passed). I did not run the gate.
