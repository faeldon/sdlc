# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The review names the doc-claim failure class (R9)

A bullet added to `.sdlc/REVIEW.md`; only removing it fails this.

```sh
awk '/^### The ways this repo.s code fails/{f=1;next} /^## /{f=0} f' .sdlc/REVIEW.md | grep -q "^- \*\*A doc's claim the change made false\.\*\*"
```

## The docs describe the workarounds (R12)

Lines added to four docs; only a revert of them fails this.

```sh
grep -q 'simplicity.workarounds' docs/REFERENCE.md && grep -q 'simplicity.workarounds' skills/retro/SKILL.md && grep -q 'which train (train' plugins/factory/README.md && grep -q 'Done: 180' docs/RETRO-SCORECARD.md
```
