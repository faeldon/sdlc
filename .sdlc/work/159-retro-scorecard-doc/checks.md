# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The scorecard doc holds the framework

Only deleting the doc or one of its sections could fail it: nothing generates or reads it.

```sh
f=docs/RETRO-SCORECARD.md && test -f "$f" && grep -q '^# Retrospective scorecard$' "$f" && grep -q '^## Value band' "$f" && grep -q '^## Pillar 1: Speed' "$f" && grep -q '^## Pillar 2: Quality' "$f" && grep -q '^## Pillar 3: Autonomy' "$f" && grep -q '^## Pillar 4: Cost' "$f" && grep -q '^## Pillar 5: Simplicity' "$f" && grep -q '^## Trust band' "$f" && grep -q '^## Insights' "$f" && grep -q '^## Seeds to build it' "$f" && grep -q '\*\*S16\*\*' "$f" && grep -q '\*\*R6\*\*' "$f"
```

## CONTRIBUTING's layout lists the doc

Only removing the layout row could fail it.

```sh
grep -q '^| `docs/RETRO-SCORECARD.md` |' docs/CONTRIBUTING.md
```
