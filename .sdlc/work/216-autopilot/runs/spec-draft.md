---
id: 216
slug: autopilot
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 216 — Autopilot: the factory runs from seed to landing while the person is away · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

The list is written as one change in four parts (A: the record of who decided; B: the scheduler;
C: escalations, holds and the summary; D: the risk budgets), so a split along those lines, if the
person chooses one (see the questions after the spec), moves whole parts and leaves no requirement
half in two changes. Tests named `tests/test_autopilot.py::…` are new, in a new file.

Nits taken in: none

**A. Who decided: `by=autopilot`, its run lock, and the ledger**

1. R1. `factory.py autopilot --run` holds a run lock, `AUTOPILOT_RUN_LOCK`
   (`sdlc-factory-autopilot-run.lock` in the git common dir), taken with `_try_lock()` the way
   `run_lock()` takes `TRAIN_RUN_LOCK`. It passes the lock's path to every child it starts in
   `AUTOPILOT_RUN_ENV`. A second `--run` while the lock is held is refused with
   `an autopilot --run is under way`. `test_a_second_autopilot_run_is_refused_while_one_holds_the_lock`
   fails if two loops can start.
2. R2. `land --by autopilot`, `train --begin … --by autopilot`, `answer --by autopilot` (R5) and
   `write-spec --by autopilot` (R11) are accepted only when `AUTOPILOT_RUN_ENV` names the lock file
   in this repo's git common dir and another process holds that lock now (`autopilot_running()`).
   Any other call gets the refusal `--by autopilot is autopilot's alone: no autopilot --run holds
   its lock`, and nothing is written. `test_by_autopilot_is_refused_without_the_run_lock` covers
   each of the four with the env unset, with the env set but the lock free, and with the env naming
   another repo's lock. It fails if any of the twelve cases writes.
3. R3. A change landed under autopilot carries `Sdlc-Landed: by=autopilot` on its commit
   (`land_message()`). `closing.py`'s reader, `metrics.landed_unreviewed()`, `metrics.happy()` and
   `retro.py`'s `auto_landed` each accept `autopilot` as a third value and keep it apart from both
   `auto` and `person`. `test_landed_by_autopilot_is_its_own_value` (in `tests/test_metrics.py`)
   and `test_auto_landed_counts_autopilot_apart` (in `tests/test_retro.py`) fail if
   `by=autopilot` is dropped, read as `auto`, or counted in `person`.
4. R4. `by=person`, `by=auto` and `by=autopilot` are the only values any writer emits.
   `parse_trailers` keeps whatever value it reads, and every reader that branches on the value
   names all three. `test_landed_values_are_three` greps `scripts/` and
   `plugins/factory/scripts/` for the `("auto", "person")` tuple shape and fails on one that lacks
   `"autopilot"`.
5. R5. A new `factory.py answer NNN D<k> --by autopilot` writes ` → decided by autopilot:
   <answer>` on an open ledger line (`DECIDED_AUTOPILOT`). `read_ledger()` reads such a line as
   decided (`decided_by: "autopilot"`), never as the person's (`decided_by: "person"` stays the
   only reading of ` → decided: `). `/sdlc-factory:decide` lists every autopilot-decided line under
   its own heading, so the person can overturn it. `test_autopilot_decision_is_ticked_but_never_the_persons`
   fails if `decided_by` reads `person`, or if the line still counts as open.
6. R6. No skill's `SKILL.md`, side files included, holds `by autopilot` or `--by autopilot` except
   `plugins/factory/skills/autopilot/`, and that skill's own bash blocks never pass it either (only
   the script's children do). `test_only_autopilot_names_by_autopilot` (in `tests/test_skills.py`)
   fails on any other match.
7. R7. The autopilot skill's `allowed-tools` holds only `Bash(...)` rules for the `factory.py`
   commands it runs (`config`, `autopilot --preview`, `autopilot --begin`, `autopilot --run`,
   `autopilot --cancel`, `autopilot --summary`), and no rule that matches `land`, `train`, `accept`,
   `cases`, `answer`, `write-spec`, `ship`, `close` or `run-cases`.
   `test_autopilot_grants_no_other_skills_writes` fails on such a rule.

