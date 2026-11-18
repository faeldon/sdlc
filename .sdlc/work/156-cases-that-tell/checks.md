# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs say how the cases rerun, class the sandbox and land

R19's three documents name the rerun, the environment class, kept traces, `--skip` and
outcome-only graders, and the new write before `land`'s WAIT: prose only a revert would take out.

```sh
grep -q "reruns alone, once" docs/CONTRIBUTING.md &&
grep -q "is \`environment\`: never rerun" docs/CONTRIBUTING.md &&
grep -q "test_no_grader_insists_on_a_tool" docs/CONTRIBUTING.md &&
grep -q "cases <NNN> --skip <why>" docs/CONTRIBUTING.md &&
! grep -q "keeps each run's folder and trace" docs/CONTRIBUTING.md &&
grep -q "factory's \`cases\` (and \`cases --skip\`)" AGENTS.md &&
grep -q "cases --skip" plugins/factory/README.md
```
