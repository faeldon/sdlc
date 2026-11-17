---
name: build
description: Add one change to the factory's supervisor, this session — the spec-writer drafts a Tier 2's spec first, and after one approval the builder plans and implements it in its own session in the change's worktree, reviewers check it in parallel rounds at a depth its diff's risk sets, a verifier checks what they ask for, the builder reworks what it keeps, and the approver writes a READY or ESCALATE decision — every agent in the background, so the supervisor stays free for the next change, and each ends uncommitted at stage test, ready for the person to ship. Use from the main checkout (or the change's worktree) once its intent is written, with sdlc-factory installed, as many times as there are changes to build. Not for committing or shipping (/sdlc:ship, which the person runs), not for drafting a spec alone (/sdlc-factory:spec), and never to merge or push.
argument-hint: "[NNN — the change to add]"
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py fresh *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py decisions *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py verdicts *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py carry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py snapshot *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py gate *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py write-spec *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py restart *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py upgrade *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py ready *)'
  - 'Bash(git diff *)'
disable-model-invocation: true
---

# Factory build — the supervisor runs a change's agents

Stages 2 to 4 of the change loop, handed to the factory's agents: the spec-writer drafts a Tier 2's
spec, the builder plans and implements, the script runs the repo's gate on each build before any
reviewer sees it, specialist reviewers check the work in rounds, a verifier
checks each change they ask for against the code, the builder reworks what it keeps, and the
approver recommends. One approval starts it; after that it runs without the person until it
reaches a decision, runs out of rounds, or hits a problem.

**This session is the supervisor.** It is the person's own session, usually a long-running one in
the main checkout, and each `/sdlc-factory:build NNN` adds one change to it. It never builds,
reviews or edits code: every agent runs as a session of its own in the change's worktree, started
by `factory.py agent` with `run_in_background`, which files the agent's reply in the change's
folder. So the supervisor never waits on an agent. It replies to the person in the turn they
asked (`070: spec-writer started`), takes their next request, a second change included, and picks
each change up again when its agent's command exits. Every message and every question it puts to
the person names the change it is about.

**It ends before anything is committed.** Each change stays uncommitted in its worktree at
`stage: test`, with every review and the decision in its folder, and the supervisor says it is
ready to ship. The person ships it with `/sdlc:ship`, from that worktree, in the order they
choose; the supervisor never does. No agent commits, pushes or merges, and a change stops if its
`HEAD` moves.

**Decisions that are the person's go through the supervisor.** When an agent reaches a call that
is the person's (a trade-off the spec leaves open, a policy, scope), it raises a `- DECISION:`
line instead of guessing, and `factory.py decisions` gathers every one into the change's ledger,
`.sdlc/work/NNN-slug/decisions.md`. A **blocking** one pauses that change alone: the supervisor
asks the person, writes the answer into the ledger, and the builder carries on with it. A
**default** one lets the run go on with the agent's stated default, recorded as assumed; the
approver escalates while any is unconfirmed, and `/sdlc:ship` shows them all.

**Under the factory, the plan is accepted by approving this run.** The builder writes `plan.md` and
builds on it without a person reading it first, which plan mode would otherwise require; it may
start read-only `Explore` and `Plan` sub-agents of its own to read the code while it plans. That
is the trade this layer makes, and the reviewers check the build against the plan as well as the
spec.

