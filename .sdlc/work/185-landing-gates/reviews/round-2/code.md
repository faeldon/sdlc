VERDICT: PASS

The change kept last round was made. `checks_clearance()` in `landing.py` now returns `step: "accept"` with "checks.md is gone, so there is nothing to judge" when `checks_sha()` is `None`. That check runs before the approver's judgement. So `_land_task` refuses, and `factory.py:4431` is never reached with `None`. `test_land_checks_refuses_outside_a_changed_train_change` now unlinks `checks.md` after the yes. It asserts a refusal containing "checks.md is gone", no session started, and no `land-checks` record written.

## Notes
- Done well: the removed-file case is handled in the one function that decides clearance, not patched at the call site. The test pins both the refusal and that no agent session ran.
- Ran: the named test `test_land_checks_refuses_outside_a_changed_train_change`, which passed. I read the gate record and did not run the whole suite.
