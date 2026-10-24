# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## <What the check proves, as its name>

<Why only a revert could fail it, in a sentence.>

```sh
<the command, asserting inside itself: grep -q, test, a script's exit code>
```
