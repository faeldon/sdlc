# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The retrospective runs the function heat as an indicator

Only removing the `indicators` line from `.sdlc/config.toml`'s `[retro]` could fail it.

```sh
grep -qx 'indicators = \["uv run --quiet --script .sdlc/function-heat.py"\]' .sdlc/config.toml
```

## The function heat prints a table for the four scripts

Only deleting or emptying `.sdlc/function-heat.py` could fail it; its behaviour is the suite's.

```sh
out=$(uv run --quiet --script .sdlc/function-heat.py) && printf '%s\n' "$out" | grep -q '^scripts/sdlc.py$' && printf '%s\n' "$out" | grep -q '^plugins/factory/scripts/landing.py$'
```
