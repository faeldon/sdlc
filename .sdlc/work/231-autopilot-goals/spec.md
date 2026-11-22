---
id: 231
slug: autopilot-goals
kind: spec
created: 2026-11-22
updated: 2026-11-22
---

# 231 — Autopilot runs toward a goal, and plans the seeds it takes to reach it · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: none.

1. **R1. `sdlc.py status --json` gives the direction doc's open items.** Next to `next_up`, it prints `direction`: each open goal (`id`, `name`, `title`, `serves`), each open milestone (`id`, `name`, `title`, `serves`, and `seeds`, the register ids its `Groups:` line names that are still open in the register, resolved by `ref_matches()`), and the doc's `problems`. A struck item is never listed. With no direction doc, every list is empty. `test_goals_come_from_the_real_status_json` (in `tests/test_autopilot.py`, through the real `sdlc.py` like `test_candidates_come_from_the_real_status_json`) fails if a struck milestone is listed, a grouped seed's title isn't resolved to its id, or a missing doc gives anything but empty lists.
2. **R2. `--goal` is read by its form.**
   - `G<n>` or `M<n>` names an open goal or milestone in `direction`, with source `direction`.
   - `theme:<name>` names a register theme, with source `register`.
   - Any other non-empty text is a goal the person stated, with source `stated`.
   - A `G`/`M` id that isn't open in the doc is refused: "isn't an open goal or milestone in the direction doc".

   `test_a_goal_is_read_by_its_form` fails on any form read as another, or on a struck id that is accepted.
3. **R3. A goal only narrows the candidates.** Each goal has a `scope`:
   - a milestone: its `seeds`;
   - a goal `G<n>`: every seed of the milestones whose `Serves:` names it, or `None` when no milestone does;
   - `theme:<name>`: the candidates of that theme;
   - a stated goal: `None`.

   `candidates()` keeps only the ids in a scope that isn't `None`, and never adds one. `test_a_goal_only_narrows_the_candidates` fails if, for any goal form, the candidates with the goal aren't a subset of those without it, or if `autopilot_config()`'s `guards` or `hold_causes()` change with the goal.
4. **R4. With no goal stated, the preview proposes one.** In order:
   - the first open milestone, in the doc's order, that has a candidate in its scope within the bounds;
   - else the register theme with the most candidates within the bounds (a tie goes to the theme whose best candidate ranks highest);
   - else none.

   It also lists up to three alternatives: the other open milestones and goals with a candidate in scope, and the next themes, each with its candidate count. `test_the_preview_proposes_a_goal_when_none_is_stated` fails on a different order, on a milestone with no candidate being proposed, or on a register theme being proposed while a milestone qualifies.
