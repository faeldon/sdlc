# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs state the landing's new gates

R20: no test reads a doc's meaning; only a revert of the doc edits would bring back the old rule's
wording or drop the new one's names.

```sh
! grep -rnI "The loop runs neither\.\|harness asks before every run" AGENTS.md plugins/factory && grep -q "\`\[commands\] build\` for \`gate --land --build\`" AGENTS.md && grep -q "checks_clearance()" AGENTS.md && grep -q "land-checks" plugins/factory/skills/land/SKILL.md && grep -q "gate --land --build" plugins/factory/README.md
```
