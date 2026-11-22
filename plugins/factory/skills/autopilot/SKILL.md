---
name: autopilot
description: Start the factory's autopilot for while you're away — behind one approval of its goal and bounds (a goal from the direction doc, a register theme or your own, the seeds or themes, a dollar cap, hours, the highest tier), the script plans the register's seeds toward that goal, opens their intents, drafts and copies their specs, builds each as soon as what it depends on has landed, answers every escalated call on its default (recorded as autopilot's, never yours), holds anything that touches a guard or a contract, and lands what is ready in batches, until a budget, the cap or the hours run out, then writes a summary to review. Use from the main checkout of a repo whose base branch turns [autopilot] on, with sdlc-factory installed, when nobody will answer the factory's questions for a while. Not for one change (/sdlc-factory:build and /sdlc-factory:land), not while you are at the keyboard to answer them, and never to loosen another skill's approval.
argument-hint: "[a goal, the seeds or themes to take, a dollar cap, hours]"
allowed-tools:
  - Read
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --preview *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --begin *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --run)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --summary)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --cancel)'
disable-model-invocation: true
---

# Factory autopilot — the factory runs from seed to landing while you're away

Every factory change waits on its person several times: the intent's yes, the build's yes, each
escalated call, the landing's yes. Each wait is right while the person is at the keyboard, and the
reason a change sits idle while they aren't. Autopilot is the mode for that time. **One yes, to
this skill's question, approves one bounded run toward one goal**, and nothing else: its goal, its
bounds and the base branch's `[autopilot]` are fixed in the run's state when it begins, and end
with it. It is not a
standing permission, and it loosens no other skill's WAIT: `/sdlc:intent`, `/sdlc-factory:build`
and `/sdlc-factory:land` ask as they always did.

**The script is the scheduler, never this session.** `factory.py autopilot --run` holds the queue,
the waves, the dependencies, the budgets and the off switch, with its state in the git common dir,
so a closed terminal or a compacted session loses nothing and a rerun resumes it. Each judgment
goes to a fresh agent session with no Write, whose reply the script files and checks: the planner
plans the next wave toward the goal, the intent-writer drafts a seed's intent, and the build's own agents (the
spec-writer, the builder, the reviewers, the arbiter, the approver) run as `/sdlc-factory:build`
runs them. This session starts the run and ends its turn.

**What it decides, and how it is recorded.** It answers an escalated default as its default, a look
as seen, and a blocking call with the option its raiser recommended, each as autopilot's, never
yours: the ledger's line says so, each call is in the change's `runs/autopilot.md` and the run's
`escalations.md`, and each landing carries `Sdlc-Landed: by=autopilot`. It never upgrades a change
to Tier 2, never runs the skills' cases or an acceptance check the read-only list refuses, and it
**holds** (leaves unlanded, under Needs you, nothing that depends on it built) a change that
touches a path in the base branch's `[autopilot] guards` (unset, its policy and review docs and
its `[review] irreversible` and `sensitive` paths), one any agent says can only be built by
breaking a contract or would be far simpler with one relaxed, one the approver asks to rethink,
one with a reviewer's or the approver's default no later build made, or one the train or
`land-check` won't take. A call you disagree with is fixed forward, by a revert or
a new seed through `/sdlc:idea`, never mid-run.

**What it runs toward.** One goal, which the yes approves with the bounds: a goal or milestone the
last retrospective set in the direction doc, a register theme the open seeds point at, or one you
state. The goal only narrows what the run takes, never the bounds, the guards or the holds. The
planner groups the candidates by the risk each lowers for the goal, reads the code each points at,
leaves one already fixed or wrong for you (never retiring it), orders the rest by the files they
share, and says what waits and why.

**What bounds it.** The dollar cap and the hours you give; two risk budgets the script counts, never
a model (review debt, its unreviewed calls weighted by kind, and change risk, each landed change's
signals, weighed more when pushed and when stacked), their weights and limits read from the base
branch's `.sdlc/factory.toml`; and the register running out of compelling seeds. Once a budget is
spent nothing new starts and what is in flight is taken on to `stage: test` and left there
unlanded; once the dollars or the hours are spent, no agent session starts at all. Then it writes
`.sdlc/reports/autopilot/<started>/summary.md`: how long it ran and what it cost, its goal and its
plans, what landed, what is mid-build and where, what is held and why, the seeds it left for you,
every call it made, each budget and what spent it, the risks to weigh, and whether the register
grew faster than the run drained it.

## Step 0 — The repo, and a run already under way (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --summary
```

`config` says a broken `.sdlc/factory.toml` first, and gives `land`, the base branch's `[land]`:
with `land.auto` off, autopilot refuses to begin, since it would land by another door. A
`--summary` that refuses has no run to summarise; one that prints `running: true` means a run is
under way: show its summary (what landed, what is in flight, what is held, the calls made, each
budget) and offer to stop it, which writes only the cancel file the loop reads between steps, as
`train --cancel` does, and is no approval of anything:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --cancel
```

