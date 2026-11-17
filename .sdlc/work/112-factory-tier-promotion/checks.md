# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs describe the upgrade, and none calls it a promotion

R15 is prose in five docs, so only a revert of these lines could fail it.

```sh
grep -q 'upgrade to Tier 2' plugins/factory/agents/builder.md &&
grep -q 'build/round-<N>.upgraded.md' plugins/factory/README.md &&
grep -q "through \`sdlc\`'s own \`upgrade\`" AGENTS.md &&
grep -q 'sdlc.py upgrade <NNN>' docs/REFERENCE.md &&
grep -q 'An upgrade to Tier 2' plugins/factory/scripts/factory.py &&
! grep -qi 'promot' plugins/factory/agents/builder.md plugins/factory/README.md docs/REFERENCE.md plugins/factory/skills/build/SKILL.md
```
