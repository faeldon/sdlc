---
id: 126
slug: is-read-refuses-writers
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-1
depends_on:
serves: [O6]
---

# 126 — is_read() refuses file -C and git's --ext-diff and --textconv

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`is_read()` (`plugins/factory/scripts/factory.py`), from 123, decides which evidence commands only
read and so may leave out `exit:`. Two writers still pass as reads: `file -C -m <magic>`, on R1's
plain-read list, compiles a magic file and writes `<magic>.mgc`; and git's `--ext-diff` and
`--textconv` run an external program from `git diff`, `git log -p` or `git show`, which can write.
123 left the first undone: "`file` is on R1's plain-read list, but `file -C -m <magic>` compiles a
magic file and writes `<magic>.mgc`. A later change could give `file` its own condition (no `-C`)
the way `sort` has one."

## Outcome

- `is_read()` refuses `file` with `-C` in any spelling, and a git read command with `--ext-diff`
  or `--textconv`; each is a `NON_READS` row, and `file x` and `git diff` stay `READS` rows, in the
  one table test.
- **Moves O6:** a change can't pass the evidence check on a command that wrote.

## Affected

- **Area:** the factory's evidence check.
- **Files & components:** `is_read()` and its tables in `plugins/factory/scripts/factory.py`;
  `tests/test_factory.py`.
- **Downstream:** `read_evidence()` and `land_verdict()`, so every builder report and behaviour
  check.
- **Contracts:** a builder report and a behaviour check end with `## Evidence`; none other.

## Constraints

- A non-read never becomes a read, and every current `READS` row stays.

## Open questions

- Is git's `-c` (`-c diff.external=…`) refused too, since it does the same?

## Approach

Give `file` its own condition, as `sort` has, and a git argument condition beside the existing git
handling, with their table rows.
