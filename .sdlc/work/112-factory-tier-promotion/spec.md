---
id: 112
slug: factory-tier-promotion
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 112 — Promote a change to Tier 2 in the middle of a factory run · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

The intent calls this a *promotion*. The code and the docs call it an **upgrade**, because
"promote" also means moving a build from one environment to the next (dev, qa, prod). Every name
below uses that word: the command, the step, the record and the answer's prefix.

1. **R1.** `sdlc.py upgrade <id>`, run in the change's own checkout on a Tier 1 change at
   `stage: plan` or `stage: build`, sets `tier: 2`, `stage: plan` and `updated: <today>` by editing
   those frontmatter lines in place. Every other byte of `intent.md` stays the same. It writes
   `spec.md` and `plan.md` from `template_path()` with `new`'s substitutions, but only when they
   are missing: a file that exists is never written over, and is listed as `kept`. It prints JSON:
   `change`, `tier`, `stage`, `created`, `kept`. Pinned by
   `test_upgrade_sets_tier_and_stage_by_line`, `test_upgrade_scaffolds_only_what_is_missing` and
   `test_upgrade_leaves_check_strict_clean` (`tests/test_sdlc.py`). Each fails if a key is
   reordered, `id: 012` is rewritten, an existing `plan.md` changes, or `check --strict` reports
   the folder.
2. **R2.** `sdlc.py upgrade` refuses, writing nothing, in four cases: a change already at Tier 2, a
   Tier 1 change at any stage but `plan` or `build`, an id `names_change()` doesn't match to this
   checkout's branch, or the base branch (`trunk_refusal()`). Pinned by
   `test_upgrade_refuses_and_writes_nothing`, one parametrised case each.
3. **R3.** An **upgrade answer** is a ticked, decided, blocking line in `decisions.md` (not
   superseded) whose answer after ` → decided: ` starts with `upgrade to Tier 2`, in any case. When
   one exists on a Tier 1 change that has no upgrade record, `verdicts` names `upgrade` next and
   gives the line's id as `upgrading`. An open line, a default, or a superseded line is never an
   upgrade answer. Pinned by `test_verdicts_names_upgrade_on_an_upgrade_answer` and
   `test_only_a_decided_blocking_answer_upgrades`.
4. **R4.** `factory.py upgrade <NNN>` refuses unless `verdicts` names `upgrade`. When it does, it
   writes `build/round-<P>.upgraded.md` with one line, `UPGRADED: D<n>`. `P` is one past the
   newest round built or reviewed. It then runs `sdlc.py upgrade` of its own version (`_sdlc()`)
   and prints `change`, `round`, `decision`, `tier`, `stage`, `created` and `kept`. It commits
   nothing, and `HEAD` doesn't move. If a run stops after the record is written but before the
   tier is set, a rerun finishes the upgrade and writes no second record. Pinned by
   `test_upgrade_writes_the_record_then_the_tier`, `test_upgrade_moves_no_head` and
   `test_an_upgrade_cut_short_finishes_on_rerun` (`tests/test_factory.py`).
5. **R5.** A change is upgraded once, and only upward. Once a `.upgraded.md` record exists,
   `verdicts` never names `upgrade` again, even for a later upgrade answer, and
   `factory.py upgrade` refuses. There is no downgrade command. Pinned by
   `test_no_second_upgrade`.
6. **R6.** On an upgraded change whose round `P` has no builder report yet, `verdicts` names `spec`
   at round `P` while the stage isn't `build`, with `written` true once `spec.md` is no longer its
   scaffold. At `stage: build` it names `build` at round `P`. The run's rounds count again from `P`,
   as from a restart: `limit` is `P - 1 + rounds`, `exhausted` is counted from `P`, and `depth()`
   counts each round's place from `P`. Pinned by `test_an_upgraded_run_specs_then_builds_round_p`
   and `test_an_upgraded_run_counts_its_rounds_from_p`.
7. **R7.** `agent --task spec` on an upgraded change adds to the spec-writer's prompt the round it
   was upgraded at, the decision's question and the person's answer, and that the build so far is
   in the worktree. The reply still goes only to `runs/spec-draft.md` and
   `runs/spec-questions.md`, and `spec.md` stays its scaffold until `write-spec`. Pinned by
   `test_the_spec_prompt_names_the_upgrade`.
