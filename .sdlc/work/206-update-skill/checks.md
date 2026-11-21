# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## AGENTS.md maps the hook and its cache (R10)

The paragraph is prose in the map, which no test reads; only an edit that takes it out could fail.

```sh
grep -q '^\*\*Updates: `cmd_update()` and the one hook.\*\*' AGENTS.md &&
grep -q 'hooks/hooks.json' AGENTS.md &&
grep -q 'sdlc-update.json' AGENTS.md &&
grep -q 'That cache is the one write' AGENTS.md
```

## README's skill table lists /sdlc:update (R15)

A row in a table a person reads, which no test checks.

```sh
grep -q '^| `/sdlc:update` |' README.md
```
