DECISION: ESCALATE

**Why.** All three reviewers passed round 1 (code, test, behaviour). Each of R1–R15 has a named test, R16's documentation was checked by the code reviewer, and the gate passed (2623 passed, 18 skipped). Nothing is open: there is no `notes.md`, no `decisions.md` and no default. I'm escalating for one reason only. The change extends the `Sdlc-*` trailer contract, a published interface for hosts (REFERENCE.md *Metrics*). The new `Sdlc-Role` fields and the new `Sdlc-Calls` line get written into every host's `Close` commits for good. A revert doesn't remove them from history, so a person should confirm this extension before it lands. I found nothing wrong with it. I read `parse_trailers()`: an older parser puts `Sdlc-Calls` under a generic key without raising. `model=` never holds a `:`, so `_value()` reads it as plain text. R12 pins that an old commit parses the same as before.

**Open items**
- None. Every round-1 verdict is PASS. The code reviewer left two nits:
  - `metrics.py:306`: a `&` in the middle of a multi-line command isn't counted as background. The spec allows this because every count is a lower bound.
  - `metrics.py:261`: the `uvx`/`npx` slicing would read better with a comment.

**Decisions to confirm**
- No blocking decisions and no open defaults.
- For the person: confirm the additive extension of the published trailer contract:
  - `Sdlc-Role` gains `model=`, `edits=`, `shell_edits=`, `bg=`, `tool_errors=`, `test_runs=` and `broke=`.
  - A new `Sdlc-Calls: <role> <name>=<n> …` line.
  - Retro's JSON gains `spend.agents` (with `groups`, `unrecorded` and `changes`, the last only with `--metrics`).
  - Coverage can now say `behaviour=failed`.

**For the person at ship**
- Look at `trailers()` and `parse_trailers()` in `scripts/metrics.py` (lines ~1553–1564 and the new `calls` branch at line 1647). Check that only counts and names reach a commit.
- Then look at `_shell()`, `_segments()` and `_behaviour()`. These classify commands without keeping any command text.
- Then `_agent_models()` in `scripts/sdlc.py`. It passes `models` by position, a departure explained in plan.md's *As built*.
- Then `_agents()` in `scripts/retro.py`, and the REFERENCE.md *Metrics* paragraph.

- IMPACT: minor — hosts' `Close` commits newly carry per-role behaviour counts, models and tool calls, and retro newly compares agents by role and model; old commits read the same as before.

**Undone items:** none (there is no `notes.md`, and the builder reports nothing left over).

**How to recover:** the prompt names no irreversible paths. plan.md's Rollback is `git revert`. `Close` commits made while the change was in keep the new fields, and they stay readable by both old and new parsers.
