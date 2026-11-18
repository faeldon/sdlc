---
name: land
description: Land a batch of factory changes that are ready to ship as one train — each one shipped with the impact its approver proposed, its acceptance checks and skills' cases run, its undone notes carried or dropped, its agents' nits filed as [nit] entries, its assumed decisions confirmed and How to recover in its commit, as ship does, then committed, stacked in order on the base branch (a conflict resolved by one landing agent and reviewed again), gated once at the tip (a red tip bisected and the change at fault left out), and closed in order, archived and pushed as git.push says — through sdlc's own ship and close, behind one approval for the whole batch, which passes itself when no change in it carries a risk signal. Use from the main checkout once the supervisor says changes are ready; after the one yes the train runs unattended in the background (factory.py train --run), stopping only where the person is needed, and a rerun resumes it past that stop. Not for a change built by hand (/sdlc:ship and /sdlc:close), not for one touching an irreversible path its approver proposed no way back for (ship that by hand), and never with --force.
argument-hint: "[NNN… — the ready changes to land; every one when none is named]"
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py sdlc-path *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-check *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train *)'
disable-model-invocation: true
---

# Factory land — ship and close a batch of ready changes

The last stage of a factory change, for a batch of them at once: what `/sdlc:ship` and
`/sdlc:close` do for one change built by hand, done for each ready change in order, behind one
approval. The factory's review rounds stand in for ship's review: the reviewers checked each
change at its depth, the verifier kept what was real, and the approver decided.

**Every step is `sdlc`'s own.** `factory.py` runs the `sdlc.py` of its own version, beside it (the
clone's, or the marketplace cache's), for `ship` and `close`: the stamp, the staging, the merge,
the archive, the push, each one the code `/sdlc:ship` and `/sdlc:close` run. It never copies
them. The batch lands as a **train**: each change is committed in its worktree, stacked on the
one before it in the batch's order (`factory.py resolve --onto`, its own rebase), the base
branch's gate runs once at the stack's tip, and the changes close in order, each by `sdlc.py
close`'s fast-forward, so the base branch's first-parent line reads as a one-at-a-time landing.
`factory.py train` reads the train's state (in the git common dir, never in a tree) and names
each next step; after the yes, `factory.py train --run` takes those steps itself, in order, and
starts the landing's agents, until the batch is landed or a stop needs the person. Each change's commit carries `Sdlc-Landed: by=person`, or `by=auto` when the
gate passed itself, and no `Sdlc-Findings`, so the retrospective never reads a factory review as
the person's. What ship asks a person for beyond its review (the acceptance checks, the skills'
cases, each undone note's disposition, each assumed decision, `How to recover:`) the landing's
question shows and its yes approves: the approver proposed the dispositions and the recovery, and
`factory.py` writes only what was approved. So does each nit its reviewers weighed to file
(`{<theme> <cost> <value>}` on a `- NIT:` line): the script weighs, the yes files.

**Run it from the main checkout.** After the yes, this session runs nothing but the loop, in the
background: the turn ends while the train lands, and the session is free (the supervisor's own
included) until the harness says the loop has exited.

