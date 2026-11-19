# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The named files have no prose line past 100 columns

Only rewrapping a line back out could fail it; table rows, fenced blocks and frontmatter
descriptions, which can't wrap, are left out.

```sh
python3 -I -c '
import sys
bad = []
for f in [".github/workflows/check.yml", "AGENTS.md", "plugins/factory/README.md",
          "plugins/factory/agents/reviewer-code.md", "plugins/factory/agents/reviewer-ux.md",
          ".sdlc/function-heat.py", "check.sh"]:
    fence = False
    for n, line in enumerate(open(f, encoding="utf-8").read().split("\n"), 1):
        if line.startswith("```"):
            fence = not fence
        elif len(line) > 100 and not fence and not line.startswith(("|", "description: ")):
            bad.append(f"{f}:{n}")
print(*bad, sep="\n")
sys.exit(1 if bad else 0)
'
```

## check.sh says why its summary counts skipped tests

Only removing the comment could fail it.

```sh
grep -q 'pytest -rs` names each reason' check.sh && grep -q 'skipped` count is expected' check.sh
```

## heat() says how a file added after the boundary counts

Only removing the comment could fail it.

```sh
grep -q 'A file added after `since` has no boundary lines' .sdlc/function-heat.py
```
