---
id: 132
slug: is-read-refuses-gpg
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O6]
---

# 132 — is_read() refuses git's signature options that run gpg

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

126 made `is_read()` (`plugins/factory/scripts/factory.py`) refuse git's options that run an
external program from a read, `--ext-diff` and `--textconv` (`GIT_RUNS`), but left out the
signature options, which run `gpg`: `git log --show-signature` / `git show --show-signature`, and any
pretty format holding a `%G` placeholder (`%G?`, `%GS`, `%GK`, `%GG` …), as in
`git log --format=%G?` or `--pretty=format:…%GS`. So an evidence command can run gpg, which writes
to `~/.gnupg` and can prompt, and still count as a read that needs no `exit:` line. 126's code
reviewer raised it as a default decision (assume: leave it, file a follow-up), but wrote the line
without its `- `, so the ledger never caught it; only the approver's note carried it here. Its
nit F1 also noted the comment at the refusal table claims "run an external program" more broadly
than the table covers.

## Outcome

- `is_read()` refuses a git read command carrying `--show-signature` (in any abbreviation git
  takes), or a `--format=`/`--pretty=` value holding a `%G` placeholder; each is a `NON_READS` row
  in the one table test, and `git log --format=%H %s` and `git show HEAD` stay `READS` rows.
- The comment at the refusal table says exactly what is covered.
- **Moves O6:** a change can't pass the evidence check on a command that ran another program.

## Affected

- **Area:** the factory's evidence check.
- **Files & components:** `is_read()`, `_git_reads()` and `GIT_RUNS` in
  `plugins/factory/scripts/factory.py`; `tests/test_factory.py`.
- **Downstream:** `read_evidence()` and `land_verdict()`, so every builder report and behaviour
  check.
- **Contracts:** none beyond what 126 already came near.

## Constraints

- A non-read never becomes a read, and every current `READS` row stays.

## Open questions

- Does `log.showSignature=true` in a host's git config count? It turns signatures on with no flag,
  so `is_read()` can't see it from the command alone.
- Is `-c log.showSignature=true` already refused by 126's `-c` handling?
- Is `%G` the only placeholder family that runs gpg?

## Approach

`--show-signature` added to `GIT_RUNS` with its shortest abbreviation; a check in `_git_reads()`
refusing a `--format`/`--pretty`/`format:` value that holds `%G`; table rows; the comment fixed.
No open nits touch these paths.
