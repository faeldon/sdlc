# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The deep review lists closing.py and landing.py

The two lines are config, not behaviour: only an edit that takes them out of `[review] sensitive`
could fail this, and 153's build greps the base branch for them in the same quoted form.

```sh
sed -n '/^\[review\]/,/^\]/p' .sdlc/config.toml | grep -qF '"scripts/closing.py"' &&
  sed -n '/^\[review\]/,/^\]/p' .sdlc/config.toml | grep -qF '"plugins/factory/scripts/landing.py"'
```
