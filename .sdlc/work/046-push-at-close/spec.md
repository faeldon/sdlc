---
id: 046
slug: push-at-close
kind: spec
created: 2026-11-09
updated: 2026-11-09
---

# 046 — Close and release push behind their own approval, and status nudges unpushed work · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. `[git] push`**, a list of `"close"` and `"release"`. Unset, `load_config()` resolves it
   to `["close", "release"]` when `archive.target` is `github`, else `[]`; an explicit list
   (`[]` included) always wins. Any other value is a config problem. Tested both ways.
2. **R2. `[git] nudge_after_changes`**, int, default 1; 0 turns the nudge off. In `INT_KEYS`.
3. **R3. `close --check` reports `push`**: `on`, the remote and base branch, and as `unpushed` the
   commits the push of the base branch would send (oneline: the `Close` or `Drop` commit while
   it isn't written yet, the change's own, then what the base branch already holds unpushed) and
   the issues they close. Off, it says why in `off_because` (`push` doesn't name `close`, or no
   remote). With no tracking ref, `unpushed` is null and the push still goes.
4. **R4. `close` pushes as its last step**, after `delete branch`, when `push` names `close`: the
   base branch to `release.remote`, never forced, for shipped and dropped changes alike. A failed
   push leaves close's exit 0, every earlier step kept, and sets `push_failed` with git's reason
   and the retry (`/sdlc:publish`). A close stopping before it (exit 1, or 3 inside the worktree)
   pushes when its rerun completes.
5. **R5. `release` pushes the base branch and the new tag** after tagging, when `push` names
   `release`; `release --check` reports it as `push`. A failed push leaves the release made and
   local, and says `/sdlc:publish` finishes it.
6. **R6. `publish`**: with the current tag unpublished, as now (base branch, tag, publish
   command, each skipped when already there). With the tag already on the remote and the base
   branch ahead of it, it pushes the base branch alone, no refusal. Nothing ahead: says there's
   nothing to publish.
7. **R7. One push.** `"push"` appears in `sdlc.py` only in one `_push()` helper (never
   `--force`), called only from `cmd_publish`, `cmd_close` and `cmd_release`; no skill runs
   `git push` or has a push rule. The test pinning this replaces `test_only_publish_pushes`.
8. **R8. `status` prints `■ Unpushed`** when the base branch's remote-tracking ref exists and
   the base branch holds at least `nudge_after_changes` `Close`/`Drop` commits it doesn't: the
   count, the oldest's age, and the issues they'd close, ending `→ /sdlc:publish`. It never runs
   a network command; never a problem, `check --strict` unchanged.
9. **R9. Close's report** says what was pushed and which issues GitHub will now close; with push
   off, it carries the same nudge line as status.
10. **R10. Skills**: close's WAIT gains "…, then push <git.base> to <remote>" when `push` is set,
    and its plan shows the commits; release's replaces "Nothing is pushed." with "…, then push
    <git.base> and <tag> to <remote>" when `push` names `release`; publish gains a WAIT variant
    for a push-only publish; status's precedence puts an `Unpushed` nudge right after a quiet
    depended-on change, recommending `/sdlc:publish`.
11. **R11. Docs**: `AGENTS.md`'s "Only publish pushes" becomes "only publish, and close and
    release when `git.push` names them, push"; `docs/REFERENCE.md` the two keys and the defaults;
    `guide/process.md` (and `.sdlc/setup.json` by `record`) and `README.md` say when work reaches
    the remote.
12. **R12. Nit `2026-10-24-9`**: release's skill has no line past 100 characters.

## Design

- **Config.** `CONFIG_KEYS["git"]` gains `push` (default `None`, resolved in `load_config()` from
  `archive.target`) and `nudge_after_changes`.
- **`_push(home, remote, ref)`**: `cmd_publish`'s `push()` closure lifted out unchanged
  (`_git_err(home, "push", "-q", remote, ref)`), the one place the string appears.
- **`_unpushed(home, cfg)`** → `{remote, ahead: [sha, subject], closes: [N], changes,
  oldest_days}`, from `refs/remotes/<remote>/<trunk>..<trunk>` locally: a stale tracking ref
  under-counts, never errs. Status, close's report and publish's plan all read it.
- **Close**: a `("push", …)` step after `delete branch` in `steps`, skipped when not configured;
  the step never returns an error, it records `push_failed` and lets close exit 0, since the
  change has landed. A rerun after exit 3 reaches it through close's existing resume; after
  everything is done, close can't find the change, so the retry is publish's (R6).
- **Release**: `push trunk`, `push tag` after `tag` in `cmd_release`, through publish's
  `pushed()` skip-if-there check, lifted out too.
- **Publish**: the `{trunk} has moved past {tag}` refusal becomes a branch: tag on the remote →
  steps are `push {trunk}` only.
- **Status skill precedence**: problems, ready to close, quiet build+, quiet depended-on,
  **Unpushed**, priority high, Release due, Retro due, Next up.

## Contracts touched

- **Only publish pushes (`AGENTS.md`, `test_only_publish_pushes`).** This changes it, on purpose
  and loudly: close and release push too, only when `git.push` names them and only behind the
  question each already asks. Nothing else may, never forced. The test is rewritten around
  `_push()` and its three callers, not deleted.
- **A skill's WAIT step (always Tier 2).** Close's and release's questions now approve a push; the
  question names the remote and branch, and close's plan lists the commits, so the yes covers what
  is shown.
- **What a host already has means.** `/sdlc:publish` now also pushes `main` between releases, and
  an existing GitHub host's close now pushes without an edit to its config. The person's decision
  (default on), said in the docs; `push = []` restores the old behaviour.
- **Close never pushes / `Closes #N` waits for a push.** Still true with push off; with it on the
  issue closes as close ends.
- **The marketplace (this repo).** Pushing `main` at close puts unreleased code on what new
  installs read, under the current version. Accepted by the person; existing installs refresh only
  on a version change.
- **Windows; nothing names the agent.** `_push` goes through `_git`; nothing added to commit text.

## Alternatives rejected

- **Push silently, no mention in the question.** The person chose folding it into the existing
  yes; silence makes public pushes the one write the plugin makes unannounced.
- **A separate push question after close.** One more stop, against O3.
- **Push only the change's commits.** Git pushes a branch tip; the `Close` commit sits on top of
  everything unpushed. Listing it all is honest.
- **A network check in status (`ls-remote`, `gh`).** Status stays offline; the tracking ref is
  updated by every push the plugin makes.
- **Retry a failed push from close.** After the branch is deleted, close can't find the change;
  publish already owns retries.

## Verification

- `./check.sh` passes, with new tests (a bare repo as `origin`) in `tests/test_release.py` or a
  new `tests/test_push.py`: close pushes or doesn't per `push`; a refused push leaves close at 0
  with `push_failed`; release pushes branch and tag; publish pushes the branch alone after a
  published tag; status shows `Unpushed` at and above the threshold, not below, not at 0; the
  `push` default follows `archive.target`.
- `test_only_publish_pushes` replaced by the `_push()` caller test, still failing on a skill
  with `git push`.
- `sdlc.py drift` reports nothing after `record`.
- By hand, in this repo after it lands: `sdlc.py status` shows `■ Unpushed` (15 commits, closing
  #42–#46), and `/sdlc:publish` pushes `main` without refusing.
