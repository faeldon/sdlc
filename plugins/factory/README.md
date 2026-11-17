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
- **`/sdlc-factory:land [NNN…]`**, from a session of its own in the main checkout: the ready
  changes as one batch, in that order, each shipped with the impact its approver proposed and
  the nits its intent or spec names by id retired, committed, brought up to date with the base branch and closed, through `sdlc`'s own `ship`,
  `base` and `close` (`factory.py` runs the `sdlc.py` of its own version, beside it, never a
  copy). A change the base branch moved under is gated by the script again, as rebased, before
  its review; a red gate stops it, for you to ship by hand. A rebase that conflicts goes to the
  change's own builder, and every reviewer at its depth checks the resolution before it lands;
  what the landing deleted from the register (the change's own seeds, the bugs it fixes, the nits
  it retired) stays deleted whatever the resolution kept.
  When the base branch moves again before a change closes, the landing goes back to that change's
  rebase, gates and reviews it as it now stands, and closes it, up to `[land] moves` times. Answer
  `yes, with a fix` and name the change, and the fix goes to its own builder, is gated, and every
  reviewer at its depth reads it before it lands. Your words for it go into the change's
  `decisions.md` as a ticked `(person, fix)` line, never on a command line. A path changed after
  the last review round any other way is a signal, and the commit says so (`unreviewed=<n>`).
  One approval covers the batch, and it **passes itself when no change in it carries a risk
  signal** (a sensitive or irreversible path, `impact: major`, an ESCALATE, an open or assumed
  decision, an issue someone filed, a resolved conflict no reviewer has seen, a path no review
  read, a fix made while landing, acceptance checks, skills' cases in scope, undone notes),
  recorded as `Sdlc-Landed: by=auto` on the change's commit and never as your review. Otherwise
  its one question shows what your yes approves, for each change: each acceptance check's name
  and command and the skills' cases with their cost cap, each run then through `factory.py
  accept` and `cases` behind the harness's own prompt (a failure stops that change and those
  after it, and a rebased change runs its checks again); each undone note carried to the
  register as a seed or dropped, as its approver proposed; each assumed decision confirmed; and
  the `How to recover:` its commit carries for an irreversible path. A change touching an
  irreversible path its approver proposed no way back for is left for `/sdlc:ship`, which also
  stays the way to land a change by hand.
- **`/sdlc-factory:spec NNN`** (Tier 2, `stage: plan`): the `spec-writer` alone, for a spec you
  want approved on its own before building by hand or with the factory. Then `stage: design`.

The builder may start read-only `Explore` and `Plan` sub-agents of its own while it plans or
reworks, to read code across the repo; they never write, so it stays the only editor. Each
reviewer runs on a model that fits the change: haiku for a Tier 1 at the light depth, sonnet for a
Tier 2 or a run touching a sensitive path, opus for the security reviewer, the builder and the
approver. The supervisor runs on whatever model your session does.

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
  (and `/sdlc-factory:spec NNN`, before its spec-writer) runs `factory.py fresh`, which brings the change's branch up to the base branch through
  `sdlc`'s own `base` (and its `resolve` when the base changed what the change's uncommitted work
  changes), and shows how far behind it was, what moved and the undo. Only the change's own branch
  moves; never a stash, a merge of the base or a force. A real conflict is aborted and left for
  you (`/sdlc:ship` resolves it), and a run that stopped part way at `stage: build` is held where
  it was: its rounds were reviewed on that base, and landing rebases and gates it again.
- **Gated by the script, before any reviewer.** After each builder report, `factory.py gate` runs
  the base branch's `[commands] check` in the change's worktree, never the change's own config, and
  records each attempt in `build/round-<N>.gate.md`. A red gate, or one that changes the tree,
  starts no reviewer: the builder fixes it, at most twice a round, and a third red gate stops the
  change for you. Light runs are gated like full ones. The gate's command can't be changed by the
  change, but the script it runs (a `check.sh`) is in the change's tree: list it in
  `[review] sensitive` to have an edit to it reviewed at the full depth and named at ship.
- **One gate at a time, by default.** Gates from every worktree of the repo share `gate_jobs`
  slots (1 unless the base branch's `factory.toml` says more), so parallel runs' checks don't
  fight over every core. A gate that waits prints `NNN-slug: waiting for a gate slot (1 of 1 in
  use)`, and its wait is not in its `Seconds:`. A gate run by hand (`sdlc.py gate`) shares the
  same slots, waiting at most 30 minutes for one.
- **Verified before reworked.** After each round with a `CHANGES` verdict, the `verifier` checks
  every `- CHANGE:` against the code and keeps or drops it, with why. The builder reworks only what
  it keeps; `/sdlc:ship` shows what it dropped.
- **Later rounds read the rework.** After every builder report, `factory.py snapshot` hashes what
  the build left, so a reviewer back for round 2 reads the paths the rework changed and the kept
  changes, never raises a settled point again, and files a problem in code the change didn't
  touch as `- PREEXISTING:`, carried to `notes.md` for ship, never reworked here.
- **At the cap, step back.** When the rounds run out with changes still kept, the approver must
  ESCALATE and say, under `## Reconsider the approach`, what kept coming back.
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
  each command run as `$ <command>`, the tail of its output, and `exit: <n>`. A reply without
  it, or holding its answer after a preamble (a verdict, the approver's decision, or a verifier's
  answers the script can't read), goes back to the agent that wrote it once a round, a landing
  round included, and its new reply is written over the old; a second stops the run. The gate
  itself is the script's, so "the gate passes" is never taken on an agent's word.
- **Depth follows risk.** With `[review] sensitive` set in the base branch's
  `.sdlc/config.toml`, a diff touching none of those paths runs the light depth (`[light]` below);
  one touching any runs the full depth, and a run never lightens. With no list, every run is full.
  A Tier 2 change's light rounds add the test reviewer, which reads the tests against the spec's
  numbered requirements, unless you set `[light] reviewers` yourself; a Tier 1's run the code
  reviewer alone. The tier picks the reviewers, never the depth.

## Decisions that are yours

An agent that reaches a call that is yours (a trade-off the spec leaves open, a policy, scope)
raises it instead of guessing: `- DECISION: [blocking] ...` or `- DECISION: [default] ...`, with the
options and its recommendation. They're gathered into the change's ledger,
`.sdlc/work/NNN-slug/decisions.md`, each with an id (`D1`, `D2`, …).

- **Blocking**: the run pauses, and the session running it, the only one that can talk to you,
  asks you. Your answer is written into the ledger (`- [x] D1 ... → decided: ...`) and the agent is
  resumed with it.
- **Default**: the run goes on with the agent's stated default, marked as assumed. The approver
  escalates while any is unconfirmed, and `/sdlc:ship` shows every one, so your approval there
  confirms it or sends the change back. A later default that replaces one names it,
  `- DECISION: [default] (supersedes D2) ...`, and the ledger ticks D2 `→ superseded by D4`: no
  longer assumed, shown beside the default that replaced it. A decided line can't be superseded.

## The agents

| agent | does | can change files |
|---|---|---|
| `spec-writer` | drafts `spec.md`, filed in `runs/` for you to approve, copied after your yes | no |
| `builder` | writes `plan.md` and the code, test first, in slices; reworks | yes |
| `reviewer-code` | correctness against the spec, contract, readability, cost | no |
| `reviewer-security` | trust boundaries, injection, authz, secrets, dependencies | no |
| `reviewer-test` | every requirement proven by a test that can fail; reads `checks.md`, never runs it | no |
| `reviewer-behaviour` | runs the spec's end-to-end path on a gated build; reads `checks.md`, never runs it | no |
| `reviewer-ui` | how the change looks: theme fit, spacing, contrast, overflow at phone width, from screenshots | no |
| `reviewer-ux` | how it works for a person: the task, empty, loading and error states, labels, reach | no |
| `verifier` | keeps or drops each requested change, checked against the code | no |
| `approver` | READY or ESCALATE, for the person at ship | no |

Only the builder edits. The others return text, and the skill writes it to the change's folder.

**The UI and UX reviewers** run only in a repo that declares a front end (`[ui]`, below), and only
on a round whose diff touches its `paths`; once one round runs them, the later ones do too. They
never make a run's depth full. Neither has a shell: before each runs, `factory.py agent` starts
the dev server `[ui]` names on a free port (on a new one, up to three tries, when another process
takes it first, each lost try in `shots.json`'s `retries`; only a port that already answers, or
won't bind once the server has exited, is lost, and a server that fails on its own is started
once), takes each page at each width with its screenshot command, stops the process group it started, and gives the reviewer the images and the changed
paths. A shot that fails refuses that review, with what the commands printed, so neither judges a
page it couldn't see. The images go under `.sdlc/reports/shots/<change>/round-<N>/<role>/` with
a `shots.json` of what ran, a folder that ignores itself, so none is committed. Each reviewer has
its own folder, fixture copy and server, so a round's two start together.

## What it leaves in the change's folder

```
.sdlc/work/NNN-slug/
  build/round-<N>.md            the builder's reports, each ending with its ## Evidence
  build/round-<N>.files         what each round's build left, hashed by path
  build/round-<N>.gate.md       opens GATE: PASS or GATE: FAIL, then each attempt of the gate
  reviews/round-<N>/<role>.md   each opens VERDICT: PASS or VERDICT: CHANGES, then - CHANGE: lines
  reviews/round-<N>/verified.md - KEPT: and - DROPPED: lines, one per change asked for, by its id
  decisions.md                  the ledger of the calls that are yours
  decision.md                   opens DECISION: READY or DECISION: ESCALATE
  decision-<n>.md               an escalated run's decision, kept as it was when it was sent back
  build/round-<N>.restart.md    RESTART: decision-<n>.md, and WORDS: R<k> with your words: round N
                                starts the run again
  build/round-<N>.upgraded.md   UPGRADED: D<k>, the decision your answer upgraded to Tier 2 by:
                                round N is the upgraded run's first
  notes.md                      - [ ] lines for what the last round still kept, and pre-existing ones
  runs/spec-draft.md            the spec-writer's draft, whole, which write-spec copies into
                                spec.md after your yes
  runs/spec-questions.md        the open questions it resolved and left, after the draft's ---
  runs/<agent>.sessions         each agent session's id, one a line, which close's measuring reads
  runs/costs.jsonl              each agent run's reported cost, duration and tokens, with its role
                                and model
  runs/stopped.md               while the run is stopped: STOPPED: ship, mend or rerun, the NEXT:
                                step, and each - PROBLEM: as verdicts worded it; removed by the
                                first reading that finds the cause gone
```

**What a run cost, while it runs.** Every agent run's result reports its cost and tokens, and
`factory.py agent` keeps those figures in `runs/costs.jsonl`: numbers and names only, never a
prompt or a reply. The hand-back to `stage: test` and `factory.py ready` give each change's total,
split by role and by model, so you can see where the spend goes before you ship and tune
`[models]` or `rounds` from it. It is the API-equivalent figure Claude Code reports; on a
subscription it shows where the spend went, not a bill. A resumed builder's session reports its
total so far, so a session counts once, at its last figure.

All of it is committed with the change, at `/sdlc-factory:land` or `/sdlc:ship`, so history keeps
how the change was made.
`/sdlc:close` counts from it what the run cost in rework (rounds after the first, red gates,
`CHANGES` verdicts, the changes the verifier dropped, an `ESCALATE`, a default you overturned at
ship), so a factory change and one built by hand are measured the same way.

## Configuration: `.sdlc/factory.toml`

Optional. The defaults:

```toml
reviewers = ["code", "security", "test", "behaviour"]   # the full depth: which reviewers run
rounds = 3                                 # review rounds before the approver decides anyway (1-5)

[light]                                    # the depth a diff touching no sensitive path gets
reviewers = ["code"]                       # unset, a Tier 2 adds "test" when the full depth has
rounds = 2                                 # it; set, it is used as written at either tier

mode = "auto"                              # the permission mode agent sessions run in, read from
                                           # the base branch; one of acceptEdits, auto,
                                           # bypassPermissions, manual, dontAsk, plan
gate_jobs = 1                              # the most gates running at once across every
                                           # worktree, read from the base branch

[models]                                   # override a role's model (else the rule above)
# code = "sonnet"

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

`mode`, `gate_jobs`, `[land]` and `[ui]` are read from the base branch's copy of the file, never a change's
own, so a change can't widen what its agents may do unasked, or choose the command a UI review
starts. `serve`, `shoot` and `paths` must all be set for a UI review; the screenshot command is
yours, so any tool that writes a PNG to `{out}` will do, and Playwright's CLI is one
(`npx playwright install chromium` once, or `uvx --from playwright playwright …` without Node).
A page that fills in after it loads needs the command to wait for it (Playwright's
`--wait-for-selector '<css>'`), or the shot shows it empty.
A page that shows only what its data holds needs data holding each state a change could add.
Name it in `fixture`: a file or folder in the checkout, so a change that adds a state adds its
data in the same diff. Before each shot, `shots` copies it afresh to
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

## Mechanism

`scripts/factory.py` does what isn't left to a model: which change a session is in and whether its
stage allows the step, where `HEAD` was, what each review's first line says, the verifier's
answers, the ledger, the depth the diff calls for, and which step the loop takes next (`build`,
`gate`, `fix`, `review`, `verify`, `rework`, `decide`, `upgrade`, `spec`, `approve`, `done` or
`stop`); a Tier 1 change upgraded to Tier 2 on your answer (`upgrade`, through `sdlc`'s own
`upgrade`); the gate
itself, the base branch's check run on each build and recorded attempt by attempt (`gate`, the
one place it runs a host's command), each holding one of `gate_jobs` slots, an OS lock on
`sdlc-factory-gate-<k>.lock` in the git common dir that the OS frees however the gate ends, and
that `sdlc.py gate`, the gate run by hand, takes too, through pinned copies; the
change brought up to the base before a run (`fresh`, through `sdlc`'s own `base` and `resolve`);
each agent session, its
prompt, model and reply's file, and the session ids under `runs/` that measuring reads (`agent`,
the one place it runs `claude`); an approved spec draft copied into `spec.md` byte for byte
(`write-spec`); the screenshots a UI review reads, from `[ui]`'s own commands
(`shots`, which `agent` runs first); the changes ready to ship and their order (`ready`); the landing's
batch, its signals and its question (`land-check`), each change's landing (`land`, `resolve`,
`land-fix`, `land-verdicts`), its acceptance checks and skills' cases (`accept`, `cases`, never
pre-approved);
for the eval and the review, which bugs escaped and through which diff (`escapes`), the slice of
code to look at (`slice`), a report folder (`report-dir`) and the eval's scores (`score`). It never
imports `sdlc.py`: installed from the marketplace, each plugin is cached on its own, so it reads
the register and the `Close` commits' trailers with copies of `sdlc.py`'s parsing, pinned by tests.
For `fresh`, `upgrade` and landing alone it runs the `sdlc.py` of its own version, beside it (`sdlc-path`: the clone's,
or the cache's), so ship, base, upgrade and close have one implementation; another version is refused.

## License

MIT. The agents adapt material from [Agent Skills](https://github.com/addyosmani/agent-skills) by
Addy Osmani, under MIT: see `NOTICE`. The loop's shape is the idea behind zazencodes' "Software
Factory for Claude Code"; no text of it is used, since it carries no license.