5. **R5. The WAIT names the goal.** `--preview` prints `goal` (`source`, `arg`, `title`, `serves`, the scope's candidate count) and `alternatives`. Its `question` begins `Run autopilot toward <arg> "<title>" (<source>) until …` and `shown` opens with a `Goal:` block: the goal, where it came from, the alternatives, and that another goal is a new `--preview`. With no goal to propose, `warnings` says "no goal: state one with --goal". Two cases are warnings and never refusals: a goal with no candidate within the bounds, and a doc `problem`. `test_autopilot_preview_writes_nothing` (extended) fails if the question or `shown` leaves out the goal, or if anything is written.
6. **R6. `--begin` fixes the goal.** It refuses, writing nothing:
   - with no `--goal`: "the bounds need a goal (--goal), the one --preview named";
   - with a `--goal` that R2 no longer resolves.

   Otherwise it writes `state["goal"]` (`source`, `arg`, `title`, `serves`, `scope`). New cases in `test_autopilot_begin_refusals` (`no goal`, `a closed milestone`) and `test_autopilot_begin_writes_the_state_once` fail otherwise.
7. **R7. The planner is given the goal.** `wave_brief()` writes `## Goal` (source, id, title, what it serves) and `Level: <n>` before the candidates, which are already narrowed by R3. `test_the_wave_brief_names_the_goal` fails if either is missing.
8. **R8. The planner's reply is a plan, and the script checks it.** The reply is groups, each a `## <the risk it lowers for the goal>` heading holding `- WAVE: <seed> — tier <1|2> — <why this order: the files it shares>` and `- WAITS: <seed> — <why>` lines. `- LEAVE: <seed> — fixed|wrong|off-goal — <what shows it>` lines may appear anywhere. The script refuses a reply if any of these holds (`read_plan()`, which replaces `read_wave()`):
   - a candidate is placed in no line, or in two;
   - a WAVE or WAITS line sits outside a group;
   - a WAVE has no tier, or a tier past `bounds.level`;
   - a WAVE, WAITS or LEAVE line has an empty reason;
   - a `fixed` or `wrong` LEAVE names no repo-relative path that exists in the main checkout;
   - a seed isn't a candidate;
   - there are more WAVE lines than the room.

   An empty wave is a reply with no WAVE line. `NONE` is retired. A refused reply is asked for once more with the refusal, as today. `test_planner_reply_is_checked_by_the_script` (extended) and `test_the_planner_places_every_candidate` fail if any of these replies is accepted.
9. **R9. A seed the planner leaves is the person's.** A LEAVE goes into `state["seeds"]` with its kind and reason, so no later wave offers it again. The run never retires it, files it or edits it: the register and the direction doc are byte for byte the same after the run. `test_a_seed_the_planner_leaves_is_left_for_the_person` fails if the seed is opened, offered again, or either file changes. `test_autopilot_end_to_end` gains the same byte checks.
10. **R10. The planner's tier and reason reach the intent-writer.** The intent brief gets `Planned: tier <n>, <group>: <reason>` after the register entry. The intent-writer's own `tier:` still decides, capped by the level as today. `test_the_intent_brief_carries_the_plan` fails if the line is missing or if the planner's tier overrides the draft's.
11. **R11. The report says what the goal got and whether the backlog grew.** At `--begin` the state records the register's entry ids (`register_ids()`: `ENTRY_RE` over the main checkout's `inbox.md`, skipping fenced lines). The summary then gives:
    - `## Goal`: the goal and its source;
    - `## The plan`: each wave's groups, and the last plan's WAITS, each with its why;
    - `## Left for you`: each `fixed` or `wrong` seed, with its reason, saying the run retired none;
    - under `## The run`: the register's count at the start and at the end, `filed` (ids at the end that weren't there at the start) and `drained` (ids gone), and the line "The register grew faster than this run drained it" when `filed > drained`.

    `summary()` gives `goal`, `plans` and `register` as data. `test_the_summary_says_whether_the_register_grew` fails on wrong counts, or on the line when `filed <= drained`. `test_summary_names_every_call_and_no_machine` still holds.
12. **R12. A run begun before this change resumes.** A state with no `goal` or `register` runs as before. The brief says `Goal: none (begun before goals)`, the scope is `None`, and the summary says the register wasn't counted. `test_a_run_begun_without_a_goal_resumes` fails on a `KeyError` or on a narrowed candidate.
13. **R13. The skill, the planner and the docs say the same thing.**
    - Step 1 of `skills/autopilot/SKILL.md` asks for a goal along with the bounds (optional). It passes `--goal` when one is named, and shows `goal` and `alternatives` with `shown`.
    - Step 3 passes the preview's `goal.arg` to `--begin`.
    - Its quoted question form matches `preview()`'s wording.
    - The `wave` part of `prompts/autopilot.md` and `agents/autopilot-planner.md` describe R8's format.
    - The factory README's *Autopilot* section names the goal, its three sources and the report's register line.

    `test_skills.py` passes unchanged, with no new `Bash(...)` rule: `--preview *` and `--begin *` cover `--goal`. `test_the_skill_quotes_the_preview_question` fails if the skill's quoted form and `preview()`'s question drift apart.

## Design

### Assumptions, each checked in the code

- Autopilot already reads the register through `sdlc.py status --json` of its own version (`status_items()`, `factory._sdlc`). `factory.py` never imports `sdlc.py`. So the direction doc reaches autopilot the same way: through `status --json`, not through a third copy of `direction_items()`.
- `next_up()` already parses the direction doc (`direction_items(_direction_text(home, cfg))`, the path from `docs.direction`). R1 only prints what it read, plus each milestone's grouped seeds resolved to ids with `ref_matches()`, which only `sdlc.py` has.
- Candidates are `next_up`'s `ready` group (`candidates()`). The milestone rule ranks only a milestone's *first* ready grouped seed. The others come up as each is opened, because `next_up` leaves out a seed an open change's `idea:` names. So a milestone goal is worked through wave by wave without widening the ready group.
- The planner has `Read, Grep, Glob` and no Write (`test_new_agents_have_no_write`). "Checks each against the code" is its reading. The script then checks only what it can check mechanically: that a `fixed`/`wrong` LEAVE cites a path that exists.
- `--preview` must write nothing and run no paid session before the WAIT, so anything it proposes is the script's work.

