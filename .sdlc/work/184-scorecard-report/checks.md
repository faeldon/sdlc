# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## REFERENCE.md no longer says the report lacks the figures (R20)

The three sentences are prose a later edit could only bring back by hand.

```sh
! grep -n "doesn't show these yet\|aren't in its body yet" docs/REFERENCE.md \
  && grep -q '`{{scorecard}}`' docs/REFERENCE.md \
  && grep -q '`sdlc.py retro`.s `scorecard` is that table' docs/REFERENCE.md
```

## S14 is marked done in the scorecard doc (R20)

A status line in a planning doc, which only an edit could revert.

```sh
grep -q 'own section. \*\*Done: 184.\*\* | S1–S13 |' docs/RETRO-SCORECARD.md \
  && grep -q -- '- \*\*S14\*\*, with 2026-11-18-105, done: 184.' docs/RETRO-SCORECARD.md
```

## The retire windows are documented as the windows read (R17)

A docstring and a doc sentence; the behaviour is pinned by `test_retire_with_too_few_windows_names_nothing`.

```sh
grep -q 'below `RETIRE_AFTER` when every item was decided early' docs/REFERENCE.md \
  && grep -q 'when every item was decided early (each used, or never a candidate), and no' scripts/retro.py
```
