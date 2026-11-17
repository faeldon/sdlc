---
id: 070
slug: factory-supervisor
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 070 — A supervisor that runs a factory change and calls the person only when needed · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. "Chief of staff" is renamed **supervisor** throughout the repo; a test fails on any
   remaining "chief of staff".
2. R2. `/sdlc-factory:build NNN` is the supervisor's skill: a long-running session in the main
   checkout, each invocation adding one change to it. It edits no code; its only writes are the
   spec the person approved and `factory.py` stage moves. Agents' replies are filed by
   `factory.py`, never by the session.
3. R3. The supervisor never waits on an agent: every agent run is started as a background `Bash`
   command, and the supervisor replies to the person in the same turn ("070: spec-writer
   started"). A second `/sdlc-factory:build NNN`, or any question, is answered while others run.
4. R4. `factory.py start <NNN> --for build` runs from the main checkout or the change's worktree,
   finds the change's worktree itself, and accepts a Tier 2 at `plan` (`spec: true`). Its other
   refusals are unchanged.
5. R5. `factory.py agent <NNN> <role> [--resume] [--to <file>] [--message <text>]` is the one way
   the factory runs an agent: `claude -p --agent sdlc-factory:<role> --session-id <id>
   --permission-mode <factory.mode> --output-format json`, `cwd` the change's worktree, or
   `--resume <id>` for the role's recorded session. It records each role's session id in
   `<folder>/runs/<role>`, writes the agent's reply verbatim to `--to` (a path inside the change's
   folder) when given, and prints `{role, session, to, exit}`; a non-zero exit or a timeout is
   reported, never retried. The builder is resumed for every rework, as `SendMessage` does today.
   It is the only place `factory.py` runs `claude`: no shell, `encoding="utf-8"`, its subprocess
   helper pinned to `sdlc.py`'s by a test.
6. R6. A new `.sdlc/factory.toml` key, `factory.mode` (default `auto`), is the permission mode
   agent sessions run in, read from the base branch so a change can't widen its own.
7. R7. The spec-writer runs this way, its draft kept in the command's output until the person's
   yes: nothing in the repo is written before it. The builder plans and builds in its session as
   today (`plan.md`, then code). The reviewers, verifier and approver run this way too, each in
   parallel where the loop allows. No agent's tools change but the builder's (R16): none that
   judges gains Write or Edit, and only the builder edits.
8. R8. Each change has exactly one WAIT, asked when it's ready: for a Tier 2 at `plan`, when its
   spec draft arrives, the supervisor shows it and asks `Write this spec and run the factory on
   NNN-<slug>: …, agents in <factory.mode>, at most <max_runs> runs? (yes / revise a requirement /
   change the reviewers or rounds / no)`; for a Tier 2 at `design` or a Tier 1 at `plan`, the run
   question, at once. Every dialog the supervisor shows names its change in the question.