## Step 0 — The change and the run (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start <NNN> --for build
```

Every command about a change runs in its worktree, which `factory.py` finds from the main checkout.
`config` and `start` give the run's shape from `.sdlc/factory.toml`: the full depth's reviewers
(`factory.reviewers`, default code, security, test and behaviour, the one that runs the spec's
end-to-end path) and round limit (`factory.rounds`,
default 3), the light depth's (`factory.light`, default the code reviewer for 2 rounds, with
the test reviewer too for a Tier 2 unless the repo sets `[light] reviewers`, so name `start`'s
`light.reviewers`, which says this change's), the
permission mode the agent sessions run in (`mode`, from the base branch's file, default `auto`),
each role's model at either depth (`models_at`: `factory.models` where the repo sets one, else
opus for the spec-writer, builder, security reviewer and approver, sonnet for the verifier, and
for the other reviewers sonnet on a Tier 2 or a full-depth run, haiku otherwise), the base
branch's `[ui]` (`ui`: the dev server `serve` starts, the screenshot command `shoot`, the `paths`
that count as UI, and the `fixture` data the server is given a fresh copy of), and `max_runs`, the most agent runs this can take, counted at the full depth.

**The UI reviewers join on their own.** With `[ui]`'s `serve`, `shoot` and `paths` all set, a round
whose diff touches one of those paths adds the `ui` and `ux` reviewers at either depth, and keeps
them in later rounds; `verdicts` lists them in `missing` like any reviewer. Before each of them
runs, `agent` starts the declared server, screenshots each page at each width under
`.sdlc/reports/shots/`, and stops the server; a shot that fails refuses that review, so neither
ever judges a page it couldn't see. Without `[ui]` they never run.

**The depth is set by the diff, after the first build.** With no `[review] sensitive` list in
the base branch's `.sdlc/config.toml`, every run is full, as it always was. With one, a diff that
touches none of its paths runs light; one that touches any, or that a round already reviewed at
the full depth, runs full, and a run never lightens. `verdicts` reports it each time (`depth`,
`why`, `sensitive`), and the reviewers it calls for follow it.

**The gate is the script's, at either depth.** Before any reviewer reads a build, `factory.py gate`
runs the base branch's `[commands] check` (never the change's own copy of the config) in the
change's worktree, and a red one sends the builder back, at most twice a round; a third red gate
stops the change. Gates from every worktree share the base branch's `gate_jobs` slots (`config`
and `start` show it, default 1), so a gate may print that it is waiting for one; its wait is not
in its time. `verdicts` reports it (`gate`: its command, this round's fails, and the verdict on
the build as it stands; null, with `gate_why`, when the base branch names no check, and then no
build is gated). `start` also gives `head`, the commit
the run starts from, `spec`, true for a Tier 2 at `stage: plan`, whose spec the spec-writer drafts
before the gate, and every refusal: no worktree for the change, or a stage this can't start from
(Tier 2 needs `stage: plan` or `design`; Tier 1, `stage: plan`). A run that stopped part way left
the change at `stage: build`, and starts again from where its files say.

**An escalated change can go back to the factory.** At `stage: test` with a `decision.md` that
opens `DECISION: ESCALATE`, `start` gives a `restart` object instead of a refusal: `archive`, the
name the old decision will be kept under (`decision-<n>.md`, never written over), `round`, the
round the new build will be (the new run's first, so its round limit and the gate's fixes count
from there), `reconsider`, whether the decision has a `## Reconsider the approach` section, and
`reasons`, its text. Nothing is written yet. A READY decision is refused (it is ship's or land's),
as is a test change with no decision or one that won't read. **A run upgraded to Tier 2 part way**
(see `upgrade` in Step 3) is named by `start`'s `upgraded`, its `round` (P, the upgraded run's first),
the `decision` that upgraded it and the person's `answer`; null otherwise. **If there are refusals,
show them and stop.** `start` also gives `base`, the branch the change lands on, and `behind`, how many of
its commits the change lacks.

