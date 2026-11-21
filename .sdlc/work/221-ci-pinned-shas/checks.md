# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## Dependabot proposes bumps to the pinned actions

The file is added once and read only by GitHub, so only its removal could fail this.

```sh
grep -q '^version: 2$' .github/dependabot.yml && grep -q 'package-ecosystem: github-actions' .github/dependabot.yml && grep -q 'directory: /$' .github/dependabot.yml
```