### The goal

`resolve_goal(arg, direction, items, bounds)` in `autopilot.py` returns `{source, arg, title, serves, scope}` or a refusal (R2, R3). `propose_goal(direction, items, bounds)` is R4's order, and returns the proposed goal and the alternatives. Both are pure over `status --json`'s data. `preview()` calls `status_items()` once (now also returning `direction`) and either resolves `--goal` or proposes one. The question and `shown` gain the goal (R5).

The goal the WAIT approved is the one `--begin` resolves again from `--goal <goal.arg>`, so a register that moves between the preview and the yes can't swap the goal under it (R6). `--begin` refuses rather than re-proposing.

`candidates(items, bounds, state, goal=None)` adds one filter after the existing ones: `if scope is not None and id not in scope: skip`. Bounds, guards, budgets and `hold_causes()` never read the goal (R3). `--seeds` and `--themes` still apply, and intersect with the scope.

### The plan

`wave_brief()` adds `## Goal` and `Level:` (R7). The `wave` prompt part (still one line) asks for R8's format. `read_plan(main, result, found, room, level)` parses the reply into groups, WAVE lines (with tier and reason), WAITS lines and LEAVE lines, and returns `(plan, problem)`.

`plan_wave()` keeps its two-try mend and returns `{"wave": [ids], "plan": plan, …}`. `apply_wave()` records the plan in `state["plans"]` and each LEAVE in `state["seeds"][id] = {"change": None, "why": "<kind>: <reason>", "left": kind}`. That entry is what keeps it out of later waves, since `candidates()` already skips ids in `state["seeds"]`. `open_seed()` writes the WAVE line's tier and reason into the intent brief (R10). Nothing in this path touches `inbox.md` or the direction doc (R9).

### The report

`--begin` stores `register: {"start": [ids]}`, from `register_ids(main)`, which uses the factory's existing `ENTRY_RE`, `INBOX` and `FENCE_RE`. `end_run()` reads the ids again. `summary()` computes `filed` and `drained` from the two sets and adds `goal`, `plans` and `register`. `write_summary()` renders R11's sections through `_placeholders()` as today. The count is the register's movement over the run window, whoever moved it: close filing a landing's held entries, the person retiring a seed, a shipped seed leaving. The summary says so.

### Edge cases

- **No direction doc, or one with no ids:** `direction` is empty, so R4 falls to a theme or to none. A stated goal always works.
- **A theme goal whose theme has no candidate within the bounds:** the preview warns. `--begin` accepts it, and the run ends at its first wave with "no candidate is left within the bounds".
- **A `G` goal with no milestone serving it:** the scope is `None`. The planner judges which candidates serve it and LEAVEs the rest as `off-goal`.
- **A resumed run with an old state:** R12.

### Boundaries

- **Always:** the goal named in the WAIT's question; the goal fixed at `--begin`; every candidate placed by the planner with its reason; a seed left with what shows it; the register's count in the report.
- **Asks first:** the goal itself. A goal other than the proposed one is a new `--preview` and the question asked again.
- **Never:** widen the bounds, the guards or `hold_causes()`; write, retire or file a register entry; edit the direction doc; run a paid session before the WAIT; let the planner write or run anything.

## Contracts touched