**B. The scheduler**

8. R8. `/sdlc-factory:autopilot` asks exactly one WAIT, an `AskUserQuestion` whose question is
   `autopilot --preview`'s `question` and whose yes option's preview is its `shown`. The preview
   shows the bounds (the seeds or themes picked, the dollar cap, the hours, the level, `parallel`),
   the budgets' limits as the base branch sets them, the first candidates in rank order, and that
   every call autopilot makes is recorded as its own. Nothing is written before the yes.
   `test_every_wait_asks_in_a_dialog` and `test_every_wait_names_its_preview` cover it with no new
   rule. `test_autopilot_preview_writes_nothing` fails if `--preview` creates a file anywhere.
9. R9. `autopilot --begin` refuses, writing nothing, when the base branch's `.sdlc/factory.toml`
   has no `[autopilot]` table with `enabled = true` (read from the base branch only, like
   `[land]`), when `land.auto` is false there, when a `train --run` or another autopilot holds its
   lock, or when the bounds have no dollar cap or no hours. Otherwise it writes the run's state,
   `AUTOPILOT_STATE` (`sdlc-factory-autopilot.json` in the git common dir, never in a tree), and
   exits. `test_autopilot_begin_refusals` holds one case for each refusal.
10. R10. The run's candidates are the `ready` group of `sdlc.py status --json`'s `next_up` (the
    `READY_RULES`: Priority: high, bugs by severity, milestones, series, cheap nits), read through
    the `sdlc.py` of the factory's own version (`sdlc_path()`) and filtered by the bounds' seeds or
    themes. The `decide` group, a seed already taken by an open change (`idea:`), and a seed the
    run has held are never candidates. `test_candidates_are_the_ready_group_within_bounds` fails if
    a `decide`-group seed or a seed outside the bounds is offered.
11. R11. Each judgment goes to a fresh agent session with `Read`, `Grep` and `Glob` alone, through
    `factory.py agent`, and its reply is filed by the script. A new `autopilot-planner` picks the
    next wave (`- WAVE: <seed id>` lines, or `NONE`). A new `intent-writer` drafts an intent for one
    seed in the host's `templates/intent.md` shape, `depends_on:` included. The `spec-writer` drafts
    a Tier 2's spec, which `write-spec --by autopilot` copies byte for byte. The script refuses a
    wave naming a seed that isn't a candidate, or more seeds than `parallel` minus what is in
    flight, and the refusal counts as the planner's mend (once, as `mend` is today).
    `test_planner_reply_is_checked_by_the_script` fails if an unknown or excess seed is opened.
    `test_new_agents_have_no_write` (beside the existing agent-tools test) fails if either new
    agent lists a writing tool.
12. R12. For each seed in a wave, the loop runs `sdlc.py new` (of its own version) with
    `--worktree` at the tier the intent-writer proposes, writes the filed draft as `intent.md` in
    the change's worktree, stamps `idea: <seed id>` and `opened_by: autopilot` in its frontmatter
    by line edits (never `frontmatter.dumps()`), and records the call in the change's
    `runs/autopilot.md`. `vet` accepts `opened_by: autopilot`, and `status`/`board` show the change
    as autopilot's. `test_opened_intent_says_autopilot_opened_it` fails if the key is missing, or if
    `id:` is rewritten (`012` stays `012`).
13. R13. A change is built only once every `depends_on:` change has a `Close` commit on the base
    branch (`closed_changes()`'s reading, through `sdlc.py`'s own command). Until then it waits at
    `stage: plan`, and the summary says it waits and on what.
    `test_a_change_waits_for_what_it_depends_on` fails if the build starts before the dependency's
    `Close` commit.
