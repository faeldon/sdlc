# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The workflow's comment claims nothing about setup-uv's cache token

Nit 2026-11-21-23: the claim is about a third-party action the file can't show, and only putting
the words back could fail this.

```sh
! grep -q "cache token" .github/workflows/check.yml
```
