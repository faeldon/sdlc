# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The review doc names both escape classes

The two bullets are prose in `.sdlc/REVIEW.md`, which only an edit that takes them out could lose.

```sh
grep -q '^- \*\*A transcript.s shape assumed, not read\.\*\*' .sdlc/REVIEW.md && grep -q '^- \*\*A path compared as text between two sources that write it differently\.\*\*' .sdlc/REVIEW.md
```
