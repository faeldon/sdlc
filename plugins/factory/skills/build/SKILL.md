---
name: build
description: Hand one change to the factory's agents after one approval — the builder plans and implements it in the change's worktree, the code, security and test reviewers check it in parallel rounds, the builder reworks what they ask for, and the approver writes a READY or ESCALATE decision — leaving everything uncommitted at stage test for /sdlc:ship. Use from the change's own worktree once its spec is approved (Tier 2, stage design) or its intent is written (Tier 1, stage plan), with sdlc-factory installed. Not for drafting the spec (/sdlc-factory:spec), not for committing or shipping (/sdlc:ship), and never to merge or push.
argument-hint: "[NNN — the change; this worktree's]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Agent
  - SendMessage
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py decisions *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py verdicts *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py carry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage *)'
  - 'Bash(git diff *)'
disable-model-invocation: true
---

# Factory build — agents plan, build and review a change

Stages 3 and 4 of the change loop, handed to the factory's agents: the builder plans and
implements, specialist reviewers check the work in rounds, the builder reworks what they ask for,
and the approver recommends. One approval starts it; after that it runs without stopping until it
reaches a decision, runs out of rounds, or hits a problem.

**It ends before anything is committed.** The work stays uncommitted in the change's worktree at
`stage: test`, with every review and the decision in the change's folder, and the person takes it
from there with `/sdlc:ship`, which reviews the diff itself and makes the one commit. No agent
commits, pushes or merges, and the run stops if `HEAD` moves.

**This session is the chief of staff.** Agents can't talk to the person; this session can. When an
agent reaches a call that is the person's (a trade-off the spec leaves open, a policy, scope), it
raises a `- DECISION:` line instead of guessing, and `factory.py decisions` gathers every one into
the change's ledger, `work/NNN-slug/decisions.md`. A **blocking** one pauses the run: this session
asks the person, writes the answer into the ledger, and resumes the builder with it. A **default**
one lets the run go on with the agent's stated default, recorded as assumed; the approver
escalates while any is unconfirmed, and `/sdlc:ship` shows them all.

**Under the factory, the plan is accepted by approving this run.** The builder writes `plan.md` and
builds on it without a person reading it first, which plan mode would otherwise require. That is
the trade this layer makes, and the reviewers check the build against the plan as well as the spec.

## Step 0 — The change and the run (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start <NNN> --for build
```

`config` and `start` give the run's shape from `.sdlc/factory.toml`: the reviewers
(`factory.reviewers`, default code, security and test), the round limit (`factory.rounds`,
default 3), any model a role is set to (`factory.models`), and `max_runs`, the most agent runs
this can take. `start` also gives `head`, the commit the run starts from, and every refusal: not
this change's worktree, or a stage this can't start from (Tier 2 needs `stage: design`, an approved
spec; Tier 1, `stage: plan`). A run that stopped part way left the change at `stage: build`, and
starts again from where its files say. **If there are refusals, show them and stop.** Keep `head`.

## Step 1 — Show it

Show the person: the change and its tier, the agents that will run (builder, each reviewer,
approver) with each one's model (the agent's own unless `factory.models` sets one), the round
limit, and `max_runs`, so the cost is in front of them before they agree to it. Name the files the
run will write: code and `plan.md` by the builder; `build/round-<N>.md`,
`reviews/round-<N>/<role>.md` and `decision.md` by this skill, from the agents' replies;
`decisions.md` for the calls the agents raise; `notes.md` for what the rounds don't resolve. Say
that the run will stop to ask them about any blocking decision, so they know to stay near it.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Run the factory on NNN-<slug>: the builder plans and builds it, <reviewers> review it in up to <rounds> rounds, the approver decides, at most <max_runs> agent runs, all left uncommitted at stage: test? (yes / change the reviewers or rounds / no)`

**Do nothing more until the person says yes.** Approval is for this run only. Changing the
reviewers or rounds is an edit to `.sdlc/factory.toml` and a new question.

