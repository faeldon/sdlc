# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The policy doc says close holds the lock from its merge to its Close commit

Only a revert of the AGENTS.md edit could drop the sentence; the code it describes is tested in
`tests/test_train.py`.

```sh
grep -q "holds \`_main_lock()\` from its merge to that commit" AGENTS.md
```

## The policy doc says the train stacks through resolve --onto and land no longer runs base

Only a revert of the AGENTS.md edit could drop the words; `tests/test_train.py` proves the code.

```sh
grep -q "stacked on the one before it by the factory's own rebase (\`resolve --onto\`)" AGENTS.md && grep -q "committed by \`land\` (which no longer runs \`base\`)" AGENTS.md
```

## The land skill may run the train

Only a revert could take the rule out; `tests/test_skills.py` checks every command in a bash block
has a rule, so a rule missing while the block stays would fail the suite, but a block and rule
both gone would not.

```sh
grep -q 'factory.py train \*' plugins/factory/skills/land/SKILL.md && grep -q 'factory.py train --begin <NNN…> --by <auto or person>' plugins/factory/skills/land/SKILL.md
```
