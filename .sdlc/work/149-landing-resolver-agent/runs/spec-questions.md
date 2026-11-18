
Resolved:

- **How is "conflicted files only" enforced?** By the script, at `resolve --continue`. Tool
  permissions can't do it: `Edit` takes any path and `Bash` writes anything. So the resolver lacks
  `Write` and `Agent`, and `--continue` refuses any changed or untracked path outside the conflicted
  files and the landing's records, read from one `git status --porcelain -z` listing (R8, R9).
- **Does `land-fix` stay with the change's own builder?** Yes. It is in `RESUMES` and is a change to
  the work, not a merge (R11).
- **Does `scripts/metrics.py` change?** No. Roles come from the `runs/*.sessions` file names
  (`sdlc.py`'s `_agent_sessions()`), with no list of roles, so `Sdlc-Role: resolver` follows on its
  own (R12).

Left for you:

- **Sonnet or opus as the resolver's default?** The spec goes with the intent's sonnet.
  - Sonnet: resolving costs a fraction of the builder's run. A wrong semantic merge is still caught
    by the tip's gate and every reviewer at the run's depth, at the cost of an ejection or a
    rework.
  - Opus: semantic conflicts (two changes editing one function) are likelier right the first time,
    for a few times the cost. And the first measurements of the resolver on its own would be of
    opus, not of what the default ends up being.
  - Either way a host can set `[models] resolver`. Changing the default later is one line in
    `FIXED_MODELS` and one in the agent's frontmatter.
- **The single-change `resolve` task** (the builder, resumed) is reached by no skill since `land`
  stopped running `base`. Keep it as is (this spec), retire it, or move it to the resolver in a
  later change.
- **Pre-existing, not fixed here:** `cmd_resolve --continue` stages files by `_conflicted()`'s
  `git diff --name-only` output, which git quotes for a non-ASCII path, so `git add` of such a
  conflicted file would miss it. The new fence doesn't rely on that output, but the staging still
  does. Worth a `[nit]` or a bug.
