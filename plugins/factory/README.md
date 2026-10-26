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
  writes why    a person approves     code, security, test reviewers, in rounds    reviews and   lands it
                (WAIT)                builder reworks what they ask for            commits
                                      approver: READY or ESCALATE                  (WAIT)        (WAIT)
                                      (one WAIT, then unattended)
```

- **`/sdlc-factory:spec NNN`** (Tier 2, `stage: plan`): the `spec-writer` agent drafts `spec.md`
  from the intent and the repo's policy and review docs. You read the draft, and nothing is
  written until you say yes. Then `stage: design`.
- **`/sdlc-factory:build NNN`** (Tier 2 at `stage: design`, or Tier 1 at `stage: plan`): one
  approval, showing the agents, each one's model, the round limit and the most agent runs it can
  take. Then it runs unattended, except to ask you about a blocking decision, and stops at
  `stage: test` with everything **uncommitted**. `/sdlc:ship` reviews it and makes the one commit.

The agents never commit, push or merge, and the run stops if `HEAD` moves. **Under the factory,
the builder's `plan.md` is accepted by your approval of the run**, not read by you in plan mode
first. That is the trade this layer makes; the reviewers check the build against the plan and the
spec.

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
| `approver` | READY or ESCALATE, for the person at ship | no |

Only the builder edits. The others return text, and the skill writes it to the change's folder.

## What it leaves in the change's folder

```
.sdlc/work/NNN-slug/
  build/round-<N>.md            the builder's reports
  reviews/round-<N>/<role>.md   each opens VERDICT: PASS or VERDICT: CHANGES, then - CHANGE: lines
  decisions.md                  the ledger of the calls that are yours
  decision.md                   opens DECISION: READY or DECISION: ESCALATE
  notes.md                      - [ ] lines for what the last round still asked for
```

All of it is committed with the change at `/sdlc:ship`, so history keeps how the change was made.
`/sdlc:close` counts from it what the run cost in rework (rounds after the first, `CHANGES`
verdicts, an `ESCALATE`, a default you overturned at ship), so a factory change and one built by
hand are measured the same way.

## Configuration: `.sdlc/factory.toml`

Optional. The defaults:

```toml
reviewers = ["code", "security", "test"]   # which reviewers run each round
rounds = 3                                 # review rounds before the approver decides anyway (1-5)

[models]                                   # override an agent's model
# builder = "sonnet"
```

A run takes at most `2 + rounds × (reviewers + 1)` agent runs (14 with the defaults), and the build
skill shows the number before you approve it.

## Mechanism

`scripts/factory.py` does what isn't left to a model: which change a session is in and whether its
stage allows the step, where `HEAD` was, what each review's first line says, the ledger, and which
step the loop takes next (`build`, `review`, `rework`, `decide`, `approve`, `done` or `stop`). It doesn't
call `sdlc.py`: installed from the marketplace, each plugin is cached on its own.

## License

MIT. The agents adapt material from [Agent Skills](https://github.com/addyosmani/agent-skills) by
Addy Osmani, under MIT: see `NOTICE`. The loop's shape is the idea behind zazencodes' "Software
Factory for Claude Code"; no text of it is used, since it carries no license.