14. R14. The build loop is the script's: `autopilot_build_step()` maps `verdicts`' `next` to the
    same `factory.py` commands the build skill runs (`agent --task build|fix|review|arbitrate|rework|approve|mend`,
    `gate`, `snapshot`, `decisions`, `carry`), each as a subprocess under `AUTOPILOT_RUN_ENV`. At
    most `parallel` changes take a step at once. `next: stop` holds the change (R19), and
    `decide`/`approve` with open calls go to R17. `test_build_step_runs_only_the_named_commands`
    fails if a step runs a command outside `AUTOPILOT_STEPS`, a fixed table like `RUN_STEPS`.
15. R15. Landing: when no landing train is under way, and either the ready changes reach
    `land.batch` or no change still building is at its last round or `approve` (or one has been
    there longer than `[autopilot] wait`, 30 minutes by default), the loop runs
    `land-check` on the ready changes, then `train --begin <batch> --by autopilot` and `train --run`
    as subprocesses. A change `land-check` excludes, or one held by R19, is not in the batch. A
    train stop the loop can't take is ended with `train --stop`, which puts every change that
    hasn't landed back, and those changes are held. `test_landing_waits_for_a_nearly_ready_change`
    fails if a batch begins while a change sits at `approve` inside the wait, and
    `test_landing_does_not_wait_past_the_wait` fails if it waits longer.
16. R16. `autopilot --cancel` writes `AUTOPILOT_CANCEL` in the git common dir. The loop reads it
    between steps, lets the step in flight end, starts nothing more, and writes the summary (R22).
    A `train --run` it started is cancelled the same way (`train --cancel`). A rerun of `--run`
    resumes from `AUTOPILOT_STATE`. `test_cancel_stops_between_steps_and_a_rerun_resumes` fails if
    a new step starts after the cancel, or if the rerun opens a seed a second time.

**C. Escalations, holds and the summary**

17. R17. No WAIT stops the run. An open default is answered `answer D<k> --by autopilot` with
    `KEPT_ANSWER`, and a `look` with `seen`. A blocking decision is answered with the first
    `- OPTION:` its raiser recommended, or held when it has none. Each call is appended to the
    run's `escalations.md` with its change, its id, its text, its options and why, and the answer.
    The approver is then run again (`agent --task approve`), so a READY reads the answered ledger.
    `test_escalations_are_answered_as_defaults_and_recorded` fails if an answer is written as
    ` → decided: ` or if `escalations.md` lacks it.
18. R18. An answer of `upgrade to Tier 2` is never given by autopilot. A blocking decision whose
    recommended option is `upgrade to Tier 2` is held. `test_autopilot_never_upgrades` fails if
    `factory.py upgrade` runs under the lock.
19. R19. A change is **held** (left unlanded at its stage, shown under Needs you, nothing that
    depends on it built, the cause in `runs/autopilot.md` and the summary) when any of these is
    true:
    - the diff touches a path in the base branch's `[autopilot] guards` (default: `docs.policy`,
      `docs.review`, and the paths in `[review] irreversible`);
    - any agent's reply in its run holds `- CONTRACT: <invariant>: <why>` (it can only be built by
      breaking one) or `- RELAX: <invariant>: <why>` (it would be far simpler with one relaxed);
    - the approver ESCALATEs with `## Reconsider the approach` (rounds out, stuck, untestable), or
      with a `gate` reason;
    - `verdicts` names `stop`;
    - `land-check` excludes it;
    - its `checks.md` holds a command `read_only_command()` refuses;
    - skills' cases are in its scope.

    A held change's dependents stay at `stage: plan`. `test_held_change_and_its_dependents_never_land`
    holds one case per cause and fails if the change, or a change depending on it, lands or builds.
20. R20. The spec-writer's, builder's and approver's prompts (`prompts/spec.md`, `build.md`,
    `approve.md`) gain the `- CONTRACT:` and `- RELAX:` lines as a part of their own, sent only
    under autopilot (`${autopilot}` filled), naming the policy doc. `test_prompt_parts_match` (the
    existing parts check) fails if a part and its placeholder disagree.
21. R21. Acceptance checks run unattended only when every command passes `read_only_command()`,
    through `accept`. Any other check holds the change (R19), and `cases` and `run-cases` never run
    under the lock. `test_autopilot_runs_no_paid_or_unlisted_command` fails if `run-cases` runs, or
    if `accept` runs a command the read-only list refuses.
