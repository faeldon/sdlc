# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The resolver is told how to resolve a file one side deleted

Its agent file's instructions are prose no test reads; only an edit taking them out could fail.

```sh
grep -q '^- \*\*A file one side deleted\*\* (a modify/delete conflict)' plugins/factory/agents/resolver.md
```

## grep's long-option threshold counts the characters after its `--`

A named constant and its use, the nit's fix: same behaviour, so only a revert of the text fails.

```sh
grep -q '^GREP_FOLLOWS_MIN = 3$' plugins/factory/scripts/landing.py && grep -q 'len(name) - 2 >= GREP_FOLLOWS_MIN' plugins/factory/scripts/landing.py
```
