---
id: 215
slug: evidence-exits
tier: 1
impact: patch
stage: shipped
created: 2026-11-21
opened: 2026-11-21T11:27Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
fixes: [2026-11-21-35]
serves: [O6]
origin: self
---

# 215 — Agents' evidence carries an exit: on every command

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From bug 2026-11-21-35: three factory runs on 2026-11-21 stopped on a missing `exit:` in a
`## Evidence` section and needed a mend: 212's and 210's behaviour checks, which cited
`cat .sdlc/work/NNN-slug/build/round-1.gate.md (head)`, and 214's builder, which cited
`gh run view <id> --log-failed | grep FAILED` and `uv run … sdlc.py vet`. Each costs a mend run,
and a second miss in the same round stops the change for the person: under autopilot
(2026-11-21-32) that is a change stalled overnight.

The builder's, the behaviour reviewer's and the resolver's prompts (`plugins/factory/agents/
builder.md`, `reviewer-behaviour.md`, `resolver.md`) say a command needs no `exit:` "if it is a read
that shows its output", but none says what a read is. `is_read()` in
`plugins/factory/scripts/factory.py` is strict on purpose: a closed allowlist of programs in every
stage of a pipe, nothing after the command, so `gh`, `uv run` and a trailing `(head)` make a
command a non-read. `reviewer-behaviour.md` adds to it by telling the reviewer to cite the gate
record as `$ cat …gate.md` "which a read owes no `exit:`".

## Outcome

- Every agent that ends with `## Evidence` is told to write `exit: <n>` after every command, reads
  included, so whether the script counts a command as a read never decides whether a reply is
  read. `is_read()` stays as strict as it is.
- `reviewer-behaviour.md`'s gate-record citation shows its `exit:`.
- A test fails if any agent prompt in `plugins/factory/agents/` still says a read "owes no
  `exit:`" or that `exit:` may be left off, and a test feeds `read_evidence()` the three commands
  from today's stops with their `exit:` lines and fails if any is flagged.
- **Moves O6:** a factory run stops for a missing `exit:` less often, so fewer mends, and no
  change stalls for want of a line its agent could have written.

## Affected

- **Area:** the factory's agent prompts and the evidence reader.
- **Files & components:** `plugins/factory/agents/builder.md`, `reviewer-behaviour.md`,
  `resolver.md`, and any other agent prompt with the same wording; the mend and land-mend task
  text in `plugins/factory/scripts/factory.py` if it repeats the exemption; the factory's evidence
  tests.
- **Downstream:** every factory run's builder, behaviour check and resolver reply, and
  `verdicts`, which reads them.
- **Contracts:** `read_evidence()` and `is_read()` (AGENTS.md: every command with its `exit:` but a
  read that shows its output, which only the script judges); `test_no_agent_but_the_builder_runs_checks`.

## Constraints

- The script's rule doesn't loosen: a reply missing an `exit:` on a non-read is still a stop.
- The read exemption may stay in the script for older replies; only the prompts stop relying on it.

## Open questions

- Should AGENTS.md's wording ("every command with its `exit:` but a read that shows its output")
  change too, or does it stay as the script's rule while the prompts ask for more?
- Do the reviewer prompts other than behaviour (code, security, test) end with an `## Evidence`
  the script reads, and so need the same line?

## Approach

Change each agent prompt that ends with `## Evidence` to ask for `exit:` on every command, reads
included, and fix the behaviour reviewer's gate-record example to show its `exit:`. Add a test
over `plugins/factory/agents/*.md` that fails on the old exemption's wording, and a
`read_evidence()` test on today's three commands with their exits. Check the mend task text in
`factory.py` says the same. Take in the two nits on `factory.py` while there. Three prompts, one
script, tests.

Nits taken in: 2026-11-20-61
