---
name: release
description: Cut a release from the changes closed since the last one — list them from git history with the impact each recorded at ship, propose the version they add up to, and after one approval bump the version files, add the notes to the changelog if one is set, commit "Release X.Y.Z" and tag it, all locally. Use from the main checkout after a batch of /sdlc:close runs, when it's time for users to get them. Not for a single change still open (ship and close it first), and never for pushing or publishing, which is /sdlc:publish.
argument-hint: "[X.Y.Z — only to release as a version other than the computed one, e.g. a deliberate 1.0.0]"
allowed-tools:
  - Read
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py unreleased *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py release *)'
disable-model-invocation: true
---

# Release — turn a batch of closed changes into a version

The first half of the release loop. The change loop (intent → spec → plan → build → ship →
close) runs once per change and ends on `main`. Releasing runs after a batch of those, over
whatever has landed since the last release: it reads each change's `impact:` from its own commit
in history, takes the highest as the bump, and makes one local commit and one tag. Nothing leaves
the machine here; that is `/sdlc:publish`, behind its own approval.

**History is the source.** Close removes each change's folder from `main`, but the change's own
commit still holds its intent, and the `Close NNN-slug` commit after it names the change. The
boundary is the tag for the version the files hold now, so a release is always "everything since
the version we're on".

## Step 0 — What's landed (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py unreleased
```

`config`'s `release` section says where the version lives (`release.version_files`), what the tag
is called (`release.tag`, `v{version}` by default), whether the notes also go to a file
(`release.changelog`), and the command, if any, that runs after the bump (`release.after_bump`:
a lock file regenerated from the new version, say), and the command, if any, that builds what
`/sdlc:publish` will upload (`release.prepare`). `unreleased` lists each change since the tag (`changes`: id, title,
impact, and `closed: false` for one whose close stopped after its merge), the ones still open in
worktrees (`open`, not in this release), and the proposed `next` version with its `bump`.
`config`'s `git.base` is the branch changes land on and the release is cut from, `main` unless
the repo's is another; where this skill says `main`, it means that branch.

Three answers mean there is nothing to approve yet. Say which and stop:

- **`configure` is set:** the repo hasn't said where its version lives. Name the key and suggest
  the files that hold a `version` line (a manifest, `pyproject.toml`, `package.json`). Adding it is
  a change to `.sdlc/config.toml`, made like any other.
- **`missing` is set:** the current version has no tag, so there is no boundary. Show its `hint`,
  the command that tags the commit that released it. Tagging is the human's call; it's local.
- **`problems` is non-empty:** a change has no valid `impact:`, or the version files disagree.
  Each one names what to fix.

## Step 1 — The plan

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py release --check
```

Add `--version X.Y.Z` only when the human named a version, say a deliberate 1.0.0: below 1.0 a
`major` is released as `minor` on purpose, and only a person decides 1.0.0. The script refuses a
version that isn't greater than the current one.

Show the human: the current version and the next, the bump and the changes that decide it (one
line each, with impact), the changes still open and left out, the files that will change, the
notes exactly as they will read, and the tag. When `after_bump` is in the output, show it too:
it runs after the version files are set, every tracked file it changes goes into the release
commit with them, and anything new it leaves untracked is listed, never committed. When
`prepare` is in the output, show it too: it runs after `after_bump`, builds into untracked or
ignored paths only (a tracked file it changes is put back and refused), and the end of what it
prints is kept on the tag, for `/sdlc:publish` to show at its approval. If `refusals` is non-empty, show them and stop: each
says what it needs (the main checkout, on `main`, committed; a tag that doesn't exist yet;
something with an impact other than `none`).

## Step 2 — WAIT for explicit approval

Ask literally:

> `Release <next>: set it in <files>, commit "Release <next>" with these notes, and tag it <tag>? Nothing is pushed. (yes / release as another version / no)`

With `after_bump` set, say it after the files: `…set it in <files>, run <after_bump> and commit
what it changes, commit "Release <next>"…`. With `prepare` set, say it after that: `…, run
<prepare> to build what publish will upload, commit "Release <next>"…`.

**Do nothing more until the human says yes.** Approval is for this release only. Another version
is a new plan: run Step 1 again with `--version` and ask again.

## Step 3 — Make it

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py release
```

With `--version X.Y.Z` exactly as approved, if one was. Exit 0 is `done`: the version files, the
changelog when configured, the `after_bump` command when configured, the `prepare` command when
configured, the commit, the tag, and the `note` of what was prepared. Exit 1 reports the step
that failed and what it said, in `refusals`; the files are put back when the `after_bump` or
`prepare` command or the commit fails, so a rerun finds `main` as it was, apart from any
`untracked` file the command left, which the output lists.

## Step 4 — Report and stop

Report the version, the commit and tag, the notes, what was prepared (`prepared`, and
`note_error` if the note couldn't be kept, in which case publish will show nothing prepared), and
the `undo` the output gives: until
`/sdlc:publish` pushes it, `git tag -d <tag> && git reset --keep HEAD~1` takes the release back.
That command is the human's to run, not this skill's.

Say plainly that nothing was pushed, and end with the next step: **`/sdlc:publish`**, now or once
the release has been looked at. If the output's `retro_due.due` is true, add one line after it:
a retrospective is due, its `why`, and **`/sdlc:retro`** once this release is published. Don't run
it: that's the human's call.

## Out of scope

- Pushing, publishing, a GitHub release. That's `/sdlc:publish`, behind its own approval.
- Editing a version file by hand, or picking the bump from commit messages: the impacts were
  settled at ship, with the diff in front of someone.
- Running the `undo`. The human's command.
