---
name: land
description: Land a batch of factory changes that are ready to ship — each one shipped with the impact its approver proposed, its acceptance checks and skills' cases run, its undone notes carried or dropped, its assumed decisions confirmed and How to recover in its commit, as ship does, then committed, brought up to date with the base branch (a conflict resolved by its own builder and reviewed again), and closed, archived and pushed as git.push says — through sdlc's own ship, base and close, behind one approval for the whole batch, which passes itself when no change in it carries a risk signal. Use from a session of its own in the main checkout once the supervisor says changes are ready. Not for a change built by hand (/sdlc:ship and /sdlc:close), not for one touching an irreversible path its approver proposed no way back for (ship that by hand), and never with --force.
argument-hint: "[NNN… — the ready changes to land; every one when none is named]"
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py sdlc-path *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-check *)'
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
clone's, or the marketplace cache's), for `ship`, `base` and `close`: the stamp, the staging, the
rebase, the merge, the archive, the push, each one the code `/sdlc:ship` and `/sdlc:close` run. It
never copies them. Each change's commit carries `Sdlc-Landed: by=person`, or `by=auto` when the
gate passed itself, and no `Sdlc-Findings`, so the retrospective never reads a factory review as
the person's. What ship asks a person for beyond its review (the acceptance checks, the skills'
cases, each undone note's disposition, each assumed decision, `How to recover:`) the landing's
question shows and its yes approves: the approver proposed the dispositions and the recovery, and
`factory.py` writes only what was approved.

**Run it from a session of its own in the main checkout.** Landing takes this session while it
runs; the supervisor's stays free for the next change.

