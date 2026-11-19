# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Nit 2026-11-18-68, answered (R16)

The redundant `RUN_STEPS["eject"]` lookup the nit names is gone: `_run_plan()` in `landing.py`
reads `RUN_STEPS[nxt]` once, after the `RUN_EJECTS` check, with no lookup of `"eject"` of its
own. `RUN_STOPS` is not unused: `test_the_train_driver_takes_every_step_a_reading_names` reads it
as the steps that are always the person's (with `RUN_STEPS` and `done` covering every
`TRAIN_STEPS`), and `test_the_loop_runs_only_its_named_commands` pins it to `{"accept", "stop"}`.
No code change; the nit is retired by the spec naming it.

## `decision_preamble` moved too (R1, R3)

The spec's list named eight functions, but `decision_preamble()` is also called only by
`loop_state()`, so `test_the_line_between_script_and_module_holds[run_state]` (R3's rule, which R1
says decides the list) asked for it to move. It did, with `RUN_STATE_NAMES` naming it: raised as
a default decision in the build report.

## The kill test at the gate, on POSIX too (R17)

The Windows test's body is a helper, `_killed_at_its_gate()`, that
`test_a_train_run_killed_at_its_gate_resumes` also runs on POSIX with `start_new_session` and
`killpg`, so the path it takes (block at the tip's gate, kill, write the stacked changes'
behaviour replies, run again) is shown here and on CI's Linux job, not only on Windows.
