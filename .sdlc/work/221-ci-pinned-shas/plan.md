# 221 — Plan

> Tier 1 with three files, so a short plan: what the build changes, in what order, and what proves it.

## Files to change

- `tests/test_ci.py` (new): reads every `.github/workflows/*.yml` and `*.yaml` (`workflow_files()`,
  round 2: GitHub runs both) and refuses a `uses:` not pinned
  to a 40-hex commit SHA with a trailing `# v<version>` comment. Plain text reads with a regex, no
  YAML parser, as the other workflow tests in `tests/test_skills.py` read the file.
- `.github/workflows/check.yml`: each `uses:` pinned to the commit its current tag names, resolved
  with `gh api`: `actions/checkout@v4` → `11d5960a…` (v4.4.0, the commit `v4` points at);
  `astral-sh/setup-uv@v6` → `d0cc045d…` (v6.8.0, the commit the annotated `v6` tag peels to).
- `.github/dependabot.yml` (new): the `github-actions` ecosystem, weekly, so the pins get bumps.

## Work order

1. The test, run against the current tag pins: red, naming both `uses:` lines.
2. Pin `check.yml`: the test green.
3. `dependabot.yml`, proved by an acceptance check in `checks.md` (only a revert removes it).

## Tests

- `tests/test_ci.py::test_every_action_is_pinned_to_a_commit`: the outcome's pinned SHAs and a
  failing test on a tag or branch pin. Marked `portable`: it reads text only.
- `tests/test_ci.py::test_the_check_refuses_a_tag_or_branch_pin`: the rule itself, on inline
  examples, so the test is seen refusing a tag, a branch and a short SHA.
- `tests/test_ci.py::test_a_yaml_workflow_is_read_as_well` (round 2): a `.yaml` workflow is
  checked too, a non-workflow file is not.
- `checks.md`: Dependabot watches `github-actions`.
- Outcome 4 (rewritten in round 2): the pins, `tests/test_ci.py` and the gate. CI's run on the
  pushed commit is a post-ship observation, not proved here.

## Rollback

`git revert` undoes everything; nothing is written outside the repo. Dependabot may have opened
bump PRs by then, which are closed by hand.
