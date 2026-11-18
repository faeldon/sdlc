# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## AGENTS.md has no line past 100 columns

A reflow changes line breaks only, which no test reads, so only rewrapping it back could fail it.

```sh
python3 -c "import sys; sys.exit(any(len(l) > 100 for l in open('AGENTS.md', encoding='utf-8').read().splitlines()))"
```

## The supersedes sentences and the README's UI paragraph are wrapped

Each was one long line; a revert of the wrap is the only way back to one.

```sh
python3 -c "
import sys
for path, words in (('plugins/factory/agents/reviewer-code.md', 'supersedes D<n>'),
                    ('plugins/factory/agents/reviewer-ux.md', 'supersedes D<n>'),
                    ('plugins/factory/README.md', 'must all be set for a UI review')):
    lines = [l for l in open(path, encoding='utf-8').read().splitlines() if words in l]
    sys.exit(1) if not lines or any(len(l) > 100 for l in lines) else None
"
```

## Ship's pass files say a factory run's own reviewers ran, and security a deep diff

Wording no test pins: only a rewrite back to the old sentences could fail it.

```sh
grep -q "not a factory run, whose own reviewers ran" skills/ship/behaviour.md && grep -q "a deep" skills/ship/security.md && grep -q "isn't a factory run, whose own reviewers ran" skills/ship/security.md && grep -q "isn't a factory run, whose own reviewers ran" skills/ship/ui.md && grep -q "factory.py shots NNN --round 1 --role ui" skills/ship/ui.md && ! grep -q "review.sensitive" skills/ship/security.md
```