With no refusals, bring the change up to date before any agent reads it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py fresh <NNN>
```

`fresh` runs `sdlc.py`'s own `base` in the change's worktree, and its `resolve` when the base
changed what the change's uncommitted work changes, so the spec-writer drafts and the builder
builds on current code. It is a write before this skill's WAIT, by a named exception to
confirm-before-writing, as ship's `base` is: it moves only the change's own branch, never stashes,
merges the base or forces, and prints the command that undoes it. Its `state`: `current`,
`fast-forwarded`, `rebased` or `resolved`, each with `from`, `head` and `undo`; `held` for a run that
stopped part way at `stage: build`, or one upgraded to Tier 2 at any stage, which moves nothing, since its rounds were gated and reviewed on
the base they had and landing rebases and gates it again; or `refused`, with the worktree as it
was. A conflict git can't settle is aborted and refused, naming its files: the person resolves it
with `/sdlc:ship` from the worktree, or `sdlc.py resolve`, never an agent before the run's yes.
**If `fresh` refuses, show its refusal and stop.** Keep `fresh`'s `head`, not `start`'s: it is
the `--head` every `verdicts` is given, and a run stops when `HEAD` moves.

## Step 1 — Show it

With `spec` true, first draft the spec, in the background:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task spec
```

Say `NNN-slug: spec-writer started`, and end the turn. When it exits, read its JSON: `to`, the
complete draft, `.sdlc/work/NNN-slug/runs/spec-draft.md`; `questions`, the open questions it
resolved and left, `.sdlc/work/NNN-slug/runs/spec-questions.md` (null when it gave none);
`preamble`, anything written before the draft, no part of it. Read both files. Check the draft
against `intent.md` before showing it: every `<...>` prompt replaced, requirements numbered and
each checkable, a **Contracts touched** line for each invariant the change comes near. If one of
those is missing, send it back once, to the same spec-writer, which keeps its draft in context, and
say so if the second draft still lacks it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task spec --recheck
```

`spec.md` is not written yet: the draft is only in `runs/`, an uncommitted run record.

With `upgraded`, show first, naming the change: that it was upgraded from Tier 1 to Tier 2 before
round `round` on the person's answer to `decision` (`answer`, word for word), that the draft
specifies the whole change, the build so far included, and that the builder that built it is
resumed for round `round`, rewriting `plan.md` against the spec before it builds.

With a `restart`, show first, naming the change: the decision's first reason, its `## Reconsider
the approach` section word for word (or that it has none), and the decisions still assumed in its
`decisions.md` (an unconfirmed default is a common reason to escalate, and the person may want to
answer it before the rebuild); then that `decision.md` will be kept as `archive`, and that the
builder starts afresh at round `round`, told the approver's reasons.

Then show the person, naming the change: the spec draft and its questions, when there is one; the
change and its tier; how far it was behind `base` (`behind`) and what `fresh` did, its state,
`from` → `head` and its `undo`, or, when it `held`, that the run resumes `<behind>` commits behind
`<base>`; the gate command the script will run, from the base branch's
`.sdlc/config.toml`, or that there is none; the agents that will run (builder, each reviewer at
each depth, the verifier, approver) with each one's model from `models_at`; the round limits; the
depth rule above; the permission mode; with `[ui]` set, its `serve` and `paths`, since the dev
server runs unasked once they agree; and `max_runs`, the factory's own runs, the builder's fixes
of a red gate included and its sub-agents not, so the cost is in front of them before they agree
to it. Name the files the run will write, all by `factory.py` in the change's folder: code and
`plan.md` by the builder; `build/round-<N>.md`, `reviews/round-<N>/<role>.md`,
`reviews/round-<N>/verified.md` and `decision.md`, the agents' replies; `build/round-<N>.gate.md`,
each attempt of the gate on that round's build; `runs/<agent>.sessions`, each session's id, for
measuring; `runs/costs.jsonl`, each run's reported cost and tokens; with a spec draft, `runs/spec-draft.md` and
`runs/spec-questions.md`, already written, and `spec.md`, copied from the draft by `write-spec`;
with `upgraded`, `build/round-<P>.upgraded.md`, `spec.md` and `plan.md`, already written by
`upgrade`;
`runs/stopped.md`, while the
run is stopped, its problems and the way on, for the board and `/sdlc:status`; `build/round-<N>.files` by
`snapshot`; `decisions.md` for the calls the agents raise; `notes.md` for what the rounds don't
resolve; with a `restart`, `decision-<n>.md` and `build/round-<R>.restart.md` by `restart`. Say that the run will ask them about any blocking decision, and that every builder report
and behaviour check must end with its `## Evidence` (each command run, its output, its exit), or
the change stops: the behaviour check runs the spec's end-to-end path, and reads `checks.md`
without running it, which `/sdlc:ship` does under a prompt.

