---
id: 173
slug: style-paydown
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 173 — Pay down the style nits in one change · plan

> Written by the builder after reading the files the nits name. A Tier 1 change whose Approach
> reaches seven files, so it gets a plan.

## Files to change

- `.github/workflows/check.yml`: rewrap the header comment's 166-column line (-75, -77, -78).
- `AGENTS.md`: rewrap *Modules loaded by path* and *The board* (2026-11-19-5) and *The factory*
  (-83), filling the short lines those edits left in the same paragraphs; one 101-column bullet line
  in *Only the named steps push*, so the file has no line past 100.
- `plugins/factory/README.md`: rewrap every prose line past 100 (-82, -96, 2026-11-19-10), and fill
  the short lines of the paragraph on what `factory.py` does. Table rows and fenced blocks stay as
  they are: a markdown table row can't wrap, and a fence is literal.
- `plugins/factory/agents/reviewer-code.md`, `reviewer-ux.md`: rewrap the prose lines past 100
  (-81): the "Under a decision's line" paragraph, the round-file sentence and the nit-weights
  paragraph. The frontmatter `description:` lines stay on one line (decision below).
- `check.sh`: answer -76 in the comment over the pytest step: the summary's `skipped` count is
  expected (the board's pairs of states that can't overlap, 28 of them, and the `browser` tests
  without Chromium), and `pytest -rs` names each reason. Rewrap its 102-column line on the way.
- `.sdlc/function-heat.py`: -108's comment over `heat()`'s blame call, saying a file added after
  the boundary has no boundary lines, so the commit that added it counts as one.

No code but a comment changes. Reused: nothing; the rewrap was checked to keep every word, in
order, by comparing each file's whitespace-collapsed text with `HEAD`'s.

## Work order

1. Rewrap the markdown files, carrying each long line's overflow into the next line until one fits,
   so the diff stays near the lines named; then fill the named paragraphs' short leftovers.
2. Rewrap `check.yml`'s header by hand.
3. `check.sh`'s comment (-76) and `function-heat.py`'s (-108).
4. The acceptance check, then the full gate: these files are read by many tests' substring checks,
   so the whole suite, not one test, shows a rewrap broke none.

## Tests

No behaviour changes, so no new test. The outcome (lines near 100, the two comments) is proved by
`checks.md`, which only a revert could fail. The full gate (`factory.py check`) shows no test that
reads these files' text broke; `tests/test_function_heat.py` and `tests/test_board.py -rs` were run
by name (the latter to confirm what the 28 skips are).

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, and `check.yml`'s comment
changes no CI step.
