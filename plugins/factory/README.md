# sdlc-factory — agents for the change loop, optional

A companion to the `sdlc` plugin. `sdlc` on its own is **manual mode**: a person drives every
stage of a change. The factory doesn't replace that process; it runs on it. Manual mode is its
deterministic spine, and the factory hands the judgment in it (a change's **spec, plan, build and
review**) to agents, while every stage and check around them stays the code a person runs by hand,
and ship and close stay `sdlc`'s own code, run by the person or, for a batch, by
`/sdlc-factory:land`. Install it in the repos where you want that; leave it out
where you don't. A repo without it runs `sdlc` exactly as before, and a repo with it can still
build any change by hand.

```bash
claude plugin install sdlc-factory@sdlc      # needs sdlc, which it depends on
```

## Where it sits

Inside the change loop, between a person's intent and the change's landing. Nothing before or after
changes, and the release and retrospective loops never see the difference: a change the agents
built is a change.

With the factory enabled for the repo (Claude Code's `enabledPlugins`, at any scope),
`/sdlc:intent`'s question offers `yes, for the factory` beside `yes, by hand`. That answer creates
the change, its worktree and its issue as the other does, but starts no plan mode and leaves the
session in the main checkout, with the change at `stage: plan`, where `/sdlc-factory:build NNN`
starts it. It starts no run: the supervisor's own WAIT does. A batch (`/sdlc:intent` with
groups separated by `;`) always does the same, and its report gives each change's
`/sdlc-factory:build NNN`.

What stays deterministic, and the person's, is manual mode's:

- **The stages.** `factory.py` refuses a step the change's tier and `stage:` don't allow, and
  moves `stage:` only as far as `test`: `shipped` is `sdlc.py ship`'s alone.
- **The artifacts.** The agents write the same `spec.md`, `plan.md` and code a person would, in
  the same folder, and `sdlc.py check` audits them the same way.
- **The depth of review.** It comes from the diff against the base branch's `[review] sensitive`,
  read by the script, never judged by an agent, so a change can't lighten its own review.
