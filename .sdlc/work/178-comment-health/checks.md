# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The scorecard records comment health as done (R15)

The scorecard is prose no code reads, so only an edit that takes the lines back out could fail it.

```sh
grep -q '^| \*\*S17\*\* |.*\*\*Done: 178\.\*\*' docs/RETRO-SCORECARD.md && grep -q '^- \*\*S17\*\*, done: 178\.$' docs/RETRO-SCORECARD.md && grep -q '^### Supporting: comment health$' docs/RETRO-SCORECARD.md && grep -q 'comment est. tokens' docs/RETRO-SCORECARD.md
```
