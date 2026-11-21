# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## autopilot.py is a sensitive path beside landing.py

The design keeps autopilot in a module of its own so `[review] sensitive` can name it; only an
edit of this repo's config could take it out.

```sh
grep -q '"plugins/factory/scripts/autopilot.py",' .sdlc/config.toml
```

## The autopilot skill exists with its one WAIT

Only removing the skill could fail it.

```sh
test -f plugins/factory/skills/autopilot/SKILL.md && grep -q '^## Step 2 — WAIT for explicit approval$' plugins/factory/skills/autopilot/SKILL.md
```