## Step 2 — WAIT for explicit approval

Ask literally, with a spec draft:

> `Write this spec and run the factory on NNN-<slug>: the builder plans and builds it, the base branch's gate <command> runs on each build before any reviewer (up to 2 fixes a round), <reviewers> review it in up to <rounds> rounds (or <light reviewers> in up to <light rounds> when the diff touches no sensitive path), and, on a diff touching <ui paths>, the ui and ux reviewers, which start <serve>, a verifier checks each round's changes, the approver decides, at most <max_runs> agent runs, agents in <mode>, all left uncommitted at stage: test? (yes / revise a requirement / change the reviewers or rounds / no)`

And without one:

> `Run the factory on NNN-<slug>: the builder plans and builds it, the base branch's gate <command> runs on each build before any reviewer (up to 2 fixes a round), <reviewers> review it in up to <rounds> rounds (or <light reviewers> in up to <light rounds> when the diff touches no sensitive path), and, on a diff touching <ui paths>, the ui and ux reviewers, which start <serve>, a verifier checks each round's changes, the approver decides, at most <max_runs> agent runs, agents in <mode>, all left uncommitted at stage: test? (yes / change the reviewers or rounds / no)`

And with a `restart`:

> `Send NNN-<slug> back to the factory: decision.md kept as decision-<n>.md, the builder rebuilds from round <R> with the approver's reasons, the base branch's gate <command> runs on each build before any reviewer (up to 2 fixes a round), <reviewers> review it in up to <rounds> more rounds (or <light reviewers> in up to <light rounds> when the diff touches no sensitive path), and, on a diff touching <ui paths>, the ui and ux reviewers, which start <serve>, a verifier checks each round's changes, the approver decides again, at most <max_runs> agent runs, agents in <mode>, all left uncommitted at stage: test? (yes / change the reviewers or rounds / no)`

And with `upgraded`, on its spec draft:

> `Write this spec and carry on NNN-<slug>'s factory run as Tier 2: the builder, resumed, rewrites plan.md against it and builds round <P>, the base branch's gate <command> runs on each build before any reviewer (up to 2 fixes a round), <reviewers> review it in up to <rounds> more rounds (or <light reviewers> in up to <light rounds> when the diff touches no sensitive path), and, on a diff touching <ui paths>, the ui and ux reviewers, which start <serve>, a verifier checks each round's changes, the approver decides, at most <max_runs> more agent runs, agents in <mode>, all left uncommitted at stage: test? (yes / revise a requirement / change the reviewers or rounds / no)`

A no leaves the change a Tier 2 at `stage: plan`, which `sdlc.py check` reads as sound; the person
comes back to it with `/sdlc-factory:build`, `/sdlc-factory:spec` or `/sdlc:spec`.

A typed `yes, <words>` to it is a yes with the person's direction for the builder.

Leave out the parenthesis when the base branch's `.sdlc/config.toml` lists no `[review]
sensitive` paths: every run is then full. When it names no `[commands] check`, the gate clause reads
`, with no gate configured` instead. Leave out `and, on a diff touching <ui paths>, the ui and ux
reviewers, which start <serve>,` when `start`'s `ui` lacks `serve`, `shoot` or `paths`: no UI
review can run.

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Do nothing more for this change until the person says yes.** Approval is for this run only.
`revise a requirement` takes their words to the spec-writer, and the question is asked again on its
new draft. Words never go in a command line: write them at the end of the change's `decisions.md`
(`Write` it with a `# Decisions` heading first when it doesn't exist) as a ticked line,
`- [x] R<n> (person, revise): <their words, as they gave them>`, `<n>` one past the highest `R`
there. It is the one write before this gate, by a named exception to confirm-before-writing, as
ship's `findings.md` is: it writes only the change's own uncommitted folder, holds only the
person's words, and decides nothing. Then, in the background:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task spec --revise <R1>
```

Changing the reviewers or rounds is an edit to `.sdlc/factory.toml` and a new question.

## Step 3 — Run it

With a spec draft, copy it into `spec.md` and advance the change:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py write-spec <NNN> && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> design && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> build
```

