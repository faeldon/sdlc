---
name: decide
description: Walk the person through one factory change's open decisions and assumed defaults at stage test, one at a time — each with its background, the default, the alternatives the agent weighed and why it chose the default — and after one approval record their answers in the change's decisions.md and say what the change needs next. Use after a factory run escalates, when status says a change needs its defaults confirmed, or to answer a READY change's defaults carried to the landing before it lands. Not for a run still building (the supervisor asks its own blocking decisions), not for more than one change at once, and never to rebuild, ship or land a change.
argument-hint: "[NNN — the change whose decisions to take]"
allowed-tools:
  - Read
  - Edit
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py ask *)'
disable-model-invocation: true
---

# Factory decide — the person's open calls on one change, one at a time

A factory run leaves the calls its agents couldn't make in the change's ledger,
`.sdlc/work/NNN-slug/decisions.md`: blocking decisions the supervisor didn't get to, and defaults the
build went ahead on. The approver settles the defaults it can from the spec, the code and the
rounds, carries to the landing those the person can weigh from its question (`- CONFIRM:`, on a
READY: the landing's yes confirms them, and this skill takes them too, carried to the landing or
not, for a person who would answer them first, its item's `confirm` the approver's reason), and
escalates the rest, with any other reason it escalates for: a `look`, filed in the
ledger for the person to acknowledge, or a `gate`, which the hand gate clears once it is green on
the change as it stands. This skill asks the person what is left, on one change, one item
at a time, with what they need to judge it in front of them, and records their answers where the
supervisor records its own: `- [x] … → decided: <answer>`.

**It answers nothing itself.** Every answer is the person's, chosen or typed. A line the approver
settled (`→ settled by the approver:`) is its call, shown here as one list and never asked; a person
who wants to overturn one can still change the ledger by hand, or ship by hand, where it is shown.
It starts no agent, and rebuilds, ships and lands nothing: it says which of those comes next.

## Step 0 — What is open (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py ask <NNN>
```

`config` gives no key this skill reads; it is run so a broken `.sdlc/factory.toml` is said first.
A refusal is said, naming the change, with what the person can do instead, and the skill stops:

- **Not at `stage: test`.** At `build` or `design`, a run is still building it: its blocking
  decisions are asked in the session running `/sdlc-factory:build`, so answer them there, and run
  this again once the run reports the change ready to ship. At `plan`, the change hasn't been
  built yet. At `shipped` or `dropped`, there is nothing left to decide.
- **A number that names no change**, or one `ask` can't find: say what it said, and that
  `/sdlc:status` lists the open changes, and those that need deciding under `■ Needs you`.

Otherwise `ask` prints `decision`, the approver's,
`items`, each open line in id order (`id`, `kind`, `source`, `reply`, `question`, `options`, `why`,
`escalated`, `confirm`), `settled`, the defaults the approver settled with its reasons, and `gate`: each
`gate` reason with whether it is `cleared`, and the hand gate's `record`, or null with none.

Tell the person about each uncleared `gate` reason, naming the change: what the approver said, and
that once they have fixed it, the hand gate run from the change's worktree (the command `ask
--answered` names in `then`), green on the change as it stands, clears it; an edit after makes it
stale. Run nothing for it: the gate is the person's own command, never this skill's.

`ask` also prints `autopilot`: each line the factory's autopilot answered while the person was
away (`id`, `kind`, `question`, `answer`), its calls and never theirs. Whenever it holds any, show
them first, naming the change, under their own heading, `Autopilot's calls`, one line each (`D2
(blocking): Keep drafts 30 days or forever? → 30 days`), none of them asked. A call the person
disagrees with is fixed forward: a new seed through `/sdlc:idea`, or a revert once the change has
landed; never an edit of the ledger here.

With no `items`, say that nothing is open on `NNN-slug` and stop. Otherwise show first, naming the
change: the approver's `decision`, and the `settled` list as one block (`The approver settled
these: D3: Log the draft id? (spec R4 forbids it)`), none of them asked.

## Step 1 — Ask each item in a dialog of its own (writes nothing)

For each item in order, read what it needs to be judged: the reply that raised it (`reply`, under
the change's folder), around its `- DECISION:` line, and the part of `spec.md` (or the intent's
Approach, at Tier 1) it touches. Then ask it with `AskUserQuestion`, one item to a dialog, never two
items and never two changes in one: the question's text says the change's `NNN-slug`, who raised
it in which round (`source`), the background in two or three sentences of your own from what you
read, the question as the agent put it, the approver's reason it is the person's (`escalated`),
or, for a default carried to the landing, its reason the landing's yes is enough (`confirm`), the
default and why it was chosen (`why`), and each alternative with its notes. Its options:

- With `options`: the default first, labelled as its option text, then at most three alternatives,
  each its option text, its notes as the option's description. Any more are listed in the
  question's text, for the person to type.
- With no `options` (a ledger from before them, or a bare line): `keep the default` and `change it`.
  For `change it`, ask what they want instead, as text.

- A `look` item (`kind: look`, the approver's reason in `question`, its `reply` `decision.md`): read
  the decision around it, and ask whether they have looked. The question names what to look at:
  the reason's text before ` — `, the file, function or contract the approver put first (the whole
  reason, when it has no ` — `), then why. Its answers are `seen` and `checked something`, and the
  question says what each means: `seen` records it as acknowledged and accepted as built, without
  claiming they verified anything; `checked something` records what they verified, so for it, ask
  what they checked, as text. A look is never answered for them, and never by an agent.

For a blocking item, the first option is the agent's recommendation, marked as such in its
description. Hold each answer: the option the person chose, or their words when they typed one.
Never fill in an answer they didn't give; an item dismissed, empty, timed out or refused is left
open, and said so. These dialogs collect answers and record nothing.

## Step 2 — WAIT for explicit approval

Show each answer under its id, the question and what the person chose: `D2: Page the drafts
list at 50? → 50, the default kept`, or the alternative, or the words they gave. Then ask literally:

> `Record <n> answers in NNN-slug's decisions.md as shown? (yes / change one / no)`

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in them
an option in that order, labelled as written, `header` the skill's name, and each answer as shown
above, under its id as the `preview` of each yes option. A preview past 40 lines keeps its approving
part and ends "… <k> more lines in <path>", or "… <k> more lines, shown above" when no file holds
them yet. Only a chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty,
timed out or refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, right after what the preview holds, and stop.