- **The gates.** The supervisor starts nothing before its one WAIT (the spec and the run, or
  `/sdlc-factory:spec`'s for a spec alone), and the run leaves everything uncommitted.
  `/sdlc:ship` reviews it as it would any change, with its own checks, its WAIT and its one
  commit, and `/sdlc:close` lands it. Or `/sdlc-factory:land` runs ship's and close's own code for
  a batch of ready changes, behind one gate that passes itself only when no change in it carries
  a risk signal, the factory's rounds standing in for ship's review.
- **The measuring.** Close counts a factory change's rework from the same trailers as one built
  by hand.

The agents fill only the slots where a person would otherwise judge: drafting, building,
reviewing, and deciding whether to escalate.

```
/sdlc:intent ── /sdlc-factory:build, the supervisor ──────────────────────────── /sdlc:ship ── /sdlc:close
  a person      spec-writer drafts a Tier 2's spec                              a person,     a person
  writes why    one WAIT: the spec and the run                                  when ready,   lands it
                builder plans and builds, in its own session                    in order      (WAIT)
                reviewers, in rounds, at the diff's depth                       (WAIT)
                verifier checks what they ask for; builder reworks what it keeps
                approver: READY or ESCALATE → "ready to ship"
```

- **`/sdlc-factory:build NNN`**, the **supervisor** (Tier 2 at `stage: plan` or `design`, Tier 1
  at `stage: plan`): your own session, usually a long-running one in the main checkout, which you
  hand one change at a time, as many as you like. Every agent runs as a session of its own in the
  change's worktree (`claude -p --agent`), in the background, so the supervisor answers you at once
  and takes the next change while the first builds. For a Tier 2 at `plan`, the `spec-writer`
  drafts `spec.md` first; you read it, and the one approval covers the spec and the run, showing
  the agents, each one's model, the round limit, the permission mode the agents run in and the most
  agent runs it can take. Then the change runs unattended, except to ask you about a blocking
  decision (naming the change), and stops at `stage: test` with everything **uncommitted**, and
  the supervisor says it's ready to ship. Ask it what's ready, and it lists every such change in
  the order to ship them, a change after what it `depends_on`, with the others that touch the same
  paths. The supervisor never ships: you land them.
- **`/sdlc-factory:decide NNN`**, on one change at `stage: test`: its open decisions and assumed
  defaults, one at a time, each with its background, the default, the alternatives the agent
  weighed and why it chose the default, asked in a dialog with the default first, and each `look`
  the approver escalated for, naming what to look at (`seen`, acknowledged and accepted as built,
  or what you checked). The approver files no look for a published interface you already approved
  in the spec or an answer; it names it for ship instead. After one approval it writes your
  answers into `decisions.md` (`→ decided:`), as the supervisor does, and says what's next: decide
  again, rebuild (an answer the build doesn't follow), the hand gate (a `gate` reason not yet
  green on the change as it stands), or ship. It reads
  through `factory.py ask`, which writes nothing, and starts no agent.
- **`/sdlc-factory:land [NNN…]`**, from the main checkout: the ready
  changes as one batch, in that order, each shipped with the impact its approver proposed and
  the nits on its intent's or spec's `Nits taken in:` line retired, committed, and landed as a **train**, through
  `sdlc`'s own `ship` and `close` (`factory.py` runs the `sdlc.py` of its own version, beside it,
  never a copy). The train stacks each change on the one before it, in order, on the base
  branch; a stack that conflicts goes to the `resolver`, an agent of its own given every change's
  spec and diff, which may edit only the conflicted files, and every reviewer at that change's depth
  checks the resolution before it lands. The base branch's gate runs once, at the stack's tip; a red
  tip is bisected by prefix and the change at fault is ejected, back to its commit as it was before
  the train with the reason and the gate file in its commit, while the rest land; nothing of it
  reaches the base branch. Then the changes close in order, each by close's fast-forward, so the
  base branch's history reads as a one-at-a-time landing. When the base branch moves under the
  train, every change not landed re-stacks onto it and the tip is gated again, up to `[land] moves`
  times. A rerun resumes a train under way, and the board shows each change's place in it. After
  your yes the skill runs each change's acceptance checks and cases behind their own prompts, then
  starts `factory.py train --run` in the background and ends its turn: the loop takes every
  step itself and starts the landing's agents, ejects a change the gate found at fault as your
  yes approved, runs each change's acceptance checks again as stacked while its `checks.md` is the
  one your yes covered, runs the base branch's `[commands] build` once at the tip when a change
  calls for it (a path its `build_when` matches, or a `[review] sensitive` one, as `/sdlc:ship`
  does by hand), and stops only where you're needed (any other ejection, a train stop, a red
  build, checks changed since your yes that the script's read-only list and the approver haven't
  both cleared, a refused push, a command or agent that fails), naming why and the way on; rerun `/sdlc-factory:land` to go on past it. `train --cancel` stops the loop after the step
  in flight, and one loop runs at a time, under a run lock in the git common dir. Answer
  `yes, with a fix` and name the change, and the fix goes to its own builder, is gated, and every
  reviewer at its depth reads it before it lands; a builder that finds it already made edits
  nothing, answers `FIX: ALREADY MADE` with its evidence, and the train goes on to the gate and
  that review all the same. Your words for it go into the change's
  `decisions.md` as a ticked `(person, fix)` line, never on a command line. A path changed after
  the last review round any other way is a signal, and the commit says so (`unreviewed=<n>`).
  One approval covers the batch, and it **passes itself when no change in it carries a risk
  signal** (a sensitive or irreversible path, `impact: major`, an ESCALATE, an open or assumed
  decision, a default the approver settled, an issue someone filed, a resolved conflict no reviewer
  has seen, a path no review read, a fix made while landing, acceptance checks, skills' cases in
  scope (and any that failed, hit the sandbox or were skipped), undone notes, nits to file),
  recorded as `Sdlc-Landed: by=auto` on the change's commit and never as your review. Otherwise
  its one question shows what your yes approves, for each change: each acceptance check's name
  and command, run then through `factory.py accept` behind the harness's own prompt (a failure
  stops that change and those after it, and a rebased change runs its checks again, by the loop
  itself: unattended only for the commands your yes showed, or, for one changed since, when every
  added or edited command passes the read-only list and the approver judges it harmless, its
  judgement filed in `build/land-<n>.checks.md`; the approver's word alone never runs one), and the
  skills' cases with their cost cap, run before the question through `factory.py cases`, behind
  the same prompt, so it shows each case that failed (with its failing graders and its traces),
  hit the sandbox, or was skipped (`cases --skip` when you decline the run), which your yes
  accepts as shown, as ship's `wrong` does; each undone note carried to the
  register as a seed or dropped, as its approver proposed, and a `pre-existing:` one it proposed
  as a bug filed as a `[bug]` with its severity and paths (`filed as a bug, <severity>: <title>
  (<paths>)`); each nit its agents weighed to file, as a `[nit]` entry with its theme, paths,
  cost and value (`[nit] <title> (<theme>, <cost>, <value>; <paths>)`); each assumed decision
  confirmed; and the `How to recover:` its commit carries for an irreversible path. A change
  touching an irreversible path its approver proposed no way back for, or with a bug proposed on a
  severity that isn't one of the process doc's words (`sdlc.py bugs`), with no paths or on any other
  item, is left for `/sdlc:ship`, which also stays the way to land a change by hand.
