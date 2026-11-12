---
id: 051
slug: test-reviewer-reads-checks
kind: plan
created: 2026-11-12
updated: 2026-11-12
---

# 051 — The test reviewer reads checks.md and never runs it · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/agents/reviewer-test.md`: the "How each test could fail" bullet reads each
  `checks.md` section and never runs it, with the behaviour check's reason; `## Notes` names each
  check and what it expects of it.
- `plugins/factory/agents/verifier.md`: settles a claim about a check by reading it, never running
  its commands.
- `plugins/factory/README.md`: the agent table's `reviewer-test` row says it reads `checks.md` and
  never runs it.
- `tests/test_skills.py`: one test over the factory's agents with `Bash` but the builder.
- `.sdlc/work/051-test-reviewer-reads-checks/intent.md`: both open questions struck.

## Work order

1. Add the test; it fails on today's `reviewer-test.md` and `verifier.md`.
2. Edit the two agents and the README row; the test passes.
3. Strike the intent's open questions; `./check.sh`.

## Tests

`test_no_agent_but_the_builder_runs_checks`: for each agent in `AGENT_TOOLS` with `Bash` but
`builder`, its text never says "run each section"; `reviewer-test`, `reviewer-behaviour` and
`verifier` each say they never run `checks.md`. It fails on `main`'s `reviewer-test.md`.

## Rollback

`git revert <sha>`. Prompt text and a test only: nothing outside the repo, no host data.
