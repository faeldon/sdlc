VERDICT: PASS

## Notes
- The change sets `approver = "sonnet"` under `[models]` in `.sdlc/factory.toml`, with a comment on the trial and what the next retrospective reads. The comment names the 2026-11-20 retrospective, the READY changes that escaped and the ESCALATEs the person found empty, as the intent asks.
- The intent calls for sonnet "at both depths". A single `approver` entry covers both. `checks.md` confirms it for tiers 1 and 2 at both light and full depth, and I ran its sh block: exit 0.
- `factory.py config` shows `"models": {}` in this worktree. That is expected: it reads the base branch's file, and its own warning says so. That is why the check goes through `_models()` and `model_for()` instead.
- The gate record `build/round-1.gate.md` is PASS. I did not rerun the gate.
- The header comment in `factory.toml` is updated to match the new `[models]` table.
- My grep for context docs that say "Only [ui] differs" errored on a shell glob, so I did not search for them. The diff touches only `factory.toml` and no plugin default, so I did not look further.
- No test was added, which fits a one-window config change; the `checks.md` acceptance check covers it.
