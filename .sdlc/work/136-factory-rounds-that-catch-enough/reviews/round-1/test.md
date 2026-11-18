VERDICT: PASS

Every requirement R1–R10 has a test that would fail without it, and the suite is green.

## Notes
- **Coverage by requirement.**
  - R1: `test_a_light_round_includes_the_behaviour_reviewer`. It checks both tiers, the `REVIEWERS` ordering, and that `behaviour` is missing when only `code` ran. `test_the_behaviour_reviewer_never_deepens_a_light_run` and the existing light-list test (updated) cover the rest.
  - R2: the parametrised `test_reviewers_scale_with_the_change`. It asserts `haiku` is returned nowhere by default, and that an explicit `[models]` entry still gives `haiku`.
  - R3: `test_a_change_kept_twice_escalates_before_the_rounds_run_out`. It covers the `approve`, `exhausted` and `stuck` fields, a `READY` being refused, and a different change kept in round 2 still going to `rework`. It also covers a restart resetting the comparison.
  - R4: the prompt sentence is pinned. Each reviewer file's "Later rounds" section is checked for "word for word".
  - R5: `test_an_untestable_requirement_escalates_after_its_round`. It checks `verify` comes first, then `approve` with `exhausted` true. An all-PASS round also reaches `approve` with `exhausted` true and `untestable` listed.
  - R7: `test_an_early_escalation_names_its_reason_to_the_approver`. It covers the `stuck` and `untestable` prompts and checks a plain run gets neither.
  - R8: `test_retro_counts_a_landing_catch_once_per_change`. It covers a double catch counted once, a build-round finding, a landing nit, a finding answered wrong, and a hand-reviewed change that no agent looked at.
  - R9: `test_a_host_s_own_depth_and_models_are_kept`, at both tiers.
  - R10: the build-question test is updated to expect `code and behaviour`.
- **No `checks.md`** exists for this change, so there are no acceptance checks to judge.
- NIT: tests/test_factory.py:1676: R6's README table of changes 124, 125, 129 and 131 has no test. It cannot be checked mechanically, so a person should confirm it against each change's `Close` commit. {tests S low}
- NIT: tests/test_factory.py:1358: the R3 test has no case where round N-1 has no `verified.md`, which the code handles. A one-line fixture would pin that branch. {tests S low}
- **Test command run:** `uv run --group dev pytest -q -n auto`. Result: 2414 passed, 13 skipped, no failures. I did not run `./check.sh`'s ruff or plugin-validate steps.