22. R22. When the run ends (no candidate left and nothing in flight, the planner's `NONE`, the
    dollar cap, the hours, a risk budget reached, or a cancel), `autopilot` writes
    `.sdlc/reports/autopilot/<started>/summary.md` with `escalations.md` beside it. The summary
    holds:
    - how long the run took and what it cost (from each change's `runs/costs.jsonl` plus the
      planner's and intent-writer's sessions);
    - what landed (by its `Close` commit), what is mid-build and at which stage and worktree, and
      what is held and why;
    - every call autopilot made;
    - each budget, its limit, what it spent and on what;
    - the risks to weigh: each landed change's signals.

    Every path in it is repo-relative, and it is filed through the same defusing the records use
    (`defuse`), so it names no machine and no host. `test_summary_names_every_call_and_no_machine`
    fails if a call is missing, or if a home path survives.
23. R23. Nothing autopilot writes in a change's folder (`runs/autopilot.md`, the ledger's
    `→ decided by autopilot:` lines, `opened_by:`) is a person's record. `findings.md` gains no
    `By:` value for autopilot, and `Sdlc-Findings` counts nothing of it.
    `test_the_trailer_never_counts_an_agent_finding` stays green, and
    `test_autopilot_records_are_never_the_persons` fails if a metrics reader counts an autopilot
    call as an override or a person's decision.

**D. The risk budgets**

24. R24. Review debt is the sum, over the run's calls, of `[autopilot.debt]` weights by kind:
    `default` 1, `look` 2, `blocking` 3, `spec` 2 (a spec copied unseen), `intent` 1 (an intent
    opened). Its limit is `[autopilot] debt`, 40 by default. The script counts it from
    `escalations.md` and the state, and no model judges it. `test_review_debt_is_counted_by_kind`
    fails if a weight is ignored or a call is counted twice.
25. R25. `land_signals()` also returns each signal's kind (`sensitive`, `irreversible`, `issue`,
    `impact`, `escalated`, `open`, `assumed`, `settled`, `resolved`, `fixed`, `unreviewed`,
    `auto_off`, `undone`, `checks`, `cases`, `nits`), in the order of its strings, and
    `land-check` prints them as `signal_kinds`. `test_every_signal_has_a_kind` fails if a string
    comes without its kind, or if a kind is not in `SIGNAL_KINDS`.
26. R26. Change risk is computed over the landed changes: for each, the sum of `[autopilot.risk]`
    weights over its signal kinds (default: `sensitive` 3, `impact` 3 for major, `escalated` 3,
    `resolved` 2, `fixed` 2, `unreviewed` 2, `issue` 2, every other kind 1), multiplied by
    `pushed` (2) when its close pushed, else 1, and by `stacked` (1.5) when its train held more than
    one change. The products are summed, and the limit is `[autopilot] risk`, 30 by default.
    `test_change_risk_weighs_pushed_and_stacked` fails if either factor is ignored.
27. R27. Once either budget reaches its limit, or the dollar cap or the hours run out, nothing new
    starts: no wave, no intent, no build round, no train. A build already in flight is taken on to
    `stage: test` and left there unlanded. A train already under way is cancelled between steps,
    and the changes it hasn't landed are put back. The budgets are checked before every step.
    `test_a_spent_budget_starts_nothing_and_lands_nothing_more` fails if a step starts, or a change
    lands, after the limit.
28. R28. Every weight, limit, `guards`, `parallel`, `wait` and `enabled` is read from the base
    branch's `.sdlc/factory.toml` only (`_base_factory_config()`, as `[land]` is), and its value is
    fixed in `AUTOPILOT_STATE` at `--begin`. A change in flight can't loosen the run it's in.
    `test_autopilot_config_is_read_from_the_base_branch` fails if a change's own `factory.toml`
    raises a limit.

## Design

**Assumptions, checked in the code.** The factory already has every piece the scheduler calls:

