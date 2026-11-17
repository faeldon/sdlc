---
id: 094
slug: inbox-labels-resolve-skip
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-17, 2026-11-17-18]
serves: none
---

# 094 — inbox-commit names only the entries that changed, resolve skips a commit a merge empties, and a reviewer's preamble is mended, not a stop

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`inbox-commit` names entries as updated when their text didn't change (bug 2026-11-17-17).
Retiring 2026-11-17-7 on 2026-11-17 committed as "Retire 2026-11-17-7; Update 2026-11-17-10",
though the diff only deleted 17-7's ten lines. `parse_entries()` (`scripts/sdlc.py`) reads an
`After:` id as the title of the entry it names while that entry is in the file, and as the bare id
once it's gone. `cmd_inbox_commit()` compares the parsed entries, so an entry whose `After:` names
the retired one reads as changed. The subject is history: anyone reading `git log` for when an
entry changed, retro or a person, is told 17-10 was edited when it wasn't.

Nit 2026-11-17-11, raised by 077 and taken in here: when merging a conflict leaves one of the
branch's commits with nothing of its own, `git rebase --continue` refuses with "No changes", and
`resolve --continue` reports "the rebase won't go on", so ship aborts and stops. Nothing is lost,
but a batch of seven changes landing over the same board files is when it's likely to bite.

A factory reviewer that writes a sentence before its `VERDICT:` line stops the run (bug
2026-11-17-18). On 2026-11-17, 088's round-2 UI review opened "Both kept changes are in the
code. …" with `VERDICT: PASS` on line 3, and `verdicts` stopped with "reviews/round-2/ui.md
doesn't open with VERDICT: PASS or VERDICT: CHANGES". `factory.py` reads only a reply's first line
(`VERDICT_RE.match(lines[0])`, at its three readers), and only a missing `## Evidence` can be
mended, so the ways on are deleting the reply by hand and rerunning, or shipping by hand.

## Outcome

- Retiring an entry that another's `After:` names commits as `Retire <id>` alone; a test retires
  such an entry and checks the subject and `entries`.
- An entry whose own lines did change is still an `Update`; the existing tests stay green.
- `resolve --continue`, on a rebase step that a resolved conflict left empty, skips that commit
  and goes on; a test makes a branch commit that the base already holds and resolves through it.
  The aside commit (`refs/sdlc/aside/<branch>`) is still undone at the end, never skipped.
- A reviewer reply whose first line isn't its verdict is a mendable stop: `verdicts` names it, the
  supervisor asks the same reviewer once (`agent --task mend --role <reviewer>`) to reply again
  with its verdict first, written over the old reply, and a second such reply stops as today; a
  test drives a preamble reply through the mend to a review the loop reads. The first-line rule
  itself, and every copy of the parsing (ship, the board, status, land), stay as they are.
- `./check.sh` passes.

## Affected

- **Area:** the inbox's commit labelling, and the conflict resolver ship and land use.
- **Files & components:** `scripts/sdlc.py` (`cmd_inbox_commit()`, perhaps `parse_entries()`'s
  caller only; `cmd_resolve()`), `tests/test_sdlc.py` or the inbox and resolve tests where they
  live; `plugins/factory/scripts/factory.py` (`loop_state()`'s stop, `cmd_agent()`'s `mend`),
  `plugins/factory/skills/build/SKILL.md` (the `stop` step's mendable stops), AGENTS.md's factory
  paragraph, `tests/test_factory.py`.
- **Downstream:** `/sdlc:idea`, `/sdlc:bug`, `/sdlc:triage`, which commit through
  `inbox-commit`; `/sdlc:ship`'s Step 0 and `factory.py resolve`'s landing, which run `resolve`;
  the factory's supervisor, which takes the new mend; the board and status, which show the stop
  until it's mended.
  `parse_entries()`'s title resolution is read by status's `After:` ordering, which must not move.

## Constraints

- `parse_entries()`'s output for status, retro and `After:` checks stays as it is; the fix is in
  what `inbox-commit` compares.
- `inbox-commit` still refuses a removed entry without a reason, and still detects a real edit.
- `resolve` never skips a commit that holds anything, never loses the aside commit, and still
  aborts and refuses on what it can't take on.

## Approach

- In `cmd_inbox_commit()`, compare entries without the resolved `after` (the entry's raw text, or
  its `After:` refs as written), so a neighbour's removal changes nothing; leave `parse_entries()`
  alone.
- In `cmd_resolve()`'s `--continue`, when `git rebase --continue` answers that the commit is now
  empty, run `git rebase --skip` and carry on, unless the empty commit is the aside commit, which
  is handled as now. Takes in nit 2026-11-17-11.
- In `factory.py`, a reviewer reply that doesn't open with its verdict joins `## Evidence` as a
  stop the run may mend once: `verdicts` marks it mendable, `agent --task mend --role <reviewer>`
  resumes that reviewer's session with "reply again, `VERDICT:` on the first line", and its reply
  is written over the old one; the build skill's `stop` step names it. Fixes bug 2026-11-17-18.
- One test for each, red first.

## Open questions

- Is the raw text the right comparison, or would a whitespace-only edit then read as an `Update`
  too (it does today, so probably fine)?
- Should the mend also take a verifier or approver reply that doesn't open with its line, or only
  a reviewer's?
- On an empty aside commit (the uncommitted work all already on the base), is skipping it the same
  as undoing it, or does `--continue` need to note that nothing was put back?
