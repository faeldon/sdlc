---
id: 046
slug: push-at-close
tier: 2
impact: minor
stage: shipped
created: 2026-11-09
updated: 2026-11-10
shipped: 2026-11-10
idea: 2026-10-25-19
depends_on:
serves: [O2]
---

# 046 — Close and release push behind their own approval, and status nudges unpushed work

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Only `/sdlc:publish` pushes (`test_only_publish_pushes`, `cmd_publish`), so a closed change sits on
the local `main` until the next publish, which follows a release, which since 045 comes only once a
batch is due. On 2026-11-09 `main` was 13 commits ahead of `origin/main`, and issues #42–#45 were
open and labelled `landed`, each waiting for its `Close` commit's `Closes #N` to reach GitHub. That
work has no backup off this machine, no other checkout or machine sees it, and the issues read as
unfinished to anyone watching the repo. Nothing says so: neither `status` nor close's report counts
what `main` holds that the remote doesn't. The person's view: a change isn't really closed until
its issue is, so closing should push.

## Outcome

- A `[git] push` key in `.sdlc/config.toml` names the points that push: `"close"`, `"release"`,
  both, or none (`push = []`). **Enabled by default:** both points when `archive.target` is
  `github`; a host turns it off with `push = []`.
- With `close` named, close's one question ends "…then push <git.base> to <remote>?", and the same
  yes pushes the base branch to `release.remote` after the branch is deleted, never forced. Close's
  plan lists the commits the push would send, the change's own and anything else unpushed. A failed
  push never fails the close: the change has landed, the report says why, and a rerun or
  `/sdlc:publish` finishes it.
- With `release` named, release's question also pushes the base branch and the new tag;
  `/sdlc:publish` still runs the host's publish command and pushes whatever the remote lacks.
- `status` and close's report count what the base branch holds that the remote doesn't (closed
  changes, and on GitHub the open issues labelled `landed`) and, past a threshold, suggest a push
  naming the issues it would close. Never a problem, never a gate.
- This is a feature for every host, not this repo alone; here, where `main` is the marketplace,
  new installs get landed code between releases under the current version, which the person chose.
- **Moves O2:** a closed change reaches the remote at the close that lands it, so no landed work
  sits on one machine alone, and its issue closes the same day.

## Affected

- **Area:** close, release, publish, status, `[git]` config, the "only publish pushes" invariant.
- **Files & components:** `scripts/sdlc.py` (`CONFIG_KEYS["git"]`, `cmd_close` with a push step
  after `delete branch`, `cmd_release`, the push shared with `cmd_publish`, `status`'s unpushed
  count); `skills/close`, `skills/release`, `skills/status`;
  `tests/test_skills.py::test_only_publish_pushes`, which becomes "only the named steps push";
  `AGENTS.md`'s wording of the invariant; `docs/REFERENCE.md`, `guide/process.md`, `README.md`.
- **Downstream:** every GitHub host's close and release question, at once for hosts reading the
  plugin from a clone, at the next release for the rest; a host without GitHub sees only the nudge.
  This repo's `main` is what its marketplace installs from.
- **Contracts:** close's and release's WAIT steps change what they approve; never forced, a moved
  remote refused as publish refuses it; the scripts run on Windows; nothing public names the agent.

## Constraints

- Nothing is pushed without the person's yes: the push rides only on the question the skill already
  asks, and only when the key names that point.
- Never `--force`; never anything but the base branch and, at release, its tag.
- Close's steps and their resume-on-rerun are unchanged; the push is a step a rerun can finish.
- The nudge never makes `check --strict` fail.
- A missing or unreachable remote is reported, never guessed around.

## Open questions

- ~~The nudge's threshold: a count of unpushed closes, an age, or both, and the defaults.~~
  Resolved: a count, `[git] nudge_after_changes = 1`, 0 off (spec R2).
- ~~Whether close pushes when other unpushed commits ride along?~~ Resolved: it pushes all, and
  its plan lists them first; git pushes a branch tip (R3).
- ~~What `/sdlc:publish` does once release has pushed main and the tag?~~ Resolved: its steps
  skip what the remote has, and with the tag published it pushes the base branch alone (R6).
- ~~Where the remote's default branch isn't `git.base`, does the push still close the issues?~~
  Resolved: nothing changes; close already closes them itself there.
- ~~Branch protection refusing direct pushes to `main`?~~ Resolved: reported as `push_failed`,
  never failing the close, naming `push = []`; setup doesn't ask (R4).
- ~~Is a host with a remote but another tracker (or none) enabled too?~~ Resolved: no, the default
  is on only with `archive.target = "github"` (R1).