8. **R8.** `agent --task build` at round `P` of an upgraded run resumes the builder's last session
   (`--resume`, not a new `--session-id`). The prompt names the decision and its answer, says the
   change is now Tier 2 with an approved `spec.md`, and asks the builder to rewrite `plan.md`
   against it first, keeping what still holds, then to build test first. The report goes to
   `build/round-<P>.md`, written new and never added to an earlier report. Pinned by
   `test_the_upgraded_build_resumes_the_builder_into_round_p`.
9. **R9.** `agent --task decided` refuses in two cases: the upgrading decision, and any decision
   while `verdicts` names `upgrade` or `spec`, or `build` at an upgraded round. Pinned by
   `test_decided_refuses_while_an_upgrade_is_under_way`.
10. **R10.** The prompt of a reviewer reviewing round `P` says the change was upgraded to Tier 2
    before that round, and that it is reviewed against `spec.md`. The approver's prompt on an
    upgraded run says the same, naming `P` and the decision. Pinned by
    `test_reviewers_and_approver_are_told_of_the_upgrade`.
11. **R11.** `start` reports `upgraded` (`round`, `decision`, `answer`) for an upgraded change, and
    `null` otherwise. `fresh` returns `held` for an upgraded run at any stage and moves nothing,
    since its earlier rounds were gated on the base they had. Pinned by
    `test_start_reports_an_upgrade` and `test_fresh_holds_an_upgraded_run`.
12. **R12.** `check --strict` passes at every stage an upgraded run leaves the change at:
    - Tier 2 at `plan` after `upgrade`.
    - `design` after `write-spec`.
    - `build` while round `P`'s builder is live and `plan.md` is still its scaffold.

    "Live" extends `factory_first_build()`: a `.upgraded.md` record for `P`, no
    `build/round-<P>.md`, no `runs/stopped.md`, and `runs/step.md` naming `build` at round `P`,
    written less than `FACTORY_AGENT_TIMEOUT` ago. Once the build isn't live, the scaffold is a
    problem again. Pinned by `test_check_leaves_out_the_template_plan_during_a_live_upgraded_build`
    and `test_the_template_plan_shows_once_the_upgraded_build_is_not_live`, beside 105's R10 tests.
    The record's file pattern copied into `sdlc.py` is pinned to `factory.py`'s.
13. **R13.** `verdicts --record` writes `AFTER:` on an `upgrade` or `spec` reading as it does on
    `decide`: the step the run paused at. The board's step track shows all three paused at that
    step, not dropping the track. Its copy of the paused steps is pinned by `tests/test_board.py`
    (`test_an_upgrade_pauses_the_step_track`).
14. **R14.** The build skill names what the supervisor does at `upgrade` and at `spec`:
    - At `decide`, an answer that upgrades is written starting `upgrade to Tier 2`, and `decided`
      isn't run for it.
    - `upgrade` runs `factory.py upgrade`.
    - `spec` drafts through Step 1 and asks Step 2's question in its upgraded form, then Step 3's
      `write-spec` and stages, running only the stage moves still owed when `written`.

    The skill keeps exactly one `WAIT` heading, and a `Bash(...)` rule for `factory.py upgrade`.
    Pinned by the existing `tests/test_skills.py` and a new
    `test_the_build_skill_handles_every_step_verdicts_names`, which fails when a step `verdicts` can
    return has no bullet in the skill.
15. **R15.** `agents/builder.md` says how a Tier 1 builder raises an upgrade: a `[blocking]`
    decision whose options include `upgrade to Tier 2`, raised where the tree still works. The
    factory README, `factory.py`'s docstring and AGENTS.md's factory paragraph describe the upgrade
    and the `sdlc.py upgrade` call. `docs/REFERENCE.md` lists `sdlc.py upgrade`. None of them calls
    it a promotion.

## Design

### What I took as given, and checked

- A Tier 1 folder holds only `intent.md`. `new` writes `TIER_ARTIFACTS[tier]` from
  `template_path()`, which is the host's `.sdlc/templates/`, else the plugin's (`sdlc.py`'s
  `cmd_new`). So an upgrade has to write `spec.md` and `plan.md`, and `write-spec` refuses when
  there is no `spec.md` scaffold (`cmd_write_spec`, `except OSError: written = True`).