On `change one`, ask which, ask that item again as in Step 1, and come back to this question. On
`no`, record nothing and stop.

**Do nothing more until the person says yes.**

## Step 3 — Record the answers, and say what's next

`Edit` each answered line in `decisions.md`, that line alone, from `- [ ] D2 (...)` to
`- [x] D2 (...)`, with ` → decided: <answer>` at the end of it, its indented `- OPTION:` and
`- WHY:` lines under it left as they are. The answer is exactly `the assumed default, confirmed`
when the person kept the default; the option's text when they chose an alternative (or, on a
blocking line, the recommendation); and their own words, as they gave them, for anything typed.
A look's answer is `→ decided: seen`, or the words they gave for what they checked.
Then pass the ids, never the words, which go on no command line:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py ask <NNN> --answered <D2,D3>
```

Say its `next` in the person's words, naming the change:

- `decide`: some items are still open (one dismissed, or left out): `/sdlc-factory:decide NNN`
  again takes them.
- `rebuild`: an answer isn't the default the build assumed, so the build doesn't follow it yet;
  or a default kept was a reviewer's or the approver's, which no builder round after it says it
  built (`unbuilt`, each by its id, source and question): confirming it chose something the code
  doesn't do yet. Name each `unbuilt` line, and say so.
  Run `then`: `/sdlc-factory:build NNN` sends an escalated change back for another build, told the
  answers; for a READY change, `/sdlc:ship NNN` from its worktree, where the rework is done by hand.
- `gate`: every item is answered, and a `gate` reason isn't cleared yet. `then` names the hand
  gate's command, for the person to run from the change's worktree once its fault is fixed.
- `ship`: every answer kept what was built. `/sdlc-factory:land`, or `/sdlc:ship NNN` from its
  worktree.

Start none of them yourself.

## Out of scope

- A run still building: its supervisor asks its blocking decisions in its own session.
- More than one change in a run: `/sdlc:status` lists which need deciding.
- Answering, settling or ticking anything the person didn't answer, or a line the approver settled.
- Rebuilding, shipping, landing or committing the change.
