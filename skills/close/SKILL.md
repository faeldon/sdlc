---
name: close
description: Close a shipped change from the session you're in — bring the session back to the main checkout, fast-forward main to the change's branch, mirror its folder to the tracker (its GitHub issue by default), remove the folder from main in a "Close NNN-slug" commit, remove its worktree and branch, push main when git.push names close (a GitHub repo's default), then run the cleanup command the repo names for a closed change when commands.close_cleanup_runs says close runs it, or hand it to the human. Use after /sdlc:ship has committed the change in its worktree, or to finish a drop /sdlc:drop committed. Not for a change that is neither shipped nor dropped (it refuses), not for starting a drop (that's /sdlc:drop), and never for a push git.push doesn't name, tagging, or running the cleanup from the skill's own bash.
argument-hint: "[NNN — the change; default: the worktree this session is in]"
allowed-tools:
  - AskUserQuestion
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
of it behind one approval, the cleanup last and only when `commands.close_cleanup_runs` says close
runs it; otherwise the cleanup stays the human's.

**The change's own commit is the copy that counts.** Once it is on `main`, its intent, spec, plan
and notes are in history for good, so the folder can leave the tree: close removes it in a commit
of its own, `Close NNN-slug`, and nothing piles up in `.sdlc/work/`. The tracker (`archive.target` from
`config`: its GitHub issue by default) is where people read it; when one is configured it must
take the copy and read it back before the folder goes, and when there is none, history alone is
fine. The archive renders the issue a last time from the landed folder, with `stage: shipped`:
what `sdlc.py sync` kept current while the change was open. It labels the issue `landed`, and
the `Close` commit says `Closes #N`: GitHub closes the issue once that commit reaches the default
branch. When `config`'s `git.push` names `close`, the default where `archive.target` is
`github`, that is now: the same approval pushes `main` as close's last step, never forced.
Otherwise the issue stays open until `/sdlc:publish` or the human pushes. Where the default branch isn't `main`, close
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

`config`'s `git.base` is the branch close lands on, `main` unless the repo's is another; where this
skill says `main`, it means that branch.

If `config` sets `commands.close_list`, run it next, with `{suffix}` replaced by the branch name
with `-` as `_`. It is the repo's read-only listing of what a change's worktree left outside git.
None found is a fine answer. With no `close_list`, there is nothing to list; skip it.

The JSON's `cleanup`, when the repo sets `commands.close_cleanup`, is the command with `{id}`
filled in, and `runs`: whether close runs it as its last step, after the push, which it does
whatever `close_list` found. `runs` is read from the base branch's config before the merge, so a
change can't turn on its own; `because` says why it is false when that config can't be read.

## Step 1 — Show it