- `check` asks for a filled `spec.md` from `design` onwards and a filled `plan.md` from `build`
  (`SPEC_REQUIRED_FROM`, `PLAN_REQUIRED_FROM`). The only exception is a live first factory build
  (`factory_first_build()`). A Tier 1 change set to `tier: 2` at `stage: build` therefore fails
  `check --strict` straight away. That is why an upgrade moves the stage to `plan`.
- `write-spec` and `start --for spec` accept only a Tier 2 change at `stage: plan` (`STARTS`). An
  upgrade lands the change exactly there, so both work unchanged.
- The escalation restart already has the round machinery an upgrade needs: a record beside the
  round files, a new run's first round, and the limit and depth counted from it (`restart_state()`,
  `read_restarts()`, `loop_state()`'s `first`, `depth()`'s `starts`). Every reader that globs
  `build/round-*.md` or `round-*` filters on a numeric stem, so `round-<P>.upgraded.md` is never
  counted as a round. This covers `build_round()`, `raised_decisions()`, the board's `_built`, and
  `read_restarts()`'s suffix.
- The model and the light depth's reviewers follow `intent.md`'s tier at each call (`model_for()`,
  `light_reviewers()`, `change_tier()`). After an upgrade they become Tier 2's without further
  change.
- No command, key or text in the repo uses "upgrade" yet (searched), so the new name collides with
  nothing.

### The path

1. **The builder raises it.** A Tier 1 builder that finds the change needs a spec raises
   `- DECISION: [blocking] Upgrade to Tier 2? <why>. Options: upgrade to Tier 2; <the narrower
   Tier 1 it could stay>. Recommend …`. A reviewer may raise one too. `verdicts` says `decide`.
2. **The person answers it.** The supervisor asks, as at any `decide`. If the person chooses or
   types the upgrade, the supervisor ticks the line `→ decided: upgrade to Tier 2[: their words]`
   and doesn't run `decided`. That answer is the only thing that makes the upgrade the person's
   call. Neither the builder's wording nor the supervisor's reading decides it.
3. **`verdicts` → `upgrade`.** The supervisor runs `factory.py upgrade NNN`. It writes the record
   first, then has `sdlc.py upgrade` set `tier: 2` and `stage: plan` and add the scaffolds. Writing
   the record first is what lets a rerun after a stop finish the upgrade (R4).
4. **`verdicts` → `spec` at round `P`.** The supervisor goes back to Step 1 and starts
   `agent --task spec`. The prompt names the upgrade, and the draft lands in `runs/`. Step 2 then
   asks the question in its upgraded form:

   > `Write this spec and carry on NNN-<slug>'s factory run as Tier 2: the builder, resumed,
   > rewrites plan.md against it and builds round <P>, the base branch's gate <command> runs on
   > each build before any reviewer (up to 2 fixes a round), <reviewers> review it in up to
   > <rounds> more rounds (…), a verifier checks each round's changes, the approver decides, at
   > most <max_runs> more agent runs, agents in <mode>, all left uncommitted at stage: test? (yes /
   > revise a requirement / no)`

   It is the same `WAIT` heading, with a fourth wording beside the existing three.
   - On a yes, Step 3 runs `write-spec`, `stage design` and `stage build`.
   - On a no, the change stays Tier 2 at `plan`, which is `check`-clean. The person can come back
     with `/sdlc-factory:build`, `/sdlc-factory:spec` or `/sdlc:spec`.
5. **`verdicts` → `build` at round `P`.** `agent --task build` resumes the builder (R8). Round `P`
   is then gated, reviewed, verified and approved like any round, with the limit counted from `P`.

### Pieces and what each owns

- **`sdlc.py upgrade`** (new; `cmd_upgrade()`). It owns the tier, the stage and the scaffolds, so
  rendering a template stays in one place: `new`'s substitution moves into a helper both commands
  call. The title comes from `intent.md`'s `# NNN — TITLE` line, or the slug de-hyphenated. Lines
  are edited the way `stamp_shipped` does it.
- **`factory.py`.** It owns the decision and the record:
  - `UPGRADED_RE`, `UPGRADE_ANSWER_RE` and `read_upgrade(folder)`, which returns `round`,
    `decision`, `answer`, or a problem.
  - `upgrade_answer(ledger)`.
  - `cmd_upgrade()`.
  - The `upgrade` and `spec` branches in `loop_state()`, placed after `decide` and before
    `done`/`restart`/`build`.
  - `first = max(restart round, upgrade round)`.
  - The upgrade round added to `depth()`'s `starts`.
  - The prompt additions in `_task()`.
  - The `--resume` condition in `cmd_agent()`.
  - `start`'s `upgraded` and `fresh`'s `held` for an upgraded run.
  - `_record_step()`'s `AFTER:` for `PAUSES = ("decide", "upgrade", "spec")`.

  `upgrade` gets no `TASK_STEP` entry, because it isn't an agent task: it is a command, and it
  checks `verdicts` itself.