- **One WAIT per writing skill, its question the script's** (`test_every_wait_asks_in_a_dialog`, `test_every_wait_names_its_preview`). Autopilot keeps its one WAIT. The question is still `preview()`'s, printed and asked literally, with the goal in it, and the goal is in `shown`, which is the yes option's preview. The answers stay `(yes / no)`: a goal is chosen by a new preview, never by a dialog option, so the 2–4 answer rule holds.
- **Narrow `allowed-tools`.** No new command: `--goal` falls under the existing `autopilot --preview *` and `--begin *` rules. Bash blocks stay plain.
- **Agents that judge have no Write.** The planner keeps `Read, Grep, Glob`. The path check on a LEAVE is the script's, not a command the planner runs.
- **`factory.py` never imports `sdlc.py`; autopilot runs `sdlc.py`'s own `status --json`.** The direction doc comes through that call (R1). `status --json`'s shape is an internal contract between `sdlc.py` and the factory of the same version, pinned by R1's real-`sdlc.py` test.
- **Autopilot's bounds and `[autopilot]` are fixed at `--begin`.** The goal joins them in the state, resolved once (R6). It never widens a bound, a guard or a hold (R3).
- **`autopilot.py` is `[review] sensitive`.** This diff touches it, so ship's review goes to full depth, as it should.
- **The register is committed only by `inbox-commit` and close; the direction doc is the retrospective's.** Autopilot only reads both. R9 pins that byte for byte.
- **The scripts run on Windows.** Every new `write_text` passes `newline="\n"`. Paths a LEAVE cites are compared as repo-relative POSIX text and refused if absolute or containing `..`.
- **Nothing about a project.** Test data uses neutral seeds and themes (`drafts`), and milestones like `M1. Drafts reopen where they were left`.
- **A doc's claim made false.** The factory README's *Autopilot* section ("What it takes", the summary's contents) and the skill's description change with R13. AGENTS.md's autopilot paragraph still holds as written (budgets, limits and `enabled` fixed at `--begin`; `status --json` named as a call it runs), so no policy edit.

No invariant needs to change.

## Alternatives rejected

- **A copy of `direction_items()` in `factory.py`, pinned by a test.** It would be a third parser of the doc. Grouped seeds must also be resolved with `ref_matches()`, which would mean a fourth copy. `status --json` is already the channel autopilot reads the register through.
- **The planner suggesting goals at the preview.** It would be a paid session before the WAIT, writing its reply into the run folder before any yes. The script's suggestion (themes by candidate count) is free and repeatable.
- **Taking the direction doc's top goal without naming it in the question.** The yes would approve a goal the person never saw. The intent's Outcome asks for the yes to approve the goal.
- **Choosing the goal as the WAIT's dialog options** (`yes, toward M20` / `yes, toward M21` / …). Each option's preview would have to be its own `shown`. The 2–4 answer limit caps the alternatives, and the question would stop being one literal string from the script.
- **A plan file of its own.** The planner's reply is already filed in the run's folder. Parsing it into the state and rendering it in the summary gives the person one place to read.
- **Widening a milestone goal to every seed its `Groups:` names**, the `decide` group included. That widens what autopilot takes past 216's ready group. The milestone's seeds come up in turn anyway, as each is opened.
- **Retiring a seed the planner calls fixed or wrong, or filing a note about it.** The intent's Constraints forbid it. A model's "already fixed" is a claim for the person to check.
- **Measuring the backlog against the last retrospective's register size.** No record holds that size in a form autopilot reads without parsing retro reports, and the window wouldn't be the run's. "Filed against drained over the run" is the run's own effect, and it is measurable.
- **Several goals per run.** That brings back ranking between goals inside the run, which is the problem this change removes.
- **Keeping `NONE`.** With every candidate placed, an empty wave already says why each one waits or was left. `NONE` would say nothing.

## Verification

```bash
uv run --group dev pytest tests/test_autopilot.py -q -n auto
uv run --group dev pytest tests/test_skills.py tests/test_modules.py tests/test_feature_map.py -q -n auto
./check.sh
```

Healthy output:
- **Every new test passes:** `test_goals_come_from_the_real_status_json`, `test_a_goal_is_read_by_its_form`, `test_a_goal_only_narrows_the_candidates`, `test_the_preview_proposes_a_goal_when_none_is_stated`, `test_the_wave_brief_names_the_goal`, `test_the_planner_places_every_candidate`, `test_a_seed_the_planner_leaves_is_left_for_the_person`, `test_the_intent_brief_carries_the_plan`, `test_the_summary_says_whether_the_register_grew`, `test_a_run_begun_without_a_goal_resumes`, `test_the_skill_quotes_the_preview_question`.
- **The extended tests pass:** `test_autopilot_preview_writes_nothing`, `test_autopilot_begin_refusals`, `test_autopilot_begin_writes_the_state_once`, `test_planner_reply_is_checked_by_the_script` and `test_autopilot_end_to_end`.
- **`./check.sh` is fully green:** ruff, the format check, the whole suite and `claude plugin validate --strict`.

By hand, in this repo's main checkout (writes nothing):

```bash
uv run --quiet --script plugins/factory/scripts/factory.py autopilot --preview --usd 1 --hours 1
```

The JSON's `goal` is either an open milestone from `.sdlc/DIRECTION.md` that has a ready seed, or a `theme:` with its count. `alternatives` lists the others. `question` begins `Run autopilot toward …`. `git status` shows nothing changed. Running the same command with `--goal M999` exits non-zero with "isn't an open goal or milestone".

Grep `plugins/factory/README.md`, the skill and `agents/autopilot-planner.md` for `NONE` and "rank order", and reword any sentence still saying the planner picks by rank alone.

