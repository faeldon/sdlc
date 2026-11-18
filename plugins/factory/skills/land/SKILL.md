---
name: land
description: Land a batch of factory changes that are ready to ship as one train — each one shipped with the impact its approver proposed, its acceptance checks and skills' cases run, its undone notes carried or dropped, its agents' nits filed as [nit] entries, its assumed decisions confirmed and How to recover in its commit, as ship does, then committed, stacked in order on the base branch (a conflict resolved by one landing agent and reviewed again), gated once at the tip (a red tip bisected and the change at fault left out), and closed in order, archived and pushed as git.push says — through sdlc's own ship and close, behind one approval for the whole batch, which passes itself when no change in it carries a risk signal. Use from a session of its own in the main checkout once the supervisor says changes are ready; a rerun resumes the train under way. Not for a change built by hand (/sdlc:ship and /sdlc:close), not for one touching an irreversible path its approver proposed no way back for (ship that by hand), and never with --force.
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
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py gate *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-verdicts *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-fix *)'
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
each next step; this skill runs it and asks again. Each change's commit carries `Sdlc-Landed: by=person`, or `by=auto` when the
gate passed itself, and no `Sdlc-Findings`, so the retrospective never reads a factory review as
the person's. What ship asks a person for beyond its review (the acceptance checks, the skills'
cases, each undone note's disposition, each assumed decision, `How to recover:`) the landing's
question shows and its yes approves: the approver proposed the dispositions and the recovery, and
`factory.py` writes only what was approved. So does each nit its reviewers weighed to file
(`{<theme> <cost> <value>}` on a `- NIT:` line): the script weighs, the yes files.