Then stop: one run at a time.

## Step 1 — The bounds (writes nothing)

Ask the person, as plain text, for the run's goal and bounds: the goal (optional: a goal or
milestone id from the direction doc, such as `M3`, a register theme as `theme:<name>`, or a goal in
their own words; with none, the preview proposes one), which seeds (by id) or themes it may take
(any, when they name none), a dollar cap and the hours it may run, both required, and the highest
tier it may open (1 or 2, default 2). Then read the run they describe:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --preview --usd <usd> --hours <hours> --goal <goal> --themes <theme…> --seeds <id…> --level <tier>
```

Leave out `--goal`, `--themes`, `--seeds` and `--level` where the person named none; quote a goal in
their own words. `--preview` writes nothing. A `--goal` id the direction doc doesn't hold open is
refused: show the refusal and ask again. It prints `goal` (its `source`, `arg`, `title`, `serves`
and `count`, the candidates in its scope within the bounds: the one stated, or the one proposed,
the first open milestone with a candidate, else the theme with the most), `alternatives` (up to
three other goals, each with its count), `bounds`, `config` (the base branch's `[autopilot]` as the run would fix it:
`enabled`, `parallel`, `wait`, `debt`, `risk`, the weights and the `guards`), `candidates` (the
register's ready seeds within the bounds, in rank order; a seed with an `Issue:` line only when
`--seeds` names it, narrowed to the goal), `land_auto`, `warnings`, the `question` to ask and
`shown`, what its yes approves, which opens with the goal and the alternatives. Show `shown` to the
person as printed, with `goal` and `alternatives`, and say any warning, naming none of a host's
paths beyond what it prints. A `goal` of null (no goal to propose; `question` is null too) means
asking the person for one and running `--preview` again with it: there is no question to ask yet.

## Step 2 — WAIT for explicit approval

Ask `--preview`'s `question` literally, as printed; never word your own. Its form:

> `Run autopilot toward <goal.arg> "<goal.title>" (<goal.source>) until $<usd> or <hours> hours are spent, review debt reaches <debt> or change risk <risk>, or you turn it off: it plans seeds from the register toward that goal within these bounds, opens their intents, drafts and copies their specs unseen, builds them, answers every escalated call on its default (recorded as autopilot's, never yours), holds what touches a guard or a contract, and lands the rest in batches as by=autopilot, pushed as git.push says? (yes / no)`

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in them
an option in that order, labelled as written, `header` the skill's name, and `autopilot --preview`'s
`shown`, exactly as printed, as the `preview` of each yes option. A preview past 40 lines keeps its
approving part and ends "… <k> more lines in <path>", or "… <k> more lines, shown above" when no
file holds them yet. Only a chosen `yes` (or `yes, …`), or a yes typed in Other, approves;
dismissed, empty, timed out or refused is a no. If the tool is unavailable or refused, ask the same
text, answers in parentheses, right after what the preview holds, and stop.

**Do nothing more until the person says yes.** Approval is for this one run, toward this goal,
with these bounds. A no writes nothing. A different goal (one of the alternatives, or their own) or
different bounds are a new `--preview` and the question asked again.

## Step 3 — Begin, and start the loop

On the yes, with the same bounds the preview read and the goal it named, its `goal.arg` (quoted
when it is the person's own words):

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --begin --usd <usd> --hours <hours> --goal <goal.arg> --themes <theme…> --seeds <id…> --level <tier>
```

`--begin` resolves the goal again and fixes it with the bounds. It refuses, writing nothing, with
no `--goal`, with a goal or milestone the direction doc no longer holds open, when the base
branch's `.sdlc/factory.toml` has no `[autopilot]` with `enabled = true`, when `land.auto` is off
there, while a `train --run` or another autopilot runs, or with no dollar cap or hours. **If it refuses, show its refusals and
stop.** Otherwise it writes the run's state in the git common dir and prints the run's `id`. Then
start the loop with `run_in_background`, and end the turn:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py autopilot --run
```

Say that autopilot is running, its bounds, that `/sdlc-factory:autopilot` again shows where it
stands and offers to stop it, and that its summary will be at
`.sdlc/reports/autopilot/<id>/summary.md`. When the loop exits, read its JSON (`reason`, `goal`,
`landed`, `in_flight`, `held`, `left`, `calls`, `debt`, `risk`, `register`, `usd`, `hours`,
`summary`) and report it: why it ended, the goal, what landed, what is held and why, each seed left
for the person as already fixed or wrong, each budget against its limit, whether the register grew
faster than the run drained it, and where the summary and `escalations.md` are. Say plainly that every call in them was autopilot's, for the person to
review, and that a call they disagree with is fixed forward.

## Out of scope

- Approving anything but this one run: no other skill's WAIT, no standing permission.
- Running any step of the loop in this session: the script runs every step, each as its own
  process, and this session only starts it, shows where it stands and stops it.
- Writing or editing the run's records, a change's ledger or its summary.