`write-spec` copies `runs/spec-draft.md` exactly as shown, byte for byte, and refuses, writing
nothing, with no draft, off a Tier 2 at `stage: plan`, or once `spec.md` is no longer its scaffold;
a refusal stops the change, reported. On an upgraded run whose `verdicts` said `written` true (a
rerun after the spec was copied), run only the moves still owed: no `write-spec`, `stage design`
only while the change is at `stage: plan`, then `stage build`. Then strike the open questions the spec resolved in
`intent.md` with `Edit` (`- ~~Question?~~ Resolved: ...`). Without a spec draft, run only the
last `stage`. With a `restart`, run `restart` in place of both: it writes
`build/round-<R>.restart.md`, renames `decision.md` to `decision-<n>.md` and sets `stage: build`,
in that order, and a rerun finishes one cut short. When the yes came with words, first write them
at the end of `decisions.md` (`Write` it with a `# Decisions` heading first when it doesn't exist)
as `- [x] R<n> (person, restart): <their words, as they gave them>`, `<n>` one past the highest
`R` there, and pass `--words R<n>`; without words, leave `--words` out. The words never go on the
command line, only their id.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py restart <NNN> --words <R1>
```

Then go to step 2: `verdicts` names `build` at round `<R>`. Every `factory.py agent` call below runs with
`run_in_background`; when it exits, read its JSON (`to`, the file it wrote, or `problem`) and take
the next step for that change. A `problem` is a stop, reported for that change alone.

1. **Build.**

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task build
   ```

   The builder's session is resumed for every later step it takes (a rework, a decision's
   answer, a mend), with its context. **Where every builder report goes** decides what gets
   reviewed, and `factory.py` keeps the rule: `build/round-<R+1>.md`, where `<R>` is the highest
   review round so far, whether the report came from a rework or from the person's answer to a
   decision; only a report from before any review of its round is added to the end of the existing
   file.

   **After every builder report,** snapshot what its build left, `<N>` being that report's
   round, so the next round's reviewers read what the rework changed:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py snapshot <NNN> --round <N>
   ```
2. **Ask the script what's next**, after every step from here on: gather the decisions raised so
   far into the ledger, then read the loop's state.

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py decisions <NNN> && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py verdicts <NNN> --head <head> --record
   ```

   Do what its `next` says, and nothing else; `factory.py agent` refuses a step it doesn't name.
   `--record` keeps `.sdlc/work/NNN-slug/runs/stopped.md` in step with that reading: written on a
   `stop`, removed on any other step. It also writes the step it read, with since when, to
   `.sdlc/work/NNN-slug/runs/step.md`, which the board's step track reads; leave both to it.

   - **`build`**: no builder report exists yet (a run that stopped before the first), or a
     restart's or an upgrade's round has none: go back to step 1. At an upgrade's round the
     builder is resumed, told the decision, its answer and the approved spec, rewrites `plan.md`
     against it first, and reports to `build/round-<P>.md`, gated and reviewed like any round,
     the round limit counted from `P`. At a restart's round the builder is a fresh
     session, told `decision-<n>.md` and its `## Reconsider the approach` section (and the
     person's words, with `--words`), and its report is `build/round-<R>.md`, gated and reviewed
     like any round.
   - **`gate`**: the round's build hasn't been gated as it stands. The script runs the base
     branch's check on it, adding the attempt to `.sdlc/work/NNN-slug/build/round-<round>.gate.md`;
     start no reviewer until `verdicts` says `review`.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py gate <NNN>
     ```

   - **`fix`**: the gate is red on the round's build. The builder is told `The gate failed on
     round <round>: read .sdlc/work/NNN-slug/build/round-<round>.gate.md, fix what it shows, then
     report.`, and its report is added to `build/round-<round>.md`, the round being unreviewed;
     snapshot that round again after it, as after every builder report, and the script then says
     `gate` once more.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task fix
     ```

   - **`decide`**: a blocking decision is waiting (`pending`). Ask the person with
     `AskUserQuestion`, one question per pending decision (up to four at once, all of one change:
     never two changes' in one dialog): the change's
     `NNN-slug` first, then the question as the agent put it, the options it gave, its
     recommendation first and marked as such, and who raised it in which round. Record each answer
     by `Edit`ing its line in `decisions.md` from `- [ ] D1 (...)` to `- [x] D1 (...)`, with
     ` → decided: <their answer>` at the end. Then the builder carries on with it, the round's
     reviews alongside for a reviewer's decision, and its report is reviewed like any:

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task decided --decision <D1>
     ```

     Never answer a decision yourself, and never tick one the person didn't answer.

     **An answer that upgrades the change.** When the person chooses, or types, that a Tier 1
     change should become Tier 2 (an agent offers it as `upgrade to Tier 2`), write their answer
     starting with exactly those words, `→ decided: upgrade to Tier 2: <their words, if any>`, and
     run no `decided` for it, nor for any other line answered in the same dialog: the next
     `verdicts` names `upgrade`, and the builder resumed after the spec is told every decided line.
     Only the person's answer upgrades a change, never an agent's question or your reading of it.

   - **`upgrade`**: the person's answer to `upgrading` makes this Tier 1 change a Tier 2. The script
     writes `build/round-<P>.upgraded.md`, `P` the upgraded run's first round, then runs `sdlc`'s
     own `sdlc.py upgrade`, which sets `tier: 2` and `stage: plan` and scaffolds `spec.md` and
     `plan.md` where they are missing, keeping a `plan.md` the builder wrote. It commits nothing,
     and a rerun finishes one cut short. A refusal is a stop for the change, reported. It happens
     once: there is no second upgrade, and no downgrade.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py upgrade <NNN>
     ```

   - **`spec`**: an upgraded change owes its spec before round `round` builds. Go back to Step 1:
     `start` reports `upgraded`, and the spec-writer drafts it, told the upgrade, the person's
     answer and that the build so far is in the worktree; then ask Step 2's question in its
     upgraded form, and on a yes run Step 3's `write-spec` and stages, only the moves still owed
     when `written` is true. Nothing builds on the spec before that yes. Then come back here:
     `verdicts` names `build` at round `round`.

   - **`review`**: start every reviewer in `missing` **in one message**, so they run in parallel,
     each with:

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task review --role <role>
     ```

     Its reply goes to `.sdlc/work/NNN-slug/reviews/round-<round>/<role>.md`. From round 2, a
     reviewer that reviewed an earlier round is told what was reworked, what was kept last round,
     and what is settled, never to be raised again. Take no next step for the change until every
     reviewer of the round has replied.
   - **`verify`**: the verifier checks every `- CHANGE:` line of the round's `VERDICT: CHANGES`
     reviews, with the round's `untouched`, `repeats` and `settled`, as
     `sdlc-factory:verifier`, into `.sdlc/work/NNN-slug/reviews/round-<round>/verified.md`. A
     reply that leaves a change unanswered, or answers one twice, is a `stop` on the next call:
     never patch it.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task verify
     ```

   - **`rework`**: the builder is told `Round <round>'s changes are verified in
     .sdlc/work/NNN-slug/reviews/round-<round>/verified.md. Address every KEPT line, then report.`,
     and its report goes to `build/round-<round+1>.md`; the script then says `review` for that
     round.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task rework
     ```

   - **`approve`**: first carry what's unresolved into the notes, so `/sdlc:ship` must give each a
     disposition, then run the approver, whose reply goes to `.sdlc/work/NNN-slug/decision.md`.
     When `exhausted` is true, it is asked whether the approach should be reconsidered, and only an
     ESCALATE with a `## Reconsider the approach` section passes the next call.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py carry <NNN> && \
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task approve
     ```

   - **`done`**: the decision is in and readable. Go to step 3.
   - **`stop`**: report its `problems` for the change, and leave it. It stays at `stage: build`,
     and the other changes run on. A reviewer reply that doesn't open with a verdict, a decision
     that doesn't open with one, a third red gate in a round, or `HEAD` moving (an agent
     committed) is a stop: never patch a verdict in, and never reset a commit. **A stop whose
     `way` is `mend` is the one kind this run can mend itself,** once for each role its `mend`
     names: a missing `## Evidence` (the builder resumed, or a new behaviour check for that
     round, asked to run what its claims rest on again), a reviewer's verdict written after a
     preamble (that reviewer resumed, asked to reply again with its `VERDICT:` line first), the
     approver's decision written after one (`approver`, resumed for its `DECISION:` line first),
     or answers in `verified.md` the script couldn't read (`verifier`, resumed with what the
     script found). Each reply is written over the old one.

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task mend --role <a role in mend>
     ```

     Never write the evidence or the verdict yourself, and never move a verdict to the first line.
     A second reply that still needs a mend is a stop like any other: `agent` records each mend
     in `runs/mended`, `verdicts` then names that stop `rerun`, and a second mend is refused.

     The reading that stopped wrote `runs/stopped.md`: its problems word for word, and the way on
     (`way`: `ship` after a commit, `mend` for a missing `## Evidence` or an answer not in its
     shape, `rerun` otherwise) with its
     sentence, which the board and `/sdlc:status` show the person. Name that sentence in your
     report. Never write, edit or delete `runs/stopped.md` yourself: only a reading that finds the
     cause gone removes it, when the person reruns `/sdlc-factory:build NNN`.
