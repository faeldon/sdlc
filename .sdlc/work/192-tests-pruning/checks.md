# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The suite is tests/ alone, for retro's kinds

This repo's `retro.test_paths` is a setting, not behaviour any test exercises: only removing the
line would fail it, and then `skills/spec/SKILL.md` would count as a test again.

```sh
uv run --quiet --script scripts/sdlc.py config | tr -d ' \n' | grep -q '"test_paths":\["tests/"\]'
```