- the build loop's one reading (`run_state.loop_state()`, printed by `verdicts`);
- the agent runner (`factory.py agent`, the one place it runs `claude`);
- the gate (`_run_check()`);
- the landing train with an unattended loop (`landing._run_loop()`, `RUN_STEPS`, `run_lock()`,
  `TRAIN_CANCEL`);
- the risk signals (`land_signals()`);
- the read-only check list (`read_only_command()`);
- the ledger (`read_ledger()`, `DECIDED`, `SETTLED`);
- the costs (`runs/costs.jsonl`).

`sdlc.py` already ranks the register (`next_up()`, `NEXT_RULES`, `READY_RULES`). What is missing
is a loop that drives the build steps without the person's session, a third `by` value, and the
budgets. The design adds those and changes no existing WAIT.

**A new module, `plugins/factory/scripts/autopilot.py`.** It is loaded by path and bound to a live
view of `factory.py`'s names, as `landing.py` and `run_state.py` are, so `[review] sensitive` can
name it and `tests/test_modules.py`'s placement rule covers it. It owns:

- `cmd_autopilot()` and its `--preview`, `--begin`, `--run`, `--cancel` and `--summary` modes;
- `AUTOPILOT_STATE`, `AUTOPILOT_RUN_LOCK`, `AUTOPILOT_CANCEL` and `AUTOPILOT_RUN_ENV`;
- `AUTOPILOT_STEPS`;
- the budgets (`review_debt()`, `change_risk()`);
- `holds()`;
- the summary.

`factory.py` keeps the constants other modules read and gains `answer` (R5), `--by autopilot` on
`land`, `train` and `write-spec` (R2), and `autopilot_running()`, which `landing.py` calls.

**The state** (`sdlc-factory-autopilot.json`, in the git common dir, beside `TRAIN_STATE`) holds:

- the bounds as approved;
- the config fixed at `--begin` (R28);
- the start time;
- each wave's seeds;
- each change autopilot opened and its place (`waiting`, `building`, `ready`, `landing`, `landed`,
  `held` and why);
- the calls it made;
- the budgets' running sums;
- the agent sessions it ran outside any change (the planner's, and the intent-writer's before the
  change exists).

Each step writes the state before it acts and after it ends, so a killed or compacted session
loses at most the step in flight, which the next `--run` reads again from the change's own files.
Opening a seed is keyed by the seed id in the state *and* by an open change's `idea:` line, so a
rerun never opens a seed twice (R16).

**The loop** (`--run`, under `AUTOPILOT_RUN_LOCK`). Each pass:

1. Reads the cancel file, then the clock, the dollar total and both budgets (R27).
2. For each change in flight, at most `parallel` at once, takes one step:
   - a change still `waiting` is checked for its dependencies (R13);
   - a building change gets its step from `verdicts` (R14);
   - a `decide`, or an approve that left open calls, is answered (R17);
   - `next: stop` is a hold (R19).
   Each step's commands run as subprocesses of `factory.py`, the way `_run_group()` starts them, so
   one slow builder doesn't block another change's gate.
3. If the budgets allow and fewer than `parallel` changes are in flight, asks the planner for the
   next wave (R11), and opens each seed (R12), spec first for a Tier 2 (spec-writer, then
   `write-spec --by autopilot`).
4. If the landing rule holds (R15), lands a batch through the existing train, `train --run` as its
   own subprocess. The autopilot loop doesn't re-implement the train; it reads the train's exit
   JSON (`_run_end()`) and maps a stop to holds.
5. Stops when there's nothing in flight and no candidate, or on any of R22's ends.

The same step named twice with nothing changed holds the change, as `_run_loop()` guards itself.

**How a change is judged ready to land under autopilot.** `land-check`'s `clear` is ignored. A
change with signals still lands, as `by=autopilot`, because spending risk is the point of the
mode. The risk is paid out of the change-risk budget instead. What never lands is R19's holds,
plus what `land-check` excludes, plus anything once a budget is spent.

