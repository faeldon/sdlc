# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The factory's README says check runs share the gate slots

R12: the README's line is prose no test reads, so only a revert of it could fail this.

```sh
tr '\n' ' ' < plugins/factory/README.md | tr -s ' ' | grep -q 'Gates and `check` runs from every worktree share `gate_jobs` slots' && grep -q 'factory.py check NNN' plugins/factory/README.md
```
