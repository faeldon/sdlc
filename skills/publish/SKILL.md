---
name: publish
description: Publish the release /sdlc:release made — push main and its tag to the configured remote, never forced, then run the host's own publish command if it names one — or, once that tag is on the remote, push what has landed on main since, after one approval. Use from the main checkout once a release is tagged and looked at, or when status says Unpushed. Not for making the release (that's /sdlc:release), not with changes closed onto main after an unpushed release (release again), and never to force a remote that has moved.
argument-hint: ""
allowed-tools:
  - Read
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py publish *)'
disable-model-invocation: true
---

# Publish — take a release to its users

The second half of the release loop, and the playbook's production gate: the agent prepares the
release, and a person authorizes it here. Everything before this is local and can be taken back.
This can't: once `main` and the tag are on the remote, other people have them, and a release that
turns out wrong is followed by a new one, not withdrawn.

So it is its own skill, with its own approval, run when `/sdlc:release` has tagged the tip of
`main`, or when landed work waits for a push. Close and release push too, but only behind their
own questions and only when `git.push` names them; this is where a push they didn't make, or one
the remote refused, is finished. Ship never pushes, and the script refuses rather than forces.

## Step 0 — What would go out (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py publish --check
```

`config`'s `release` section names the remote (`release.remote`, `origin` by default) and the
host's own command for delivering a release (`release.publish`, with `{version}` and `{tag}`):
a package upload, a `gh release create`, a deploy. It runs with no terminal and stdin closed,
after this skill's one approval, so it must never ask for anything: what it uploads is built
beforehand by `release.prepare`, which `/sdlc:release` runs. With none set, publishing is the push alone,
which is how a repo whose users pull from it, a plugin marketplace among them, releases.
`config`'s `git.base` is the branch that is pushed, `main` unless the repo's is another; where this
skill says `main`, it means that branch.

`publish --check` gives the version, the tag, the remote, the command as it will run, what
`/sdlc:release` prepared for this tag (`prepared`: the end of `release.prepare`'s output, or null),
`unpushed`, what `main` holds that the remote doesn't (its commits, the closed changes and the
issues a push closes), and every refusal: not the main checkout, not on `main` or uncommitted
changes, no tag for the current version (`/sdlc:release` first), `main` moved past a tag the
remote doesn't have yet (changes were closed after the release; release again so they are in it),
or no such remote. Once the tag is on the remote, `main` past it is landed work, pushed alone.
`will_run` names the steps a yes would run, and `already` those the remote or the notes show done:
`push <git.base>`, `push tag`, `publish command`. With `will_run` empty there is nothing to
publish: say so and stop, with no question.

## Step 1 — Show it

Show the human the version and tag, the remote, what will be pushed (each push in `will_run`:
`main` with `unpushed.ahead` one commit a line and the issues it closes, and the tag), and the
publish command exactly as it will run when it is in `will_run`, or that it has run already or
there is none. When `prepared` is set, show it
as what the command will upload; when `release.prepare` is set and `prepared` is null, say this
release has nothing prepared, so the command runs on whatever it finds. **If there are refusals, stop
here** and say what each needs.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Publish <tag>: push <git.base> and <tag> to <remote>, then run <command>? This can't be taken back. (yes / no)`

Leave out `, then run <command>` when `publish command` isn't in `will_run`, and `and <tag>`
when `push tag` isn't. When `prepared` is set, say `…, then run <command> to upload what was
prepared, shown above?`. When `will_run` is `push <git.base>` alone, ask instead:

> `Push <git.base> to <remote>: the <n> commits shown, closing <issues>? This can't be taken back. (yes / no)`

**Do nothing more until the human says yes.** Approval is for this release and this remote only.

## Step 3 — Publish it

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py publish
```

Its steps run in order: `push <git.base>`, `push tag`, `publish command`. Each is skipped when it
is already done, so a rerun after a failure picks up where it stopped without pushing twice or
publishing twice, and a push-only publish does just the first.

- Exit 0: everything in `done` happened, and `skipped` says what was already in place.
- Exit 1: a step failed, named in `refusals` with what it said. A push the remote refused means
  it has commits this checkout doesn't: someone else pushed. Never force it; say so, and the
  human decides (pull and release again, usually). A failed publish command leaves the pushes in
  place; once its cause is fixed, a rerun runs only the command.

## Step 4 — Report and stop

Report what `done` and `skipped` list, the remote, and the tag. If the command printed where the
release went (a URL), pass it on. Say plainly what was pushed and published, since it now can't
be undone, and that the next release starts from this tag.

## Out of scope

- Making the release, or changing its version: `/sdlc:release`.
- `--force`, deleting a remote tag, or rewriting `main` on the remote. Never.
- Pushing anything but `main` and the release tag.
- `git push` from this skill: the script's push is the only one.
