# Ship — a conflict with the base branch

Step 0 reads this file when `base` refuses with `resolvable: true`: the base branch changed what
this change changes, and `sdlc.py resolve` can bring the branch up to date file by file. Once a
resolution has finished, `preflight`'s `branches` names it too, for the steps after.

## Step 0

**Resolve it here, rather than stopping.** The script does every git step; you only edit the
files it names. Never run `git stash`, `git merge`, `git rebase` or `git reset` yourself.

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py resolve <NNN>
```

It sets the uncommitted work aside as a temporary commit under `refs/sdlc/aside/<branch>`, rebases
the branch onto the base, and stops at the first conflict. Say its `undo` line. `state: clean`
means nothing needed you: go on to Step 1. `state: conflict` lists `conflicted`, the files to
merge.

For each conflicted file, learn what the base side meant before touching it: the commits the base
branch gained for that file, and the change's own side as the conflict markers show it.

```bash
git log -p ORIG_HEAD..<git.base> -- <file>
```

Then merge it by one rule: **both sides' intent survives.** Keep what each side added. Where both
changed the same lines, write the lines that carry both meanings, never one side's text with the
other's dropped. In `.sdlc/work/inbox.md`, keep every entry either side holds, except one that
either side deleted (a shipped seed, a filed nit), and keep each entry whole. Never take one side
of a file wholesale, and never leave a conflict marker. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py resolve <NNN> --continue
```

It refuses while a file still holds a marker, and names it. `state: conflict` again is the next
of the branch's commits stopping: merge those files the same way and continue. `state: clean`
lists `resolved` and records them in the change's `conflicts.md`: say which files, and go on to
Step 1. The `.sdlc/last-id` counter is the script's to settle, never yours.

**When it can't be done safely, put it back and stop.** A `--continue` refused twice on the same
files, a file whose two sides can't both be kept (each undoes what the other meant), or anything
`resolve` refuses outright:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py resolve <NNN> --abort
```

The worktree is back where `resolve` found it. Stop before Step 1, say which files and why, and
that `/sdlc:ship` can run again once they decide.

## Step 1

**A gate that fails after a resolution** is the resolution's to answer for first: when a failing
test or check sits in a file Step 0 resolved, run `resolve <NNN> --abort` as above, stop, and say
so. A failure elsewhere is reported as any failing gate is.

## Step 3

**The resolution is part of the diff.** In the correctness pass, read each file `conflicts.md`
lists in its final form against both sides (`git log -p` on the base, as in Step 0, and the
change's own intent): a line one side added and the merge dropped is an Important finding, of
class `merge dropped a side`. Ship's question names the resolved files itself, from
`conflicts.md`, so `findings.md` needs no line about it.