## Step 0 — The batch (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py sdlc-path && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-check <NNN…>
```

`config` gives `land` as the base branch holds it: `auto`, whether a batch with no risk signal
lands without asking, `batch`, the most changes one landing takes, and `land.moves`, the most times
a train follows the base branch moving under it before it stops. `sdlc-path` is the `sdlc.py`
the landing runs; a refusal there (no `sdlc` installed, or another version) is a stop: say it,
and stop. `train` says whether a train is **under way** (`under_way`): one is, when an earlier run
of this skill ended before its train did. Then say so, with its `live`, `landed` and `ejected`
changes, skip Steps 1 and 2 (its batch was approved when it began), and resume it (Step 3,
*Resuming*); a second train is refused while one is under way. A reading with `running: true` is a
loop landing it now: say so, that `train --cancel` stops it after the step in flight, and stop. `land-check` lists the changes `ready` would, in its order (a change after what it
depends on), or those named: `batch`, each with its `intent` (its `title`, `problem` and
`outcome`, quoted from its `intent.md`), its decision, the impact its approver proposed,
the others it `overlaps`, its `signals`, and what the yes approves for it: `checks` (each
acceptance check's `name` and `command`), `cases` (the skills' cases in `scope`, with `cap_usd`,
the ceiling of its own run), `undone` (each unticked `notes.md` item, with the `seed` title, the
`dropped` reason or, for a `pre-existing:` item, the `bug` its approver proposed, with its
`shown` line), `assumed` (each assumed decision, by `id`), `recover` (the `How to recover:`
lines its commit will carry) and `nits` (each agent nit `carry` recorded to file, at most five a
change, with its `title`, `text`, `theme`, `paths`, `cost`, `value`, `pass`, `role`, `round` and
`shown` line), each empty when it has none; `excluded`, the changes only
`/sdlc:ship` can land, and why (an irreversible path with no `- RECOVER:` line in `decision.md`,
or a bug proposed on a severity that isn't the process doc's, with no paths, or on an item that
isn't `pre-existing:`); `over_limit`, those past `batch`; `question`, the batch's question, worded
by the script; `shown`, what that question calls `as shown`, rendered by the script for the dialog
(each change by its title, then its checks, cases, undone notes with their dispositions, assumed
decisions, `How to recover:` lines and agents' nits to file); and `clear`, true when no change in the batch has a
signal.

## Step 1 — Show it

Show the batch in its order. Open each change with what it is, its `intent` quoted as the script
gives it, never summarised: its name and `title`, then its Problem and its Outcome. Then its
decision, its impact, the changes it overlaps (where a rebase may conflict), and each signal.
Under each change, what the yes approves for it, each part only when it has one: each acceptance check's name and its command, as written; the skills'
cases in scope and their cap (`at most $<cap_usd>`, a paid run); each undone item and its
disposition (`→ seed: <title>`, `→ dropped: <reason>`, or a bug's `shown` line, `filed as a bug,
<severity>: <title> (<paths>)`); each assumed decision by id, with what the build assumed; each
nit to file, its `shown` line, `[nit] <title> (<theme>, <cost>, <value>; <paths>)`; and the
`How to recover:` lines. Then the changes `excluded`, each with why and that `/sdlc:ship` from its
worktree lands it, and any `over_limit`, which the next landing takes.
With an empty batch, say why and stop.

**With `clear` true, the gate passes itself.** Say so, `the batch is clear: landing without
asking`, and go to Step 3 with `--by auto`. A signal is anything the plugin's rules don't let it
decide alone: a sensitive or irreversible path, `impact: major` or none proposed, an ESCALATE, a
decision still open or assumed, an issue someone filed (`closes:`), a resolved conflict no
reviewer has seen, a path changed since the last review round's snapshot (or no snapshot), a fix
made while landing, acceptance checks, skills' cases in scope, undone notes, nits to file (and
how many fell past the cap of 5), or `land.auto` off. A
change landed with paths no review read says so on its commit (`Sdlc-Landed: by=person
unreviewed=<n>`). A conflict resolved while landing is seen once every reviewer at the run's depth
passed its landing round; one `sdlc.py resolve` recorded in `conflicts.md`, once the newest
complete build round's reviewers read its files as they now stand. The script decides both;
report them as it words them.

## Step 2 — WAIT for explicit approval

Only when the batch isn't clear. Ask `land-check`'s `question` literally, as printed; never word
your own. Its fullest form, each clause there only when some change in the batch has what it
names:

> `Land <n> changes in this order, <NNN-slug, NNN-slug>, each shipped with its approver's impact, its acceptance checks and skills' cases run as shown (at most $<total>), its undone notes carried or dropped and its assumed decisions confirmed as shown, its agents' nits filed as shown, with how to recover shown, committed, stacked in this order on <base>, gated once at the tip (a red tip bisected, the change at fault left out with why and the rest landed; a conflict resolved by one landing agent and reviewed again), brought up to date as often as <base> moves while landing, up to <moves> times, and closed in order, pushed as git.push says? (yes / yes, with a fix / leave one out / no)`

`<moves>` is `config`'s `land.moves`.

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name, and `land-check`'s
`shown`, as printed, the `preview` of the `yes` and `yes, with a fix` options, so what the yes
files and confirms is in the dialog itself, not only above it. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, right after `shown`, and stop.

**Do nothing until the person says yes.** Approval is for this batch only. `leave one out` is
the person naming which: run Step 0 again with the rest, and ask again. To change a proposed
disposition, leave that change out and ship it with `/sdlc:ship`. `yes, with a fix` approves the
batch too, and asks for a fix to one change in it before it is gated: take the change and the
person's words for the fix from what they typed in Other, or else ask for both as plain text. That
is not a second gate, and nothing is written until Step 3. Then Step 3, with `--by person`.

