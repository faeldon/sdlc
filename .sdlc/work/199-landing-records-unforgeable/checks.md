# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs say the script vouches for its records, and that it stops Edit and Write, not a shell

Only a deliberate edit of the docs could take these sentences out again.

```sh
grep -q "records ledger" AGENTS.md &&
grep -q "sdlc-factory-records.jsonl" docs/REFERENCE.md &&
grep -q "sdlc-factory-records.jsonl" plugins/factory/README.md &&
grep -q "records" plugins/factory/skills/land/SKILL.md &&
grep -q "Write tools" plugins/factory/skills/land/SKILL.md &&
grep -q "can reach the git common dir" plugins/factory/skills/land/SKILL.md &&
grep -q "Write tools" plugins/factory/README.md &&
grep -q "can reach the git common dir" plugins/factory/README.md &&
grep -q "Write tools" docs/REFERENCE.md &&
grep -q "can reach the git common dir" docs/REFERENCE.md
```