Show the human: the change, the worktree and branch that will go, the commit `main` will move to,
where the change will be mirrored (or why it won't be), what `close_list` found, the command
`cleanup` will run when `cleanup.runs` is true (or `cleanup.because`), and every refusal. When `push.on` is true, show what the push will send to `push.remote`:
`push.unpushed.ahead`, one commit a line, the coming `Close` (or `Drop`) commit first, then the
change's own, then anything else `main` holds that the remote doesn't (inbox commits, another
change's close). It is all of it: git pushes the branch, not one change. With
`push.unpushed` null, say there's no tracking ref to list them from, and the push still goes. **If there are refusals, stop here** and say what each needs: `/sdlc:ship` first, commit
or remove the stray files, put the main checkout on `main` and commit what's in it, rebase the
branch onto `main` and ship again, or fix `archive` in `.sdlc/config.toml`.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Close NNN-slug: fast-forward <git.base> to it, archive it to <where>, commit the removal of .sdlc/work/NNN-slug/ as "Close NNN-slug", then remove its worktree and delete its branch? (yes / no)`

For a dropped change, ask instead:

> `Close dropped NNN-slug: archive it to <where> and close it as not planned, record a "Drop NNN-slug" commit on <git.base> that changes no files, then remove its worktree and delete its branch? (yes / no)`

`<where>` is `its GitHub issue` or the host's command. When `archive.kept_because` is set, leave
out `archive it to <where>, ` (and `and close it as not planned`). When `push.on` is true, end
with `…delete its branch, then push <git.base> to <remote>?`: the yes covers the push and every
commit shown, and they can't be taken back once pushed. When `cleanup.runs` is true, end with
`…, then run <cleanup.command>?`, after the push when there is one, the command word for word:
the yes covers it, for this change only, and what it deletes isn't in git.

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Do nothing more until the human says yes.** Approval is for this change only.

## Step 3 — Land it

1. If this session is in the change's worktree (as `/sdlc:intent` leaves it), call
   `ExitWorktree` with `action: "keep"` first, so the session is back in the main checkout before
   its worktree goes. Never `"remove"`: that deletes the branch whether or not it's merged. If it
   answers `No-op: there is no active EnterWorktree session`, the session came in by `cd` or
   started there: go on to 2, where exit 3 is that case.
2. Run it from wherever the session now is:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py close <NNN>
   ```

   - Exit 0: merged, mirrored (`archive.location`), folder removed in the `Close` commit, worktree
     removed, branch deleted, and pushed when `push` is in `done`. For a dropped change: mirrored,
     recorded in the `Drop` commit, worktree removed, branch deleted, pushed the same way. A push
     the remote refused is `push_failed`, never a failed close: the change has landed.
   - Exit 3: landed and its folder removed, but the worktree was kept because this process runs
     inside it (a session that came in by `cd`, which `ExitWorktree` can't bring back). Say so;
     finish with `/sdlc:close NNN` from a session in the main checkout.
   - Exit 1: a step refused. Report `done` and `skipped` exactly as printed. A failed mirror stops
     before the folder is removed, and a rerun picks up where it stopped without posting anything
     twice, so offer one once the cause is fixed.

## Step 4 — Report and stop

Report what `done` lists, `main`'s new commits (`git log -2 --oneline <git.base>`), where the change was
mirrored (`archive.location`) or why it wasn't, and where the session is now. When `push` is in
`done`, say `main` is on the remote and GitHub closes the issues in `push.closed` now. With
`push_failed`, say why, and that `/sdlc:publish` pushes it (never force a remote that has moved).
Otherwise, with `archive.closes`, say the issue stays open, labelled `landed`, until `main`
reaches GitHub, by `/sdlc:publish` or a push of the human's own, and GitHub closes it then. With
`unpushed` in the report (push off), say what waits for a push, as status does: its closed
changes and the issues a push closes, and `/sdlc:publish`. With
`archive.closed_because`, say close closed the issue now, and why. Say what `measure`
recorded on the `Close` commit, from its `coverage`: which stages this machine's transcripts saw,
or `none:` and why (transcripts off in `metrics.transcripts`, none for this change, or the reader
failed), which never stops a close. With `fixes`, name each bug the `Close` commit records as
fixed, from its `Sdlc-Fixes:` line. When the report has `ran`, say which code ran the close:
`main's code` (the session's own copy of the plugin wasn't the main checkout's) or `merged code`
(the change brought the plugin's scripts, so its own code ran the steps after the merge). With
`cleanup` in `done`, say close ran `cleanup.command` and it exited 0. With `cleanup_failed`, say
why, that the change has landed all the same, and end with `! <cleanup.command>` for the human
to run once the cause is fixed: close won't run it again, since the change is gone. With
`cleanup.runs` false, as before: if `close_list` found something, end with
`! <cleanup.command>` for the human, and say plainly that only they run it.
Never run it from this session: the script runs a cleanup the human approved, and a cleanup the
script didn't run is the human's command, which the repo may refuse from a session anyway.

When the report has `reaches` (only in the plugin's own repo), end with what the human's other
sessions and hosts need, one line for each key it holds: `scripts`, live in every session running
the plugin from this clone, nothing to do; `skills`, named, read when a session starts, so
`/reload-plugins` in each open session that uses them, between stages and never during one, since
old skill text calling the new script can break a run partway; `agents`, the factory's, named, the
same as skills; `hosts`, the files named, which reach a host only through `/sdlc:setup` there, and
`status` there won't nudge until the version moves; `unknown`, its reason, and that the human
reads the change's diff to see which of these apply. Say nothing about it when the report has
none.

Be explicit about what was pushed (or that nothing was), and that nothing was tagged.

## Out of scope

- `git push` from this skill, tags, pull requests. Never: the script's own push step is the only
  one, and only when `git.push` names close.
- `--force`, `git branch -D`, `ExitWorktree` with `remove`.
- Running `commands.close_cleanup` from this skill's bash, or deleting anything other than the
  change's own folder, which only `sdlc.py close` removes, in a commit, once the change is on
  `main`. The cleanup is run by `sdlc.py close` behind the yes that named it, or by the human.
- Starting a drop: writing its reason and committing it is `/sdlc:drop`, which has the `Edit`
  this skill doesn't.
