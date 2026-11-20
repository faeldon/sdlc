# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The review doc's Pass 1 names git state read after the step that changed it

The bullet is a line of prose in `.sdlc/REVIEW.md`: only an edit that took it out could fail this.

```sh
awk '/^## Pass 1/{p=1} /^## Pass 2/{p=0} p' .sdlc/REVIEW.md | grep -q '^- \*\*Git state read after the step that changed it\.\*\*'
```
