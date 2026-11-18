# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs say the builder and the resolver edit, and the builder no longer resolves

R13's words are prose in AGENTS.md, the factory README and builder.md: only a revert of those
lines brings the old rule or the builder's landing section back.

```sh
! grep -rnE "landing agent, the builder|Only the builder edits" plugins AGENTS.md \
  && ! grep -q "## A conflict, while landing" plugins/factory/agents/builder.md \
  && grep -q "only the builder and the resolver edit" AGENTS.md \
  && grep -q "Only the builder and the resolver edit" plugins/factory/README.md \
  && grep -q '^| `resolver` |' plugins/factory/README.md
```