**Run it from a session of its own in the main checkout.** Landing takes this session while it
runs; the supervisor's stays free for the next change.

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
changes, skip Steps 1 and 2 (its batch was approved when it began), and resume it at Step 3; a
second train is refused while one is under way. `land-check` lists the changes `ready` would, in its order (a change after what it
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
batch too, and asks for a fix to one change in it before it closes: take the change and the
person's words for the fix from what they typed in Other, or else ask for both as plain text. That
is not a second gate, and nothing is written until Step 3. Then Step 3, with `--by person`.

## Step 3 — The train

Begin it over the batch, in `land-check`'s order, with who passed the gate:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --begin <NNN…> --by <auto or person>
```

Then loop: read the train, do the one step it names, read again, until it says `done` or `stop`.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train
```

Each reading names `next`, the `change` it is for (and its `worktree`), the train's `live`,
`landed` and `ejected` changes, its `moves` out of `limit`, and the `changes` with each one's
pre-train and stacked commits. The script decides every step; never skip one, reorder them, or
take one it didn't name. Its `next`:

- **`commit`**: the change's first half, in its worktree. First, run what the yes approved
  running, each command named here and never in a rule this skill holds, so the harness asks
  before each run, as the reading's `before` lists them:
  - `accept`: `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py accept <NNN>`,
    which runs its acceptance checks through `sdlc.py accept` and records the attempt in
    `.sdlc/work/NNN-slug/build/land-accept.md`;
  - `cases`: `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py cases <NNN>`,
    which runs `sdlc.py run-cases <NNN>` under its own cap and writes the `Skill evals:` line
    ship reads (a skipped run says why, and is no stop).

  Then:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land <NNN> --by <auto or person>
  ```

  It refuses, before writing anything, a change whose checks haven't passed on it as it stands
  or whose cases haven't run. On `--by person` it writes each disposition (a carried item's seed
  held in the change's `entries.md`, ticked `→ seed: <id>`; a bug held there with its `Severity:` and `Paths:`,
  ticked `→ bug: <id>`; a dropped one ticked `→ dropped: <reason>`), files each nit to file as a
  `[nit]` entry with its `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by:` lines (its
  `filed_nits`, ids from the same `next-entry` call; one already filed for the change is never
  filed twice), and ticks each assumed decision confirmed. Then it sets the approver's impact, runs `sdlc.py ship`
  (stamped shipped, every path staged), adds a `Retire` line to `entries.md` for each open
  nit its intent or spec names by id (its `retired_nits`), and commits with the change's composed
  message (`Retired nits:`, `Carried forward:`, `Dropped:` and `How to recover:` in it, as
  ship's): `state: committed`, its pre-train commit. It never rebases: the train stacks it. The
  change's branch never edits the register: close files
  what `entries.md` holds, and retires the seed, the bugs and the nits, in its `Close` commit. A
  refusal is the change's own failure: the next reading ejects it (`eject`, below) and the rest
  of the train goes on.
- **`stack`**: the change rebased onto `onto`, the stacked commit of the change before it (the
  base branch's tip for the first), by the script's own rebase, from a clean tree, its records
  amended in first; `.sdlc/last-id` settles itself (the higher number):

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve <NNN> --onto <onto>
  ```

  Its `state`: `current` (already there: the first change, when the base hasn't moved),
  `stacked` (it moved: a landing round opened, to be reviewed as stacked), or `conflict`, with
  the `conflicted` files, which the next reading names `resolve`.
- **`resolve`**: the stack conflicts in `files`. One landing agent, the builder in a session of
  its own, told every change in the train, its spec and its diff, resolves them; the script
  stages them and continues the rebase:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task train-resolve && \
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve <NNN> --continue
  ```

  A marker left in a file, or a second conflict (the rebase aborted), is the change's failure:
  the next reading ejects it. A resolved conflict is reviewed again by every reviewer at the
  run's depth, after the tip's gate (`review`, below), and **a change in a batch that passed
  itself closes only once that review passes**: `land --close` refuses it before.
- **`gate`**: the base branch's `[commands] check`, run by the script in the named change's
  worktree, once at the stack's tip (`prefix` of `of`), before any reviewer reads any change,
  recorded in `.sdlc/work/NNN-slug/build/land-<n>.gate.md`:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py gate <NNN> --land
  ```

  A red tip is bisected: the reading then names `gate` on a prefix (the stack up to a change,
  gated in that change's worktree), at most ⌈log₂ n⌉ more, until the change at fault is found.
  When the base branch names no check, no gate runs. A train of one whose change didn't move runs
  none either.
- **`eject`**: the named change is at fault (`reason`: the gate red on the stack up to it, its
  acceptance checks failing as stacked, a landing review that kept a change, a reply still
  unreadable after its one mend, or a refusal of its own) and leaves the train:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --eject <NNN>
  ```

  Its branch goes back to its pre-train commit (`git reset --keep`; the `undo` is printed), with
  the reason and the gate file that shows why amended into its commit, and nothing of it reaches
  the base branch. The changes after it re-stack, and the new tip is gated again. The person
  lands it later: `/sdlc-factory:land <NNN>` once fixed, or `/sdlc:ship` from its worktree.
- **`accept`**: a change with acceptance checks runs them again on its commit as stacked
  (`factory.py accept <NNN>`, as under `commit`, behind the harness's prompt); the cases are
  never run again, since each run is paid.
- **`review`**, **`verify`**, **`mend`**: the named change's landing round, as `land-verdicts`
  reads it (`verdict`): start each `missing` reviewer (behaviour alone after a clean stack, every
  reviewer at the run's depth after a resolved conflict or a fix), the verifier when one asks
  for changes, or each role in `mend` (a behaviour check's missing `## Evidence` or `exit:`,
  verdict lines that disagree, the verifier's unread answers), each once a round, its new reply
  written over the old under `reviews/land-<n>/`, **in one message** when several:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-review --role <role>
  ```

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-verify
  ```

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-mend --role <role>
  ```

  Never patch a verdict, and never write a review an agent didn't. The round's own reading,
  with its `problems`, is always there to look at:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-verdicts <NNN> --record
  ```

  `--record` writes a `stop` to `runs/land-step.md`, which the board's landing track reads, as
  each landing command records the step it runs; leave that file to the script.
- **`close`**: the next change in order, from the main checkout. Its own commits are rebased onto
  the base branch past the `Close` commits before it, its `runs/land-train.md` (its place in the
  train, what it stacked on, the tip's gate) and the landing's record amended in, and `sdlc.py
  close` merges, archives, removes its folder, worktree and branch, and pushes as `git.push`
  says:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land <NNN> --close
  ```

  **A fix the person asked for** (`yes, with a fix`), only for the change it named, once, comes
  here, before its close: the script opens a landing round for it, the change's own builder
  makes it, and the script amends it into the change's commit; the train then re-stacks what is
  above it, gates the new tip, and every reviewer at the run's depth reads the fix. The person's
  words never go in a command line: write them at the end of the change's `decisions.md`, in
  its folder in the worktree the reading names (`Write` it with a `# Decisions` heading first
  when it doesn't exist), as a ticked line, `- [x] R<n> (person, fix): <their words, as they
  gave them>`, `<n>` one past the highest `R` there, and pass `--ask R<n>`. The words never go
  on the command line, only their id:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-fix <NNN> --ask <R1> && \
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-fix && \
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-fix <NNN> --commit
  ```

  Then read the train again. A fix made while landing stays a signal for the change, so a later
  landing never passes it by itself.

  `land --close`'s `state` is `moved` when the base branch moved since the train last stacked
  (another session's landing, an idea filed): nothing was closed, the move is counted once for
  the train (up to `land.moves`), every change not yet landed re-stacks onto the base, the new
  tip is gated again, and each is reviewed as its stack calls for; read the train again. A
  refused push is `push_failed`, never a failed close: the change has landed, and `/sdlc:publish`
  pushes it.
- **`stop`**, with its `reason` (the base branch moved more than `land.moves` times, the first
  change at fault twice in a row, a worktree gone): every change not landed goes back to its
  pre-train commit, and the train ends:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py train --stop
  ```

- **`done`**: every change landed or ejected. Step 4.

## Step 4 — Report and stop

Say whether the gate passed itself or the person approved it, how many times the tip was gated
and the base branch moved. Then each change: landed (its `Close` commit and where it was
archived), ejected (why, in the script's words, and what the person does next: `/sdlc-factory:land
NNN` once fixed, or `/sdlc:ship NNN` from its worktree), put back by a stop, excluded, or not
reached. For a landed change, each acceptance check and its result (and again as stacked), the
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
- A step the train's reading didn't name, or a second train while one is under way.
- Writing or editing a review, a verification or a decision an agent didn't return.