- **A record that won't read is a stop.** This covers a `.upgraded.md` that doesn't open with
  `UPGRADED: D<n>`, or names a line that isn't a decided upgrade answer. It mirrors
  `test_a_bad_restart_record_stops_the_run` and is a `rerun` stop.
- **`sdlc.py`'s `factory_first_build()`.** It gains the upgraded-round case (R12), with its own
  copy of the record's file pattern, pinned.
- **`board.py`.** It gains `PAUSES`, a copy pinned by `tests/test_board.py`. The card's tier
  already comes from the frontmatter, so it shows 2.

### Edge cases

- **A blocking decision raised in an unreviewed round `R`.** This is the usual case. `P = R + 1`,
  so round `R` is never reviewed on its own, and round `P`'s review reads the whole diff, `R`'s
  work included. No build reaches the approver unreviewed.
- **Several blocking decisions answered in one dialog, one of them upgrading.** The others stay
  ticked in the ledger, which the builder reads as settled. `decided` refuses while the upgrade is
  under way (R9), so the builder is never resumed on the Tier 1 path in between.
- **A filled `plan.md` already exists** because the Tier 1 builder wrote one. `upgrade` keeps it,
  and the builder rewrites it against the spec in round `P`.
- **A change at `stage: test`** (escalated) isn't upgraded. A restart covers it, and both
  `sdlc.py upgrade` and `factory.py upgrade` refuse.

### Boundaries

- **Always:** the upgrade follows the person's answer. The spec waits for its own question, and the
  change is `check --strict`-clean at every stage the run leaves it at.
- **Ask first:** nothing new. The `decide` dialog and Step 2's question are the two asks.
- **Never:** `factory.py` writes `spec.md` (only `write-spec`, after the yes). An agent reply is
  patched. A change is upgraded twice, or downgraded. Anything is committed.

## Contracts touched

- **Mechanism vs judgment.** Every step of the upgrade is named by `verdicts` from the ledger and
  the record (`upgrade`, `spec`, `build` at `P`). The script also detects the answer, by its
  `upgrade to Tier 2` prefix, so the supervisor makes no move of its own. The tier, the stage and
  the scaffolds are written by scripts, never by a skill's bash.
- **Frontmatter edited by line, never round-tripped** (the `stamp_shipped` rule). `sdlc.py upgrade`
  edits the `tier:`, `stage:` and `updated:` lines in place, and R1's test pins `id` and the key
  order.
- **The factory never imports `sdlc.py`; landing and `fresh` run it through `sdlc_path()`.**
  `factory.py upgrade` runs `sdlc.py upgrade` the same way (`_sdlc()`, same version or refused).
  **This adds a third place the factory runs `sdlc.py`, and AGENTS.md's factory paragraph has to
  say so.** It is an edit to the policy doc's map, made in this change. The alternative, a second
  copy of template rendering inside the factory, is rejected below.
- **`sdlc` reads the factory's files with copies, pinned by tests.** The record's file pattern
  (`sdlc.py`) and `PAUSES` (`board.py`) are new copies, each pinned.
- **Agents that judge have no Write; only the builder edits; no agent commits.** No agent writes the
  record, the tier or the spec. The spec-writer still returns text, and `factory.py`'s and
  `sdlc.py`'s own writes stay in the change's folder.
- **The spec is approved by a person, never written by an agent unseen.** `write-spec` is
  unchanged. It still copies `runs/spec-draft.md` only after Step 2's yes, and only over the
  scaffold.
- **Never patching an agent's reply.** Nothing here edits a reply. A bad record is a stop.
- **Writes before a WAIT (four named exceptions).** `upgrade` writes before the spec's question,
  but not before the person has answered. It runs inside a run the person approved, on their
  answer to a blocking decision, as `decided` already does. It is not a fifth exception. Ship's
  review should check that reading.
- **A writing skill has exactly one `WAIT` heading, asked in `AskUserQuestion`.** The build skill
  keeps its one heading and gains one wording of its question. Its new command has a `Bash(...)`
  rule written as it runs, and its bash blocks stay plain.
