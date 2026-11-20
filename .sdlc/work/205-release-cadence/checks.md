# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The process doc says this repo releases once each wave has landed

The answer is prose in `.sdlc/SDLC.md`, under the guide's release-loop heading; only an edit that
takes it out could fail this.

```sh
awk '/^### The release loop/{f=1;next} /^#/{f=0} f' .sdlc/SDLC.md | tr '\n' ' ' | grep -q 'wave' && awk '/^### The release loop/{f=1;next} /^#/{f=0} f' .sdlc/SDLC.md | tr '\n' ' ' | grep -q 'before the next retrospective'
```
