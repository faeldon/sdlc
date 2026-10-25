---
name: drop
description: Drop a change that won't ship, from its worktree — record why in its intent, commit its folder on its branch, then close it - mirror it to the tracker (its GitHub issue, closed as not planned), record a "Drop NNN-slug" commit on main that keeps main's files and the branch's history, and remove its worktree and branch, behind one approval. Use when a change open in a worktree is being abandoned at any stage. Not for a shipped change (that's /sdlc:close), not for a change with other uncommitted work (it refuses), and never for pushing or deleting anything by force.
argument-hint: "[NNN — the change; default: the worktree this session is in] [why it's dropped]"
allowed-tools:
  - Read
  - Edit
  - ExitWorktree
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py drop *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
disable-model-invocation: true
---

# Drop — end a change that won't ship, and keep its record

A change can stop at any stage: the problem went away, another change covers it, it cost more
than it was worth. Removing its worktree and branch by hand loses everything it was, and the
retrospective never learns what work didn't ship. This skill keeps the record: the reason in the
change's own intent, its commits reachable from `main`, its issue closed as not planned, and a
`Drop NNN-slug` commit `retro` counts.

**Nothing of the change lands.** The `Drop` commit is a merge that keeps `main`'s files exactly
(`git merge -s ours`), so the branch's commits stay in history and `git branch -d` can delete the
branch without forcing. Only the counter `new` wrote comes along, so the number stays spent.

## Step 0 — The plan (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py drop <NNN> --check ; \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close <NNN> --check ; \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config
```

Joined with `;`, not `&&`: both checks exit 1 here, as they should before the reason exists, and
the commands after them still have to run. With no number, both take the worktree this session
is in. `drop --check` names the stage the
change reached, the paths it will commit, and its refusals. Its refusal about a missing
`## Dropped` section is expected here: Step 3 writes it. Any other refusal stands: a shipped
change goes to `/sdlc:close`, and uncommitted work outside the change's folder is the human's to
commit or discard first. `close --check` refuses that the change isn't shipped or dropped until
Step 4 stamps it; read it for everything else, and for `archive.target` (where the change will be
mirrored) or `archive.kept_because` (why it won't be, which is fine). `config`'s `git.base` is
the branch the `Drop` commit lands on, `main` unless the repo's is another; where this skill says
`main`, it means that branch.

## Step 1 — The reason

If the human gave one, use it. Otherwise ask one question: why is it being dropped? Draft the
section from the answer, in their words, concrete: what changed, or what was learned, that made
the change not worth finishing. Its first paragraph goes in the `Drop` commit's body, so make it
stand alone.

```markdown
## Dropped

<why, in a paragraph that stands alone>
```

## Step 2 — Show it

Show the human: the change, the stage it reached, the section, the paths that will be committed
on its branch, where it will be mirrored (or why it won't be), and every refusal other than the
missing section. **If there are any, stop here** and say what each needs.

## Step 3 — WAIT for explicit approval

Ask literally:

> `Drop NNN-slug at <stage>: record this reason in its intent, commit its folder on its branch, record a "Drop NNN-slug" commit on <git.base> that changes no files, archive it to <where> and close it as not planned, then remove its worktree and delete its branch? (yes / edit the reason / no)`

`<where>` is `its GitHub issue` or the host's command. When `archive.kept_because` is set, leave out `archive it to <where> and close it as not
planned, `.

**Do nothing more until the human says yes.** Approval is for this change only.

## Step 4 — Drop it

1. `Edit` the change's `intent.md` to append the approved `## Dropped` section at the end. Leave
   its frontmatter alone: the script stamps it.
2. Record it on the branch:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py drop <NNN>
   ```

   It stamps `stage: dropped` and `dropped_at:`, and commits the folder. Exit 1: report its
   refusals exactly and stop.
3. If this session is in the change's worktree, call `ExitWorktree` with `action: "keep"`, so the
   session is back in the main checkout before its worktree goes. Never `"remove"`: that deletes
   the branch whether or not anything keeps its commits. If it answers `No-op: there is no active
   EnterWorktree session`, the session came in by `cd` or started there: go on to 4, where exit 3
   is that case.
4. Close it:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close <NNN>
   ```

   - Exit 0: mirrored, recorded in the `Drop` commit, worktree removed, branch deleted.
   - Exit 3: recorded, but the worktree was kept because this process runs inside it. Finish with
     `/sdlc:close NNN` from a session in the main checkout.
   - Exit 1: a step refused. Report `done` and `skipped` exactly as printed. The drop is already
     committed on the branch, so a rerun is `/sdlc:close NNN`, which picks up where it stopped.

## Step 5 — Report and stop

Report the stage it reached, what `done` lists, where it was mirrored (`archive.location`) or why
it wasn't, and where the session is now. Be explicit that nothing was pushed and nothing was
forced.

## Out of scope

- A shipped change: `/sdlc:close`.
- `git push`, `--force`, `git branch -D`, `ExitWorktree` with `remove`.
- Committing or discarding work outside the change's folder. The human decides what to keep.
- Writing anything in the intent but the `## Dropped` section.