## Step 3 — Run it

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> build
```

Every agent prompt starts with `Change folder: <folder>. Worktree: <worktree root>.`, and an
agent spawned with the `Agent` tool gets `subagent_type: "sdlc-factory:<role>"` and its
`factory.models` model when one is set.

1. **Build.** Spawn `sdlc-factory:builder` with `<paths> Build it: plan.md first (Tier 2), then
   the code, test first.` Keep the agent id it returns; every rework resumes this same builder,
   with its context, through `SendMessage`. Wait for its report, and `Write` it, exactly as
   returned, to `work/NNN-slug/build/round-1.md`.

   **Where every builder report goes** decides what gets reviewed, so it has one rule: to
   `build/round-<R+1>.md`, where `<R>` is the highest review round so far (0 before the first).
   After round 1's reviews, the next report is `build/round-2.md`, whether it came from a rework
   or from the person's answer to a decision; the script then calls for round 2's review. Only a
   report from before any review of its round (the builder resumed with an answer while building)
   is added to the end of the existing file.
2. **Ask the script what's next**, after every step from here on: gather the decisions raised so
   far into the ledger, then read the loop's state.

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py decisions <NNN> && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py verdicts <NNN> --head <head>
   ```

   Do what its `next` says, and nothing else:

   - **`build`**: no builder report exists yet (a run that stopped before the first): go back to
     step 1.
   - **`decide`**: a blocking decision is waiting (`pending`). Ask the person with
     `AskUserQuestion`, one question per pending decision (up to four at once): the question as the
     agent put it, the options it gave, its recommendation first and marked as such, and who raised
     it in which round. Record each answer by `Edit`ing its line in `decisions.md` from `- [ ] D1
     (...)` to `- [x] D1 (...)`, with ` → decided: <their answer>` at the end. Then resume the
     agent that needs it: the builder through `SendMessage` (`D1 is decided in decisions.md:
     <answer>. Continue.`), or, for a reviewer's decision, the builder with the round's reviews and
     the answer together, and `Write` its report by the rule above, so the work it did on the
     answer is reviewed. Never answer a decision yourself, and never tick one the person didn't
     answer.

   - **`review`**: spawn every reviewer in `missing` (`sdlc-factory:reviewer-<role>`) **in one
     message**, so they run in parallel, each with `<paths> Review round <round>.` `Write` each
     reply, exactly as returned, to `work/NNN-slug/reviews/round-<round>/<role>.md`. Never resume
     the builder until every reviewer of the round has replied and been written.
   - **`rework`**: `SendMessage` to the builder: `Round <round> reviews are in
     work/NNN-slug/reviews/round-<round>/. Address every VERDICT: CHANGES, then report.` `Write`
     its report to `build/round-<round+1>.md`; the script then says `review` for that round.
   - **`approve`**: first carry what's unresolved into the notes, so `/sdlc:ship` must give each a
     disposition:

     ```bash
     uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py carry <NNN>
     ```

     Then spawn `sdlc-factory:approver` with `<paths> Decide.` and `Write` its reply, exactly as
     returned, to `work/NNN-slug/decision.md`.
   - **`done`**: the decision is in and readable. Go to step 3.
   - **`stop`**: report its `problems` and stop. The change stays at `stage: build`. A reviewer
     reply that doesn't open with a verdict, a decision that doesn't open with one, or `HEAD`
     moving (an agent committed) is a stop: never patch a verdict in, and never reset a commit.
3. **Hand it back.**

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> test
   ```

## Step 4 — Report and stop

Report: the rounds it took, each round's verdicts by reviewer, the decision and its first reason,
the decisions the person made during the run and those still assumed (by id, with the default the
build rests on), what `carry` added to `notes.md`, and the files changed (`git diff --stat`). Lead with ESCALATE when
that is the decision. Say plainly that nothing is committed, and end with the next step:
**`/sdlc:ship NNN`**, which shows the decision and the verdicts with its own review before asking.

## Out of scope

- Committing, pushing, merging, or approving the change: `/sdlc:ship` and `/sdlc:close`, a
  person's steps.
- Drafting the spec: `/sdlc-factory:spec`.
- Editing a review or decision an agent returned, or writing one when an agent didn't.
