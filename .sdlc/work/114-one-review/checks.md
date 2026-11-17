# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## R3: the review names a test for each requirement, in the guide and in ship

A rule of prose in the guide and the skill: only removing those lines could fail it.

```sh
grep -q "names that test and the line whose removal would fail it" guide/review.md && grep -q "name its code and its test, with the line whose removal fails it" skills/ship/SKILL.md && grep -q 'test that passes without the code is a `\[correctness\]` finding' skills/ship/SKILL.md
```

## R4: the factory's code reviewer runs a context pass

A pass in an agent's prompt: only removing it could fail this.

```sh
grep -q '^5\. \*\*Context\.\*\*' plugins/factory/agents/reviewer-code.md && grep -q '\[docs\] context' plugins/factory/agents/reviewer-code.md && grep -q -- '- CHANGE: \[context\] <doc>:<line>:' plugins/factory/agents/reviewer-code.md && grep -q 'Anything else gets no line' plugins/factory/agents/reviewer-code.md
```

## R11: ship keeps the agents' findings and isn't bound by their wrong

Rules in ship's skill and its factory side file, read on every factory-built change: only removing
them could fail this.

```sh
grep -q 'Keep each exactly as written, never re-disposition or renumber it' skills/ship/factory.md && grep -q "never stops you raising the same fault" skills/ship/factory.md && grep -q 'one the person answered `wrong`' skills/ship/SKILL.md && grep -q "counted apart from ship's own" skills/ship/factory.md
```

## R19: ship by hand files a pre-existing item as a bug

A disposition in ship's undone side file: only removing it could fail this.

```sh
grep -q 'file it as a bug' skills/ship/undone.md && grep -q -- '→ bug: <id>' skills/ship/undone.md && grep -q -- '--bugs' skills/ship/undone.md
```
