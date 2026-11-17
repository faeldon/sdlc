---
name: land
description: Land a batch of factory changes that are ready to ship — each one shipped with the impact its approver proposed, committed, brought up to date with the base branch (a conflict resolved by its own builder and reviewed again), and closed, archived and pushed as git.push says — through sdlc's own ship, base and close, behind one approval for the whole batch, which passes itself when no change in it carries a risk signal. Use from a session of its own in the main checkout once the supervisor says changes are ready. Not for a change built by hand (/sdlc:ship and /sdlc:close), not for one with acceptance checks or undone notes (ship those by hand too), and never with --force.
argument-hint: "[NNN… — the ready changes to land; every one when none is named]"
allowed-tools:
  - Read
  - AskUserQuestion
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py sdlc-path *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-check *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-verdicts *)'
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
the person's.

**Run it from a session of its own in the main checkout.** Landing takes this session while it
runs; the supervisor's stays free for the next change.

## Step 0 — The batch (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py sdlc-path && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-check <NNN…>
```

`config` gives `land` as the base branch holds it: `auto`, whether a batch with no risk signal
lands without asking, and `batch`, the most changes one landing takes. `sdlc-path` is the `sdlc.py`
the landing runs; a refusal there (no `sdlc` installed, or another version) is a stop: say it,
and stop. `land-check` lists the changes `ready` would, in its order (a change after what it
depends on), or those named: `batch`, each with its decision, the impact its approver proposed,
the others it `overlaps`, and its `signals`; `excluded`, the changes only a person can ship, and
why (undone notes, acceptance checks, skills' cases in scope); `over_limit`, those past `batch`;
and `clear`, true when no change in the batch has a signal.

## Step 1 — Show it

Show the batch in its order: each change, its decision, its impact, the changes it overlaps (where
a rebase may conflict), and each signal. Then the changes `excluded`, each with why and that
`/sdlc:ship` from its worktree lands it, and any `over_limit`, which the next landing takes. With
an empty batch, say why and stop.

**With `clear` true, the gate passes itself.** Say so, `the batch is clear: landing without
asking`, and go to Step 3 with `--by auto`. A signal is anything the plugin's rules don't let it
decide alone: a sensitive or irreversible path, `impact: major` or none proposed, an ESCALATE, a
decision still open or assumed, an issue someone filed (`closes:`), a conflict resolved in an
earlier landing, or `land.auto` off.

## Step 2 — WAIT for explicit approval

Only when the batch isn't clear. Ask literally:

> `Land <n> changes in this order, <NNN-slug, NNN-slug>, each shipped with its approver's impact, committed, brought up to date with <base> (a conflict resolved by its builder and reviewed again) and closed, pushed as git.push says? (yes / leave one out / no)`

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Do nothing until the person says yes.** Approval is for this batch only. `leave one out` is
the person naming which: run Step 0 again with the rest, and ask again. Then Step 3, with
`--by person`.

## Step 3 — Land each change, in order

For each change in the batch, one at a time:

1. **Ship, commit, bring it up to date:**

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land <NNN> --by <auto or person>
   ```

   It sets the approver's impact, runs `sdlc.py ship` (stamped shipped, its seed dropped, every
   path staged), commits with the change's composed message, and runs `sdlc.py base`. Its
   `state`: `current` (go to 4), `rebased` (the base moved: 2), `conflict` (3), or a refusal,
   which stops this change and every one after it.
2. **`rebased`: run the gate and the spec's path again**, on the change as it now stands:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-review --role behaviour
   ```

   Then the landing's verdicts, below.
3. **`conflict`: the builder resolves it.** The rebase is started and left for it; `.sdlc/last-id`
   settles itself (the higher number).

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve <NNN> && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task resolve && \
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py resolve <NNN> --continue
   ```

   A marker left in a file, or a second conflict (the rebase aborted), stops this change. Then
   every reviewer at the run's depth reviews the resolution, **in one message**:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-review --role <role>
   ```

   **In a batch that passed itself, a resolved change stops here** once its review passes: a
   resolution is a signal, so it lands at the next `/sdlc-factory:land`, behind the person's yes.
   Go on with the next change.

   **The landing's verdicts**, after 2 or 3:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-verdicts <NNN>
   ```

   Its `next`: `review` (start each `missing` reviewer), `verify` (a reviewer asked for changes):

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task land-verify
   ```

   then read it again; `pass` (go to 4); or `stop`, with its `problems`, which stops this change
   and every one after it: a kept change is the person's, and `/sdlc:ship` from its worktree
   takes it. Never patch a verdict, and never write a review an agent didn't.
4. **Close it**, from the main checkout, which merges, archives, removes its folder, worktree and
   branch, and pushes as `git.push` says; the landing's own record is added to its commit first:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land <NNN> --close
   ```

   A refusal stops this change and every one after it. A refused push is `push_failed`, never a
   failed close: the change has landed, and `/sdlc:publish` pushes it.

## Step 4 — Report and stop

Say whether the gate passed itself or the person approved it. Then each change: landed (its
`Close` commit and where it was archived), stopped (at which step, and why: what the person does
next, usually `/sdlc:ship NNN` from its worktree), excluded, or not reached. Say what was pushed,
or that nothing was, and that nothing was tagged.

## Out of scope

- A change built by hand: `/sdlc:ship` and `/sdlc:close`.
- Running `accept` or the skills' cases: a change that needs them is excluded, and shipped by hand.
- `--force`, a merge that isn't a fast-forward, or resolving a conflict any way but by the
  change's own builder, reviewed again.
- Writing or editing a review, a verification or a decision an agent didn't return.