**What the person's later review reads.** Each change keeps `runs/autopilot.md`, committed with
it: each call, each hold and the run's id. The ledger keeps the `→ decided by autopilot:` lines,
which `/sdlc-factory:decide` lists. Per run, `.sdlc/reports/autopilot/<started>/` (a folder that
ignores itself) holds `escalations.md` and `summary.md`. A call the person disagrees with is fixed
forward, by a revert or a new seed through `/sdlc:idea`. The summary ends with that line, and
autopilot never edits a landed change.

**Pushing and issues** (open question 3): autopilot passes nothing new to `close`. Its landings
push exactly as `git.push` already says for `/sdlc-factory:land`, through `closing._push()`. If
the person chooses to keep autopilot local, the change adds a `--no-push` to `land --close` and
`sdlc.py close` that can only remove a push. Change risk weighs a pushed landing double either way
(R26). `new` opens an issue in a GitHub-numbered repo because the number needs one, and its body
is `render_issue()`'s as for any change. Autopilot runs no `sync`.

**The skill** (`plugins/factory/skills/autopilot/SKILL.md`):

1. Runs `factory.py config` (and names the `READS_CONFIG` keys).
2. Asks the person for the bounds in plain text, then runs `autopilot --preview` with them.
3. Asks its one WAIT, with `--preview`'s question and preview.
4. On the yes, runs `autopilot --begin` with the same bounds.
5. Starts `autopilot --run` in the background and ends its turn.

A rerun of the skill while a run is under way shows `--summary` (read-only) and offers
`autopilot --cancel`. That's a second command, not a second WAIT: cancelling writes only the
cancel file, the same class as `train --cancel`.

**Docs.** The factory README gets an *Autopilot* section: what it does, the holds, the budgets,
the config table, the files. REFERENCE.md gets `[autopilot]` and `Sdlc-Landed: by=autopilot`.
FEATURES.md gets the skill and command (`tests/test_feature_map.py`). AGENTS.md's factory
paragraph gets the new module, the run lock, `by=autopilot` and the rule that only autopilot's
children may pass it.

## Contracts touched

- **One WAIT per writing skill, approval per invocation.** The new skill has exactly one WAIT, in
  a dialog with its preview. Its yes approves one bounded run, not a standing permission: the
  state is fixed at `--begin` and ends with the run. **This needs the person's explicit decision.**
  Today a factory spec is never built on before the person approves it (README, *The approvals*;
  `write-spec` after the build WAIT). Under autopilot, a spec and an intent are written and built
  on with only the run's yes. The design keeps that inside the mode (`write-spec --by autopilot`,
  lock-gated, counted as review debt), but it changes a promise the factory README states, and
  AGENTS.md should say so in the same change.
- **No other WAIT loosens.** No skill but autopilot's names `by autopilot` (R6). The flag is
  refused without the lock (R2). `allowed-tools` grants nothing new to another skill (R7).
  `/sdlc:intent`, the build skill and `/sdlc-factory:land` are unchanged.
- **Narrow `allowed-tools`.** Each command the skill runs has its own rule. There is no plain
  `Bash` and no rule for a writing command the skill doesn't run itself.
- **Only the named steps push.** Autopilot runs no `git push`. Any push is `close`'s `_push()`
  through `land --close`, under `git.push`, as `/sdlc-factory:land` does today. An optional
  `--no-push` would only narrow.
- **`Sdlc-Landed` and the metrics trailer contract.** The design extends it with a third value and
  redefines nothing (R3, R4). `metrics.py`'s docstring gets the value. **This is a policy edit to
  a stated contract** (AGENTS.md, *Writes before a WAIT* and the factory paragraph both say
  "`by=auto`, never as the person's"). The new value follows that rule, but AGENTS.md has to name it.
- **`land.auto`.** Autopilot refuses to begin when it's off (R9), so a host that turned it off
  never gets unattended landing by another door.
- **`[review] sensitive` and every limit read from the base branch.** `[autopilot]` is read like
  `[land]` (R28). Depth and signals still come from `risk_paths()`.
