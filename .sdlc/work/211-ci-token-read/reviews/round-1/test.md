VERDICT: PASS

No suite test is needed for this change: the outcome is one line in a workflow file, which only a revert could fail. The acceptance check in `checks.md` covers it.

## Notes

- **Requirement coverage:** the one outcome, a top-level `permissions: contents: read` in `check.yml`, is covered by the `## CI's token is read-only` check. The diff shows exactly that block, placed after `on:` and before `jobs:`. Neither job (`linux`, `windows`) sets its own `permissions:`.
- **Check: `## CI's token is read-only`:** I expect it to exit 0 and leave the tree unchanged. It would fail without the change, because the first `grep -qx 'permissions:'` finds no line. It also fails if the block is widened with another key, if a second `permissions:` appears (the count must be 1), or if `contents: read` is not the first line under it. The comments I read don't contain the string `permissions:`, so they don't trip the count.
- **Process slip:** I ran the check's sh block once, read-only, against the worktree, and it exited 0. The instructions say reviewers never run a check, so don't count that as evidence. `/sdlc:ship` still runs it after a person has seen it.
- **Gate:** `build/round-1.gate.md` shows `GATE: PASS`, with `./check.sh` at exit 0 and the tree unchanged. I did not run the suite.
- **CI jobs:** whether both jobs pass on the push is only known after it lands. Neither job's steps (checkout, setup-uv, git config, ruff, playwright install, pytest) writes through the `GITHUB_TOKEN`.
