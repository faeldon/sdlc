# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The CI workflow is a sensitive path here

Only undoing R11's line in this repo's `[review] sensitive` could fail it.

```sh
uv run --quiet --script scripts/sdlc.py config | grep -q '"\.github/workflows/"'
```
