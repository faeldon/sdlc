# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## CI's token is read-only

The block is a line in the workflow, so only removing it could fail this: the top level of
`check.yml` declares `permissions:` with `contents: read` and nothing else, and no job widens it.

```sh
f=.github/workflows/check.yml
grep -qx 'permissions:' "$f" &&
  grep -A1 -x 'permissions:' "$f" | tail -n 1 | grep -qx '  contents: read' &&
  grep -A2 -x 'permissions:' "$f" | sed -n 3p | grep -qv '^  ' &&
  test "$(grep -c 'permissions:' "$f")" -eq 1
```
