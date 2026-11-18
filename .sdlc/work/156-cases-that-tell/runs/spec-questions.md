
**Resolved from the code:**
- *How does a failed case block a factory landing today?* `cmd_cases` writes no note when cases fail, and `_land_readiness()` puts `cases` in `before` until a note exists. That one path is what changes (R11, R14).
- *Where are traces, and why are they lost?* Each run's `tracePath` is in `/private/tmp/e-*/out/`, and it is lost without `--keep-temp` (from `result.json`). R9 keeps copies of the failing ones in the run folder.
- *Do the 3 runs per case at release already exist?* Yes: `CASE_CAP["full"] = ("3", "20")`. R18 adds only the history.
- *How many graders actually insist on a tool?* Two, both in `ship-behaviour`. Most of the 60 `tool_used` graders name `Bash` and a command only a shell runs, which already checks an outcome.
- *Can the ship side already skip cases?* Yes: ship's note takes `Skill evals: skipped, <why>` when the person declines the prompt, and the question names the skip. Only the factory needed `--skip`.

**Left for you:**
1. **The contract edit:** do the factory's cases run before `land`'s WAIT (this spec; *Writes before a WAIT* gains the factory's `cases` note), or after the yes, with a failure sent back to the next `/sdlc:land` (no contract edit, a second round per failure)?
2. **Does the two-failure rule apply to every case?** (intent's question 1) This spec applies it to every case. The other option fails a case on its first run when the failed grader is an outcome one (the question asked, a commit or push before the yes). That is cheaper on a real break, but a bad roll on those graders would block again. It's a set of grader names in `case_verdicts`, easy to add later.
3. **Who decides "wording only"?** (intent's question 2) This spec says the person decides, by declining the prompt and giving a reason that `--skip` records. Your call if you'd rather the script judged it, or showed a hint.
4. **Does release run the full suite every time?** (intent's question 3) Unchanged here: release offers it every time, as advice, and runs it only on a yes. The other option offers it only when a skill with cases changed, or the Claude Code version moved, since the last full run. That is less noise, but a model change in the same Claude Code version would go unmeasured.
5. **Before the plan starts:** check `claude plugin eval`'s grader reference for a workspace-state grader or a multi-tool `tool_used`, either of which would replace R2's `llm` grader. Also check a kept run's folder layout against R9's guard.
6. **Upstream report:** filing the sandbox's xcrun/git fault with Claude Code is yours to do, by hand. It shouldn't mention that an agent found it.
