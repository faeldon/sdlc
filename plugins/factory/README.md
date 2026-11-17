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
  change's own builder, and every reviewer at its depth checks the resolution before it lands. One approval covers the batch, and it **passes itself
  when no change in it carries a risk signal** (a sensitive or irreversible path, `impact: major`,
  an ESCALATE, an open decision, an issue someone filed, a resolved conflict no reviewer has
  seen), recorded as `Sdlc-Landed: by=auto` on the change's commit and never as your review. A
  change with acceptance checks or undone notes is left for `/sdlc:ship`, one at a time, which
  also stays the way to land a change by hand.
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

- **Gated by the script, before any reviewer.** After each builder report, `factory.py gate` runs
  the base branch's `[commands] check` in the change's worktree, never the change's own config, and
  records each attempt in `build/round-<N>.gate.md`. A red gate, or one that changes the tree,
  starts no reviewer: the builder fixes it, at most twice a round, and a third red gate stops the
  change for you. Light runs are gated like full ones. The gate's command can't be changed by the
  change, but the script it runs (a `check.sh`) is in the change's tree: list it in
  `[review] sensitive` to have an edit to it reviewed at the full depth and named at ship.
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
- **Shown, not said.** Every builder report and every behaviour check ends with `## Evidence`:
  each command run as `$ <command>`, the tail of its output, and `exit: <n>`. `factory.py` stops
  the run on a reply without it, and the gate itself is the script's, so "the gate passes" is
  never taken on an agent's word.
- **Depth follows risk.** With `[review] sensitive` set in the base branch's
  `.sdlc/config.toml`, a diff touching none of those paths runs the light depth (`[light]` below);
  one touching any runs the full depth, and a run never lightens. With no list, every run is full.

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
  confirms it or sends the change back.

## The agents

| agent | does | can change files |
|---|---|---|
| `spec-writer` | drafts `spec.md`, returned for you to approve | no |
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
the dev server `[ui]` names on a free port, takes each page at each width with its screenshot
command, stops the process group it started, and gives the reviewer the images and the changed
paths. A shot that fails refuses that review, with what the commands printed, so neither judges a
page it couldn't see. The images go under `.sdlc/reports/shots/<change>/round-<N>/` with a
`shots.json` of what ran, a folder that ignores itself, so none is committed.

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
  notes.md                      - [ ] lines for what the last round still kept, and pre-existing ones
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
reviewers = ["code"]
rounds = 2

mode = "auto"                              # the permission mode agent sessions run in, read from
                                           # the base branch; one of acceptEdits, auto,
                                           # bypassPermissions, manual, dontAsk, plan

[models]                                   # override a role's model (else the rule above)
# code = "sonnet"

[land]                                     # /sdlc-factory:land, read from the base branch
auto = true                                # a batch with no risk signal lands without asking
batch = 5                                  # the most changes one landing takes

[ui]                                       # a front end, read from the base branch; unset, no
                                           # UI review runs
# serve = "npm run dev -- --port {port}"   # the dev server, on the port shots picks
url = "http://127.0.0.1:{port}"            # where it answers
pages = ["/"]                              # the pages to shoot
# paths = ["web/", "src/components/"]      # the paths that count as UI
# shoot = "npx playwright screenshot --viewport-size '{width}, {height}' {url} {out}"
widths = [[1280, 800], [390, 844]]         # each page at each of these
timeout = 60                               # seconds the server gets to answer
```

`mode`, `[land]` and `[ui]` are read from the base branch's copy of the file, never a change's
own, so a change can't widen what its agents may do unasked, or choose the command a UI review
starts. `serve`, `shoot` and `paths` must all be set for a UI review; the screenshot command is
yours, so any tool that writes a PNG to `{out}` will do, and Playwright's CLI is one
(`npx playwright install chromium` once, or `uvx --from playwright playwright …` without Node).
A page that fills in after it loads needs the command to wait for it (Playwright's
`--wait-for-selector '<css>'`), or the shot shows it empty.
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
`gate`, `fix`, `review`, `verify`, `rework`, `decide`, `approve`, `done` or `stop`); the gate
itself, the base branch's check run on each build and recorded attempt by attempt (`gate`, the
one place it runs a host's command); each agent session, its
prompt, model and reply's file, and the session ids under `runs/` that measuring reads (`agent`,
the one place it runs `claude`); the screenshots a UI review reads, from `[ui]`'s own commands
(`shots`, which `agent` runs first); the changes ready to ship and their order (`ready`); the landing's
batch and its signals (`land-check`), each change's landing (`land`, `resolve`, `land-verdicts`);
for the eval and the review, which bugs escaped and through which diff (`escapes`), the slice of
code to look at (`slice`), a report folder (`report-dir`) and the eval's scores (`score`). It never
imports `sdlc.py`: installed from the marketplace, each plugin is cached on its own, so it reads
the register and the `Close` commits' trailers with copies of `sdlc.py`'s parsing, pinned by tests.
For landing alone it runs the `sdlc.py` of its own version, beside it (`sdlc-path`: the clone's,
or the cache's), so ship, base and close have one implementation; another version is refused.

## License

MIT. The agents adapt material from [Agent Skills](https://github.com/addyosmani/agent-skills) by
Addy Osmani, under MIT: see `NOTICE`. The loop's shape is the idea behind zazencodes' "Software
Factory for Claude Code"; no text of it is used, since it carries no license.
