---
name: close
description: Close a shipped change from the session you're in — bring the session back to the main checkout, fast-forward main to the change's branch, mirror its folder to the tracker (its GitHub issue by default), remove the folder from main in a "Close NNN-slug" commit, remove its worktree and branch, and hand the human whatever cleanup command the repo names for a closed change. Use after /sdlc:ship has committed the change in its worktree, or to finish a drop /sdlc:drop committed. Not for a change that is neither shipped nor dropped (it refuses), not for starting a drop (that's /sdlc:drop), and never for pushing, tagging or running the cleanup itself.
argument-hint: "[NNN — the change; default: the worktree this session is in]"
allowed-tools:
  - Read
  - ExitWorktree
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(git log *)'
disable-model-invocation: true
---

# Close — land a shipped change and tidy up after it

The end of a change's life, after `/sdlc:ship` has committed it, folder and all, on its own branch
in its own worktree. What's left is easy to forget or do in the wrong order: fast-forward `main`,
mirror the change to the tracker, take its folder off `main`, remove the worktree and branch, and
clean up whatever the worktree made outside git, if the repo names something. One command does all
but the last behind one approval; the last stays the human's.

**The change's own commit is the copy that counts.** Once it is on `main`, its intent, spec, plan
and notes are in history for good, so the folder can leave the tree: close removes it in a commit
of its own, `Close NNN-slug`, and nothing piles up in `work/`. The tracker (`archive.target` from
`config`: its GitHub issue by default) is where people read it; when one is configured it must
take the copy and read it back before the folder goes, and when there is none, history alone is
fine. The archive renders the issue a last time from the landed folder, with `stage: shipped`:
what `sdlc.py sync` kept current while the change was open. Close never pushes, so it labels the
issue `landed` and leaves it open, and the `Close` commit says `Closes #N`: GitHub closes the
issue once that commit reaches the default branch. Where the default branch isn't `main`, close
closes the issue itself.

**A dropped change closes too**, once `/sdlc:drop` has committed it on its branch (`kind:
"dropped"` in the JSON). Nothing of it lands: close mirrors it, closes its issue as not planned,
and records it as `Drop NNN-slug`, a merge that keeps `main`'s files and makes the branch's
commits reachable, before the worktree and branch go. This skill is how a drop that stopped
partway is finished.

**Everything it runs refuses rather than forces.** `merge --ff-only` won't merge a `main` that has
moved, `git worktree remove` won't remove uncommitted work, `git branch -d` won't delete an
unmerged branch. A refusal is the answer, not an obstacle: say what it was and stop.

## Step 0 — The plan (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close <NNN> --check && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config
```

With no number, it takes the worktree this session is in. From the main checkout with no number,
run `sdlc.py status` instead and ask which of the changes under **Ready to close** to close.

The JSON names the change, its worktree and branch, the main checkout, every refusal, and where the
change will be mirrored: `archive.target`, and `archive.kept_because` when there is nowhere to
mirror to here (`archive.target` is `none`, or GitHub can't be reached), which is a fine
answer: the folder still leaves `main`, and history keeps it.

If `config` sets `commands.close_list`, run it next, with `{suffix}` replaced by the branch name
with `-` as `_`. It is the repo's read-only listing of what a change's worktree left outside git.
None found is a fine answer. With no `close_list`, there is nothing to list; skip it.

## Step 1 — Show it

Show the human: the change, the worktree and branch that will go, the commit `main` will move to,
where the change will be mirrored (or why it won't be), what `close_list` found, and every
refusal. **If there are refusals, stop here** and say what each needs: `/sdlc:ship` first, commit
or remove the stray files, put the main checkout on `main` and commit what's in it, rebase the
branch onto `main` and ship again, or fix `archive` in `.sdlc/config.toml`.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Close NNN-slug: fast-forward main to it, archive it to <where>, commit the removal of work/NNN-slug/ as "Close NNN-slug", then remove its worktree and delete its branch? (yes / no)`

For a dropped change, ask instead:

> `Close dropped NNN-slug: archive it to <where> and close it as not planned, record a "Drop NNN-slug" commit on main that changes no files, then remove its worktree and delete its branch? (yes / no)`

`<where>` is `its GitHub issue` or the host's command. When `archive.kept_because` is set, leave out `archive it to <where>, ` (and `and close
it as not planned`).

**Do nothing more until the human says yes.** Approval is for this change only.

## Step 3 — Land it

1. If this session is in the change's worktree (as `/sdlc:intent` leaves it), call
   `ExitWorktree` with `action: "keep"` first, so the session is back in the main checkout before
   its worktree goes. Never `"remove"`: that deletes the branch whether or not it's merged.
2. Run it from wherever the session now is:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close <NNN>
   ```

   - Exit 0: merged, mirrored (`archive.location`), folder removed in the `Close` commit, worktree
     removed, branch deleted. For a dropped change: mirrored, recorded in the `Drop` commit,
     worktree removed, branch deleted.
   - Exit 3: landed and its folder removed, but the worktree was kept because this process runs
     inside it (a session that came in by `cd`, which `ExitWorktree` can't bring back). Say so;
     finish with `/sdlc:close NNN` from a session in the main checkout.
   - Exit 1: a step refused. Report `done` and `skipped` exactly as printed. A failed mirror stops
     before the folder is removed, and a rerun picks up where it stopped without posting anything
     twice, so offer one once the cause is fixed.

## Step 4 — Report and stop

Report what `done` lists, `main`'s new commits (`git log -2 --oneline main`), where the change was
mirrored (`archive.location`) or why it wasn't, and where the session is now. With
`archive.closes`, say the issue stays open, labelled `landed`, until `main` reaches GitHub, by
`/sdlc:publish` or a push of the human's own, and GitHub closes it then. With
`archive.closed_because`, say close closed the issue now, and why. Say what `measure`
recorded on the `Close` commit, from its `coverage`: which stages this machine's transcripts saw,
or `none:` and why (transcripts off in `metrics.transcripts`, none for this change, or the reader
failed), which never stops a close. When the report has `ran`, say which code ran the close:
`main's code` (the session's own copy of the plugin wasn't the main checkout's) or `merged code`
(the change brought the plugin's scripts, so its own code ran the steps after the merge). If `close_list`
found something and `config` sets `commands.close_cleanup`, end with that one command for the
human, `{id}` replaced by the change's number, and say plainly that only they run it.
Never run it from this session: a cleanup that deletes things is the human's command by design,
and the repo may refuse it from a session anyway.

Be explicit that nothing was pushed or tagged.

## Out of scope

- `git push`, tags, pull requests. Never.
- `--force`, `git branch -D`, `ExitWorktree` with `remove`.
- Running `commands.close_cleanup`, or deleting anything other than the change's own folder, which
  only `sdlc.py close` removes, in a commit, once the change is on `main`. The human's command, by
  design.
- Starting a drop: writing its reason and committing it is `/sdlc:drop`, which has the `Edit`
  this skill doesn't.