## Step 0 — The batch (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py sdlc-path && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-check <NNN…>
```

`config` gives `land` as the base branch holds it: `auto`, whether a batch with no risk signal
lands without asking, `batch`, the most changes one landing takes, and `land.moves`, the most times
a landing follows the base branch moving under a change before it closes. `sdlc-path` is the `sdlc.py`
the landing runs; a refusal there (no `sdlc` installed, or another version) is a stop: say it,
and stop. `land-check` lists the changes `ready` would, in its order (a change after what it
depends on), or those named: `batch`, each with its decision, the impact its approver proposed,
the others it `overlaps`, its `signals`, and what the yes approves for it: `checks` (each
acceptance check's `name` and `command`), `cases` (the skills' cases in `scope`, with `cap_usd`,
the ceiling of its own run), `undone` (each unticked `notes.md` item, with the `seed` title or the
`dropped` reason its approver proposed), `assumed` (each assumed decision, by `id`) and `recover`
(the `How to recover:` lines its commit will carry), each empty when it has none; `excluded`, the
changes only `/sdlc:ship` can land, and why (an irreversible path with no `- RECOVER:` line in
`decision.md`); `over_limit`, those past `batch`; `question`, the batch's question, worded by the
script; and `clear`, true when no change in the batch has a signal.

## Step 1 — Show it

Show the batch in its order: each change, its decision, its impact, the changes it overlaps (where
a rebase may conflict), and each signal. Under each change, what the yes approves for it, each
part only when it has one: each acceptance check's name and its command, as written; the skills'
cases in scope and their cap (`at most $<cap_usd>`, a paid run); each undone item and its
disposition (`→ seed: <title>`, or `→ dropped: <reason>`); each assumed decision by id, with what
the build assumed; and the `How to recover:` lines. Then the changes `excluded`, each with why and
that `/sdlc:ship` from its worktree lands it, and any `over_limit`, which the next landing takes.
With an empty batch, say why and stop.

**With `clear` true, the gate passes itself.** Say so, `the batch is clear: landing without
asking`, and go to Step 3 with `--by auto`. A signal is anything the plugin's rules don't let it
decide alone: a sensitive or irreversible path, `impact: major` or none proposed, an ESCALATE, a
decision still open or assumed, an issue someone filed (`closes:`), a resolved conflict no
reviewer has seen, a path changed since the last review round's snapshot (or no snapshot), a fix
made while landing, acceptance checks, skills' cases in scope, undone notes, or `land.auto` off. A
change landed with paths no review read says so on its commit (`Sdlc-Landed: by=person
unreviewed=<n>`). A conflict resolved while landing is seen once every reviewer at the run's depth
passed its landing round; one `sdlc.py resolve` recorded in `conflicts.md`, once the newest
complete build round's reviewers read its files as they now stand. The script decides both;
report them as it words them.

## Step 2 — WAIT for explicit approval

Only when the batch isn't clear. Ask `land-check`'s `question` literally, as printed; never word
your own. Its fullest form, each clause there only when some change in the batch has what it
names:

> `Land <n> changes in this order, <NNN-slug, NNN-slug>, each shipped with its approver's impact, its acceptance checks and skills' cases run as shown (at most $<total>), its undone notes carried or dropped and its assumed decisions confirmed as shown, with how to recover shown, committed, brought up to date with <base> as often as it moves while landing, up to <moves> times (a conflict resolved by its builder and reviewed again), and closed, pushed as git.push says? (yes / yes, with a fix / leave one out / no)`

`<moves>` is `config`'s `land.moves`.

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Do nothing until the person says yes.** Approval is for this batch only. `leave one out` is
the person naming which: run Step 0 again with the rest, and ask again. To change a proposed
disposition, leave that change out and ship it with `/sdlc:ship`. `yes, with a fix` approves the
batch too, and asks for a fix to one change in it before it closes: take the change and the
person's words for the fix from what they typed in Other, or else ask for both as plain text. That
is not a second gate, and nothing is written until Step 3. Then Step 3, with `--by person`.

## Step 3 — Land each change, in order

For each change in the batch, one at a time:

0. **Run what the yes approved running**, from the main checkout, each command named here and
   never in a rule this skill holds, so the harness asks before each run:
   - with `checks`, `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py accept
     <NNN>`, which runs them through `sdlc.py accept` and records the attempt in
     `.sdlc/work/NNN-slug/build/land-accept.md`;
   - with `cases`, `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py cases
     <NNN>`, which runs `sdlc.py run-cases <NNN>` under its own cap and writes the `Skill evals:`
     line ship reads (a skipped run says why, and is no stop).

   A failure, or a prompt the person declines, stops this change and every one after it: nothing
   of it has been written, and `/sdlc:ship` from its worktree lands it.
1. **Ship, commit, bring it up to date:**

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land <NNN> --by <auto or person>
   ```

   It refuses, before writing anything, a change whose checks haven't passed on it as it stands
   or whose cases haven't run. On `--by person` it writes each disposition (a carried item's seed
   in the register, ticked `→ seed: <id>`; a dropped one ticked `→ dropped: <reason>`) and ticks
   each assumed decision confirmed. Then it sets the approver's impact, runs `sdlc.py ship`
   (stamped shipped, its seed dropped, every path staged), deletes from the register each open
   nit its intent or spec names by id (its `retired_nits`), commits with the change's composed
   message (`Retired nits:`, `Carried forward:`, `Dropped:` and `How to recover:` in it, as
   ship's), and runs `sdlc.py base`. Landed before, it adds the earlier landing's record to its
   commit first, so it rebases again when the base moved since. Its
   `state`: `current` (go to 4), `rebased` (the base moved: 2), `conflict` (3), or a refusal,
   which stops this change and every one after it. Every rule of this step applies to each
   round the landing opens, a round sent back by `moved` (5) included.
2. **`rebased`: run the gate and the spec's path again**, on the change as it now stands. The gate
   is the script's: the base branch's `[commands] check`, recorded in
   `.sdlc/work/NNN-slug/build/land-<n>.gate.md`, before any reviewer reads the change (when the
   base branch names no check, `land-verdicts` never asks for it). Then the behaviour check runs
   the spec's path:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py gate <NNN> --land && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-review --role behaviour
   ```

   A red gate stops the second command and this change: `land-verdicts` says `stop`, and the
   person ships it by hand. A change with acceptance checks runs them again, on its commit as
   rebased, when `land-verdicts` says `accept` (after the gate, before the review): the cases are
   never run again, since each run is paid. Then the landing's verdicts, below.
3. **`conflict`: the builder resolves it.** The rebase is started and left for it; `.sdlc/last-id`
   settles itself (the higher number):

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve <NNN>
   ```

   Its `state`: `clean` when nothing but the counter conflicted, so the rebase went on by itself:
   go on as for `rebased`, in 2. Otherwise `conflict`, with the `conflicted` files, for the
   builder:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task resolve && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve <NNN> --continue
   ```

   A marker left in a file, or a second conflict (the rebase aborted), stops this change. Then
   the script's gate on the resolution, `factory.py gate <NNN> --land` as in 2, and once it is
   green, every reviewer at the run's depth reviews the resolution, **in one message**:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-review --role <role>
   ```

   **A resolved change goes on to close once its landing review passes**, in a batch that passed
   itself too: every reviewer at the run's depth has then seen the resolution, so it is no longer
   a signal. `land --close` refuses a change landed `by=auto` while that review hasn't passed.

   **The landing's verdicts**, after 2 or 3:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-verdicts <NNN>
   ```

   Its `next`: `gate` (the change as it now stands hasn't been gated: `factory.py gate <NNN>
   --land`), `accept` (its acceptance checks haven't run on it as it now stands: `factory.py
   accept <NNN>`, as in 0, behind the harness's prompt), `review` (start each `missing` reviewer),
   `verify` (a reviewer asked for changes):

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-verify
   ```

   then read it again; `pass` (go to 4); `mend` (a reply its own agent can give again: a behaviour
   check's missing `## Evidence` or `exit:`, a verdict after a preamble, the verifier's unread
   answers), for each role in its `mend`, **in one message**, then read it again:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-mend --role <role>
   ```

   Each role is mended once a landing round, its new reply written over the old under
   `reviews/land-<n>/`; one that still needs it is a `stop`. Or `stop`, with its `problems`, which
   stops this change and every one after it: a red gate or check or a kept change is the
   person's, and `/sdlc:ship` from its worktree takes it. Never patch a verdict, and never write a
   review an agent didn't.
4. **A fix the person asked for**, only for the change `yes, with a fix` named, once, after its
   round in 1 to 3 passed (else go to 5). The script opens a landing round for it, the change's
   own builder makes it, and the script amends it into the change's commit.

   The person's words never go in a command line: write them at the end of the change's
   `decisions.md`, in its folder in the worktree `land-check` named (`Write` it with a
   `# Decisions` heading first when it doesn't exist), as a ticked line,
   `- [x] R<n> (person, fix): <their words, as they gave them>`, `<n>` one past the highest `R`
   there, and pass `--ask R<n>`. The words never go on the command line, only their id:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-fix <NNN> --ask <R1> && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-fix && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-fix <NNN> --commit
   ```

   A refusal stops this change and every one after it. Then the landing's verdicts, as after 3:
   the gate on the fixed change, then every reviewer at the run's depth (`fixed: true`), in one
   message, and `pass` goes to 5. A fix made while landing stays a signal for the change, so a
   later landing never passes it by itself.
5. **Close it**, from the main checkout, which merges, archives, removes its folder, worktree and
   branch, and pushes as `git.push` says; the landing's own record is added to its commit first:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land <NNN> --close
   ```

   Its `state` is `moved` when the base branch moved since the change was gated, before the close
   or racing it: nothing was closed, the move is recorded, and the change goes back to 1, the
   same change with the same `--by`, gated and reviewed as that round's rebase calls for. In a
   batch that passed itself, it closes without asking once that review passes, as at 1. The
   script stops following after `land.moves` moves, with a refusal. A refusal stops this change
   and every one after it. A refused push is `push_failed`, never a failed close: the change has
   landed, and `/sdlc:publish` pushes it.

## Step 4 — Report and stop

Say whether the gate passed itself or the person approved it. Then each change: landed (its
`Close` commit and where it was archived), stopped (at which step, and why: what the person does
next, usually `/sdlc:ship NNN` from its worktree), excluded, or not reached. For a landed change,
each acceptance check and its result (and again after a rebase), the cases' score or why they
were skipped (run before any rebase), each undone item's disposition and where it went (the
seed's id in the register), and each decision confirmed. Say what was pushed,
or that nothing was, and that nothing was tagged.

## Out of scope

- A change built by hand: `/sdlc:ship` and `/sdlc:close`.
- Running a check or a case from this skill's own rules, or by `sdlc.py` directly: only through
  `factory.py accept` and `cases`, behind the harness's prompt.
- Wording a disposition, a confirmation or `How to recover:` the approver didn't propose: a change
  that needs another goes to `/sdlc:ship`.
- `--force`, a merge that isn't a fast-forward, or resolving a conflict any way but by the
  change's own builder, reviewed again.
- Writing or editing a review, a verification or a decision an agent didn't return.
