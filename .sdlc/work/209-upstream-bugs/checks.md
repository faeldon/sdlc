# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs say what filing upstream does

R15's lines in REFERENCE.md, README and AGENTS.md are prose no test reads, so only a revert of
them could remove them.

```sh
grep -q 'sdlc.py upstream' docs/REFERENCE.md &&
grep -q 'sdlc:host-bug:' docs/REFERENCE.md &&
grep -q 'a bug in the plugin itself goes to the plugin' README.md &&
grep -q 'by `upstream` (`upstream_tracker()`)' AGENTS.md &&
grep -q 'UPSTREAM_INPUT' AGENTS.md &&
grep -q '^- \*\*`upstream bug`\*\*' docs/FEATURES.md
```