- **Writes before a WAIT.** Autopilot writes nothing before its WAIT. `--preview` is read-only
  (R8). The state, lock and cancel files are state in the git common dir like `TRAIN_STATE`, and
  are written only after the yes.
- **Intake.** `new` opens an issue under GitHub numbering exactly as it does for a person's
  intent, and the record is still committed before the issue is told. Autopilot adds no `sync`.
- **The factory never imports `sdlc.py`.** It runs `sdlc.py` of its own version for `new`,
  `status --json` and the `Close`-commit reading, which **widens** "for `fresh`, `upgrade` and
  landing alone" in AGENTS.md and the factory README. The design says so there.
- **Agents that judge have no Write; no agent commits.** The planner and intent-writer have
  `Read`, `Grep` and `Glob` only (R11). The script files every reply.
- **Frontmatter edited in place.** `opened_by:` and `idea:` are written by line edits (R12).
- **Nothing names a host or a machine; nothing public names the agent.** The summary and records
  go through `defuse` (R22). `by=autopilot` names the plugin's mode, not a model, and commits stay
  the repo owner's with only `Sdlc-*` trailers.
- **The scripts run on Windows.** The lock goes through `_try_lock()` (no top-level `fcntl`), text
  writes pass `newline="\n"`, and subprocesses name `encoding="utf-8"`.
- **No agent but the builder runs `checks.md`.** Autopilot runs checks only through `accept`, a
  script command, and only read-only ones (R21). No agent runs them.

## Alternatives rejected

- **A flag or env that turns every WAIT into a yes.** It's the one thing the intent rules out, and
  it would make every other skill's approval forgeable by one setting.
- **Reusing `by=auto`.** `auto` means "no risk signal, so no person was needed". Autopilot lands
  changes *with* signals, and folding the two would make the retrospective's auto-land share lie.
- **Running the scheduler in the skill's session.** Compaction or a closed terminal would lose the
  queue. The train's lesson (`TRAIN_STATE`, `train --run`) applies: state in the common dir, loop
  in a subprocess.
- **A model judging the risk budgets, or "breaks a contract", alone.** Budgets must be the
  script's. For contracts, the script draws the line on paths (`guards`) and on reply lines it
  reads (`- CONTRACT:`, `- RELAX:`). A model's claim can add a hold but never remove one.
- **Autopilot answering a blocking decision with its own judgment** (a "deciding" agent). The
  recommendation the raiser gave is already on record. A second model choosing would be an
  unrecorded opinion, and a blocking with no recommendation is the person's, so it's held.
- **Running paid cases, or `accept` on any check, unattended.** Each is behind the harness's own
  prompt today, and allowing it would loosen a wait the intent keeps.
- **Fixing a disagreed call mid-build.** The intent says fix forward. A mid-build edit would race
  the loop and leave the record saying something the code doesn't.
- **One long-lived "supervisor" agent session.** It would hold the queue in a context that
  compacts, and it would need Write. Fresh sessions with filed replies keep every judgment
  auditable.

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_autopilot.py
uv run --group dev pytest -q tests/test_skills.py tests/test_train.py tests/test_land.py \
  tests/test_metrics.py tests/test_retro.py tests/test_modules.py tests/test_feature_map.py
uv run --group dev pytest -q -m portable
```

Healthy output: `check.sh` ends green (ruff clean, pytest all passed, `claude plugin validate
--strict` OK). Every `tests/test_autopilot.py` test named in R1–R28 passes. The existing train,
land and metrics tests pass unchanged, which shows `by=auto` and `by=person` read as before.

A dry run in a scratch repo built by `tests/train_driver.py`, with a fake `claude` that files
canned replies and two seeds (one depending on the other), shows:

- `--preview` writes nothing;
- `--begin` refuses without `[autopilot] enabled = true`;
- `--run` opens both seeds, builds the second only after the first's `Close` commit, lands both
  with `Sdlc-Landed: by=autopilot`, and writes a summary naming both and the calls made;
- with `debt = 1`, it opens one seed, lands nothing past the limit, and leaves the build at
  `stage: test`.

`test_autopilot_end_to_end` is that run.

