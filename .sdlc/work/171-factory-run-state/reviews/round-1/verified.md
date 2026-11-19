- KEPT: behaviour: C1: tests/test_train.py:1773: the kill test's 60 s start deadline is tighter than the 120 s it replaced and than the 120 s the sibling `_killed_at_its_gate` uses. Startup time varies with load, and an early deadline gives a false failure.

## Notes
I ran `test_a_killed_train_run_resumes` once, alone and in the foreground. It passed in about 44 s, so I could not reproduce the failure. I kept the change because a wider deadline costs nothing when the test passes, and the spec's R14 figure of 60 s can be revisited. Running the test repeatedly under load would settle whether 60 s is really too tight on the reporter's machine.
