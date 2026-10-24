---
id: NNN
slug: SLUG
kind: plan
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# NNN — TITLE · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

<Path + one line on what happens to it. New files marked `(new)`. List tests and docs as their own
lines — they are separate edits from the code, and the ones that get forgotten.>

## Work order

<Numbered steps in dependency order. Each step should end somewhere you could stop, with what it
built tested before anything depends on its new shape.>

1.
2.

## Tests

<What proves each requirement, by requirement number. An automated test wherever one can reach.
"Manual: run X, expect Y" is acceptable only where none can — write it down anyway so Stage 4 has
something to execute.>

## Rollback

<How to undo this if it goes wrong. `git revert <sha>` covers the code; say explicitly what it does
*not* cover — anything created outside the repo, data already written, something downstream already
pointed at a renamed thing. Name the command that undoes each.>
