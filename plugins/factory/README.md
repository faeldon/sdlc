# sdlc-factory — agents for the change loop, optional

A companion to the `sdlc` plugin. Where `sdlc` has a person drive every stage of a change, this
hands a change's **spec, plan, build and review** to agents, inside the same loop and behind the
same gates. Install it in the repos where you want that; leave it out where you don't. A repo
without it runs `sdlc` exactly as before, and a repo with it can still build any change by hand.

```bash
claude plugin install sdlc-factory@sdlc      # needs sdlc, which it depends on
```

## Where it sits

Inside the change loop, between a person's intent and a person's ship. Nothing before or after
changes, and the release and retrospective loops never see the difference: a change the agents
built is a change.

```
/sdlc:intent ── /sdlc-factory:spec ── /sdlc-factory:build ─────────────────────── /sdlc:ship ── /sdlc:close
  a person      spec-writer drafts    builder plans and builds                     a person      a person
  writes why    a person approves     reviewers, in rounds, at the diff's depth    reviews and   lands it
                (WAIT)                verifier checks what they ask for            commits
                                      builder reworks what it keeps                (WAIT)        (WAIT)
                                      approver: READY or ESCALATE
                                      (one WAIT, then unattended)
```

- **`/sdlc-factory:spec NNN`** (Tier 2, `stage: plan`): the `spec-writer` agent drafts `spec.md`
  from the intent and the repo's policy and review docs. You read the draft, and nothing is
  written until you say yes. Then `stage: design`.
- **`/sdlc-factory:build NNN`** (Tier 2 at `stage: design`, or Tier 1 at `stage: plan`): one
  approval, showing the agents, each one's model, the round limit and the most agent runs it can
  take. Then it runs unattended, except to ask you about a blocking decision, and stops at
  `stage: test` with everything **uncommitted**. `/sdlc:ship` reviews it and makes the one commit.

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

The agents never commit, push or merge, and the run stops if `HEAD` moves. **Under the factory,
the builder's `plan.md` is accepted by your approval of the run**, not read by you in plan mode
first. That is the trade this layer makes; the reviewers check the build against the plan and the
spec.

## Rounds that converge

- **Verified before reworked.** After each round with a `CHANGES` verdict, the `verifier` checks
  every `- CHANGE:` against the code and keeps or drops it, with why. The builder reworks only what
  it keeps; `/sdlc:ship` shows what it dropped.
- **Later rounds read the rework.** After every builder report, `factory.py snapshot` hashes what
  the build left, so a reviewer back for round 2 reads the paths the rework changed and the kept
  changes, never raises a settled point again, and files a problem in code the change didn't
  touch as `- PREEXISTING:`, carried to `notes.md` for ship, never reworked here.
- **At the cap, step back.** When the rounds run out with changes still kept, the approver must
  ESCALATE and say, under `## Reconsider the approach`, what kept coming back.
- **Shown, not said.** Every builder report and every behaviour check ends with `## Evidence`:
  each command run as `$ <command>`, the tail of its output, and `exit: <n>`. `factory.py` stops
  the run on a reply without it, so "the gate passes" is never taken on an agent's word.
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
| `reviewer-test` | every requirement proven by a test that can fail | no |
| `reviewer-behaviour` | runs the gate and the spec's end-to-end path; reads `checks.md`, never runs it | no |
| `verifier` | keeps or drops each requested change, checked against the code | no |
| `approver` | READY or ESCALATE, for the person at ship | no |

Only the builder edits. The others return text, and the skill writes it to the change's folder.

## What it leaves in the change's folder

```
.sdlc/work/NNN-slug/
  build/round-<N>.md            the builder's reports, each ending with its ## Evidence
  build/round-<N>.files         what each round's build left, hashed by path
  reviews/round-<N>/<role>.md   each opens VERDICT: PASS or VERDICT: CHANGES, then - CHANGE: lines
  reviews/round-<N>/verified.md - KEPT: and - DROPPED: lines, one per change asked for
  decisions.md                  the ledger of the calls that are yours
  decision.md                   opens DECISION: READY or DECISION: ESCALATE
  notes.md                      - [ ] lines for what the last round still kept, and pre-existing ones
```

All of it is committed with the change at `/sdlc:ship`, so history keeps how the change was made.
`/sdlc:close` counts from it what the run cost in rework (rounds after the first, `CHANGES`
verdicts, the changes the verifier dropped, an `ESCALATE`, a default you overturned at ship), so a
factory change and one built by hand are measured the same way.

## Configuration: `.sdlc/factory.toml`

Optional. The defaults:

```toml
reviewers = ["code", "security", "test", "behaviour"]   # the full depth: which reviewers run
rounds = 3                                 # review rounds before the approver decides anyway (1-5)

[light]                                    # the depth a diff touching no sensitive path gets
reviewers = ["code"]
rounds = 2

[models]                                   # override an agent's model
# builder = "sonnet"
```

A run takes at most `2 + rounds × (reviewers + 2)` agent runs at the full depth (20 with the
defaults: each round's reviewers, the verifier and the builder's rework), and the build skill shows
the number before you approve it, whatever depth the diff turns out to need.

## Mechanism

`scripts/factory.py` does what isn't left to a model: which change a session is in and whether its
stage allows the step, where `HEAD` was, what each review's first line says, the verifier's
answers, the ledger, the depth the diff calls for, and which step the loop takes next (`build`,
`review`, `verify`, `rework`, `decide`, `approve`, `done` or `stop`); for the eval and the
review, which bugs escaped and through which diff (`escapes`), the slice of code to look at
(`slice`), a report folder (`report-dir`) and the eval's scores (`score`). It doesn't call
`sdlc.py`: installed from the marketplace, each plugin is cached on its own, so it reads the
register and the `Close` commits' trailers with copies of `sdlc.py`'s parsing, pinned by tests.

## License

MIT. The agents adapt material from [Agent Skills](https://github.com/addyosmani/agent-skills) by
Addy Osmani, under MIT: see `NOTICE`. The loop's shape is the idea behind zazencodes' "Software
Factory for Claude Code"; no text of it is used, since it carries no license.