## Step 3 — The train, unattended

**First, what the yes approved running**, each command named here and never in a rule this skill
holds, so the harness asks before each run, for each change in the batch in order:

- for a change with `checks`, its acceptance checks, through `sdlc.py accept`, the attempt
  recorded in `.sdlc/work/NNN-slug/build/land-accept.md`:
  `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py accept <NNN>`
- for a change with skills' cases in scope, `sdlc.py run-cases <NNN>` under its own cap, which
  writes the `Skill evals:` line ship reads (a skipped run says why, and is no stop):
  `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py cases <NNN>`

The loop runs neither.

**A fix the person asked for** (`yes, with a fix`), only for the change it named: write their
words at the end of the change's `decisions.md`, in its folder in its worktree (`Write` it with a
`# Decisions` heading first when it doesn't exist), as a ticked line, `- [x] R<n> (person, fix):
<their words, as they gave them>`, `<n>` one past the highest `R` there, and pass
`--fix <NNN>=R<n>` to `--begin`. The words never go on the command line, only their id.

Then begin the train over the batch, in `land-check`'s order, with who passed the gate (and the
fix, with `--by person` only):

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --begin <NNN…> --by <auto or person>
```

And start the loop with the Bash tool's `run_in_background`:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --run
```

Say `landing <NNN-slug, …> in the background` and end the turn. To cancel it, the person runs
`train --cancel` (it exits after the step in flight, the train still under way), or kills the
task, the hard stop, which a rerun resumes from too.

**What the loop does.** It reads the train, takes the one step the reading names through the
command the script pins for it, and reads again, writing each step to the change's
`runs/land-step.md` for the board. It never commits, rebases or pushes but through those
commands, and only one loop runs at a time (the run lock). The steps:

- **`commit`**: `land <NNN> --by`, in the change's worktree. It refuses, before writing anything,
  a change whose checks haven't passed on it as it stands or whose cases haven't run. On `--by
  person` it writes each disposition (a carried item's seed held in the change's `entries.md`,
  ticked `→ seed: <id>`; a bug held there with its `Severity:` and `Paths:`, ticked `→ bug: <id>`;
  a dropped one ticked `→ dropped: <reason>`), files each nit to file as a `[nit]` entry with its
  `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by:` lines (its `filed_nits`, ids from the
  same `next-entry` call; one already filed for the change is never filed twice), and ticks each
  assumed decision confirmed. Then it sets the approver's impact, runs `sdlc.py ship` (stamped
  shipped, every path staged), adds a `Retire` line to `entries.md` for each open nit its intent
  or spec names by id (its `retired_nits`), and commits with the change's composed message
  (`Retired nits:`, `Carried forward:`, `Dropped:` and `How to recover:` in it, as ship's). The
  change's branch never edits the register: close files what `entries.md` holds, and retires the
  seed, the bugs and the nits, in its `Close` commit.
- **`stack`**: `resolve <NNN> --onto <onto>`, the change rebased onto the stacked commit of the
  change before it (the base branch's tip for the first), its records amended in first;
  `.sdlc/last-id` settles itself (the higher number).
- **`resolve`**: the stack conflicts. One landing agent, the builder in a fresh session, told
  every change in the train, its spec and its diff, resolves the files (`agent <NNN> --task
  train-resolve`); the script stages them with the agent's reply and continues the rebase
  (`resolve <NNN> --continue`). A resolved conflict is reviewed again by every reviewer at the
  run's depth, and **a change in a batch that passed itself closes only once that review
  passes**.
- **`gate`**: `gate <NNN> --land`, the base branch's `[commands] check`, once at the stack's tip,
  before any reviewer reads any change, recorded in `.sdlc/work/NNN-slug/build/land-<n>.gate.md`.
  A red tip is bisected by prefix, at most ⌈log₂ n⌉ more gates, until the change at fault is
  found.
- **`eject`** with `cause` `gate`: the change at fault leaves the train, as the yes approved
  (`train --eject <NNN>`): its branch goes back to its pre-train commit (`git reset --keep`; the
  `undo` is kept in the loop's output), with the reason and the gate file amended into its
  commit; the rest re-stack and the new tip is gated again. When the first change is at fault
  twice in a row, the base branch's own check is the likelier fault: the train stops.
- **`review`**, **`verify`**, **`mend`**: the change's landing round, as `land-verdicts` reads it:
  each missing reviewer, started together (`agent <NNN> --task land-review --role <role>`), the
  verifier when one asks for changes (`--task land-verify`), or each role a mend names, once a
  round (`--task land-mend --role <role>`).
- **`fix`**: the stored fix, once, as soon as that change sits in the stack (after its conflict's
  resolution, if it had one), before any gate: `land-fix <NNN> --ask R<n>`, the change's own
  builder (`agent <NNN> --task land-fix`), `land-fix <NNN> --commit`; the train then stacks what
  is above it on the fixed commit, so the tip's gate and every reviewer at the run's depth read it.
  A fix made while landing stays a signal for the change, so a later landing never passes it by
  itself.
- **`close`**: `land <NNN> --close`, from the main checkout: its own commits rebased onto the base
  past the `Close` commits before it, its `runs/land-train.md` and the landing's record amended
  in, and `sdlc.py close` merges, archives, removes its folder, worktree and branch, and pushes as
  `git.push` says. When the base branch moved since the train last stacked (`moved`), every change
  not landed re-stacks and is gated again, up to `land.moves` times.

**It stops at the first of these**, exits, and changes nothing more: an ejection with any other
`cause` (`review`: a landing review that kept a change, a reply still unreadable after its one
mend, acceptance checks failing as stacked; `refusal`: a landing command's own), a train `stop`
(the base branch moved past `land.moves`, the first change at fault twice in a row, a worktree
gone), `accept` (the checks run again as stacked, behind your prompt), a `commit` whose `before`
names what hasn't run, a refused push (the change has landed; `/sdlc:publish` pushes it), a
command that refuses or an agent session that fails, a cancel, or the same step named twice with
nothing changed.

**When the harness says the loop has exited**, read its JSON: `landed`, `live`, `moves`, `gates`,
`ejected` (each with its `reason` and `cause`), the `undos` of the ejections it made, and either
`done: true` (go to Step 4) or `stopped`, with its `next`, `change`, `cause`, `reason` and
`way_on`, each worded by the script. Report a stop as it words it: the change, why, and the way
on, and that rerunning `/sdlc-factory:land` takes it. Never take the step yourself.

### Resuming

A rerun of this skill finds the train under way (Step 0). With `running: true`, a loop is still
landing it: say so and stop. Otherwise its reading's `next` says what the person's rerun asked
for, and this skill runs that one command, then the loop again in the background:

- `eject`, any `cause` but `gate`: the person chose to leave the change out and go on:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --eject <NNN>
  ```

  Its branch goes back to its pre-train commit with the reason amended in; the person lands it
  later, `/sdlc-factory:land <NNN>` once fixed, or `/sdlc:ship` from its worktree.
