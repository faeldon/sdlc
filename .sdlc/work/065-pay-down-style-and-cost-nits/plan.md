---
id: 065
slug: pay-down-style-and-cost-nits
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 065 — Pay down the style and cost nits · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `tests/test_defaults.py`: `RECORD_CLEARS` becomes one set literal with the same ten members, on
  two lines under `}  # fmt: skip`, the idiom `scripts/sdlc.py` uses (`landing_reach()`'s
  `found`).
- `.github/workflows/check.yml`: `push:` gets `branches: ['**']`, so a tag push starts no run, and
  the header comment says it runs on branch pushes.
- `tests/test_skills.py`: `test_ci_runs_once_per_publish_not_again_for_the_tag`, beside
  `test_the_gate_and_ci_never_run_the_skills_cases`.

## Work order

1. Rewrite `RECORD_CLEARS` and run `tests/test_defaults.py`.
2. Filter the workflow's push trigger, fix its header comment, and add the test that pins it. The
   test reads the file as text, since PyYAML reads the `on` key as `True`.
3. Run `./check.sh`.

## Tests

- 2026-10-24-8: the drift tests that read `RECORD_CLEARS` pass unchanged. The ten members are the
  same set.
- 2026-11-04-13: `test_ci_runs_once_per_publish_not_again_for_the_tag` asserts that `push:` carries
  `branches:` and no `tags:`, and that `workflow_dispatch:` stays. Manual: after the next
  `/sdlc:publish`, `gh run list --workflow check.yml -L 3` shows one run for the release commit.

## Rollback

`git revert <sha>`. Nothing outside the repo changes. A reverted workflow runs on tags again from
the next push.