3. **Hand it back.**

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> test
   ```

## Step 4 — Report it ready to ship

Say `NNN-slug is ready to ship (READY|ESCALATE)`, leading with ESCALATE when that is the decision,
and report: the depth it ran at and why, the rounds it took, each round's gate attempts and their
verdicts (or that no gate is configured), each round's verdicts by reviewer and
how many changes the verifier kept and dropped, the decision and its first reason, the decisions
the person made during the run and those still assumed (by id, with the default the build rests
on; a line marked `→ superseded by D<m>` is no assumption, shown as one line beside D<m>, the
default that replaced it, never counted as open), what `carry` added to `notes.md`, the files changed (`git diff --stat` in its worktree), and
what the run cost: the `cost` that `stage <NNN> test` printed, its `usd` total and the split
`by_role` and `by_model`, called the API-equivalent cost Claude Code reported (on a subscription,
where the spend went, not a bill), with `unknown` runs said when there are any. Say plainly that
nothing is committed. Then go on with the other changes: this stops nothing.

When the person asks what's ready, read it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py ready
```

Show each change in its order, a change after what it `depends_on`, with its decision, its
`cost`'s `usd` (the same API-equivalent figure) and the others it `overlaps` (changes touching
the same paths, which ship more easily one after the other), and how to land them:
`/sdlc-factory:land`, from a session of its own in the main checkout, takes them as one batch in
this order, or `cd <worktree> && claude`, then `/sdlc:ship NNN`, one at a time. Never start either
yourself.

## Out of scope

- Committing, pushing, merging, shipping, or approving a change: `/sdlc-factory:land`, or
  `/sdlc:ship` and `/sdlc:close`, the person's steps, when they choose.
- Building, reviewing or editing code in this session: every agent runs in its own.
- Editing a review, verification or decision an agent returned, or writing one when an agent
  didn't.