- **`/sdlc-factory:spec NNN`** (Tier 2, `stage: plan`): the `spec-writer` alone, for a spec you
  want approved on its own before building by hand or with the factory. Then `stage: design`.

The builder may start read-only `Explore` and `Plan` sub-agents of its own while it plans or
reworks, to read code across the repo; they never write, so it stays the only editor. Each
reviewer runs on sonnet at either depth and tier, but the security reviewer, which runs on opus
like the builder and the approver (*Why these defaults*, below, says why); the resolver runs on
sonnet, its runs recorded under its own role, apart from the builder's. The supervisor runs on
whatever model your session does.

Two more skills stand outside any change, each run only when you ask, behind one approval that
states the most agent runs it takes. Both write only under `.sdlc/reports/`, a folder that ignores
itself, so neither ever dirties a checkout.

- **`/sdlc-factory:eval [--limit N]`**: replays the reviewers on the diffs that let real bugs
  through (each `[bug]` with an `Introduced by:`, and each bug a change fixed, from its `Close`
  commit's `Sdlc-Fixes`), as text, read-only, and scores which reviewer raised a `CHANGE:` on each
  bug's paths, against the last eval. Run it before and after changing a reviewer's prompt or
  model: keep the change only if the score holds or rises.
- **`/sdlc-factory:review [paths…]`**: has the code and security reviewers look at code no change
  touches (your paths; else the `[review] sensitive` paths; else the least recently changed
  files; never a path an open change touches) and writes what they find as proposed `[bug]`
  entries. It files nothing: `/sdlc:bug <report>` files the ones you pick. To run it regularly,
  put `/sdlc-factory:review` on a `/schedule` routine: it still stops at its approval.

The agents never commit, push or merge, and the run stops if `HEAD` moves; only the landing
commits, through `sdlc`'s own ship, and pushes, through its close. **Under the factory,
the builder's `plan.md` is accepted by your approval of the run**, not read by you in plan mode
first. That is the trade this layer makes; the reviewers check the build against the plan and the
spec.

## Rounds that converge

- **Built on current code.** Before its spec-writer or its question, `/sdlc-factory:build NNN`
  (and `/sdlc-factory:spec NNN`, before its spec-writer) runs `factory.py fresh`, which brings the
  change's branch up to the base branch through `sdlc`'s own `base` (and its `resolve` when the base
  changed what the change's uncommitted work changes), and shows how far behind it was, what moved
  and the undo. Only the change's own branch moves; never a stash, a merge of the base or a force. A
  real conflict is aborted and left for you (`/sdlc:ship` resolves it), and a run that stopped part
  way at `stage: build` is held where it was: its rounds were reviewed on that base, and landing
  rebases and gates it again.
- **Gated by the script, before any reviewer.** After each builder report, `factory.py gate` runs
  the base branch's `[commands] check` in the change's worktree, never the change's own config, and
  records each attempt in `build/round-<N>.gate.md`. A red gate, or one that changes the tree,
  starts no reviewer: the builder fixes it, at most twice a round, and a third red gate stops the
  change for you. Light runs are gated like full ones. The gate's command can't be changed by the
  change, but the script it runs (a `check.sh`) is in the change's tree: list it in
  `[review] sensitive` to have an edit to it reviewed at the full depth and named at ship.
- **One gate at a time, by default.** Gates and `check` runs from every worktree share
  `gate_jobs` slots (1 unless the base branch's `factory.toml` says more), so parallel runs'
  checks don't fight over every core. A gate that waits prints `NNN-slug: waiting for a gate slot (1
  of 1 in use)`, and its wait is not in its `Seconds:`: each attempt records it apart, as
  `Waited:`, for the retrospective's gate figures. A gate run by hand (`sdlc.py gate`) shares
  the same slots, waiting at most 30 minutes for one.
- **Agents leave the whole suite to the gate.** The builder runs each slice's tests by name, and
  the reviewers read the gate's record rather than run the suite again. A full run an agent still
  wants goes through `factory.py check NNN`, which its prompt names: the base branch's `[commands]
  check` in the change's worktree, in a gate slot, its output and exit the command's. It records
  nothing, so it never stands in for the gate.
- **Verified before reworked.** After each round with a `CHANGES` verdict, the `verifier` checks
  every `- CHANGE:` against the code and keeps or drops it, with why. The builder reworks only what
  it keeps; `/sdlc:ship` shows what it dropped.
- **Later rounds read the rework.** After every builder report, `factory.py snapshot` hashes what
  the build left, so a reviewer back for round 2 reads the paths the rework changed and the kept
  changes, never raises a settled point again, and files a problem in code the change didn't
  touch as `- PREEXISTING:`, carried to `notes.md` for ship, never reworked here. A finding may
  open with its pass (`[correctness]`, `[contract]`, `[cost]` or `[context]`; without one, the
  security reviewer's is contract and every other's correctness), and the code, security and test
  reviewers list their nits as `- NIT:` lines under `## Notes`, never verified, each weighed
  `{<theme> <cost> <value>}` by the process doc's rubric. The script disposes of each by its
  weights: an `S` with `med` value goes to the builder with a rework that runs anyway (never one
  of its own), any other `S` or `M` is filed at landing, at most five a change, an `L` or a
  `high` value is carried to `notes.md`, and an unweighed nit is only recorded.
- **At the cap, step back.** When the rounds run out with changes still kept, the approver must
  ESCALATE and say, under `## Reconsider the approach`, what kept coming back.
- **Stop early when a round can't help.** A run goes to the approver with rounds still left when
  the verifier keeps the same change, word for word, two rounds running (`stuck`; reviewers raise
  an undone kept change again in its own words so the script can tell), or when the builder's
  report says a requirement can't be tested (`- UNTESTABLE: R<n>: <why>`, `untestable`; `none` or
  `n/a` there is no requirement), once its round is reviewed. The approver is told which, and must
  ESCALATE, naming under `## Reconsider the approach` the next step it would take: a requirement to
  rewrite, a model to try, or an approach to change. A restart or an upgrade starts the count
  afresh.
- **An ESCALATE can go back.** `/sdlc-factory:build NNN` on an escalated change at `stage: test`
  asks once more, and on your yes (`yes, <words>` adds your own direction) `factory.py restart`
  keeps the old `decision.md` as `decision-<n>.md`, writes `build/round-<R>.restart.md` and sets
  `stage: build`. A fresh builder rebuilds from round R told the approver's reasons, and the new
  run is gated, reviewed and decided like any, its round limit and gate fixes counted from R. A
  READY decision never goes back: it is ship's.
- **A Tier 1 that needs a spec is upgraded, once.** When the builder finds a Tier 1 change bigger
  than its Approach, it raises a blocking decision offering `upgrade to Tier 2`. If your answer
  starts with those words, `verdicts` names `upgrade`, and `factory.py upgrade` writes
  `build/round-<P>.upgraded.md` and has `sdlc`'s own `sdlc.py upgrade` set `tier: 2` and `stage:
  plan` and scaffold `spec.md` and `plan.md` where they are missing, keeping a plan the builder
  wrote. `verdicts` then names `spec`: the spec-writer drafts it, told the upgrade and that the
  build so far is in the worktree, and the run asks you to approve it as its gate's question
  does, before anything builds on it. The builder that raised it is then resumed for round P,
  rewrites `plan.md` against the approved spec, and builds to it. Round P is gated, reviewed
  against the spec and decided like any, its round limit counted from P. Nothing is moved by
  hand. A change is upgraded once and never back, and `fresh` holds an upgraded run where it is.
- **Shown, not said.** Every builder report and every behaviour check ends with `## Evidence`:
  each command run as `$ <command>`, the tail of its output, and `exit: <n>`. Only a read that
  shows its output may leave its exit off, and the script alone judges a read (`is_read()`): a
  short allowlist of programs that change nothing, each stage of a pipeline among them, writing
  nowhere. A test run, a gate or a script always owes its exit. A verdict or decision that
  follows prose is read where it stands (`opening()`). A reply without its evidence, or holding
  answers the script can't read (verdict or decision lines that disagree, none of them first, or
  a verifier's answers in another shape), goes back to the agent that wrote it once a round, a
  landing round included, and its new reply is written over the old; a second stops the run.
  `agent` files the last of a session's replies that holds its answer, so a background task's
  notice answered after a verdict never replaces it. The gate
  itself is the script's, so "the gate passes" is never taken on an agent's word.
- **Depth follows risk.** With `[review] sensitive` set in the base branch's
  `.sdlc/config.toml`, a diff touching none of those paths runs the light depth (`[light]` below);
  one touching any runs the full depth, and a run never lightens. With no list, every run is full.
  Unless you set `[light] reviewers` yourself, the light rounds add the behaviour reviewer at
  either tier, the check every landing runs first, and a Tier 2's add the test reviewer too, which
  reads the tests against the spec's numbered requirements, each only when the full depth runs it:
  a Tier 1's light rounds run the code and behaviour reviewers. The tier picks the reviewers,
  never the depth.

## Decisions that are yours

An agent that reaches a call that is yours (a trade-off the spec leaves open, a policy, scope)
raises it instead of guessing: `- DECISION: [blocking] ...` or `- DECISION: [default] ...`, with the
options and its recommendation, each option under its line with its pros and cons and why the
agent chose its own:

```
- DECISION: [default] Page the drafts list at 50?
  - OPTION: 50 — one screen's worth; a long list needs a second page
  - OPTION: 100 — fewer pages; a slower first paint
  - WHY: the spec's list view shows 50
```

They're gathered into the change's ledger, `.sdlc/work/NNN-slug/decisions.md`, each with an id
(`D1`, `D2`, …), its alternatives kept under its line.

- **Blocking**: the run pauses, and the session running it, the only one that can talk to you,
  asks you. Your answer is written into the ledger (`- [x] D1 ... → decided: ...`) and the agent is
  resumed with it.
- **Default**: the run goes on with the agent's stated default, marked as assumed. The approver
  weighs each one: one the spec, the code or a round settles, it settles, and the ledger ticks it
  `→ settled by the approver: <reason>`, its call and never your word, still shown to you at the
  landing (a signal of its own, so a batch holding one never passes itself) and at ship; one it
  can't, it escalates to you, and the change is escalated while any is. `/sdlc-factory:decide
  NNN` then asks you each open one, one at a time, with the alternatives; `/sdlc:ship` shows every
  one, so your approval there confirms it or sends the change back. A later default that replaces
  one names it, `- DECISION: [default] (supersedes D2) ...`, and the ledger ticks D2 `→ superseded
  by D4`: no longer assumed, shown beside the default that replaced it. A decided line can't be
  superseded.

## The agents

| agent | does | can change files |
|---|---|---|
| `spec-writer` | drafts `spec.md`, filed in `runs/` for you to approve, copied after your yes | no |
| `builder` | writes `plan.md` and the code, test first, in slices; reworks | yes |
| `reviewer-code` | correctness against the spec, contract, readability, cost, and whether the context docs still tell the truth | no |
| `reviewer-security` | trust boundaries, injection, authz, secrets, dependencies | no |
| `reviewer-test` | every requirement proven by a test that can fail; reads `checks.md`, never runs it | no |
| `reviewer-behaviour` | runs the spec's end-to-end path on a gated build; reads `checks.md`, never runs it | no |
| `reviewer-ui` | how the change looks: theme fit, spacing, contrast, overflow at phone width, from screenshots | no |
| `reviewer-ux` | how it works for a person: the task, empty, loading and error states, labels, reach | no |
| `verifier` | keeps or drops each requested change, checked against the code | no |
| `resolver` | resolves a landing train's conflicted files, keeping every change's intent | only those files |
| `approver` | READY or ESCALATE, for the person at ship | no |

Only the builder and the resolver edit, the resolver only the files a conflict names:
`factory.py resolve --continue` refuses a resolution that changed any other file. The others
return text, and the skill writes it to the change's folder.

**What each agent is told** for each step is text in `plugins/factory/prompts/`, one file per task
(`build.md`, `review.md`, `land-review.md` …) and `common.md` for what several share. Each file's
`## <part>` sections are the pieces the script picks and joins, one line each, and what varies is a
placeholder, `${round}`, which the script fills (`$$` is a literal `$`). A wording change is an
edit there, not in the script. The prompts are read only from the plugin itself, never from a
host's `.sdlc/`, so every repo's agents read the same text. A file whose parts or placeholders
don't match what the script fills refuses the step, naming the file and the part, before any
session starts.

**The UI and UX reviewers** run only in a repo that declares a front end (`[ui]`, below), and only
on a round whose diff touches its `paths`; once one round runs them, the later ones do too. They
never make a run's depth full. Neither has a shell: before each runs, `factory.py agent` starts
the dev server `[ui]` names on a free port (on a new one, up to three tries, when another process
takes it first, each lost try in `shots.json`'s `retries`; only a port that already answers, or
won't bind once the server has exited, is lost, and a server that fails on its own is started
once), takes each page at each width with its screenshot command, stops the process group it
started, and gives the reviewer the images and the changed paths. A shot that fails refuses that
review, with what the commands printed, so neither judges a page it couldn't see. The images go
under `.sdlc/reports/shots/<change>/round-<N>/<role>/` with a `shots.json` of what ran, a folder
that ignores itself, so none is committed. Each reviewer has its own folder, fixture copy and
server, so a round's two start together.

## What it leaves in the change's folder

```
.sdlc/work/NNN-slug/
  build/round-<N>.md            the builder's reports, each ending with its ## Evidence
  build/round-<N>.files         what each round's build left, hashed by path
  build/round-<N>.gate.md       opens GATE: PASS or GATE: FAIL, then each attempt of the gate
  reviews/round-<N>/<role>.md   each opens VERDICT: PASS or VERDICT: CHANGES, then - CHANGE: lines
  reviews/round-<N>/verified.md - KEPT: and - DROPPED: lines, one per change asked for, by its id
  decisions.md                  the ledger of the calls that are yours, each one's options under it
  decision.md                   opens DECISION: READY or DECISION: ESCALATE
  decision-<n>.md               an escalated run's decision, kept as it was when it was sent back
  build/round-<N>.restart.md    RESTART: decision-<n>.md, and WORDS: R<k> with your words: round N
                                starts the run again
  build/round-<N>.upgraded.md   UPGRADED: D<k>, the decision your answer upgraded to Tier 2 by:
                                round N is the upgraded run's first
  notes.md                      - [ ] lines for what the last round still kept, and pre-existing ones
  findings.md                   every agent finding of every complete round, the landing's too,
                                once, By: its role, as fixed, recorded, wrong (the verifier's
                                drop) or a nit, a nit to file with its Theme:, Cost: and Value::
                                the same record ship writes, counted apart from ship's own
  runs/spec-draft.md            the spec-writer's draft, whole, which write-spec copies into
                                spec.md after your yes
  runs/spec-questions.md        the open questions it resolved and left, after the draft's ---
  runs/<agent>.sessions         each agent session's id, one a line, which close's measuring reads
  runs/costs.jsonl              each agent run's reported cost, duration and tokens, with its role
                                and model, its task, its round (or landing round, land), and its
                                purpose: spec, build, rework, gate-fix, mend, rerun or land
  runs/ejections.jsonl          each time a landing train put the change back: when (at), its
                                landing round (land), why (cause: gate, review, refusal or
                                stop) and which train (train, when it began), so the
                                retrospective counts that landing's runs as waste, and its
                                ejections and stops as overrides; a row that can't be written
                                is a problem in the eject's or stop's output, never a refusal
  runs/stopped.md               while the run is stopped: STOPPED: ship, mend or rerun, the NEXT:
                                step in a few words, a longer sentence saying why, each
                                - PROBLEM: as verdicts worded it, and, for a run that had
                                stopped early, its - STUCK: and - UNTESTABLE: lines; removed by
                                the first reading that finds the cause gone
  runs/step.md                  the step the supervisor's last reading named, for the board's
                                track, the depth it reviews at (DEPTH: full or light), and
                                - STUCK: and - UNTESTABLE: lines when the run stopped early
```

**What a run cost, while it runs.** Every agent run's result reports its cost and tokens, and
`factory.py agent` keeps those figures in `runs/costs.jsonl`: numbers and names only, never a
prompt or a reply. The hand-back to `stage: test` and `factory.py ready` give each change's total,
split by role and by model, so you can see where the spend goes before you ship and tune
`[models]` or `rounds` from it. It is the API-equivalent figure Claude Code reports; on a
subscription it shows where the spend went, not a bill. A resumed builder's session reports its
total so far, so a session counts once, at its last figure.

All of it is committed with the change, at `/sdlc-factory:land` or `/sdlc:ship`, so history keeps
how the change was made. `findings.md` is written by `factory.py carry` at the approve step, and
rewritten by a rerun, which replaces only the sections a factory role raised; `land --close` adds
its landing rounds' findings the same way, each `Class:` naming its landing round, and commits it
with no `Sdlc-Findings` trailer, so `/sdlc:retro` compares the two ways of building from one
record without counting the agents' review as yours.
Since it is public, every record is filed in a form the repo's own scan accepts: this machine's
paths as marks (`<path-to-clone>`, `<home>`), the change's own folder by its full name, and any
other shape the scan refuses, such as a test fixture's change cited by its bare number in
quoted output, as a placeholder (the number in `<` and `>`). The approver's step stops the change
when its folder still holds such a line (one written by hand, or filed before this rule), naming the
file and line; `factory.py defuse NNN` rewrites it the same way.
`/sdlc:close` counts from it what the run cost in rework (rounds after the first, red gates,
`CHANGES` verdicts, the changes the verifier dropped, an `ESCALATE`, a default you overturned at
ship), so a factory change and one built by hand are measured the same way.

## Configuration: `.sdlc/factory.toml`

Optional. The defaults:

```toml
reviewers = ["code", "security", "test", "behaviour"]   # the full depth: which reviewers run
rounds = 3                                 # review rounds before the approver decides anyway (1-5)

[light]                                    # the depth a diff touching no sensitive path gets
reviewers = ["code"]                       # unset, "behaviour" is added, and "test" for a Tier 2,
rounds = 2                                 # each when the full depth has it; set, it is used as
                                           # written at either tier

mode = "auto"                              # the permission mode agent sessions run in, read from
                                           # the base branch; one of acceptEdits, auto,
                                           # bypassPermissions, manual, dontAsk, plan
gate_jobs = 1                              # the most gates running at once across every
                                           # worktree, read from the base branch

[models]                                   # override a role's model (else the rule above),
                                           # read from the base branch
# code = "haiku"

[land]                                     # /sdlc-factory:land, read from the base branch
auto = true                                # a batch with no risk signal lands without asking
batch = 5                                  # the most changes one landing takes
moves = 3                                  # the most times a landing follows the base branch

[ui]                                       # a front end, read from the base branch; unset, no
                                           # UI review runs
# serve = "npm run dev -- --port {port}"   # the dev server, on the port shots picks
url = "http://127.0.0.1:{port}"            # where it answers
pages = ["/"]                              # the pages to shoot
# paths = ["web/", "src/components/"]      # the paths that count as UI
# shoot = "npx playwright screenshot --viewport-size '{width}, {height}' {url} {out}"
widths = [[1280, 800], [390, 844]]         # each page at each of these
timeout = 60                               # seconds the server gets to answer
# fixture = "fixtures/demo"                # data in the checkout serve is given, as {fixture}
```

`mode`, `gate_jobs`, `[models]`, `[land]` and `[ui]` are read from the base branch's copy of the
file, never a change's own, so a change can't widen what its agents may do unasked, pick its own
agents' models, or choose the command a UI review starts, and a setting committed on the base
branch reaches every open change at once, its worktree made before it or not. `serve`, `shoot` and
`paths` must all be set for a UI review; the screenshot command is yours, so any tool that writes a
PNG to `{out}` will do, and Playwright's CLI is one (`npx playwright install chromium` once, or
`uvx --from playwright playwright …` without Node). A page that fills in after it loads needs the
command to wait for it (Playwright's `--wait-for-selector '<css>'`), or the shot shows it empty. A
page that shows only what its data holds needs data holding each state a change could add. Name it
in `fixture`: a file or folder in the checkout, so a change that adds a state adds its data in the
same diff. Before each shot, `shots` copies it afresh to
`.sdlc/reports/shots/<change>/<label>/<role>/fixture/` and puts that copy's path, relative to the
checkout, in `serve`'s `{fixture}`, so a server that writes to its data never touches the
committed fixture or the next shot's. A fixture the checkout lacks refuses the UI review, with no
server started; seeding a database or building a repo from it is `serve`'s job.
An agent session can't answer a tool prompt, so a command its mode doesn't allow is refused, and
the agent reports it.

A run takes at most `2 + rounds × (reviewers + 4)` agent runs at the full depth (26 with the
defaults: each round's reviewers, the verifier, the builder's rework and its two fixes of a red
gate; two more a round with `[ui]` set), and the build skill shows the number before you approve
it, whatever depth the diff turns out to need.

### Why these defaults

The light depth's reviewers and the reviewers' model were chosen from what four light factory
runs' landings caught that their build rounds had passed, read from each change's records (its
`runs/costs.jsonl` for the models, its `reviews/` for what each round and each landing round kept):

| Change | Tier | Build rounds | Ran in the rounds | The landing kept | A build round would have caught it with |
|---|---|---|---|---|---|
| 124 | 1 | 2 | code, ui, ux on haiku | ui: a heading outranking the drawer's title; ux: an unlabelled checkbox | the same ui and ux reviewers, on sonnet |
| 125 | 1 | 1 | code on haiku | behaviour: "no gate configured" said when no base branch was read | the behaviour reviewer, absent from the light depth |
| 129 | 2 | 1 | code, test on sonnet | test: no test for a rule the landing's rebase added | none: the code it named came with the rebase |
| 131 | 1 | 1 | code on haiku | nothing; its landing gate failed on a machine path in a record | none: not a review's miss |

- **The behaviour reviewer joins the light depth**, since 125's miss was its own: the landing runs
  it after every rebase, so in a build round its catch costs a rework, not a change shipped by
  hand.
- **Every scaled reviewer runs on sonnet**, haiku nowhere unless `[models]` names it: 124's ui and
  ux reviewers were already in its rounds, so only the model could see more.
- **The test reviewer stays out of a Tier 1's light rounds**: 129's miss came with the landing's
  rebase, which no build round sees, and a Tier 1 has no numbered requirements to read tests
  against.
- **`[light] rounds` stays 2 and `rounds` 3**: each miss came from rounds that passed, not rounds
  that ran out.

`/sdlc:retro` counts how often this holds, as `Landing catches: k of n factory-reviewed changes`,
so the next change to these defaults can be decided from a window of runs.

## Mechanism

`scripts/factory.py` does what isn't left to a model: which change a session is in and whether its
stage allows the step, where `HEAD` was, what verdict each review holds, the verifier's
answers, the ledger, the depth the diff calls for, and which step the loop takes next (`build`,
`gate`, `fix`, `review`, `verify`, `rework`, `decide`, `upgrade`, `spec`, `approve`, `done` or
`stop`); a Tier 1 change upgraded to Tier 2 on your answer (`upgrade`, through `sdlc`'s own
`upgrade`); the gate itself, the base branch's check run on each build and recorded attempt by
attempt (`gate`), its `[commands] build` once at a landing train's tip (`gate --land --build`, into
`build/land-<n>.build.md`), and an agent's full run of the check that records nothing (`check`),
through one function (`_run_check()`), the only places it runs a host's command, each holding one of `gate_jobs` slots,
an OS lock on `sdlc-factory-gate-<k>.lock` in the git common dir that the OS frees however the gate
ends, and that `sdlc.py gate`, the gate run by hand, takes too, through pinned copies; the change
brought up to the base before a run (`fresh`, through `sdlc`'s own `base` and `resolve`); each agent
session, its prompt, model and reply's file, and the session ids under `runs/` that measuring reads
(`agent`, the one place it runs `claude`); an approved spec draft copied into `spec.md` byte for
byte (`write-spec`); the screenshots a UI review reads, from `[ui]`'s own commands (`shots`, which
`agent` runs first); the changes ready to ship and their order (`ready`); the landing's batch, its
signals and its question (`land-check`), the train and its next step (`train`, with `--begin`, its
`--fix`, `--eject` and `--stop`; `train --run`, the loop that takes each step, under the run lock,
and `--cancel`), each change's landing (`land`, `resolve --onto`, `land-fix`, `land-verdicts`), each
landing step recorded as it starts in `runs/land-step.md` for the board's landing track
(`land-verdicts --record` adds a stop and why, a plain line over the tool's words), its acceptance
checks and skills' cases (`accept`, `cases` and `cases --skip`, never pre-approved, each recording
its step before the commit; the loop runs `accept` itself only as stacked and cleared, and the
approver's judgement of changed checks, `agent --task land-checks`); for the eval and the review, which bugs escaped and through which diff
(`escapes`), the slice of code to look at (`slice`), a report folder (`report-dir`) and the eval's
scores (`score`). It never imports `sdlc.py`: installed from the marketplace, each plugin is cached
on its own, so it reads the register and the `Close` commits' trailers with copies of `sdlc.py`'s
parsing, pinned by tests. For `fresh`, `upgrade` and landing alone it runs the `sdlc.py` of its own
version, beside it (`sdlc-path`: the clone's, or the cache's), so ship, base, upgrade and close have
one implementation; another version is refused.

The landing's own code (`land`, `land-check`, `train`, `resolve` and `land-verdicts`, the one place
the factory commits) lives in `scripts/landing.py` beside it, which `factory.py` loads by path and
binds to a live view of its own names; its docstring says where the line between the two falls.
It is apart so a repo's `[review] sensitive` can name it, as this one's does, without naming the
whole script: a change to the landing is reviewed in depth, a change elsewhere in `factory.py`
needn't be.

## License

MIT. The agents adapt material from [Agent Skills](https://github.com/addyosmani/agent-skills) by
Addy Osmani, under MIT: see `NOTICE`. The loop's shape is the idea behind zazencodes' "Software
Factory for Claude Code"; no text of it is used, since it carries no license.
