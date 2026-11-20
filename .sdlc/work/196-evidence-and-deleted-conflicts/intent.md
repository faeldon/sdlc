---
id: 196
slug: evidence-and-deleted-conflicts
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T00:46Z
updated: 2026-11-20
shipped: 2026-11-20
idea:
depends_on:
fixes: [2026-11-20-17, 2026-11-20-14]
serves: [O3, O6]
---

# 196 — The factory reads evidence that prints headings, and resolves a deleted file's conflict

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two factory bugs stopped wave 5 on 2026-11-20, each on work that was sound.

Bug 2026-11-20-17: `read_evidence()` in `plugins/factory/scripts/factory.py` ends a reply's
`## Evidence` section at the first line starting with `## `. A read that prints Markdown, such as
a report or a doc whose first output line is a `## ` heading, therefore ends the section on its
own output. The read counts as having printed nothing, and is flagged "has no `exit:` line",
though `is_read()` accepts it. 189-retro-insights's builder ran
`sed -n '/^## Insights/,/^## Speed/p' /tmp/rep189.md`, whose output begins `## Insights`. Its one
mend ended the same way, so the run stopped.

Bug 2026-11-20-14: when a train stacks a change that deletes a file an earlier change in the train
edited (a modify/delete conflict, `UD`/`DU`), the landing's `resolve` step raises
`FileNotFoundError` on the deleted path before the resolver agent starts. The loop stops with the
change mid-rebase. 193 added tests to `tests/test_factory.py` and 194 deleted that file to split
it, so landing 193 then 194 stopped at `resolve 194`. 194 still can't land through the factory.

Two nits sit on the same code: 2026-11-20-8 (`by_alts` is built from every ledger entry with
options) and 2026-11-20-9 (`len(name) >= 5` counts the leading `--`, while its comment says three
characters after it).

## Outcome

- A read whose output contains `## ` lines owes no `exit:` line: only a heading after the
  command's output ends the Evidence section. A test fails if 189's report shape is flagged.
- A modify/delete conflict reaches the resolver. It is told which side deleted the file, what the
  other side changed, and where the deleted file's content went, and its answer is staged like any
  other. A test fails if a train whose second change deletes a file the first edited stops at
  `resolve` instead of handing it to the resolver.
- 189 reruns with `/sdlc-factory:build 189`, and 194 lands with `/sdlc-factory:land 194`, both
  without a hand step.
- The two nits are fixed.
- **Moves O3:** a factory run stops only for what needs the person, never on its own record of
  sound work.
- **Moves O6:** a train lands a change that moves or splits files, unattended.

## Affected

- `plugins/factory/scripts/factory.py` (`read_evidence()`, the `train-resolve` task's setup,
  `cmd_decisions()`'s `by_alts`).
- `plugins/factory/scripts/landing.py` (sensitive: the resolve step, `GREP_FOLLOWS_LONG`).
- `plugins/factory/prompts/` for the resolver's modify/delete instructions, and its pinned prompt
  fixture.
- `tests/test_factory_*.py` and `tests/test_train.py`.
- **What reads it:** every factory build's evidence check, and every landing train's resolve step.

## Constraints

- The resolver edits only the files the conflict names (`resolve --continue` checks this), and no
  agent commits.
- A resolved conflict is still reviewed again at the run's depth.
- Evidence stays strict: a command that isn't a read still owes its `exit:`.
- `factory_records.py`'s pinned copies stay in step.

## Approach

In `read_evidence()`, end the section only at a `## ` heading that follows a command's `exit:` or
comes after a blank line outside any command's output, so a read's printed headings stay its
output. In the resolve setup, list each conflicted path with its git status (`git status
--porcelain`'s `UD`/`DU`/`AU`/`UA`). For a deleted side, give the resolver the surviving side's
text from the index (`git show :2:<path>` or `:3:<path>`) instead of reading the work tree, and let
`resolve --continue` accept a staged deletion. Tighten `by_alts` and fix the comment.

Nits taken in: 2026-11-20-8, 2026-11-20-9

## Open questions

- How does the resolver say where a deleted file's content now lives: its own judgment from the
  other change's diff, or a rename git detected?