9. R9. A blocking decision or an ESCALATE is asked as soon as it is gathered, naming its change,
   and its answer goes to the builder through `agent … builder --resume --message`. A change that
   stops (an agent's failure, `HEAD` moving, a refusal) is reported, and the others run on.
10. R10. When a change's run reaches `done`, the supervisor sets `stage: test` and tells the person
    `NNN-slug is ready to ship (READY|ESCALATE)`, and stops nothing and ships nothing.
11. R11. `factory.py ready`, read-only, lists the changes at `stage: test` with a `decision.md`:
    each one's decision, its `depends_on:`, and the other ready changes whose diff against the
    base branch touches the same paths. The supervisor shows it when asked what's ready, with an
    order that puts dependencies first and each change's `cd <worktree> && claude` then
    `/sdlc:ship NNN`. `/sdlc:ship` is unchanged and only the person starts it.
12. R12. `metrics.py` attributes a dialog in a main-checkout session to the change its question
    names (`NNN-slug`), its span keyed by change so interleaved runs don't swap gates. Agent
    sessions are attributed by their branch. Each agent session's role reaches `Sdlc-Role` lines,
    from its `--agent`; plan mode confirms how the transcript records it, falling back to
    `runs/<role>`.
13. R13. `GATES` gains `"first_approval"` for `sdlc-factory:build`. `REQUIRED` becomes `intent,
    run, ship, close` for factory runs with no separate spec stage, and for every factory Tier 1.
    Old trailers keep their numbers.
14. R14. README's factory section and `AGENTS.md`'s factory paragraph describe the supervisor,
    agents as sessions in the change's worktree, several changes at once, and shipping by the
    person when ready; `docs/REFERENCE.md` documents `factory.mode`.
15. R15. `./check.sh` passes.
16. R16. The builder may spawn read-only subagents while planning or reworking, to read the code
    it must change: its `tools:` gain `Agent`, limited to the `Explore` and `Plan` types in its
    definition, and its text says so and forbids any other. None of them can write, edit or
    commit, so the builder stays the only editor. Their runs are counted: `measure` reads them
    from the builder session's own `subagents/` folder, as it reads any session's, each reaching
    an `Sdlc-Role` line under its type. They aren't counted in `max_runs`, which counts the
    factory's own agent runs, and Step 1 says so when it shows the run's cost.
17. R17. `factory.py agent` passes `--model` on every run: the role's `factory.models` entry when
    `.sdlc/factory.toml` sets one, else the rule: the builder, the approver and the security
    reviewer `opus`; the code, test and behaviour reviewers `sonnet` when the change is Tier 2 or
    the run is at full depth (a sensitive path touched), `haiku` otherwise; the spec-writer and
    the verifier their definitions' models (`opus`, `sonnet`). `config` and `start` print each
    role's model, and the run's gate shows them. The supervisor's model is the person's session's
    own, which the plugin never sets. Pinned by a test of each rule.

## Design

| Role | Runs as | Where |
|---|---|---|
| Supervisor | the person's long-running session (`/sdlc-factory:build`, once per change) | main checkout |
| Spec-writer, builder, reviewers, verifier, approver | `claude -p --agent sdlc-factory:<role>`, started in the background by `factory.py agent` | the change's worktree |

The loop per change, each step a background command and the supervisor reacting to each exit:
(spec-writer) → gate → `stage build` → builder (`build/round-1.md`) → `snapshot` → `decisions` /
`verdicts` → reviewers (`reviews/round-N/<role>.md`) → verifier → builder `--resume` (rework) → …
→ `carry` → approver (`decision.md`) → `stage test` → "ready to ship". `verdicts` stays the one
place that says what's next.

The supervisor's files are the agents' files, written by `factory.py`, so "write it exactly as
returned" becomes mechanical.

## Contracts touched

- **An `allowed-tools` rule that lets a command that writes run without asking (always Tier 2).**
  `factory.py agent` starts sessions that edit code unprompted, in `factory.mode`. It is listed
  only in the build skill's rules, never in `ALLOW_RULES`, and the mode is named in every gate.
- **Agents that judge have no Write; only the builder edits; nothing commits.** Unchanged: each
  agent's tools are its definition's, now in its own session. The builder's subagents are
  read-only types (`Explore`, `Plan`), pinned by the agent-tools test (R16).
- **The person's decisions go through `decisions.md`, asked by the build session**, now named the
  supervisor. Unchanged.
- **One WAIT per writing skill, in a dialog.** One per invocation, asked when the change is ready.
- **`factory.py` is self-contained; the scripts run on Windows.** The new subprocess helper is
  pinned, with no shell.
- **The metrics trailer format.** Extended (R12, R13), never redefined.
- **`disable-model-invocation` on every skill; only the named steps push; `sdlc` loads nothing
  from `plugins/`.** Untouched.

## Alternatives rejected

- **Subagents for the agents.** Their transcripts sit in the supervisor's session on `main`, so
  every stop and token needs marker matching, and the supervisor's context fills with every run.
- **The supervisor shipping, automatically or by invoking `/sdlc:ship`.** The person orders the
  ships and resolves conflicts, and no policy edit is needed.
- **A separate planner.** The builder plans as today, and approving the run accepts it.
- **Delegated decisions.** A seed, filed at ship: a standing approval, which policy forbids today.
- **The pilot.** After this lands.

## Verification

- `uv run --group dev pytest tests/test_metrics.py tests/test_skills.py plugins/factory/tests -q`:
  the naming test; `start` from the main checkout; `agent` against a fake `claude` on `PATH`
  (argv, `cwd`, `--resume`, `--to`, timeout, non-zero exit); `ready`'s order and overlaps;
  `factory.mode` read from the base branch; per-change attribution in an interleaved
  main-checkout transcript; `first_approval`; the `REQUIRED` rows;
  `test_agents_have_their_tools_and_nothing_more` pinning the builder's `Agent` to `Explore` and
  `Plan`; a builder session's `subagents/` folder read into `Sdlc-Role` lines.
- `./check.sh`: green.
- Manual: from the main checkout, `/sdlc-factory:build` on a Tier 2 scratch change, then on a
  second before the first's spec arrives. Expect both replies in the same turn, each gate asked
  when its draft lands, `runs/` and the round files in each worktree, "ready to ship" for each,
  `ready` listing them in order, and, after a manual `/sdlc:ship` and `/sdlc:close`,
  `Sdlc-Mode: factory` with `required=4`.