- `stop`: every change not landed goes back to its pre-train commit, and the train ends; then
  Step 4, without the loop:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --stop
  ```

- `accept`, or a `commit` whose `before` names `accept` or `cases`: run `factory.py accept <NNN>`
  (or `cases <NNN>`) as above, behind the harness's prompt; the cases never run again once run,
  since each run is paid.
- anything else: the loop takes it.

Then `train --run` with `run_in_background`, as above.

## Step 4 — Report and stop

Say whether the gate passed itself or the person approved it, how many times the tip was gated
and the base branch moved. Then each change: landed (its `Close` commit and where it was
archived), ejected (why, in the script's words; whether the loop made it on a gate fault, its
`cause` `gate`, with its undo, or the person resumed past it; and what the person does next:
`/sdlc-factory:land NNN` once fixed, or `/sdlc:ship NNN` from its worktree), put back by a stop,
excluded, or not reached. For a landed change, each acceptance check and its result (and again as stacked), the
cases' score or why they were skipped (run before any stack), each undone item's disposition and
where it went (the seed's id, in the register once it closed), and each decision confirmed. Say
what was pushed, or that nothing was, and that nothing was tagged.

## Out of scope

- A change built by hand: `/sdlc:ship` and `/sdlc:close`.
- Running a check or a case from this skill's own rules, or by `sdlc.py` directly: only through
  `factory.py accept` and `cases`, behind the harness's prompt.
- Wording a disposition, a confirmation or `How to recover:` the approver didn't propose: a change
  that needs another goes to `/sdlc:ship`.
- `--force`, a merge that isn't a fast-forward, a stash, or resolving a conflict any way but by
  the train's landing agent, reviewed again.
- A step the train's reading didn't name, a step the loop is taking, or a second train or
  loop while one is under way.
- Writing or editing a review, a verification or a decision an agent didn't return.
