# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## CI's push trigger names branches and no tags

Only putting the bare `on: push` back could fail it: a tag push then starts a second run of a
commit its branch push already checked.

```sh
on=$(sed -n '/^on:/,/^jobs:/p' .github/workflows/check.yml)
printf '%s\n' "$on" | grep -q '^    branches:' && ! printf '%s\n' "$on" | grep -q 'tags' && printf '%s\n' "$on" | grep -q '^  workflow_dispatch:'
```