- **`TIER_ARTIFACTS` and `check --strict`.** An upgraded change owes all three files, by the stage
  rules as they stand. R12 widens one exemption, for a live build only, and the exemption hides
  no other problem (a test mirrors `test_a_live_first_build_hides_no_other_problem`).
- **`breaking` / `TEMPLATE_READS`.** `upgrade` reads whole templates, as `new` does, and no new
  heading, so nothing is breaking and no `TEMPLATE_READS` entry is owed. The command is new, so
  `RETIRED_KEYS` and `.sdlc/deprecations.toml` are untouched.
- **The scripts run on Windows.** Every write passes `encoding="utf-8", newline="\n"`, and the
  paths `upgrade` prints are `as_posix()`. The R1, R2 and R12 tests are marked `portable`.
- **Change folders and ids.** `sdlc.py upgrade` finds the folder through `change_dirs()` and
  `work_rel()`, and matches the id with `names_change()`.

## Alternatives rejected

- **The name "promote".** It is the intent's word, but in deployment it means moving a build from
  one environment to the next (dev → qa → prod). A command or step called `promote` would read as
  a release step. "Upgrade" names the tier change and nothing else in this repo.
- **Let the builder write the spec.** The builder plans and builds against a spec, so writing its
  own yardstick defeats the review, and nobody would approve it. The spec-writer drafts it and the
  person approves it.
- **Keep the hand steps (the supervisor edits `tier:` and `stage:`).** This is the problem in the
  intent. The run's records wouldn't show it, and a supervisor following the skill has no step to
  take.
- **Route the upgrade through ESCALATE and `restart`.** That costs an approver run, needs a
  `decision.md`, and starts a fresh builder that throws away the context of the build so far. A
  restart is for a run that reached `test`. An upgrade happens mid-build, and the builder carrying
  on is the point.
- **Keep the round count across the upgrade.** A run upgraded in its last round would go straight
  to the approver with no round reviewed against the spec. Counting again from `P` costs more
  runs, and Step 2's question shows the new `max_runs` before the yes.
- **Have `factory.py` write `spec.md` and `plan.md` itself.** It would need a second copy of
  `new`'s substitutions and of the host-template lookup, pinned by yet another test, and an
  upgrade by hand would still have no command. One `sdlc.py upgrade` serves both.
- **Leave the change at `stage: design` while the builder writes `plan.md`.** `check` would pass
  without an exemption. But `fresh` and the board read `design` as "not building yet": a rerun
  would rebase rounds that were gated on the old base, and the card would sit in the wrong column.
- **Detect an upgrade from the agent's question, or let the supervisor judge it.** An agent asking
  is not the person deciding, and a judged reading is a hand step by another name. The answer's
  prefix is mechanical, and it is the person's.
- **A downgrade path.** The intent asks for none. A Tier 2 that turns out not to need its spec is
  the person's call outside a run, and could be an idea of its own.

## Verification

```bash
uv run --group dev pytest -q tests/test_sdlc.py -k "upgrade or upgraded_build"
uv run --group dev pytest -q tests/test_factory.py -k "upgrad or decided_refuses or fresh_holds or start_reports"
uv run --group dev pytest -q tests/test_board.py -k upgrade
uv run --group dev pytest -q tests/test_skills.py
uv run --group dev pytest -q -m portable
./check.sh
```

Healthy output: every selected test passes, and none is skipped for a missing fixture. The
`portable` run includes R1's, R2's and R12's tests. `./check.sh` ends green: ruff clean, the full
suite passing under `-n auto`, and `claude plugin validate --strict` passing for both plugins. By
hand in a scratch repo (`reopen-drafts`, Tier 1, `stage: build`, one builder report raising a
blocking upgrade decision, ticked `→ decided: upgrade to Tier 2`), these calls should print, in
order:

- `factory.py verdicts 001 --head <h>`: `next: upgrade`.
- `factory.py upgrade 001`: `round: 2`, `tier: 2`, `stage: plan`, `created: [spec.md, plan.md]`.
- `sdlc.py check --strict`: exit 0.
- `verdicts`: `next: spec`, `round: 2`, `written: false`.

After a filled `spec.md` and `stage build`, `verdicts` prints `next: build`, `round: 2`, and the
limit is `1 + rounds`.

