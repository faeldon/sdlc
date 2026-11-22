# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## Both prompts say a hook-refused command is no `$ ` line and every exit is a real code

The sentences are prompt text no test runs, so only an edit that takes them out could fail this.

```sh
for f in plugins/factory/agents/reviewer-behaviour.md plugins/factory/agents/builder.md; do
  tr '\n' ' ' < "$f" | grep -q 'A command a hook refused never ran, so it is no `\$ ` line' || exit 1
  grep -q 'echo "exit: \$?"' "$f" || exit 1
done
tr '\n' ' ' < plugins/factory/agents/reviewer-behaviour.md | grep -q "list it under \`## Notes\`" || exit 1
```
