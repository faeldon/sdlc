VERDICT: PASS

## Notes

I found no Critical or High issues. A goal can only narrow what a run takes: nothing that gates the run reads it, and every new string from the planner is checked by the script or only shown to the person.

**Trust boundaries checked (STRIDE)**

- **The planner's reply (model output, untrusted) → `read_plan()`.**
  - **Tampering:** the plan can't widen what the run takes. Any seed that isn't a candidate is refused, every candidate must be placed exactly once, and there can't be more WAVE lines than the room.
  - **Tier:** a WAVE tier past `level` is refused. The planner's tier only reaches the intent-writer as the `Planned:` line. `open_seed()` still takes the draft's own `tier:`, capped by the bounds as before.
  - **Spoofing a skip:** a LEAVE takes a seed out of this run only. It lands in `state["seeds"]` with `left` set, is shown under `## Left for you` or the plan's "Off the goal" lines, and is never retired. The worst a misbehaving planner can do is skip work, and the summary shows that.
- **A LEAVE's cited path → `cited_paths()`.** Absolute paths, drive letters and `..` segments are refused before `(main / rel).exists()`. The check only tests existence and reads nothing, so even a symlink leaks at most whether a path exists inside the repo. That is not an information-disclosure path.
- **The person's `--goal` text → the question, `shown`, the planner's brief and the summary.** It is the person's own input. It reaches the question the person approves, and `summary.md` is still passed through `factory._placeholders()` as a whole (line 1593). It changes no bound, guard or hold.
- **The direction doc and register → `sdlc.py status --json` → `direction_open()`.** It only reads: it is a projection of `direction_items()` and `inbox_entries()` through `ref_matches()`. Nothing in the diff writes `inbox.md` or the direction doc. `register_ids()` only reads.
- **Bounds and guards (elevation of privilege).** The scope filter in `candidates()` runs before the existing `bounds["seeds"]` check and the `Issue:` check (D9), so an outsider's seed in a milestone or theme scope still needs `--seeds` to name it. Neither `hold_causes()` nor `autopilot_config()` reads the goal. `--begin` resolves `--goal` again and refuses rather than proposing one, so the goal the yes approved can't be swapped between the preview and the yes.
- **Repudiation:** the goal and its source are kept in the state, the brief and the summary, and the calls are still recorded as autopilot's.
- **Dependencies and secrets:** there are no new dependencies and no secrets in code, fixtures or artifacts.

**Medium, Low and Info findings**

- **Low:** Step 1 of the skill says to "quote a goal in their own words" but doesn't say how. Inside double quotes, `$(...)` or backticks in the person's text would be expanded by the shell. The person could run that command anyway, and Claude Code prompts on command substitution, so it isn't exploitable. Saying single quotes would make it robust.
- **Info:** a `fixed` or `wrong` LEAVE only needs some existing repo path in its reason, such as `README.md`. That is all the script can check mechanically, and the spec says so. The safeguard is that the seed is left for the person, not retired.
- **Info:** the `Planned:` line copies the planner's reason, which is model text, into the intent-writer's brief. That agent already reads untrusted seed text, and its draft still goes through `hold_causes()` and the tier cap, so this adds no new reach.

- NIT: plugins/factory/skills/autopilot/SKILL.md:101: say to single-quote a goal given in the person's own words, so `$`, backticks and `"` in it stay literal {robustness S med}

**What is done well**

- `begin_goal()` resolves the goal again and refuses rather than proposing one.
- The milestone and theme scope sits before the D9 `Issue:` filter, so that filter still applies inside a goal's scope.
- `cited_paths()` refuses traversal and absolute paths.
- Left seeds are kept separate from held ones in the summary.

**What I checked and ran**

I read `intent.md`, `spec.md` and the diffs of `autopilot.py`, `factory.py`, `sdlc.py`, `prompts/autopilot.md`, the skill and the planner agent. I also checked that `write_summary()`'s whole text still goes through `_placeholders()`. The `round-1.gate.md` record is `GATE: PASS` (`./check.sh`, exit 0). I didn't run the gate myself.
